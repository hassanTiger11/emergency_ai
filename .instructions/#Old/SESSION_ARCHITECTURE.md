# 📚 Session Management Architecture

## 🎯 Problem & Solution

### The Problem
The original API used a **single global recorder** that all users shared:
```python
recorder = Recorder()  # ONE recorder for everyone! ❌
```

**Issues:**
- User A starts recording → User B opens app → they both use the same recorder
- Recording conflicts between devices
- No way to track which recording belongs to which device
- All files mixed together in output folder

### The Solution
**Session-based architecture** where each browser/device gets a unique session ID:
- Each device maintains its own session ID (stored in browser localStorage)
- Backend maintains a dictionary of recorders (one per session)
- Files are saved with session ID prefix for easy tracking

---

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   Frontend      │
│   (Browser)     │
│                 │
│  localStorage:  │
│  session_id =   │
│  "abc-123..."   │
└────────┬────────┘
         │
         │ POST /api/start-recording
         │ { session_id: "abc-123..." }
         ▼
┌─────────────────┐
│   Backend API   │
│                 │
│  SessionManager │
│  {              │
│    "abc-123":   │ ◄── Recorder for Device 1
│      Recorder() │
│    "xyz-789":   │ ◄── Recorder for Device 2
│      Recorder() │
│    "def-456":   │ ◄── Recorder for Device 3
│      Recorder() │
│  }              │
└─────────────────┘
```

---

## 🔧 Implementation Details

### 1. Frontend: Session ID Generation

**Location:** `static/index_with_sessions.html`

```javascript
function getOrCreateSessionId() {
    // Check if session ID exists in browser
    let sessionId = localStorage.getItem('paramedic_session_id');
    
    if (!sessionId) {
        // Generate new UUID v4
        sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
        // Store in browser permanently
        localStorage.setItem('paramedic_session_id', sessionId);
    }
    return sessionId;
}

const SESSION_ID = getOrCreateSessionId();
```

**How it works:**
1. When user opens the app, JavaScript checks `localStorage`
2. If no session ID exists → generates new UUID and saves it
3. If session ID exists → reuses it (same device, multiple visits)
4. Session ID is sent with EVERY API request

**Key Points:**
- ✅ Session persists across browser refreshes
- ✅ Each browser tab gets same session ID (same device)
- ✅ Clearing browser data = new session
- ✅ Different browsers = different sessions

---

### 2. Backend: Session Manager

**Location:** `api_with_sessions.py`

```python
class SessionManager:
    """Manages multiple recording sessions"""
    def __init__(self):
        self.sessions: Dict[str, Recorder] = {}  # session_id → Recorder
        self._lock = threading.Lock()  # Thread safety
    
    def get_or_create_recorder(self, session_id: str) -> Recorder:
        """Get existing recorder or create new one"""
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = Recorder()
            return self.sessions[session_id]
```

**How it works:**
1. Backend maintains dictionary: `{session_id: Recorder}`
2. When request comes in, extracts `session_id` from request body
3. Looks up recorder for that session (or creates new one)
4. Each recorder is independent (separate threads, separate audio buffers)

**Thread Safety:**
- Uses `threading.Lock()` to prevent race conditions
- Multiple devices can record simultaneously without conflicts

---

### 3. API Endpoints

#### Start Recording
```python
@app.post("/api/start-recording")
async def start_recording(request: SessionRequest):
    session_id = request.session_id
    
    # Get or create recorder for THIS session
    recorder = session_manager.get_or_create_recorder(session_id)
    
    if recorder.is_recording():
        raise HTTPException(400, "Already recording for this session")
    
    recorder.start()
    return {"status": "recording", "session_id": session_id}
```

#### Stop Recording
```python
@app.post("/api/stop-recording")
async def stop_recording(request: SessionRequest):
    session_id = request.session_id
    
    # Get recorder for THIS session
    recorder = session_manager.get_recorder(session_id)
    
    if not recorder:
        raise HTTPException(404, "Session not found")
    
    recorder.stop()
    audio = recorder.get_audio()
    
    # Process audio...
    # Save with session prefix
    save_outputs(transcript, analysis, session_id, timestamp)
```

---

### 4. File Storage

Files are saved with session prefix for easy tracking:

**Format:** `{session_id_short}_{timestamp}_{type}.ext`

**Example:**
```
output/
  abc12345_20251002143012_recording.wav
  abc12345_20251002143012_transcript.txt
  abc12345_20251002143012_analysis.json
  abc12345_20251002143012_report.txt
  
  xyz78901_20251002143045_recording.wav
  xyz78901_20251002143045_transcript.txt
  ...
```

**Benefits:**
- ✅ Easy to find all recordings from one device
- ✅ Sort by session ID to group conversations
- ✅ Timestamp shows when recording happened

---

## 🔄 Complete Flow Example

### Scenario: Two Paramedics, Two Devices

**Device 1 (Tablet A):**
1. Opens app → generates `session_id: "abc-123-..."`
2. Clicks "Start Recording" → sends `{session_id: "abc-123"}`
3. Backend creates `Recorder()` for "abc-123"
4. Records for 2 minutes
5. Clicks "Stop" → processes audio → saves as `abc12345_*.wav`

**Device 2 (Tablet B):**
1. Opens app → generates `session_id: "xyz-789-..."`
2. Clicks "Start Recording" → sends `{session_id: "xyz-789"}`
3. Backend creates NEW `Recorder()` for "xyz-789"
4. Records for 3 minutes (WHILE Device 1 is still recording!)
5. Clicks "Stop" → processes audio → saves as `xyz78901_*.wav`

**No conflicts!** Each has its own recorder, own thread, own files.

---

## 🎨 Session ID Display

The UI shows a shortened session ID for user awareness:

```javascript
// Full ID: abc12345-6789-4abc-yxxx-123456789012
// Displayed: abc12345...

