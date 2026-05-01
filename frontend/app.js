/* ═══════════════════════════════════════════════════════════════════════════
   SAANYE CRM — Application Logic
   ════════════════════════════════════════════════════════════════════════════ */

const API = 'http://localhost:8000/api/v1';

/* ─── Formatters ─────────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

function fmt$(n) {
  if (n == null) return '—';
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) return (n / 1_000_000_000).toFixed(1) + 'B';
  if (abs >= 1_000_000)     return (n / 1_000_000).toFixed(1) + 'M';
  if (abs >= 1_000)         return (n / 1_000).toFixed(1) + 'k';
  return n.toFixed(0);
}

function fmtPesos(n) {
  if (n == null) return '—';
  return '$' + new Intl.NumberFormat('es-CO').format(Math.round(n));
}

function fmtPct(n) {
  if (n == null) return '—';
  return (n > 0 ? '+' : '') + n.toFixed(1) + '%';
}

function deltaClass(n) {
  if (n == null || n === 0) return 'flat';
  return n > 0 ? 'up' : 'down';
}

function deltaArrow(n) {
  if (n == null || n === 0) return '→';
  return n > 0 ? '▲' : '▼';
}

function deltaBadge(pct) {
  const cls = deltaClass(pct);
  return `<span class="delta ${cls}">${deltaArrow(pct)} ${fmtPct(pct)}</span>`;
}

/* ─── DateTime ───────────────────────────────────────────────────────────── */
function updateClock() {
  const now = new Date();
  $('datetime').textContent = now.toLocaleString('es-CO', {
    weekday: 'short', day: '2-digit', month: 'short',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
setInterval(updateClock, 1000);
updateClock();

/* ─── Connection status ──────────────────────────────────────────────────── */
function setStatus(state, text) {
  const dot = $('status-dot');
  const txt = $('status-text');
  dot.className = 'status-dot ' + state;
  txt.textContent = text;
}

/* ─── Toast ──────────────────────────────────────────────────────────────── */
let _toastTimer;
function showToast(msg, isError = false) {
  let toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className = 'toast ' + (isError ? 'error' : '');
  clearTimeout(_toastTimer);
  requestAnimationFrame(() => toast.classList.add('show'));
  _toastTimer = setTimeout(() => toast.classList.remove('show'), 3500);
}

/* ─── Fetch helper ───────────────────────────────────────────────────────── */
async function apiFetch(path) {
  setStatus('pulse', 'Consultando…');
  try {
    const res = await fetch(API + path);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    setStatus('ok', 'Conectado · ' + new Date().toLocaleTimeString('es-CO'));
    return json.data ?? [];
  } catch (e) {
    setStatus('error', 'Error de conexión');
    showToast('No se pudo conectar con el servidor', true);
    return null;
  }
}

/* ─── View routing ───────────────────────────────────────────────────────── */
const views = {
  mtd:          { title: 'Resumen MTD', badge: 'Mes actual vs año anterior' },
  caida:        { title: 'Clientes en Caída', badge: 'Top 50 por pérdida' },
  recuperados:  { title: 'Clientes Recuperados', badge: 'Regresaron a comprar' },
};

let activeView = 'mtd';

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const view = el.dataset.view;
    switchView(view);
  });
});

function switchView(view) {
  activeView = view;
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  $('view-' + view).classList.add('active');
  $('nav-' + view).classList.add('active');
  $('page-title').textContent = views[view].title;
  $('page-badge').textContent = views[view].badge;
  if (view === 'caida' && !_caidaLoaded)  loadCaida();
  if (view === 'recuperados' && !_recLoaded) loadRecuperados();
}

/* ══════════════════════════ VIEW: MTD ═══════════════════════════════════ */
let _mtdChart = null;
let _mtdData  = [];

async function loadMTD() {
  $('btn-refresh').classList.add('spinning');
  const data = await apiFetch('/analytics/mtd');
  $('btn-refresh').classList.remove('spinning');
  if (!data) return;
  _mtdData = data;
  renderKpisMTD(data);
  renderChartMTD(data);
  renderTableMTD(data);
  ['kpi-total-actual','kpi-variacion','kpi-clientes','kpi-vendedores'].forEach(id => $( id).classList.add('loaded'));
}

function renderKpisMTD(data) {
  const totalActual    = data.reduce((s, r) => s + (r.ventaActual   || 0), 0);
  const totalAnterior  = data.reduce((s, r) => s + (r.ventaAnterior || 0), 0);
  const totalClientes  = data.reduce((s, r) => s + (r.clientesActivos || 0), 0);
  const vendedores     = new Set(data.map(r => r.vendedor)).size;
  const pct = totalAnterior ? ((totalActual - totalAnterior) / totalAnterior * 100) : null;

  $('kpi-val-actual').textContent    = '$' + fmt$(totalActual);
  $('kpi-sub-actual').textContent    = 'Año anterior: $' + fmt$(totalAnterior);

  $('kpi-val-var').innerHTML         = deltaBadge(pct);
  $('kpi-sub-var').textContent       = fmtPesos(totalActual - totalAnterior);

  $('kpi-val-clientes').textContent  = totalClientes.toLocaleString('es-CO');
  $('kpi-sub-clientes').textContent  = 'Este mes';

  $('kpi-val-vendedores').textContent = vendedores;
  $('kpi-sub-vendedores').textContent = 'con ventas activas';
}

