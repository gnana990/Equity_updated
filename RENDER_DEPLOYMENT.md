# Render Deployment Guide for NSE Equity Project

## 🚀 Quick Deployment Steps

### 1. Connect GitHub Repository
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository containing this project

### 2. Configure Service
- **Name**: `equity-updated`
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
- **Plan**: Free

### 3. Environment Variables
Set these in Render dashboard:

```
KITE_API_KEY=tmp23p1tsmywqb5s
KITE_API_SECRET=d1lkd7orpowxrdm4ff6l4fnctp0cjmh9
KITE_ACCESS_TOKEN=pgn2d2uNCDgt1nweUUhCkG7VAC44kmxM
MONGODB_URI=mongodb+srv://hello:Hello123@option-chain.15yln1l.mongodb.net/?retryWrites=true&w=majority&appName=Option-chain
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=kondareddyroopa667@gmail.com
SMTP_PASSWORD=your_gmail_app_password
FLASK_SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
PYTHON_VERSION=3.11.0
```

### 4. Deploy
Click "Create Web Service" and wait for deployment to complete.

## 📝 Files Included for Deployment

**Essential Files:**
- `app.py` - Main Flask application
- `config.py` - Configuration settings
- `kiteconnect_config.py` - KiteConnect API integration
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version
- `Procfile` - Process configuration
- `render.yaml` - Render deployment config
- `templates/` - HTML templates

**Utility Files:**
- `generate_token_now.py` - Daily token generator
- `test_api.py` - API testing script
- `DAILY_TOKEN_GUIDE.md` - Token generation guide
- `README.md` - Project documentation

**Removed Files:**
- `netlify.toml` - Not needed for Render
- `get_access_token.py` - Replaced by generate_token_now.py
- `__pycache__/` - Python cache files

## 🔄 Daily Token Update Process

1. Generate new token using `generate_token_now.py`
2. Update `KITE_ACCESS_TOKEN` in Render environment variables
3. Redeploy service (automatic if using Git)

## 🌐 Expected URL
Your app will be available at: `https://equity-updated.onrender.com`

## ✅ Post-Deployment Checklist
- [ ] App loads successfully
- [ ] Login functionality works
- [ ] Live market data displays correctly
- [ ] Options chain loads with real NSE data
- [ ] Email alerts are functional
- [ ] All major indices (NIFTY, BANKNIFTY, etc.) work

## 🔧 Troubleshooting
- Check Render logs for deployment errors
- Verify all environment variables are set
- Ensure MongoDB connection is working
- Test KiteConnect API token validity
