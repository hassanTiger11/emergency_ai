# 2-Day Performance Optimization Roadmap

## Timeline: October 9-11, 2025

## Day 1 (Oct 9): Database & Profile Picture Optimization

### Phase 1A: Profile Picture Optimization (3-4 hours)

**Problem**: Profile pictures stored as base64 (up to 5MB) cause slow initial load times.

**Implementation**:

1. **Add image compression on backend** (`endpoints/user_routes.py`)

   - Install Pillow dependency (already in requirements.txt)
   - Add compression function before base64 encoding
   - Resize images to max 300x300px
   - Compress to 80% quality JPEG
   - Expected size reduction: 5MB → ~50-100KB (95% smaller)

```python
# In endpoints/user_routes.py, around line 115
from PIL import Image
import io

def compress_profile_picture(file_content: bytes, max_size: int = 300) -> bytes:
    """Compress and resize profile picture"""
    img = Image.open(io.BytesIO(file_content))
    
    # Convert RGBA to RGB if needed
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Resize maintaining aspect ratio
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # Compress to JPEG
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=80, optimize=True)
    return output.getvalue()
```


2. **Update profile picture upload endpoint**

   - Apply compression before base64 encoding (line 115-118)
   - Update existing profile pictures with compressed versions

3. **Add browser-side caching** (`static/js/auth-check.js`)

   - Cache profile picture data in localStorage with 24-hour expiry
   - Load from cache first, fetch from API only if expired/missing
   - Expected improvement: 3-5 seconds → 0.1-0.3 seconds

```javascript
// In static/js/auth-check.js
const PROFILE_CACHE_KEY = 'profile_pic_cache';
const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours

function getCachedProfilePic(userId) {
    const cache = JSON.parse(localStorage.getItem(PROFILE_CACHE_KEY) || '{}');
    const cached = cache[userId];
    if (cached && Date.now() - cached.timestamp < CACHE_EXPIRY) {
        return cached.data;
    }
    return null;
}

function cacheProfilePic(userId, data) {
    const cache = JSON.parse(localStorage.getItem(PROFILE_CACHE_KEY) || '{}');
    cache[userId] = { data, timestamp: Date.now() };
    localStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(cache));
}
```


### Phase 1B: Database Query Optimization (2-3 hours)

**Problem**: Loading all conversations at once with full JSON analysis data is slow.

**Implementation**:

1. **Add database indexes** (create migration file `database/add_indexes.py`)

   - Index on `conversations.paramedic_id` and `conversations.created_at`
   - Index on `paramedics.email`
   - Expected query speed: 500ms → 50-100ms

```python
# Create new file: database/add_indexes.py
from database.connection import engine
from sqlalchemy import text

def add_performance_indexes():
    with engine.connect() as conn:
        # Add indexes for faster queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_paramedic_created 
            ON conversations(paramedic_id, created_at DESC);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
            ON conversations(session_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_paramedics_email 
            ON paramedics(email);
        """))
        conn.commit()

if __name__ == "__main__":
    add_performance_indexes()
    print("Indexes created successfully")
```


2. **Add pagination to conversations endpoint** (`endpoints/user_routes.py`)

   - Modify `/api/user/conversations` to support `page` and `limit` parameters
   - Default to 10 conversations per page
   - Add pagination metadata in response

```python
# Update in endpoints/user_routes.py around line 167
@router.get("/conversations", response_model=dict)
async def get_conversations(
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 10
):
    offset = (page - 1) * limit
    
    conversations = db.query(Conversation).filter(
        Conversation.paramedic_id == current_user.id
    ).order_by(Conversation.created_at.desc()).offset(offset).limit(limit).all()
    
    total = db.query(Conversation).filter(
        Conversation.paramedic_id == current_user.id
    ).count()
    
    summaries = []
    for conv in conversations:
        summary = ConversationSummary(
            id=conv.id,
            session_id=conv.session_id,
            created_at=conv.created_at
        )
        if isinstance(conv.analysis, dict):
            summary.patient_name = conv.analysis.get('patient_name')
            summary.chief_complaint = conv.analysis.get('chief_complaint')
        summaries.append(summary)
    
    return {
        "conversations": summaries,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "has_more": offset + limit < total
        }
    }
```


3. **Implement lazy loading in frontend** (`static/js/sidebar.js`)

   - Load initial 10 conversations
   - Add "Load More" button
   - Implement infinite scroll (optional)

```javascript
// Update in static/js/sidebar.js
let currentPage = 1;
let hasMore = true;

async function loadConversations(page = 1) {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    try {
        const response = await fetch(`/api/user/conversations?page=${page}&limit=10`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (page === 1) {
                displayConversations(data.conversations);
            } else {
                appendConversations(data.conversations);
            }
            
            hasMore = data.pagination.has_more;
            currentPage = page;
            
            updateLoadMoreButton();
        }
    } catch (error) {
        console.error('Failed to load conversations:', error);
    }
}

function appendConversations(conversations) {
    const listContainer = document.getElementById('conversationsList');
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
}
```


