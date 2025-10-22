#!/usr/bin/env python3
"""
Backend Test Suite for MoodMesh - Analytics & Meditation Features
Tests the /api/mood/analytics/{user_id} and meditation endpoints thoroughly
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import time

# Backend URL from frontend .env
BACKEND_URL = "https://mood-fitness-connect.preview.emergentagent.com/api"

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

class MoodMeshMeditationTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = None
        self.auth_token = None
        self.test_username = f"meditation_test_user_{int(time.time())}"
        self.test_password = "testpass123"
        self.session_id = None
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def register_test_user(self):
        """Register a test user for meditation testing"""
        try:
            response = requests.post(f"{self.base_url}/auth/register", json={
                "username": self.test_username,
                "password": self.test_password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_id = data["user_id"]
                self.auth_token = data["access_token"]
                self.log_test("Meditation User Registration", True, f"Created user: {self.test_username}")
                return True
            else:
                self.log_test("Meditation User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Meditation User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_get_breathing_exercises(self):
        """Test GET /api/meditation/exercises endpoint"""
        try:
            response = requests.get(f"{self.base_url}/meditation/exercises")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check structure
                if "exercises" not in data:
                    self.log_test("Get Breathing Exercises - Structure", False, "Missing 'exercises' key")
                    return False
                
                exercises = data["exercises"]
                
                # Should return 5 exercises
                if len(exercises) != 5:
                    self.log_test("Get Breathing Exercises - Count", False, f"Expected 5 exercises, got {len(exercises)}")
                    return False
                
                # Check first exercise structure
                first_exercise = exercises[0]
                required_keys = ["id", "name", "duration", "pattern", "description", "instructions", "benefits"]
                missing_keys = [key for key in required_keys if key not in first_exercise]
                
                if missing_keys:
                    self.log_test("Get Breathing Exercises - Exercise Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify specific exercises exist
                exercise_ids = [ex["id"] for ex in exercises]
                expected_ids = ["box_breathing", "breathing_478", "deep_belly", "alternate_nostril", "resonant_breathing"]
                
                for expected_id in expected_ids:
                    if expected_id not in exercise_ids:
                        self.log_test("Get Breathing Exercises - Expected IDs", False, f"Missing exercise: {expected_id}")
                        return False
                
                self.log_test("Get Breathing Exercises", True, f"Successfully returned {len(exercises)} breathing exercises")
                return True
            else:
                self.log_test("Get Breathing Exercises", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Breathing Exercises", False, f"Exception: {str(e)}")
            return False
    
    def test_get_meditation_sessions(self):
        """Test GET /api/meditation/sessions endpoint"""
        try:
            response = requests.get(f"{self.base_url}/meditation/sessions")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check structure
                if "sessions" not in data:
                    self.log_test("Get Meditation Sessions - Structure", False, "Missing 'sessions' key")
                    return False
                
                sessions = data["sessions"]
                
                # Should return 10 sessions
                if len(sessions) != 10:
                    self.log_test("Get Meditation Sessions - Count", False, f"Expected 10 sessions, got {len(sessions)}")
                    return False
                
                # Check first session structure
                first_session = sessions[0]
                required_keys = ["id", "title", "duration", "category", "description", "instructions", "goal"]
                missing_keys = [key for key in required_keys if key not in first_session]
                
                if missing_keys:
                    self.log_test("Get Meditation Sessions - Session Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Check categories
                categories = set(session["category"] for session in sessions)
                expected_categories = {"stress_relief", "sleep", "focus", "anxiety"}
                
                if not expected_categories.issubset(categories):
                    missing_cats = expected_categories - categories
                    self.log_test("Get Meditation Sessions - Categories", False, f"Missing categories: {missing_cats}")
                    return False
                
                self.log_test("Get Meditation Sessions", True, f"Successfully returned {len(sessions)} meditation sessions")
                return True
            else:
                self.log_test("Get Meditation Sessions", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Meditation Sessions", False, f"Exception: {str(e)}")
            return False
    
    def test_get_meditation_sessions_filtered(self):
        """Test GET /api/meditation/sessions?category=stress_relief endpoint"""
        try:
            response = requests.get(f"{self.base_url}/meditation/sessions?category=stress_relief")
            
            if response.status_code == 200:
                data = response.json()
                sessions = data["sessions"]
                
                # All sessions should be stress_relief category
                for session in sessions:
                    if session["category"] != "stress_relief":
                        self.log_test("Get Filtered Sessions", False, f"Found non-stress_relief session: {session['category']}")
                        return False
                
                # Should have at least 1 stress_relief session
                if len(sessions) == 0:
                    self.log_test("Get Filtered Sessions", False, "No stress_relief sessions found")
                    return False
                
                self.log_test("Get Filtered Sessions", True, f"Successfully filtered {len(sessions)} stress_relief sessions")
                return True
            else:
                self.log_test("Get Filtered Sessions", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Filtered Sessions", False, f"Exception: {str(e)}")
            return False
    
    def test_start_meditation_session(self):
        """Test POST /api/meditation/start endpoint"""
        try:
            if not self.test_user_id:
                self.log_test("Start Session - No User", False, "No test user available")
                return False
            
            session_data = {
                "user_id": self.test_user_id,
                "session_type": "breathing",
                "content_id": "box_breathing",
                "duration": 240
            }
            
            response = requests.post(f"{self.base_url}/meditation/start", json=session_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["id", "user_id", "session_type", "content_id", "duration", "completed", "timestamp"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Start Session - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify data matches request
                if (data["user_id"] != session_data["user_id"] or
                    data["session_type"] != session_data["session_type"] or
                    data["content_id"] != session_data["content_id"] or
                    data["duration"] != session_data["duration"]):
                    self.log_test("Start Session - Data Mismatch", False, "Response data doesn't match request")
                    return False
                
                # Should not be completed initially
                if data["completed"] != False:
                    self.log_test("Start Session - Initial State", False, "Session should not be completed initially")
                    return False
                
                # Store session ID for completion test
                self.session_id = data["id"]
                
                self.log_test("Start Meditation Session", True, f"Successfully started session: {data['id']}")
                return True
            else:
                self.log_test("Start Meditation Session", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Start Meditation Session", False, f"Exception: {str(e)}")
            return False
    
    def test_complete_meditation_session(self):
        """Test POST /api/meditation/complete endpoint"""
        try:
            if not self.session_id:
                self.log_test("Complete Session - No Session", False, "No session ID available")
                return False
            
            completion_data = {
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/meditation/complete", json=completion_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "message" not in data or "stars_earned" not in data:
                    self.log_test("Complete Session - Structure", False, "Missing message or stars_earned")
                    return False
                
                # Should award 2 stars
                if data["stars_earned"] != 2:
                    self.log_test("Complete Session - Stars", False, f"Expected 2 stars, got {data['stars_earned']}")
                    return False
                
                self.log_test("Complete Meditation Session", True, f"Successfully completed session, earned {data['stars_earned']} stars")
                return True
            else:
                self.log_test("Complete Meditation Session", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Complete Meditation Session", False, f"Exception: {str(e)}")
            return False
    
    def test_get_meditation_progress(self):
        """Test GET /api/meditation/progress/{user_id} endpoint"""
        try:
            if not self.test_user_id:
                self.log_test("Get Progress - No User", False, "No test user available")
                return False
            
            response = requests.get(f"{self.base_url}/meditation/progress/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["total_sessions", "total_minutes", "breathing_sessions", "meditation_sessions", 
                               "favorite_category", "current_streak", "recent_sessions"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Get Progress - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should have at least 1 session if we completed one
                if self.session_id and data["total_sessions"] == 0:
                    self.log_test("Get Progress - Session Count", False, "Expected at least 1 completed session")
                    return False
                
                # Verify data types
                if not isinstance(data["total_sessions"], int) or data["total_sessions"] < 0:
                    self.log_test("Get Progress - Total Sessions Type", False, "Invalid total_sessions value")
                    return False
                
                if not isinstance(data["recent_sessions"], list):
                    self.log_test("Get Progress - Recent Sessions Type", False, "recent_sessions should be a list")
                    return False
                
                self.log_test("Get Meditation Progress", True, f"Progress: {data['total_sessions']} sessions, {data['total_minutes']} minutes")
                return True
            else:
                self.log_test("Get Meditation Progress", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Meditation Progress", False, f"Exception: {str(e)}")
            return False
    
    def create_mood_log_for_recommendations(self, mood_text):
        """Create a mood log to test recommendations"""
        try:
            response = requests.post(f"{self.base_url}/mood/log", json={
                "user_id": self.test_user_id,
                "mood_text": mood_text
            })
            return response.status_code == 200
        except:
            return False
    
    def test_get_meditation_recommendations(self):
        """Test GET /api/meditation/recommendations/{user_id} endpoint"""
        try:
            if not self.test_user_id:
                self.log_test("Get Recommendations - No User", False, "No test user available")
                return False
            
            # Create some mood logs to influence recommendations
            self.create_mood_log_for_recommendations("I'm feeling really stressed and anxious about work")
            time.sleep(0.5)
            self.create_mood_log_for_recommendations("Having trouble sleeping, feeling overwhelmed")
            time.sleep(0.5)
            
            response = requests.get(f"{self.base_url}/meditation/recommendations/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "recommendations" not in data:
                    self.log_test("Get Recommendations - Structure", False, "Missing 'recommendations' key")
                    return False
                
                recommendations = data["recommendations"]
                
                if not isinstance(recommendations, list):
                    self.log_test("Get Recommendations - Type", False, "recommendations should be a list")
                    return False
                
                # Should have at least 1 recommendation
                if len(recommendations) == 0:
                    self.log_test("Get Recommendations - Count", False, "No recommendations returned")
                    return False
                
                # Check first recommendation structure
                first_rec = recommendations[0]
                required_keys = ["type", "content", "reason"]
                missing_keys = [key for key in required_keys if key not in first_rec]
                
                if missing_keys:
                    self.log_test("Get Recommendations - Rec Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Type should be 'breathing' or 'meditation'
                if first_rec["type"] not in ["breathing", "meditation"]:
                    self.log_test("Get Recommendations - Type Value", False, f"Invalid type: {first_rec['type']}")
                    return False
                
                self.log_test("Get Meditation Recommendations", True, f"Successfully returned {len(recommendations)} recommendations")
                return True
            else:
                self.log_test("Get Meditation Recommendations", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Meditation Recommendations", False, f"Exception: {str(e)}")
            return False
    
    def test_meditation_endpoints_availability(self):
        """Test if all meditation endpoints are available"""
        try:
            endpoints = [
                "/meditation/exercises",
                "/meditation/sessions",
                f"/meditation/progress/{str(uuid.uuid4())}",
                f"/meditation/recommendations/{str(uuid.uuid4())}"
            ]
            
            all_available = True
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code not in [200, 404]:
                    self.log_test(f"Endpoint {endpoint}", False, f"Status: {response.status_code}")
                    all_available = False
            
            if all_available:
                self.log_test("Meditation Endpoints Availability", True, "All endpoints are accessible")
                return True
            else:
                self.log_test("Meditation Endpoints Availability", False, "Some endpoints are not accessible")
                return False
        except Exception as e:
            self.log_test("Meditation Endpoints Availability", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all meditation tests"""
        print("=" * 60)
        print("🧘 MOODMESH MEDITATION BACKEND TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test endpoint availability first
        results["endpoints_availability"] = self.test_meditation_endpoints_availability()
        
        # Test breathing exercises endpoint
        results["breathing_exercises"] = self.test_get_breathing_exercises()
        
        # Test meditation sessions endpoint
        results["meditation_sessions"] = self.test_get_meditation_sessions()
        
        # Test filtered sessions
        results["filtered_sessions"] = self.test_get_meditation_sessions_filtered()
        
        # Register test user for session tests
        if self.register_test_user():
            results["user_registration"] = True
            
            # Test session workflow
            results["start_session"] = self.test_start_meditation_session()
            results["complete_session"] = self.test_complete_meditation_session()
            results["progress"] = self.test_get_meditation_progress()
            results["recommendations"] = self.test_get_meditation_recommendations()
        else:
            results["user_registration"] = False
            results["start_session"] = False
            results["complete_session"] = False
            results["progress"] = False
            results["recommendations"] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 MEDITATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All meditation tests PASSED!")
            return True
        else:
            print("⚠️  Some meditation tests FAILED!")
            return False

if __name__ == "__main__":
    print("🧪 RUNNING MOODMESH BACKEND TESTS")
    print("=" * 60)
    
    # Run Analytics Tests
    analytics_tester = MoodMeshAnalyticsTest()
    analytics_success = analytics_tester.run_all_tests()
    
    print("\n" + "=" * 60)
    
    # Run Meditation Tests  
    meditation_tester = MoodMeshMeditationTest()
    meditation_success = meditation_tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    
    if analytics_success and meditation_success:
        print("🎉 ALL TESTS PASSED! Backend is working correctly.")
        exit(0)
    else:
        if not analytics_success:
            print("❌ Analytics tests failed")
        if not meditation_success:
            print("❌ Meditation tests failed")
        exit(1)