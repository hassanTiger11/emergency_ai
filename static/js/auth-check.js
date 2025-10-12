/**
 * Authentication Check
 * Checks if authentication is enabled and handles auth flow
 */

// Check if running in auth mode by making a quick health check
let authEnabled = false;
let currentUser = null;

// Profile picture caching configuration
const PROFILE_CACHE_KEY = 'profile_pic_cache';
const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

/**
 * Get cached profile picture for a user
 * @param {number} userId - The user's ID
 * @returns {string|null} - Cached profile picture data URL or null if not found/expired
 */
function getCachedProfilePic(userId) {
    try {
        const cache = JSON.parse(localStorage.getItem(PROFILE_CACHE_KEY) || '{}');
        const cached = cache[userId];
        
        if (cached && Date.now() - cached.timestamp < CACHE_EXPIRY) {
            console.log('💾 Using cached profile picture');
            return cached.data;
        }
        
        // Expired or not found
        if (cached) {
            console.log('⏰ Profile picture cache expired');
        }
        return null;
    } catch (e) {
        console.error('Error reading profile picture cache:', e);
        return null;
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
        console.log('💾 Profile picture cached successfully');
    } catch (e) {
        console.error('Error caching profile picture:', e);
    }
}

/**
 * Clear profile picture cache for a user (useful after picture update/delete)
 * @param {number} userId - The user's ID
 */
function clearProfilePicCache(userId) {
    try {
        const cache = JSON.parse(localStorage.getItem(PROFILE_CACHE_KEY) || '{}');
        delete cache[userId];
        localStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(cache));
        console.log('🗑️ Profile picture cache cleared');
    } catch (e) {
        console.error('Error clearing profile picture cache:', e);
    }
}

async function checkAuthStatus(retryCount = 0) {
    try {
        // Try to get auth endpoints - if they exist, auth is enabled
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
            },
            timeout: 5000  // 5 second timeout
        });
        
        // If we get a response (even 401), auth is enabled
        authEnabled = true;
        
        if (response.ok) {
            // User is authenticated
            currentUser = await response.json();
            localStorage.setItem('user_info', JSON.stringify(currentUser));
            
            // Cache profile picture for faster future loads
            if (currentUser.profile_pic_data) {
                cacheProfilePic(currentUser.id, currentUser.profile_pic_data);
            }
            
            showSidebar(currentUser);  // Pass the fresh user data
            console.log('✅ User authenticated:', currentUser.name);
            
            // Initialize sidebar conversations
            if (typeof loadConversations === 'function') {
                setTimeout(() => {
                    loadConversations();
                }, 500);
            }
            
            return true;
        } else if (response.status === 401) {
            // Auth enabled but user not logged in
            console.log('🔐 Authentication required');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            hideSidebar();
            redirectToLogin();
            return false;
        } else if (response.status === 403) {
            // Token invalid or expired
            console.log('🔐 Invalid token');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            hideSidebar();
            redirectToLogin();
            return false;
        } else if (response.status === 503) {
            // Database connection error
            console.log('❌ Database connection error - showing error page');
            window.location.href = '/db-error';
            return false;
        }
    } catch (error) {
        console.log('🔍 Auth check error:', error);
        
        // Check if we have a stored token - if yes, auth is likely enabled but server is starting
        const storedToken = localStorage.getItem('auth_token');
        if (storedToken && retryCount < 3) {
            console.log(`🔐 Found stored token - retrying auth check (attempt ${retryCount + 1}/3)...`);
            authEnabled = true;
            // Retry after a delay
            setTimeout(() => {
                checkAuthStatus(retryCount + 1);
            }, 2000);
        } else if (storedToken && retryCount >= 3) {
            console.log('🔐 Max retries reached - redirecting to login');
            redirectToLogin();
        } else {
            // No stored token and endpoint error - likely auth is disabled
            authEnabled = false;
            hideSidebar();
            console.log('⚠️  Running without authentication');
        }
    }
    
    return authEnabled;
}

function redirectToLogin() {
    // Only redirect if we're not already on the login page
    const currentPath = window.location.pathname;
    if (!currentPath.includes('login') && !currentPath.includes('db-error')) {
        console.log('🔄 Redirecting to login page...');
        window.location.href = '/login';
    } else if (currentPath.includes('login')) {
        // Already on login page, just hide sidebar
        console.log('📍 Already on login page');
        hideSidebar();
    }
}

function showSidebar(userData = null) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    
    if (sidebar) {
        sidebar.style.display = 'flex';
        console.log('👤 Sidebar shown - user authenticated');
        
        // Use fresh user data if provided, otherwise fall back to localStorage
        let user = userData;
        if (!user) {
            const userInfo = localStorage.getItem('user_info');
            if (userInfo) {
                try {
                    user = JSON.parse(userInfo);
                } catch (e) {
                    console.log('Error parsing user info:', e);
                }
            }
        }
        
        if (user) {
            const userNameElement = document.getElementById('userName');
            const userAvatarElement = document.getElementById('userAvatar');
            
            if (userNameElement) {
                userNameElement.textContent = user.name || 'User';
            }
            
            if (userAvatarElement) {
                // Try to use cached profile picture first for instant loading
                const cachedPic = user.id ? getCachedProfilePic(user.id) : null;
                
                if (cachedPic) {
                    // Use cached picture (instant load from localStorage)
                    userAvatarElement.innerHTML = `<img src="${cachedPic}" alt="Profile" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
                } else if (user.profile_pic_data) {
                    // Use fresh profile picture data
                    userAvatarElement.innerHTML = `<img src="${user.profile_pic_data}" alt="Profile" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
                } else if (user.profile_pic_url) {
                    // Fallback to URL with error handling for 404
                    const img = document.createElement('img');
                    img.src = user.profile_pic_url;
                    img.alt = 'Profile';
                    img.style.cssText = 'width: 100%; height: 100%; border-radius: 50%; object-fit: cover;';
                    img.onerror = () => {
                        console.log('🖼️ Profile picture URL failed, using emoji fallback');
                        userAvatarElement.textContent = '👨‍⚕️';
                    };
                    userAvatarElement.appendChild(img);
                } else {
                    userAvatarElement.textContent = '👨‍⚕️'; // Medical professional emoji
                }
            }
            
            console.log('👤 User data updated:', {
                name: user.name,
                email: user.email,
                profile_pic: user.profile_pic_url ? 'Yes' : 'No'
            });
        }
    }
    if (toggle) toggle.style.display = 'block';
}

function hideSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    
    if (sidebar) {
        sidebar.style.display = 'none';
        console.log('🔒 Sidebar hidden - running in guest mode');
    }
    if (toggle) toggle.style.display = 'none';
}

// Check auth status on page load
checkAuthStatus();


