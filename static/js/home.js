document.addEventListener('DOMContentLoaded', function() {

  const cookieBanner = document.getElementById('cookieBanner');
  const cookieAccept = document.getElementById('cookieAccept');
  const cookieDecline = document.getElementById('cookieDecline');

  if (!localStorage.getItem('cookieConsent')) {
    cookieBanner.classList.add('active');
  }

  if (cookieAccept) {
    cookieAccept.addEventListener('click', function() {
      localStorage.setItem('cookieConsent', 'accepted');
      cookieBanner.classList.remove('active');
    });
  }

  if (cookieDecline) {
    cookieDecline.addEventListener('click', function() {
      localStorage.setItem('cookieConsent', 'declined');
      cookieBanner.classList.remove('active');
    });
  }

  const eventOverlay = document.getElementById('eventPopupOverlay');
  const eventClose = document.getElementById('eventPopupClose');
  const eventTodayHide = document.getElementById('eventTodayHide');

  const hideUntil = localStorage.getItem('eventPopupHideUntil');
  const now = new Date().getTime();

  if (!hideUntil || now > parseInt(hideUntil)) {
    setTimeout(function() {
      eventOverlay.classList.add('active');
    }, 500);
  }

  function closeEventPopup() {
    if (eventTodayHide && eventTodayHide.checked) {
      const tomorrow = new Date();
      tomorrow.setHours(23, 59, 59, 999);
      localStorage.setItem('eventPopupHideUntil', tomorrow.getTime().toString());
    }
    eventOverlay.classList.remove('active');
  }

  if (eventClose) {
    eventClose.addEventListener('click', closeEventPopup);
  }

  if (eventOverlay) {
    eventOverlay.addEventListener('click', function(e) {
      if (e.target === eventOverlay) {
        closeEventPopup();
      }
    });
  }
});
