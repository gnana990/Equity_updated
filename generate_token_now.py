#!/usr/bin/env python3
"""
Daily Token Generator for KiteConnect
Run this script daily to generate a fresh access token
"""

from kiteconnect import KiteConnect
from kiteconnect_config import KITE_API_KEY, KITE_API_SECRET

def generate_daily_token():
    """Generate access token from request token - Run this daily"""
    
    print("Daily KiteConnect Token Generator")
    print("=" * 50)
    print("\nSteps to generate your daily token:")
    print("1. Visit this URL in your browser:")
    print(f"   https://kite.trade/connect/login?api_key={KITE_API_KEY}&v=3")
    print("\n2. Login with your Zerodha credentials")
    print("3. After login, you'll be redirected to:")
    print("   https://equity-updated.onrender.com/kite/callback?request_token=...")
    print("\n4. Copy the 'request_token' from the URL")
    print("5. Paste it below:")
    
    request_token = input("\nEnter request token: ").strip()
    
    if not request_token:
        print("Request token is required!")
        return None
    
    try:
        print("\nGenerating access token...")
        
        # Initialize KiteConnect
        kite = KiteConnect(api_key=KITE_API_KEY)
        
        # Generate session
        data = kite.generate_session(request_token, api_secret=KITE_API_SECRET)
        
        # Extract access token
        access_token = data["access_token"]
        user_id = data["user_id"]
        
        print("\nSUCCESS! Your daily credentials:")
        print("=" * 50)
        print(f"Access Token: {access_token}")
        print(f"User ID: {user_id}")
        print(f"Generated: {data.get('login_time', 'Now')}")
        
        # Test the connection
        kite.set_access_token(access_token)
        profile = kite.profile()
        
        print(f"\nConnection test successful!")
        print(f"Welcome, {profile['user_name']} ({profile['email']})")
        print(f"Available margin: Rs.{profile.get('net', 'N/A')}")
        
        print("\nUpdate your kiteconnect_config.py:")
        print(f'KITE_ACCESS_TOKEN = "{access_token}"')
        
        print("\nIMPORTANT NOTES:")
        print("• This token is valid for the entire trading day")
        print("• Generate a new token daily before market opens")
        print("• Update your production environment with the new token")
        
        return access_token
        
    except Exception as e:
        print(f"Error generating access token: {e}")
        print("\nTroubleshooting:")
        print("• Make sure you copied the complete request token")
        print("• Ensure you're using the latest request token")
        print("• Try the authentication flow again")
        return None

if __name__ == "__main__":
    token = generate_daily_token()
    if token:
        print("\nNext steps:")
        print("1. Copy the access token to kiteconnect_config.py")
        print("2. Update your production environment")
        print("3. Your project will now fetch live NSE data!")
        print("\nPro tip: Run this script every morning before market opens")
    else:
        print("\nFailed to generate token. Please try again.")
