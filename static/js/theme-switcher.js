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
    if (document.body && document.body.dataset.userTheme) {
        savedTheme = document.body.dataset.userTheme;
        localStorage.setItem('theme', savedTheme);
        applyTheme(savedTheme);
    } else {
        savedTheme = localStorage.getItem('theme') || 'light';
        applyTheme(savedTheme);
    }
})();

document.addEventListener('DOMContentLoaded', function() {
    // Re-apply theme after DOM loads (in case body wasn't available before)
    let savedTheme = 'light';
    if (document.body.dataset.userTheme) {
        savedTheme = document.body.dataset.userTheme;
        localStorage.setItem('theme', savedTheme);
    } else {
        savedTheme = localStorage.getItem('theme') || 'light';
    }
    applyTheme(savedTheme);
    
    // Ensure theme persists across all page navigations
    document.querySelectorAll('a[href], button[type="submit"], form').forEach(el => {
        el.addEventListener('click', function(e) {
            // Save current theme before navigation
            const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
            localStorage.setItem('theme', currentTheme);
        }, true); // Use capture phase to ensure it runs before navigation
    });
    
    // Also intercept form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
            localStorage.setItem('theme', currentTheme);
        });
    });
});

