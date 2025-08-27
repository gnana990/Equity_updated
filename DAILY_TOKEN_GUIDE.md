# Daily Access Token Generation & Deployment Guide

## 🔑 Daily Token Generation (Run Every Morning)

### Step 1: Get Request Token
1. Open this URL in your browser:
   ```
   https://kite.trade/connect/login?api_key=tmp23p1tsmywqb5s&v=3
   ```

2. Login with your Zerodha credentials

3. After login, you'll be redirected to:
   ```
   https://equity-updated.onrender.com/kite/callback?request_token=XXXXXXXXXX&action=login&status=success
   ```

4. Copy the `request_token` value from the URL

### Step 2: Generate Access Token
1. Run the token generator:
   ```bash
   python generate_token_now.py
   ```

2. Paste the request token when prompted

3. Copy the new access token from the output

### Step 3: Update Configuration
1. Open `kiteconnect_config.py`
2. Replace the old token:
   ```python
   KITE_ACCESS_TOKEN = "your_new_token_here"
   ```

### Step 4: Test Connection
```bash
python test_api.py
```

## 🚀 Deployment to Render

### Method 1: Git Deployment (Recommended)
1. Commit your changes:
   ```bash
   git add .
   git commit -m "Update access token for [date]"
   git push origin main
   ```

2. Render will automatically deploy the changes

### Method 2: Manual Environment Variable Update
1. Go to your Render dashboard
2. Select your service: equity-project
3. Go to Environment tab
4. Update `KITE_ACCESS_TOKEN` with the new token
5. Save and redeploy

## 📋 Daily Checklist
- [ ] Generate new access token (before 9 AM)
- [ ] Update kiteconnect_config.py
- [ ] Test API connection locally
- [ ] Deploy to production
- [ ] Verify live data is working

## 🔧 Troubleshooting
- **Token expired**: Generate new token using the guide above
- **API connection failed**: Check if market is open and token is valid
- **Deployment failed**: Check Render logs for errors

## 📞 Quick Commands
```bash
# Generate token
python generate_token_now.py

# Test API
python test_api.py

# Deploy via Git
git add . && git commit -m "Update token" && git push
```
