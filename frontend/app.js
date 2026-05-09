/* ═══════════════════════════════════════════════════════════════════════════
   SAANYE CRM — The Sales Bar App Logic
   ════════════════════════════════════════════════════════════════════════════ */

const API = 'http://localhost:8000/api/v1';

const $ = id => document.getElementById(id);

// Formateo financiero (MM = millones)
function fmtMM(n) {
  if (n == null) return '—';
  const val = n / 1_000_000;
  return '$' + val.toLocaleString('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' MM';
}

function fmtPesos(n) {
  if (n == null) return '—';
  return '$' + Math.round(n).toLocaleString('es-CO');
}

function fmtPct(n) {
  if (n == null) return '—';
  return (n > 0 ? '+' : '') + n.toFixed(1) + '%';
}

function showToast(msg, isError = false) {
  let toast = $('toast');
  toast.textContent = msg;
  toast.className = 'toast ' + (isError ? 'error' : '');
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

let vendedoras = [];
let metas = {};
let currentVendedora = null;

async function init() {
  try {
    const [vendRes, metasRes] = await Promise.all([
      fetch(API + '/analytics/vendedoras'),
      fetch(API + '/analytics/metas')
    ]);
    
    if (vendRes.ok) {
      const vendData = await vendRes.json();
      vendedoras = vendData.data || [];
      populateDropdown();
    }
    
    if (metasRes.ok) {
      metas = await metasRes.json();
    }
  } catch (e) {
    showToast('Error cargando configuración inicial', true);
  }
}

function populateDropdown() {
  const select = $('select-vendedora');
  select.innerHTML = '<option value="">Selecciona tu nombre...</option>';
  
  vendedoras.forEach(v => {
    if (!v.vendedor) return;
    const opt = document.createElement('option');
    opt.value = v.vendedor;
    opt.textContent = v.vendedor.toUpperCase();
    select.appendChild(opt);
  });
}

$('select-vendedora').addEventListener('change', (e) => {
  currentVendedora = e.target.value;
  if (!currentVendedora) {
    $('dashboard-content').style.display = 'none';
    $('welcome-state').style.display = 'block';
    return;
  }
  
  $('dashboard-content').style.display = 'flex';
  $('welcome-state').style.display = 'none';
  loadDashboard();
});

$('btn-refresh').addEventListener('click', () => {
  if (currentVendedora) loadDashboard();
});

async function loadDashboard() {
  $('btn-refresh').classList.add('spinning');
  
  try {
    const vQuery = `?vendedor=${encodeURIComponent(currentVendedora)}`;
    
    // Disparar requests en paralelo
    const [mtdRes, caidaRes, estrellaRes] = await Promise.all([
      fetch(API + '/analytics/mtd' + vQuery),
      fetch(API + '/analytics/clientes/caida' + vQuery),
      fetch(API + '/analytics/clientes/mtd' + vQuery) // MTD clientes para Top 20
    ]);
    
    if (mtdRes.ok) renderBloque1((await mtdRes.json()).data);
    if (caidaRes.ok) renderBloque2((await caidaRes.json()).data);
    if (estrellaRes.ok) renderBloque3((await estrellaRes.json()).data);
    
  } catch (e) {
    showToast('Error cargando datos', true);
  } finally {
    $('btn-refresh').classList.remove('spinning');
  }
}

// ── BLOQUE 1: Mis Números ──────────────────────────────────────────────────
function renderBloque1(data) {
  let ventaActual = 0;
  let ventaAnterior = 0;
  
  if (data && data.length > 0) {
    // Si viene agrupado, sumar todo (aunque debería ser 1 fila por el filtro)
    ventaActual = data.reduce((s, r) => s + (r.ventaActual || 0), 0);
    ventaAnterior = data.reduce((s, r) => s + (r.ventaAnterior || 0), 0);
  }
  
  $('kpi-ventas-totales').textContent = fmtMM(ventaActual);
  $('kpi-ventas-sub').textContent = `vs año anterior: ${fmtMM(ventaAnterior)}`;
  
  // Meta
  const metaObj = metas[currentVendedora.toLowerCase()];
  if (metaObj && metaObj.meta_mensual > 0) {
    const metaVal = metaObj.meta_mensual;
    const pct = Math.min(100, Math.round((ventaActual / metaVal) * 100));
    
    $('kpi-meta-pct').textContent = `${pct}%`;
    $('kpi-meta-bar').style.width = `${pct}%`;
    $('kpi-meta-sub').textContent = `Presupuesto: ${fmtMM(metaVal)}`;
    
    if (pct >= 100) {
      $('kpi-meta-bar').style.background = 'linear-gradient(90deg, #27AE60, #2ecc71)';
      $('kpi-meta-pct').style.color = '#27AE60';
    } else {
      $('kpi-meta-bar').style.background = 'linear-gradient(90deg, var(--teal), #34d399)';
      $('kpi-meta-pct').style.color = 'var(--teal)';
    }
  } else {
    $('kpi-meta-pct').textContent = '—';
    $('kpi-meta-bar').style.width = '0%';
    $('kpi-meta-sub').textContent = 'Presupuesto: no definido';
    $('kpi-meta-pct').style.color = 'var(--text-muted)';
  }
}

// ── BLOQUE 2: Fuga de Dinero ───────────────────────────────────────────────
function renderBloque2(data) {
  const container = $('list-caida');
  
  if (!data || data.length === 0) {
    container.innerHTML = `<div class="loading-state">¡Excelente! No tienes clientes con caídas significativas.</div>`;
    return;
  }
  
  container.innerHTML = data.slice(0, 15).map((r, i) => {
    const impacto = r.diferencia; // es negativo
    const pct = r.pctCambio;
    const nit = r.nit;
    
    return `
      <div class="list-row">
        <div class="row-main">
          <div class="row-info">
            <div class="client-name">${r.nombreCliente || 'Cliente Desconocido'}</div>
            <div class="client-nit">NIT: ${nit}</div>
          </div>
          <div class="row-stats">
            <div class="stat-value stat-danger">${fmtMM(impacto)}</div>
            <div class="delta-badge down">${fmtPct(pct)}</div>
          </div>
        </div>
        <button class="btn-expand" onclick="toggleProductos('${nit}', 'panel-${nit}-${i}')">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
          Ver Productos
        </button>
        <div class="productos-panel" id="panel-${nit}-${i}">
          <div style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 10px;">Cargando productos...</div>
        </div>
      </div>
    `;
  }).join('');
}

async function toggleProductos(nit, panelId) {
  const panel = $(panelId);
  const btn = panel.previousElementSibling;
  
  const isOpen = panel.classList.contains('open');
  
  if (isOpen) {
    panel.classList.remove('open');
    btn.classList.remove('open');
    return;
  }
  
  // Abrir y cargar
  panel.classList.add('open');
  btn.classList.add('open');
  
  if (panel.dataset.loaded) return; // Ya cargado
  
  try {
    const res = await fetch(`${API}/analytics/productos/perdidos/${nit}?vendedor=${encodeURIComponent(currentVendedora)}`);
    if (!res.ok) throw new Error('Failed');
    
    const data = (await res.json()).data;
    
    if (!data || data.length === 0) {
      panel.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted); padding: 8px;">No se encontraron productos específicos.</div>`;
    } else {
      panel.innerHTML = data.map(p => `
        <div class="prod-item">
          <div class="prod-name">
            ${p.nombreProducto || p.producto}
            <div class="prod-cant">Cant: ${p.cantHistorica || 0} → ${p.cantReciente || 0} (${fmtPct(p.pctCambioCant)})</div>
          </div>
          <div class="prod-stats">
            <span class="stat-danger">-${fmtPesos(Math.abs(p.impacto))}</span>
            <span class="delta-badge down" style="padding: 2px 4px; font-size: 0.7rem;">${fmtPct(p.pctCambioValor)}</span>
          </div>
        </div>
      `).join('');
    }
    panel.dataset.loaded = 'true';
  } catch(e) {
    panel.innerHTML = `<div style="font-size: 0.8rem; color: var(--danger); padding: 8px;">Error al cargar productos.</div>`;
  }
}

// Global para los botones
window.toggleProductos = toggleProductos;

// ── BLOQUE 3: Clientes Estrella ────────────────────────────────────────────
function renderBloque3(data) {
  const container = $('list-estrella');
  
  if (!data || data.length === 0) {
    container.innerHTML = `<div class="loading-state">Aún no hay compras registradas este mes.</div>`;
    return;
  }
  
  const top20 = data.slice(0, 20);
  
  container.innerHTML = top20.map((r, i) => {
    return `
      <div class="list-row rank-row">
        <div class="rank-badge">${i + 1}</div>
        <div class="row-info">
          <div class="client-name" style="font-size: 0.95rem;">${r.nombreCliente || 'Cliente Desconocido'}</div>
          <div class="client-nit">${r.cantFacturas || 0} facturas</div>
        </div>
        <div class="row-stats">
          <div class="stat-value stat-neutral" style="font-size: 1rem;">${fmtMM(r.totalVenta)}</div>
        </div>
      </div>
    `;
  }).join('');
}

init();
