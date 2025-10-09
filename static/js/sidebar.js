/**
 * Sidebar JavaScript
 * Handles sidebar toggle and conversation history
 */

// Initialize sidebar state
let sidebarOpen = false;

// Toggle sidebar
document.getElementById('sidebarToggle')?.addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    sidebarOpen = !sidebarOpen;
    
    if (sidebarOpen) {
        sidebar.classList.add('open');
    } else {
        sidebar.classList.remove('open');
    }
});

// Start new session
function startNewSession() {
    // Clear current report
    document.getElementById('reportSection').innerHTML = '';
    
    // Generate new session ID
    if (typeof generateSessionId === 'function') {
        const newSessionId = generateSessionId();
        sessionId = newSessionId;
        document.getElementById('sessionDisplay').textContent = newSessionId.substring(0, 8);
    }
    
    // Reset recording state
    const recordButton = document.getElementById('recordButton');
    const buttonText = document.getElementById('buttonText');
    const statusText = document.getElementById('statusText');
    
    if (recordButton) {
        recordButton.className = 'record-button idle';
        buttonText.textContent = 'Start Recording';
        statusText.textContent = 'Click the button to begin';
    }
    
    console.log('Started new session');
}

// Load conversations from API
async function loadConversations() {
    console.log('🔄 loadConversations called');
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) {
        console.log('🔄 No auth token, skipping conversation load');
        return;
    }
    
    try {
        console.log('🔄 Fetching conversations from API...');
        const response = await fetch('/api/user/conversations', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        console.log('🔄 API response status:', response.status);
        
        if (response.ok) {
            const conversations = await response.json();
            console.log('🔄 API returned conversations:', conversations);
            displayConversations(conversations);
        } else {
            console.log('🔄 API error:', response.status, response.statusText);
            const errorText = await response.text();
            console.log('🔄 Error details:', errorText);
        }
    } catch (error) {
        console.error('🔄 Failed to load conversations:', error);
    }
}

// Display conversations in sidebar
function displayConversations(conversations) {
    console.log('📋 displayConversations called with:', conversations);
    const listContainer = document.getElementById('conversationsList');
    
    if (!conversations || conversations.length === 0) {
        console.log('📋 No conversations, showing empty message');
        listContainer.innerHTML = '<p class="no-conversations">No previous sessions</p>';
        return;
    }
    
    console.log(`📋 Processing ${conversations.length} conversations`);
    listContainer.innerHTML = conversations.map(conv => {
        console.log('📋 Processing conversation:', conv);
        const smartTime = formatSmartTime(conv.created_at);
        const title = conv.patient_name || conv.chief_complaint || `Session ${conv.session_id.substring(0, 8)}`;
        
        console.log('📋 Final display:', { title, smartTime });
        
        return `
            <button class="conversation-item" onclick="loadConversation(${conv.id})">
                <div class="conversation-title">${title}</div>
                <div class="conversation-date">${smartTime}</div>
            </button>
        `;
    }).join('');
}

// Smart time formatting with timezone auto-detection
function formatSmartTime(dateString) {
    console.log('🕒 formatSmartTime called with:', dateString);
    
    // Tag the timestamp to UTC with a Z label "ISO 8601"
    let utcString = dateString;
    if (!dateString.endsWith('Z') && !dateString.includes('+')) {
        utcString = dateString + 'Z';
    }

    const date = new Date(utcString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    console.log('🕒 Time calculation:', {
        date: date.toISOString(),
        now: now.toISOString(),
        diffHours,
        diffDays
    });
    
    // Recent: relative time (more user-friendly)
    if (diffHours < 1) {
        console.log('🕒 Returning: Just now');
        return "Just now";
    }
    if (diffHours < 24) {
        console.log(`🕒 Returning: ${diffHours} hours ago`);
        return `${diffHours} hours ago`;
    }
    if (diffDays === 1) {
        console.log('🕒 Returning: Yesterday');
        return "Yesterday";
    }
    if (diffDays < 7) {
        console.log(`🕒 Returning: ${diffDays} days ago`);
        return `${diffDays} days ago`;
    }
    
    // Older: show with timezone (more precise)
    try {
        // Auto-detect user's timezone
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        console.log('🕒 User timezone:', userTimezone);
        
        const result = date.toLocaleString('en-US', {
            timeZone: userTimezone,
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            timeZoneName: 'short'
        });
        console.log('🕒 Returning timezone format:', result);
        return result;
        // Result: "Oct 7 at 11:00 PM AST"
    } catch (error) {
        console.log('🕒 Timezone error, using fallback:', error);
        // Fallback to simple date if timezone detection fails
        const fallback = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        console.log('🕒 Returning fallback:', fallback);
        return fallback;
    }
}

// Load a specific conversation
async function loadConversation(conversationId) {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    try {
        const response = await fetch(`/api/user/conversations/${conversationId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const conversation = await response.json();
            
            // Update session ID display
            sessionId = conversation.session_id;
            document.getElementById('sessionDisplay').textContent = conversation.session_id.substring(0, 8);
            
            // Display the report
            if (typeof displayReport === 'function') {
                displayReport(conversation.analysis);
            }
            
            // Mark as active
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.closest('.conversation-item')?.classList.add('active');
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
    }
}

// Update user profile in sidebar
function updateSidebarUser() {
    const userInfo = localStorage.getItem('user_info');
    if (userInfo) {
        const user = JSON.parse(userInfo);
        
        const userName = document.getElementById('userName');
        const userAvatar = document.getElementById('userAvatar');
        
        if (userName) {
            userName.textContent = user.name || user.email;
        }
        
        if (userAvatar) {
            if (user.profile_pic_data) {
                userAvatar.innerHTML = `<img src="${user.profile_pic_data}" alt="Profile">`;
            } else if (user.profile_pic_url) {
                // Fallback to URL with error handling for 404
                const img = document.createElement('img');
                img.src = user.profile_pic_url;
                img.alt = 'Profile';
                img.onerror = () => {
                    console.log('🖼️ Profile picture URL failed in sidebar, using emoji fallback');
                    userAvatar.textContent = '👨‍⚕️';
                };
                userAvatar.appendChild(img);
            }
        }
    }
}

// Initialize sidebar on page load
// Wait for auth check to complete, then initialize sidebar
setTimeout(() => {
    const authToken = localStorage.getItem('auth_token');
    if (authToken) {
        updateSidebarUser();
        loadConversations();
    }
}, 1000);

// Reload conversations after successful recording
const originalUploadAudio = window.uploadAudio;
if (originalUploadAudio) {
    window.uploadAudio = async function(...args) {
        const result = await originalUploadAudio.apply(this, args);
        // Reload conversations after successful upload
        const authToken = localStorage.getItem('auth_token');
        if (authToken) {
            setTimeout(loadConversations, 1000);
        }
        return result;
    };
}


