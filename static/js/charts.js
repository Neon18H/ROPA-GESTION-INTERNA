(function () {
  if (typeof Chart === 'undefined') return;

  function parseJsonScript(id) {
    const node = document.getElementById(id);
    if (!node) return null;
    try {
      return JSON.parse(node.textContent || '{}');
    } catch (error) {
      return null;
    }
  }

  const dashboardData = parseJsonScript('dashboard-chart-data');
  if (dashboardData) {
    const incomeCtx = document.getElementById('dashboardIncomeChart');
    if (incomeCtx) {
      new Chart(incomeCtx, {
        type: 'line',
        data: {
          labels: dashboardData.incomeDaily.labels || [],
          datasets: [{
            label: 'Ingresos',
            data: dashboardData.incomeDaily.values || [],
            borderColor: '#2f6fed',
            backgroundColor: 'rgba(47,111,237,0.15)',
            fill: true,
            tension: 0.25,
          }],
        },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }

    const topCtx = document.getElementById('dashboardTopProductsChart');
    if (topCtx) {
      new Chart(topCtx, {
        type: 'bar',
        data: {
          labels: dashboardData.topProducts.labels || [],
          datasets: [{ label: 'Unidades', data: dashboardData.topProducts.values || [], backgroundColor: '#198754' }],
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
      });
    }

    const brandCtx = document.getElementById('dashboardBrandChart');
    if (brandCtx) {
      new Chart(brandCtx, {
        type: 'doughnut',
        data: {
          labels: dashboardData.brandSplit.labels || [],
          datasets: [{ data: dashboardData.brandSplit.values || [] }],
        },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }
  }

  const financeData = parseJsonScript('finance-chart-data');
  if (financeData) {
    const ieCtx = document.getElementById('financeIncomeExpenseChart');
    if (ieCtx) {
      new Chart(ieCtx, {
        type: 'line',
        data: {
          labels: financeData.incomeExpense.labels || [],
          datasets: [
            { label: 'Ingresos', data: financeData.incomeExpense.income || [], borderColor: '#0d6efd', tension: 0.2 },
            { label: 'Gastos', data: financeData.incomeExpense.expense || [], borderColor: '#dc3545', tension: 0.2 },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }

    const profitCtx = document.getElementById('financeProfitWeekChart');
    if (profitCtx) {
      new Chart(profitCtx, {
        type: 'bar',
        data: { labels: financeData.profitWeek.labels || [], datasets: [{ label: 'Utilidad', data: financeData.profitWeek.values || [], backgroundColor: '#20c997' }] },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }

    const supplierCtx = document.getElementById('financeSupplierChart');
    if (supplierCtx) {
      new Chart(supplierCtx, {
        type: 'doughnut',
        data: { labels: financeData.supplier.labels || [], datasets: [{ data: financeData.supplier.values || [] }] },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }
  }
})();
