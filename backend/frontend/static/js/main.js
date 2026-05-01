/* ── Config ──────────────────────────────────────────────────────── */
const API  = '/api/v1';

/* ── Formatters ──────────────────────────────────────────────────── */
const COP  = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
const NUM  = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const fmt  = v => COP.format(v ?? 0);
const fmtN = v => NUM.format(v ?? 0);
const pctColor = p => p >= 0 ? 'c-green' : p >= -20 ? 'c-yellow' : 'c-red';
const pctBg    = p => p >= 0 ? 'rgba(16,185,129,.08)' : p >= -20 ? 'rgba(245,158,11,.08)' : 'rgba(239,68,68,.08)';
const sign     = v => v > 0 ? `+${fmt(v)}` : fmt(v);
const signPct  = v => v > 0 ? `+${v.toFixed(1)}%` : `${v.toFixed(1)}%`;

/* ── State ───────────────────────────────────────────────────────── */
let mtdData         = [];
let caidaAll        = [];
let recuperadosData = [];
let mtdChart        = null;

/* ── HTTP ────────────────────────────────────────────────────────── */
async function apiFetch(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status} — ${url}`);
  return r.json();
}

/* ═══════════════════════════════════════════════════════════════════
   KPI 1 — MTD
═══════════════════════════════════════════════════════════════════ */
async function loadMTD() {
  try {
    const { data } = await apiFetch(`${API}/analytics/mtd`);
    mtdData = data;

    const totActual   = data.reduce((s, r) => s + (r.ventaActual  ?? 0), 0);
    const totAnterior = data.reduce((s, r) => s + (r.ventaAnterior ?? 0), 0);
    const totClientes = data.reduce((s, r) => s + (r.clientesActivos ?? 0), 0);
    const variacion   = totAnterior > 0 ? (totActual - totAnterior) / totAnterior * 100 : 0;

    // KPI cards
    setText('kpi-total-val',    fmt(totActual));
    setText('kpi-total-sub',    `Año anterior: ${fmt(totAnterior)}`);

    const varEl = document.getElementById('kpi-var-val');
    varEl.textContent = signPct(variacion);
    varEl.className   = `kpi-value ${pctColor(variacion)}`;
    setText('kpi-var-sub',      `${sign(totActual - totAnterior)}`);

    setText('kpi-clientes-val', fmtN(totClientes));

    renderMTDChart();
  } catch (e) {
    console.error('[MTD]', e);
  }
}

function renderMTDChart() {
  const labels   = mtdData.map(r => r.nombreVendedor || r.vendedor);
  const actual   = mtdData.map(r => r.ventaActual   ?? 0);
  const anterior = mtdData.map(r => r.ventaAnterior ?? 0);

  const ctx = document.getElementById('chart-mtd').getContext('2d');
  if (mtdChart) mtdChart.destroy();

  mtdChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Año actual',
          data: actual,
          backgroundColor: 'rgba(108,99,255,.7)',
          borderColor: '#6c63ff',
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: 'Año anterior',
          data: anterior,
          backgroundColor: 'rgba(255,255,255,.08)',
          borderColor: 'rgba(255,255,255,.15)',
          borderWidth: 1,
          borderRadius: 4,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#94a3b8', font: { size: 12 } }
        },
        tooltip: {
          backgroundColor: '#1a1f32',
          borderColor: 'rgba(255,255,255,.1)',
          borderWidth: 1,
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          callbacks: {
            label: ctx => `  ${ctx.dataset.label}: ${fmt(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#64748b', font: { size: 11 } },
          grid:  { color: 'rgba(255,255,255,.04)' }
        },
        y: {
          ticks: {
            color: '#64748b',
            font: { size: 11 },
            callback: v => {
              if (v >= 1_000_000) return `$${(v/1_000_000).toFixed(0)}M`;
              if (v >= 1_000)    return `$${(v/1_000).toFixed(0)}k`;
              return `$${v}`;
            }
          },
          grid: { color: 'rgba(255,255,255,.04)' }
        }
      }
    }
  });
}

