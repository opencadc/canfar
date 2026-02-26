// Mobile navigation visibility with better breakpoints
document.addEventListener('DOMContentLoaded', function() {
    function ensureMobileMenu() {
        const hamburgerButton = document.querySelector('.md-header__button.md-icon[for="__drawer"]');
        const tabs = document.querySelector('.md-tabs');
        const header = document.querySelector('.md-header');
        
        // Show hamburger menu on screens smaller than 1440px (instead of 1219px)
        if (hamburgerButton && window.innerWidth <= 1440) {
            hamburgerButton.style.display = 'block';
            hamburgerButton.style.visibility = 'visible';
            console.log('Mobile menu visible at width:', window.innerWidth);
        } else if (hamburgerButton && window.innerWidth > 1440) {
            // Hide hamburger on large screens where tabs should be visible
            hamburgerButton.style.display = 'none';
        }
        
        // Ensure tabs are visible on desktop
        if (tabs && window.innerWidth > 1440) {
            tabs.style.display = 'block';
        }
        
        // Force refresh of navigation state
        if (header) {
            header.style.position = 'relative';
            setTimeout(() => {
                header.style.position = '';
            }, 10);
        }
    }
    
    // Run on load
    ensureMobileMenu();
    
    // Run on resize
    window.addEventListener('resize', ensureMobileMenu);
    
    // Run after Material theme initializes
    setTimeout(ensureMobileMenu, 100);
    setTimeout(ensureMobileMenu, 500);
});
