#!/usr/bin/env python3
"""
Convert Kite request token to access token.
Run this after getting the request token from the login process.
"""

from kiteconnect import KiteConnect
import sys

# Your Kite Connect credentials
API_KEY = "p1azabgr32cikm26"
API_SECRET = "tpmcx0weg8q7h1mx9s8dwte0ehu9a870"

def generate_access_token(request_token):
    """Generate access token from request token."""
    
    try:
        print(f"🔧 Generating access token...")
        print(f"📱 API Key: {API_KEY}")
        print(f"🎫 Request Token: {request_token}")
        
        # Initialize KiteConnect
        kite = KiteConnect(api_key=API_KEY)
        
        # Generate session
        print("🔄 Generating session...")
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        
        access_token = data["access_token"]
        user_id = data["user_id"]
        user_name = data.get("user_name", "Unknown")
        
        print(f"\n🎉 SUCCESS! Access token generated:")
        print("=" * 60)
        print(f"ACCESS_TOKEN: {access_token}")
        print(f"USER_ID: {user_id}")
        print(f"USER_NAME: {user_name}")
        print("=" * 60)
        
        # Test the connection
        print(f"\n🧪 Testing connection...")
        kite.set_access_token(access_token)
        
        profile = kite.profile()
        print(f"✅ Connected successfully!")
        print(f"👤 User: {profile['user_name']} ({profile['email']})")
        
        margins = kite.margins()
        available_margin = margins['equity']['available']['live_balance']
        print(f"💰 Available Margin: ₹{available_margin:,.2f}")
        
        # Update .env file
        print(f"\n📝 Updating .env file...")
        
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Replace the access token
            env_content = env_content.replace(
                'KITE_ACCESS_TOKEN=your_access_token',
                f'KITE_ACCESS_TOKEN={access_token}'
            )
            
            # Update user ID
            env_content = env_content.replace(
                f'KITE_USER_ID=CD7525',
                f'KITE_USER_ID={user_id}'
            )
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            print("✅ .env file updated successfully!")
            
        except Exception as e:
            print(f"⚠️ Could not update .env file: {e}")
            print(f"Please manually update .env with:")
            print(f"KITE_ACCESS_TOKEN={access_token}")
            print(f"KITE_USER_ID={user_id}")
        
        print(f"\n🚀 Setup Complete!")
        print(f"🔸 Access token is valid until market close today")
        print(f"🔸 Restart your trading bot to use live Kite API")
        print(f"🔸 Set ENABLE_LIVE_TRADING=true in .env for live trading")
        
        return access_token
        
    except Exception as e:
        print(f"❌ Error generating access token: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"- Make sure the request token is correct and recent")
        print(f"- Request tokens expire in ~2-3 minutes")
        print(f"- Check your API credentials")
        return None

def main():
    """Main function."""
    
    if len(sys.argv) != 2:
        print("🚀 Kite Access Token Generator")
        print("=" * 40)
        print("Usage: python generate_access_token.py <request_token>")
        print("\nSteps:")
        print("1. Login to: https://kite.zerodha.com/connect/login?api_key=p1azabgr32cikm26")
        print("2. Copy the request_token from redirect URL")
        print("3. Run: python generate_access_token.py <request_token>")
        return
    
    request_token = sys.argv[1].strip()
    
    if not request_token:
        print("❌ Please provide a valid request token")
        return
    
    print("⚠️ IMPORTANT: This will enable live trading with real money!")
    
    # Generate access token
    generate_access_token(request_token)

if __name__ == "__main__":
    main()