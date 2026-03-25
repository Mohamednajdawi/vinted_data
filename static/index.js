let chartInstances = {};
let lastDashboardData = null;
let lastInventoryData = null;
let catSortCol = 'count';
let catSortDir = 'desc';

function destroyChart(id) {
    if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

document.addEventListener('DOMContentLoaded', () => openSyncModal());

async function loadDashboardData(url, method = 'GET', body = null) {
    const options = { method, headers: {} };
    if (body) { options.headers['Content-Type'] = 'application/json'; options.body = JSON.stringify(body); }
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    if (result.success === false) throw new Error(result.error || 'Vinted API Error');
    
    let data = result;
    if (result.stats !== undefined) {
        data = result.stats;
    }
    return data;
}

function renderDashboard(data) {
    console.log('[Dashboard] data:', data);
    if (!data || !data.monthly_sales) {
        const raw = data?._debug?.raw_fetched ?? 'unknown';
        alert(`Sync received ${raw} orders. Data could not be rendered — check the browser console.`);
        return;
    }

    const currency = data.currency || 'EUR';
    const fmt = v => `€${(v||0).toFixed(2)}`;

    // KPI stats
    document.getElementById('total_revenue').textContent = fmt(data.total_revenue);
    document.getElementById('total_orders').textContent = data.total_orders || 0;
    document.getElementById('pending_revenue').textContent = fmt(data.pending_revenue);
    document.getElementById('aov').textContent = fmt(data.aov);
    document.getElementById('best_month').textContent = data.best_month || '—';
    document.getElementById('worst_month').textContent = data.worst_month || '—';
    document.getElementById('syncTag').innerHTML = `<span style="color:#34d399">●</span> Updated: ${new Date().toLocaleTimeString()}`;

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    // -- 1. Monthly Revenue Line Chart --
    const months = Object.keys(data.monthly_sales);
    const monthVals = Object.values(data.monthly_sales);
    destroyChart('salesChart');
    const ctxS = document.getElementById('salesChart').getContext('2d');
    const gradS = ctxS.createLinearGradient(0, 0, 0, 280);
    gradS.addColorStop(0, 'rgba(56,189,248,0.4)'); gradS.addColorStop(1, 'rgba(56,189,248,0)');
    chartInstances['salesChart'] = new Chart(ctxS, {
        type: 'line',
        data: { labels: months, datasets: [{ label: 'Revenue (€)', data: monthVals, borderColor: '#38bdf8', backgroundColor: gradS, borderWidth: 3, fill: true, tension: 0.4, pointBackgroundColor: '#fff', pointBorderColor: '#38bdf8', pointRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } } }
    });

    // -- 2. Cumulative Revenue Line Chart --
    const cumMonths = Object.keys(data.cumulative_revenue || {});
    const cumVals = Object.values(data.cumulative_revenue || {});
    destroyChart('cumulativeChart');
    const ctxC = document.getElementById('cumulativeChart').getContext('2d');
    const gradC = ctxC.createLinearGradient(0, 0, 0, 280);
    gradC.addColorStop(0, 'rgba(52,211,153,0.4)'); gradC.addColorStop(1, 'rgba(52,211,153,0)');
    chartInstances['cumulativeChart'] = new Chart(ctxC, {
        type: 'line',
        data: { labels: cumMonths, datasets: [{ label: 'Cumulative (€)', data: cumVals, borderColor: '#34d399', backgroundColor: gradC, borderWidth: 3, fill: true, tension: 0.4, pointRadius: 3 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } } }
    });

    // -- 3. Day of Week Bar Chart --
    const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    const dayVals = days.map(d => (data.day_of_week_sales || {})[d] || 0);
    destroyChart('dayChart');
    const ctxD = document.getElementById('dayChart').getContext('2d');
    const gradD = ctxD.createLinearGradient(0, 0, 0, 280);
    gradD.addColorStop(0, '#c084fc'); gradD.addColorStop(1, '#818cf8');
    chartInstances['dayChart'] = new Chart(ctxD, {
        type: 'bar',
        data: { labels: days.map(d => d.slice(0,3)), datasets: [{ data: dayVals, backgroundColor: gradD, borderRadius: 6, borderSkipped: false }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { display: false, beginAtZero: true }, x: { grid: { display: false } } } }
    });

    // -- 4. Hour of Day Bar Chart --
    const hours = Object.keys(data.hour_of_day || {}).map(Number).sort((a,b)=>a-b);
    const hourVals = hours.map(h => (data.hour_of_day || {})[h] || 0);
    const hourLabels = hours.map(h => `${String(h).padStart(2,'0')}:00`);
    destroyChart('hourChart');
    const ctxH = document.getElementById('hourChart').getContext('2d');
    const gradH = ctxH.createLinearGradient(0, 0, 0, 280);
    gradH.addColorStop(0, '#f472b6'); gradH.addColorStop(1, '#e879f9');
    chartInstances['hourChart'] = new Chart(ctxH, {
        type: 'bar',
        data: { labels: hourLabels, datasets: [{ data: hourVals, backgroundColor: gradH, borderRadius: 4, borderSkipped: false }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { display: false, beginAtZero: true }, x: { grid: { display: false }, ticks: { maxRotation: 60, font: { size: 10 } } } } }
    });

    // -- 5. Price Distribution Doughnut --
    const priceLabels = Object.keys(data.price_distribution || {});
    const priceVals = Object.values(data.price_distribution || {});
    destroyChart('priceChart');
    chartInstances['priceChart'] = new Chart(document.getElementById('priceChart'), {
        type: 'doughnut',
        data: { labels: priceLabels, datasets: [{ data: priceVals, backgroundColor: ['#38bdf8','#34d399','#c084fc','#f472b6','#fb923c','#facc15','#818cf8'], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#94a3b8', boxWidth: 10, padding: 10 } } } }
    });

    lastDashboardData = data;
    
    // Populate Status Filter
    const filter = document.getElementById('statusFilter');
    if (filter) {
        const uniqueStatuses = [...new Set((data.latest_sales || []).map(s => s.status))].sort();
        filter.innerHTML = '<option value="all">All Statuses</option>';
        uniqueStatuses.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s;
            opt.textContent = s;
            filter.appendChild(opt);
        });
    }

    renderRecentSales(data.latest_sales || []);

    // -- Top 10 Items Table --
    const tbody2 = document.getElementById('top_items_body');
    tbody2.innerHTML = '';
    (data.top_items || []).forEach(item => {
        tbody2.insertAdjacentHTML('beforeend', `
          <tr>
            <td class="item-name">${String(item.title).substring(0,28)}${item.title.length>28?'…':''}</td>
            <td style="color:#94a3b8">${item.date_str}</td>
            <td style="font-weight:600;color:#34d399">€${(+item.price).toFixed(2)}</td>
          </tr>`);
    });
}

window.filterTransactions = (status) => {
    if (!lastDashboardData || !lastDashboardData.latest_sales) return;
    const filtered = status === 'all' 
        ? lastDashboardData.latest_sales 
        : lastDashboardData.latest_sales.filter(s => s.status === status);
    renderRecentSales(filtered);
};

const renderRecentSales = (salesList) => {
    const tbody = document.getElementById('recent_sales_body');
    if (!tbody) return;
    tbody.innerHTML = '';
    salesList.forEach(sale => {
        const isOk = /beendet|erfolgreich|completed|terminé|livré/i.test(sale.status);
        tbody.insertAdjacentHTML('beforeend', `
          <tr>
            <td class="item-name">${String(sale.title).substring(0,28)}${sale.title.length>28?'…':''}</td>
            <td style="color:#94a3b8">${sale.date_str}</td>
            <td><span class="status-badge ${isOk?'status-success':'status-pending'}">${isOk?'Completed':'Processing'}</span></td>
            <td style="font-weight:600">€${(+sale.price).toFixed(2)}</td>
          </tr>`);
    });
};

function openSyncModal() { document.getElementById('syncModal').classList.add('active'); }
function closeSyncModal() { document.getElementById('syncModal').classList.remove('active'); document.getElementById('syncStatus').style.display='none'; }

async function syncLiveData() {
    const domain = document.getElementById('vintedDomain').value.trim();
    const cookie = document.getElementById('vintedCookie').value.trim();
    if (!domain || !cookie) { alert('Domain and Cookie are required'); return; }
    const statusEl = document.getElementById('syncStatus');
    statusEl.style.display = 'block'; statusEl.style.color = '#38bdf8';
    statusEl.textContent = 'Downloading your full sales history...';
    try {
        const data = await loadDashboardData('/api/v1/live_sync', 'POST', { domain, cookie });
        renderDashboard(data);
        statusEl.textContent = 'Sync completed!'; statusEl.style.color = '#34d399';
        setTimeout(closeSyncModal, 1200);
    } catch(e) {
        statusEl.textContent = e.message; statusEl.style.color = '#f43f5e';
    }
}

function showTab(tabName) {
    document.getElementById('sales-section').style.display = tabName === 'sales' ? 'block' : 'none';
    document.getElementById('inventory-section').style.display = tabName === 'inventory' ? 'block' : 'none';
    document.getElementById('tab-sales').classList.toggle('active', tabName === 'sales');
    document.getElementById('tab-inventory').classList.toggle('active', tabName === 'inventory');
}

async function syncInventory() {
    const domain = document.getElementById('vintedDomain').value.trim();
    const cookie = document.getElementById('vintedCookie').value.trim();
    if (!domain || !cookie) { alert('Please connect your account (cookie) in the Sales tab first or use the modal.'); openSyncModal(); return; }
    
    const statusEl = document.getElementById('inv-status');
    statusEl.textContent = 'Syncing your active inventory...';
    
    try {
        console.log('[Inventory] Initiating sync for', domain);
        const data = await loadDashboardData('/api/v1/live_inventory_sync', 'POST', { domain, cookie });
        console.log('[Inventory] Received sync data:', data);
        renderInventory(data);
        statusEl.textContent = 'Inventory synced successfully.';
    } catch(e) {
        console.error('[Inventory] Sync failed:', e);
        statusEl.textContent = `Error: ${e.message}`;
        statusEl.style.color = '#f43f5e';
    }
}

function renderInventory(data) {
    try {
        console.log('[Inventory] Starting renderInventory. Raw data:', data);
        
        // Handle possible nested stats
        let stats = data;
        if (data && data.stats && data.total_items === undefined) {
            console.log('[Inventory] Using nested .stats object');
            stats = data.stats;
        }

        if (!stats || stats.total_items === undefined) {
            console.error('[Inventory] Invalid data structure for renderInventory:', stats);
            return;
        }

        console.log('[Inventory] Rendering KPIs...');
        const safeSet = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
            else console.warn(`[Inventory] Element #${id} not found`);
        };

        const kpis = document.getElementById('inv-kpis');
        if (kpis) kpis.style.display = 'grid';
        
        const charts = document.getElementById('inv-charts');
        if (charts) charts.style.display = 'grid';
        
        const tableWrap = document.getElementById('inv-table-wrap');
        if (tableWrap) tableWrap.style.display = 'block';
        
        const engWrap = document.getElementById('inv-engagement');
        if (engWrap) engWrap.style.display = 'grid';

        console.log('[Inventory] renderInventory called with stats:', stats);
        if (!stats || Object.keys(stats).length === 0) {
            console.error('[Inventory] Stats object is empty or null!');
        }

        const fmt = v => `€${(v||0).toFixed(2)}`;
        safeSet('inv-total', stats.total_items || 0);
        safeSet('inv-potential', fmt(stats.total_potential_revenue));
        safeSet('inv-avg', fmt(stats.avg_listing_price));
        safeSet('inv-favs', stats.total_favourites != null ? stats.total_favourites : '—');
        safeSet('inv-views', stats.total_views != null ? stats.total_views : '—');
        safeSet('inv-days', stats.avg_days_listed != null ? `${stats.avg_days_listed}d` : '—');
        safeSet('inv-er', (stats.avg_engagement_rate || 0).toFixed(1) + '%');
        
        // Velocity logic
        const velocity = stats.avg_days_listed > 0 ? (stats.total_favourites / stats.avg_days_listed).toFixed(2) : '0.00';
        safeSet('inv-velocity', velocity);

        console.log('[Inventory] Rendering charts...');
        // Bar Chart
        if (document.getElementById('invPriceChart')) {
            const priceLabels = Object.keys(stats.price_distribution || {});
            const priceVals = Object.values(stats.price_distribution || {});
            destroyChart('invPriceChart');
            const ctxIP = document.getElementById('invPriceChart').getContext('2d');
            chartInstances['invPriceChart'] = new Chart(ctxIP, {
                type: 'bar',
                data: { labels: priceLabels, datasets: [{ data: priceVals, backgroundColor: '#38bdf8', borderRadius: 6 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true }, x: { grid: { display: false } } } }
            });
        }

        // Doughnut Chart
        if (document.getElementById('invCatChart')) {
            const catSource = Object.keys(stats.brands || {}).length > 0 ? stats.brands : stats.categories;
            const catHeader = Object.keys(stats.brands || {}).length > 0 ? 'Brand Mix' : 'Categories';
            const headerEl = document.getElementById('invCatHeader');
            if (headerEl) headerEl.textContent = catHeader;
            
            const catLabels = Object.keys(catSource || {});
            const catVals = Object.values(catSource || {});
            destroyChart('invCatChart');
            const ctxIC = document.getElementById('invCatChart').getContext('2d');
            chartInstances['invCatChart'] = new Chart(ctxIC, {
                type: 'doughnut',
                data: { labels: catLabels, datasets: [{ data: catVals, backgroundColor: ['#c084fc','#34d399','#38bdf8','#f472b6','#fb923c','#facc15','#818cf8','#a78bfa'], borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'right', labels: { color: '#94a3b8', boxWidth: 10, padding: 8 } } } }
            });
        }

        // Status Distribution Chart
        if (document.getElementById('invStatusChart') && stats.status_distribution) {
            const sLabels = Object.keys(stats.status_distribution);
            const sVals = Object.values(stats.status_distribution);
            const sColors = sLabels.map(l => {
                if (l === 'Available') return '#34d399';
                if (l === 'Sold') return '#f472b6';
                if (l === 'Hidden') return '#94a3b8';
                if (l === 'Reserved') return '#fb923c';
                return '#64748b';
            });
            destroyChart('invStatusChart');
            const ctxIS = document.getElementById('invStatusChart').getContext('2d');
            chartInstances['invStatusChart'] = new Chart(ctxIS, {
                type: 'doughnut',
                data: { labels: sLabels, datasets: [{ data: sVals, backgroundColor: sColors, borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'right', labels: { color: '#94a3b8', boxWidth: 10, padding: 8 } } } }
            });
        }

        console.log('[Inventory] Rendering tables...');
        const getChip = er => {
            if (er > 10) return '<span class="insight-chip chip-high">🔥 Viral</span>';
            if (er > 4) return '<span class="insight-chip chip-mid">💎 Good</span>';
            return '<span class="insight-chip chip-low">🧊 Static</span>';
        };

        const engRow = (item) => {
            if (!item) return '';
            const p = (+item.price_val || 0).toFixed(2);
            const brand = item.brand ? `<span style="color:#94a3b8;font-size:11px"> · ${item.brand}</span>` : '';
            const title = String(item.title || 'Unknown');
            const er = item.engagement_rate || 0;
            const statusClass = `badge-${(item.stock_status || 'available').toLowerCase()}`;
            const statusBadge = `<span class="status-badge ${statusClass}">${item.stock_status || 'Available'}</span>`;
            
            return `<tr>
              <td class="item-name">${title.substring(0,25)}${title.length>25?'…':''}${brand}${statusBadge}${getChip(er)}</td>
              <td style="color:#34d399;font-weight:600">€${p}</td>
              <td style="color:#f472b6">${item.favs != null ? '❤ '+item.favs : '—'}</td>
              <td style="color:#38bdf8">${item.views != null ? '👁 '+item.views : '—'}</td>
            </tr>`;
        };

        const renderTableBody = (id, items) => {
            const body = document.getElementById(id);
            if (body) {
                body.innerHTML = '';
                if (!items || items.length === 0) {
                    body.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:20px">No items found</td></tr>';
                } else {
                    items.forEach(item => body.insertAdjacentHTML('beforeend', engRow(item)));
                }
            }
        };
        lastInventoryData = stats;
        renderCatTable();

        try {
            console.log('[Inventory] Rendering Most Liked...');
            renderTableBody('inv-liked-body', stats.most_liked);
            console.log('[Inventory] Rendering Most Viewed...');
            renderTableBody('inv-viewed-body', stats.most_viewed);
            console.log('[Inventory] Rendering Top Listings...');
            renderTableBody('inv-top-body', stats.top_listings);
        } catch (e) {
            console.error('[Inventory] Table rendering failed:', e);
        }

        console.log('[Inventory] renderInventory completed successfully.');
    } catch (err) {
        console.error('[Inventory] Critical error in renderInventory:', err);
    }
};

window.sortCat = (col) => {
    if (!lastInventoryData || !lastInventoryData.category_performance) return;
    
    if (catSortCol === col) {
        catSortDir = catSortDir === 'desc' ? 'asc' : 'desc';
    } else {
        catSortCol = col;
        catSortDir = 'desc';
    }
    
    const data = lastInventoryData.category_performance;
    data.sort((a, b) => {
        let valA = a[col];
        let valB = b[col];
        
        // Handle strings (category names)
        if (typeof valA === 'string') {
            return catSortDir === 'asc' 
                ? String(valA).localeCompare(String(valB)) 
                : String(valB).localeCompare(String(valA));
        }
        
        // Handle numbers
        return catSortDir === 'asc' ? (valA - valB) : (valB - valA);
    });
    
    renderCatTable();
};

const renderCatTable = () => {
    if (!lastInventoryData || !lastInventoryData.category_performance) return;
    const catBody = document.getElementById('inv-cat-perf-body');
    if (!catBody) return;
    
    catBody.innerHTML = '';
    lastInventoryData.category_performance.forEach(c => {
        const getChip = er => {
            if (er > 10) return '<span class="insight-chip chip-high">🔥 Viral</span>';
            if (er > 4) return '<span class="insight-chip chip-mid">💎 Good</span>';
            return '<span class="insight-chip chip-low">🧊 Static</span>';
        };
        catBody.insertAdjacentHTML('beforeend', `
            <tr>
                <td style="font-weight:600;color:#e2e8f0">${c.catalog_title || c.category_title || 'Other'}</td>
                <td>${c.count}</td>
                <td>€${(+c.price_val || 0).toFixed(2)}</td>
                <td style="color:#38bdf8">👁 ${c.view_count}</td>
                <td style="color:#f472b6">❤ ${c.favourite_count}</td>
                <td style="font-weight:600">${c.er}% ${getChip(c.er)}</td>
            </tr>
        `);
    });
    const wrap = document.getElementById('inv-cat-perf-wrap');
    if (wrap) wrap.style.display = 'block';
};




