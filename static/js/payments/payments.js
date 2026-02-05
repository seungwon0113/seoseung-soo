document.addEventListener('DOMContentLoaded', function() {
    initializePaymentPage();
});

window.selectedPaymentMethod = 'card';

window.usedPoints = 0;

function initializePaymentPage() {
    setupPaymentMethodSelection();
    setupCouponApplication();
    setupAddressSearch();
    setupFormValidation();
    setupDiscountSelection();
    setupDropdownCloseOnOutsideClick();
    setupTossPayment();
    setupPointUsage();
}

function setupPaymentMethodSelection() {
    const paymentMethodOptions = document.querySelectorAll('.payment-method-option');
    const virtualAccountSection = document.getElementById('virtualAccountSection');
    const paymentButton = document.getElementById('tossPaymentBtn');
    
    paymentMethodOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            const radio = this.querySelector('input[type="radio"]');
            const method = this.getAttribute('data-method');
            
            paymentMethodOptions.forEach(opt => opt.classList.remove('selected'));
            
            this.classList.add('selected');
            radio.checked = true;
            
            window.selectedPaymentMethod = method;
            
            if (virtualAccountSection) {
                if (method === 'virtual') {
                    virtualAccountSection.style.display = 'block';
                } else {
                    virtualAccountSection.style.display = 'none';
                }
            }
            
            if (paymentButton) {
                const amount = paymentButton.getAttribute('data-amount');
                const formattedAmount = parseInt(amount).toLocaleString();
                const paymentText = paymentButton.querySelector('.payment-text');
                if (paymentText) {
                    if (method === 'virtual') {
                        paymentText.textContent = `${formattedAmount}원 가상계좌 발급`;
                    } else {
                        paymentText.textContent = `${formattedAmount}원 결제하기`;
                    }
                }
            }
        });
    });
    
    setupCardOptionSelection();
}

function setupCardOptionSelection() {
    const cardOptions = document.querySelectorAll('.card-option');
    
    cardOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const cardType = this.getAttribute('data-value');
            const cardName = this.querySelector('span').textContent;
            
            window.selectedCardType = cardType;
            
            const dropdown = this.closest('.card-dropdown');
            if (dropdown) {
                dropdown.classList.remove('show');
            }
            
            updateSelectedCardDisplay(cardName);
        });
    });
}

function setupDropdownCloseOnOutsideClick() {
    document.addEventListener('click', function(e) {
        if (e.target.closest('.payment-method') || e.target.closest('.card-dropdown-container')) {
            return;
        }
        
        const dropdownContainer = document.querySelector('.card-dropdown-container.show');
        
        if (dropdownContainer) {
            dropdownContainer.classList.remove('show');
        }
    });
}

function setupCouponApplication() {
    const couponBtn = document.querySelector('.coupon-btn');
    const couponInput = document.querySelector('.coupon-input');
    
    if (couponBtn && couponInput) {
        couponBtn.addEventListener('click', function() {
            const couponCode = couponInput.value.trim();
            
            if (!couponCode) {
                alert('쿠폰 코드를 입력해주세요.');
                return;
            }
            
            applyCoupon(couponCode);
        });
        
        couponInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                couponBtn.click();
            }
        });
    }
}

function applyCoupon(couponCode) {
    const couponBtn = document.querySelector('.coupon-btn');
    const originalText = couponBtn.textContent;
    couponBtn.textContent = '적용 중...';
    couponBtn.disabled = true;
    
    setTimeout(() => {
        const discountAmount = validateCoupon(couponCode);
        
        if (discountAmount > 0) {
            updateDiscountAmount(discountAmount);
            showSuccessMessage(`쿠폰이 적용되었습니다. ${discountAmount.toLocaleString()}원 할인`);
            couponBtn.textContent = '적용됨';
            couponBtn.style.background = '#28a745';
            couponBtn.style.color = 'white';
        } else {
            showErrorMessage('유효하지 않은 쿠폰입니다.');
            couponBtn.textContent = originalText;
            couponBtn.disabled = false;
        }
    }, 1000);
}

