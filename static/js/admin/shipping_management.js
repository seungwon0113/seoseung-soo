function showShippingDetailModal(row) {
    const orderNumber = row.getAttribute('data-order-number');
    const customerEmail = row.getAttribute('data-customer-email');
    const customerName = row.getAttribute('data-customer-name');
    const orderDate = row.getAttribute('data-order-date');
    const orderAmount = row.getAttribute('data-order-amount');
    const shippingStatus = row.getAttribute('data-shipping-status');

    document.getElementById('shippingDetailNumber').textContent = orderNumber;
    document.getElementById('shippingDetailCustomer').textContent = customerEmail + ' (' + customerName + ')';
    document.getElementById('shippingDetailDate').textContent = orderDate;
    document.getElementById('shippingDetailAmount').textContent = orderAmount + '원';
    document.getElementById('shippingDetailStatus').textContent = shippingStatus;

    const contentEl = row.querySelector('.order-detail-content');
    const productsEl = document.getElementById('shippingDetailProducts');
    if (contentEl && productsEl) {
        productsEl.innerHTML = contentEl.innerHTML;
    }

    document.getElementById('shippingDetailModal').style.display = 'block';
}

function closeShippingDetailModal() {
    document.getElementById('shippingDetailModal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    const tbody = document.querySelector('.shipping-table tbody');
    if (tbody) {
        tbody.addEventListener('click', function(event) {
            if (event.target.closest('[data-no-row-click]')) return;
            const row = event.target.closest('tr.shipping-row-clickable');
            if (!row) return;
            showShippingDetailModal(row);
        });
    }

    const shippingDetailModal = document.getElementById('shippingDetailModal');
    if (shippingDetailModal) {
        shippingDetailModal.addEventListener('click', function(event) {
            if (event.target === shippingDetailModal) {
                closeShippingDetailModal();
            }
        });
    }
});
