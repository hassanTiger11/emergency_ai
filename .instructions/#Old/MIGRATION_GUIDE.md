# Migration Guide - Adding Authentication to Existing Installation

This guide helps you upgrade an existing Paramedic Assistant installation to include the new authentication system.

## 🔄 Overview

The authentication system is **completely optional** and **backward compatible**. Your existing installation will continue to work without any changes.

## Option 1: Keep Running Without Authentication (Recommended for Development)

**No action needed!** 

The application defaults to running without authentication. Everything works exactly as before.

```bash
# Your .env file (or no .env at all)
OPENAI_API_KEY=your_key
# ENABLE_AUTH defaults to false
```

Just run the app as usual:
```bash
uvicorn api:app --reload
```

## Option 2: Enable Authentication (Recommended for Production)

Follow these steps to enable the new authentication system:

### Step 1: Update Dependencies

```bash
pip install -r requirements.txt
```

This installs the new authentication-related packages:
- SQLAlchemy (database ORM)
- psycopg2-binary (PostgreSQL driver)
- passlib & bcrypt (password hashing)
- python-jose & cryptography (JWT tokens)

### Step 2: Set Up PostgreSQL Database

#### Local Development

1. Install PostgreSQL if not already installed
2. Create a database:
   ```sql
   CREATE DATABASE emergency_ai;
   ```
3. Note your connection details

#### Production (Render)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Create a new PostgreSQL database
3. Copy the connection string

### Step 3: Update Environment Variables

Create or update your `.env` file:

```bash
# Existing
OPENAI_API_KEY=your_openai_api_key

# New - Authentication
ENABLE_AUTH=true

# New - JWT Secret (generate a secure random key!)
JWT_SECRET_KEY=your-secure-32-character-random-key

# New - Database Connection
DATABASE_URL=postgresql://user:password@localhost:5432/emergency_ai
```

**Generate a secure JWT key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Start the Application

```bash
uvicorn api:app --reload
```

On first start with `ENABLE_AUTH=true`, the database tables will be automatically created.

### Step 5: Create Your First Account

1. Visit `http://localhost:8000`
2. You'll be redirected to the login page
3. Click "Sign up"
4. Fill in your information:
   - Name
   - Email
   - Medical ID
   - National ID
   - Password (min 8 characters)
   - Age (optional)
5. Click "Create Account"
6. You'll be logged in automatically!

## 📊 What Happens When You Enable Auth?

### Before (ENABLE_AUTH=false)
- ✅ Recording works normally
- ✅ Reports generated
- ✅ Files saved to `.output/` directory
- ❌ No user accounts
- ❌ No conversation history
- ❌ No sidebar

### After (ENABLE_AUTH=true)
- ✅ Everything from before still works
- ✅ **Plus** user accounts and login
- ✅ **Plus** conversation history in database
- ✅ **Plus** ChatGPT-style sidebar
- ✅ **Plus** profile pictures
- ✅ **Plus** settings page
- ✅ Files still saved to `.output/` (backup)

## 🔄 Can I Switch Back and Forth?

**Yes!** You can toggle authentication on/off anytime:

```bash
# Turn off authentication
ENABLE_AUTH=false

# Turn on authentication
ENABLE_AUTH=true
```

The app adapts automatically. No code changes needed.

## 💾 What About Existing Data?

### Existing Recording Files
All your existing `.output/` files remain untouched:
- `*.wav` audio files
- `*.txt` transcripts  
- `*.json` analysis files
- `*.pdf` reports

These continue to be created whether auth is enabled or not.

### Database Data
When you enable auth for the first time:
- Database tables are created empty
- Previous sessions are NOT automatically imported
- New sessions are saved to database going forward

**Note**: You could write a migration script to import old files into the database if needed, but it's not required.

## 🚀 Deploying to Render with Auth

### If You Already Have a Render Deployment

1. **Add PostgreSQL Database:**
   - In Render dashboard, create new PostgreSQL instance
   - Link it to your web service
   
