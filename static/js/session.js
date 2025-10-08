/**
 * Session Management Module
 * Handles session ID generation and persistence
 */

function getOrCreateSessionId() {
    let sessionId = localStorage.getItem('paramedic_session_id');
    if (!sessionId) {
        sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
        localStorage.setItem('paramedic_session_id', sessionId);
        console.log('📱 Created new session:', sessionId);
    } else {
        console.log('📱 Using existing session:', sessionId);
    }
    return sessionId;
}

const SESSION_ID = getOrCreateSessionId();

// Initialize session display
if (document.getElementById('sessionDisplay')) {
    document.getElementById('sessionDisplay').textContent = SESSION_ID.substring(0, 8) + '...';
}

