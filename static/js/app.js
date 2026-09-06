/**
 * PriceTracker - Laravel Light Mode Application Logic
 */

let allProducts = [];
let activeFilter = 'all';
let priceChartInstance = null;

// DOM Elements
const productsGrid = document.getElementById('productsGrid');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearchBtn');
const filterTabs = document.querySelectorAll('.filter-btn');
const visibleCountBadge = document.getElementById('visibleCountBadge');
const refreshAllBtn = document.getElementById('refreshAllBtn');
const refreshAllIcon = document.getElementById('refreshAllIcon');

// Metrics
const metricTotalProducts = document.getElementById('metricTotalProducts');
const metricDealsHit = document.getElementById('metricDealsHit');
const metricTotalHistory = document.getElementById('metricTotalHistory');
const metricActiveAlerts = document.getElementById('metricActiveAlerts');

// Modals
const productModal = document.getElementById('productModal');
const productForm = document.getElementById('productForm');
const openAddModalBtn = document.getElementById('openAddModalBtn');
const emptyAddBtn = document.getElementById('emptyAddBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const saveProductBtn = document.getElementById('saveProductBtn');
const saveBtnText = document.getElementById('saveBtnText');
const saveBtnSpinner = document.getElementById('saveBtnSpinner');

const historyModal = document.getElementById('historyModal');
const closeHistoryModalBtn = document.getElementById('closeHistoryModalBtn');
const historyProductTitle = document.getElementById('historyProductTitle');
const historyProductSub = document.getElementById('historyProductSub');
const histTargetPrice = document.getElementById('histTargetPrice');
const histLowestPrice = document.getElementById('histLowestPrice');
const histCurrentPrice = document.getElementById('histCurrentPrice');
const historyTableBody = document.getElementById('historyTableBody');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  fetchProducts();
  setupEventListeners();
});

function setupEventListeners() {
  // Add Modal
  openAddModalBtn?.addEventListener('click', openAddModal);
  emptyAddBtn?.addEventListener('click', openAddModal);
  closeModalBtn?.addEventListener('click', closeAddModal);
  cancelModalBtn?.addEventListener('click', closeAddModal);
  productForm?.addEventListener('submit', handleSaveProduct);

  // History Modal
  closeHistoryModalBtn?.addEventListener('click', closeHistoryModal);

  // Search
  searchInput?.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    clearSearchBtn.style.display = val ? 'block' : 'none';
    renderProducts();
  });
  clearSearchBtn?.addEventListener('click', () => {
    searchInput.value = '';
    clearSearchBtn.style.display = 'none';
    renderProducts();
  });

  // Filter Tabs
  filterTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      filterTabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      activeFilter = tab.dataset.filter;
      renderProducts();
    });
  });

  // Refresh All
  refreshAllBtn?.addEventListener('click', handleRefreshAll);

  // Close modals on escape key or backdrop click
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAddModal();
      closeHistoryModal();
    }
  });
  [productModal, historyModal].forEach((modal) => {
    modal?.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeAddModal();
        closeHistoryModal();
      }
    });
  });
}

// --- API Data Fetching ---
async function fetchProducts() {
  setLoading(true);
  try {
    const res = await fetch('/api/v1/products/');
    if (!res.ok) throw new Error(`Server returned status ${res.status}`);
    allProducts = await res.json();
    renderProducts();
    updateMetrics();
  } catch (err) {
    showToast(`Failed to load products: ${err.message}`, 'error');
  } finally {
    setLoading(false);
  }
}

// --- Metrics Calculation ---
function updateMetrics() {
  const total = allProducts.length;
  const dealsHit = allProducts.filter(
    (p) => p.current_price !== null && p.current_price <= p.target_price
  ).length;
  const activeAlerts = allProducts.filter((p) => p.is_active).length;

  metricTotalProducts.textContent = total;
  metricDealsHit.textContent = dealsHit;
  metricActiveAlerts.textContent = activeAlerts;
  metricTotalHistory.textContent = `${total}+`;
}

