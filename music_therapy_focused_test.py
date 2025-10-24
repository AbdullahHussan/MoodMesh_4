#!/usr/bin/env python3
"""
Focused Music Therapy Test - Addressing User Reported Issues
Tests specific endpoints mentioned in the review request:
1. GET /api/music/library - built-in audio library
2. Audio URL accessibility 
3. Spotify login endpoint
"""

import requests
import json
import time
from urllib.parse import urlparse, parse_qs

# Backend URL from frontend .env
BACKEND_URL = "https://posescan-ai.preview.emergentagent.com/api"

class MusicTherapyFocusedTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def test_music_library_endpoint(self):
        """Test GET /api/music/library - should return built-in audio library"""
        try:
            response = requests.get(f"{self.base_url}/music/library")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required categories
                expected_categories = ["nature", "white_noise", "binaural_beats"]
                missing_categories = [cat for cat in expected_categories if cat not in data]
                
                if missing_categories:
                    self.log_test("Music Library - Categories", False, f"Missing categories: {missing_categories}")
                    return False
                
                # Count items in each category
                nature_count = len(data["nature"])
                white_noise_count = len(data["white_noise"])
                binaural_count = len(data["binaural_beats"])
                total_count = nature_count + white_noise_count + binaural_count
                
                self.log_test("Music Library - Structure", True, f"Found {total_count} items: {nature_count} nature, {white_noise_count} white noise, {binaural_count} binaural beats")
                
                # Verify each item has required fields
                all_items = data["nature"] + data["white_noise"] + data["binaural_beats"]
                required_fields = ["id", "title", "description", "category", "duration", "audio_url", "tags"]
                
                for i, item in enumerate(all_items):
                    missing_fields = [field for field in required_fields if field not in item]
                    if missing_fields:
                        self.log_test("Music Library - Item Structure", False, f"Item {i} missing fields: {missing_fields}")
                        return False
                
                self.log_test("Music Library - Item Structure", True, "All items have required fields")
                return True, data
            else:
                self.log_test("Music Library", False, f"Status: {response.status_code}, Response: {response.text}")
                return False, None
        except Exception as e:
            self.log_test("Music Library", False, f"Exception: {str(e)}")
            return False, None
    
    def test_audio_url_accessibility(self, library_data):
        """Test if audio URLs in the library are accessible"""
        if not library_data:
            self.log_test("Audio URL Test", False, "No library data available")
            return False
        
        try:
            # Test a few URLs from each category
            test_urls = []
            
            # Get first URL from each category
            if library_data["nature"]:
                test_urls.append(("Nature", library_data["nature"][0]["audio_url"]))
            if library_data["white_noise"]:
                test_urls.append(("White Noise", library_data["white_noise"][0]["audio_url"]))
            if library_data["binaural_beats"]:
                test_urls.append(("Binaural Beats", library_data["binaural_beats"][0]["audio_url"]))
            
            accessible_count = 0
            total_tested = len(test_urls)
            
            for category, url in test_urls:
                try:
                    # Test with HEAD request to check accessibility
                    response = requests.head(url, timeout=10, allow_redirects=True)
                    if response.status_code == 200:
                        self.log_test(f"Audio URL - {category}", True, f"Accessible (Status: {response.status_code})")
                        accessible_count += 1
                    else:
                        self.log_test(f"Audio URL - {category}", False, f"Not accessible (Status: {response.status_code})")
                        # Try with GET request in case HEAD is not supported
                        get_response = requests.get(url, timeout=10, stream=True)
                        if get_response.status_code == 200:
                            self.log_test(f"Audio URL - {category} (GET)", True, f"Accessible via GET (Status: {get_response.status_code})")
                            accessible_count += 1
                        else:
                            self.log_test(f"Audio URL - {category} (GET)", False, f"Not accessible via GET (Status: {get_response.status_code})")
                except requests.exceptions.RequestException as e:
                    self.log_test(f"Audio URL - {category}", False, f"Request failed: {str(e)}")
            
            if accessible_count == total_tested:
                self.log_test("Audio URLs Overall", True, f"All {accessible_count}/{total_tested} URLs are accessible")
                return True
            elif accessible_count > 0:
                self.log_test("Audio URLs Overall", False, f"Only {accessible_count}/{total_tested} URLs are accessible")
                return False
            else:
                self.log_test("Audio URLs Overall", False, f"None of the {total_tested} URLs are accessible")
                return False
                
        except Exception as e:
            self.log_test("Audio URL Test", False, f"Exception: {str(e)}")
            return False
    
    def test_spotify_login_endpoint(self):
        """Test GET /api/music/spotify/login - should return valid auth URL"""
        try:
            response = requests.get(f"{self.base_url}/music/spotify/login")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "auth_url" not in data:
                    self.log_test("Spotify Login - Structure", False, "Missing 'auth_url' key")
                    return False
                
                auth_url = data["auth_url"]
                
                # Validate URL format
                if not auth_url.startswith("https://accounts.spotify.com/authorize"):
                    self.log_test("Spotify Login - URL Format", False, f"Invalid auth URL format: {auth_url}")
                    return False
                
                # Parse URL and check required parameters
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                
                required_params = ["client_id", "response_type", "redirect_uri", "scope"]
                missing_params = [param for param in required_params if param not in query_params]
                
                if missing_params:
                    self.log_test("Spotify Login - URL Parameters", False, f"Missing parameters: {missing_params}")
                    return False
                
                # Validate specific parameter values
                if query_params.get("response_type", [""])[0] != "code":
                    self.log_test("Spotify Login - Response Type", False, f"Expected response_type=code, got {query_params.get('response_type')}")
                    return False
                
                # Check if client_id is present and not empty
                client_id = query_params.get("client_id", [""])[0]
                if not client_id:
                    self.log_test("Spotify Login - Client ID", False, "Client ID is empty")
                    return False
                
                # Check if redirect_uri is present
                redirect_uri = query_params.get("redirect_uri", [""])[0]
                if not redirect_uri:
                    self.log_test("Spotify Login - Redirect URI", False, "Redirect URI is empty")
                    return False
                
                # Check if scope includes required permissions
                scope = query_params.get("scope", [""])[0]
                required_scopes = ["user-read-private", "streaming"]
                missing_scopes = [s for s in required_scopes if s not in scope]
                
                if missing_scopes:
                    self.log_test("Spotify Login - Scopes", False, f"Missing required scopes: {missing_scopes}")
                    return False
                
                self.log_test("Spotify Login", True, f"Valid auth URL generated with client_id: {client_id[:8]}...")
                return True
            else:
                self.log_test("Spotify Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Spotify Login", False, f"Exception: {str(e)}")
            return False
    
    def test_spotify_callback_endpoint_exists(self):
        """Test that Spotify callback endpoint exists"""
        try:
            # Test with invalid code to verify endpoint exists
            response = requests.get(f"{self.base_url}/music/spotify/callback?code=invalid_test_code")
            
            # Should return error (not 404) indicating endpoint exists
            if response.status_code == 404:
                self.log_test("Spotify Callback", False, "Endpoint not found (404)")
                return False
            else:
                self.log_test("Spotify Callback", True, f"Endpoint exists (Status: {response.status_code})")
                return True
        except Exception as e:
            self.log_test("Spotify Callback", False, f"Exception: {str(e)}")
            return False
    
    def run_focused_tests(self):
        """Run focused tests for user-reported issues"""
        print("=" * 70)
        print("🎵 MUSIC THERAPY FOCUSED TESTING - USER REPORTED ISSUES")
        print("=" * 70)
        print("Testing specific endpoints mentioned in review request:")
        print("1. GET /api/music/library - built-in audio library")
        print("2. Audio URL accessibility")
        print("3. Spotify login endpoint")
        print("=" * 70)
        
        results = {}
        
        # Test 1: Music Library Endpoint
        print("\n📚 Testing Music Library Endpoint...")
        library_success, library_data = self.test_music_library_endpoint()
        results["music_library"] = library_success
        
        # Test 2: Audio URL Accessibility
        print("\n🔊 Testing Audio URL Accessibility...")
        results["audio_urls"] = self.test_audio_url_accessibility(library_data)
        
        # Test 3: Spotify Login Endpoint
        print("\n🎧 Testing Spotify Login Endpoint...")
        results["spotify_login"] = self.test_spotify_login_endpoint()
        
        # Test 4: Spotify Callback Endpoint Exists
        print("\n🔄 Testing Spotify Callback Endpoint...")
        results["spotify_callback"] = self.test_spotify_callback_endpoint_exists()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 FOCUSED TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        # Detailed findings
        print("\n" + "=" * 70)
        print("🔍 DETAILED FINDINGS")
        print("=" * 70)
        
        if not results["audio_urls"]:
            print("❌ CRITICAL ISSUE: Audio URLs are not accessible (403 Forbidden)")
            print("   - This prevents audio playback for relaxation")
            print("   - URLs appear to be from Pixabay CDN but return 403 errors")
            print("   - Recommendation: Use different audio sources or host files locally")
        
        if results["spotify_login"]:
            print("✅ Spotify OAuth integration is working correctly")
        else:
            print("❌ Spotify OAuth has issues that need to be resolved")
        
        if results["music_library"]:
            print("✅ Music library endpoint returns correct structure and data")
        else:
            print("❌ Music library endpoint has structural issues")
        
        return passed == total

if __name__ == "__main__":
    tester = MusicTherapyFocusedTest()
    success = tester.run_focused_tests()
    
    if success:
        print("\n🎉 All focused tests PASSED!")
    else:
        print("\n⚠️  Some focused tests FAILED - see details above")