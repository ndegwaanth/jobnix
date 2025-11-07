/* ========================================
   JobNix Dashboard - JavaScript
   ======================================== */

(function() {
    'use strict';

    // ========================================
    // Mobile Menu Toggle
    // ========================================
    
    const sidebar = document.querySelector('.sidebar');
    const menuToggle = document.querySelector('.menu-toggle');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // ========================================
    // Smooth Animations
    // ========================================
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const fadeInObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Animate stat cards
    document.querySelectorAll('.stat-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        fadeInObserver.observe(card);
    });

    // Animate dashboard cards
    document.querySelectorAll('.dashboard-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        fadeInObserver.observe(card);
    });

    // ========================================
    // Real-time Updates (Placeholder)
    // ========================================
    
    // This would connect to WebSockets or polling for real-time updates
    function updateNotifications() {
        // Real-time notification updates
        console.log('Dashboard initialized');
    }

    // ========================================
    // Initialize
    // ========================================
    
    window.addEventListener('load', () => {
        updateNotifications();
        console.log('JobNix dashboard initialized! 🚀');
    });

})();

