document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toast').forEach((el) => bootstrap.Toast.getOrCreateInstance(el).show());
  if (window.jQuery && document.getElementById('inventoryTable')) {
    window.jQuery('#inventoryTable').DataTable({
      pageLength: 15,
      language: { url: 'https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json' }
    });
  }
});
