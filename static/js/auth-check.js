/**
 * Authentication Check
 * Checks if authentication is enabled and handles auth flow
 */

// Check if running in auth mode by making a quick health check
let authEnabled = false;
let currentUser = null;

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
            console.log('🔐 Authentication required - redirecting to login');
            redirectToLogin();
            return false;
        } else if (response.status === 403) {
            // Token invalid or expired
            console.log('🔐 Invalid token - redirecting to login');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            redirectToLogin();
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
    if (!window.location.pathname.includes('login')) {
        console.log('🔄 Redirecting to login page...');
        window.location.href = '/login';
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
                // Use profile picture if available, otherwise use emoji
                if (user.profile_pic_url) {
                    userAvatarElement.innerHTML = `<img src="${user.profile_pic_url}" alt="Profile" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
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


