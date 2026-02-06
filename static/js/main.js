let siteHeader;
let lastScrollTop = 0;

document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.querySelector('.menu-toggle');
  const mobileMenu = document.getElementById('mobileMenu');
  const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
  const mobileMenuClose = document.getElementById('mobileMenuClose');
  siteHeader = document.querySelector('.site-header');
  
  let hoverTimeout;
  let isScrolling = false;
  
  function openMenu() {
    mobileMenu.classList.add('is-open');
    mobileMenuOverlay.classList.add('is-open');
    menuToggle.classList.add('active');
    document.body.classList.add('menu-open');
  }
  
  function closeMenu() {
    mobileMenu.classList.remove('is-open');
    mobileMenuOverlay.classList.remove('is-open');
    menuToggle.classList.remove('active');
    
    setTimeout(() => {
      document.body.classList.remove('menu-open');
    }, 400);
  }
  
  if (menuToggle && mobileMenu && mobileMenuOverlay) {
    menuToggle.addEventListener('click', () => {
      const isOpen = mobileMenu.classList.contains('is-open');
      if (isOpen) {
        closeMenu();
      } else {
        openMenu();
      }
    });
    
    menuToggle.addEventListener('mouseenter', () => {
      if (window.innerWidth > 768) {
        clearTimeout(hoverTimeout);
        openMenu();
      }
    });
    
    const menuContainer = document.querySelector('.site-header');
    menuContainer.addEventListener('mouseleave', () => {
      if (window.innerWidth > 768) {
        hoverTimeout = setTimeout(() => {
          closeMenu();
        }, 300);
      }
    });
    
    mobileMenu.addEventListener('mouseleave', () => {
      if (window.innerWidth > 768) {
        hoverTimeout = setTimeout(() => {
          closeMenu();
        }, 100);
      }
    });
    
    mobileMenu.addEventListener('mouseenter', () => {
      clearTimeout(hoverTimeout);
    });
    
    if (mobileMenuClose) {
      mobileMenuClose.addEventListener('click', closeMenu);
    }
    
    mobileMenuOverlay.addEventListener('click', closeMenu);
    
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 768 && !menuToggle.contains(e.target) && !mobileMenu.contains(e.target)) {
        closeMenu();
      }
    });
  }

  const searchToggle = document.getElementById('searchToggle');
  const searchDropdown = document.getElementById('searchDropdown');
  
  if (searchToggle && searchDropdown) {
    searchToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      searchDropdown.classList.toggle('active');
      
      if (searchDropdown.classList.contains('active')) {
        const input = searchDropdown.querySelector('.search-dropdown-input');
        if (input) {
          setTimeout(() => input.focus(), 100);
        }
      }
    });
    
    document.addEventListener('click', (e) => {
      if (!searchDropdown.contains(e.target) && !searchToggle.contains(e.target)) {
        searchDropdown.classList.remove('active');
      }
    });
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && searchDropdown.classList.contains('active')) {
        searchDropdown.classList.remove('active');
      }
    });
  }
  
  const mainCategoryLinks = document.querySelectorAll('.mobile-main-category a');
  const subCategories = document.querySelector('.mobile-sub-categories');
  const subCategorySections = document.querySelectorAll('.sub-category-section');
  
  let categoryHoverTimeout;
  
  function showSubCategory(category) {
    mainCategoryLinks.forEach(link => {
      link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[data-category="${category}"]`);
    if (activeLink) {
      activeLink.classList.add('active');
    }
    
    if (subCategories) {
      subCategories.classList.add('active');
    }
    
    subCategorySections.forEach(section => {
      if (section.getAttribute('data-parent') === category) {
        section.classList.add('active');
      } else {
        section.classList.remove('active');
      }
    });
  }
  
  function hideSubCategory() {
    mainCategoryLinks.forEach(link => {
      link.classList.remove('active');
    });
    
    if (subCategories) {
      subCategories.classList.remove('active');
    }
    subCategorySections.forEach(section => {
      section.classList.remove('active');
    });
  }
  
  mainCategoryLinks.forEach(link => {
    const category = link.getAttribute('data-category');
    
    link.addEventListener('click', (e) => {
      if (window.innerWidth <= 768) {
        e.preventDefault();
        
        if (link.classList.contains('active')) {
          hideSubCategory();
        } else {
          showSubCategory(category);
        }
      }
    });
    
    link.addEventListener('mouseenter', (e) => {
      if (window.innerWidth > 768) {
        clearTimeout(categoryHoverTimeout);
        showSubCategory(category);
      }
    });
  });
  
  const categoryContainer = document.querySelector('.mobile-category-nav');
  if (categoryContainer) {
    categoryContainer.addEventListener('mouseleave', () => {
      if (window.innerWidth > 768) {
        categoryHoverTimeout = setTimeout(() => {
          hideSubCategory();
        }, 200);
      }
    });
    
    categoryContainer.addEventListener('mouseenter', () => {
      if (window.innerWidth > 768) {
        clearTimeout(categoryHoverTimeout);
      }
    });
  }
});

document.addEventListener('DOMContentLoaded', function() {
  const desktopCategoryLinks = document.querySelectorAll('.category-nav a[data-category]');
  const desktopSubCategories = document.querySelector('.desktop-sub-categories');
  const desktopSubCategorySections = document.querySelectorAll('.desktop-sub-category-section');
  
  let hoverTimeout;
  
  function showDesktopSubCategory(category) {
    if (desktopSubCategories) {
      desktopSubCategories.style.display = 'block';
    }
    
    desktopSubCategorySections.forEach(section => {
      if (section.getAttribute('data-parent') === category) {
        section.classList.add('active');
      } else {
        section.classList.remove('active');
      }
    });
  }
  
  function hideDesktopSubCategory() {
    if (desktopSubCategories) {
      desktopSubCategories.style.display = 'none';
    }
    
    desktopSubCategorySections.forEach(section => {
      section.classList.remove('active');
    });
  }
  
  if (window.innerWidth > 768) {
    desktopCategoryLinks.forEach(link => {
      const category = link.getAttribute('data-category');
      
      link.addEventListener('mouseenter', () => {
        clearTimeout(hoverTimeout);
        showDesktopSubCategory(category);
      });
    });
    
    const mainNav = document.querySelector('.main-nav');
    if (mainNav) {
      mainNav.addEventListener('mouseleave', () => {
        hoverTimeout = setTimeout(() => {
          hideDesktopSubCategory();
        }, 200);
      });
      
      mainNav.addEventListener('mouseenter', () => {
        clearTimeout(hoverTimeout);
      });
    }
    
    if (desktopSubCategories) {
      desktopSubCategories.addEventListener('mouseenter', () => {
        clearTimeout(hoverTimeout);
      });
      
      desktopSubCategories.addEventListener('mouseleave', () => {
        hoverTimeout = setTimeout(() => {
          hideDesktopSubCategory();
        }, 200);
      });
    }
  }

  function handleScroll() {
    if (!siteHeader || window.innerWidth > 768) return;
    
    const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollThreshold = 10;
    
    if (Math.abs(currentScrollTop - lastScrollTop) < scrollThreshold) return;
    
    if (currentScrollTop > lastScrollTop && currentScrollTop > 100) {
      siteHeader.classList.add('hidden');
    } else {
      siteHeader.classList.remove('hidden');
    }
    
    lastScrollTop = currentScrollTop;
  }

  if (window.innerWidth <= 768) {
    window.addEventListener('scroll', handleScroll, { passive: true });
  }

  window.addEventListener('resize', () => {
    if (window.innerWidth <= 768) {
      window.addEventListener('scroll', handleScroll, { passive: true });
      if (siteHeader) {
        siteHeader.classList.remove('hidden');
      }
    } else {
      window.removeEventListener('scroll', handleScroll);
      if (siteHeader) {
        siteHeader.classList.remove('hidden');
      }
    }
  });
});


