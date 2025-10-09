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
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    try {
        const response = await fetch('/api/user/conversations', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const conversations = await response.json();
            displayConversations(conversations);
        }
    } catch (error) {
        console.error('Failed to load conversations:', error);
    }
}

// Display conversations in sidebar
function displayConversations(conversations) {
    const listContainer = document.getElementById('conversationsList');
    
    if (!conversations || conversations.length === 0) {
        listContainer.innerHTML = '<p class="no-conversations">No previous sessions</p>';
        return;
    }
    
    listContainer.innerHTML = conversations.map(conv => {
        const date = new Date(conv.created_at);
        const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const title = conv.patient_name || conv.chief_complaint || `Session ${conv.session_id.substring(0, 8)}`;
        
        return `
            <button class="conversation-item" onclick="loadConversation(${conv.id})">
                <div class="conversation-title">${title}</div>
                <div class="conversation-date">${dateStr}</div>
            </button>
        `;
    }).join('');
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
        
        if (userAvatar && user.profile_pic_url) {
            userAvatar.innerHTML = `<img src="${user.profile_pic_url}" alt="Profile">`;
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