function validateCoupon(couponCode) {
    const validCoupons = {
        'WELCOME10': 10000,
        'SAVE5000': 5000,
        'FIRST20': 20000
    };
    
    return validCoupons[couponCode] || 0;
}

function updateDiscountAmount(amount) {
    const discountElement = document.querySelector('.summary-row .summary-value');
    if (discountElement) {
        discountElement.textContent = `-${amount.toLocaleString()}원`;
    }
    
    calculateTotalAmount();
}

function setupAddressSearch() {
    const addressSearchBtn = document.querySelector('.address-search-btn');
    
    if (addressSearchBtn) {
        addressSearchBtn.addEventListener('click', function() {
            openAddressSearch();
        });
    }
}

function openAddressSearch() {
    if (typeof daum === 'undefined' || !daum.Postcode) {
        alert('우편번호 서비스를 불러올 수 없습니다. 페이지를 새로고침 후 다시 시도해주세요.');
        return;
    }

    const zipcodeInput = document.querySelector('.postal-code-input');
    const addressInput = document.querySelector('.address-input');
    const detailInput = document.querySelector('.detail-address-input');

    new daum.Postcode({
        oncomplete: function(data) {
            var addr = '';
            var extraAddr = '';

            if (data.userSelectedType === 'R') {
                addr = data.roadAddress;
                if (data.bname !== '' && /(동|로|가)$/.test(data.bname)) {
                    extraAddr += data.bname;
                }
                if (data.buildingName !== '' && data.apartment === 'Y') {
                    extraAddr += (extraAddr !== '' ? ', ' + data.buildingName : data.buildingName);
                }
                if (extraAddr !== '') {
                    extraAddr = ' (' + extraAddr + ')';
                }
            } else {
                addr = data.jibunAddress;
            }

            if (zipcodeInput) zipcodeInput.value = data.zonecode;
            if (addressInput) addressInput.value = addr + extraAddr;
            if (detailInput) {
                detailInput.value = '';
                detailInput.focus();
            }
        }
    }).open();
}

function setupFormValidation() {
    const inputs = document.querySelectorAll('input[required], select[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('error')) {
                validateField(this);
            }
        });
    });
}

function setupDiscountSelection() {
    const discountSelect = document.querySelector('.discount-select');
    if (discountSelect) {
        discountSelect.addEventListener('change', function() {
            calculateTotalAmount();
        });
    }
}

function setupPointUsage() {
    const pointInput = document.getElementById('pointInput');
    const useAllPointsBtn = document.getElementById('useAllPointsBtn');
    
    if (!pointInput) return;

    const maxPoint = parseInt(pointInput.getAttribute('data-max-point')) || 0;
    const originalFinalAmount = parseInt(pointInput.getAttribute('data-final-amount')) || 0;

    pointInput.addEventListener('input', function() {
        let value = parseInt(this.value) || 0;
        
        if (value < 0) value = 0;
        
        if (value > maxPoint) value = maxPoint;
        
        if (value > originalFinalAmount) value = originalFinalAmount;
        
        this.value = value;
        window.usedPoints = value;
        
        updatePaymentAmount();
    });

    if (useAllPointsBtn) {
        useAllPointsBtn.addEventListener('click', function() {
            const useAmount = Math.min(maxPoint, originalFinalAmount);
            pointInput.value = useAmount;
            window.usedPoints = useAmount;
            
            updatePaymentAmount();
        });
    }
}

