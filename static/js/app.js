document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  document.querySelectorAll('.sidebar-nav .nav-link').forEach((link) => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (path === href || (href !== '/' && path.startsWith(href))) {
      link.classList.add('active');
    }
  });

  if (typeof bootstrap === 'undefined') return;

  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
    bootstrap.Tooltip.getOrCreateInstance(el);
  });

  document.querySelectorAll('.toast').forEach((el) => {
    bootstrap.Toast.getOrCreateInstance(el).show();
  });

  const offcanvasElement = document.getElementById('mobileSidebar');
  if (offcanvasElement) {
    const offcanvas = bootstrap.Offcanvas.getOrCreateInstance(offcanvasElement);
    offcanvasElement.querySelectorAll('.nav-link').forEach((link) => {
      link.addEventListener('click', () => offcanvas.hide());
    });
  }
});
