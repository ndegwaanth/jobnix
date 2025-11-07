/* ========================================
   JobNix Signup Page - JavaScript
   ======================================== */

(function() {
    'use strict';

    let selectedRole = '';

    // ========================================
    // Role Selection
    // ========================================
    
    window.selectRole = function(role) {
        selectedRole = role;
        
        // Hide role selection
        const roleSelection = document.getElementById('roleSelection');
        const signupForm = document.getElementById('signupForm');
        
        roleSelection.style.display = 'none';
        signupForm.style.display = 'block';
        
        // Set role in form
        document.getElementById('userRole').value = role;
        
        // Update role badge
        const roleBadge = document.getElementById('selectedRoleBadge');
        roleBadge.textContent = role === 'youth' ? 'Job Seeker / Youth' : 'Employer';
        roleBadge.className = 'role-badge ' + role;
        
        // Show/hide role-specific fields
        const youthFields = document.getElementById('youthFields');
        const employerFields = document.getElementById('employerFields');
        
        if (role === 'youth') {
            youthFields.style.display = 'block';
            employerFields.style.display = 'none';
            // Make employer fields not required
            const employerRequired = employerFields.querySelectorAll('[required]');
            employerRequired.forEach(field => field.removeAttribute('required'));
        } else {
            youthFields.style.display = 'none';
            employerFields.style.display = 'block';
            // Make youth fields not required
            const youthRequired = youthFields.querySelectorAll('[required]');
            youthRequired.forEach(field => field.removeAttribute('required'));
        }
        
        // Add visual feedback
        document.querySelectorAll('.role-card').forEach(card => {
            card.classList.remove('selected');
            if (card.dataset.role === role) {
                card.classList.add('selected');
            }
        });
        
        // Smooth scroll to form
        signupForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    // ========================================
    // Go Back to Role Selection
    // ========================================
    
    window.goBack = function() {
        const roleSelection = document.getElementById('roleSelection');
        const signupForm = document.getElementById('signupForm');
        
        roleSelection.style.display = 'block';
        signupForm.style.display = 'none';
        
        selectedRole = '';
        document.getElementById('userRole').value = '';
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // ========================================
    // Password Toggle
    // ========================================
    
    window.togglePassword = function(inputId) {
        const input = document.getElementById(inputId);
        const button = input.nextElementSibling;
        const icon = button.querySelector('i');
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    };

    // ========================================
    // Password Strength Indicator
    // ========================================
    
    const passwordInput = document.getElementById('password');
    const passwordStrength = document.getElementById('passwordStrength');
    const strengthFill = passwordStrength.querySelector('.strength-fill');
    const strengthText = passwordStrength.querySelector('.strength-text');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            
            strengthFill.className = 'strength-fill ' + strength.level;
            strengthText.textContent = strength.text;
            
            if (password.length === 0) {
                strengthFill.style.width = '0%';
                strengthText.textContent = 'Password strength';
            }
        });
    }

    function calculatePasswordStrength(password) {
        let strength = 0;
        
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^a-zA-Z0-9]/.test(password)) strength++;
        
        if (strength <= 2) {
            return { level: 'weak', text: 'Weak password' };
        } else if (strength <= 4) {
            return { level: 'medium', text: 'Medium strength' };
        } else {
            return { level: 'strong', text: 'Strong password' };
        }
    }

    // ========================================
    // Form Validation
    // ========================================
    
    const form = document.getElementById('registrationForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
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
            showError(username, 'Username is required');
            isValid = false;
        } else if (username.value.length < 3) {
            showError(username, 'Username must be at least 3 characters');
            isValid = false;
        }
        
        // Validate email
        const email = document.getElementById('email');
        if (!email.value.trim()) {
            showError(email, 'Email is required');
            isValid = false;
        } else if (!isValidEmail(email.value)) {
            showError(email, 'Please enter a valid email address');
            isValid = false;
        }
        
        // Validate password
        const password = document.getElementById('password');
        if (!password.value) {
            showError(password, 'Password is required');
            isValid = false;
        } else if (password.value.length < 8) {
            showError(password, 'Password must be at least 8 characters');
            isValid = false;
        }
        
        // Validate password confirmation
        const confirmPassword = document.getElementById('confirmPassword');
        if (!confirmPassword.value) {
            showError(confirmPassword, 'Please confirm your password');
            isValid = false;
        } else if (password.value !== confirmPassword.value) {
            showError(confirmPassword, 'Passwords do not match');
            isValid = false;
        }
        
        // Validate phone
        const phone = document.getElementById('phone');
        if (!phone.value.trim()) {
            showError(phone, 'Phone number is required');
            isValid = false;
        } else if (!isValidPhone(phone.value)) {
            showError(phone, 'Please enter a valid phone number');
            isValid = false;
        }
        
        // Validate role-specific required fields
        if (selectedRole === 'employer') {
            const companyName = document.getElementById('companyName');
            if (!companyName.value.trim()) {
                showError(companyName, 'Company name is required');
                isValid = false;
            }
        }
        
        // Validate terms
        const terms = document.getElementById('terms');
        if (!terms.checked) {
            const termsError = terms.closest('.checkbox-group').querySelector('.error-message');
            termsError.textContent = 'You must agree to the terms and conditions';
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

    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function isValidPhone(phone) {
        const phoneRegex = /^[\d\s\-\+\(\)]+$/;
        return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
    }

    // ========================================
    // Real-time Validation
    // ========================================
    
    const inputs = document.querySelectorAll('input, select');
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
        
        // Validate based on field type
        if (field.hasAttribute('required') && !value) {
            showError(field, 'This field is required');
            return false;
        }
        
        if (field.type === 'email' && value && !isValidEmail(value)) {
            showError(field, 'Please enter a valid email address');
            return false;
        }
        
        if (field.id === 'phone' && value && !isValidPhone(value)) {
            showError(field, 'Please enter a valid phone number');
            return false;
        }
        
        if (field.id === 'confirmPassword' && value) {
            const password = document.getElementById('password').value;
            if (value !== password) {
                showError(field, 'Passwords do not match');
                return false;
            }
        }
        
        if (field.id === 'username' && value && value.length < 3) {
            showError(field, 'Username must be at least 3 characters');
            return false;
        }
        
        return true;
    }

    // ========================================
    // Check URL for role parameter
    // ========================================
    
    window.addEventListener('load', function() {
        const urlParams = new URLSearchParams(window.location.search);
        const roleParam = urlParams.get('role');
        
        if (roleParam && (roleParam === 'youth' || roleParam === 'employer' || roleParam === 'institution')) {
            // Auto-select role if provided in URL
            setTimeout(() => {
                selectRole(roleParam);
            }, 300);
        }
    });

    // ========================================
    // Initialize
    // ========================================
    
    console.log('JobNix signup page initialized! 🚀');

})();