function updatePaymentAmount() {
    const pointInput = document.getElementById('pointInput');
    const paymentButton = document.getElementById('tossPaymentBtn');
    const finalAmountDisplay = document.getElementById('finalAmountDisplay');
    const pointDiscountRow = document.querySelector('.point-discount-row');
    const pointDiscountValue = document.querySelector('.point-discount-value');
    
    if (!pointInput || !paymentButton) return;

    const originalFinalAmount = parseInt(pointInput.getAttribute('data-final-amount')) || 0;
    const usedPoints = window.usedPoints || 0;
    const newFinalAmount = originalFinalAmount - usedPoints;

    paymentButton.setAttribute('data-amount', newFinalAmount);
    const paymentText = paymentButton.querySelector('.payment-text');
    if (paymentText) {
        const formattedAmount = newFinalAmount.toLocaleString();
        if (window.selectedPaymentMethod === 'virtual') {
            paymentText.textContent = `${formattedAmount}원 가상계좌 발급`;
        } else {
            paymentText.textContent = `${formattedAmount}원 결제하기`;
        }
    }

    if (finalAmountDisplay) {
        finalAmountDisplay.textContent = newFinalAmount.toLocaleString() + '원';
    }

    if (pointDiscountRow && pointDiscountValue) {
        if (usedPoints > 0) {
            pointDiscountRow.style.display = 'flex';
            pointDiscountValue.textContent = `-${usedPoints.toLocaleString()}원`;
        } else {
            pointDiscountRow.style.display = 'none';
        }
    }
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = '필수 입력 항목입니다.';
    }
    
    if (field.type === 'tel' && value) {
        const phoneRegex = /^[0-9-+\s()]+$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            errorMessage = '올바른 연락처 형식이 아닙니다.';
        }
    }
    
    if (isValid) {
        field.classList.remove('error');
        removeErrorMessage(field);
    } else {
        field.classList.add('error');
        showErrorMessage(field, errorMessage);
    }
    
    return isValid;
}

