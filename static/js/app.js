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

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      form.querySelectorAll('button[type="submit"]').forEach((button) => {
        if (button.dataset.noLoading === 'true') return;
        button.disabled = true;
        if (!button.dataset.originalHtml) {
          button.dataset.originalHtml = button.innerHTML;
        }
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';
      });
    });
  });

  const confirmModalElement = document.getElementById('confirmActionModal');
  if (confirmModalElement) {
    const confirmModal = bootstrap.Modal.getOrCreateInstance(confirmModalElement);
    const confirmText = document.getElementById('confirmActionMessage');
    const confirmAccept = document.getElementById('confirmActionAccept');

    document.querySelectorAll('[data-confirm]').forEach((trigger) => {
      trigger.addEventListener('click', (event) => {
        event.preventDefault();
        confirmText.textContent = trigger.dataset.confirm || '¿Deseas continuar?';

        confirmAccept.onclick = () => {
          if (trigger.tagName === 'A') {
            window.location.href = trigger.href;
          } else if (trigger.tagName === 'BUTTON') {
            const targetForm = trigger.form || (trigger.dataset.confirmForm ? document.querySelector(trigger.dataset.confirmForm) : null);
            if (targetForm) targetForm.submit();
          }
          confirmModal.hide();
        };

        confirmModal.show();
      });
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
