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



  document.querySelectorAll('table[data-enhance="simple"]').forEach((table) => {
    table.classList.add('table-striped');
  });

  const topbarSearch = document.querySelector('.topbar-search input[type="search"]');
  if (topbarSearch) {
    topbarSearch.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        topbarSearch.value = '';
        topbarSearch.blur();
      }
    });
  }

  document.querySelectorAll('input[type="file"][data-image-preview-target]').forEach((input) => {
    input.addEventListener('change', (event) => {
      const file = event.target.files && event.target.files[0];
      if (!file) return;

      const previewSelector = input.dataset.imagePreviewTarget;
      if (!previewSelector) return;

      const objectUrl = URL.createObjectURL(file);
      document.querySelectorAll(previewSelector).forEach((img) => {
        if (!img) return;
        img.src = objectUrl;
        img.classList.remove('d-none');
      });

      const emptySelector = input.dataset.imageEmptyTarget;
      if (!emptySelector) return;
      document.querySelectorAll(emptySelector).forEach((node) => {
        if (!node) return;
        node.classList.remove('d-flex');
        node.classList.add('d-none');
      });
    });
  });
});