function renderChartMTD(data) {
  const top = data.slice(0, 12);
  const labels = top.map(r => r.nombreVendedor?.split(' ')[0] || r.vendedor);
  const actual  = top.map(r => r.ventaActual   || 0);
  const anterior = top.map(r => r.ventaAnterior || 0);

  if (_mtdChart) _mtdChart.destroy();

  const ctx = $('chart-mtd').getContext('2d');
  _mtdChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Actual',
          data: actual,
          backgroundColor: 'rgba(99,102,241,.85)',
          borderRadius: 6,
          borderSkipped: false,
        },
        {
          label: 'Año Anterior',
          data: anterior,
          backgroundColor: 'rgba(99,102,241,.2)',
          borderRadius: 6,
          borderSkipped: false,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index' },
      plugins: {
        legend: {
          labels: { color: '#8892b0', font: { family: 'Inter', size: 11 }, boxWidth: 12, padding: 16 }
        },
        tooltip: {
          backgroundColor: '#151929',
          borderColor: 'rgba(255,255,255,.08)',
          borderWidth: 1,
          titleColor: '#e8eaf2',
          bodyColor: '#8892b0',
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: $${fmt$(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#8892b0', font: { family: 'Inter', size: 10 }, maxRotation: 35 },
          grid:  { color: 'rgba(255,255,255,.04)' }
        },
        y: {
          ticks: {
            color: '#8892b0',
            font: { family: 'Inter', size: 10 },
            callback: v => '$' + fmt$(v)
          },
          grid: { color: 'rgba(255,255,255,.04)' }
        }
      }
    }
  });
}

function renderTableMTD(data) {
  const maxVenta = Math.max(...data.map(r => r.ventaActual || 0));
  const tbody = $('tbody-mtd');

  tbody.innerHTML = data.map(r => {
    const pct = r.ventaAnterior ? ((r.ventaActual - r.ventaAnterior) / r.ventaAnterior * 100) : null;
    const barW = maxVenta ? (((r.ventaActual || 0) / maxVenta) * 100).toFixed(1) : 0;
    const barColor = pct >= 0 ? '#6366f1' : '#f43f5e';
    return `
      <tr>
        <td>
          <div style="font-weight:600;color:var(--text-primary)">${r.nombreVendedor || r.vendedor || '—'}</div>
          <div style="font-size:.7rem;color:var(--text-muted);margin-top:2px">${r.vendedor || ''}</div>
        </td>
        <td class="num">
          <div>${fmtPesos(r.ventaActual)}</div>
          <div class="mini-bar-wrap" style="margin-top:4px">
            <div class="mini-bar"><div class="mini-bar-fill" style="width:${barW}%;background:${barColor}"></div></div>
          </div>
        </td>
        <td class="num">${fmtPesos(r.ventaAnterior)}</td>
        <td class="num">${deltaBadge(pct)}</td>
        <td class="num"><span style="color:var(--text-primary);font-weight:600">${r.clientesActivos ?? 0}</span></td>
      </tr>`;
  }).join('') || '<tr><td colspan="5" class="loading-row">Sin datos</td></tr>';
}

// Search filter MTD
$('search-mtd').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  const filtered = _mtdData.filter(r =>
    (r.nombreVendedor || '').toLowerCase().includes(q) ||
    (r.vendedor || '').toLowerCase().includes(q)
  );
  renderTableMTD(filtered);
});

/* ══════════════════════════ VIEW: CAÍDA ═════════════════════════════════ */
let _caidaLoaded = false;

async function loadCaida() {
  _caidaLoaded = true;
  const dias    = $('filter-dias').value;
  const minimo  = $('filter-minimo').value;

  $('tbody-caida').innerHTML = '<tr><td colspan="7" class="loading-row">Cargando datos…</td></tr>';
  $('kpi-caida-total').classList.remove('loaded');
  $('kpi-caida-perdida').classList.remove('loaded');

  const data = await apiFetch(`/analytics/clientes/caida?dias_comparar=${dias}&minimo_venta=${minimo}`);
  if (!data) return;

  // KPIs
  const perdida = data.reduce((s, r) => s + (r.diferencia || 0), 0);
  $('kpi-val-caida-total').textContent   = data.length;
  $('kpi-val-caida-perdida').textContent = '$' + fmt$(Math.abs(perdida));
  $('kpi-caida-total').classList.add('loaded');
  $('kpi-caida-perdida').classList.add('loaded');

  // Table
  const tbody = $('tbody-caida');
  tbody.innerHTML = data.map(r => {
    const pct = r.pctCambio ?? null;
    return `
      <tr>
        <td>
          <div style="font-weight:600;color:var(--text-primary)">${r.nombreCliente || '—'}</div>
          <span style="font-family:'JetBrains Mono',monospace;font-size:.7rem;color:var(--text-muted)">NIT: ${r.nit || '—'}</span>
        </td>
        <td>${r.nombreVendedor || r.vendedor || '—'}</td>
        <td class="num">${fmtPesos(r.ventaAnterior)}</td>
        <td class="num">${fmtPesos(r.ventaReciente)}</td>
        <td class="num" style="color:var(--danger)">${fmtPesos(r.diferencia)}</td>
        <td class="num">${deltaBadge(pct)}</td>
        <td><button class="btn-action" onclick="openProductos('${r.nit}')">Ver productos →</button></td>
      </tr>`;
  }).join('') || '<tr><td colspan="7" class="loading-row">Sin clientes en caída para este período</td></tr>';
}

