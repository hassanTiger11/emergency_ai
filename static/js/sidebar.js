/**
 * Sidebar JavaScript
 * Handles sidebar toggle and conversation history
 */

// Initialize sidebar state
let sidebarOpen = false;

// Pagination state
let currentPage = 1;
let hasMore = true;
let isLoadingConversations = false;

// Conversation caching
const conversationCache = new Map();

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
async function startNewSession() {
    console.log('🆕 Starting new session...');
    
    // Check if currently recording and save if needed
    if (typeof window.isRecording !== 'undefined' && window.isRecording) {
        console.log('💾 Currently recording - saving current session first...');
        try {
            // Stop current recording and save it
            if (typeof stopRecording === 'function') {
                await stopRecording();
            }
            // Wait a bit for the upload to complete
            await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (error) {
            console.warn('⚠️ Failed to save current recording:', error);
        }
    }
    
    // Clear current report
    const reportSection = document.getElementById('reportSection');
    if (reportSection) {
        reportSection.innerHTML = '';
        reportSection.style.display = 'none';
    }
    
    // Generate new session ID
    const newSessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
    
    // Update global session ID
    sessionId = newSessionId;
    localStorage.setItem('paramedic_session_id', newSessionId);
    
    // Update session display
    const sessionDisplay = document.getElementById('sessionDisplay');
    if (sessionDisplay) {
        sessionDisplay.textContent = newSessionId.substring(0, 8) + '...';
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
    
    // Reset any global recording state
    if (typeof window.isRecording !== 'undefined') {
        window.isRecording = false;
    }
    if (typeof window.isProcessing !== 'undefined') {
        window.isProcessing = false;
    }
    
    console.log('✅ Started new session:', newSessionId);
}

// Load conversations from API (with pagination)
async function loadConversations(page = 1) {
    console.log('🔄 loadConversations called, page:', page);
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) {
        console.log('🔄 No auth token, skipping conversation load');
        return;
    }
    
    if (isLoadingConversations) {
        console.log('🔄 Already loading conversations, skipping...');
        return;
    }
    
    isLoadingConversations = true;
    
    try {
        console.log('🔄 Fetching conversations from API...');
        const response = await fetch(`/api/user/conversations?page=${page}&limit=10`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        console.log('🔄 API response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('🔄 API returned data:', data);
            
            const conversations = data.conversations || [];
            const pagination = data.pagination || {};
            
            if (page === 1) {
                // First page - replace all conversations
                displayConversations(conversations);
            } else {
                // Additional pages - append conversations
                appendConversations(conversations);
            }
            
            // Update pagination state
            currentPage = pagination.page || page;
            hasMore = pagination.has_more || false;
            
            // Update Load More button visibility
            updateLoadMoreButton();
        } else {
            console.log('🔄 API error:', response.status, response.statusText);
            const errorText = await response.text();
            console.log('🔄 Error details:', errorText);
        }
    } catch (error) {
        console.error('🔄 Failed to load conversations:', error);
    } finally {
        isLoadingConversations = false;
    }
}

// Load more conversations (next page)
async function loadMoreConversations() {
    if (!hasMore || isLoadingConversations) {
        console.log('🔄 No more conversations to load or already loading');
        return;
    }
    
    console.log('🔄 Loading more conversations, page:', currentPage + 1);
    await loadConversations(currentPage + 1);
}

// Display conversations in sidebar (replaces existing list)
function displayConversations(conversations) {
    console.log('📋 displayConversations called with:', conversations);
    const listContainer = document.getElementById('conversationsList');
    
    if (!conversations || conversations.length === 0) {
        console.log('📋 No conversations, showing empty message');
        listContainer.innerHTML = '<p class="no-conversations">No previous sessions</p>';
        updateLoadMoreButton();
        return;
    }
    
    console.log(`📋 Processing ${conversations.length} conversations`);
    const html = conversations.map(conv => {
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
    
    listContainer.innerHTML = html;
    updateLoadMoreButton();
}

// Append conversations to existing list (for pagination)
function appendConversations(conversations) {
    console.log('📋 appendConversations called with:', conversations);
    const listContainer = document.getElementById('conversationsList');
    
    if (!conversations || conversations.length === 0) {
        console.log('📋 No conversations to append');
        return;
    }
    
    console.log(`📋 Appending ${conversations.length} conversations`);
    
    // Remove "Load More" button temporarily
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.remove();
    }
    
    const html = conversations.map(conv => {
        const smartTime = formatSmartTime(conv.created_at);
        const title = conv.patient_name || conv.chief_complaint || `Session ${conv.session_id.substring(0, 8)}`;
        
        return `
            <button class="conversation-item" onclick="loadConversation(${conv.id})">
                <div class="conversation-title">${title}</div>
                <div class="conversation-date">${smartTime}</div>
            </button>
        `;
    }).join('');
    
    listContainer.insertAdjacentHTML('beforeend', html);
    updateLoadMoreButton();
}

// Update Load More button visibility
function updateLoadMoreButton() {
    const listContainer = document.getElementById('conversationsList');
    let loadMoreBtn = document.getElementById('loadMoreBtn');
    
    // Remove existing button
    if (loadMoreBtn) {
        loadMoreBtn.remove();
    }
    
    // Add button if there are more conversations to load
    if (hasMore) {
        loadMoreBtn = document.createElement('button');
        loadMoreBtn.id = 'loadMoreBtn';
        loadMoreBtn.className = 'load-more-btn';
        loadMoreBtn.textContent = isLoadingConversations ? 'Loading...' : 'Load More';
        loadMoreBtn.disabled = isLoadingConversations;
        loadMoreBtn.onclick = loadMoreConversations;
        
        listContainer.appendChild(loadMoreBtn);
        console.log('📋 Load More button added');
    }
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

// Load a specific conversation (with caching)
async function loadConversation(conversationId) {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    // Check cache first for instant loading
    if (conversationCache.has(conversationId)) {
        console.log('💾 Loading conversation from cache:', conversationId);
        const conversation = conversationCache.get(conversationId);
        displayConversationData(conversation);
        return;
    }
    
    try {
        console.log('🔄 Fetching conversation from API:', conversationId);
        const response = await fetch(`/api/user/conversations/${conversationId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const conversation = await response.json();
            
            // Cache the conversation for future instant loading
            conversationCache.set(conversationId, conversation);
            console.log('💾 Conversation cached:', conversationId);
            
            displayConversationData(conversation);
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
    }
}

// Display conversation data (separated for reuse)
function displayConversationData(conversation) {
    // Update session ID display
    sessionId = conversation.session_id;
    document.getElementById('sessionDisplay').textContent = conversation.session_id.substring(0, 8);
    
    // Display the report - pass the full conversation object
    if (typeof displayReport === 'function') {
        displayReport(conversation);
    }
    
    // Mark as active
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.conversation-item')?.classList.add('active');
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
        // Clear cache and reload conversations after successful upload
        const authToken = localStorage.getItem('auth_token');
        if (authToken) {
            conversationCache.clear();  // Clear cache to show new conversation
            currentPage = 1;  // Reset to first page
            hasMore = true;
            setTimeout(() => loadConversations(1), 1000);
        }
        return result;
    };
}


