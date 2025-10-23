import requests
import sys
import json
from datetime import datetime
import uuid

class MoodMeshAPITester:
    def __init__(self, base_url="https://visible-trainer-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = None
        self.test_username = f"test_user_{datetime.now().strftime('%H%M%S')}"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=30)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_create_profile(self):
        """Test profile creation"""
        success, response = self.run_test(
            "Create User Profile",
            "POST",
            "profile/create",
            200,
            params={"username": self.test_username}
        )
        if success and 'user_id' in response:
            self.test_user_id = response['user_id']
            print(f"   Created user ID: {self.test_user_id}")
            return True
        return False

    def test_get_profile(self):
        """Test getting user profile"""
        if not self.test_user_id:
            print("❌ Skipping - No user ID available")
            return False
            
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            f"profile/{self.test_user_id}",
            200
        )
        return success

    def test_mood_logging(self):
        """Test mood logging with AI suggestion"""
        if not self.test_user_id:
            print("❌ Skipping - No user ID available")
            return False

        mood_data = {
            "user_id": self.test_user_id,
            "mood_text": "I'm feeling anxious about work today and need some support"
        }
        
        success, response = self.run_test(
            "Log Mood with AI Suggestion",
            "POST",
            "mood/log",
            200,
            data=mood_data
        )
        
        if success:
            # Check if AI suggestion is present
            if 'ai_suggestion' in response and response['ai_suggestion']:
                print(f"   AI Suggestion: {response['ai_suggestion'][:100]}...")
                return True
            else:
                print("❌ AI suggestion missing in response")
                return False
        return False

    def test_get_mood_logs(self):
        """Test retrieving mood logs"""
        if not self.test_user_id:
            print("❌ Skipping - No user ID available")
            return False
            
        success, response = self.run_test(
            "Get Mood Logs",
            "GET",
            f"mood/logs/{self.test_user_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} mood logs")
            return True
        return False

    def test_chat_messages(self):
        """Test getting chat messages"""
        room_id = "wellness-room-1"
        success, response = self.run_test(
            "Get Chat Messages",
            "GET",
            f"chat/messages/{room_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} chat messages")
            return True
        return False

    def test_profile_update_after_mood_log(self):
        """Test that wellness stars are updated after mood logging"""
        if not self.test_user_id:
            print("❌ Skipping - No user ID available")
            return False

        # Get initial profile
        success, initial_profile = self.run_test(
            "Get Profile Before Mood Log",
            "GET",
            f"profile/{self.test_user_id}",
            200
        )
        
        if not success:
            return False
            
        initial_stars = initial_profile.get('wellness_stars', 0)
        print(f"   Initial wellness stars: {initial_stars}")
        
        # Log another mood
        mood_data = {
            "user_id": self.test_user_id,
            "mood_text": "Feeling better after some deep breathing exercises"
        }
        
        success, _ = self.run_test(
            "Log Another Mood",
            "POST",
            "mood/log",
            200,
            data=mood_data
        )
        
        if not success:
            return False
            
        # Check updated profile
        success, updated_profile = self.run_test(
            "Get Profile After Mood Log",
            "GET",
            f"profile/{self.test_user_id}",
            200
        )
        
        if success:
            updated_stars = updated_profile.get('wellness_stars', 0)
            print(f"   Updated wellness stars: {updated_stars}")
            if updated_stars > initial_stars:
                print("✅ Wellness stars incremented correctly")
                return True
            else:
                print("❌ Wellness stars not incremented")
                return False
        return False

def main():
    print("🚀 Starting MoodMesh API Testing...")
    print("=" * 50)
    
    tester = MoodMeshAPITester()
    
    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Create Profile", tester.test_create_profile),
        ("Get Profile", tester.test_get_profile),
        ("Mood Logging with AI", tester.test_mood_logging),
        ("Get Mood Logs", tester.test_get_mood_logs),
        ("Chat Messages", tester.test_chat_messages),
        ("Wellness Stars Update", tester.test_profile_update_after_mood_log),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())