/* ═══════════════════════════════════════════════════════════════════
   KPI 2 — Clientes Recuperados
═══════════════════════════════════════════════════════════════════ */
async function loadRecuperados() {
  try {
    const { data, total } = await apiFetch(`${API}/analytics/clientes/recuperados`);
    recuperadosData = data;

    setText('kpi-rec-val', fmtN(total));
    setText('badge-rec', total);

    const list = document.getElementById('list-recuperados');
    if (total === 0) {
      list.innerHTML = '<div class="empty">Sin clientes recuperados este período</div>';
      return;
    }

    list.innerHTML = data.map(c => `
      <div class="list-item" onclick="showPerdidos('${c.nit}', '${esc(c.nombreVendedor || c.vendedor)}')">
        <div class="list-item-top">
          <span class="nit-chip">${c.nit}</span>
          <span class="vendor-name">${esc(c.nombreVendedor || c.vendedor)}</span>
        </div>
        <div class="list-item-bot">
          <span class="dias-badge">${c.diasAusente} días ausente</span>
          <span class="total-chip">${fmt(c.totalReciente)}</span>
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('[Recuperados]', e);
  }
}

/* ═══════════════════════════════════════════════════════════════════
   KPI 3 — Clientes en Caída
═══════════════════════════════════════════════════════════════════ */
async function loadCaida() {
  try {
    const { data, total } = await apiFetch(`${API}/analytics/clientes/caida`);
    caidaAll = data;

    setText('badge-caida', total);

    // Poblar filtro de vendedores
    const vendedores = [...new Set(data.map(r => r.nombreVendedor || r.vendedor))].sort();
    const sel = document.getElementById('sel-vendedor');
    sel.innerHTML = '<option value="">Todos los vendedores</option>' +
      vendedores.map(v => `<option value="${v}">${esc(v)}</option>`).join('');

    renderCaida(data);
  } catch (e) {
    console.error('[Caida]', e);
  }
}

function filterCaida() {
  const v = document.getElementById('sel-vendedor').value;
  renderCaida(v ? caidaAll.filter(r => (r.nombreVendedor || r.vendedor) === v) : caidaAll);
}

function renderCaida(rows) {
  const tbody = document.getElementById('tbody-caida');
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty">Sin datos</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const pct = r.pctCambio ?? 0;
    const cls = pctColor(pct);
    return `
      <tr style="background:${pctBg(pct)}">
        <td>${esc(r.nombreVendedor || r.vendedor || '—')}</td>
        <td class="mono">${r.nit}</td>
        <td class="num">${fmt(r.ventaAnterior)}</td>
        <td class="num">${fmt(r.ventaReciente)}</td>
        <td class="num ${cls}">${sign(r.diferencia ?? 0)}</td>
        <td class="num ${cls}">${signPct(pct)}</td>
        <td>
          <button class="btn-sm" onclick="showPerdidos('${r.nit}','${esc(r.nombreVendedor||r.vendedor)}')">
            Ver productos
          </button>
        </td>
      </tr>`;
  }).join('');
}

/* ═══════════════════════════════════════════════════════════════════
   KPI 4 — Productos Perdidos (modal)
═══════════════════════════════════════════════════════════════════ */
async function showPerdidos(nit, vendedor) {
  document.getElementById('overlay').classList.remove('hidden');
  document.getElementById('modal-nit').textContent = `NIT ${nit}`;
  document.getElementById('modal-vendor').textContent = vendedor || '';
  document.getElementById('tbody-perdidos').innerHTML =
    '<tr><td colspan="5" class="loading-row"><span class="spinner"></span> Cargando...</td></tr>';

  try {
    const { data, total } = await apiFetch(`${API}/analytics/productos/perdidos/${nit}`);
    const tbody = document.getElementById('tbody-perdidos');

    if (total === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty">Sin productos perdidos identificados</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(p => {
      const pct = p.pctCambio ?? 0;
      return `
        <tr>
          <td>${esc(p.producto)}</td>
          <td class="num">${fmt(p.totalHistorico)}</td>
          <td class="num">${fmt(p.totalReciente)}</td>
          <td class="num c-red">${fmt(p.impacto)}</td>
          <td class="num c-red">${signPct(pct)}</td>
        </tr>`;
    }).join('');
  } catch (e) {
    document.getElementById('tbody-perdidos').innerHTML =
      `<tr><td colspan="5" class="error-row">${e.message}</td></tr>`;
  }
}

function closeModal() {
  document.getElementById('overlay').classList.add('hidden');
}

/* ═══════════════════════════════════════════════════════════════════
   Ventas Detalladas
═══════════════════════════════════════════════════════════════════ */
async function loadVentas() {
  const fi = document.getElementById('fi').value;
  const ff = document.getElementById('ff').value;
  if (!fi || !ff) return;

  document.getElementById('tbody-ventas').innerHTML =
    '<tr><td colspan="8" class="loading-row"><span class="spinner"></span> Consultando ERP...</td></tr>';
  setText('ventas-footer', '');

  try {
    const { data, total } = await apiFetch(`${API}/ventas/raw?fecha_inicial=${fi}&fecha_final=${ff}`);
    const tbody = document.getElementById('tbody-ventas');

    if (total === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty">Sin ventas en ese rango</td></tr>';
      return;
    }

    tbody.innerHTML = data.map(r => `
      <tr>
        <td>${r.fecha ?? ''}</td>
        <td class="mono">${r.prefijo ?? ''}</td>
        <td class="mono">${r.numero ?? ''}</td>
        <td>${esc(r.nombreVendedor || r.vendedor || '—')}</td>
        <td class="mono">${r.nit ?? ''}</td>
        <td>${esc(r.producto ?? '')}</td>
        <td class="num">${fmtN(r.totalCantidad)}</td>
        <td class="num">${fmt(r.totalNeto)}</td>
      </tr>`).join('');

    const gran = data.reduce((s, r) => s + (r.totalNeto ?? 0), 0);
    setText('ventas-footer', `${fmtN(total)} registros — Total: ${fmt(gran)}`);
  } catch (e) {
    document.getElementById('tbody-ventas').innerHTML =
      `<tr><td colspan="8" class="error-row">${e.message}</td></tr>`;
  }
}

/* ═══════════════════════════════════════════════════════════════════
   Navegación
═══════════════════════════════════════════════════════════════════ */
function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
  document.getElementById(`view-${name}`)?.classList.remove('hidden');
  document.querySelector(`[data-view="${name}"]`)?.classList.add('active');
  const titles = { jefe: 'Dashboard Comercial', ventas: 'Ventas Detalladas' };
  setText('page-title', titles[name] ?? name);
}

/* ═══════════════════════════════════════════════════════════════════
   Refresh
═══════════════════════════════════════════════════════════════════ */
async function refreshAll() {
  setText('last-update', '');
  document.getElementById('last-update').innerHTML = '<span class="spinner"></span>';
  await Promise.all([loadMTD(), loadCaida(), loadRecuperados()]);
  setText('last-update', `Actualizado ${new Date().toLocaleTimeString('es-CO')}`);
}

/* ── Helpers ─────────────────────────────────────────────────────── */
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ── Init ────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Fechas por defecto: primer día del mes → hoy
  const hoy     = new Date();
  const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  document.getElementById('fi').value = primero.toISOString().split('T')[0];
  document.getElementById('ff').value = hoy.toISOString().split('T')[0];

  // Navegación
  document.querySelectorAll('.nav-item').forEach(li =>
    li.addEventListener('click', () => switchView(li.dataset.view))
  );

  // Cerrar modal con Escape
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  refreshAll();
});
