/* ========================================
   JobNix Login Page - JavaScript
   ======================================== */

(function() {
    'use strict';

    let currentRole = 'youth';

    // ========================================
    // Role Switching
    // ========================================
    
    window.switchRole = function(role) {
        currentRole = role;
        
        // Update tabs
        document.querySelectorAll('.role-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.role === role) {
                tab.classList.add('active');
            }
        });
        
        // Update hidden input
        document.getElementById('userRole').value = role;
        
        // Update form styling based on role
        const loginBox = document.querySelector('.login-box');
        if (role === 'employer') {
            loginBox.style.borderTop = '4px solid var(--accent)';
        } else {
            loginBox.style.borderTop = '4px solid var(--primary)';
        }
    };

    // ========================================
    // Password Toggle
    // ========================================
    
    window.togglePassword = function() {
        const passwordInput = document.getElementById('password');
        const toggleButton = passwordInput.nextElementSibling;
        const icon = toggleButton.querySelector('i');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            passwordInput.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    };

    // ========================================
    // Form Validation
    // ========================================
    
    const form = document.getElementById('loginForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            const loginBtn = document.getElementById('loginBtn');
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
        });
    }

    function validateForm() {
        let isValid = true;
        
        // Clear previous errors
        document.querySelectorAll('.error-message').forEach(error => {
            error.textContent = '';
        });
        document.querySelectorAll('.error').forEach(input => {
            input.classList.remove('error');
        });
        
        // Validate username
        const username = document.getElementById('username');
        if (!username.value.trim()) {
            showError(username, 'Username or email is required');
            isValid = false;
        }
        
        // Validate password
        const password = document.getElementById('password');
        if (!password.value) {
            showError(password, 'Password is required');
            isValid = false;
        } else if (password.value.length < 6) {
            showError(password, 'Password must be at least 6 characters');
            isValid = false;
        }
        
        return isValid;
    }

    function showError(input, message) {
        input.classList.add('error');
        const errorElement = input.closest('.form-group').querySelector('.error-message');
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    // ========================================
    // Real-time Validation
    // ========================================
    
    const inputs = document.querySelectorAll('input[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('error')) {
                validateField(this);
            }
        });
    });

    function validateField(field) {
        const value = field.value.trim();
        
        // Clear previous error
        field.classList.remove('error');
        const errorElement = field.closest('.form-group')?.querySelector('.error-message');
        if (errorElement) {
            errorElement.textContent = '';
        }
        
        if (field.hasAttribute('required') && !value) {
            showError(field, 'This field is required');
            return false;
        }
        
        if (field.id === 'password' && value && value.length < 6) {
            showError(field, 'Password must be at least 6 characters');
            return false;
        }
        
        return true;
    }

    // ========================================
    // Social Login (Placeholder)
    // ========================================
    
    window.socialLogin = function(provider) {
        // This would integrate with OAuth providers
        console.log(`Social login with ${provider} - to be implemented`);
        
        // Show message
        const alertContainer = document.querySelector('.alert-container');
        if (alertContainer) {
            alertContainer.innerHTML = `
                <div class="alert alert-error">
                    <i class="fas fa-info-circle"></i>
                    ${provider.charAt(0).toUpperCase() + provider.slice(1)} login will be available soon
                </div>
            `;
        }
    };

    // ========================================
    // Enter Key Submit
    // ========================================
    
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
            const form = document.getElementById('loginForm');
            if (form && form.checkValidity()) {
                form.requestSubmit();
            }
        }
    });

    // ========================================
    // Auto-focus first input
    // ========================================
    
    window.addEventListener('load', function() {
        const usernameInput = document.getElementById('username');
        if (usernameInput && !usernameInput.value) {
            usernameInput.focus();
        }
    });

    // ========================================
    // Initialize
    // ========================================
    
    console.log('JobNix login page initialized! 🚀');

})();

