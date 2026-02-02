function changeMainImage(imageUrl) {
    document.getElementById('mainImage').src = imageUrl;
    
    const thumbnails = document.querySelectorAll('.thumbnail');
    thumbnails.forEach(thumbnail => {
        thumbnail.classList.remove('active');
    });
    
    const clickedThumbnail = document.querySelector(`.thumbnail[src="${imageUrl}"]`);
    if (clickedThumbnail) {
        clickedThumbnail.classList.add('active');
    }
}

function increaseQuantity() {
    const quantityDisplay = document.getElementById('quantityDisplay');
    const cartQuantity = document.getElementById('cartQuantity');
    const productStock = document.querySelector('.size-quantity-section').dataset.productStock;
    let currentQuantity = parseInt(quantityDisplay.textContent);
    
    if (currentQuantity < parseInt(productStock)) {
        currentQuantity++;
        quantityDisplay.textContent = currentQuantity;
        cartQuantity.value = currentQuantity;
    } else {
        alert('재고가 부족합니다.');
    }
}

function decreaseQuantity() {
    const quantityDisplay = document.getElementById('quantityDisplay');
    const cartQuantity = document.getElementById('cartQuantity');
    let currentQuantity = parseInt(quantityDisplay.textContent);
    
    if (currentQuantity > 1) {
        currentQuantity--;
        quantityDisplay.textContent = currentQuantity;
        cartQuantity.value = currentQuantity;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('.comment-input-wrapper textarea');
    
    textareas.forEach(function(textarea) {
        const charCount = textarea.parentElement.querySelector('.char-count');
        
        if (charCount) {
            function updateCharCount() {
                const count = textarea.value.length;
                charCount.textContent = count;
                
                if (count > 450) {
                    charCount.style.color = '#ef4444';
                } else if (count > 400) {
                    charCount.style.color = '#f59e0b';
                } else {
                    charCount.style.color = '#374151';
                }
            }
            
            textarea.addEventListener('input', updateCharCount);
            updateCharCount();
        }
    });
    
    const cartForm = document.querySelector('.cart-form');
    if (cartForm) {
        cartForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const quantityDisplay = document.getElementById('quantityDisplay');
            const cartQuantity = document.getElementById('cartQuantity');
            
            if (quantityDisplay && cartQuantity) {
                cartQuantity.value = quantityDisplay.textContent;
            }
            
            const formData = new FormData(cartForm);
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(cartForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok');
            })
            .then(data => {
                if (data.success) {
                    toast.success(data.message, '장바구니 담기');
                } else {
                    toast.error(data.message, '오류');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                toast.error('장바구니 추가 중 오류가 발생했습니다.', '오류');
            });
        });
    }
});

function editComment(commentId) {
    const commentItem = document.getElementById(`comment-${commentId}`);
    const commentContent = commentItem.querySelector('.comment-content');
    const editForm = document.getElementById(`edit-form-${commentId}`);
    const editTextarea = document.getElementById(`edit-textarea-${commentId}`);
    const charCount = document.getElementById(`edit-char-count-${commentId}`);
    
    commentContent.style.display = 'none';
    editForm.style.display = 'block';
    
    editTextarea.focus();
    
    function updateCharCount() {
        const count = editTextarea.value.length;
        charCount.textContent = count;
        
        if (count > 450) {
            charCount.style.color = '#ef4444';
        } else if (count > 400) {
            charCount.style.color = '#f59e0b';
        } else {
            charCount.style.color = '#374151';
        }
    }
    
    editTextarea.addEventListener('input', updateCharCount);
    updateCharCount();
}

function cancelEditComment(commentId) {
    const commentItem = document.getElementById(`comment-${commentId}`);
    const commentContent = commentItem.querySelector('.comment-content');
    const editForm = document.getElementById(`edit-form-${commentId}`);
    const editTextarea = document.getElementById(`edit-textarea-${commentId}`);
    const editIsPublished = document.getElementById(`edit-is-published-${commentId}`);
    
    const originalContent = commentContent.dataset.content;
    const originalIsPublished = commentContent.dataset.isPublished === 'true';
    
    editTextarea.value = originalContent;
    editIsPublished.checked = originalIsPublished;
    
    editForm.style.display = 'none';
    commentContent.style.display = 'block';
}

