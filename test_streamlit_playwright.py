#!/usr/bin/env python3
"""
Test Streamlit AI Agent interface using Playwright.
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def test_streamlit_ai_agent():
    """Test the AI Agent page in Streamlit."""
    
    async with async_playwright() as p:
        print("🌐 Starting browser test...")
        
        # Launch browser
        browser = await p.chromium.launch(headless=True)  # Set to False to see the browser
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to Streamlit app
            print("📍 Navigating to Streamlit app...")
            await page.goto("http://localhost:8501", wait_until="networkidle")
            await page.wait_for_timeout(3000)  # Wait for app to load
            
            # Check if the page loaded successfully
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Look for the main header
            header = await page.query_selector("h1")
            if header:
                header_text = await header.inner_text()
                print(f"📊 Found header: {header_text}")
            
            # Try to find and click AI Agent in navigation
            print("🤖 Looking for AI Agent navigation...")
            
            # Look for selectbox options
            selectbox = await page.query_selector("[data-testid='stSelectbox']")
            if selectbox:
                print("✅ Found navigation selectbox")
                
                # Click on selectbox to open options
                await selectbox.click()
                await page.wait_for_timeout(1000)
                
                # Look for AI Agent option
                ai_agent_option = await page.query_selector("text=🤖 AI Agent")
                if ai_agent_option:
                    print("✅ Found AI Agent option")
                    await ai_agent_option.click()
                    await page.wait_for_timeout(2000)
                    
                    # Check if AI Agent page loaded
                    ai_header = await page.query_selector("text=AI Trading Agent")
                    if ai_header:
                        print("✅ AI Agent page loaded successfully!")
                        
                        # Test the chat interface
                        print("💬 Testing chat interface...")
                        
                        # Look for text area
                        text_area = await page.query_selector("textarea")
                        if text_area:
                            print("✅ Found chat text area")
                            
                            # Type a test message
                            await text_area.fill("GET PORTFOLIO STATUS")
                            await page.wait_for_timeout(500)
                            
                            # Look for and click send button
                            send_button = await page.query_selector("text=🚀 Send to Agent")
                            if send_button:
                                print("✅ Found send button")
                                print("🚀 Sending test message...")
                                await send_button.click()
                                
                                # Wait for response
                                await page.wait_for_timeout(5000)
                                
                                # Check for response
                                chat_history = await page.query_selector("text=Chat History")
                                if chat_history:
                                    print("✅ Chat history appeared - message processed!")
                                else:
                                    print("⚠️ No chat history visible")
                            else:
                                print("❌ Send button not found")
                        else:
                            print("❌ Chat text area not found")
                        
                        # Test other tabs
                        print("📊 Testing Performance tab...")
                        perf_tab = await page.query_selector("text=📊 Performance")
                        if perf_tab:
                            await perf_tab.click()
                            await page.wait_for_timeout(2000)
                            print("✅ Performance tab loaded")
                        
                        print("🏥 Testing Health Check tab...")
                        health_tab = await page.query_selector("text=🏥 Health Check")
                        if health_tab:
                            await health_tab.click()
                            await page.wait_for_timeout(2000)
                            print("✅ Health Check tab loaded")
                        
                    else:
                        print("❌ AI Agent page header not found")
                else:
                    print("❌ AI Agent option not found in dropdown")
            else:
                print("❌ Navigation selectbox not found")
            
            # Take a screenshot for verification
            await page.screenshot(path="streamlit_ai_agent_test.png")
            print("📸 Screenshot saved as streamlit_ai_agent_test.png")
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            await page.screenshot(path="streamlit_error.png")
            
        finally:
            await browser.close()

async def main():
    """Main test function."""
    print("🧪 STREAMLIT AI AGENT PLAYWRIGHT TEST")
    print("=" * 60)
    
    # Check if Streamlit is running
    import requests
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit app is running")
        else:
            print(f"⚠️ Streamlit returned status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Cannot connect to Streamlit: {e}")
        print("💡 Make sure to run: source venv/bin/activate && python run_streamlit.py")
        return
    
    # Run the test
    await test_streamlit_ai_agent()
    
    print("\n" + "=" * 60)
    print("🎉 Playwright test completed!")
    print("📸 Check streamlit_ai_agent_test.png for visual verification")

if __name__ == "__main__":
    asyncio.run(main())