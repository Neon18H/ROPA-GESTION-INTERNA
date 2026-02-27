document.addEventListener('DOMContentLoaded', () => {
  if (typeof bootstrap !== 'undefined') {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => bootstrap.Tooltip.getOrCreateInstance(el));
    document.querySelectorAll('.toast').forEach((el) => bootstrap.Toast.getOrCreateInstance(el).show());
  }

  const offcanvasElement = document.getElementById('mobileSidebar');
  if (offcanvasElement && typeof bootstrap !== 'undefined') {
    const offcanvas = bootstrap.Offcanvas.getOrCreateInstance(offcanvasElement);
    offcanvasElement.querySelectorAll('.nav-link').forEach((link) => link.addEventListener('click', () => offcanvas.hide()));
  }

  const confirmModalEl = document.getElementById('confirmModal');
  const confirmButton = document.getElementById('modalConfirmButton');
  let pendingDeleteUrl = null;
  if (confirmModalEl && confirmButton && typeof bootstrap !== 'undefined') {
    const confirmModal = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
    document.querySelectorAll('[data-confirm-delete]').forEach((btn) => {
      btn.addEventListener('click', (event) => {
        event.preventDefault();
        pendingDeleteUrl = btn.getAttribute('href');
        confirmModal.show();
      });
    });
    confirmButton.addEventListener('click', () => {
      if (pendingDeleteUrl) window.location.href = pendingDeleteUrl;
    });
  }

  document.querySelectorAll('[data-search-debounce]').forEach((input) => {
    let timeout = null;
    input.addEventListener('input', () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        input.dispatchEvent(new CustomEvent('debounced:input', { bubbles: true }));
      }, Number(input.dataset.searchDebounce || 300));
    });
  });
});