function saveComment(commentId) {
    const editTextarea = document.getElementById(`edit-textarea-${commentId}`);
    const editIsPublished = document.getElementById(`edit-is-published-${commentId}`);
    const content = editTextarea.value.trim();
    
    if (content.length < 1) {
        alert('댓글 내용을 입력해주세요.');
        return;
    }
    
    if (content.length > 500) {
        alert('댓글은 최대 500자까지 입력 가능합니다.');
        return;
    }
    
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/reviews/comment/update/${commentId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            content: content,
            is_published: editIsPublished.checked
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const commentItem = document.getElementById(`comment-${commentId}`);
            const commentContent = commentItem.querySelector('.comment-content');
            const editForm = document.getElementById(`edit-form-${commentId}`);
            
            commentContent.dataset.content = data.comment.content;
            commentContent.dataset.isPublished = data.comment.is_published;
            
            commentContent.textContent = data.comment.content;
            
            editForm.style.display = 'none';
            commentContent.style.display = 'block';
            
            alert('댓글이 수정되었습니다.');
        } else {
            alert(data.error || '댓글 수정에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('댓글 수정 중 오류가 발생했습니다.');
    });
}

function editReview(reviewId) {
    const reviewText = document.getElementById(`review-text-${reviewId}`);
    const editForm = document.getElementById(`review-edit-form-${reviewId}`);
    const editTextarea = document.getElementById(`review-edit-textarea-${reviewId}`);
    const charCount = document.getElementById(`review-edit-char-count-${reviewId}`);
    
    reviewText.style.display = 'none';
    editForm.style.display = 'block';
    
    editTextarea.focus();
    
    function updateCharCount() {
        const count = editTextarea.value.length;
        charCount.textContent = count;
        
        if (count > 900) {
            charCount.style.color = '#ef4444';
        } else if (count > 800) {
            charCount.style.color = '#f59e0b';
        } else {
            charCount.style.color = '#374151';
        }
    }
    
    editTextarea.addEventListener('input', updateCharCount);
    updateCharCount();
}

function cancelEditReview(reviewId) {
    const reviewText = document.getElementById(`review-text-${reviewId}`);
    const editForm = document.getElementById(`review-edit-form-${reviewId}`);
    const editTextarea = document.getElementById(`review-edit-textarea-${reviewId}`);
    
    const originalContent = reviewText.dataset.content;
    const originalRating = reviewText.dataset.rating;
    
    editTextarea.value = originalContent;
    
    const ratingInput = document.querySelector(`input[name="rating-edit-${reviewId}"][value="${originalRating}"]`);
    if (ratingInput) {
        ratingInput.checked = true;
    }
    
    editForm.style.display = 'none';
    reviewText.style.display = 'block';
}

function saveReview(reviewId) {
    const editTextarea = document.getElementById(`review-edit-textarea-${reviewId}`);
    const content = editTextarea.value.trim();
    const ratingInput = document.querySelector(`input[name="rating-edit-${reviewId}"]:checked`);
    
    if (!ratingInput) {
        alert('평점을 선택해주세요.');
        return;
    }
    
    const rating = parseInt(ratingInput.value);
    
    if (content.length < 10) {
        alert('리뷰 내용을 최소 10자 이상 입력해주세요.');
        return;
    }
    
    if (content.length > 1000) {
        alert('리뷰는 최대 1000자까지 입력 가능합니다.');
        return;
    }
    
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/reviews/update/${reviewId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            content: content,
            rating: rating
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const reviewText = document.getElementById(`review-text-${reviewId}`);
            const reviewRating = document.getElementById(`review-rating-${reviewId}`);
            const editForm = document.getElementById(`review-edit-form-${reviewId}`);
            
            reviewText.dataset.content = data.review.content;
            reviewText.dataset.rating = data.review.rating;
            
            reviewText.textContent = data.review.content;
            reviewRating.textContent = data.review.star_display;
            
            editForm.style.display = 'none';
            reviewText.style.display = 'block';
            
            alert('리뷰가 수정되었습니다.');
        } else {
            alert(data.error || '리뷰 수정에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('리뷰 수정 중 오류가 발생했습니다.');
    });
}

let drawerQuantity = 1;

function openMobileDrawer() {
    const drawer = document.getElementById('mobilePurchaseDrawer');
    if (drawer) {
        drawer.classList.add('active');
    }
}

function closeMobileDrawer() {
    const drawer = document.getElementById('mobilePurchaseDrawer');
    if (drawer) {
        drawer.classList.remove('active');
    }
}

