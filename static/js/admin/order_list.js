function showOrderDetailModal(row) {
    const orderNumber = row.getAttribute('data-order-number');
    const customerEmail = row.getAttribute('data-customer-email');
    const customerName = row.getAttribute('data-customer-name');
    const orderDate = row.getAttribute('data-order-date');
    const orderAmount = row.getAttribute('data-order-amount');
    const orderStatus = row.getAttribute('data-order-status');

    document.getElementById('orderDetailNumber').textContent = orderNumber;
    document.getElementById('orderDetailCustomer').textContent = customerEmail + ' (' + customerName + ')';
    document.getElementById('orderDetailDate').textContent = orderDate;
    document.getElementById('orderDetailAmount').textContent = orderAmount + '원';
    document.getElementById('orderDetailStatus').textContent = orderStatus;

    const contentEl = row.querySelector('.order-detail-content');
    const productsEl = document.getElementById('orderDetailProducts');
    if (contentEl && productsEl) {
        productsEl.innerHTML = contentEl.innerHTML;
    }

    document.getElementById('orderDetailModal').style.display = 'block';
}

function closeOrderDetailModal() {
    document.getElementById('orderDetailModal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    const tbody = document.querySelector('.order-list tbody');
    if (tbody) {
        tbody.addEventListener('click', function(event) {
            const row = event.target.closest('tr.order-row-clickable');
            if (!row) return;
            showOrderDetailModal(row);
        });
    }

    const orderDetailModal = document.getElementById('orderDetailModal');
    if (orderDetailModal) {
        orderDetailModal.addEventListener('click', function(event) {
            if (event.target === orderDetailModal) {
                closeOrderDetailModal();
            }
        });
    }
});
