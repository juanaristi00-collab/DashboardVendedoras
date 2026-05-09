const API_BASE_URL = '';   // <── David: URL pública del servidor (ej: 'https://api.saanye.com')
const API = API_BASE_URL + '/api/v1';
const API_TOKEN = '';       // <── David: token Bearer cuando active auth

async function apiFetch(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (API_TOKEN) headers['Authorization'] = `Bearer ${API_TOKEN}`;
  return fetch(url, { ...options, headers });
}
let currentPin = '';
let metasData = {};

const $ = id => document.getElementById(id);

function showToast(msg, isError = false) {
  let toast = $('toast');
  toast.textContent = msg;
  toast.className = 'toast ' + (isError ? 'error' : '');
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

$('btn-login').addEventListener('click', async () => {
  const pin = $('admin-pin').value;
  if (!pin) return;
  
  // Test PIN with a dummy save (or just load metas and assume PIN is needed later)
  // Actually, let's load vendedoras and metas, and we'll use PIN when saving.
  currentPin = pin;
  
  try {
    const [vendRes, metasRes] = await Promise.all([
      apiFetch(API + '/analytics/vendedoras'),
      apiFetch(API + '/analytics/metas')
    ]);
    
    if (!vendRes.ok) {
        console.error("Error cargando vendedoras:", vendRes.status);
        throw new Error('Error cargando vendedoras');
    }
    
    const vendData = await vendRes.json();
    metasData = await metasRes.json();
    
    console.log("Vendedoras en admin:", vendData);
    console.log("Metas en admin (Supabase):", metasData);
    
    renderMetasList(vendData.data);
    
    $('login-section').style.display = 'none';
    $('metas-section').style.display = 'block';
  } catch (e) {
    console.error("Admin fetch error:", e);
    showToast('Error de conexión', true);
  }
});

function renderMetasList(vendedoras) {
  const list = $('metas-list');
  list.innerHTML = '';
  
  vendedoras.forEach(v => {
    if (!v.vendedor) return;
    
    const login = v.vendedor.toLowerCase();
    const meta = metasData[login]?.meta_mensual || '';
    
    const row = document.createElement('div');
    row.className = 'vendedora-row';
    row.innerHTML = `
      <div class="vendedora-name">@${login}</div>
      <div class="vendedora-meta">
        <input type="number" class="form-control meta-input" data-login="${login}" value="${meta}" placeholder="Meta en $" />
      </div>
    `;
    list.appendChild(row);
  });
}

$('btn-save').addEventListener('click', async () => {
  const inputs = document.querySelectorAll('.meta-input');
  const newMetas = {};
  
  inputs.forEach(input => {
    const login = input.dataset.login;
    const val = parseFloat(input.value);
    if (!isNaN(val) && val > 0) {
      newMetas[login] = { meta_mensual: val };
    }
  });
  
  $('btn-save').disabled = true;
  $('btn-save').textContent = 'Guardando...';
  
  try {
    const res = await apiFetch(API + '/analytics/metas?pin=' + encodeURIComponent(currentPin), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newMetas)
    });
    
    if (res.ok) {
      showToast('Metas guardadas correctamente');
    } else {
      showToast('PIN incorrecto o error al guardar', true);
    }
  } catch (e) {
    showToast('Error de conexión', true);
  } finally {
    $('btn-save').disabled = false;
    $('btn-save').textContent = 'Guardar Metas';
  }
});
