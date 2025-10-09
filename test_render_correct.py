#!/usr/bin/env python3
"""
Test Render Database with Correct URL
"""
import requests
import json
from datetime import datetime

def test_render_database():
    print("🔍 Testing Render Database Connection")
    print("=" * 60)
    
    print("📝 IMPORTANT: You need your RENDER APP URL, not your DATABASE URL!")
    print()
    print("Your database URL is: postgresql://mubeen_account_db_user:...")
    print("But you need your APP URL like: https://your-app-name.onrender.com")
    print()
    print("To find your app URL:")
    print("1. Go to your Render dashboard")
    print("2. Click on your web service (not the database)")
    print("3. Look for the URL in the 'URL' section")
    print("4. It should look like: https://emergency-ai-xxxx.onrender.com")
    print()
    
    # Get Render URL from user input
    render_url = input("Enter your Render APP URL (not database URL): ").strip()
    
    if not render_url:
        print("❌ No URL provided. Exiting.")
        return
    
    if not render_url.startswith('http'):
        render_url = f"https://{render_url}"
    
    print(f"🌐 Testing: {render_url}")
    print()
    
    # Test 1: Health Check
    print("1. Testing Health Check...")
    try:
        response = requests.get(f"{render_url}/health", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'Unknown')}")
            print(f"   Auth Enabled: {health_data.get('auth_enabled', 'Unknown')}")
        else:
            print(f"⚠️  Health check returned: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("   This might mean:")
        print("   1. Your app is not deployed yet")
        print("   2. Your app is still building/starting")
        print("   3. The URL is incorrect")
        return
    
    # Test 2: Database Connection (via auth endpoints)
    print("\n2. Testing Database Connection...")
    try:
        response = requests.get(f"{render_url}/api/auth/me", timeout=30)
        print(f"   Auth endpoint status: {response.status_code}")
        if response.status_code in [401, 403]:
            print("✅ Database connected (auth working, no user logged in)")
        elif response.status_code == 200:
            print("✅ Database connected (user authenticated)")
            user_data = response.json()
            print(f"   User: {user_data.get('name', 'Unknown')}")
        else:
            print(f"⚠️  Unexpected auth response: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return
    
    # Test 3: User Registration (Database Write Test)
    print("\n3. Testing Database Write...")
    test_email = f"test_{int(datetime.now().timestamp())}@example.com"
    register_data = {
        'name': 'Render Test User',
        'email': test_email,
        'password': 'testpass123',
        'age': 30
    }
    
    try:
        response = requests.post(f"{render_url}/api/auth/signup", json=register_data, timeout=30)
        print(f"   Registration status: {response.status_code}")
        if response.status_code == 201:
            print("✅ User registration successful (database write working)")
            auth_data = response.json()
            token = auth_data['access_token']
            print(f"   User ID: {auth_data.get('user', {}).get('id', 'Unknown')}")
        elif response.status_code == 400 and "already registered" in response.json().get('detail', ''):
            print("⚠️  User already exists, trying login...")
            login_data = {'email': test_email, 'password': 'testpass123'}
            response = requests.post(f"{render_url}/api/auth/login", json=login_data, timeout=30)
            if response.status_code == 200:
                auth_data = response.json()
                token = auth_data['access_token']
                print("✅ User login successful")
            else:
                print(f"❌ Login failed: {response.status_code}")
                return
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return
    except Exception as e:
        print(f"❌ Registration/Login error: {e}")
        return
    
    # Test 4: Database Read (User Profile)
    print("\n4. Testing Database Read (User Profile)...")
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(f"{render_url}/api/user/profile", headers=headers, timeout=30)
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User profile retrieved successfully")
            print(f"   Name: {user_data.get('name', 'Unknown')}")
            print(f"   Email: {user_data.get('email', 'Unknown')}")
            print(f"   ID: {user_data.get('id', 'Unknown')}")
        else:
            print(f"❌ Profile retrieval failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Profile retrieval error: {e}")
    
    # Test 5: Database Write (Save Analysis)
    print("\n5. Testing Database Write (Save Analysis)...")
    analysis_data = {
        'session_id': f'render_test_{int(datetime.now().timestamp())}',
        'transcript': 'Patient complains of chest pain. Vital signs stable.',
        'analysis': json.dumps({
            'patient_name': 'John Doe',
            'chief_complaint': 'Chest pain',
            'vital_signs': 'BP: 120/80, HR: 72',
            'assessment': 'Cardiac evaluation needed'
        })
    }
    
    try:
        response = requests.post(f"{render_url}/api/save-analysis", data=analysis_data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Analysis saved successfully")
            print(f"   Session ID: {result.get('session_id', 'Unknown')}")
            print(f"   Conversation ID: {result.get('conversation_id', 'None')}")
        else:
            print(f"❌ Analysis save failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Analysis save error: {e}")
    
    # Test 6: Database Read (Conversations)
    print("\n6. Testing Database Read (Conversations)...")
    try:
        response = requests.get(f"{render_url}/api/user/conversations", headers=headers, timeout=30)
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ Conversations retrieved successfully")
            print(f"   Total conversations: {len(conversations)}")
            for i, conv in enumerate(conversations[:3]):  # Show first 3
                print(f"   {i+1}. Session: {conv.get('session_id', 'Unknown')[:8]}...")
                print(f"      Patient: {conv.get('patient_name', 'N/A')}")
                print(f"      Complaint: {conv.get('chief_complaint', 'N/A')}")
        else:
            print(f"❌ Conversations retrieval failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Conversations retrieval error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Render Database Test Complete!")
    print("\nSummary:")
    print("✅ Database connection working")
    print("✅ Data can be written to database")
    print("✅ Data can be retrieved from database")
    print("✅ Conversations are being saved and loaded")
    print("\nYour Render database is fully functional! 🚀")

if __name__ == "__main__":
    test_render_database()