document.getElementById('sessionDisplay').textContent = 
    SESSION_ID.substring(0, 8) + '...';
```

**Why show it?**
- Users can verify they're on the right device
- Helps with debugging ("My session is abc12345...")
- Makes it clear each device is independent

---

## 🔐 Security & Privacy Notes

### Current Implementation (No Auth)
- Session ID is stored in browser `localStorage`
- Anyone with access to the device can use that session
- Session ID is not a secure authentication token

### For Production (Recommendations)
1. **Add Authentication:**
   ```python
   - User login system
   - JWT tokens
   - Session tied to user account
   ```

2. **Session Expiry:**
   ```python
   - Auto-cleanup old sessions after 24 hours
   - Require re-authentication periodically
   ```

3. **Encryption:**
   ```python
   - Encrypt session IDs in transit (HTTPS - already done on Render)
   - Encrypt stored recordings
   ```

4. **Access Control:**
   ```python
   - Limit who can view/download recordings
   - Audit logs for file access
   ```

---

## 🧹 Session Cleanup

### Automatic Cleanup (Not Implemented Yet)
You could add automatic session cleanup:

```python
# In SessionManager
def cleanup_old_sessions(self, max_age_hours=24):
    """Remove sessions older than max_age_hours"""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    with self._lock:
        old_sessions = [
            sid for sid, recorder in self.sessions.items()
            if recorder.created_at < cutoff and not recorder.is_recording()
        ]
        for sid in old_sessions:
            del self.sessions[sid]
```

### Manual Cleanup
```javascript
// Frontend: Clear session and start fresh
function resetSession() {
    localStorage.removeItem('paramedic_session_id');
    location.reload();
}
```

---

## 📊 Admin Endpoints

### View Active Sessions
```bash
GET /api/sessions

Response:
{
  "active_sessions": 3,
  "session_ids": ["abc12345...", "xyz78901...", "def45678..."]
}
```

### Cleanup Session
```bash
POST /api/cleanup-session
{
  "session_id": "abc-123-..."
}
```

---

## 🚀 Testing Multi-Device Setup

### Test Locally

1. **Open two browser windows:**
   ```
   Window 1: http://localhost:8000
   Window 2: http://localhost:8000 (incognito/different browser)
   ```

2. **Check session IDs:**
   - Look at header → should show different IDs
   - Check browser console → logs session ID

3. **Record simultaneously:**
   - Window 1: Start recording
   - Window 2: Start recording (should work!)
   - Both should record independently

4. **Check output folder:**
   ```
   output/
     abc12345_*  ← Window 1 files
     xyz78901_*  ← Window 2 files
   ```

### Test on Render

1. **Deploy the new code**
2. **Open from different devices:**
   - Laptop
   - Phone
   - Tablet
3. **Each should have its own session**

---

## ⚡ Performance Considerations

### Memory Usage
- Each session = 1 Recorder instance
- Each Recorder holds audio in memory until processed
- **Recommendation:** Limit max sessions or add auto-cleanup

### Concurrent Recording
- Multiple recorders use different audio input streams
- **Note:** On server deployment, you may not have audio input
  - Solution: Implement file upload endpoint for pre-recorded audio

---

## 🔄 Migration Guide

### From Old API to New API

**Step 1:** Backup current `api.py`:
```bash
cp api.py api_old.py
```

**Step 2:** Replace files:
```bash
cp api_with_sessions.py api.py
cp static/index_with_sessions.html static/index.html
```

**Step 3:** Test locally:
```bash
python api.py
# Open http://localhost:8000 in multiple tabs
```

**Step 4:** Deploy to Render:
```bash
git add .
git commit -m "Add session management for multi-device support"
git push origin main
```

---

## 🎓 Key Takeaways

1. **Session ID = Device Identity**
   - Each browser gets unique ID
   - Stored in localStorage (persists across visits)

2. **Backend Maintains Session Dictionary**
   - `{session_id: Recorder}`
   - Each recorder is independent

3. **Thread-Safe Operations**
   - Uses locks to prevent race conditions
   - Multiple devices can record simultaneously

4. **Files Tracked by Session**
   - Easy to find all recordings from one device
   - Format: `{session_id}_{timestamp}_{type}`

5. **No Conflicts**
   - Each device has own recorder
   - Recordings don't interfere with each other

---

## 📝 Summary

This session management system allows multiple paramedics to use the same deployed application simultaneously without conflicts. Each device maintains its own recording session, and all files are tracked by session ID for easy organization.

**Before:** ONE global recorder (conflicts!)
**After:** ONE recorder PER device (no conflicts!)

Perfect for field deployment where multiple paramedics need to use the system at the same time! 🚑

