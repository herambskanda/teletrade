#!/usr/bin/env python3
"""
Interactive script to get Zerodha Kite access token.
This script will help you generate the access token needed for live trading.
"""

import webbrowser
from urllib.parse import urlparse, parse_qs

# Your Kite Connect credentials
API_KEY = "p1azabgr32cikm26"
API_SECRET = "tpmcx0weg8q7h1mx9s8dwte0ehu9a870"

def get_kite_access_token():
    """Interactive process to get Kite access token."""
    
    print("🚀 Zerodha Kite Connect - Access Token Generator")
    print("=" * 60)
    print(f"📱 API Key: {API_KEY}")
    print(f"🔐 User ID: CD7525")
    print("=" * 60)
    
    # Step 1: Generate login URL
    login_url = f"https://kite.zerodha.com/connect/login?api_key={API_KEY}"
    
    print("\n📋 STEP 1: Login to Kite")
    print(f"🔗 Opening login URL: {login_url}")
    print("\n⚠️  IMPORTANT INSTRUCTIONS:")
    print("1. A browser window will open to Kite Connect login")
    print("2. Login with your Zerodha credentials")
    print("3. After login, you'll be redirected to a URL")
    print("4. Copy the ENTIRE redirect URL and paste it back here")
    print("5. The URL will contain 'request_token' parameter")
    
    input("\n👍 Press Enter when ready to open browser...")
    
    # Open browser
    webbrowser.open(login_url)
    
    print("\n📋 STEP 2: Get Redirect URL")
    print("After logging in, copy the redirect URL from browser address bar.")
    print("Example: https://example.com?request_token=abc123&action=login&status=success")
    
    redirect_url = input("\n🔗 Paste the redirect URL here: ").strip()
    
    # Extract request token
    try:
        parsed_url = urlparse(redirect_url)
        params = parse_qs(parsed_url.query)
        request_token = params.get('request_token', [None])[0]
        
        if not request_token:
            print("❌ Error: Could not find 'request_token' in URL")
            print("Please make sure you copied the complete redirect URL")
            return None
            
        print(f"\n✅ Request Token: {request_token}")
        
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        return None
    
    # Step 3: Generate access token
    print("\n📋 STEP 3: Generate Access Token")
    
    try:
        from kiteconnect import KiteConnect
        
        kite = KiteConnect(api_key=API_KEY)
        
        # Generate session
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        
        access_token = data["access_token"]
        user_id = data["user_id"]
        
        print("\n🎉 SUCCESS! Access token generated:")
        print("=" * 60)
        print(f"ACCESS_TOKEN: {access_token}")
        print(f"USER_ID: {user_id}")
        print("=" * 60)
        
        # Update .env file
        print("\n📝 Updating .env file...")
        
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Replace the access token
        env_content = env_content.replace(
            'KITE_ACCESS_TOKEN=your_access_token',
            f'KITE_ACCESS_TOKEN={access_token}'
        )
        
        # Update user ID if needed
        env_content = env_content.replace(
            'KITE_USER_ID=CD7525',
            f'KITE_USER_ID={user_id}'
        )
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file updated successfully!")
        print("\n🔄 Please restart your trading bot to use the new access token.")
        
        return access_token
        
    except ImportError:
        print("❌ Error: kiteconnect library not installed")
        print("Run: pip install kiteconnect")
        return None
        
    except Exception as e:
        print(f"❌ Error generating access token: {e}")
        print("\nPossible issues:")
        print("- Request token might be expired (valid for ~2-3 minutes)")
        print("- API credentials might be incorrect")
        print("- Network connectivity issues")
        return None


def test_kite_connection(access_token):
    """Test the Kite connection with access token."""
    
    print("\n🧪 Testing Kite API Connection...")
    
    try:
        from kiteconnect import KiteConnect
        
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(access_token)
        
        # Test basic API calls
        print("📊 Fetching profile...")
        profile = kite.profile()
        print(f"✅ Connected as: {profile['user_name']} ({profile['email']})")
        
        print("💰 Fetching margins...")
        margins = kite.margins()
        print(f"✅ Available margin: ₹{margins['equity']['available']['live_balance']:,.2f}")
        
        print("📈 Fetching instruments...")
        instruments = kite.instruments("NSE")[:5]  # First 5 instruments
        print(f"✅ Found {len(instruments)} NSE instruments")
        
        print("🎯 Testing quote fetch...")
        quote = kite.quote(["NSE:RELIANCE"])
        reliance_price = quote["NSE:RELIANCE"]["last_price"]
        print(f"✅ RELIANCE current price: ₹{reliance_price}")
        
        print("\n🎉 All API tests passed! Kite connection is working perfectly.")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def main():
    """Main function."""
    
    print("\n⚠️  IMPORTANT SAFETY NOTICE:")
    print("🔸 This will enable LIVE TRADING with real money")
    print("🔸 Make sure you understand the risks involved")
    print("🔸 Start with paper trading first to test the system")
    print("🔸 The bot will use your actual Zerodha account")
    
    proceed = input("\n❓ Do you want to proceed? (yes/no): ").strip().lower()
    
    if proceed != 'yes':
        print("❌ Aborted. Access token not generated.")
        return
    
    # Get access token
    access_token = get_kite_access_token()
    
    if access_token:
        # Test connection
        if test_kite_connection(access_token):
            print("\n🚀 Setup Complete!")
            print("🔸 Your trading bot is now connected to live Kite API")
            print("🔸 Restart the FastAPI server to use the new token")
            print("🔸 Make sure ENABLE_LIVE_TRADING=true in .env for live trades")
        else:
            print("\n⚠️  Setup completed but connection test failed.")
            print("Please check your network connection and try again.")
    else:
        print("\n❌ Failed to generate access token.")
        print("Please try again or check your API credentials.")


if __name__ == "__main__":
    main()