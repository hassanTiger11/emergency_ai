/**
 * Authentication JavaScript
 * Handles login and signup functionality
 */

// Check if user is already logged in with VALID token
async function checkExistingAuth() {
    const token = localStorage.getItem('auth_token');
    if (token) {
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                // Token is valid, redirect to main page
                window.location.href = '/';
            } else {
                // Token is invalid, clear it
                console.log('🔐 Invalid token detected, clearing localStorage');
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_info');
            }
        } catch (error) {
            // Network error or server issue, clear token to be safe
            console.log('🔐 Auth check failed, clearing localStorage');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
        }
    }
}

// Run the check
checkExistingAuth();

// Toggle between login and signup forms
function toggleForms() {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    
    if (loginForm.style.display === 'none') {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
    }
    
    // Clear messages
    hideMessage();
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    document.getElementById('successMessage').style.display = 'none';
}

// Show success message
function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
}

// Hide messages
function hideMessage() {
    document.getElementById('errorMessage').style.display = 'none';
    document.getElementById('successMessage').style.display = 'none';
}

// Login form handler
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMessage();
    
    const loginBtn = document.getElementById('loginBtn');
    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';
    
    const formData = {
        email: document.getElementById('loginEmail').value,
        password: document.getElementById('loginPassword').value
    };
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store token and user info
            localStorage.setItem('auth_token', data.access_token);
            localStorage.setItem('user_info', JSON.stringify(data.user));
            
            showSuccess('Login successful! Redirecting...');
            
            // Redirect to main page
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showError(data.detail || 'Login failed. Please check your credentials.');
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    } catch (error) {
        showError('Network error. Please try again.');
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
});

// Signup form handler
document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMessage();
    
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('signupConfirmPassword').value;
    
    // Validate passwords match
    if (password !== confirmPassword) {
        showError('Passwords do not match!');
        return;
    }
    
    const signupBtn = document.getElementById('signupBtn');
    signupBtn.disabled = true;
    signupBtn.textContent = 'Creating account...';
    
    const formData = {
        name: document.getElementById('signupName').value,
        email: document.getElementById('signupEmail').value,
        medical_id: "N/A",  // Default value for MVP
        national_id: "N/A", // Default value for MVP
        age: document.getElementById('signupAge').value ? parseInt(document.getElementById('signupAge').value) : null,
        password: password
    };
    
    try {
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store token and user info
            localStorage.setItem('auth_token', data.access_token);
            localStorage.setItem('user_info', JSON.stringify(data.user));
            
            showSuccess('Account created successfully! Redirecting...');
            
            // Redirect to main page
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showError(data.detail || 'Signup failed. Please try again.');
            signupBtn.disabled = false;
            signupBtn.textContent = 'Create Account';
        }
    } catch (error) {
        showError('Network error. Please try again.');
        signupBtn.disabled = false;
        signupBtn.textContent = 'Create Account';
    }
});


