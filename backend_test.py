#!/usr/bin/env python3
"""
Backend Test Suite for MoodMesh Analytics Feature
Tests the /api/mood/analytics/{user_id} endpoint thoroughly
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import time

# Backend URL from frontend .env
BACKEND_URL = "https://feature-explorer-31.preview.emergentagent.com/api"

class MoodMeshAnalyticsTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = None
        self.auth_token = None
        self.test_username = f"analytics_test_user_{int(time.time())}"
        self.test_password = "testpass123"
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def register_test_user(self):
        """Register a test user for analytics testing"""
        try:
            response = requests.post(f"{self.base_url}/auth/register", json={
                "username": self.test_username,
                "password": self.test_password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_id = data["user_id"]
                self.auth_token = data["access_token"]
                self.log_test("User Registration", True, f"Created user: {self.test_username}")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def create_mood_log(self, mood_text, timestamp_offset_hours=0):
        """Create a mood log for testing"""
        try:
            response = requests.post(f"{self.base_url}/mood/log", json={
                "user_id": self.test_user_id,
                "mood_text": mood_text
            })
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to create mood log: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception creating mood log: {str(e)}")
            return None
    
    def test_analytics_empty_user(self):
        """Test analytics endpoint with a user who has no mood logs"""
        try:
            # Create a new user with no mood logs
            empty_user_id = str(uuid.uuid4())
            
            response = requests.get(f"{self.base_url}/mood/analytics/{empty_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify empty analytics structure
                expected_keys = ["total_logs", "mood_trend", "hourly_distribution", 
                               "common_emotions", "insights", "current_streak", "longest_streak"]
                
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    self.log_test("Empty User Analytics - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify empty values
                if (data["total_logs"] == 0 and 
                    data["mood_trend"] == [] and 
                    data["hourly_distribution"] == {} and 
                    data["common_emotions"] == [] and 
                    data["insights"] == [] and 
                    data["current_streak"] == 0 and 
                    data["longest_streak"] == 0):
                    self.log_test("Empty User Analytics", True, "Correctly returns empty analytics")
                    return True
                else:
                    self.log_test("Empty User Analytics", False, f"Unexpected values: {data}")
                    return False
            else:
                self.log_test("Empty User Analytics", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Empty User Analytics", False, f"Exception: {str(e)}")
            return False
    
    def test_analytics_with_data(self):
        """Test analytics endpoint with a user who has multiple mood logs"""
        try:
            # Create multiple mood logs with different content and times
            mood_logs = [
                "I'm feeling really happy today! The sun is shining and everything feels great.",
                "Feeling a bit anxious about work tomorrow. Stressed about the presentation.",
                "Had a wonderful day with friends. Feeling grateful and joyful.",
                "Feeling sad and lonely tonight. Missing my family.",
                "Excited about the weekend plans! Can't wait to relax.",
                "Feeling overwhelmed with all the tasks. Need to take a break.",
                "Happy and content after a good workout session.",
                "Anxious thoughts keep coming back. Worried about the future."
            ]
            
            # Create mood logs
            created_logs = []
            for mood_text in mood_logs:
                log = self.create_mood_log(mood_text)
                if log:
                    created_logs.append(log)
                time.sleep(0.1)  # Small delay to ensure different timestamps
            
            if len(created_logs) == 0:
                self.log_test("Create Test Data", False, "Failed to create any mood logs")
                return False
            
            self.log_test("Create Test Data", True, f"Created {len(created_logs)} mood logs")
            
            # Wait a moment for data to be processed
            time.sleep(1)
            
            # Test analytics endpoint
            response = requests.get(f"{self.base_url}/mood/analytics/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                expected_keys = ["total_logs", "mood_trend", "hourly_distribution", 
                               "common_emotions", "insights", "current_streak", "longest_streak"]
                
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    self.log_test("Analytics Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Test total_logs
                if data["total_logs"] == len(created_logs):
                    self.log_test("Total Logs Count", True, f"Correct count: {data['total_logs']}")
                else:
                    self.log_test("Total Logs Count", False, f"Expected {len(created_logs)}, got {data['total_logs']}")
                
                # Test mood_trend (should have at least one entry for today)
                if isinstance(data["mood_trend"], list) and len(data["mood_trend"]) > 0:
                    self.log_test("Mood Trend", True, f"Has {len(data['mood_trend'])} trend entries")
                else:
                    self.log_test("Mood Trend", False, f"Invalid mood trend: {data['mood_trend']}")
                
                # Test hourly_distribution
                if isinstance(data["hourly_distribution"], dict):
                    total_hourly = sum(data["hourly_distribution"].values())
                    if total_hourly == len(created_logs):
                        self.log_test("Hourly Distribution", True, f"Correct hourly distribution")
                    else:
                        self.log_test("Hourly Distribution", False, f"Hourly sum {total_hourly} != logs {len(created_logs)}")
                else:
                    self.log_test("Hourly Distribution", False, "Invalid hourly distribution format")
                
                # Test common_emotions
                if isinstance(data["common_emotions"], list):
                    if len(data["common_emotions"]) > 0:
                        # Check if emotions have word and count
                        first_emotion = data["common_emotions"][0]
                        if "word" in first_emotion and "count" in first_emotion:
                            self.log_test("Common Emotions", True, f"Found {len(data['common_emotions'])} common emotions")
                        else:
                            self.log_test("Common Emotions", False, "Invalid emotion structure")
                    else:
                        self.log_test("Common Emotions", True, "No common emotions (acceptable)")
                else:
                    self.log_test("Common Emotions", False, "Invalid common emotions format")
                
                # Test insights
                if isinstance(data["insights"], list):
                    self.log_test("Insights", True, f"Generated {len(data['insights'])} insights")
                else:
                    self.log_test("Insights", False, "Invalid insights format")
                
                # Test streaks (should be non-negative integers)
                if isinstance(data["current_streak"], int) and data["current_streak"] >= 0:
                    self.log_test("Current Streak", True, f"Current streak: {data['current_streak']}")
                else:
                    self.log_test("Current Streak", False, f"Invalid current streak: {data['current_streak']}")
                
                if isinstance(data["longest_streak"], int) and data["longest_streak"] >= 0:
                    self.log_test("Longest Streak", True, f"Longest streak: {data['longest_streak']}")
                else:
                    self.log_test("Longest Streak", False, f"Invalid longest streak: {data['longest_streak']}")
                
                return True
            else:
                self.log_test("Analytics with Data", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Analytics with Data", False, f"Exception: {str(e)}")
            return False
    
    def test_single_mood_log(self):
        """Test analytics with only one mood log"""
        try:
            # Create a new user for this test
            single_user_response = requests.post(f"{self.base_url}/auth/register", json={
                "username": f"single_test_{int(time.time())}",
                "password": "testpass123"
            })
            
            if single_user_response.status_code != 200:
                self.log_test("Single Log Test Setup", False, "Failed to create test user")
                return False
            
            single_user_data = single_user_response.json()
            single_user_id = single_user_data["user_id"]
            
            # Create one mood log
            log_response = requests.post(f"{self.base_url}/mood/log", json={
                "user_id": single_user_id,
                "mood_text": "Testing with just one mood log entry"
            })
            
            if log_response.status_code != 200:
                self.log_test("Single Log Creation", False, "Failed to create mood log")
                return False
            
            time.sleep(1)  # Wait for processing
            
            # Test analytics
            response = requests.get(f"{self.base_url}/mood/analytics/{single_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["total_logs"] == 1:
                    self.log_test("Single Mood Log Analytics", True, "Correctly handles single log")
                    return True
                else:
                    self.log_test("Single Mood Log Analytics", False, f"Expected 1 log, got {data['total_logs']}")
                    return False
            else:
                self.log_test("Single Mood Log Analytics", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Single Mood Log Analytics", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_user_id(self):
        """Test analytics endpoint with invalid user_id"""
        try:
            invalid_user_id = "invalid-user-id-12345"
            response = requests.get(f"{self.base_url}/mood/analytics/{invalid_user_id}")
            
            # Should return empty analytics gracefully, not an error
            if response.status_code == 200:
                data = response.json()
                if data["total_logs"] == 0:
                    self.log_test("Invalid User ID", True, "Gracefully handles invalid user ID")
                    return True
                else:
                    self.log_test("Invalid User ID", False, f"Unexpected data for invalid user: {data}")
                    return False
            else:
                self.log_test("Invalid User ID", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid User ID", False, f"Exception: {str(e)}")
            return False
    
    def test_endpoint_availability(self):
        """Test if the analytics endpoint is available"""
        try:
            # Test with a random UUID to check endpoint availability
            test_id = str(uuid.uuid4())
            response = requests.get(f"{self.base_url}/mood/analytics/{test_id}")
            
            if response.status_code in [200, 404]:
                self.log_test("Endpoint Availability", True, "Analytics endpoint is accessible")
                return True
            else:
                self.log_test("Endpoint Availability", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Endpoint Availability", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all analytics tests"""
        print("=" * 60)
        print("🧪 MOODMESH ANALYTICS BACKEND TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test endpoint availability first
        results["endpoint_availability"] = self.test_endpoint_availability()
        
        # Test with empty user (no registration needed)
        results["empty_user"] = self.test_analytics_empty_user()
        
        # Test with invalid user ID
        results["invalid_user"] = self.test_invalid_user_id()
        
        # Register test user for data tests
        if self.register_test_user():
            results["user_registration"] = True
            
            # Test with single mood log
            results["single_log"] = self.test_single_mood_log()
            
            # Test with multiple mood logs
            results["multiple_logs"] = self.test_analytics_with_data()
        else:
            results["user_registration"] = False
            results["single_log"] = False
            results["multiple_logs"] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All analytics tests PASSED!")
            return True
        else:
            print("⚠️  Some analytics tests FAILED!")
            return False

if __name__ == "__main__":
    tester = MoodMeshAnalyticsTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)