# Spotify Integration Setup Guide

## Issue: "INVALID_CLIENT: Invalid redirect URI"

This error occurs when the redirect URI configured in your app doesn't match what's registered in the Spotify Developer Dashboard.

## Solution: Register the Redirect URI in Spotify Dashboard

### Step 1: Access Spotify Developer Dashboard
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account

### Step 2: Find Your App
1. Click on your app (the one with Client ID: `d1dbf68dc2df4f809d868d3380d0e96a`)
2. Click "Settings" button

### Step 3: Add Redirect URI
1. Scroll down to "Redirect URIs" section
2. Add this exact URL:
   ```
   https://alt-plivo-service.preview.emergentagent.com/music
   ```
3. Click "Add" button
4. Scroll to the bottom and click "Save" button

### Step 4: Test the Connection
1. Go back to your Music & Sound Therapy page
2. Click "Connect Spotify" button
3. You should now be redirected to Spotify authorization page
4. After authorizing, you'll be redirected back to your app

## Troubleshooting

### If you still get errors:
1. **Double-check the URL** - It must match exactly (including https://, no trailing slash)
2. **Wait a few minutes** - Spotify may take a moment to propagate changes
3. **Clear browser cache** - Sometimes old OAuth tokens are cached
4. **Try incognito mode** - To ensure no cached data interferes

### Common Mistakes:
- ❌ Adding trailing slash: `https://alt-plivo-service.preview.emergentagent.com/music/`
- ❌ Using http instead of https: `http://relax-player-patch.preview.emergentagent.com/music`
- ❌ Wrong path: `https://alt-plivo-service.preview.emergentagent.com/spotify`
- ✅ Correct: `https://alt-plivo-service.preview.emergentagent.com/music`

## What's Been Fixed

✅ **Audio Playback Bug**: All relaxation audio files (nature sounds, white noise, binaural beats) now work correctly
✅ **Error Handling**: Better error messages for Spotify OAuth issues
✅ **Frontend Improvements**: Added proper Promise handling for audio playback

## Need Help?

If you're still experiencing issues after following these steps:
1. Check the browser console for detailed error messages (F12 → Console tab)
2. Verify your Spotify Client ID and Secret are correct in backend/.env
3. Ensure you're using the same Spotify account that owns the app
