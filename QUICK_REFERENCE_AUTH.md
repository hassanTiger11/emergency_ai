# Authentication Quick Reference

## Toggle Authentication

```bash
# .env file
ENABLE_AUTH=false  # Disable (development)
ENABLE_AUTH=true   # Enable (production)
```

## Environment Variables

```bash
# Required for all modes
OPENAI_API_KEY=your_openai_api_key

# Required when ENABLE_AUTH=true
JWT_SECRET_KEY=your-secure-secret-key-min-32-chars
DATABASE_URL=postgresql://user:password@localhost:5432/emergency_ai
```

## Generate Secure JWT Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## API Endpoints Summary

### Public Endpoints (Always Available)
- `GET /` - Main page
- `GET /api/health` - Health check
- `POST /api/upload-audio` - Upload audio (saves to DB if authenticated)
- `POST /api/generate-pdf` - Generate PDF report

### Auth Endpoints (When ENABLE_AUTH=true)
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/verify-token` - Verify token

### User Endpoints (Requires Authentication)
- `GET /api/user/profile` - Get profile
- `PUT /api/user/profile` - Update profile
- `POST /api/user/profile-picture` - Upload photo
- `DELETE /api/user/profile-picture` - Delete photo
- `GET /api/user/conversations` - List conversations
- `GET /api/user/conversations/{id}` - Get conversation
- `DELETE /api/user/conversations/{id}` - Delete conversation

## Frontend Pages

### Always Available
- `/` - Main recording page
  - Without auth: Works normally
  - With auth: Shows sidebar, requires login

### Auth-Only Pages (When ENABLE_AUTH=true)
- `/login.html` - Login/Signup page
- `/settings.html` - User settings and profile

## Database Tables

### paramedics
```sql
id, medical_id, national_id, name, email, age, 
hashed_password, profile_pic_url, created_at, updated_at
```

### conversations
```sql
id, session_id, paramedic_id, transcript, 
analysis (JSON), created_at
```

## User Journey (With Auth)

1. User visits `/`
2. Redirected to `/login.html` if not authenticated
3. Create account or login
4. Access main page with sidebar
5. Record sessions (auto-saved to database)
6. View history in sidebar
7. Manage profile in `/settings.html`

## Authentication Headers

All authenticated requests need:
```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN'
}
```

Token stored in: `localStorage.getItem('auth_token')`

## Password Requirements

- Minimum 8 characters
- Hashed with bcrypt
- Never stored in plain text

## Profile Picture Requirements

- Max size: 5MB
- Formats: JPG, JPEG, PNG, GIF, WebP
- Stored in: `uploads/profile_pics/`

## Common Issues & Solutions

### "Database not configured" error
- Check `ENABLE_AUTH=true` in `.env`
- Verify `DATABASE_URL` is set correctly

### 401 Unauthorized
- Token expired or invalid
- Clear localStorage and login again
- Check JWT_SECRET_KEY hasn't changed

### Sidebar not showing
- Auth is disabled (`ENABLE_AUTH=false`)
- Not logged in
- Check browser console for errors

## Development Workflow

1. **Start with auth disabled** for core feature development
   ```bash
   ENABLE_AUTH=false
   ```

2. **Enable auth for testing** user flows
   ```bash
   ENABLE_AUTH=true
   # Set up local PostgreSQL
   DATABASE_URL=postgresql://user:pass@localhost:5432/emergency_ai
   ```

3. **Deploy with auth enabled**
   ```bash
   ENABLE_AUTH=true
   # Use Render PostgreSQL
   DATABASE_URL=${{ render_postgres_url }}
   ```

## Security Checklist

- [ ] Strong JWT_SECRET_KEY (32+ chars)
- [ ] DATABASE_URL uses SSL in production
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS enabled (automatic on Render)
- [ ] Password minimum length enforced
- [ ] Profile pictures size limited

## Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (no auth)
ENABLE_AUTH=false uvicorn api:app --reload

# Run locally (with auth)
ENABLE_AUTH=true uvicorn api:app --reload

# Create database tables manually (if needed)
python -c "from database.connection import init_db; init_db()"

# Test API health
curl http://localhost:8000/api/health
```

## Files Created/Modified

### Backend
- `database/` - New directory
  - `models.py` - SQLAlchemy models
  - `schemas.py` - Pydantic schemas
  - `connection.py` - Database connection
  - `auth.py` - Auth utilities
- `endpoints/`
  - `config.py` - Updated with auth config
  - `auth_routes.py` - Auth endpoints
  - `user_routes.py` - User management
  - `routes.py` - Updated to save to DB
- `api.py` - Updated to include auth routes

### Frontend
- `static/`
  - `login.html` - New login page
  - `settings.html` - New settings page
  - `index.html` - Updated with sidebar
  - `css/sidebar.css` - New sidebar styles
  - `js/auth.js` - Auth handling
  - `js/auth-check.js` - Auth state check
  - `js/sidebar.js` - Sidebar functionality
  - `js/settings.js` - Settings page logic
  - `js/recording.js` - Updated for auth

### Configuration
- `requirements.txt` - Added auth dependencies
- `.env.example` - Example environment variables
- `AUTHENTICATION_SETUP.md` - Full setup guide
- `QUICK_REFERENCE_AUTH.md` - This file

## Contact & Support

For issues:
1. Check logs: `docker logs` or console output
2. Verify `.env` configuration
3. Test database connection
4. Clear browser cache/localStorage
5. Review [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md)