function showErrorMessage(field, message) {
    removeErrorMessage(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

function removeErrorMessage(field) {
    const existingError = field.parentNode.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }
}

function calculateTotalAmount() {
    const paymentButton = document.getElementById('tossPaymentBtn');
    const pointInput = document.getElementById('pointInput');
    const finalAmountDisplay = document.getElementById('finalAmountDisplay');
    const pointDiscountRow = document.querySelector('.point-discount-row');
    const pointDiscountValue = document.querySelector('.point-discount-value');
    
    if (!paymentButton) {
        return;
    }
    
    let originalAmount = parseInt(paymentButton.getAttribute('data-original-amount')) || 0;
    if (originalAmount === 0) {
        originalAmount = parseInt(paymentButton.getAttribute('data-amount')) || 0;
        paymentButton.setAttribute('data-original-amount', originalAmount);
    }
    
    const discountAmount = getCurrentDiscountAmount();
    const usedPoints = window.usedPoints || 0;
    const finalAmount = originalAmount - discountAmount - usedPoints;
    
    const paymentText = paymentButton.querySelector('.payment-text');
    
    if (paymentText) {
        const formattedAmount = finalAmount.toLocaleString();
        if (window.selectedPaymentMethod === 'virtual') {
            paymentText.textContent = `${formattedAmount}원 가상계좌 발급`;
        } else {
            paymentText.textContent = `${formattedAmount}원 결제하기`;
        }
        paymentButton.setAttribute('data-amount', finalAmount);
    }

    if (finalAmountDisplay) {
        finalAmountDisplay.textContent = finalAmount.toLocaleString() + '원';
    }

    if (pointDiscountRow && pointDiscountValue) {
        if (usedPoints > 0) {
            pointDiscountRow.style.display = 'flex';
            pointDiscountValue.textContent = `-${usedPoints.toLocaleString()}원`;
        } else {
            pointDiscountRow.style.display = 'none';
        }
    }

    if (pointInput) {
        const newMaxUsable = originalAmount - discountAmount;
        pointInput.setAttribute('data-final-amount', newMaxUsable);
    }
}

function getCurrentDiscountAmount() {
    const discountSelect = document.querySelector('.discount-select');
    if (discountSelect) {
        return parseInt(discountSelect.value) || 0;
    }
    return 0;
}

function processPayment() {
    if (!validateForm()) {
        showErrorMessage(null, '필수 정보를 모두 입력해주세요.');
        return;
    }
    
    const selectedPaymentMethod = document.querySelector('input[name="payment-method"]:checked');
    if (!selectedPaymentMethod) {
        showErrorMessage(null, '결제 방법을 선택해주세요.');
        return;
    }
    
    if (selectedPaymentMethod.value === 'card' && !window.selectedCardType) {
        showErrorMessage(null, '카드 종류를 선택해주세요.');
        return;
    }
    
    const paymentButton = document.getElementById('tossPaymentBtn');
    if (!paymentButton) {
        showErrorMessage(null, '결제 버튼을 찾을 수 없습니다.');
        return;
    }
    
    const discountAmount = getCurrentDiscountAmount();
    const totalAmount = parseInt(paymentButton.getAttribute('data-amount')) || 0;
    const finalAmount = totalAmount;
    
    if (!confirm(`${finalAmount.toLocaleString()}원을 결제하시겠습니까?`)) {
        return;
    }
    
    processPaymentRequest(selectedPaymentMethod.value, finalAmount);
}

function validateForm() {
    const requiredFields = document.querySelectorAll('input[required], select[required]');
    
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function processPaymentRequest(paymentMethod, amount) {
    const paymentButton = document.querySelector('.payment-button');
    const originalText = paymentButton.innerHTML;
    
    paymentButton.innerHTML = '<span>결제 처리 중...</span>';
    paymentButton.disabled = true;
        
    setTimeout(() => {
        const isSuccess = Math.random() > 0.1;
        
        if (isSuccess) {
            showSuccessMessage('결제가 완료되었습니다!');
            setTimeout(() => {
                window.location.href = '/orders/success/';
            }, 2000);
        } else {
            showErrorMessage(null, '결제 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
            paymentButton.innerHTML = originalText;
            paymentButton.disabled = false;
        }
    }, 2000);
}

function showSuccessMessage(message) {
    alert(message);
}

function showErrorMessage(element, message) {
    if (element) {
        showErrorMessage(element, message);
    } else {
        alert(message);
    }
}

function formatNumber(num) {
    return num.toLocaleString();
}

window.addEventListener('beforeunload', function(e) {
    const paymentButton = document.getElementById('tossPaymentBtn');
    const isPaymentInProgress = paymentButton && paymentButton.disabled;
    
    if (isPaymentInProgress) {
        e.preventDefault();
        e.returnValue = '';
    }
});

function initializeTossPaymentWidget(paymentData, amount) {
    const clientKeyElement = document.getElementById('tossClientKey');
    const clientKey = clientKeyElement ? clientKeyElement.value : '';
    
    if (!clientKey) {
        alert('결제 시스템을 초기화할 수 없습니다. 클라이언트 키가 설정되지 않았습니다.');
        const paymentButton = document.getElementById('tossPaymentBtn');
        if (paymentButton) {
            const finalAmount = amount || 0;
            paymentButton.innerHTML = `<span class="payment-text">${finalAmount.toLocaleString()}원 결제하기</span>`;
            paymentButton.disabled = false;
        }
        return;
    }
    
    const tossPayments = TossPayments(clientKey);
    
    let successUrl = paymentData.successUrl;
    let failUrl = paymentData.failUrl;
    
    if (paymentData.preOrderKey) {
        if (!successUrl.includes('preOrderKey=')) {
            successUrl += (successUrl.includes('?') ? '&' : '?') + `preOrderKey=${paymentData.preOrderKey}`;
        }
        if (!failUrl.includes('preOrderKey=')) {
            failUrl += (failUrl.includes('?') ? '&' : '?') + `preOrderKey=${paymentData.preOrderKey}`;
        }
    }
    
    tossPayments.requestPayment('카드', {
        amount: amount,
        orderId: paymentData.orderId,
        orderName: paymentData.orderName,
        successUrl: successUrl,
        failUrl: failUrl,
        customerEmail: document.querySelector('.email-input')?.value || '',
        customerName: document.querySelector('.form-input[placeholder*="이름"]')?.value || '',
    })
    .catch(function (error) {
        const paymentButton = document.getElementById('tossPaymentBtn');
        const finalAmount = parseInt(paymentButton.getAttribute('data-amount')) || amount || 0;
        
        if (error.code === 'USER_CANCEL') {
            paymentButton.innerHTML = `<span class="payment-text">${finalAmount.toLocaleString()}원 결제하기</span>`;
            paymentButton.disabled = false;
        } else {
            alert('결제 요청 중 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'));
            paymentButton.innerHTML = `<span class="payment-text">${finalAmount.toLocaleString()}원 결제하기</span>`;
            paymentButton.disabled = false;
        }
    });
}

function validateDeliveryForm() {
    const recipientName = document.getElementById('recipientName');
    const addressInput = document.querySelector('.address-input');
    const phone1 = document.getElementById('phone1');
    const phone2 = document.getElementById('phone2');
    const phone3 = document.getElementById('phone3');
    const emailId = document.getElementById('emailId');
    const emailDomain = document.getElementById('emailDomain');

    if (!recipientName || !recipientName.value.trim()) {
        return { valid: false, message: '받는사람을 입력해주세요.' };
    }

    if (!addressInput || !addressInput.value.trim()) {
        return { valid: false, message: '주소를 입력해주세요.' };
    }

    if (!phone1 || !phone2 || !phone3 ||
        !phone1.value.trim() || !phone2.value.trim() || !phone3.value.trim()) {
        return { valid: false, message: '휴대전화를 입력해주세요.' };
    }

    if (!emailId || !emailId.value.trim()) {
        return { valid: false, message: '이메일을 입력해주세요.' };
    }

    if (!emailDomain || !emailDomain.value.trim()) {
        return { valid: false, message: '이메일 도메인을 선택해주세요.' };
    }

    return { valid: true, message: '' };
}

function setupTossPayment() {
    const tossPaymentBtn = document.getElementById('tossPaymentBtn');
    if (!tossPaymentBtn) {
        return;
    }
    
    tossPaymentBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const validation = validateDeliveryForm();
        if (!validation.valid) {
            alert(validation.message);
            return;
        }

        const usedPoints = window.usedPoints || 0;
        if (usedPoints > 0 && usedPoints < 1000) {
            alert('포인트는 최소 1,000P 이상부터 사용 가능합니다.');
            return;
        }
        
        const preOrderKey = tossPaymentBtn.getAttribute('data-pre-order-key');
        const amount = parseInt(tossPaymentBtn.getAttribute('data-amount')) || 0;
        
        if (!preOrderKey) {
            alert('주문 정보를 찾을 수 없습니다.');
            return;
        }
        
        if (amount <= 0) {
            if (usedPoints < 1000) {
                alert('포인트는 최소 1,000P 이상부터 사용 가능합니다.');
                return;
            }
            requestPointOnlyPayment(preOrderKey, usedPoints);
            return;
        }
        
        if (window.selectedPaymentMethod === 'virtual') {
            requestVirtualAccountPayment(preOrderKey, amount);
        } else {
            requestTossPayment(preOrderKey, amount);
        }
    });
}

