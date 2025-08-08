#!/usr/bin/env python3
"""
Test Kite API setup and help generate access token.
"""

import webbrowser
from kiteconnect import KiteConnect

# Your Kite Connect credentials
API_KEY = "p1azabgr32cikm26"
API_SECRET = "tpmcx0weg8q7h1mx9s8dwte0ehu9a870"

def main():
    print("🚀 Zerodha Kite API Setup Test")
    print("=" * 50)
    
    # Step 1: Generate login URL
    login_url = f"https://kite.zerodha.com/connect/login?api_key={API_KEY}"
    
    print(f"📱 API Key: {API_KEY}")
    print(f"🔗 Login URL: {login_url}")
    print("\n📋 TO GET ACCESS TOKEN:")
    print("1. Visit the login URL above")
    print("2. Login with your Zerodha credentials")
    print("3. After login, copy the redirect URL")
    print("4. Extract the 'request_token' parameter")
    print("5. Use that token to generate session")
    
    print(f"\n🌐 Opening browser to: {login_url}")
    webbrowser.open(login_url)
    
    print("\n✅ Browser opened! Please complete the login process.")
    print("After you get the request token, update .env file with:")
    print("KITE_ACCESS_TOKEN=your_generated_access_token")

if __name__ == "__main__":
    main()