(function () {
  const salesLineNode = document.getElementById('sales-line-data');
  const topCustomersNode = document.getElementById('top-customers-chart-data');

  if (!salesLineNode || !topCustomersNode || typeof Chart === 'undefined') {
    return;
  }

  const salesData = JSON.parse(salesLineNode.textContent || '{}');
  const customersData = JSON.parse(topCustomersNode.textContent || '{}');

  const salesCtx = document.getElementById('salesLineChart');
  if (salesCtx) {
    new Chart(salesCtx, {
      type: 'line',
      data: {
        labels: salesData.labels || [],
        datasets: [{
          label: 'Ventas por día',
          data: salesData.totals || [],
          borderColor: '#0d6efd',
          backgroundColor: 'rgba(13, 110, 253, 0.15)',
          tension: 0.3,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }

  const customersCtx = document.getElementById('topCustomersChart');
  if (customersCtx) {
    new Chart(customersCtx, {
      type: 'bar',
      data: {
        labels: customersData.labels || [],
        datasets: [{
          label: 'Total gastado',
          data: customersData.totals || [],
          backgroundColor: 'rgba(25, 135, 84, 0.7)',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }
})();
