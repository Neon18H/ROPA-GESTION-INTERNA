(function () {
  function fromJsonScript(id) {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : [];
  }

  const salesLabels = fromJsonScript('chart-sales-labels');
  const salesValues = fromJsonScript('chart-sales-values');
  const topLabels = fromJsonScript('chart-top-labels');
  const topValues = fromJsonScript('chart-top-values');
  const expenseLabels = fromJsonScript('chart-expense-labels');
  const expenseValues = fromJsonScript('chart-expense-values');

  const salesCanvas = document.getElementById('salesChart');
  if (salesCanvas) {
    new Chart(salesCanvas, {
      type: 'line',
      data: { labels: salesLabels, datasets: [{ label: 'Ventas', data: salesValues, borderColor: '#111', tension: 0.2 }] },
    });
  }

  const topCanvas = document.getElementById('topProductsChart');
  if (topCanvas) {
    new Chart(topCanvas, {
      type: 'bar',
      data: { labels: topLabels, datasets: [{ label: 'Ingresos', data: topValues, backgroundColor: '#2f6fed' }] },
    });
  }

  const expenseCanvas = document.getElementById('expenseChart');
  if (expenseCanvas) {
    new Chart(expenseCanvas, {
      type: 'doughnut',
      data: { labels: expenseLabels, datasets: [{ label: 'Egresos', data: expenseValues }] },
    });
  }
})();
