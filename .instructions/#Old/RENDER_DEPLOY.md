# 🚀 Deploying to Render - Quick Start Guide

## Prerequisites
- GitHub account
- Render account (free tier works)
- OpenAI API key

## Step-by-Step Deployment

### 1. Prepare Your Repository

1. **Commit all your changes:**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   ```

2. **Push to GitHub:**
   ```bash
   git push origin main
   ```

   Make sure `.env` is in `.gitignore` (it already is!)

### 2. Deploy on Render

#### Method A: Quick Deploy (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)

2. Click **"New +"** → **"Web Service"**

3. **Connect your GitHub repository:**
   - Click "Connect account" if first time
   - Find and select your `emergency_AI` repository

4. **Configure the service:**
   - **Name**: `paramedic-assistant` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: Docker ✅ (auto-detected from Dockerfile)
   - **Instance Type**: Free (or paid for better performance)

5. **Add Environment Variable:**
   - Click **"Add Environment Variable"**
   - **Key**: `OPENAI_API_KEY`
   - **Value**: Your actual OpenAI API key
   - Click **"Add"**

6. **Deploy:**
   - Click **"Create Web Service"**
   - Wait 5-10 minutes for build and deployment
   - Your app will be live at: `https://paramedic-assistant.onrender.com`

#### Method B: Using Blueprint (render.yaml)

1. Go to Render Dashboard → **"Blueprints"**

2. Click **"New Blueprint Instance"**

3. Connect your repository

4. Render reads `render.yaml` and configures automatically

5. Add `OPENAI_API_KEY` in environment variables

6. Deploy!

### 3. Verify Deployment

1. **Check the logs** in Render dashboard for any errors

2. **Visit your URL**: `https://your-app-name.onrender.com`

3. **Test the recording** - ensure microphone access works (HTTPS required)

## Important Notes

### ⚠️ Free Tier Limitations
- Spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds to start
- 750 hours/month limit (shared across all free services)

### 🎙️ Microphone Access
- **HTTPS is required** for browser microphone access
- Render provides HTTPS automatically
- On localhost during development, microphone works on HTTP

### 💾 File Storage
- `output/` directory is **ephemeral** (files lost on restart/redeploy)
- For production, consider:
  - AWS S3
  - Cloudinary
  - Render Persistent Disk (paid feature)

### 🔒 Security Best Practices
- Never commit `.env` to Git
- Rotate your OpenAI API key if exposed
- Use Render's environment variables for secrets
- Enable authentication for production use

## Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Ensure all files are committed
- Review build logs in Render dashboard

### "No module named..." Error
- Verify all dependencies in `requirements.txt`
- Check Python version compatibility

### Microphone Not Working
- Ensure you're using HTTPS (automatic on Render)
- Check browser permissions
- Try different browser

### OpenAI API Errors
- Verify API key is set correctly in environment variables
- Check OpenAI account has credits
- Review API rate limits

## Updating Your App

After making changes:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render automatically detects the push and redeploys! 🎉

## Cost Optimization

### Free Tier (Good for testing)
- Use free instance type
- Spins down when inactive
- Limited to 750 hours/month

### Paid Instance (Recommended for production)
- **Starter ($7/month)**: Always-on, 512MB RAM
- **Standard ($25/month)**: 2GB RAM, better performance
- No spin-down delays
- Better for real paramedic use

## Next Steps

1. ✅ Deploy to Render
2. 🧪 Test thoroughly with real scenarios
3. 👥 Share URL with team for feedback
4. 🔐 Add authentication (if needed)
5. 💾 Set up cloud storage for reports
6. 📊 Add analytics/monitoring

## Support

- [Render Documentation](https://render.com/docs)
- [OpenAI API Docs](https://platform.openai.com/docs)
- Check your Render dashboard logs for issues

---

**Ready to deploy? Follow the steps above and you'll be live in minutes!** 🚀

