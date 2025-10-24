#!/usr/bin/env python3
"""
Comprehensive Exercise Trainer Backend Testing
Tests all scenarios mentioned in the review request
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import time

# Backend URL from frontend .env
BACKEND_URL = "https://posescan-ai.preview.emergentagent.com/api"

class ExerciseTrainerComprehensiveTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = None
        self.auth_token = None
        self.test_username = f"comprehensive_test_user_{int(time.time())}"
        self.test_password = "testpass123"
        self.session_ids = []
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def register_test_user(self):
        """Register a test user for comprehensive testing"""
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
    
    def test_exercise_library_structure(self):
        """Test that exercise library has 12 exercises with proper structure"""
        try:
            response = requests.get(f"{self.base_url}/exercises/list")
            
            if response.status_code == 200:
                data = response.json()
                exercises = data["exercises"]
                
                # Should have exactly 12 exercises
                if len(exercises) != 12:
                    self.log_test("Exercise Library Count", False, f"Expected 12 exercises, got {len(exercises)}")
                    return False
                
                # Check categories distribution
                categories = {}
                for ex in exercises:
                    cat = ex["category"]
                    categories[cat] = categories.get(cat, 0) + 1
                
                expected_categories = {"strength": 4, "cardio": 4, "yoga": 4}
                if categories != expected_categories:
                    self.log_test("Exercise Categories", False, f"Expected {expected_categories}, got {categories}")
                    return False
                
                # Check required fields for each exercise
                required_fields = ["id", "name", "description", "category", "difficulty", 
                                 "target_muscles", "video_url", "form_tips", "calories_per_rep", 
                                 "key_points", "pose_requirements"]
                
                for ex in exercises:
                    missing_fields = [field for field in required_fields if field not in ex]
                    if missing_fields:
                        self.log_test("Exercise Structure", False, f"Exercise {ex['id']} missing: {missing_fields}")
                        return False
                
                self.log_test("Exercise Library Structure", True, "12 exercises with proper structure (4 strength, 4 cardio, 4 yoga)")
                return True
            else:
                self.log_test("Exercise Library Structure", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Exercise Library Structure", False, f"Exception: {str(e)}")
            return False
    
    def test_complete_session_lifecycle_ai_coach(self):
        """Test complete session lifecycle: start → update → complete with AI coach"""
        try:
            if not self.test_user_id:
                self.log_test("Session Lifecycle (AI Coach) - No User", False, "No test user available")
                return False
            
            # 1. Start session with AI coach
            session_data = {
                "user_id": self.test_user_id,
                "exercise_id": "squats",
                "target_reps": 15,
                "used_ai_coach": True
            }
            
            start_response = requests.post(f"{self.base_url}/exercises/session/start", json=session_data)
            if start_response.status_code != 200:
                self.log_test("Session Lifecycle (AI Coach) - Start", False, f"Start failed: {start_response.status_code}")
                return False
            
            start_data = start_response.json()
            session_id = start_data["session_id"]
            self.session_ids.append(session_id)
            
            # 2. Update session progress multiple times
            updates = [
                {"completed_reps": 5, "form_accuracy": 85.0, "feedback_notes": ["Good depth", "Keep knees aligned"]},
                {"completed_reps": 10, "form_accuracy": 88.0, "feedback_notes": ["Excellent form", "Maintain pace"]},
                {"completed_reps": 15, "form_accuracy": 92.0, "feedback_notes": ["Perfect squat depth", "Great control"]}
            ]
            
            for update in updates:
                update["session_id"] = session_id
                update_response = requests.post(f"{self.base_url}/exercises/session/update", json=update)
                if update_response.status_code != 200:
                    self.log_test("Session Lifecycle (AI Coach) - Update", False, f"Update failed: {update_response.status_code}")
                    return False
            
            # 3. Complete session
            complete_data = {
                "session_id": session_id,
                "completed_reps": 15,
                "duration_seconds": 180,
                "form_accuracy": 92.0
            }
            
            complete_response = requests.post(f"{self.base_url}/exercises/session/complete", json=complete_data)
            if complete_response.status_code != 200:
                self.log_test("Session Lifecycle (AI Coach) - Complete", False, f"Complete failed: {complete_response.status_code}")
                return False
            
            complete_result = complete_response.json()
            
            # Verify completion results
            if complete_result["stars_awarded"] != 3:
                self.log_test("Session Lifecycle (AI Coach) - Stars", False, f"Expected 3 stars, got {complete_result['stars_awarded']}")
                return False
            
            # Verify calorie calculation (15 reps * 0.7 calories_per_rep = 10.5)
            expected_calories = 10.5
            if abs(complete_result["calories_burned"] - expected_calories) > 0.1:
                self.log_test("Session Lifecycle (AI Coach) - Calories", False, f"Expected {expected_calories}, got {complete_result['calories_burned']}")
                return False
            
            self.log_test("Session Lifecycle (AI Coach)", True, f"Complete lifecycle: start→update→complete, 3 stars, {complete_result['calories_burned']} calories")
            return True
        except Exception as e:
            self.log_test("Session Lifecycle (AI Coach)", False, f"Exception: {str(e)}")
            return False
    
    def test_complete_session_lifecycle_manual(self):
        """Test complete session lifecycle without AI coach"""
        try:
            if not self.test_user_id:
                self.log_test("Session Lifecycle (Manual) - No User", False, "No test user available")
                return False
            
            # 1. Start session without AI coach
            session_data = {
                "user_id": self.test_user_id,
                "exercise_id": "push-ups",
                "target_reps": 20,
                "used_ai_coach": False
            }
            
            start_response = requests.post(f"{self.base_url}/exercises/session/start", json=session_data)
            if start_response.status_code != 200:
                self.log_test("Session Lifecycle (Manual) - Start", False, f"Start failed: {start_response.status_code}")
                return False
            
            start_data = start_response.json()
            session_id = start_data["session_id"]
            self.session_ids.append(session_id)
            
            # 2. Update session (manual counting, no form accuracy)
            update_data = {
                "session_id": session_id,
                "completed_reps": 20,
                "form_accuracy": None,  # No AI coach, so no form tracking
                "feedback_notes": None
            }
            
            update_response = requests.post(f"{self.base_url}/exercises/session/update", json=update_data)
            if update_response.status_code != 200:
                self.log_test("Session Lifecycle (Manual) - Update", False, f"Update failed: {update_response.status_code}")
                return False
            
            # 3. Complete session
            complete_data = {
                "session_id": session_id,
                "completed_reps": 20,
                "duration_seconds": 120,
                "form_accuracy": None  # No AI coach
            }
            
            complete_response = requests.post(f"{self.base_url}/exercises/session/complete", json=complete_data)
            if complete_response.status_code != 200:
                self.log_test("Session Lifecycle (Manual) - Complete", False, f"Complete failed: {complete_response.status_code}")
                return False
            
            complete_result = complete_response.json()
            
            # Verify completion results
            if complete_result["stars_awarded"] != 3:
                self.log_test("Session Lifecycle (Manual) - Stars", False, f"Expected 3 stars, got {complete_result['stars_awarded']}")
                return False
            
            # Verify calorie calculation (20 reps * 0.5 calories_per_rep = 10.0)
            expected_calories = 10.0
            if abs(complete_result["calories_burned"] - expected_calories) > 0.1:
                self.log_test("Session Lifecycle (Manual) - Calories", False, f"Expected {expected_calories}, got {complete_result['calories_burned']}")
                return False
            
            self.log_test("Session Lifecycle (Manual)", True, f"Complete manual lifecycle: start→update→complete, 3 stars, {complete_result['calories_burned']} calories")
            return True
        except Exception as e:
            self.log_test("Session Lifecycle (Manual)", False, f"Exception: {str(e)}")
            return False
    
    def test_wellness_stars_integration(self):
        """Test that wellness stars are properly awarded and integrated"""
        try:
            if not self.test_user_id:
                self.log_test("Wellness Stars Integration - No User", False, "No test user available")
                return False
            
            # Get user's current wellness stars
            profile_response = requests.get(f"{self.base_url}/profile/{self.test_user_id}")
            if profile_response.status_code != 200:
                self.log_test("Wellness Stars Integration - Profile", False, "Could not get user profile")
                return False
            
            initial_stars = profile_response.json().get("wellness_stars", 0)
            
            # Complete a quick exercise session
            session_data = {
                "user_id": self.test_user_id,
                "exercise_id": "jumping-jacks",
                "target_reps": 10,
                "used_ai_coach": False
            }
            
            # Start session
            start_response = requests.post(f"{self.base_url}/exercises/session/start", json=session_data)
            session_id = start_response.json()["session_id"]
            
            # Complete session
            complete_data = {
                "session_id": session_id,
                "completed_reps": 10,
                "duration_seconds": 30,
                "form_accuracy": None
            }
            
            complete_response = requests.post(f"{self.base_url}/exercises/session/complete", json=complete_data)
            if complete_response.status_code != 200:
                self.log_test("Wellness Stars Integration - Complete", False, "Could not complete session")
                return False
            
            # Check that stars were awarded
            profile_response_after = requests.get(f"{self.base_url}/profile/{self.test_user_id}")
            final_stars = profile_response_after.json().get("wellness_stars", 0)
            
            expected_stars = initial_stars + 3
            if final_stars != expected_stars:
                self.log_test("Wellness Stars Integration", False, f"Expected {expected_stars} stars, got {final_stars}")
                return False
            
            self.log_test("Wellness Stars Integration", True, f"Successfully awarded 3 stars: {initial_stars} → {final_stars}")
            return True
        except Exception as e:
            self.log_test("Wellness Stars Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_calorie_calculation_by_exercise_type(self):
        """Test calorie calculation for different exercise types"""
        try:
            if not self.test_user_id:
                self.log_test("Calorie Calculation - No User", False, "No test user available")
                return False
            
            # Test different exercise types with known calorie values
            test_cases = [
                {"exercise_id": "push-ups", "reps": 10, "expected_calories": 5.0},  # 10 * 0.5
                {"exercise_id": "squats", "reps": 5, "expected_calories": 3.5},     # 5 * 0.7
                {"exercise_id": "burpees", "reps": 3, "expected_calories": 3.0},    # 3 * 1.0
                {"exercise_id": "plank", "reps": 2, "expected_calories": 6.0},      # 2 * 3.0 (plank is time-based)
            ]
            
            for test_case in test_cases:
                # Start session
                session_data = {
                    "user_id": self.test_user_id,
                    "exercise_id": test_case["exercise_id"],
                    "target_reps": test_case["reps"],
                    "used_ai_coach": False
                }
                
                start_response = requests.post(f"{self.base_url}/exercises/session/start", json=session_data)
                session_id = start_response.json()["session_id"]
                
                # Complete session
                complete_data = {
                    "session_id": session_id,
                    "completed_reps": test_case["reps"],
                    "duration_seconds": 60,
                    "form_accuracy": None
                }
                
                complete_response = requests.post(f"{self.base_url}/exercises/session/complete", json=complete_data)
                result = complete_response.json()
                
                # Check calorie calculation
                if abs(result["calories_burned"] - test_case["expected_calories"]) > 0.1:
                    self.log_test("Calorie Calculation", False, 
                                f"{test_case['exercise_id']}: Expected {test_case['expected_calories']}, got {result['calories_burned']}")
                    return False
            
            self.log_test("Calorie Calculation", True, "Correct calorie calculation for all exercise types")
            return True
        except Exception as e:
            self.log_test("Calorie Calculation", False, f"Exception: {str(e)}")
            return False
    
    def test_progress_tracking_comprehensive(self):
        """Test comprehensive progress tracking with multiple sessions"""
        try:
            if not self.test_user_id:
                self.log_test("Progress Tracking - No User", False, "No test user available")
                return False
            
            # Get initial progress
            progress_response = requests.get(f"{self.base_url}/exercises/progress/{self.test_user_id}")
            if progress_response.status_code != 200:
                self.log_test("Progress Tracking - Initial", False, "Could not get initial progress")
                return False
            
            initial_progress = progress_response.json()
            
            # We should have completed several sessions by now
            if initial_progress["total_sessions"] < 3:
                self.log_test("Progress Tracking - Session Count", False, f"Expected at least 3 sessions, got {initial_progress['total_sessions']}")
                return False
            
            # Check that all required fields are present and valid
            required_fields = ["total_sessions", "total_reps", "total_calories", "total_minutes", 
                             "exercises_tried", "favorite_exercise", "current_streak"]
            
            for field in required_fields:
                if field not in initial_progress:
                    self.log_test("Progress Tracking - Fields", False, f"Missing field: {field}")
                    return False
            
            # Verify data types and ranges
            if not isinstance(initial_progress["total_sessions"], int) or initial_progress["total_sessions"] < 0:
                self.log_test("Progress Tracking - Total Sessions", False, "Invalid total_sessions value")
                return False
            
            if not isinstance(initial_progress["total_reps"], int) or initial_progress["total_reps"] < 0:
                self.log_test("Progress Tracking - Total Reps", False, "Invalid total_reps value")
                return False
            
            if not isinstance(initial_progress["current_streak"], int) or initial_progress["current_streak"] < 0:
                self.log_test("Progress Tracking - Streak", False, "Invalid current_streak value")
                return False
            
            # Check that we have a favorite exercise
            if initial_progress["exercises_tried"] > 0 and not initial_progress["favorite_exercise"]:
                self.log_test("Progress Tracking - Favorite Exercise", False, "Should have a favorite exercise")
                return False
            
            self.log_test("Progress Tracking", True, 
                        f"Comprehensive stats: {initial_progress['total_sessions']} sessions, "
                        f"{initial_progress['total_reps']} reps, {initial_progress['total_calories']} calories, "
                        f"{initial_progress['exercises_tried']} exercises tried, "
                        f"favorite: {initial_progress['favorite_exercise']}")
            return True
        except Exception as e:
            self.log_test("Progress Tracking", False, f"Exception: {str(e)}")
            return False
    
    def test_form_accuracy_tracking(self):
        """Test form accuracy tracking for AI coach sessions"""
        try:
            if not self.test_user_id:
                self.log_test("Form Accuracy Tracking - No User", False, "No test user available")
                return False
            
            # Start AI coach session
            session_data = {
                "user_id": self.test_user_id,
                "exercise_id": "lunges",
                "target_reps": 8,
                "used_ai_coach": True
            }
            
            start_response = requests.post(f"{self.base_url}/exercises/session/start", json=session_data)
            session_id = start_response.json()["session_id"]
            
            # Update with form accuracy
            update_data = {
                "session_id": session_id,
                "completed_reps": 8,
                "form_accuracy": 87.5,
                "feedback_notes": ["Good lunge depth", "Keep torso upright", "Excellent balance"]
            }
            
            update_response = requests.post(f"{self.base_url}/exercises/session/update", json=update_data)
            if update_response.status_code != 200:
                self.log_test("Form Accuracy Tracking - Update", False, "Could not update with form accuracy")
                return False
            
            # Complete session
            complete_data = {
                "session_id": session_id,
                "completed_reps": 8,
                "duration_seconds": 90,
                "form_accuracy": 87.5
            }
            
            complete_response = requests.post(f"{self.base_url}/exercises/session/complete", json=complete_data)
            if complete_response.status_code != 200:
                self.log_test("Form Accuracy Tracking - Complete", False, "Could not complete session")
                return False
            
            # Check progress to see if form accuracy is tracked
            progress_response = requests.get(f"{self.base_url}/exercises/progress/{self.test_user_id}")
            progress = progress_response.json()
            
            # Should have average form accuracy now
            if progress.get("average_form_accuracy") is None:
                self.log_test("Form Accuracy Tracking", False, "No average form accuracy calculated")
                return False
            
            if not (0 <= progress["average_form_accuracy"] <= 100):
                self.log_test("Form Accuracy Tracking", False, f"Invalid form accuracy: {progress['average_form_accuracy']}")
                return False
            
            self.log_test("Form Accuracy Tracking", True, f"Form accuracy tracked: {progress['average_form_accuracy']}%")
            return True
        except Exception as e:
            self.log_test("Form Accuracy Tracking", False, f"Exception: {str(e)}")
            return False
    
    def test_streak_calculation(self):
        """Test streak calculation for consecutive daily exercises"""
        try:
            if not self.test_user_id:
                self.log_test("Streak Calculation - No User", False, "No test user available")
                return False
            
            # Get current progress to check streak
            progress_response = requests.get(f"{self.base_url}/exercises/progress/{self.test_user_id}")
            if progress_response.status_code != 200:
                self.log_test("Streak Calculation", False, "Could not get progress")
                return False
            
            progress = progress_response.json()
            
            # Since we've done exercises today, we should have at least a 1-day streak
            if progress["current_streak"] < 1:
                self.log_test("Streak Calculation", False, f"Expected at least 1-day streak, got {progress['current_streak']}")
                return False
            
            self.log_test("Streak Calculation", True, f"Current streak: {progress['current_streak']} days")
            return True
        except Exception as e:
            self.log_test("Streak Calculation", False, f"Exception: {str(e)}")
            return False
    
    def test_exercise_history_retrieval(self):
        """Test exercise history retrieval with proper sorting"""
        try:
            if not self.test_user_id:
                self.log_test("Exercise History - No User", False, "No test user available")
                return False
            
            # Get exercise history
            history_response = requests.get(f"{self.base_url}/exercises/history/{self.test_user_id}")
            if history_response.status_code != 200:
                self.log_test("Exercise History", False, "Could not get exercise history")
                return False
            
            history = history_response.json()
            sessions = history["sessions"]
            
            # Should have multiple sessions
            if len(sessions) < 3:
                self.log_test("Exercise History - Count", False, f"Expected at least 3 sessions, got {len(sessions)}")
                return False
            
            # Check that sessions are sorted by most recent first
            for i in range(len(sessions) - 1):
                current_time = datetime.fromisoformat(sessions[i]["session_start"])
                next_time = datetime.fromisoformat(sessions[i + 1]["session_start"])
                if current_time < next_time:
                    self.log_test("Exercise History - Sorting", False, "Sessions not sorted by most recent first")
                    return False
            
            # Check session structure
            required_fields = ["session_id", "user_id", "exercise_id", "exercise_name", 
                             "target_reps", "completed_reps", "used_ai_coach", "session_start"]
            
            for session in sessions:
                missing_fields = [field for field in required_fields if field not in session]
                if missing_fields:
                    self.log_test("Exercise History - Structure", False, f"Missing fields: {missing_fields}")
                    return False
            
            self.log_test("Exercise History", True, f"Retrieved {len(sessions)} sessions, properly sorted and structured")
            return True
        except Exception as e:
            self.log_test("Exercise History", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all comprehensive exercise trainer tests"""
        print("=" * 70)
        print("🏋️ EXERCISE TRAINER COMPREHENSIVE BACKEND TESTING")
        print("=" * 70)
        
        results = {}
        
        # Test exercise library structure
        results["exercise_library"] = self.test_exercise_library_structure()
        
        # Register test user for session tests
        if self.register_test_user():
            results["user_registration"] = True
            
            # Test complete session lifecycles
            results["session_lifecycle_ai"] = self.test_complete_session_lifecycle_ai_coach()
            results["session_lifecycle_manual"] = self.test_complete_session_lifecycle_manual()
            
            # Test wellness stars integration
            results["wellness_stars"] = self.test_wellness_stars_integration()
            
            # Test calorie calculations
            results["calorie_calculation"] = self.test_calorie_calculation_by_exercise_type()
            
            # Test progress tracking
            results["progress_tracking"] = self.test_progress_tracking_comprehensive()
            
            # Test form accuracy tracking
            results["form_accuracy"] = self.test_form_accuracy_tracking()
            
            # Test streak calculation
            results["streak_calculation"] = self.test_streak_calculation()
            
            # Test exercise history
            results["exercise_history"] = self.test_exercise_history_retrieval()
        else:
            results["user_registration"] = False
            for key in ["session_lifecycle_ai", "session_lifecycle_manual", "wellness_stars", 
                       "calorie_calculation", "progress_tracking", "form_accuracy", 
                       "streak_calculation", "exercise_history"]:
                results[key] = False
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All comprehensive exercise trainer tests PASSED!")
            return True
        else:
            print("⚠️  Some comprehensive tests FAILED!")
            return False

if __name__ == "__main__":
    test = ExerciseTrainerComprehensiveTest()
    test.run_all_tests()