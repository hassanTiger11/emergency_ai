# Authentication System Setup Guide

This guide explains how to set up and use the authentication system for the Paramedic Assistant application.

## 🎯 Overview

The application now includes a **complete user authentication and management system** that can be toggled on/off via configuration. When enabled, it provides:

- ✅ User signup and login
- ✅ Secure password hashing (bcrypt)
- ✅ JWT token-based authentication
- ✅ User profile management with profile pictures
- ✅ Conversation history storage in PostgreSQL
- ✅ ChatGPT-style sidebar for accessing previous sessions
- ✅ Settings page for managing user information

## 🔧 Configuration

### Enabling/Disabling Authentication

The authentication system is controlled by a single environment variable:

```bash
ENABLE_AUTH=true   # Enable authentication
ENABLE_AUTH=false  # Disable authentication (default)
```

**When disabled**: The application runs without any authentication requirements, perfect for development or single-user scenarios.

**When enabled**: Users must create an account and log in to use the application.

## 📋 Prerequisites

### 1. Install Dependencies

Update your Python environment with the required packages:

```bash
pip install -r requirements.txt
```

New dependencies include:
- `sqlalchemy` - ORM for database operations
- `psycopg2-binary` - PostgreSQL driver
- `passlib` and `bcrypt` - Password hashing
- `python-jose` and `cryptography` - JWT token handling
- `pydantic-settings` - Configuration management

### 2. PostgreSQL Database Setup

You need a PostgreSQL database. You have two options:

#### Option A: Local PostgreSQL (Development)

1. Install PostgreSQL on your machine
2. Create a database:
   ```sql
   CREATE DATABASE emergency_ai;
   ```
3. Note your credentials (username, password, host, port)

#### Option B: Render PostgreSQL (Production)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Create a new PostgreSQL database
3. Copy the connection string provided by Render

### 3. Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Authentication Toggle
ENABLE_AUTH=true

# JWT Secret Key (IMPORTANT: Change this in production!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-min-32-chars

# Database Configuration
# For local development:
DATABASE_URL=postgresql://username:password@localhost:5432/emergency_ai

# For Render (will be auto-populated by Render):
# DATABASE_URL=postgresql://user:password@host:port/database
```

⚠️ **Security Notes**:
- Generate a strong `JWT_SECRET_KEY` (at least 32 characters)
- Never commit your `.env` file to version control
- Use different keys for development and production

### Generating a Secure JWT Secret

You can generate a secure random key using Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🚀 Running the Application

### Development Mode (Without Authentication)

```bash
# .env file
ENABLE_AUTH=false

# Run the app
uvicorn api:app --reload
```

The app runs without authentication - perfect for testing the core recording functionality.

### Production Mode (With Authentication)

```bash
# .env file
ENABLE_AUTH=true
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET_KEY=your-secure-secret-key