// --- Render Products Grid ---
function renderProducts() {
  const query = searchInput.value.toLowerCase().trim();

  const filtered = allProducts.filter((p) => {
    const matchesSearch =
      !query ||
      p.name.toLowerCase().includes(query) ||
      p.url.toLowerCase().includes(query);

    if (!matchesSearch) return false;
    if (activeFilter === 'deals') {
      return p.current_price !== null && p.current_price <= p.target_price;
    }
    if (activeFilter === 'active') {
      return p.is_active === true;
    }
    return true;
  });

  visibleCountBadge.textContent = `${filtered.length} Product${filtered.length === 1 ? '' : 's'}`;

  if (allProducts.length === 0) {
    emptyState.style.display = 'block';
    productsGrid.style.display = 'none';
    return;
  }

  emptyState.style.display = 'none';
  productsGrid.style.display = 'grid';

  if (filtered.length === 0) {
    productsGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
        <i class="fa-solid fa-filter-circle-xmark" style="font-size: 32px; margin-bottom: 8px; color: var(--text-light);"></i>
        <p>No products match your search query or filter.</p>
      </div>
    `;
    return;
  }

  productsGrid.innerHTML = filtered
    .map((product) => {
      const isDeal =
        product.current_price !== null && product.current_price <= product.target_price;
      const currency = product.currency || 'USD';
      const formattedCurrent =
        product.current_price !== null
          ? `${currency} ${Number(product.current_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          : 'Pending Scrape';
      const formattedTarget = `${currency} ${Number(product.target_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

      let domain = 'Store Link';
      try {
        domain = new URL(product.url).hostname.replace('www.', '');
      } catch (e) {}

      const lastCheckedText = product.last_checked_at
        ? new Date(product.last_checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : 'Just now';

      return `
        <article class="product-card ${isDeal ? 'deal-hit' : ''}" id="card-${product.id}">
          <div>
            <div class="card-top">
              <span class="domain-pill" title="${product.url}">
                <i class="fa-solid fa-link"></i> ${domain}
              </span>
              <span class="badge-status ${isDeal ? 'badge-deal' : 'badge-tracking'}">
                ${isDeal ? '🎯 Target Reached' : 'Tracking'}
              </span>
            </div>

            <h3 class="product-name" title="${escapeHtml(product.name)}">
              ${escapeHtml(product.name)}
            </h3>

            <div class="price-box">
              <div class="price-col">
                <span class="price-label">Current Price</span>
                <span class="current-price-val ${isDeal ? 'deal' : ''}">${formattedCurrent}</span>
              </div>
              <div class="price-col" style="text-align: right;">
                <span class="price-label">Target Alert</span>
                <span class="target-price-val">${formattedTarget}</span>
              </div>
            </div>

            <div class="card-meta">
              <span><i class="fa-regular fa-clock"></i> ${lastCheckedText}</span>
              <span><i class="fa-solid fa-bell"></i> ${product.is_active ? 'Active' : 'Paused'}</span>
            </div>
          </div>

          <div class="card-actions">
            <button class="btn btn-default btn-action" onclick="checkProductNow(${product.id})" id="btn-check-${product.id}">
              <i class="fa-solid fa-arrows-rotate"></i> Check Price
            </button>
            <button class="btn btn-default btn-action" onclick="openHistoryModal(${product.id})">
              <i class="fa-solid fa-chart-line"></i> History
            </button>
            <a href="${product.url}" target="_blank" rel="noopener noreferrer" class="btn btn-default btn-icon-only" title="Open Store Page">
              <i class="fa-solid fa-arrow-up-right-from-square"></i>
            </a>
            <button class="btn btn-default btn-icon-only" onclick="deleteProduct(${product.id})" title="Delete Product">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </div>
        </article>
      `;
    })
    .join('');
}

// --- Add / Save Product Handler ---
function openAddModal() {
  productForm.reset();
  document.getElementById('editProductId').value = '';
  document.getElementById('modalHeading').innerHTML = '<i class="fa-solid fa-circle-plus text-primary"></i> Track New Product';
  saveBtnText.innerHTML = '<i class="fa-solid fa-check"></i> Save &amp; Scrape';
  productModal.style.display = 'flex';
  document.getElementById('productName').focus();
}

function closeAddModal() {
  productModal.style.display = 'none';
}

async function handleSaveProduct(e) {
  e.preventDefault();
  const name = document.getElementById('productName').value.trim();
  const url = document.getElementById('productUrl').value.trim();
  const target_price = parseFloat(document.getElementById('targetPrice').value);
  const currency = document.getElementById('productCurrency').value;

  saveBtnSpinner.style.display = 'inline-block';
  saveProductBtn.disabled = true;

  try {
    const res = await fetch('/api/v1/products/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, url, target_price, currency }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail?.[0]?.msg || err.detail || 'Failed to save product');
    }

    const created = await res.json();
    closeAddModal();
    showToast(`Added "${name}" to tracking successfully!`, 'success');
    await fetchProducts();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    saveBtnSpinner.style.display = 'none';
    saveProductBtn.disabled = false;
  }
}

// --- Check Price On Demand ---
async function checkProductNow(productId) {
  const btn = document.getElementById(`btn-check-${productId}`);
  if (btn) {
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';
    btn.disabled = true;
  }

  try {
    const res = await fetch(`/api/v1/products/${productId}/check-now`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to scrape price');
    const data = await res.json();

    if (data.status === 'success') {
      showToast(
        data.alert_triggered
          ? `🎉 Price drop alert! Price is now $${data.new_price} (Target reached)`
          : `Updated! Price is $${data.new_price}`,
        data.is_price_drop ? 'success' : 'info'
      );
    } else {
      showToast(`Notice: ${data.message}`, 'info');
    }
    await fetchProducts();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Check Price';
      btn.disabled = false;
    }
  }
}

// --- Check All Prices ---
async function handleRefreshAll() {
  if (allProducts.length === 0) return;
  refreshAllIcon.classList.add('fa-spin');
  refreshAllBtn.disabled = true;

  showToast(`Checking prices for ${allProducts.length} items...`, 'info');

  for (const p of allProducts) {
    try {
      await fetch(`/api/v1/products/${p.id}/check-now`, { method: 'POST' });
    } catch (e) {}
  }

  await fetchProducts();
  refreshAllIcon.classList.remove('fa-spin');
  refreshAllBtn.disabled = false;
  showToast('All product prices updated!', 'success');
}

// --- Delete Product ---
async function deleteProduct(productId) {
  const p = allProducts.find((item) => item.id === productId);
  if (!confirm(`Are you sure you want to stop tracking "${p ? p.name : 'this item'}"?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/v1/products/${productId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete product');
    showToast('Product removed from tracking.', 'info');
    await fetchProducts();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// --- Price History Modal & Chart.js (Laravel Light Palette) ---
async function openHistoryModal(productId) {
  const product = allProducts.find((p) => p.id === productId);
  if (!product) return;

  historyProductTitle.textContent = product.name;
  historyProductSub.textContent = `Target Alert: ${product.currency} ${product.target_price.toLocaleString()}`;
  histTargetPrice.textContent = `${product.currency} ${product.target_price.toLocaleString()}`;
  histCurrentPrice.textContent = product.current_price
    ? `${product.currency} ${product.current_price.toLocaleString()}`
    : '-';

  historyModal.style.display = 'flex';

  try {
    const res = await fetch(`/api/v1/products/${productId}/history`);
    if (!res.ok) throw new Error('Could not load history');
    const historyData = await res.json();

    renderHistoryChartAndTable(product, historyData);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderHistoryChartAndTable(product, history) {
  const sorted = [...history].sort(
    (a, b) => new Date(a.recorded_at) - new Date(b.recorded_at)
  );

  const lowest = sorted.length > 0 ? Math.min(...sorted.map((h) => h.price)) : product.current_price;
  histLowestPrice.textContent = lowest ? `${product.currency} ${lowest.toLocaleString()}` : '-';

  const newestFirst = [...sorted].reverse();
  historyTableBody.innerHTML = newestFirst
    .map((h) => {
      const isBelow = h.price <= product.target_price;
      const dateStr = new Date(h.recorded_at).toLocaleString();
      return `
        <tr>
          <td>${dateStr}</td>
          <td><strong>${h.currency} ${h.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></td>
          <td>
            <span class="badge-status ${isBelow ? 'badge-deal' : 'badge-tracking'}">
              ${isBelow ? 'At/Below Target' : 'Above Target'}
            </span>
          </td>
        </tr>
      `;
    })
    .join('');

  // Chart.js Light Theme Configuration
  const ctx = document.getElementById('priceHistoryChart').getContext('2d');
  if (priceChartInstance) {
    priceChartInstance.destroy();
  }

  const labels = sorted.map((h) =>
    new Date(h.recorded_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  );
  const dataPoints = sorted.map((h) => h.price);

  const gradient = ctx.createLinearGradient(0, 0, 0, 220);
  gradient.addColorStop(0, 'rgba(255, 45, 32, 0.15)');
  gradient.addColorStop(1, 'rgba(255, 45, 32, 0.0)');

  priceChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.length > 0 ? labels : ['Current'],
      datasets: [
        {
          label: 'Recorded Price',
          data: dataPoints.length > 0 ? dataPoints : [product.current_price || product.target_price],
          borderColor: '#ff2d20', // Laravel signature red
          backgroundColor: gradient,
          fill: true,
          tension: 0.3,
          pointBackgroundColor: '#ff2d20',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: 'Target Threshold',
          data: Array(labels.length || 1).fill(product.target_price),
          borderColor: '#10b981', // Emerald green target line
          borderDash: [5, 5],
          borderWidth: 2,
          fill: false,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#475569',
            font: { family: 'Nunito', size: 12, weight: '600' },
          },
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#ffffff',
          bodyColor: '#f1f5f9',
          borderColor: '#cbd5e1',
          borderWidth: 1,
          padding: 10,
        },
      },
      scales: {
        x: {
          ticks: { color: '#64748b', font: { family: 'Nunito', size: 11 } },
          grid: { color: '#f1f5f9' },
        },
        y: {
          ticks: { color: '#64748b', font: { family: 'Nunito', size: 11 } },
          grid: { color: '#f1f5f9' },
        },
      },
    },
  });
}

function closeHistoryModal() {
  historyModal.style.display = 'none';
}

// --- Helpers & Toasts ---
function setLoading(isLoading) {
  loadingState.style.display = isLoading ? 'block' : 'none';
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const iconMap = {
    success: 'fa-circle-check text-success',
    error: 'fa-circle-exclamation text-danger',
    info: 'fa-circle-info text-info',
  };
  const icon = iconMap[type] || 'fa-bell text-primary';

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