function increaseDrawerQuantity() {
    const productStock = document.querySelector('.size-quantity-section')?.dataset.productStock;
    const maxStock = productStock ? parseInt(productStock) : 0;
    
    if (drawerQuantity < maxStock) {
        drawerQuantity++;
        updateDrawerQuantity();
    } else {
        alert('재고가 부족합니다.');
    }
}

function decreaseDrawerQuantity() {
    if (drawerQuantity > 1) {
        drawerQuantity--;
        updateDrawerQuantity();
    }
}

function updateDrawerQuantity() {
    const quantityDisplay = document.getElementById('drawerQuantityDisplay');
    const quantityDisplay2 = document.getElementById('drawerQuantityDisplay2');
    const cartQuantity = document.getElementById('drawerCartQuantity');
    
    if (quantityDisplay) {
        quantityDisplay.textContent = drawerQuantity;
    }
    if (quantityDisplay2) {
        quantityDisplay2.textContent = drawerQuantity;
    }
    if (cartQuantity) {
        cartQuantity.value = drawerQuantity;
    }
    
    const unitPriceElement = document.querySelector('.unit-price');
    const totalPriceElement = document.getElementById('drawerTotalPrice');
    
    if (unitPriceElement && totalPriceElement) {
        const unitPrice = parseInt(unitPriceElement.dataset.price);
        const totalPrice = unitPrice * drawerQuantity;
        
        totalPriceElement.textContent = totalPrice.toLocaleString() + '원';
    }
}

function setupOptionButtons(btnSelector, inputId, datasetKey) {
    const buttons = document.querySelectorAll(btnSelector);
    const input = document.getElementById(inputId);
    if (!buttons.length || !input) return;

    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            buttons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const value = this.dataset[datasetKey];
            if (value) {
                input.value = value;
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    setupOptionButtons('.color-option-btn', 'selectedColorId', 'color');
    setupOptionButtons('.drawer-color-option-btn', 'drawerSelectedColorId', 'color');
    setupOptionButtons('.size-btn', 'selectedSizeId', 'sizeId');
    setupOptionButtons('.drawer-size-btn', 'drawerSelectedSizeId', 'sizeId');

    const mobileFabBtn = document.getElementById('mobileFabBtn');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const drawerClose = document.getElementById('drawerClose');
    
    if (mobileFabBtn) {
        mobileFabBtn.addEventListener('click', openMobileDrawer);
    }
    
    if (drawerOverlay) {
        drawerOverlay.addEventListener('click', closeMobileDrawer);
    }
    
    if (drawerClose) {
        drawerClose.addEventListener('click', closeMobileDrawer);
    }

    const drawerCartForm = document.querySelector('.drawer-cart-form');
    if (drawerCartForm) {
        drawerCartForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const drawerCartQuantity = document.getElementById('drawerCartQuantity');
            const drawerQuantityDisplay = document.getElementById('drawerQuantityDisplay');
            if (drawerCartQuantity && drawerQuantityDisplay) {
                drawerCartQuantity.value = drawerQuantityDisplay.textContent || '1';
            }

            const formData = new FormData(drawerCartForm);
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(drawerCartForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok');
            })
            .then(data => {
                if (data.success) {
                    closeMobileDrawer();
                    if (typeof toast !== 'undefined') {
                        toast.success(data.message, '장바구니 담기');
                    } else {
                        alert(data.message);
                    }
                } else {
                    if (typeof toast !== 'undefined') {
                        toast.error(data.message, '오류');
                    } else {
                        alert(data.message);
                    }
                }
            })
            .catch(error => {
                if (typeof toast !== 'undefined') {
                    toast.error('장바구니 추가 중 오류가 발생했습니다.', '오류');
                } else {
                    alert('장바구니 추가 중 오류가 발생했습니다.');
                }
            });
        });
    }
    
    const buyNowButton = document.getElementById('buyNowButton');
    if (buyNowButton) {
        buyNowButton.addEventListener('click', function () {
            handleImmediatePurchase(false);
        });
    }
    
    const drawerBuyBtn = document.getElementById('drawerBuyBtn');
    if (drawerBuyBtn) {
        drawerBuyBtn.addEventListener('click', function () {
            handleImmediatePurchase(true);
        });
    }
});

function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : '';
}