2. **Add Environment Variables:**
   ```
   ENABLE_AUTH=true
   JWT_SECRET_KEY=your-production-secret-key
   DATABASE_URL=${{ your_postgres_connection }}
   ```

3. **Redeploy:**
   - Push code to GitHub
   - Render will auto-deploy
   - Database tables created on first run

### Fresh Render Deployment

See [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md) for complete instructions.

## 🛠️ Troubleshooting Migration

### "Module not found" errors

**Problem:** Missing new dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### "Database not configured" error

**Problem:** `ENABLE_AUTH=true` but no database URL

**Solution:** Add to `.env`:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/emergency_ai
```

### App won't start with auth enabled

**Problem:** Database connection failed

**Solution:** 
1. Check PostgreSQL is running
2. Verify DATABASE_URL is correct
3. Test connection:
   ```bash
   psql postgresql://user:password@localhost:5432/emergency_ai
   ```

### Can't access login page

**Problem:** Browser cached old version

**Solution:**
1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Clear browser cache
3. Try incognito/private window

### Forgot to set JWT_SECRET_KEY

**Problem:** App starts but login fails

**Solution:** Add to `.env`:
```bash
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

Then restart the app.

## 📝 Rollback Plan

If you want to revert to the pre-auth version:

### Option A: Disable Auth (Recommended)
```bash
# .env
ENABLE_AUTH=false
```
App works as before, database unused.

### Option B: Full Rollback (Not Recommended)
1. Checkout previous git commit:
   ```bash
   git log  # Find commit before auth was added
   git checkout <commit-hash>
   ```
2. Reinstall old dependencies:
   ```bash
   pip install -r requirements.txt
   ```

**Note:** Option A is much simpler and maintains the new features for future use.

## 🎯 Recommended Migration Path

For **production deployments**, we recommend this staged approach:

### Stage 1: Test Locally Without Auth
```bash
ENABLE_AUTH=false
uvicorn api:app --reload
```
Verify core functionality still works.

### Stage 2: Test Locally With Auth
```bash
# Set up local PostgreSQL
ENABLE_AUTH=true
DATABASE_URL=postgresql://user:pass@localhost:5432/emergency_ai
JWT_SECRET_KEY=test-key-for-development
uvicorn api:app --reload
```
Test the new features:
- Create account
- Login
- Record session
- View in sidebar
- Update profile
- Upload picture

### Stage 3: Deploy to Production
```bash
# On Render, set environment variables:
ENABLE_AUTH=true
JWT_SECRET_KEY=<strong-production-key>
DATABASE_URL=<render-postgres-url>
```
Deploy and test with real users.

## ✅ Post-Migration Checklist

After enabling authentication in production:

- [ ] PostgreSQL database is running and accessible
- [ ] `ENABLE_AUTH=true` in environment
- [ ] Strong `JWT_SECRET_KEY` set (min 32 chars)
- [ ] `DATABASE_URL` configured correctly
- [ ] Database tables created successfully
- [ ] Can access login page
- [ ] Can create new account
- [ ] Can login with created account
- [ ] Sidebar appears after login
- [ ] Recording and analysis still works
- [ ] Conversations saved to database
- [ ] Can view conversation history
- [ ] Can access settings page
- [ ] Can upload profile picture
- [ ] Can update profile information
- [ ] Logout works correctly

## 📞 Getting Help

If you encounter issues during migration:

1. **Check logs:** Look for error messages in console
2. **Verify config:** Double-check all environment variables
3. **Test database:** Ensure PostgreSQL connection works
4. **Try fresh start:** Create new database and test account
5. **Review docs:** See [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md)

## 🎉 Success!

Once migration is complete, you'll have:
- ✅ Secure user authentication
- ✅ Persistent conversation storage
- ✅ Professional user management
- ✅ Better scalability
- ✅ Production-ready system

And the best part? You can turn it off anytime with `ENABLE_AUTH=false`!

---

**Remember:** The authentication system is completely optional. Your existing installation continues to work perfectly without it.

