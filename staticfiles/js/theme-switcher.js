// Theme Switcher JavaScript
function toggleTheme() {
    const body = document.body;
    const themeIcons = document.querySelectorAll('#theme-icon');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    let newTheme;
    if (currentTheme === 'light') {
        newTheme = 'dark';
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
        // Update all theme icons
        themeIcons.forEach(icon => {
            icon.className = 'fas fa-sun';
        });
    } else {
        newTheme = 'light';
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        // Update all theme icons
        themeIcons.forEach(icon => {
            icon.className = 'fas fa-moon';
        });
    }
    
    localStorage.setItem('theme', newTheme);
    
    // Update theme preference on server
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        fetch('/accounts/update-theme/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ theme: newTheme })
        }).catch(err => console.error('Failed to update theme:', err));
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to apply theme immediately
function applyTheme(theme) {
    const body = document.body;
    const themeIcons = document.querySelectorAll('#theme-icon');
    
    if (theme === 'dark') {
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
        themeIcons.forEach(icon => {
            icon.className = 'fas fa-sun';
        });
    } else {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        themeIcons.forEach(icon => {
            icon.className = 'fas fa-moon';
        });
    }
    localStorage.setItem('theme', theme);
}

// Initialize theme on page load - check localStorage, server preference, and apply
(function() {
    // Apply theme IMMEDIATELY (before DOM is ready) to prevent flash
    let savedTheme = 'light';
    
    // Try to get theme from body data attribute first (server-side preference)
    if (document.body && document.body.dataset && document.body.dataset.userTheme) {
        savedTheme = document.body.dataset.userTheme;
        localStorage.setItem('theme', savedTheme);
    } else {
        // Fallback to localStorage
        savedTheme = localStorage.getItem('theme') || 'light';
    }
    
    // Apply theme immediately
    if (document.body) {
        applyTheme(savedTheme);
    }
    
    // Also try to apply when body becomes available
    const observer = new MutationObserver(function(mutations) {
        if (document.body) {
            applyTheme(savedTheme);
            observer.disconnect();
        }
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
})();

document.addEventListener('DOMContentLoaded', function() {
    // Re-apply theme after DOM loads (in case body wasn't available before)
    let savedTheme = 'light';
    if (document.body && document.body.dataset && document.body.dataset.userTheme) {
        savedTheme = document.body.dataset.userTheme;
        localStorage.setItem('theme', savedTheme);
    } else {
        savedTheme = localStorage.getItem('theme') || 'light';
    }
    applyTheme(savedTheme);
    
    // Ensure theme persists across all page navigations - use more aggressive approach
    function saveThemeBeforeNavigation() {
        const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
        localStorage.setItem('theme', currentTheme);
    }
    
    // Intercept all link clicks
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href]');
        if (link && link.href && !link.href.startsWith('javascript:') && !link.href.startsWith('#')) {
            saveThemeBeforeNavigation();
        }
    }, true);
    
    // Intercept all form submissions
    document.addEventListener('submit', function(e) {
        saveThemeBeforeNavigation();
    }, true);
    
    // Intercept all button clicks that might cause navigation
    document.addEventListener('click', function(e) {
        const button = e.target.closest('button[type="submit"]');
        if (button) {
            saveThemeBeforeNavigation();
        }
    }, true);
    
    // Also save theme periodically (every 2 seconds) as a backup
    setInterval(function() {
        if (document.body) {
            const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
            const saved = localStorage.getItem('theme');
            if (currentTheme !== saved) {
                localStorage.setItem('theme', currentTheme);
            }
        }
    }, 2000);
});