### Phase 1C: Response Caching Strategy (1-2 hours)

**Implementation**:

1. **Add conversation caching in frontend**

   - Cache loaded conversations in memory
   - Reuse cached data when clicking same conversation
   - Invalidate cache after new recording

```javascript
// In static/js/sidebar.js
const conversationCache = new Map();

async function loadConversation(conversationId) {
    // Check cache first
    if (conversationCache.has(conversationId)) {
        displayReport(conversationCache.get(conversationId));
        return;
    }
    
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    try {
        const response = await fetch(`/api/user/conversations/${conversationId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const conversation = await response.json();
            conversationCache.set(conversationId, conversation);
            displayReport(conversation);
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
    }
}
```


## Day 2 (Oct 10-11): UI Responsiveness & Testing

### Phase 2A: Loading States & Visual Feedback (2-3 hours)

**Implementation**:

1. **Add loading skeletons** (`static/css/sidebar.css`)

   - Show skeleton loaders while profile picture loads
   - Show skeleton for conversation list
   - Smooth transitions when data arrives

```css
/* Add to static/css/sidebar.css */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.profile-skeleton {
    width: 50px;
    height: 50px;
    border-radius: 50%;
}

.conversation-skeleton {
    height: 60px;
    margin-bottom: 10px;
    border-radius: 8px;
}
```


2. **Progressive loading indicators** (`static/js/auth-check.js`, `static/js/sidebar.js`)

   - Show immediate placeholder
   - Update with cached data if available
   - Replace with fresh data when loaded

### Phase 2B: Performance Testing & Metrics (2-3 hours)

**Implementation**:

1. **Add performance monitoring**

   - Measure page load time
   - Track API response times
   - Log cache hit rates

```javascript
// Add to static/js/auth-check.js
const performanceMetrics = {
    profileLoadStart: 0,
    profileLoadEnd: 0,
    conversationsLoadStart: 0,
    conversationsLoadEnd: 0,
    
    logMetrics() {
        console.log('Performance Metrics:', {
            profileLoadTime: this.profileLoadEnd - this.profileLoadStart,
            conversationsLoadTime: this.conversationsLoadEnd - this.conversationsLoadStart
        });
    }
};
```


2. **Optimize bundle size**

   - Review and remove unused console.log statements
   - Minify JavaScript files (optional, for production)

3. **Test on Render.com**

   - Deploy changes to Render
   - Test with real database and network latency
   - Verify performance improvements

### Phase 2C: Final Optimizations & Polish (2-3 hours)

**Implementation**:

1. **Database connection pooling** (`database/connection.py`)

   - Configure SQLAlchemy connection pool for better performance

```python
# Update in database/connection.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
```


2. **Optimize JSON response size**

   - Only return necessary fields in conversation summaries
   - Compress large JSON responses if needed

3. **Add error handling for slow connections**

   - Timeout handling for API calls
   - Retry logic with exponential backoff
   - User-friendly error messages

## Expected Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Profile Picture Load | 3-5 sec | 0.3-0.5 sec | 85% faster |
| Conversation List Load | 2-3 sec | 0.3-0.5 sec | 85% faster |
| Clicking Conversation | 1-2 sec | 0.1-0.3 sec | 90% faster |
| Database Queries | 500ms | 50-100ms | 80% faster |
| Initial Page Load | 5-8 sec | 1-2 sec | 75% faster |

## Key Files to Modify

1. `endpoints/user_routes.py` - Profile picture compression, pagination
2. `static/js/auth-check.js` - Profile picture caching
3. `static/js/sidebar.js` - Conversation lazy loading, caching
4. `database/add_indexes.py` - New file for database indexes
5. `database/connection.py` - Connection pooling
6. `static/css/sidebar.css` - Loading skeletons
7. `database/schemas.py` - Update response models for pagination

## Testing Checklist

- [ ] Profile pictures load in under 1 second
- [ ] Conversation list loads in under 1 second
- [ ] Clicking conversations shows immediate cached response
- [ ] Load more button works correctly
- [ ] Database indexes applied successfully
- [ ] No regression in existing functionality
- [ ] All optimizations deployed to Render.com

### To-dos

- [ ] Add image compression function and update profile picture upload endpoint to compress images to 300x300px at 80% quality
- [ ] Implement browser-side profile picture caching with 24-hour expiry in auth-check.js
- [ ] Create database migration script and add performance indexes for conversations and paramedics tables
- [ ] Add pagination support to conversations endpoint with page and limit parameters
- [ ] Implement lazy loading with Load More button in sidebar.js for conversations
- [ ] Add in-memory conversation caching to avoid re-fetching clicked conversations
- [ ] Add CSS skeleton loaders and progressive loading indicators for better UX
- [ ] Configure SQLAlchemy connection pooling in database/connection.py
- [ ] Test all optimizations on Render.com and verify 70-80% performance improvements
