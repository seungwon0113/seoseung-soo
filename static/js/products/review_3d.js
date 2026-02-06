document.addEventListener('DOMContentLoaded', function() {
    const sphereContainer = document.querySelector('.review-sphere-container');
    const spheres = document.querySelectorAll('.review-sphere');
    const detailPanel = document.querySelector('.review-detail-panel');
    const closePanel = document.querySelector('.close-panel');
    
    if (!sphereContainer || !spheres.length) return;
    
    const isMobile = window.innerWidth <= 768;
    const SPHERE_RADIUS = isMobile ? 15 : 20;
    const MIN_DISTANCE = SPHERE_RADIUS * 2 + 5;
    const HORIZONTAL_PADDING = isMobile ? 20 : 100;
    
    let selectedSphere = null;
    let offsetX = 0;
    let offsetY = 0;
    let isDragging = false;
    
    function getContainerSize() {
        return {
            width: sphereContainer.offsetWidth,
            height: sphereContainer.offsetHeight
        };
    }
    
    function initializeSpheres() {
        const { width, height } = getContainerSize();   
        
        if (width === 0 || height === 0) {
            setTimeout(initializeSpheres, 100);
            return;
        }
        
        const positions = [];
        
        spheres.forEach((sphere, index) => {
            let x, y;
            let attempts = 0;
            const maxAttempts = 100;
            
            do {
                x = HORIZONTAL_PADDING + Math.random() * (width - SPHERE_RADIUS * 2 - HORIZONTAL_PADDING * 2);
                y = Math.random() * (height - SPHERE_RADIUS * 2);
                attempts++;
            } while (isOverlapping(x, y, positions) && attempts < maxAttempts);
            
            positions.push({ x, y });
            
            sphere.style.left = `${x}px`;
            sphere.style.top = `${y}px`;
            sphere.dataset.index = index;
        });
    }
    
    function isOverlapping(x, y, positions) {
        for (let pos of positions) {
            const dx = (x + SPHERE_RADIUS) - (pos.x + SPHERE_RADIUS);
            const dy = (y + SPHERE_RADIUS) - (pos.y + SPHERE_RADIUS);
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < MIN_DISTANCE) {
                return true;
            }
        }
        return false;
    }
    
    setTimeout(initializeSpheres, 100);
    
    spheres.forEach(sphere => {
        sphere.addEventListener('mousedown', e => {
            e.preventDefault();
            selectedSphere = sphere;
            isDragging = false;
            
            const rect = sphere.getBoundingClientRect();
            const containerRect = sphereContainer.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            
            sphere.style.zIndex = '20';
            sphere.classList.add('dragging');
        });
        
        sphere.addEventListener('touchstart', e => {
            e.preventDefault();
            const touch = e.touches[0];
            selectedSphere = sphere;
            isDragging = false;
            
            const rect = sphere.getBoundingClientRect();
            offsetX = touch.clientX - rect.left;
            offsetY = touch.clientY - rect.top;
            
            sphere.style.zIndex = '20';
            sphere.classList.add('dragging');
        }, { passive: false });
        
        const handleSphereClick = function(e) {
            if (!isDragging) {
                const reviewId = parseInt(this.dataset.reviewId);
                showReviewModal(reviewId);
            }
        };
        
        sphere.addEventListener('click', handleSphereClick);
        sphere.addEventListener('touchend', function(e) {
            if (!isDragging) {
                e.preventDefault();
                handleSphereClick.call(this, e);
            }
        }, { passive: false });
    });
    
    document.addEventListener('mousemove', e => {
        if (!selectedSphere) return;
        e.preventDefault();
        isDragging = true;
        
        const { width, height } = getContainerSize();
        const containerRect = sphereContainer.getBoundingClientRect();
        let x = e.clientX - containerRect.left - offsetX;
        let y = e.clientY - containerRect.top - offsetY;
        
        x = Math.max(HORIZONTAL_PADDING, Math.min(width - SPHERE_RADIUS * 2 - HORIZONTAL_PADDING, x));
        y = Math.max(0, Math.min(height - SPHERE_RADIUS * 2, y));
        
        selectedSphere.style.left = `${x}px`;
        selectedSphere.style.top = `${y}px`;
        
        checkCollision(selectedSphere);
    });
    
    document.addEventListener('touchmove', e => {
        if (!selectedSphere) return;
        e.preventDefault();
        isDragging = true;
        
        const { width, height } = getContainerSize();
        const touch = e.touches[0];
        const containerRect = sphereContainer.getBoundingClientRect();
        let x = touch.clientX - containerRect.left - offsetX;
        let y = touch.clientY - containerRect.top - offsetY;
        
        x = Math.max(HORIZONTAL_PADDING, Math.min(width - SPHERE_RADIUS * 2 - HORIZONTAL_PADDING, x));
        y = Math.max(0, Math.min(height - SPHERE_RADIUS * 2, y));
        
        selectedSphere.style.left = `${x}px`;
        selectedSphere.style.top = `${y}px`;
        
        checkCollision(selectedSphere);
    }, { passive: false });

    document.addEventListener('mouseup', () => {
        if (selectedSphere) {
            selectedSphere.style.zIndex = '';
            selectedSphere.classList.remove('dragging');
            selectedSphere = null;
        }
    });
    
    document.addEventListener('touchend', () => {
        if (selectedSphere) {
            selectedSphere.style.zIndex = '';
            selectedSphere.classList.remove('dragging');
            selectedSphere = null;
        }
        setTimeout(() => {
            isDragging = false;
        }, 100);
    });
    
    function checkCollision(currentSphere) {
        const { width, height } = getContainerSize();
        const rect1 = currentSphere.getBoundingClientRect();
        const containerRect = sphereContainer.getBoundingClientRect();
        const r1 = SPHERE_RADIUS;
        const x1 = rect1.left - containerRect.left + r1;
        const y1 = rect1.top - containerRect.top + r1;
        
        spheres.forEach(otherSphere => {
            if (otherSphere === currentSphere) return;
            
            const rect2 = otherSphere.getBoundingClientRect();
            const r2 = SPHERE_RADIUS;
            const x2 = rect2.left - containerRect.left + r2;
            const y2 = rect2.top - containerRect.top + r2;
            
            const dx = x2 - x1;
            const dy = y2 - y1;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < MIN_DISTANCE && distance > 0) {
                const overlap = MIN_DISTANCE - distance;
                const angle = Math.atan2(dy, dx);
                const moveX = overlap * Math.cos(angle);
                const moveY = overlap * Math.sin(angle);
                
                const otherX = parseFloat(otherSphere.style.left || 0) + moveX;
                const otherY = parseFloat(otherSphere.style.top || 0) + moveY;
                
                const boundedX = Math.max(HORIZONTAL_PADDING, Math.min(width - SPHERE_RADIUS * 2 - HORIZONTAL_PADDING, otherX));
                const boundedY = Math.max(0, Math.min(height - SPHERE_RADIUS * 2, otherY));
                
                gsap.to(otherSphere, {
                    left: boundedX,
                    top: boundedY,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            }
        });
    }
    
    const reviewModal = document.getElementById('reviewModal');
    const modalClose = document.querySelector('.modal-close');
    const modalOverlay = document.querySelector('.modal-overlay');
    const modalImages = document.getElementById('modalImages');
    const modalAvatar = document.getElementById('modalAvatar');
    const modalUsername = document.getElementById('modalUsername');
    const modalRating = document.getElementById('modalRating');
    const modalReviewText = document.getElementById('modalReviewText');
    const modalDate = document.getElementById('modalDate');
    const modalPrev = document.getElementById('modalPrev');
    const modalNext = document.getElementById('modalNext');
    
    if (!reviewModal || !modalImages || !modalAvatar || !modalUsername || !modalRating || !modalReviewText || !modalDate) {
    }
    
    if (!reviewModal) {
        return;
    }
    
    let currentReviewIndex = 0;
    let currentReviewId = null;
    let sliderCurrentIndex = 0;
    let slideInterval = null;
    
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;
    let isSwiping = false;
    const SWIPE_THRESHOLD = 50;
    
    let nextReviewTimeout;
    function showNextReview() {
        if (!window.reviewData || window.reviewData.length === 0) return;
        
        clearTimeout(nextReviewTimeout);
        nextReviewTimeout = setTimeout(() => {
            const nextIndex = (currentReviewIndex + 1) % window.reviewData.length;
            currentReviewIndex = nextIndex;
            sliderCurrentIndex = 0;
            showReviewModal(window.reviewData[nextIndex].id);
            updateNavButtons();
        }, 100);
    }
    
    let prevReviewTimeout;
    function showPrevReview() {
        if (!window.reviewData || window.reviewData.length === 0) return;
        
        clearTimeout(prevReviewTimeout);
        prevReviewTimeout = setTimeout(() => {
            const prevIndex = (currentReviewIndex - 1 + window.reviewData.length) % window.reviewData.length;
            currentReviewIndex = prevIndex;
            sliderCurrentIndex = 0;
            showReviewModal(window.reviewData[prevIndex].id);
            updateNavButtons();
        }, 100);
    }
    
    function updateNavButtons() {
        if (!window.reviewData || window.reviewData.length === 0) return;
        
        const isFirst = currentReviewIndex === 0;
        const isLast = currentReviewIndex === window.reviewData.length - 1;
        
        if (modalPrev) {
            if (window.reviewData.length === 1) {
                modalPrev.style.display = 'none';
            } else {
                modalPrev.style.display = 'flex';
                modalPrev.style.opacity = isFirst ? '0.3' : '1';
            }
        }
        
        if (modalNext) {
            if (window.reviewData.length === 1) {
                modalNext.style.display = 'none';
            } else {
                modalNext.style.display = 'flex';
                modalNext.style.opacity = isLast ? '0.3' : '1';
            }
        }
    }
    
    function showReviewModal(reviewId) {
        if (slideInterval) {
            clearInterval(slideInterval);
            slideInterval = null;
        }
        
        if (!window.reviewData || window.reviewData.length === 0) {
            return;
        }
        
        const review = window.reviewData.find(r => r.id === reviewId);
        if (!review) {
            return;
        }
        
        currentReviewIndex = window.reviewData.findIndex(r => r.id === reviewId);
        currentReviewId = reviewId;
        
        modalAvatar.innerHTML = '';
        if (review.hasProfileImage && review.profileImage) {
            const img = document.createElement('img');
            img.src = review.profileImage;
            img.alt = review.username;
            modalAvatar.appendChild(img);
        } else {
            modalAvatar.textContent = 'S';
        }
        
        modalUsername.textContent = review.username;
        modalRating.textContent = review.rating;
        modalReviewText.textContent = review.content;
        modalDate.textContent = review.date;
        
        modalImages.innerHTML = '';
        modalImages.classList.remove('no-image');
        
        if (review.images.length > 0) {
            if (review.images.length > 1) {
                modalImages.classList.add('slideshow');
            }
            
            review.images.forEach((imageUrl, index) => {
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = '리뷰 이미지';
                img.className = index === 0 ? 'active' : '';
                img.style.objectFit = window.innerWidth <= 768 ? 'contain' : 'cover';
                modalImages.appendChild(img);
            });
            
            if (review.images.length > 1) {
                let currentImageIndex = 0;
                slideInterval = setInterval(() => {
                    if (!reviewModal || !reviewModal.classList.contains('active')) {
                        clearInterval(slideInterval);
                        return;
                    }
                    
                    const images = modalImages ? modalImages.querySelectorAll('img') : [];
                    if (images.length === 0) {
                        clearInterval(slideInterval);
                        return;
                    }
                    
                    if (images[currentImageIndex]) {
                        images[currentImageIndex].classList.remove('active');
                    }
                    currentImageIndex = (currentImageIndex + 1) % images.length;
                    if (images[currentImageIndex]) {
                        images[currentImageIndex].classList.add('active');
                    }
                }, 1000);
            }
        } 
        else if (review.productImages && review.productImages.length > 0) {
            modalImages.classList.add('slideshow');
            
            review.productImages.forEach((imageUrl, index) => {
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = '상품 이미지';
                img.className = index === 0 ? 'active' : '';
                img.style.objectFit = window.innerWidth <= 768 ? 'contain' : 'cover';
                modalImages.appendChild(img);
            });
            
            let currentImageIndex = 0;
            slideInterval = setInterval(() => {
                if (!reviewModal || !reviewModal.classList.contains('active')) {
                    clearInterval(slideInterval);
                    return;
                }
                
                const images = modalImages ? modalImages.querySelectorAll('img') : [];
                if (images.length === 0) {
                    clearInterval(slideInterval);
                    return;
                }
                
                if (images[currentImageIndex]) {
                    images[currentImageIndex].classList.remove('active');
                }
                currentImageIndex = (currentImageIndex + 1) % images.length;
                if (images[currentImageIndex]) {
                    images[currentImageIndex].classList.add('active');
                }
            }, 1000);
        }
        else {
            modalImages.classList.add('no-image');
            modalImages.textContent = '📷';
        }
        
        reviewModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        updateNavButtons();
        
        if (modalImages) {
            modalImages.style.transition = 'none';
            modalImages.style.transform = 'translateX(0%)';
            setTimeout(() => {
                modalImages.style.transition = '';
            }, 300);
        }
        
        const chatBot = document.querySelector('.floating-chat');
        if (chatBot) {
            chatBot.style.display = 'none';
        }
        
        if (window.innerWidth <= 768) {
            document.addEventListener('touchmove', preventScroll, { passive: false });
        }
    }
    
    function preventScroll(e) {
        e.preventDefault();
    }
    
    function closeReviewModal() {
        if (reviewModal) {
            reviewModal.classList.remove('active');
        }
        if (modalImages) {
            modalImages.classList.remove('slideshow');
        }
        document.body.style.overflow = '';
        
        if (window.innerWidth <= 768) {
            document.removeEventListener('touchmove', preventScroll);
        }
        
        const chatBot = document.querySelector('.floating-chat');
        if (chatBot) {
            chatBot.style.display = '';
        }
    }
    
    if (modalClose) {
        modalClose.addEventListener('click', closeReviewModal);
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', closeReviewModal);
    }
    
    if (modalPrev) {
        modalPrev.addEventListener('click', (e) => {
            e.stopPropagation();
            showPrevReview();
        });
    }
    
    if (modalNext) {
        modalNext.addEventListener('click', (e) => {
            e.stopPropagation();
            showNextReview();
        });
    }
    
    if (reviewModal) {
        const modalContent = reviewModal.querySelector('.modal-container') || reviewModal;
        
        modalContent.addEventListener('touchstart', function(e) {
            if (!reviewModal.classList.contains('active')) return;
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            isSwiping = true;
        }, { passive: true });
        
        modalContent.addEventListener('touchmove', function(e) {
            if (!isSwiping || !reviewModal.classList.contains('active')) return;
            touchEndX = e.touches[0].clientX;
            touchEndY = e.touches[0].clientY;
            
            const diffX = touchEndX - touchStartX;
            const diffY = Math.abs(touchEndY - touchStartY);
            
            if (Math.abs(diffX) > diffY && Math.abs(diffX) > 10) {
                e.preventDefault();
            }
        }, { passive: false });
        
        modalContent.addEventListener('touchend', function(e) {
            if (!isSwiping || !reviewModal.classList.contains('active')) return;
            
            const diffX = touchEndX - touchStartX;
            const diffY = Math.abs(touchEndY - touchStartY);
            
            if (Math.abs(diffX) > diffY && Math.abs(diffX) > SWIPE_THRESHOLD) {
                if (diffX > 0) {
                    showPrevReview();
                } else {
                    showNextReview();
                }
            }
            
            // 리셋
            touchStartX = 0;
            touchStartY = 0;
            touchEndX = 0;
            touchEndY = 0;
            isSwiping = false;
        }, { passive: true });
    }
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && reviewModal && reviewModal.classList.contains('active')) {
            closeReviewModal();
        }
        
        if (reviewModal && reviewModal.classList.contains('active')) {
            if (e.key === 'ArrowLeft') {
                showPrevReview();
            } else if (e.key === 'ArrowRight') {
                showNextReview();
            }
        }
    });
    
    const expandBtn = document.getElementById('sphereExpandBtn');
    if (expandBtn) {
        expandBtn.addEventListener('click', function() {
            sphereContainer.classList.add('expanded');
            const spheresHeight = sphereContainer.querySelector('.review-spheres').scrollHeight;
            sphereContainer.style.height = spheresHeight + 40 + 'px';
        });
    }
});