# 🚀 Render Deployment Guide for NSE Equity Project

Your NSE Equity Project is now ready for deployment on Render! Follow this step-by-step guide.

## 📋 Pre-Deployment Checklist

✅ **Files Created:**
- `render.yaml` - Render service configuration
- `Procfile` - Process file for web service
- `runtime.txt` - Python version specification
- `config.py` - Environment-based configuration
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore file
- Updated `requirements.txt` with gunicorn
- Updated `app.py` for production

## 🔧 Step 1: Prepare Your Repository

1. **Initialize Git (if not already done):**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - NSE Equity Project ready for deployment"
   ```

2. **Push to GitHub:**
   - Create a new repository on GitHub
   - Push your code:
   ```bash
   git remote add origin https://github.com/yourusername/nse-equity-project.git
   git branch -M main
   git push -u origin main
   ```

## 🌐 Step 2: Deploy on Render

1. **Sign up/Login to Render:**
   - Go to https://render.com
   - Sign up or login with your GitHub account

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your NSE Equity Project repository

3. **Configure Service:**
   - **Name:** `nse-equity-project`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan:** Free (or paid for better performance)

## 🔐 Step 3: Set Environment Variables

In Render dashboard, go to Environment tab and add these variables:

### **Required Environment Variables:**
```
KITE_API_KEY=tmp23p1tsmywqb5s
KITE_API_SECRET=d1lkd7orpowxrdm4ff6l4fnctp0cjmh9
KITE_ACCESS_TOKEN=yi4cZe39bxvsTdQhY2ZRM7dMuerQYgLe
MONGODB_URI=mongodb+srv://hello:Hello123@option-chain.15yln1l.mongodb.net/?retryWrites=true&w=majority&appName=Option-chain
SMTP_USER=hellopythonhere@gmail.com
SMTP_PASSWORD=uhex ufof seya lxuz
FLASK_SECRET_KEY=your-super-secret-production-key-here
ENVIRONMENT=production
```

### **Important Notes:**
- **FLASK_SECRET_KEY:** Generate a strong secret key for production
- **KITE_ACCESS_TOKEN:** This token expires daily - you'll need to update it
- **MONGODB_URI:** Your current MongoDB connection string
- **SMTP credentials:** Your email settings for alerts

## 🔄 Step 4: Handle Daily Token Refresh

Since KiteConnect tokens expire daily, you have two options:

### **Option A: Manual Update (Simple)**
1. Generate new token daily using your `get_access_token.py` script
2. Update `KITE_ACCESS_TOKEN` in Render environment variables
3. Restart the service

### **Option B: Automated Refresh (Recommended)**
Add this route to your app for automated token refresh:

```python
@app.route('/refresh-token', methods=['POST'])
def refresh_token():
    # Add token refresh logic here
    # Update environment variable programmatically
    pass
```

## 🎯 Step 5: Deploy and Test

1. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment to complete (5-10 minutes)

2. **Test Your Application:**
   - Visit your Render URL: `https://your-app-name.onrender.com`
   - Test login/signup functionality
   - Verify options chain data loading
   - Test alert system

## 📊 Step 6: Monitor Your Application

1. **Render Dashboard:**
   - Monitor logs for errors
   - Check service health
   - Monitor resource usage

2. **Application Features to Test:**
   - ✅ User authentication
   - ✅ Options chain data display
   - ✅ Email alerts
   - ✅ Historical data
   - ✅ Background processing

## ⚠️ Important Production Considerations

### **Security:**
- Never commit `.env` file to Git
- Use strong secret keys
- Regularly rotate API tokens
- Monitor for unauthorized access

### **Performance:**
- Free tier has limitations (750 hours/month)
- Consider upgrading for production use
- Monitor response times and errors

### **Maintenance:**
- Daily token refresh required
- Monitor email delivery
- Regular database cleanup
- Keep dependencies updated

## 🔧 Troubleshooting

### **Common Issues:**

1. **Build Fails:**
   - Check `requirements.txt` for correct versions
   - Verify Python version in `runtime.txt`

2. **App Won't Start:**
   - Check environment variables are set
   - Verify MongoDB connection string
   - Check logs for specific errors

3. **KiteConnect Errors:**
   - Verify API credentials
   - Check if token is expired
   - Ensure rate limits aren't exceeded

4. **Email Alerts Not Working:**
   - Verify SMTP credentials
   - Check Gmail app password settings
   - Monitor email delivery logs

## 🎉 Success!

Your NSE Equity Project is now live on Render! 

**Your app will be available at:** `https://your-app-name.onrender.com`

### **Next Steps:**
1. Share the URL with users
2. Set up daily token refresh routine
3. Monitor application performance
4. Scale as needed

## 📞 Support

If you encounter issues:
1. Check Render logs first
2. Verify all environment variables
3. Test locally with production config
4. Check KiteConnect API status

**Your professional options trading platform is now ready for the world!** 🚀