function handleImmediatePurchase(isMobileDrawer) {
    const productIdElement = document.getElementById('buyNowButton');
    if (!productIdElement) {
        alert('상품 정보를 찾을 수 없습니다.');
        return;
    }

    const isAuthenticated = productIdElement.dataset.isAuthenticated === 'true';
    const loginUrl = productIdElement.dataset.loginUrl || '/login/';
    if (!isAuthenticated) {
        const nextUrl = window.location.pathname + window.location.search;
        window.location.href = `${loginUrl}?next=${encodeURIComponent(nextUrl)}`;
        return;
    }

    const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrftoken = csrfTokenInput ? csrfTokenInput.value : getCsrfToken();

    if (!csrftoken) {
        const nextUrl = window.location.pathname + window.location.search;
        window.location.href = `${loginUrl}?next=${encodeURIComponent(nextUrl)}`;
        return;
    }

    const productId = parseInt(productIdElement.dataset.productId || '0', 10);
    if (!productId) {
        alert('상품 정보를 찾을 수 없습니다.');
        return;
    }

    let quantity = 1;
    let colorId = null;
    let sizeId = null;

    if (isMobileDrawer) {
        const drawerQuantityDisplay = document.getElementById('drawerQuantityDisplay');
        if (drawerQuantityDisplay) {
            quantity = parseInt(drawerQuantityDisplay.textContent || '1', 10);
        }
        const drawerHiddenColorInput = document.getElementById('drawerSelectedColorId');
        if (drawerHiddenColorInput && drawerHiddenColorInput.value) {
            colorId = parseInt(drawerHiddenColorInput.value, 10);
        }
        const drawerHiddenSizeInput = document.getElementById('drawerSelectedSizeId');
        if (drawerHiddenSizeInput && drawerHiddenSizeInput.value) {
            sizeId = parseInt(drawerHiddenSizeInput.value, 10);
        }
    } else {
        const quantityDisplay = document.getElementById('quantityDisplay');
        if (quantityDisplay) {
            quantity = parseInt(quantityDisplay.textContent || '1', 10);
        }
        const hiddenColorInput = document.getElementById('selectedColorId');
        if (hiddenColorInput && hiddenColorInput.value) {
            colorId = parseInt(hiddenColorInput.value, 10);
        }
        const hiddenSizeInput = document.getElementById('selectedSizeId');
        if (hiddenSizeInput && hiddenSizeInput.value) {
            sizeId = parseInt(hiddenSizeInput.value, 10);
        }
    }

    const hasSizeOptions = document.querySelectorAll('.size-btn, .drawer-size-btn').length > 0;
    if (hasSizeOptions && !sizeId) {
        const message = '사이즈를 선택해주세요.';
        if (typeof toast !== 'undefined') {
            toast.error(message, '알림');
        } else {
            alert(message);
        }
        return;
    }

    const items = [
        {
            product_id: productId,
            quantity: quantity,
            color_id: colorId,
            size_id: sizeId,
        },
    ];

    fetch('/orders/preorder/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ items }),
    })
        .then(response => {
            // 로그인 필요로 인해 Django의 LoginRequiredMixin이 리다이렉트한 경우
            if (response.redirected && response.url.includes('/login')) {
                window.location.href = response.url;
                // 이후 체이닝 중단
                return Promise.reject(new Error('redirect_to_login'));
            }

            if (!response.ok) {
                return response
                    .json()
                    .catch(() => null)
                    .then(data => {
                        const message =
                            data && data.message
                                ? data.message
                                : '주문 처리 중 오류가 발생했습니다.';
                        throw new Error(message);
                    });
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.redirectUrl) {
                window.location.href = data.redirectUrl;
            } else {
                const message = data.message || '주문 처리 중 오류가 발생했습니다.';
                if (typeof toast !== 'undefined') {
                    toast.error(message, '오류');
                } else {
                    alert(message);
                }
            }
        })
        .catch(error => {
            // 로그인 리다이렉트는 이미 처리했으므로 추가 알림 불필요
            if (error && error.message === 'redirect_to_login') {
                return;
            }

            if (typeof toast !== 'undefined') {
                toast.error(
                    error && error.message
                        ? error.message
                        : '주문 처리 중 오류가 발생했습니다.',
                    '오류'
                );
            } else {
                alert(
                    (error && error.message) ||
                        '주문 처리 중 오류가 발생했습니다.'
                );
            }
        });
}