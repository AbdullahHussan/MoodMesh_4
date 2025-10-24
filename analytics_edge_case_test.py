#!/usr/bin/env python3
"""
Additional Edge Case Tests for MoodMesh Analytics
Tests streak calculations, consecutive days, and data accuracy
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import time

BACKEND_URL = "https://posescan-ai.preview.emergentagent.com/api"

class AnalyticsEdgeCaseTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
    
    def create_test_user(self, suffix=""):
        """Create a test user and return user_id"""
        try:
            username = f"edge_test_user_{int(time.time())}{suffix}"
            response = requests.post(f"{self.base_url}/auth/register", json={
                "username": username,
                "password": "testpass123"
            })
            
            if response.status_code == 200:
                data = response.json()
                return data["user_id"], username
            return None, None
        except Exception as e:
            print(f"Failed to create user: {str(e)}")
            return None, None
    
    def create_mood_log(self, user_id, mood_text):
        """Create a mood log"""
        try:
            response = requests.post(f"{self.base_url}/mood/log", json={
                "user_id": user_id,
                "mood_text": mood_text
            })
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to create mood log: {str(e)}")
            return False
    
    def test_consecutive_days_streak(self):
        """Test streak calculation with logs on consecutive days"""
        try:
            user_id, username = self.create_test_user("_streak")
            if not user_id:
                self.log_test("Consecutive Days Setup", False, "Failed to create user")
                return False
            
            # Create multiple mood logs to simulate consecutive days
            # Note: Since we can't manipulate timestamps directly, we'll create multiple logs
            # and check if the streak logic works with same-day logs
            
            moods = [
                "Day 1: Feeling good about starting this journey",
                "Day 1 evening: Reflecting on the day",
                "Day 2: Another day of growth",
                "Day 2 afternoon: Continuing the streak"
            ]
            
            for mood in moods:
                if not self.create_mood_log(user_id, mood):
                    self.log_test("Consecutive Days Logs", False, "Failed to create mood log")
                    return False
                time.sleep(0.1)
            
            time.sleep(1)  # Wait for processing
            
            # Get analytics
            response = requests.get(f"{self.base_url}/mood/analytics/{user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if streak is calculated (should be at least 1 for same day)
                if data["current_streak"] >= 1 and data["longest_streak"] >= 1:
                    self.log_test("Consecutive Days Streak", True, f"Current: {data['current_streak']}, Longest: {data['longest_streak']}")
                    return True
                else:
                    self.log_test("Consecutive Days Streak", False, f"Unexpected streaks - Current: {data['current_streak']}, Longest: {data['longest_streak']}")
                    return False
            else:
                self.log_test("Consecutive Days Streak", False, f"API error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Consecutive Days Streak", False, f"Exception: {str(e)}")
            return False
    
    def test_data_accuracy_detailed(self):
        """Test detailed data accuracy of analytics calculations"""
        try:
            user_id, username = self.create_test_user("_accuracy")
            if not user_id:
                self.log_test("Data Accuracy Setup", False, "Failed to create user")
                return False
            
            # Create specific mood logs with known words
            test_moods = [
                "I am feeling happy and joyful today",
                "Feeling anxious and worried about tomorrow", 
                "Happy thoughts are filling my mind",
                "Anxious feelings keep returning",
                "Joyful moments with family today"
            ]
            
            # Expected word counts
            expected_words = {
                "happy": 2,
                "anxious": 2, 
                "joyful": 2,
                "worried": 1,
                "thoughts": 1,
                "feelings": 1,
                "moments": 1
            }
            
            for mood in test_moods:
                if not self.create_mood_log(user_id, mood):
                    self.log_test("Data Accuracy Logs", False, "Failed to create mood log")
                    return False
                time.sleep(0.1)
            
            time.sleep(1)  # Wait for processing
            
            # Get analytics
            response = requests.get(f"{self.base_url}/mood/analytics/{user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check total logs
                if data["total_logs"] != len(test_moods):
                    self.log_test("Data Accuracy - Count", False, f"Expected {len(test_moods)}, got {data['total_logs']}")
                    return False
                
                # Check common emotions for expected words
                common_emotions = {item["word"]: item["count"] for item in data["common_emotions"]}
                
                accuracy_issues = []
                for word, expected_count in expected_words.items():
                    if word in common_emotions:
                        if common_emotions[word] != expected_count:
                            accuracy_issues.append(f"{word}: expected {expected_count}, got {common_emotions[word]}")
                
                if accuracy_issues:
                    self.log_test("Data Accuracy - Words", False, f"Issues: {', '.join(accuracy_issues)}")
                else:
                    self.log_test("Data Accuracy - Words", True, "Word extraction and counting accurate")
                
                # Check hourly distribution sums to total
                hourly_total = sum(data["hourly_distribution"].values())
                if hourly_total == len(test_moods):
                    self.log_test("Data Accuracy - Hourly", True, "Hourly distribution sums correctly")
                else:
                    self.log_test("Data Accuracy - Hourly", False, f"Hourly sum {hourly_total} != total logs {len(test_moods)}")
                
                return len(accuracy_issues) == 0
            else:
                self.log_test("Data Accuracy", False, f"API error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Data Accuracy", False, f"Exception: {str(e)}")
            return False
    
    def test_large_dataset(self):
        """Test analytics with a larger dataset"""
        try:
            user_id, username = self.create_test_user("_large")
            if not user_id:
                self.log_test("Large Dataset Setup", False, "Failed to create user")
                return False
            
            # Create 20 mood logs
            base_moods = [
                "Feeling great today",
                "A bit stressed about work", 
                "Happy and content",
                "Worried about the future",
                "Excited for the weekend"
            ]
            
            created_count = 0
            for i in range(20):
                mood = f"{base_moods[i % len(base_moods)]} - entry {i+1}"
                if self.create_mood_log(user_id, mood):
                    created_count += 1
                time.sleep(0.05)  # Small delay
            
            time.sleep(2)  # Wait for processing
            
            # Get analytics
            response = requests.get(f"{self.base_url}/mood/analytics/{user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["total_logs"] == created_count:
                    self.log_test("Large Dataset", True, f"Correctly processed {created_count} logs")
                    
                    # Check if insights are generated for larger dataset
                    if len(data["insights"]) > 0:
                        self.log_test("Large Dataset Insights", True, f"Generated {len(data['insights'])} insights")
                    else:
                        self.log_test("Large Dataset Insights", False, "No insights generated for large dataset")
                    
                    return True
                else:
                    self.log_test("Large Dataset", False, f"Expected {created_count}, got {data['total_logs']}")
                    return False
            else:
                self.log_test("Large Dataset", False, f"API error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Large Dataset", False, f"Exception: {str(e)}")
            return False
    
    def test_special_characters_and_unicode(self):
        """Test analytics with special characters and unicode in mood text"""
        try:
            user_id, username = self.create_test_user("_unicode")
            if not user_id:
                self.log_test("Unicode Setup", False, "Failed to create user")
                return False
            
            # Test with various special characters and unicode
            special_moods = [
                "Feeling 😊 happy today! 🌟",
                "Très content aujourd'hui (very happy today)",
                "感觉很好 (feeling good)",
                "Mood: 100% awesome!!! @#$%",
                "Mixed emotions... 50/50 happy-sad"
            ]
            
            for mood in special_moods:
                if not self.create_mood_log(user_id, mood):
                    self.log_test("Unicode Logs", False, f"Failed to create log with: {mood}")
                    return False
                time.sleep(0.1)
            
            time.sleep(1)  # Wait for processing
            
            # Get analytics
            response = requests.get(f"{self.base_url}/mood/analytics/{user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["total_logs"] == len(special_moods):
                    self.log_test("Unicode and Special Characters", True, "Handles special characters correctly")
                    return True
                else:
                    self.log_test("Unicode and Special Characters", False, f"Expected {len(special_moods)}, got {data['total_logs']}")
                    return False
            else:
                self.log_test("Unicode and Special Characters", False, f"API error: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Unicode and Special Characters", False, f"Exception: {str(e)}")
            return False
    
    def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("=" * 60)
        print("🔬 ANALYTICS EDGE CASE TESTING")
        print("=" * 60)
        
        results = {}
        
        results["consecutive_days"] = self.test_consecutive_days_streak()
        results["data_accuracy"] = self.test_data_accuracy_detailed()
        results["large_dataset"] = self.test_large_dataset()
        results["unicode_special"] = self.test_special_characters_and_unicode()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 EDGE CASE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} edge case tests passed")
        
        return passed == total

if __name__ == "__main__":
    tester = AnalyticsEdgeCaseTest()
    success = tester.run_edge_case_tests()
    exit(0 if success else 1)