$('btn-apply-caida').addEventListener('click', () => { _caidaLoaded = false; loadCaida(); });

/* ══════════════════════════ VIEW: RECUPERADOS ════════════════════════════ */
let _recLoaded = false;

async function loadRecuperados() {
  _recLoaded = true;
  const dias  = $('filter-dias-rec').value;
  const gap   = $('filter-gap').value;

  $('tbody-rec').innerHTML = '<tr><td colspan="6" class="loading-row">Cargando datos…</td></tr>';
  $('kpi-rec-total').classList.remove('loaded');
  $('kpi-rec-dias').classList.remove('loaded');

  const data = await apiFetch(`/analytics/clientes/recuperados?dias_recientes=${dias}&meses_gap=${gap}`);
  if (!data) return;

  // KPIs
  const avgDias = data.length ? (data.reduce((s,r) => s + (r.diasAusente || 0), 0) / data.length) : 0;
  $('kpi-val-rec-total').textContent = data.length;
  $('kpi-val-rec-dias').textContent  = Math.round(avgDias);
  $('kpi-rec-total').classList.add('loaded');
  $('kpi-rec-dias').classList.add('loaded');

  // Table
  const tbody = $('tbody-rec');
  tbody.innerHTML = data.map(r => `
    <tr>
      <td>
        <div style="font-weight:600;color:var(--text-primary)">${r.nombreCliente || '—'}</div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:.7rem;color:var(--text-muted)">NIT: ${r.nit || '—'}</span>
      </td>
      <td>${r.nombreVendedor || r.vendedor || '—'}</td>
      <td class="num">${r.ultimaCompra   || '—'}</td>
      <td class="num">${r.ultimaCompraPrevia || '—'}</td>
      <td class="num">
        <span style="color:var(--warning);font-weight:700">${r.diasAusente ?? '—'} días</span>
      </td>
      <td class="num">${fmtPesos(r.totalReciente)}</td>
    </tr>`
  ).join('') || '<tr><td colspan="6" class="loading-row">Sin clientes recuperados para este período</td></tr>';
}

$('btn-apply-rec').addEventListener('click', () => { _recLoaded = false; loadRecuperados(); });

/* ══════════════════════════ MODAL: PRODUCTOS PERDIDOS ════════════════════ */
async function openProductos(nit) {
  $('modal-nit-label').textContent   = 'NIT: ' + nit;
  $('tbody-productos').innerHTML     = '<tr><td colspan="5" class="loading-row">Cargando productos…</td></tr>';
  $('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';

  const data = await apiFetch(`/analytics/productos/perdidos/${nit}`);
  if (!data) return;

  const tbody = $('tbody-productos');
  tbody.innerHTML = data.map(r => {
    return `
      <tr>
        <td>
          <div style="font-weight:600;color:var(--text-primary)">${r.producto || '—'}</div>
        </td>
        <td class="num">${fmtPesos(r.totalHistorico)}</td>
        <td class="num">${fmtPesos(r.totalReciente)}</td>
        <td class="num" style="color:var(--danger)">-${fmtPesos(r.impacto)}</td>
        <td class="num">${deltaBadge(r.pctCambio)}</td>
      </tr>`;
  }).join('') || '<tr><td colspan="5" class="loading-row">No se encontraron productos perdidos</td></tr>';
}

// Expose globally for inline onclick
window.openProductos = openProductos;

$('modal-close').addEventListener('click', closeModal);
$('modal-overlay').addEventListener('click', e => { if (e.target === $('modal-overlay')) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

function closeModal() {
  $('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

/* ══════════════════════════ REFRESH BUTTON ══════════════════════════════ */
$('btn-refresh').addEventListener('click', () => {
  if (activeView === 'mtd') loadMTD();
  else if (activeView === 'caida')       { _caidaLoaded = false; loadCaida(); }
  else if (activeView === 'recuperados') { _recLoaded   = false; loadRecuperados(); }
});

/* ══════════════════════════ INIT ════════════════════════════════════════ */
loadMTD();
