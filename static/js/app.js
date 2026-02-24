document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toast').forEach((el) => {
    const toast = bootstrap.Toast.getOrCreateInstance(el, { delay: 4000 });
    toast.show();
  });

  document.querySelectorAll('[data-kpi]').forEach((el) => {
    const target = parseInt(el.dataset.kpi || '0', 10);
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 30));
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = current;
      }
    }, 25);
  });

  if (window.jQuery && document.getElementById('productsTable')) {
    window.jQuery('#productsTable').DataTable({
      pageLength: 10,
      language: { url: 'https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json' }
    });
  }

  const chartCanvas = document.getElementById('sales30Chart');
  if (chartCanvas && window.Chart) {
    new Chart(chartCanvas, {
      type: 'line',
      data: {
        labels: [...Array(30)].map((_, i) => `Día ${i + 1}`),
        datasets: [{
          label: 'Ventas',
          data: [12,10,14,15,16,17,13,11,10,19,21,24,18,17,20,19,15,23,22,24,20,18,19,16,15,18,21,24,22,25],
          borderColor: '#60a5fa',
          backgroundColor: 'rgba(96,165,250,.18)',
          fill: true,
          tension: .35
        }]
      },
      options: { plugins: { legend: { labels: { color: '#cbd5e1' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8' } } } }
    });
  }
});