# Run the app
uvicorn api:app --host 0.0.0.0 --port 8000
```

On first run, the database tables will be automatically created.

## 📊 Database Schema

The system creates two main tables:

### `paramedics` Table
- `id` - Primary key
- `medical_id` - Unique medical ID
- `national_id` - Unique national ID
- `name` - Full name
- `email` - Email (unique, used for login)
- `age` - Optional age
- `hashed_password` - Bcrypt hashed password
- `profile_pic_url` - Profile picture URL
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### `conversations` Table
- `id` - Primary key
- `session_id` - Unique session identifier
- `paramedic_id` - Foreign key to paramedics
- `transcript` - Full conversation transcript
- `analysis` - JSON analysis results
- `created_at` - Conversation timestamp

## 👥 User Journey

### 1. First Visit
1. User navigates to `/`
2. If auth is enabled and user not logged in → redirected to `/login.html`
3. User clicks "Sign up" to create an account

### 2. Creating an Account
Required fields:
- Full Name
- Email Address
- Medical ID (unique)
- National ID (unique)
- Password (minimum 8 characters)
- Age (optional)

### 3. Login
- User logs in with email and password
- Receives JWT token (valid for 7 days)
- Token stored in browser localStorage
- Redirected to main recording page

### 4. Main Page (Authenticated)
- **Sidebar** (collapsible, ChatGPT-style):
  - User profile with avatar
  - "New Session" button
  - List of previous conversations
  - Settings button at bottom
- **Main Area**:
  - Recording interface (same as before)
  - Session reports

### 5. Recording a Session
- Click "Start Recording"
- Speak the paramedic report
- Click "Stop Recording"
- Audio is transcribed and analyzed
- **Automatically saved to database**
- Appears in sidebar conversation history

### 6. Settings Page (`/settings.html`)
Users can:
- Upload/delete profile picture (max 5MB)
- Update name, email, age
- Change password
- View Medical ID and National ID (read-only)
- Logout

## 🔒 API Endpoints

### Authentication Endpoints

**POST** `/api/auth/signup`
- Create new paramedic account
- Returns JWT token and user info

**POST** `/api/auth/login`
- Login with email and password
- Returns JWT token and user info

**GET** `/api/auth/me`
- Get current user info (requires auth token)

**POST** `/api/auth/verify-token`
- Verify if token is valid

### User Management Endpoints

**GET** `/api/user/profile`
- Get user profile

**PUT** `/api/user/profile`
- Update user profile (name, email, age, password)

**POST** `/api/user/profile-picture`
- Upload profile picture

**DELETE** `/api/user/profile-picture`
- Delete profile picture

**GET** `/api/user/conversations`
- Get all user conversations (summary list)

**GET** `/api/user/conversations/{id}`
- Get specific conversation details

**DELETE** `/api/user/conversations/{id}`
- Delete a conversation

### Recording Endpoint (Updated)

**POST** `/api/upload-audio`
- Upload and process audio recording
- If authenticated: saves to database
- If not authenticated: only processes (file system backup)

## 🔐 Security Features

1. **Password Security**
   - Bcrypt hashing with salt
   - Minimum 8 characters required
   - Passwords never stored in plain text

2. **JWT Tokens**
   - Signed with secret key
   - 7-day expiration
   - Validated on each authenticated request

3. **Database Security**
   - Connection pooling with pre-ping
   - SQL injection prevention via ORM
   - Unique constraints on sensitive fields

4. **File Uploads**
   - Profile pictures: Max 5MB
   - Allowed formats: JPG, PNG, GIF, WebP
   - Files stored outside web root

## 🎨 Frontend Features

### ChatGPT-Style Sidebar
- Collapsible with toggle button
- Shows user profile and avatar
- Lists previous conversations
- Click any conversation to load it
- Settings button at bottom

### Responsive Design
- Works on desktop and mobile
- Sidebar becomes full-screen on mobile
- Touch-friendly interface

### Authentication State Management
- JWT token in localStorage
- Auto-redirect if not authenticated
- Token validation on page load
- Graceful handling of expired tokens

## 🐛 Troubleshooting

### Database Connection Issues

```
Error: could not connect to server
```

**Solution**: Check your DATABASE_URL is correct and PostgreSQL is running.

### Authentication Not Working

```
Status: 401 Unauthorized
```

**Solutions**:
1. Check if `ENABLE_AUTH=true` in `.env`
2. Verify JWT_SECRET_KEY is set
3. Clear browser localStorage and try logging in again

### Tables Not Created

**Solution**: Tables are auto-created on first run. Check database permissions.

```python
# Manual table creation if needed
from database.connection import init_db
init_db()
```

### Profile Picture Not Showing

**Solution**: 
1. Check `uploads/profile_pics/` directory exists
2. Verify `/uploads` static route is mounted
3. Check file permissions

## 📝 Development Tips

### Switching Between Modes

You can easily switch between development (no auth) and production (with auth):

```bash
# Development - no auth
ENABLE_AUTH=false

# Production - with auth
ENABLE_AUTH=true
```

No code changes needed! The frontend automatically adapts.

### Database Migrations

For now, the system uses simple auto-creation. For production with migrations, consider:

```bash
pip install alembic
alembic init alembic
# Configure alembic and create migrations
```

### Testing Authentication

1. Start with `ENABLE_AUTH=false` to test core features
2. Switch to `ENABLE_AUTH=true` to test auth flow
3. Create test accounts with different roles
4. Test session persistence across browser restarts

## 🚀 Deployment to Render

### Environment Variables in Render

In your Render dashboard, set these environment variables:

```
OPENAI_API_KEY=your_key
ENABLE_AUTH=true
JWT_SECRET_KEY=your_production_secret_key
DATABASE_URL=${{ your_postgres_connection }}
```

Render will automatically populate `DATABASE_URL` if you link a PostgreSQL database.

### Database Setup on Render

1. Create PostgreSQL database in Render
2. Link it to your web service
3. Tables will auto-create on first deploy
4. Monitor logs for any database errors

## 📚 Additional Resources

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [JWT.io](https://jwt.io/) - Debug JWT tokens

## 🤝 Support

If you encounter issues:
1. Check `.env` configuration
2. Verify database connection
3. Check browser console for frontend errors
4. Review server logs for backend errors
5. Ensure all dependencies are installed

---

**Important**: Always use `ENABLE_AUTH=true` with a strong `JWT_SECRET_KEY` in production!


