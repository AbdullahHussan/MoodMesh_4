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
BACKEND_URL = "https://posescan-ai.preview.emergentagent.com/api"

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

class MoodMeshExerciseTrainerTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = None
        self.auth_token = None
        self.test_username = f"exercise_test_user_{int(time.time())}"
        self.test_password = "testpass123"
        self.session_id = None
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def register_test_user(self):
        """Register a test user for exercise testing"""
        try:
            response = requests.post(f"{self.base_url}/auth/register", json={
                "username": self.test_username,
                "password": self.test_password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_id = data["user_id"]
                self.auth_token = data["access_token"]
                self.log_test("Exercise User Registration", True, f"Created user: {self.test_username}")
                return True
            else:
                self.log_test("Exercise User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Exercise User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_get_exercise_list_all(self):
        """Test GET /api/exercises/list - Get all exercises"""
        try:
            response = requests.get(f"{self.base_url}/exercises/list")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "count" not in data or "exercises" not in data:
                    self.log_test("Get Exercise List - Structure", False, "Missing 'count' or 'exercises' key")
                    return False
                
                exercises = data["exercises"]
                
                # Should return 12 exercises
                if len(exercises) != 12:
                    self.log_test("Get Exercise List - Count", False, f"Expected 12 exercises, got {len(exercises)}")
                    return False
                
                # Check first exercise structure
                first_exercise = exercises[0]
                required_keys = ["id", "name", "description", "category", "difficulty", "target_muscles", 
                               "video_url", "form_tips", "calories_per_rep"]
                missing_keys = [key for key in required_keys if key not in first_exercise]
                
                if missing_keys:
                    self.log_test("Get Exercise List - Exercise Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify categories exist
                categories = set(ex["category"] for ex in exercises)
                expected_categories = {"strength", "cardio", "yoga"}
                
                if not expected_categories.issubset(categories):
                    missing_cats = expected_categories - categories
                    self.log_test("Get Exercise List - Categories", False, f"Missing categories: {missing_cats}")
                    return False
                
                # Verify difficulties exist
                difficulties = set(ex["difficulty"] for ex in exercises)
                expected_difficulties = {"beginner", "intermediate", "advanced"}
                
                if not expected_difficulties.issubset(difficulties):
                    missing_diffs = expected_difficulties - difficulties
                    self.log_test("Get Exercise List - Difficulties", False, f"Missing difficulties: {missing_diffs}")
                    return False
                
                self.log_test("Get Exercise List (All)", True, f"Successfully returned {len(exercises)} exercises")
                return True
            else:
                self.log_test("Get Exercise List (All)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Exercise List (All)", False, f"Exception: {str(e)}")
            return False
    
    def test_get_exercise_list_filtered_category(self):
        """Test GET /api/exercises/list?category=strength - Filter by category"""
        try:
            response = requests.get(f"{self.base_url}/exercises/list?category=strength")
            
            if response.status_code == 200:
                data = response.json()
                exercises = data["exercises"]
                
                # All exercises should be strength category
                for exercise in exercises:
                    if exercise["category"] != "strength":
                        self.log_test("Get Exercise List (Strength)", False, f"Found non-strength exercise: {exercise['category']}")
                        return False
                
                # Should have 4 strength exercises
                if len(exercises) != 4:
                    self.log_test("Get Exercise List (Strength)", False, f"Expected 4 strength exercises, got {len(exercises)}")
                    return False
                
                self.log_test("Get Exercise List (Strength)", True, f"Successfully filtered {len(exercises)} strength exercises")
                return True
            else:
                self.log_test("Get Exercise List (Strength)", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Exercise List (Strength)", False, f"Exception: {str(e)}")
            return False
    
    def test_get_exercise_list_filtered_difficulty(self):
        """Test GET /api/exercises/list?difficulty=beginner - Filter by difficulty"""
        try:
            response = requests.get(f"{self.base_url}/exercises/list?difficulty=beginner")
            
            if response.status_code == 200:
                data = response.json()
                exercises = data["exercises"]
                
                # All exercises should be beginner difficulty
                for exercise in exercises:
                    if exercise["difficulty"] != "beginner":
                        self.log_test("Get Exercise List (Beginner)", False, f"Found non-beginner exercise: {exercise['difficulty']}")
                        return False
                
                # Should have beginner exercises
                if len(exercises) == 0:
                    self.log_test("Get Exercise List (Beginner)", False, "No beginner exercises found")
                    return False
                
                self.log_test("Get Exercise List (Beginner)", True, f"Successfully filtered {len(exercises)} beginner exercises")
                return True
            else:
                self.log_test("Get Exercise List (Beginner)", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Exercise List (Beginner)", False, f"Exception: {str(e)}")
            return False
    
    def test_get_exercise_details_valid(self):
        """Test GET /api/exercises/{exercise_id} - Get specific exercise details"""
        try:
            # Test with push-ups
            response = requests.get(f"{self.base_url}/exercises/push-ups")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_keys = ["id", "name", "description", "category", "difficulty", "target_muscles", 
                               "video_url", "form_tips", "calories_per_rep", "key_points", "pose_requirements"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Get Exercise Details (Valid) - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify it's the correct exercise
                if data["id"] != "push-ups" or data["name"] != "Push-Ups":
                    self.log_test("Get Exercise Details (Valid) - ID Match", False, "Exercise ID/name doesn't match")
                    return False
                
                # Check form_tips is a list
                if not isinstance(data["form_tips"], list) or len(data["form_tips"]) == 0:
                    self.log_test("Get Exercise Details (Valid) - Form Tips", False, "form_tips should be a non-empty list")
                    return False
                
                # Check target_muscles is a list
                if not isinstance(data["target_muscles"], list) or len(data["target_muscles"]) == 0:
                    self.log_test("Get Exercise Details (Valid) - Target Muscles", False, "target_muscles should be a non-empty list")
                    return False
                
                self.log_test("Get Exercise Details (Valid)", True, f"Successfully retrieved details for {data['name']}")
                return True
            else:
                self.log_test("Get Exercise Details (Valid)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Exercise Details (Valid)", False, f"Exception: {str(e)}")
            return False
    
    def test_get_exercise_details_invalid(self):
        """Test GET /api/exercises/{exercise_id} - Invalid exercise ID"""
        try:
            response = requests.get(f"{self.base_url}/exercises/invalid-exercise-id")
            
            if response.status_code == 404:
                self.log_test("Get Exercise Details (Invalid)", True, "Correctly returns 404 for invalid exercise ID")
                return True
            else:
                self.log_test("Get Exercise Details (Invalid)", False, f"Expected 404, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Exercise Details (Invalid)", False, f"Exception: {str(e)}")
            return False
    
    def test_start_exercise_session(self):
        """Test POST /api/exercises/session/start - Start exercise session"""
        try:
            if not self.test_user_id:
                self.log_test("Start Exercise Session - No User", False, "No test user available")
                return False
            
            session_data = {
                "user_id": self.test_user_id,
                "exercise_id": "push-ups",
                "target_reps": 10,
                "used_ai_coach": True
            }
            
            response = requests.post(f"{self.base_url}/exercises/session/start", json=session_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["session_id", "exercise", "target_reps", "message"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Start Exercise Session - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify data matches request
                if (data["target_reps"] != session_data["target_reps"] or
                    data["exercise"]["id"] != session_data["exercise_id"]):
                    self.log_test("Start Exercise Session - Data Mismatch", False, "Response data doesn't match request")
                    return False
                
                # Store session ID for later tests
                self.session_id = data["session_id"]
                
                self.log_test("Start Exercise Session", True, f"Successfully started session: {data['session_id']}")
                return True
            else:
                self.log_test("Start Exercise Session", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Start Exercise Session", False, f"Exception: {str(e)}")
            return False
    
    def test_update_exercise_session(self):
        """Test POST /api/exercises/session/update - Update session progress"""
        try:
            if not self.session_id:
                self.log_test("Update Exercise Session - No Session", False, "No session ID available")
                return False
            
            update_data = {
                "session_id": self.session_id,
                "completed_reps": 5,
                "form_accuracy": 85.0,
                "feedback_notes": ["Good form", "Keep back straight"]
            }
            
            response = requests.post(f"{self.base_url}/exercises/session/update", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "message" not in data or "completed_reps" not in data:
                    self.log_test("Update Exercise Session - Structure", False, "Missing message or completed_reps")
                    return False
                
                # Verify completed_reps matches
                if data["completed_reps"] != update_data["completed_reps"]:
                    self.log_test("Update Exercise Session - Reps Mismatch", False, f"Expected {update_data['completed_reps']}, got {data['completed_reps']}")
                    return False
                
                self.log_test("Update Exercise Session", True, f"Successfully updated session to {data['completed_reps']} reps")
                return True
            else:
                self.log_test("Update Exercise Session", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Update Exercise Session", False, f"Exception: {str(e)}")
            return False
    
    def test_complete_exercise_session(self):
        """Test POST /api/exercises/session/complete - Complete session and award stars"""
        try:
            if not self.session_id:
                self.log_test("Complete Exercise Session - No Session", False, "No session ID available")
                return False
            
            complete_data = {
                "session_id": self.session_id,
                "completed_reps": 10,
                "duration_seconds": 120,
                "form_accuracy": 90.0
            }
            
            response = requests.post(f"{self.base_url}/exercises/session/complete", json=complete_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["message", "completed_reps", "target_reps", "duration_seconds", 
                               "calories_burned", "stars_awarded", "form_accuracy"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Complete Exercise Session - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should award 3 stars
                if data["stars_awarded"] != 3:
                    self.log_test("Complete Exercise Session - Stars", False, f"Expected 3 stars, got {data['stars_awarded']}")
                    return False
                
                # Verify completed_reps matches
                if data["completed_reps"] != complete_data["completed_reps"]:
                    self.log_test("Complete Exercise Session - Reps", False, f"Expected {complete_data['completed_reps']}, got {data['completed_reps']}")
                    return False
                
                # Calories should be calculated (10 reps * 0.5 calories_per_rep = 5.0)
                expected_calories = 5.0
                if abs(data["calories_burned"] - expected_calories) > 0.1:
                    self.log_test("Complete Exercise Session - Calories", False, f"Expected ~{expected_calories}, got {data['calories_burned']}")
                    return False
                
                self.log_test("Complete Exercise Session", True, f"Successfully completed session, earned {data['stars_awarded']} stars, burned {data['calories_burned']} calories")
                return True
            else:
                self.log_test("Complete Exercise Session", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Complete Exercise Session", False, f"Exception: {str(e)}")
            return False
    
    def test_get_exercise_history(self):
        """Test GET /api/exercises/history/{user_id} - Get user's exercise history"""
        try:
            if not self.test_user_id:
                self.log_test("Get Exercise History - No User", False, "No test user available")
                return False
            
            response = requests.get(f"{self.base_url}/exercises/history/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "count" not in data or "sessions" not in data:
                    self.log_test("Get Exercise History - Structure", False, "Missing 'count' or 'sessions' key")
                    return False
                
                sessions = data["sessions"]
                
                # Should have at least 1 session if we completed one
                if self.session_id and len(sessions) == 0:
                    self.log_test("Get Exercise History - Session Count", False, "Expected at least 1 session")
                    return False
                
                # Check first session structure if exists
                if sessions:
                    first_session = sessions[0]
                    required_keys = ["session_id", "user_id", "exercise_id", "exercise_name", 
                                   "target_reps", "completed_reps", "used_ai_coach", "session_start"]
                    missing_keys = [key for key in required_keys if key not in first_session]
                    
                    if missing_keys:
                        self.log_test("Get Exercise History - Session Structure", False, f"Missing keys: {missing_keys}")
                        return False
                    
                    # Verify user_id matches
                    if first_session["user_id"] != self.test_user_id:
                        self.log_test("Get Exercise History - User ID", False, "Session user_id doesn't match")
                        return False
                
                self.log_test("Get Exercise History", True, f"Successfully retrieved {len(sessions)} exercise sessions")
                return True
            else:
                self.log_test("Get Exercise History", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Exercise History", False, f"Exception: {str(e)}")
            return False
    
    def test_get_exercise_progress(self):
        """Test GET /api/exercises/progress/{user_id} - Get user's progress statistics"""
        try:
            if not self.test_user_id:
                self.log_test("Get Exercise Progress - No User", False, "No test user available")
                return False
            
            response = requests.get(f"{self.base_url}/exercises/progress/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["total_sessions", "total_reps", "total_calories", "total_minutes", 
                               "exercises_tried", "favorite_exercise", "average_form_accuracy", "current_streak"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Get Exercise Progress - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should have at least 1 session if we completed one
                if self.session_id and data["total_sessions"] == 0:
                    self.log_test("Get Exercise Progress - Session Count", False, "Expected at least 1 completed session")
                    return False
                
                # Verify data types
                if not isinstance(data["total_sessions"], int) or data["total_sessions"] < 0:
                    self.log_test("Get Exercise Progress - Total Sessions Type", False, "Invalid total_sessions value")
                    return False
                
                if not isinstance(data["total_reps"], int) or data["total_reps"] < 0:
                    self.log_test("Get Exercise Progress - Total Reps Type", False, "Invalid total_reps value")
                    return False
                
                if not isinstance(data["current_streak"], int) or data["current_streak"] < 0:
                    self.log_test("Get Exercise Progress - Current Streak Type", False, "Invalid current_streak value")
                    return False
                
                # If we completed a session, check values
                if self.session_id and data["total_sessions"] > 0:
                    if data["total_reps"] != 10:  # We completed 10 reps
                        self.log_test("Get Exercise Progress - Reps Count", False, f"Expected 10 total reps, got {data['total_reps']}")
                        return False
                    
                    if abs(data["total_calories"] - 5.0) > 0.1:  # 10 reps * 0.5 = 5.0 calories
                        self.log_test("Get Exercise Progress - Calories Count", False, f"Expected ~5.0 calories, got {data['total_calories']}")
                        return False
                    
                    if data["exercises_tried"] != 1:  # We tried 1 exercise (push-ups)
                        self.log_test("Get Exercise Progress - Exercises Tried", False, f"Expected 1 exercise tried, got {data['exercises_tried']}")
                        return False
                    
                    if data["favorite_exercise"] != "Push-Ups":  # Should be push-ups
                        self.log_test("Get Exercise Progress - Favorite Exercise", False, f"Expected 'Push-Ups', got {data['favorite_exercise']}")
                        return False
                
                self.log_test("Get Exercise Progress", True, f"Progress: {data['total_sessions']} sessions, {data['total_reps']} reps, {data['total_calories']} calories")
                return True
            else:
                self.log_test("Get Exercise Progress", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Exercise Progress", False, f"Exception: {str(e)}")
            return False
    
    def test_exercise_endpoints_availability(self):
        """Test if all exercise endpoints are available"""
        try:
            endpoints = [
                "/exercises/list",
                "/exercises/push-ups",
                f"/exercises/history/{str(uuid.uuid4())}",
                f"/exercises/progress/{str(uuid.uuid4())}"
            ]
            
            all_available = True
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code not in [200, 404]:
                    self.log_test(f"Endpoint {endpoint}", False, f"Status: {response.status_code}")
                    all_available = False
            
            if all_available:
                self.log_test("Exercise Endpoints Availability", True, "All endpoints are accessible")
                return True
            else:
                self.log_test("Exercise Endpoints Availability", False, "Some endpoints are not accessible")
                return False
        except Exception as e:
            self.log_test("Exercise Endpoints Availability", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all exercise trainer tests"""
        print("=" * 60)
        print("🏋️ EXERCISE TRAINER BACKEND TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test endpoint availability first
        results["endpoints_availability"] = self.test_exercise_endpoints_availability()
        
        # Test exercise list endpoints
        results["exercise_list_all"] = self.test_get_exercise_list_all()
        results["exercise_list_strength"] = self.test_get_exercise_list_filtered_category()
        results["exercise_list_beginner"] = self.test_get_exercise_list_filtered_difficulty()
        
        # Test exercise details endpoints
        results["exercise_details_valid"] = self.test_get_exercise_details_valid()
        results["exercise_details_invalid"] = self.test_get_exercise_details_invalid()
        
        # Register test user for session tests
        if self.register_test_user():
            results["user_registration"] = True
            
            # Test session workflow
            results["start_session"] = self.test_start_exercise_session()
            results["update_session"] = self.test_update_exercise_session()
            results["complete_session"] = self.test_complete_exercise_session()
            results["exercise_history"] = self.test_get_exercise_history()
            results["exercise_progress"] = self.test_get_exercise_progress()
        else:
            results["user_registration"] = False
            results["start_session"] = False
            results["update_session"] = False
            results["complete_session"] = False
            results["exercise_history"] = False
            results["exercise_progress"] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 EXERCISE TRAINER TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All exercise trainer tests PASSED!")
            return True
        else:
            print("⚠️  Some exercise trainer tests FAILED!")
            return False

class MoodMeshMusicTherapyTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = None
        self.auth_token = None
        self.test_username = f"music_test_user_{int(time.time())}"
        self.test_password = "testpass123"
        self.journal_id = None
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def register_test_user(self):
        """Register a test user for music therapy testing"""
        try:
            response = requests.post(f"{self.base_url}/auth/register", json={
                "username": self.test_username,
                "password": self.test_password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_id = data["user_id"]
                self.auth_token = data["access_token"]
                self.log_test("Music User Registration", True, f"Created user: {self.test_username}")
                return True
            else:
                self.log_test("Music User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Music User Registration", False, f"Exception: {str(e)}")
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
    
    # Phase 1: Built-in Audio Library Tests
    def test_get_builtin_audio_library(self):
        """Test GET /api/music/library - Should return categorized audio"""
        try:
            response = requests.get(f"{self.base_url}/music/library")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check structure - should have 3 categories
                expected_categories = ["nature", "white_noise", "binaural_beats"]
                missing_categories = [cat for cat in expected_categories if cat not in data]
                
                if missing_categories:
                    self.log_test("Get Audio Library - Structure", False, f"Missing categories: {missing_categories}")
                    return False
                
                # Count total items (should be 13 as per seeded data)
                total_items = sum(len(data[cat]) for cat in expected_categories)
                if total_items != 13:
                    self.log_test("Get Audio Library - Count", False, f"Expected 13 items, got {total_items}")
                    return False
                
                # Check nature sounds (should have 5)
                if len(data["nature"]) != 5:
                    self.log_test("Get Audio Library - Nature Count", False, f"Expected 5 nature sounds, got {len(data['nature'])}")
                    return False
                
                # Check white noise (should have 3)
                if len(data["white_noise"]) != 3:
                    self.log_test("Get Audio Library - White Noise Count", False, f"Expected 3 white noise, got {len(data['white_noise'])}")
                    return False
                
                # Check binaural beats (should have 4)
                if len(data["binaural_beats"]) != 4:
                    self.log_test("Get Audio Library - Binaural Count", False, f"Expected 4 binaural beats, got {len(data['binaural_beats'])}")
                    return False
                
                # Check first item structure
                if data["nature"]:
                    first_item = data["nature"][0]
                    required_keys = ["id", "title", "description", "category", "duration", "audio_url", "tags"]
                    missing_keys = [key for key in required_keys if key not in first_item]
                    
                    if missing_keys:
                        self.log_test("Get Audio Library - Item Structure", False, f"Missing keys: {missing_keys}")
                        return False
                
                self.log_test("Get Audio Library", True, f"Successfully returned {total_items} audio items in 3 categories")
                return True
            else:
                self.log_test("Get Audio Library", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Audio Library", False, f"Exception: {str(e)}")
            return False
    
    def test_get_audio_library_filtered(self):
        """Test GET /api/music/library?category=nature - Category filtering"""
        try:
            response = requests.get(f"{self.base_url}/music/library?category=nature")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should still return all categories but only nature should have items
                if "nature" not in data or "white_noise" not in data or "binaural_beats" not in data:
                    self.log_test("Get Filtered Audio Library - Structure", False, "Missing category keys")
                    return False
                
                # Nature should have 5 items
                if len(data["nature"]) != 5:
                    self.log_test("Get Filtered Audio Library - Nature Count", False, f"Expected 5 nature sounds, got {len(data['nature'])}")
                    return False
                
                # Other categories should be empty when filtering by nature
                if len(data["white_noise"]) != 0 or len(data["binaural_beats"]) != 0:
                    self.log_test("Get Filtered Audio Library - Other Categories", False, "Other categories should be empty when filtering")
                    return False
                
                self.log_test("Get Filtered Audio Library", True, f"Successfully filtered to {len(data['nature'])} nature sounds")
                return True
            else:
                self.log_test("Get Filtered Audio Library", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Filtered Audio Library", False, f"Exception: {str(e)}")
            return False
    
    # Phase 2: Spotify OAuth Tests
    def test_spotify_login_endpoint(self):
        """Test GET /api/music/spotify/login - Should return auth_url"""
        try:
            response = requests.get(f"{self.base_url}/music/spotify/login")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "auth_url" not in data:
                    self.log_test("Spotify Login - Structure", False, "Missing 'auth_url' key")
                    return False
                
                # Check if auth_url is a valid URL
                auth_url = data["auth_url"]
                if not auth_url.startswith("https://accounts.spotify.com/authorize"):
                    self.log_test("Spotify Login - URL Format", False, f"Invalid auth URL format: {auth_url}")
                    return False
                
                # Check if URL contains required parameters
                required_params = ["client_id", "response_type", "redirect_uri", "scope"]
                for param in required_params:
                    if param not in auth_url:
                        self.log_test("Spotify Login - URL Parameters", False, f"Missing parameter: {param}")
                        return False
                
                self.log_test("Spotify Login", True, "Successfully generated Spotify auth URL")
                return True
            else:
                self.log_test("Spotify Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Spotify Login", False, f"Exception: {str(e)}")
            return False
    
    def test_spotify_callback_endpoint_exists(self):
        """Test that Spotify callback endpoint exists (can't test full flow without auth)"""
        try:
            # Test with invalid code to verify endpoint exists
            response = requests.get(f"{self.base_url}/music/spotify/callback?code=invalid_test_code")
            
            # Should return 500 (error processing invalid code) not 404 (endpoint not found)
            if response.status_code in [500, 400]:
                self.log_test("Spotify Callback Endpoint", True, "Endpoint exists and processes requests")
                return True
            elif response.status_code == 404:
                self.log_test("Spotify Callback Endpoint", False, "Endpoint not found")
                return False
            else:
                self.log_test("Spotify Callback Endpoint", True, f"Endpoint exists (status: {response.status_code})")
                return True
        except Exception as e:
            self.log_test("Spotify Callback Endpoint", False, f"Exception: {str(e)}")
            return False
    
    # Phase 3: AI Recommendations Tests
    def test_music_recommendations_new_user(self):
        """Test GET /api/music/recommendations/{user_id} - New user with no mood logs"""
        try:
            if not self.test_user_id:
                self.log_test("Music Recommendations (New User) - No User", False, "No test user available")
                return False
            
            response = requests.get(f"{self.base_url}/music/recommendations/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["mood_analysis", "builtin_recommendations", "spotify_genres", "spotify_search_suggestions"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Music Recommendations (New User) - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should have default recommendations for new users
                if "Welcome" not in data["mood_analysis"]:
                    self.log_test("Music Recommendations (New User) - Welcome Message", False, "Should contain welcome message for new users")
                    return False
                
                # Should have some builtin recommendations
                if not isinstance(data["builtin_recommendations"], list) or len(data["builtin_recommendations"]) == 0:
                    self.log_test("Music Recommendations (New User) - Builtin Recs", False, "Should have builtin recommendations")
                    return False
                
                # Check builtin recommendation structure
                first_rec = data["builtin_recommendations"][0]
                rec_keys = ["id", "title", "category", "reason"]
                missing_rec_keys = [key for key in rec_keys if key not in first_rec]
                
                if missing_rec_keys:
                    self.log_test("Music Recommendations (New User) - Rec Structure", False, f"Missing recommendation keys: {missing_rec_keys}")
                    return False
                
                self.log_test("Music Recommendations (New User)", True, f"Successfully returned recommendations for new user")
                return True
            else:
                self.log_test("Music Recommendations (New User)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Music Recommendations (New User)", False, f"Exception: {str(e)}")
            return False
    
    def test_music_recommendations_with_mood_logs(self):
        """Test GET /api/music/recommendations/{user_id} - User with mood logs"""
        try:
            if not self.test_user_id:
                self.log_test("Music Recommendations (With Mood) - No User", False, "No test user available")
                return False
            
            # Create some mood logs first
            mood_logs = [
                "I'm feeling really stressed and anxious about work deadlines",
                "Having trouble sleeping, my mind keeps racing with worries",
                "Feeling overwhelmed and need something to help me focus"
            ]
            
            for mood_text in mood_logs:
                self.create_mood_log_for_recommendations(mood_text)
                time.sleep(0.2)
            
            # Wait for processing
            time.sleep(1)
            
            response = requests.get(f"{self.base_url}/music/recommendations/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["mood_analysis", "builtin_recommendations", "spotify_genres", "spotify_search_suggestions"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Music Recommendations (With Mood) - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should have personalized mood analysis (not welcome message)
                if "Welcome" in data["mood_analysis"]:
                    self.log_test("Music Recommendations (With Mood) - Personalized", False, "Should have personalized analysis, not welcome message")
                    return False
                
                # Should have builtin recommendations
                if not isinstance(data["builtin_recommendations"], list) or len(data["builtin_recommendations"]) == 0:
                    self.log_test("Music Recommendations (With Mood) - Builtin Recs", False, "Should have builtin recommendations")
                    return False
                
                # Should have Spotify genres
                if not isinstance(data["spotify_genres"], list) or len(data["spotify_genres"]) == 0:
                    self.log_test("Music Recommendations (With Mood) - Spotify Genres", False, "Should have Spotify genres")
                    return False
                
                # Should have search suggestions
                if not isinstance(data["spotify_search_suggestions"], list) or len(data["spotify_search_suggestions"]) == 0:
                    self.log_test("Music Recommendations (With Mood) - Search Suggestions", False, "Should have search suggestions")
                    return False
                
                self.log_test("Music Recommendations (With Mood)", True, f"Successfully returned personalized recommendations")
                return True
            else:
                self.log_test("Music Recommendations (With Mood)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Music Recommendations (With Mood)", False, f"Exception: {str(e)}")
            return False
    
    # Phase 4: Audio Journaling Tests
    def test_create_audio_journal(self):
        """Test POST /api/music/journal/create - Create audio journal entry"""
        try:
            if not self.test_user_id:
                self.log_test("Create Audio Journal - No User", False, "No test user available")
                return False
            
            journal_data = {
                "user_id": self.test_user_id,
                "mood": "calm",
                "journal_text": "Today I listened to ocean waves while reflecting on my day. It helped me feel more centered and peaceful.",
                "voice_recording_url": "https://example.com/voice_recording.mp3",
                "music_played": "Ocean Waves",
                "music_source": "builtin"
            }
            
            response = requests.post(f"{self.base_url}/music/journal/create", json=journal_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["message", "journal_id", "stars_earned"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Create Audio Journal - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should award 3 wellness stars
                if data["stars_earned"] != 3:
                    self.log_test("Create Audio Journal - Stars", False, f"Expected 3 stars, got {data['stars_earned']}")
                    return False
                
                # Store journal ID for later tests
                self.journal_id = data["journal_id"]
                
                self.log_test("Create Audio Journal", True, f"Successfully created journal, earned {data['stars_earned']} stars")
                return True
            else:
                self.log_test("Create Audio Journal", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Audio Journal", False, f"Exception: {str(e)}")
            return False
    
    def test_create_audio_journal_minimal(self):
        """Test POST /api/music/journal/create - With minimal required fields"""
        try:
            if not self.test_user_id:
                self.log_test("Create Audio Journal (Minimal) - No User", False, "No test user available")
                return False
            
            # Test with only required fields
            journal_data = {
                "user_id": self.test_user_id,
                "mood": "reflective",
                "journal_text": "A simple journal entry without voice recording or music context."
            }
            
            response = requests.post(f"{self.base_url}/music/journal/create", json=journal_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should still award 3 stars
                if data["stars_earned"] != 3:
                    self.log_test("Create Audio Journal (Minimal) - Stars", False, f"Expected 3 stars, got {data['stars_earned']}")
                    return False
                
                self.log_test("Create Audio Journal (Minimal)", True, "Successfully created minimal journal entry")
                return True
            else:
                self.log_test("Create Audio Journal (Minimal)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Audio Journal (Minimal)", False, f"Exception: {str(e)}")
            return False
    
    def test_get_user_audio_journals(self):
        """Test GET /api/music/journal/{user_id} - Get user's journals"""
        try:
            if not self.test_user_id:
                self.log_test("Get Audio Journals - No User", False, "No test user available")
                return False
            
            response = requests.get(f"{self.base_url}/music/journal/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "journals" not in data:
                    self.log_test("Get Audio Journals - Structure", False, "Missing 'journals' key")
                    return False
                
                journals = data["journals"]
                
                # Should have at least 2 journals from previous tests
                if len(journals) < 2:
                    self.log_test("Get Audio Journals - Count", False, f"Expected at least 2 journals, got {len(journals)}")
                    return False
                
                # Check first journal structure
                first_journal = journals[0]
                required_keys = ["id", "user_id", "mood", "journal_text", "timestamp"]
                missing_keys = [key for key in required_keys if key not in first_journal]
                
                if missing_keys:
                    self.log_test("Get Audio Journals - Journal Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify user_id matches
                if first_journal["user_id"] != self.test_user_id:
                    self.log_test("Get Audio Journals - User ID", False, "Journal user_id doesn't match")
                    return False
                
                self.log_test("Get Audio Journals", True, f"Successfully retrieved {len(journals)} journal entries")
                return True
            else:
                self.log_test("Get Audio Journals", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Audio Journals", False, f"Exception: {str(e)}")
            return False
    
    def test_get_specific_audio_journal(self):
        """Test GET /api/music/journal/entry/{journal_id} - Get specific journal"""
        try:
            if not self.journal_id:
                self.log_test("Get Specific Journal - No Journal ID", False, "No journal ID available")
                return False
            
            response = requests.get(f"{self.base_url}/music/journal/entry/{self.journal_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check structure
                required_keys = ["id", "user_id", "mood", "journal_text", "timestamp"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Get Specific Journal - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify it's the correct journal
                if data["id"] != self.journal_id:
                    self.log_test("Get Specific Journal - ID Match", False, "Journal ID doesn't match")
                    return False
                
                if data["user_id"] != self.test_user_id:
                    self.log_test("Get Specific Journal - User ID", False, "User ID doesn't match")
                    return False
                
                self.log_test("Get Specific Journal", True, f"Successfully retrieved specific journal: {data['mood']}")
                return True
            else:
                self.log_test("Get Specific Journal", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Specific Journal", False, f"Exception: {str(e)}")
            return False
    
    # Phase 5: Music History Tests
    def test_save_music_history(self):
        """Test POST /api/music/history/save - Save listening history"""
        try:
            if not self.test_user_id:
                self.log_test("Save Music History - No User", False, "No test user available")
                return False
            
            history_data = {
                "user_id": self.test_user_id,
                "track_name": "Ocean Waves",
                "artist": "Nature Sounds",
                "source": "builtin",
                "mood_context": "relaxation",
                "duration_played": 1800
            }
            
            response = requests.post(f"{self.base_url}/music/history/save", json=history_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "message" not in data:
                    self.log_test("Save Music History - Structure", False, "Missing 'message' key")
                    return False
                
                if "successfully" not in data["message"].lower():
                    self.log_test("Save Music History - Success Message", False, f"Unexpected message: {data['message']}")
                    return False
                
                self.log_test("Save Music History", True, "Successfully saved music history")
                return True
            else:
                self.log_test("Save Music History", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Save Music History", False, f"Exception: {str(e)}")
            return False
    
    def test_save_spotify_music_history(self):
        """Test POST /api/music/history/save - Save Spotify track"""
        try:
            if not self.test_user_id:
                self.log_test("Save Spotify History - No User", False, "No test user available")
                return False
            
            history_data = {
                "user_id": self.test_user_id,
                "track_name": "Weightless",
                "artist": "Marconi Union",
                "source": "spotify",
                "mood_context": "anxiety relief",
                "duration_played": 480
            }
            
            response = requests.post(f"{self.base_url}/music/history/save", json=history_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "successfully" not in data["message"].lower():
                    self.log_test("Save Spotify History - Success Message", False, f"Unexpected message: {data['message']}")
                    return False
                
                self.log_test("Save Spotify History", True, "Successfully saved Spotify history")
                return True
            else:
                self.log_test("Save Spotify History", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Save Spotify History", False, f"Exception: {str(e)}")
            return False
    
    def test_get_music_history(self):
        """Test GET /api/music/history/{user_id} - Get listening history"""
        try:
            if not self.test_user_id:
                self.log_test("Get Music History - No User", False, "No test user available")
                return False
            
            response = requests.get(f"{self.base_url}/music/history/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "history" not in data:
                    self.log_test("Get Music History - Structure", False, "Missing 'history' key")
                    return False
                
                history = data["history"]
                
                # Should have at least 2 history entries from previous tests
                if len(history) < 2:
                    self.log_test("Get Music History - Count", False, f"Expected at least 2 history entries, got {len(history)}")
                    return False
                
                # Check first history entry structure
                first_entry = history[0]
                required_keys = ["id", "user_id", "track_name", "artist", "source", "timestamp"]
                missing_keys = [key for key in required_keys if key not in first_entry]
                
                if missing_keys:
                    self.log_test("Get Music History - Entry Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify user_id matches
                if first_entry["user_id"] != self.test_user_id:
                    self.log_test("Get Music History - User ID", False, "History user_id doesn't match")
                    return False
                
                # Check that we have both builtin and spotify sources
                sources = set(entry["source"] for entry in history)
                if "builtin" not in sources or "spotify" not in sources:
                    self.log_test("Get Music History - Sources", False, f"Expected both builtin and spotify sources, got: {sources}")
                    return False
                
                self.log_test("Get Music History", True, f"Successfully retrieved {len(history)} history entries")
                return True
            else:
                self.log_test("Get Music History", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Music History", False, f"Exception: {str(e)}")
            return False
    
    def test_music_endpoints_availability(self):
        """Test if all music therapy endpoints are available"""
        try:
            endpoints = [
                "/music/library",
                "/music/spotify/login",
                f"/music/recommendations/{str(uuid.uuid4())}",
                f"/music/journal/{str(uuid.uuid4())}",
                f"/music/history/{str(uuid.uuid4())}"
            ]
            
            all_available = True
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code not in [200, 404, 500]:  # 500 is acceptable for some endpoints without proper auth
                    self.log_test(f"Endpoint {endpoint}", False, f"Status: {response.status_code}")
                    all_available = False
            
            if all_available:
                self.log_test("Music Endpoints Availability", True, "All endpoints are accessible")
                return True
            else:
                self.log_test("Music Endpoints Availability", False, "Some endpoints are not accessible")
                return False
        except Exception as e:
            self.log_test("Music Endpoints Availability", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all music therapy tests"""
        print("=" * 60)
        print("🎵 MOODMESH MUSIC THERAPY BACKEND TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test endpoint availability first
        results["endpoints_availability"] = self.test_music_endpoints_availability()
        
        # Phase 1: Built-in Audio Library (No auth required)
        results["builtin_audio_library"] = self.test_get_builtin_audio_library()
        results["audio_library_filtering"] = self.test_get_audio_library_filtered()
        
        # Phase 2: Spotify OAuth Flow
        results["spotify_login"] = self.test_spotify_login_endpoint()
        results["spotify_callback_exists"] = self.test_spotify_callback_endpoint_exists()
        
        # Register test user for user-specific tests
        if self.register_test_user():
            results["user_registration"] = True
            
            # Phase 3: AI Recommendations
            results["recommendations_new_user"] = self.test_music_recommendations_new_user()
            results["recommendations_with_mood"] = self.test_music_recommendations_with_mood_logs()
            
            # Phase 4: Audio Journaling
            results["create_audio_journal"] = self.test_create_audio_journal()
            results["create_journal_minimal"] = self.test_create_audio_journal_minimal()
            results["get_user_journals"] = self.test_get_user_audio_journals()
            results["get_specific_journal"] = self.test_get_specific_audio_journal()
            
            # Phase 5: Music History
            results["save_music_history"] = self.test_save_music_history()
            results["save_spotify_history"] = self.test_save_spotify_music_history()
            results["get_music_history"] = self.test_get_music_history()
        else:
            results["user_registration"] = False
            results["recommendations_new_user"] = False
            results["recommendations_with_mood"] = False
            results["create_audio_journal"] = False
            results["create_journal_minimal"] = False
            results["get_user_journals"] = False
            results["get_specific_journal"] = False
            results["save_music_history"] = False
            results["save_spotify_history"] = False
            results["get_music_history"] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 MUSIC THERAPY TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All music therapy tests PASSED!")
            return True
        else:
            print("⚠️  Some music therapy tests FAILED!")
            return False

class MoodMeshResourceLibraryTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = "test_user_123"
        self.test_username = f"resource_test_user_{int(time.time())}"
        self.test_password = "testpass123"
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def register_test_user(self):
        """Register a test user for resource testing"""
        try:
            response = requests.post(f"{self.base_url}/auth/register", json={
                "username": self.test_username,
                "password": self.test_password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_id = data["user_id"]
                self.log_test("Resource User Registration", True, f"Created user: {self.test_username}")
                return True
            else:
                self.log_test("Resource User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Resource User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_get_all_resources(self):
        """Test GET /api/resources - Get all resources"""
        try:
            response = requests.get(f"{self.base_url}/resources")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should return a list
                if not isinstance(data, list):
                    self.log_test("Get All Resources - Type", False, "Response should be a list")
                    return False
                
                # Should return 13 resources as per seeded data
                if len(data) != 13:
                    self.log_test("Get All Resources - Count", False, f"Expected 13 resources, got {len(data)}")
                    return False
                
                # Check first resource structure
                if data:
                    first_resource = data[0]
                    required_keys = ["id", "title", "category", "description", "content", "tags", "views", "bookmarks"]
                    missing_keys = [key for key in required_keys if key not in first_resource]
                    
                    if missing_keys:
                        self.log_test("Get All Resources - Structure", False, f"Missing keys: {missing_keys}")
                        return False
                
                self.log_test("Get All Resources", True, f"Successfully returned {len(data)} resources")
                return True
            else:
                self.log_test("Get All Resources", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get All Resources", False, f"Exception: {str(e)}")
            return False
    
    def test_get_resources_with_filters(self):
        """Test GET /api/resources with various filters"""
        try:
            # Test category filter: conditions
            response = requests.get(f"{self.base_url}/resources?category=conditions")
            if response.status_code == 200:
                data = response.json()
                for resource in data:
                    if resource["category"] != "conditions":
                        self.log_test("Filter by Category (conditions)", False, f"Found non-conditions resource: {resource['category']}")
                        return False
                self.log_test("Filter by Category (conditions)", True, f"Found {len(data)} conditions resources")
            else:
                self.log_test("Filter by Category (conditions)", False, f"Status: {response.status_code}")
                return False
            
            # Test category filter: techniques
            response = requests.get(f"{self.base_url}/resources?category=techniques")
            if response.status_code == 200:
                data = response.json()
                for resource in data:
                    if resource["category"] != "techniques":
                        self.log_test("Filter by Category (techniques)", False, f"Found non-techniques resource: {resource['category']}")
                        return False
                self.log_test("Filter by Category (techniques)", True, f"Found {len(data)} techniques resources")
            else:
                self.log_test("Filter by Category (techniques)", False, f"Status: {response.status_code}")
                return False
            
            # Test category filter: videos
            response = requests.get(f"{self.base_url}/resources?category=videos")
            if response.status_code == 200:
                data = response.json()
                for resource in data:
                    if resource["category"] != "videos":
                        self.log_test("Filter by Category (videos)", False, f"Found non-videos resource: {resource['category']}")
                        return False
                self.log_test("Filter by Category (videos)", True, f"Found {len(data)} videos resources")
            else:
                self.log_test("Filter by Category (videos)", False, f"Status: {response.status_code}")
                return False
            
            # Test subcategory filter: anxiety
            response = requests.get(f"{self.base_url}/resources?subcategory=anxiety")
            if response.status_code == 200:
                data = response.json()
                for resource in data:
                    if resource.get("subcategory") != "anxiety":
                        self.log_test("Filter by Subcategory (anxiety)", False, f"Found non-anxiety resource: {resource.get('subcategory')}")
                        return False
                self.log_test("Filter by Subcategory (anxiety)", True, f"Found {len(data)} anxiety resources")
            else:
                self.log_test("Filter by Subcategory (anxiety)", False, f"Status: {response.status_code}")
                return False
            
            # Test content_type filter: article
            response = requests.get(f"{self.base_url}/resources?content_type=article")
            if response.status_code == 200:
                data = response.json()
                for resource in data:
                    if resource["content_type"] != "article":
                        self.log_test("Filter by Content Type (article)", False, f"Found non-article resource: {resource['content_type']}")
                        return False
                self.log_test("Filter by Content Type (article)", True, f"Found {len(data)} article resources")
            else:
                self.log_test("Filter by Content Type (article)", False, f"Status: {response.status_code}")
                return False
            
            # Test search filter: depression
            response = requests.get(f"{self.base_url}/resources?search=depression")
            if response.status_code == 200:
                data = response.json()
                # Should find resources containing "depression" in title, description, or tags
                if len(data) == 0:
                    self.log_test("Search Filter (depression)", False, "No resources found for 'depression' search")
                    return False
                self.log_test("Search Filter (depression)", True, f"Found {len(data)} resources matching 'depression'")
            else:
                self.log_test("Search Filter (depression)", False, f"Status: {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_test("Resource Filters", False, f"Exception: {str(e)}")
            return False
    
    def test_get_single_resource(self):
        """Test GET /api/resources/{resource_id} - Get single resource"""
        try:
            # First get all resources to find a valid ID
            response = requests.get(f"{self.base_url}/resources")
            if response.status_code != 200:
                self.log_test("Get Single Resource - Setup", False, "Failed to get resources list")
                return False
            
            resources = response.json()
            if not resources:
                self.log_test("Get Single Resource - Setup", False, "No resources available")
                return False
            
            # Test with valid resource ID
            test_resource_id = resources[0]["id"]
            initial_views = resources[0].get("views", 0)
            
            response = requests.get(f"{self.base_url}/resources/{test_resource_id}")
            if response.status_code == 200:
                data = response.json()
                
                # Check structure
                required_keys = ["id", "title", "category", "description", "content", "views"]
                missing_keys = [key for key in required_keys if key not in data]
                if missing_keys:
                    self.log_test("Get Single Resource - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Check if view count incremented
                if data["views"] != initial_views + 1:
                    self.log_test("Get Single Resource - View Count", False, f"Expected views {initial_views + 1}, got {data['views']}")
                    return False
                
                self.log_test("Get Single Resource (Valid ID)", True, f"Successfully retrieved resource: {data['title']}")
            else:
                self.log_test("Get Single Resource (Valid ID)", False, f"Status: {response.status_code}")
                return False
            
            # Test with invalid resource ID
            response = requests.get(f"{self.base_url}/resources/invalid-resource-id")
            if response.status_code == 404:
                self.log_test("Get Single Resource (Invalid ID)", True, "Correctly returns 404 for invalid ID")
            else:
                self.log_test("Get Single Resource (Invalid ID)", False, f"Expected 404, got {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_test("Get Single Resource", False, f"Exception: {str(e)}")
            return False
    
    def test_categories_summary(self):
        """Test GET /api/resources/categories/summary - Get category counts"""
        try:
            response = requests.get(f"{self.base_url}/resources/categories/summary")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check structure
                expected_categories = ["conditions", "techniques", "videos", "reading", "myths"]
                missing_categories = [cat for cat in expected_categories if cat not in data]
                if missing_categories:
                    self.log_test("Categories Summary - Structure", False, f"Missing categories: {missing_categories}")
                    return False
                
                # Check that counts are non-negative integers
                for category, count in data.items():
                    if not isinstance(count, int) or count < 0:
                        self.log_test("Categories Summary - Count Type", False, f"Invalid count for {category}: {count}")
                        return False
                
                # Total should be 13 (as per seeded data)
                total_count = sum(data.values())
                if total_count != 13:
                    self.log_test("Categories Summary - Total Count", False, f"Expected total 13, got {total_count}")
                    return False
                
                self.log_test("Categories Summary", True, f"Successfully returned category counts: {data}")
                return True
            else:
                self.log_test("Categories Summary", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Categories Summary", False, f"Exception: {str(e)}")
            return False
    
    def test_bookmark_resource(self):
        """Test POST /api/resources/bookmark - Bookmark a resource"""
        try:
            # First get a resource to bookmark
            response = requests.get(f"{self.base_url}/resources")
            if response.status_code != 200:
                self.log_test("Bookmark Resource - Setup", False, "Failed to get resources")
                return False
            
            resources = response.json()
            if not resources:
                self.log_test("Bookmark Resource - Setup", False, "No resources available")
                return False
            
            test_resource_id = resources[0]["id"]
            initial_bookmarks = resources[0].get("bookmarks", 0)
            
            # Test creating a bookmark
            bookmark_data = {
                "user_id": self.test_user_id,
                "resource_id": test_resource_id
            }
            
            response = requests.post(f"{self.base_url}/resources/bookmark", json=bookmark_data)
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "message" not in data or "success" not in data:
                    self.log_test("Bookmark Resource - Response Structure", False, "Missing message or success field")
                    return False
                
                if not data["success"]:
                    self.log_test("Bookmark Resource - Success Flag", False, "Success flag is False")
                    return False
                
                self.log_test("Bookmark Resource (First Time)", True, f"Successfully bookmarked resource")
            else:
                self.log_test("Bookmark Resource (First Time)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # Test bookmarking the same resource again (should return "Already bookmarked")
            response = requests.post(f"{self.base_url}/resources/bookmark", json=bookmark_data)
            if response.status_code == 200:
                data = response.json()
                if "Already bookmarked" in data.get("message", ""):
                    self.log_test("Bookmark Resource (Duplicate)", True, "Correctly handles duplicate bookmark")
                else:
                    self.log_test("Bookmark Resource (Duplicate)", False, f"Unexpected message: {data.get('message')}")
                    return False
            else:
                self.log_test("Bookmark Resource (Duplicate)", False, f"Status: {response.status_code}")
                return False
            
            # Verify bookmark count incremented on the resource
            response = requests.get(f"{self.base_url}/resources/{test_resource_id}")
            if response.status_code == 200:
                resource_data = response.json()
                if resource_data["bookmarks"] == initial_bookmarks + 1:
                    self.log_test("Bookmark Count Increment", True, f"Bookmark count correctly incremented to {resource_data['bookmarks']}")
                else:
                    self.log_test("Bookmark Count Increment", False, f"Expected {initial_bookmarks + 1}, got {resource_data['bookmarks']}")
                    return False
            else:
                self.log_test("Bookmark Count Increment", False, "Failed to verify bookmark count")
                return False
            
            return True
        except Exception as e:
            self.log_test("Bookmark Resource", False, f"Exception: {str(e)}")
            return False
    
    def test_get_user_bookmarks(self):
        """Test GET /api/resources/bookmarks/{user_id} - Get user's bookmarks"""
        try:
            # Test with user who has bookmarks (from previous test)
            response = requests.get(f"{self.base_url}/resources/bookmarks/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should return a list
                if not isinstance(data, list):
                    self.log_test("Get User Bookmarks - Type", False, "Response should be a list")
                    return False
                
                # Should have at least 1 bookmark from previous test
                if len(data) == 0:
                    self.log_test("Get User Bookmarks - Count", False, "Expected at least 1 bookmark")
                    return False
                
                # Check first bookmark structure (should be full resource details)
                first_bookmark = data[0]
                required_keys = ["id", "title", "category", "description", "content"]
                missing_keys = [key for key in required_keys if key not in first_bookmark]
                if missing_keys:
                    self.log_test("Get User Bookmarks - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                self.log_test("Get User Bookmarks (With Data)", True, f"Successfully returned {len(data)} bookmarked resources")
            else:
                self.log_test("Get User Bookmarks (With Data)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # Test with user who has no bookmarks
            empty_user_id = "user_with_no_bookmarks"
            response = requests.get(f"{self.base_url}/resources/bookmarks/{empty_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) == 0:
                    self.log_test("Get User Bookmarks (Empty)", True, "Correctly returns empty array for user with no bookmarks")
                else:
                    self.log_test("Get User Bookmarks (Empty)", False, f"Expected empty array, got: {data}")
                    return False
            else:
                self.log_test("Get User Bookmarks (Empty)", False, f"Status: {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_test("Get User Bookmarks", False, f"Exception: {str(e)}")
            return False
    
    def test_remove_bookmark(self):
        """Test DELETE /api/resources/bookmark/{user_id}/{resource_id} - Remove bookmark"""
        try:
            # First get user's bookmarks to find one to remove
            response = requests.get(f"{self.base_url}/resources/bookmarks/{self.test_user_id}")
            if response.status_code != 200:
                self.log_test("Remove Bookmark - Setup", False, "Failed to get user bookmarks")
                return False
            
            bookmarks = response.json()
            if not bookmarks:
                self.log_test("Remove Bookmark - Setup", False, "No bookmarks to remove")
                return False
            
            test_resource_id = bookmarks[0]["id"]
            initial_bookmarks = bookmarks[0].get("bookmarks", 0)
            
            # Test removing an existing bookmark
            response = requests.delete(f"{self.base_url}/resources/bookmark/{self.test_user_id}/{test_resource_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "message" not in data or "success" not in data:
                    self.log_test("Remove Bookmark - Response Structure", False, "Missing message or success field")
                    return False
                
                if not data["success"]:
                    self.log_test("Remove Bookmark - Success Flag", False, "Success flag is False")
                    return False
                
                self.log_test("Remove Bookmark (Existing)", True, "Successfully removed bookmark")
            else:
                self.log_test("Remove Bookmark (Existing)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # Verify bookmark count decremented on the resource
            response = requests.get(f"{self.base_url}/resources/{test_resource_id}")
            if response.status_code == 200:
                resource_data = response.json()
                if resource_data["bookmarks"] == initial_bookmarks - 1:
                    self.log_test("Bookmark Count Decrement", True, f"Bookmark count correctly decremented to {resource_data['bookmarks']}")
                else:
                    self.log_test("Bookmark Count Decrement", False, f"Expected {initial_bookmarks - 1}, got {resource_data['bookmarks']}")
                    return False
            else:
                self.log_test("Bookmark Count Decrement", False, "Failed to verify bookmark count")
                return False
            
            # Test removing non-existent bookmark (should return 404)
            response = requests.delete(f"{self.base_url}/resources/bookmark/{self.test_user_id}/{test_resource_id}")
            
            if response.status_code == 404:
                self.log_test("Remove Bookmark (Non-existent)", True, "Correctly returns 404 for non-existent bookmark")
            else:
                self.log_test("Remove Bookmark (Non-existent)", False, f"Expected 404, got {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_test("Remove Bookmark", False, f"Exception: {str(e)}")
            return False
    
    def test_resource_endpoints_availability(self):
        """Test if all resource endpoints are available"""
        try:
            endpoints = [
                "/resources",
                "/resources/categories/summary",
                f"/resources/bookmarks/{str(uuid.uuid4())}"
            ]
            
            all_available = True
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code not in [200, 404]:
                    self.log_test(f"Endpoint {endpoint}", False, f"Status: {response.status_code}")
                    all_available = False
            
            if all_available:
                self.log_test("Resource Endpoints Availability", True, "All endpoints are accessible")
                return True
            else:
                self.log_test("Resource Endpoints Availability", False, "Some endpoints are not accessible")
                return False
        except Exception as e:
            self.log_test("Resource Endpoints Availability", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all resource library tests"""
        print("=" * 60)
        print("📚 MOODMESH RESOURCE LIBRARY BACKEND TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test endpoint availability first
        results["endpoints_availability"] = self.test_resource_endpoints_availability()
        
        # Test basic resource retrieval
        results["get_all_resources"] = self.test_get_all_resources()
        results["resource_filters"] = self.test_get_resources_with_filters()
        results["single_resource"] = self.test_get_single_resource()
        results["categories_summary"] = self.test_categories_summary()
        
        # Register test user for bookmark tests
        if self.register_test_user():
            results["user_registration"] = True
            
            # Test bookmark functionality
            results["bookmark_resource"] = self.test_bookmark_resource()
            results["get_user_bookmarks"] = self.test_get_user_bookmarks()
            results["remove_bookmark"] = self.test_remove_bookmark()
        else:
            results["user_registration"] = False
            results["bookmark_resource"] = False
            results["get_user_bookmarks"] = False
            results["remove_bookmark"] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 RESOURCE LIBRARY TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All resource library tests PASSED!")
            return True
        else:
            print("⚠️  Some resource library tests FAILED!")
            return False

class MoodMeshAITherapistTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = "test-therapist-user-001"
        self.session_id = None
        self.checkin_id = None
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
    
    def create_mood_log(self, mood_text):
        """Create a mood log for testing mood context"""
        try:
            response = requests.post(f"{self.base_url}/mood/log", json={
                "user_id": self.test_user_id,
                "mood_text": mood_text
            })
            return response.status_code == 200
        except:
            return False
    
    def test_enhanced_chat_first_message(self):
        """Test POST /api/therapist/chat - First message (should create new session)"""
        try:
            chat_data = {
                "user_id": self.test_user_id,
                "message": "Hi, I'm feeling really anxious about my upcoming job interview. I can't stop worrying about it."
            }
            
            response = requests.post(f"{self.base_url}/therapist/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["therapist_response", "session_id", "suggested_techniques", "mood_context"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Enhanced Chat - First Message Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should create a new session
                if not data["session_id"]:
                    self.log_test("Enhanced Chat - Session Creation", False, "No session_id returned")
                    return False
                
                # Store session ID for future tests
                self.session_id = data["session_id"]
                
                # Should have therapist response
                if not data["therapist_response"] or len(data["therapist_response"]) < 10:
                    self.log_test("Enhanced Chat - Response Quality", False, "Therapist response too short or empty")
                    return False
                
                # Should suggest techniques for anxiety
                if not isinstance(data["suggested_techniques"], list):
                    self.log_test("Enhanced Chat - Techniques Structure", False, "suggested_techniques should be a list")
                    return False
                
                self.log_test("Enhanced Chat - First Message", True, f"Session created: {data['session_id'][:8]}..., {len(data['suggested_techniques'])} techniques suggested")
                return True
            else:
                self.log_test("Enhanced Chat - First Message", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Enhanced Chat - First Message", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_chat_anxiety_keywords(self):
        """Test chat with anxiety keywords to trigger mindfulness techniques"""
        try:
            if not self.session_id:
                self.log_test("Anxiety Keywords Test - No Session", False, "No session available")
                return False
            
            chat_data = {
                "user_id": self.test_user_id,
                "message": "I'm having panic attacks and my mind is racing with worried thoughts. I feel so anxious and stressed.",
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/therapist/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should suggest mindfulness techniques for anxiety
                mindfulness_found = False
                for technique in data["suggested_techniques"]:
                    if ("grounding" in technique.get("technique_name", "").lower() or 
                        "mindfulness" in technique.get("technique_type", "").lower()):
                        mindfulness_found = True
                        
                        # Check technique structure
                        if "steps" not in technique or not isinstance(technique["steps"], list):
                            self.log_test("Anxiety Keywords - Technique Steps", False, "Technique missing steps")
                            return False
                        break
                
                if not mindfulness_found:
                    self.log_test("Anxiety Keywords - Mindfulness Trigger", False, "No mindfulness technique suggested for anxiety")
                    return False
                
                self.log_test("Enhanced Chat - Anxiety Keywords", True, "Mindfulness technique correctly suggested for anxiety")
                return True
            else:
                self.log_test("Enhanced Chat - Anxiety Keywords", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Chat - Anxiety Keywords", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_chat_cbt_trigger(self):
        """Test chat with thought patterns to trigger CBT techniques"""
        try:
            if not self.session_id:
                self.log_test("CBT Trigger Test - No Session", False, "No session available")
                return False
            
            chat_data = {
                "user_id": self.test_user_id,
                "message": "I always think the worst will happen. I believe I'm never good enough and I should be perfect at everything.",
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/therapist/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should suggest CBT techniques for thought patterns
                cbt_found = False
                for technique in data["suggested_techniques"]:
                    if ("cognitive" in technique.get("technique_name", "").lower() or 
                        "cbt" in technique.get("technique_type", "").lower()):
                        cbt_found = True
                        
                        # Verify CBT technique has proper structure
                        required_keys = ["technique_name", "technique_type", "description", "steps"]
                        missing_keys = [key for key in required_keys if key not in technique]
                        if missing_keys:
                            self.log_test("CBT Trigger - Technique Structure", False, f"Missing keys: {missing_keys}")
                            return False
                        break
                
                if not cbt_found:
                    self.log_test("CBT Trigger - CBT Technique", False, "No CBT technique suggested for thought patterns")
                    return False
                
                self.log_test("Enhanced Chat - CBT Trigger", True, "CBT technique correctly suggested for thought patterns")
                return True
            else:
                self.log_test("Enhanced Chat - CBT Trigger", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Chat - CBT Trigger", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_chat_dbt_trigger(self):
        """Test chat with overwhelm to trigger DBT techniques"""
        try:
            if not self.session_id:
                self.log_test("DBT Trigger Test - No Session", False, "No session available")
                return False
            
            chat_data = {
                "user_id": self.test_user_id,
                "message": "I feel completely overwhelmed and out of control. The emotions are too intense and I can't handle it anymore.",
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/therapist/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should suggest DBT techniques for overwhelm
                dbt_found = False
                for technique in data["suggested_techniques"]:
                    if ("tipp" in technique.get("technique_name", "").lower() or 
                        "dbt" in technique.get("technique_type", "").lower()):
                        dbt_found = True
                        
                        # Verify DBT technique mentions distress tolerance
                        if "distress" not in technique.get("description", "").lower():
                            self.log_test("DBT Trigger - Distress Tolerance", False, "DBT technique should mention distress tolerance")
                            return False
                        break
                
                if not dbt_found:
                    self.log_test("DBT Trigger - DBT Technique", False, "No DBT technique suggested for overwhelm")
                    return False
                
                self.log_test("Enhanced Chat - DBT Trigger", True, "DBT technique correctly suggested for overwhelm")
                return True
            else:
                self.log_test("Enhanced Chat - DBT Trigger", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Chat - DBT Trigger", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_crisis_detection(self):
        """Test enhanced crisis detection with expanded keywords"""
        try:
            if not self.session_id:
                self.log_test("Crisis Detection Test - No Session", False, "No session available")
                return False
            
            chat_data = {
                "user_id": self.test_user_id,
                "message": "I feel hopeless and worthless. I can't go on like this anymore. Nothing matters.",
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/therapist/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should detect crisis
                if not data.get("crisis_detected", False):
                    self.log_test("Crisis Detection - Detection", False, "Crisis not detected with hopeless/worthless keywords")
                    return False
                
                # Should have crisis severity
                if "crisis_severity" not in data or not data["crisis_severity"]:
                    self.log_test("Crisis Detection - Severity", False, "Crisis severity not provided")
                    return False
                
                # Severity should be medium or high for these keywords
                if data["crisis_severity"] not in ["medium", "high"]:
                    self.log_test("Crisis Detection - Severity Level", False, f"Unexpected severity: {data['crisis_severity']}")
                    return False
                
                self.log_test("Enhanced Crisis Detection", True, f"Crisis detected with severity: {data['crisis_severity']}")
                return True
            else:
                self.log_test("Enhanced Crisis Detection", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Crisis Detection", False, f"Exception: {str(e)}")
            return False
    
    def test_mood_context_integration(self):
        """Test that therapist responses reference mood patterns"""
        try:
            # First create some mood logs
            mood_logs = [
                "Feeling anxious and worried about the future",
                "Had a panic attack today, feeling overwhelmed",
                "Struggling with negative thoughts about myself"
            ]
            
            for mood in mood_logs:
                self.create_mood_log(mood)
                time.sleep(0.1)
            
            # Wait for processing
            time.sleep(1)
            
            chat_data = {
                "user_id": self.test_user_id,
                "message": "How can I manage my anxiety better?",
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/therapist/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should have mood context
                if not data.get("mood_context"):
                    self.log_test("Mood Context - Context Provided", False, "No mood_context in response")
                    return False
                
                mood_context = data["mood_context"]
                
                # Check mood context structure
                required_keys = ["recent_mood_count", "recent_moods", "patterns"]
                missing_keys = [key for key in required_keys if key not in mood_context]
                
                if missing_keys:
                    self.log_test("Mood Context - Structure", False, f"Missing mood context keys: {missing_keys}")
                    return False
                
                # Should have recent moods
                if mood_context["recent_mood_count"] < 3:
                    self.log_test("Mood Context - Recent Count", False, f"Expected at least 3 recent moods, got {mood_context['recent_mood_count']}")
                    return False
                
                self.log_test("Mood Context Integration", True, f"Mood context provided with {mood_context['recent_mood_count']} recent moods")
                return True
            else:
                self.log_test("Mood Context Integration", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Mood Context Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_session_management_get_sessions(self):
        """Test GET /api/therapist/sessions/{user_id}"""
        try:
            response = requests.get(f"{self.base_url}/therapist/sessions/{self.test_user_id}")
            
            if response.status_code == 200:
                sessions = response.json()
                
                if not isinstance(sessions, list):
                    self.log_test("Get Sessions - Structure", False, "Response should be a list")
                    return False
                
                # Should have at least 1 session from previous tests
                if len(sessions) == 0:
                    self.log_test("Get Sessions - Count", False, "No sessions found")
                    return False
                
                # Check first session structure
                first_session = sessions[0]
                required_keys = ["session_id", "user_id", "session_start", "message_count"]
                missing_keys = [key for key in required_keys if key not in first_session]
                
                if missing_keys:
                    self.log_test("Get Sessions - Session Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify user_id matches
                if first_session["user_id"] != self.test_user_id:
                    self.log_test("Get Sessions - User ID", False, "Session user_id doesn't match")
                    return False
                
                self.log_test("Session Management - Get Sessions", True, f"Retrieved {len(sessions)} sessions")
                return True
            else:
                self.log_test("Session Management - Get Sessions", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Management - Get Sessions", False, f"Exception: {str(e)}")
            return False
    
    def test_session_details(self):
        """Test GET /api/therapist/session/{session_id}"""
        try:
            if not self.session_id:
                self.log_test("Session Details - No Session", False, "No session ID available")
                return False
            
            response = requests.get(f"{self.base_url}/therapist/session/{self.session_id}")
            
            if response.status_code == 200:
                session_data = response.json()
                
                # Check session structure
                required_keys = ["session_id", "user_id", "session_start", "message_count", "messages"]
                missing_keys = [key for key in required_keys if key not in session_data]
                
                if missing_keys:
                    self.log_test("Session Details - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should have messages from our tests
                if not isinstance(session_data["messages"], list):
                    self.log_test("Session Details - Messages Structure", False, "Messages should be a list")
                    return False
                
                if len(session_data["messages"]) == 0:
                    self.log_test("Session Details - Messages Count", False, "No messages in session")
                    return False
                
                # Check first message structure
                first_message = session_data["messages"][0]
                message_keys = ["user_message", "therapist_response", "timestamp"]
                missing_msg_keys = [key for key in message_keys if key not in first_message]
                
                if missing_msg_keys:
                    self.log_test("Session Details - Message Structure", False, f"Missing message keys: {missing_msg_keys}")
                    return False
                
                self.log_test("Session Details", True, f"Session details with {len(session_data['messages'])} messages")
                return True
            else:
                self.log_test("Session Details", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Details", False, f"Exception: {str(e)}")
            return False
    
    def test_mood_checkin_create(self):
        """Test POST /api/therapist/mood-checkin"""
        try:
            checkin_data = {
                "user_id": self.test_user_id,
                "mood_rating": 7,
                "emotions": ["Happy", "Calm"],
                "note": "Feeling good today after our therapy session"
            }
            
            response = requests.post(f"{self.base_url}/therapist/mood-checkin", json=checkin_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["check_in_id", "user_id", "mood_rating", "emotions", "note", "timestamp"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("Mood Check-in Create - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify data matches
                if (data["user_id"] != checkin_data["user_id"] or
                    data["mood_rating"] != checkin_data["mood_rating"] or
                    data["emotions"] != checkin_data["emotions"] or
                    data["note"] != checkin_data["note"]):
                    self.log_test("Mood Check-in Create - Data Match", False, "Response data doesn't match request")
                    return False
                
                # Store check-in ID
                self.checkin_id = data["check_in_id"]
                
                self.log_test("Mood Check-in Create", True, f"Check-in created with rating {data['mood_rating']}")
                return True
            else:
                self.log_test("Mood Check-in Create", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Mood Check-in Create", False, f"Exception: {str(e)}")
            return False
    
    def test_mood_checkins_get(self):
        """Test GET /api/therapist/mood-checkins/{user_id}"""
        try:
            response = requests.get(f"{self.base_url}/therapist/mood-checkins/{self.test_user_id}")
            
            if response.status_code == 200:
                checkins = response.json()
                
                if not isinstance(checkins, list):
                    self.log_test("Get Mood Check-ins - Structure", False, "Response should be a list")
                    return False
                
                # Should have at least 1 check-in from previous test
                if len(checkins) == 0:
                    self.log_test("Get Mood Check-ins - Count", False, "No check-ins found")
                    return False
                
                # Check first check-in structure
                first_checkin = checkins[0]
                required_keys = ["check_in_id", "user_id", "mood_rating", "emotions", "timestamp"]
                missing_keys = [key for key in required_keys if key not in first_checkin]
                
                if missing_keys:
                    self.log_test("Get Mood Check-ins - Check-in Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Verify user_id matches
                if first_checkin["user_id"] != self.test_user_id:
                    self.log_test("Get Mood Check-ins - User ID", False, "Check-in user_id doesn't match")
                    return False
                
                self.log_test("Get Mood Check-ins", True, f"Retrieved {len(checkins)} check-ins")
                return True
            else:
                self.log_test("Get Mood Check-ins", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Mood Check-ins", False, f"Exception: {str(e)}")
            return False
    
    def test_ai_insights(self):
        """Test GET /api/therapist/insights/{user_id}"""
        try:
            response = requests.get(f"{self.base_url}/therapist/insights/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_keys = ["total_sessions", "total_conversations", "total_mood_logs", "total_checkins", "ai_insights"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    self.log_test("AI Insights - Structure", False, f"Missing keys: {missing_keys}")
                    return False
                
                # Should have some data from our tests
                if data["total_sessions"] == 0:
                    self.log_test("AI Insights - Sessions Count", False, "No sessions counted")
                    return False
                
                if data["total_conversations"] == 0:
                    self.log_test("AI Insights - Conversations Count", False, "No conversations counted")
                    return False
                
                # AI insights should be a substantial text
                if not data["ai_insights"] or len(data["ai_insights"]) < 50:
                    self.log_test("AI Insights - Insights Quality", False, "AI insights too short or empty")
                    return False
                
                # Check if insights contain therapeutic language
                insights_text = data["ai_insights"].lower()
                therapeutic_terms = ["progress", "therapy", "coping", "growth", "resilience", "techniques"]
                
                therapeutic_found = any(term in insights_text for term in therapeutic_terms)
                if not therapeutic_found:
                    self.log_test("AI Insights - Therapeutic Content", False, "Insights don't contain therapeutic language")
                    return False
                
                self.log_test("AI Insights", True, f"Generated insights: {data['total_sessions']} sessions, {data['total_conversations']} conversations analyzed")
                return True
            else:
                self.log_test("AI Insights", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("AI Insights", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all AI Therapist tests"""
        print("=" * 60)
        print("🤖 MOODMESH AI THERAPIST BACKEND TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test enhanced chat functionality
        results["first_message"] = self.test_enhanced_chat_first_message()
        results["anxiety_keywords"] = self.test_enhanced_chat_anxiety_keywords()
        results["cbt_trigger"] = self.test_enhanced_chat_cbt_trigger()
        results["dbt_trigger"] = self.test_enhanced_chat_dbt_trigger()
        results["crisis_detection"] = self.test_enhanced_crisis_detection()
        results["mood_context"] = self.test_mood_context_integration()
        
        # Test session management
        results["get_sessions"] = self.test_session_management_get_sessions()
        results["session_details"] = self.test_session_details()
        
        # Test mood check-ins
        results["create_checkin"] = self.test_mood_checkin_create()
        results["get_checkins"] = self.test_mood_checkins_get()
        
        # Test AI insights
        results["ai_insights"] = self.test_ai_insights()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 AI THERAPIST TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All AI Therapist tests PASSED!")
            return True
        else:
            print("⚠️  Some AI Therapist tests FAILED!")
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
    
    # Run Resource Library Tests
    resource_tester = MoodMeshResourceLibraryTest()
    resource_success = resource_tester.run_all_tests()
    
    print("\n" + "=" * 60)
    
    # Run AI Therapist Tests
    therapist_tester = MoodMeshAITherapistTest()
    therapist_success = therapist_tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    
    if analytics_success and meditation_success and resource_success and therapist_success:
        print("🎉 ALL TESTS PASSED! Backend is working correctly.")
        exit(0)
    else:
        if not analytics_success:
            print("❌ Analytics tests failed")
        if not meditation_success:
            print("❌ Meditation tests failed")
        if not resource_success:
            print("❌ Resource Library tests failed")
        if not therapist_success:
            print("❌ AI Therapist tests failed")
        exit(1)