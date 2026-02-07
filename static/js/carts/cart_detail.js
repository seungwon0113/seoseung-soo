function increaseCartQuantity(cartId) {
    const input = document.getElementById(`quantity-${cartId}`);
    const maxValue = parseInt(input.getAttribute('max'));
    const currentValue = parseInt(input.value);
    
    if (currentValue < maxValue) {
        input.value = currentValue + 1;
        updateItemTotal(cartId);
        submitCartUpdate(cartId, input.value);
    } else {
        alert('재고가 부족합니다.');
    }
}

function decreaseCartQuantity(cartId) {
    const input = document.getElementById(`quantity-${cartId}`);
    const currentValue = parseInt(input.value);
    
    if (currentValue > 1) {
        input.value = currentValue - 1;
        updateItemTotal(cartId);
        submitCartUpdate(cartId, input.value);
    } else {
        if (confirm('수량을 0으로 하면 상품이 삭제됩니다. 계속하시겠습니까?')) {
            deleteCartItem(cartId);
        }
    }
}

function submitCartUpdate(cartId, quantity) {
    const cartItem = document.querySelector(`[data-cart-id="${cartId}"]`);
    if (cartItem) {
        const form = cartItem.querySelector('form.quantity-form');
        if (form) {
            const quantityInput = form.querySelector('input[name="quantity"]');
            quantityInput.value = quantity;
            form.submit();
        } else {
            console.error('quantity-form을 찾을 수 없습니다:', cartId);
        }
    } else {
        console.error('cart-item을 찾을 수 없습니다:', cartId);
    }
}

function updateItemTotal(cartId) {
    const cartItem = document.querySelector(`[data-cart-id="${cartId}"]`);
    const quantityInput = document.getElementById(`quantity-${cartId}`);
    const quantity = parseInt(quantityInput.value);
    
    const salePriceElement = cartItem.querySelector('.sale-price');
    const priceElement = cartItem.querySelector('.price');
    
    let unitPrice = 0;
    if (salePriceElement) {
        unitPrice = parseInt(salePriceElement.textContent.replace(/[^0-9]/g, ''));
    } else if (priceElement) {
        unitPrice = parseInt(priceElement.textContent.replace(/[^0-9]/g, ''));
    }
    
    const totalPrice = unitPrice * quantity;
    const totalPriceElement = cartItem.querySelector('.total-price');
    totalPriceElement.textContent = totalPrice.toLocaleString() + '원';
    
    updateGrandTotal();
}

function updateGrandTotal() {
    const cartItems = document.querySelectorAll('.cart-item');
    let grandTotal = 0;
    
    cartItems.forEach(item => {
        const totalPriceElement = item.querySelector('.total-price');
        const totalPrice = parseInt(totalPriceElement.textContent.replace(/[^0-9]/g, ''));
        grandTotal += totalPrice;
    });
    
    const shippingFee = grandTotal >= 50000 ? 0 : 3000;
    const finalTotal = grandTotal + shippingFee;
    
    const summaryRows = document.querySelectorAll('.summary-row');
    summaryRows.forEach(row => {
        const label = row.querySelector('.label');
        const value = row.querySelector('.value');
        
        if (label && value) {
            if (label.textContent.includes('상품 금액')) {
                value.textContent = grandTotal.toLocaleString() + '원';
            } else if (label.textContent.includes('배송비')) {
                value.textContent = shippingFee === 0 ? '무료' : '3,000원';
            } else if (label.textContent.includes('총 결제 금액')) {
                value.textContent = finalTotal.toLocaleString() + '원';
            }
        }
    });
}


function deleteCartItem(cartId) {
    const cartItem = document.querySelector(`[data-cart-id="${cartId}"]`);
    if (!cartItem) {
        console.error('cart-item을 찾을 수 없습니다:', cartId);
        return;
    }

    const form = cartItem.querySelector('form.delete-form');
    if (!form) {
        console.error('delete-form을 찾을 수 없습니다:', cartId);
        return;
    }

    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert('상품 삭제에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('상품 삭제 중 오류가 발생했습니다.');
    });
}

function formatAllPrices() {
    const salePrices = document.querySelectorAll('.sale-price');
    const prices = document.querySelectorAll('.price');
    const originalPrices = document.querySelectorAll('.original-price');
    const totalPrices = document.querySelectorAll('.total-price');
    
    [...salePrices, ...prices, ...originalPrices, ...totalPrices].forEach(element => {
        const text = element.textContent;
        const number = parseInt(text.replace(/[^0-9]/g, ''));
        if (!isNaN(number)) {
            element.textContent = number.toLocaleString() + '원';
        }
    });
    
    const summaryValues = document.querySelectorAll('.summary-row .value');
    summaryValues.forEach(element => {
        const text = element.textContent;
        if (text.includes('원') && !text.includes('무료')) {
            const number = parseInt(text.replace(/[^0-9]/g, ''));
            if (!isNaN(number)) {
                element.textContent = number.toLocaleString() + '원';
            }
        }
    });
}

function createOrderFromCartAPI() {
    const items = [];
    const cartItems = document.querySelectorAll('.cart-item[data-cart-id]');
    
    cartItems.forEach(item => {
        const productId = parseInt(item.dataset.productId);
        const quantity = parseInt(item.querySelector('.quantity-input')?.value || 1);
        const productName = item.querySelector('.item-name')?.textContent?.trim() || '';
        const colorId = item.dataset.colorId ? parseInt(item.dataset.colorId) : null;
        const sizeId = item.dataset.sizeId ? parseInt(item.dataset.sizeId) : null;

        if (productId) {
            const itemData = {
                product_id: productId,
                product_name: productName,
                quantity: quantity
            };
            if (colorId) {
                itemData.color_id = colorId;
            }
            if (sizeId) {
                itemData.size_id = sizeId;
            }
            items.push(itemData);
        }
    });
    
    if (items.length === 0) {
        alert('주문할 상품이 없습니다.');
        return;
    }
    
    fetch('/orders/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            items: items
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = `/payments/?preOrderKey=${data.preOrderKey}`;
        } else {
            alert(data.error || '주문 생성에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('주문 생성 중 오류가 발생했습니다.');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    formatAllPrices();
    
    const quantityInputs = document.querySelectorAll('.quantity-input');
    
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const cartId = this.id.split('-')[1];
            const quantity = parseInt(this.value);
            const maxValue = parseInt(this.getAttribute('max'));
            
            if (quantity < 1) {
                if (confirm('수량을 0으로 하면 상품이 삭제됩니다. 계속하시겠습니까?')) {
                    deleteCartItem(cartId);
                } else {
                    this.value = 1;
                    updateItemTotal(cartId);
                }
            } else if (quantity > maxValue) {
                alert('재고가 부족합니다.');
                this.value = maxValue;
                updateItemTotal(cartId);
                submitCartUpdate(cartId, maxValue);
            } else {
                updateItemTotal(cartId);
                submitCartUpdate(cartId, quantity);
            }
        });
        
        input.addEventListener('input', function() {
            const cartId = this.id.split('-')[1];
            const quantity = parseInt(this.value) || 0;
            
            if (quantity > 0) {
                updateItemTotal(cartId);
            }
        });
    });
    
    const orderBtn = document.getElementById('orderBtn');
    if (orderBtn) {
        orderBtn.addEventListener('click', function(e) {
            e.preventDefault();
            createOrderFromCartAPI();
        });
    }
});