#!/usr/bin/env python3
"""
Music Endpoint Removal Test for MoodMesh
Tests that all music and sound therapy endpoints have been removed from the backend
"""

import requests
import json
import uuid
import time

# Backend URL from frontend .env
BACKEND_URL = "https://posescan-ai.preview.emergentagent.com/api"

class MusicRemovalTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = None
        self.auth_token = None
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def register_test_user(self):
        """Register a test user for testing other endpoints"""
        try:
            test_username = f"removal_test_user_{int(time.time())}"
            response = requests.post(f"{self.base_url}/auth/register", json={
                "username": test_username,
                "password": "testpass123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.test_user_id = data["user_id"]
                self.auth_token = data["access_token"]
                self.log_test("User Registration", True, f"Created user: {test_username}")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_music_endpoints_removed(self):
        """Test that all music/spotify endpoints return 404 Not Found"""
        
        # List of music endpoints that should be removed
        music_endpoints = [
            "/music/spotify/login",
            "/music/spotify/callback",
            "/music/spotify/refresh", 
            "/music/spotify/profile",
            "/music/spotify/search",
            "/music/spotify/recommendations",
            "/music/library",
            f"/music/recommendations/{str(uuid.uuid4())}",
            "/music/journal/create",
            f"/music/journal/{str(uuid.uuid4())}",
            f"/music/journal/entry/{str(uuid.uuid4())}",
            "/music/history/save",
            f"/music/history/{str(uuid.uuid4())}"
        ]
        
        all_removed = True
        removed_count = 0
        
        print("\n🎵 Testing Music Endpoint Removal:")
        print("=" * 50)
        
        for endpoint in music_endpoints:
            try:
                # Test GET endpoints
                if endpoint in ["/music/journal/create", "/music/history/save"]:
                    # These are POST endpoints, test with POST
                    response = requests.post(f"{self.base_url}{endpoint}", json={})
                elif "/music/spotify/refresh" in endpoint:
                    # This is a POST endpoint
                    response = requests.post(f"{self.base_url}{endpoint}", json={})
                else:
                    # GET endpoints
                    response = requests.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 404:
                    self.log_test(f"Removed: {endpoint}", True, "404 Not Found (correctly removed)")
                    removed_count += 1
                else:
                    self.log_test(f"Still exists: {endpoint}", False, f"Status: {response.status_code}")
                    all_removed = False
                    
            except Exception as e:
                self.log_test(f"Error testing {endpoint}", False, f"Exception: {str(e)}")
                all_removed = False
        
        print(f"\n📊 Removal Summary: {removed_count}/{len(music_endpoints)} endpoints removed")
        return all_removed
    
    def test_other_endpoints_still_work(self):
        """Test that non-music endpoints still work correctly"""
        
        if not self.test_user_id:
            self.log_test("Other Endpoints Test", False, "No test user available")
            return False
        
        print("\n🔧 Testing Other Endpoints Still Work:")
        print("=" * 50)
        
        working_endpoints = 0
        total_endpoints = 0
        
        # Test meditation endpoints
        try:
            total_endpoints += 1
            response = requests.get(f"{self.base_url}/meditation/exercises")
            if response.status_code == 200:
                self.log_test("Meditation Exercises", True, "Working correctly")
                working_endpoints += 1
            else:
                self.log_test("Meditation Exercises", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Meditation Exercises", False, f"Exception: {str(e)}")
        
        # Test resources endpoint
        try:
            total_endpoints += 1
            response = requests.get(f"{self.base_url}/resources")
            if response.status_code == 200:
                self.log_test("Resources", True, "Working correctly")
                working_endpoints += 1
            else:
                self.log_test("Resources", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Resources", False, f"Exception: {str(e)}")
        
        # Test mood analytics
        try:
            total_endpoints += 1
            response = requests.get(f"{self.base_url}/mood/analytics/{self.test_user_id}")
            if response.status_code == 200:
                self.log_test("Mood Analytics", True, "Working correctly")
                working_endpoints += 1
            else:
                self.log_test("Mood Analytics", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Mood Analytics", False, f"Exception: {str(e)}")
        
        # Test meditation progress
        try:
            total_endpoints += 1
            response = requests.get(f"{self.base_url}/meditation/progress/{self.test_user_id}")
            if response.status_code == 200:
                self.log_test("Meditation Progress", True, "Working correctly")
                working_endpoints += 1
            else:
                self.log_test("Meditation Progress", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Meditation Progress", False, f"Exception: {str(e)}")
        
        print(f"\n📊 Working Endpoints: {working_endpoints}/{total_endpoints}")
        return working_endpoints == total_endpoints
    
    def test_backend_health(self):
        """Test that backend is running without errors"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "MoodMesh API" in data.get("message", ""):
                    self.log_test("Backend Health", True, "Backend is running correctly")
                    return True
                else:
                    self.log_test("Backend Health", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Backend Health", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all music removal tests"""
        print("=" * 60)
        print("🎵 MOODMESH MUSIC ENDPOINT REMOVAL TESTING")
        print("=" * 60)
        
        results = {}
        
        # Test backend health first
        results["backend_health"] = self.test_backend_health()
        
        # Test that music endpoints are removed
        results["music_endpoints_removed"] = self.test_music_endpoints_removed()
        
        # Register test user for other endpoint tests
        if self.register_test_user():
            results["user_registration"] = True
            # Test that other endpoints still work
            results["other_endpoints_work"] = self.test_other_endpoints_still_work()
        else:
            results["user_registration"] = False
            results["other_endpoints_work"] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 MUSIC REMOVAL TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if results.get("music_endpoints_removed", False):
            print("🎉 SUCCESS: All music endpoints have been successfully removed!")
        else:
            print("⚠️  FAILURE: Some music endpoints are still present!")
        
        if results.get("other_endpoints_work", False):
            print("✅ SUCCESS: Other endpoints are still working correctly!")
        else:
            print("⚠️  WARNING: Some other endpoints may have issues!")
        
        return passed == total

if __name__ == "__main__":
    tester = MusicRemovalTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎊 ALL TESTS PASSED - Music endpoints successfully removed!")
        exit(0)
    else:
        print("\n💥 SOME TESTS FAILED - Check results above")
        exit(1)