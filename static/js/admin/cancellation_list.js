function showApprovalModal(orderId, orderNumber) {
    document.getElementById('approvalOrderNumber').textContent = orderNumber;
    document.getElementById('approvalForm').action = `/orders/admin/cancellation/${orderId}/process/`;
    document.getElementById('approvalModal').style.display = 'block';
}

function showRejectModal(orderId, orderNumber) {
    document.getElementById('rejectOrderNumber').textContent = orderNumber;
    document.getElementById('rejectForm').action = `/orders/admin/cancellation/${orderId}/process/`;
    document.getElementById('rejectModal').style.display = 'block';
}

function showAdminMemoModal(orderNumber, memoContent) {
    document.getElementById('adminMemoOrderNumber').textContent = orderNumber;
    const el = document.getElementById('adminMemoContent');
    el.textContent = memoContent && memoContent.trim() ? memoContent.trim() : '메모 없음';
    document.getElementById('adminMemoModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    if (modalId === 'approvalModal') {
        document.getElementById('approvalAdminNote').value = '';
    } else if (modalId === 'rejectModal') {
        document.getElementById('rejectAdminNote').value = '';
    }
}

window.onclick = function(event) {
    const approvalModal = document.getElementById('approvalModal');
    const rejectModal = document.getElementById('rejectModal');
    const adminMemoModal = document.getElementById('adminMemoModal');
    if (event.target === approvalModal) {
        closeModal('approvalModal');
    }
    if (event.target === rejectModal) {
        closeModal('rejectModal');
    }
    if (event.target === adminMemoModal) {
        closeModal('adminMemoModal');
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const tbody = document.querySelector('.cancellation-list tbody');
    if (tbody) {
        tbody.addEventListener('click', function(event) {
            if (event.target.closest('[data-no-row-click]')) return;
            const row = event.target.closest('tr.order-row-clickable');
            if (!row) return;
            const orderNumber = row.getAttribute('data-order-number');
            const memoEl = row.querySelector('.admin-memo-content');
            const memoContent = memoEl ? memoEl.textContent : '';
            showAdminMemoModal(orderNumber, memoContent);
        });
    }
});