function requestTossPayment(preOrderKey, amount) {
    const paymentButton = document.getElementById('tossPaymentBtn');
    const originalText = paymentButton.innerHTML;
    
    paymentButton.innerHTML = '<span class="payment-text">결제 요청 중...</span>';
    paymentButton.disabled = true;
    
    fetch('/payments/toss/request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            preOrderKey: preOrderKey,
            usedPoint: window.usedPoints || 0
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const finalAmount = data.amount || amount;
            data.preOrderKey = preOrderKey;
            initializeTossPaymentWidget(data, finalAmount);
        } else {
            alert(data.error || '결제 요청에 실패했습니다.');
            paymentButton.innerHTML = originalText;
            paymentButton.disabled = false;
        }
    })
    .catch(error => {
        alert('결제 요청 중 오류가 발생했습니다.');
        paymentButton.innerHTML = originalText;
        paymentButton.disabled = false;
    });
}

function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        return csrfToken.value;
    }
    
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    
    return '';
}

function requestPointOnlyPayment(preOrderKey, usedPoints) {
    const paymentButton = document.getElementById('tossPaymentBtn');
    const originalText = paymentButton.innerHTML;
    
    paymentButton.innerHTML = '<span class="payment-text">포인트 결제 처리 중...</span>';
    paymentButton.disabled = true;
    
    fetch('/payments/point-only/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            preOrderKey: preOrderKey,
            usedPoint: usedPoints
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirectUrl || '/orders/status/';
        } else {
            alert(data.error || '포인트 결제에 실패했습니다.');
            paymentButton.innerHTML = originalText;
            paymentButton.disabled = false;
        }
    })
    .catch(error => {
        alert('포인트 결제 요청 중 오류가 발생했습니다.');
        paymentButton.innerHTML = originalText;
        paymentButton.disabled = false;
    });
}

