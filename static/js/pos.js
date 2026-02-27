document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.querySelector('#itemsTable tbody');
  const totalFormsInput = document.querySelector('#id_items-TOTAL_FORMS');
  if (!tableBody || !totalFormsInput) return;

  const reindexRows = () => {
    const rows = [...tableBody.querySelectorAll('tr')];
    rows.forEach((row, idx) => {
      row.querySelectorAll('input').forEach((input) => {
        const field = input.dataset.field;
        input.name = `items-${idx}-${field}`;
        input.id = `id_items-${idx}-${field}`;
      });
    });
    totalFormsInput.value = rows.length;
  };

  const bindRowEvents = (row) => {
    const removeButton = row.querySelector('.remove-item');
    if (removeButton) {
      removeButton.addEventListener('click', () => {
        row.remove();
        reindexRows();
      });
    }

    const restoreButton = row.querySelector('.restore-suggested-price');
    const unitPriceInput = row.querySelector('input[data-field="unit_price"]');
    if (restoreButton && unitPriceInput) {
      restoreButton.addEventListener('click', () => {
        unitPriceInput.value = row.dataset.defaultSalePrice || '0';
      });
    }
  };

  document.querySelectorAll('.add-item').forEach((button) => {
    button.addEventListener('click', () => {
      const idx = tableBody.querySelectorAll('tr').length;
      const suggestedPrice = button.dataset.defaultSalePrice || '0';
      const row = document.createElement('tr');
      row.dataset.defaultSalePrice = suggestedPrice;
      row.innerHTML = `
        <td>${button.dataset.displayName}<input type="hidden" data-field="variant" name="items-${idx}-variant" value="${button.dataset.variantId}"></td>
        <td><input class="form-control" data-field="quantity" type="number" name="items-${idx}-quantity" value="1" min="1"></td>
        <td>
          <label class="form-label form-label-sm mb-1">Precio sugerido</label>
          <div class="input-group">
            <input class="form-control" data-field="unit_price" type="number" name="items-${idx}-unit_price" value="${suggestedPrice}" step="0.01" min="0">
            <button type="button" class="btn btn-outline-secondary restore-suggested-price">Restaurar sugerido</button>
          </div>
        </td>
        <td><input class="form-control" data-field="tax_rate" type="number" name="items-${idx}-tax_rate" value="" step="0.01" min="0" max="100"></td>
        <td><input class="form-control" data-field="discount" type="number" name="items-${idx}-discount" value="0" step="0.01"></td>
        <td><button type="button" class="btn btn-sm btn-outline-danger remove-item">×</button></td>`;
      tableBody.appendChild(row);
      bindRowEvents(row);
      reindexRows();
    });
  });
});
