document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toast').forEach((el) => {
    bootstrap.Toast.getOrCreateInstance(el).show();
  });

  document.querySelectorAll('[data-inline-edit]').forEach((button) => {
    button.addEventListener('click', () => {
      const targetId = button.getAttribute('data-inline-edit');
      const row = document.getElementById(targetId);
      if (!row) return;
      row.classList.toggle('d-none');
    });
  });
});
