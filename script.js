// Wait for the page to fully load
document.addEventListener('DOMContentLoaded', () => {

    const burgerBtn = document.getElementById('burger-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    // Check if the elements exist before adding an event listener
    if (burgerBtn && mobileMenu) {
        burgerBtn.addEventListener('click', () => {
            // Toggle the 'active' class to show/hide the menu
            mobileMenu.classList.toggle('active');
        });
    }

});