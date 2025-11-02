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

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const body = document.body;
    const themeIcons = document.querySelectorAll('#theme-icon');
    
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
        // Update all theme icons
        themeIcons.forEach(icon => {
            icon.className = 'fas fa-sun';
        });
    } else {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        // Update all theme icons
        themeIcons.forEach(icon => {
            icon.className = 'fas fa-moon';
        });
    }
});