function requestVirtualAccountPayment(preOrderKey, amount) {
    const bankSelect = document.getElementById('bankSelect');
    const depositorName = document.getElementById('depositorName');
    const paymentButton = document.getElementById('tossPaymentBtn');
    
    if (!bankSelect || !bankSelect.value) {
        alert('입금 은행을 선택해주세요.');
        return;
    }
    
    if (!depositorName || !depositorName.value.trim()) {
        alert('입금자명을 입력해주세요.');
        return;
    }
    
    const originalText = paymentButton.innerHTML;
    paymentButton.innerHTML = '<span class="payment-text">가상계좌 발급 중...</span>';
    paymentButton.disabled = true;
    
    fetch('/orders/virtual/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            preOrderKey: preOrderKey
        })
    })
    .then(response => response.json())
    .then(orderData => {
        if (!orderData.success && !orderData.orderId) {
            throw new Error(orderData.error || '주문 생성에 실패했습니다.');
        }
        
        const orderId = orderData.orderId;
        
        return fetch('/payments/toss/virtual/request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                orderId: orderId,
                customerName: depositorName.value.trim(),
                bank: bankSelect.value
            })
        });
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showVirtualAccountResult(data);
        } else {
            throw new Error(data.error || '가상계좌 발급에 실패했습니다.');
        }
    })
    .catch(error => {
        alert(error.message || '가상계좌 발급 중 오류가 발생했습니다.');
        paymentButton.innerHTML = originalText;
        paymentButton.disabled = false;
    });
}

function showVirtualAccountResult(data) {
    let modal = document.getElementById('virtualResultModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'virtualResultModal';
        modal.className = 'virtual-result-modal';
        document.body.appendChild(modal);
    }
    
    const bankNames = {
        'KOOKMIN': '국민은행',
        'SHINHAN': '신한은행',
        'WOORI': '우리은행',
        'NH': '농협은행',
    };
    
    const bankName = bankNames[data.bank] || data.bank;
    const dueDate = data.due_date ? formatDueDate(data.due_date) : '24시간 내';
    
    modal.innerHTML = `
        <div class="virtual-result-content">
            <div class="virtual-result-icon">🏦</div>
            <h3 class="virtual-result-title">가상계좌가 발급되었습니다</h3>
            <div class="virtual-result-info">
                <div class="virtual-result-row">
                    <span class="label">은행</span>
                    <span class="value">${bankName}</span>
                </div>
                <div class="virtual-result-row">
                    <span class="label">계좌번호</span>
                    <span class="value account-number">${data.account_number}</span>
                </div>
                <div class="virtual-result-row">
                    <span class="label">예금주</span>
                    <span class="value">${data.account_holder}</span>
                </div>
                <div class="virtual-result-row">
                    <span class="label">입금기한</span>
                    <span class="value">${dueDate}</span>
                </div>
            </div>
            <p style="font-size: 13px; color: #6b7280; margin-bottom: 20px;">
                위 계좌로 입금해주시면 자동으로 결제가 완료됩니다.
            </p>
            <button type="button" class="virtual-result-btn" onclick="closeVirtualResultModal()">
                확인
            </button>
        </div>
    `;
    
    modal.classList.add('show');
}

function closeVirtualResultModal() {
    const modal = document.getElementById('virtualResultModal');
    if (modal) {
        modal.classList.remove('show');
    }
    window.location.href = '/users/mypage/orders/';
}

function formatDueDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}.${month}.${day} ${hours}:${minutes}까지`;
}
