/**
 * Settings Page JavaScript
 * Handles user profile and settings management
 */

// Check authentication
const authToken = localStorage.getItem('auth_token');
if (!authToken) {
    window.location.href = '/login.html';
}

// Profile picture caching configuration (same as auth-check.js)
const PROFILE_CACHE_KEY = 'profile_pic_cache';

/**
 * Clear profile picture cache for a user
 * @param {number} userId - The user's ID
 */
function clearProfilePicCache(userId) {
    try {
        const cache = JSON.parse(localStorage.getItem(PROFILE_CACHE_KEY) || '{}');
        delete cache[userId];
        localStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(cache));
        console.log('🗑️ Profile picture cache cleared for user:', userId);
    } catch (e) {
        console.error('Error clearing profile picture cache:', e);
    }
}

/**
 * Cache profile picture for a user
 * @param {number} userId - The user's ID
 * @param {string} data - Profile picture data URL
 */
function cacheProfilePic(userId, data) {
    try {
        const cache = JSON.parse(localStorage.getItem(PROFILE_CACHE_KEY) || '{}');
        cache[userId] = { 
            data, 
            timestamp: Date.now() 
        };
        localStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(cache));
        console.log('💾 Profile picture cached successfully for user:', userId);
    } catch (e) {
        console.error('Error caching profile picture:', e);
    }
}

// Get authorization headers
function getAuthHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
    };
}

// Show message
function showMessage(text, type = 'success') {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// Load user profile
async function loadProfile() {
    try {
        const response = await fetch('/api/user/profile', {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const user = await response.json();
            
            // Update form fields
            document.getElementById('name').value = user.name || '';
            document.getElementById('email').value = user.email || '';
            document.getElementById('age').value = user.age || '';
            document.getElementById('medicalId').value = user.medical_id || '';
            document.getElementById('nationalId').value = user.national_id || '';
            
            // Update profile picture
            if (user.profile_pic_data) {
                const container = document.getElementById('profilePicContainer');
                container.innerHTML = `<img src="${user.profile_pic_data}" class="profile-pic-preview" alt="Profile">`;
                document.getElementById('deletePhotoBtn').style.display = 'inline-block';
            } else if (user.profile_pic_url) {
                // Fallback to URL with error handling for 404
                const container = document.getElementById('profilePicContainer');
                const img = document.createElement('img');
                img.src = user.profile_pic_url;
                img.className = 'profile-pic-preview';
                img.alt = 'Profile';
                img.onerror = () => {
                    console.log('🖼️ Profile picture URL failed in settings, using placeholder');
                    container.innerHTML = '<div class="profile-pic-placeholder" id="profilePicPlaceholder">👤</div>';
                };
                container.appendChild(img);
                document.getElementById('deletePhotoBtn').style.display = 'inline-block';
            }
            
            // Update localStorage
            localStorage.setItem('user_info', JSON.stringify(user));
        } else if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            window.location.href = '/login.html';
        }
    } catch (error) {
        showMessage('Failed to load profile', 'error');
    }
}

// Update profile
document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        age: document.getElementById('age').value ? parseInt(document.getElementById('age').value) : null
    };
    
    try {
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const user = await response.json();
            localStorage.setItem('user_info', JSON.stringify(user));
            showMessage('Profile updated successfully!', 'success');
        } else {
            const data = await response.json();
            showMessage(data.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    }
});

// Update password
document.getElementById('passwordForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        showMessage('Passwords do not match!', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ password: newPassword })
        });
        
        if (response.ok) {
            showMessage('Password updated successfully!', 'success');
            document.getElementById('passwordForm').reset();
        } else {
            const data = await response.json();
            showMessage(data.detail || 'Failed to update password', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    }
});

// Upload profile picture
document.getElementById('profilePicInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
        showMessage('File too large. Maximum size is 5MB.', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/user/profile-picture', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (response.ok) {
            const user = await response.json();
            localStorage.setItem('user_info', JSON.stringify(user));
            
            // Clear old cache and cache new profile picture
            clearProfilePicCache(user.id);
            if (user.profile_pic_data) {
                cacheProfilePic(user.id, user.profile_pic_data);
            }
            
            // Update preview
            const container = document.getElementById('profilePicContainer');
            if (user.profile_pic_data) {
                container.innerHTML = `<img src="${user.profile_pic_data}" class="profile-pic-preview" alt="Profile">`;
            } else if (user.profile_pic_url) {
                // Use URL with error handling
                const img = document.createElement('img');
                img.src = user.profile_pic_url + '?t=' + Date.now();
                img.className = 'profile-pic-preview';
                img.alt = 'Profile';
                img.onerror = () => {
                    console.log('🖼️ Profile picture URL failed after upload, using placeholder');
                    container.innerHTML = '<div class="profile-pic-placeholder" id="profilePicPlaceholder">👤</div>';
                };
                container.appendChild(img);
            }
            document.getElementById('deletePhotoBtn').style.display = 'inline-block';
            
            showMessage('Profile picture uploaded successfully!', 'success');
        } else {
            const data = await response.json();
            showMessage(data.detail || 'Failed to upload picture', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    }
});

// Delete profile picture
document.getElementById('deletePhotoBtn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete your profile picture?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/user/profile-picture', {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const user = await response.json();
            localStorage.setItem('user_info', JSON.stringify(user));
            
            // Clear cached profile picture
            clearProfilePicCache(user.id);
            
            // Reset to placeholder
            const container = document.getElementById('profilePicContainer');
            container.innerHTML = '<div class="profile-pic-placeholder" id="profilePicPlaceholder">👤</div>';
            document.getElementById('deletePhotoBtn').style.display = 'none';
            
            showMessage('Profile picture deleted successfully!', 'success');
        } else {
            showMessage('Failed to delete picture', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    }
});

// Logout
document.getElementById('logoutBtn').addEventListener('click', () => {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login.html';
    }
});

// Load profile on page load
loadProfile();


