# 🚨 Voice Calling Setup Guide - Automated Crisis Calls

## Overview

Your mental health app now has **AI-powered automated voice calling** capability! When the AI detects emotional breakdown or crisis situations, it can:

1. **Automatically call** user's saved close contacts
2. **Use AI-generated text-to-speech** to deliver personalized crisis messages
3. **Call appropriate authorities** (crisis hotlines) if no contacts are saved
4. **Smart consent handling**: Auto-call for critical cases, ask permission for others

---

## 🆓 How to Get FREE Plivo Account ($15 Credit = ~750 Minutes)

### Step 1: Sign Up for Plivo Trial

1. Visit: **https://www.plivo.com/request-trial/**
2. Fill out the form:
   - **Name & Email**: Your details
   - **Phone Number**: Your contact number
   - **Expected Monthly Volume**: Select "Less than 1,000"
   - **Primary Use Case**: Write: "Mental health crisis detection app - automated emergency notifications"
3. Submit and wait for approval email (usually instant)

### Step 2: Get Your API Credentials

1. Log into Plivo Console: **https://console.plivo.com**
2. Go to **Overview** page
3. Copy these credentials:
   - **Auth ID**: Found at top of dashboard (looks like: `MAXXXXXXXXXXXXXXXXXX`)
   - **Auth Token**: Click "Show" next to Auth ID (looks like: `YzJkxxxxxxxxxxxxxxx`)

### Step 3: Get a Phone Number

1. In Plivo Console, go to **Phone Numbers** → **Buy Numbers**
2. Select your country (e.g., United States)
3. Choose **Voice-enabled** number
4. Click **Buy** (Free in trial mode)
5. Copy your new phone number (format: `+1234567890`)

### Step 4: Add Credentials to Your App

1. Open `/app/backend/.env` file
2. Add your credentials:

```env
PLIVO_AUTH_ID="YOUR_AUTH_ID_HERE"
PLIVO_AUTH_TOKEN="YOUR_AUTH_TOKEN_HERE"
PLIVO_PHONE_NUMBER="+1234567890"
```

3. Save the file
4. Restart backend: `sudo supervisorctl restart backend`

---

## ✅ How to Test

### 1. Verify Setup

Check if Plivo is working by looking at backend logs:
```bash
tail -f /var/log/supervisor/backend.out.log
```

You should see: `"Plivo client initialized successfully"`

### 2. Add Emergency Contacts

1. Go to **Crisis Support** page in your app
2. Add at least one emergency contact with a **valid phone number**
3. Important: For trial accounts, verify your phone number in Plivo Console first:
   - Go to **Settings** → **Verify Callee** in Plivo Console
   - Add your personal number to test calling

### 3. Trigger Crisis Detection

**Option A: Through AI Therapist**
1. Go to AI Therapist chat
2. Send a crisis message like: "I can't take this anymore, I feel hopeless and worthless"
3. AI will detect crisis and show emergency popup
4. Click **"Call for Help Now"** button

**Option B: Through Mood Log**
1. Go to Mood Log page
2. Write crisis-related text: "I'm having dark thoughts and feel like giving up"
3. Submit mood log
4. Emergency popup will appear
5. Click **"Call for Help Now"** button

### 4. What Happens When Call Initiates

- **Critical Severity**: Auto-calls immediately without asking
- **High/Medium Severity**: Shows confirmation dialog first
- AI generates personalized message based on crisis context
- Calls your emergency contacts one by one (up to 3)
- If no contacts saved, recommends calling crisis hotlines

---

## 🎯 How It Works

### AI Crisis Detection Flow

```
User sends emotional message
        ↓
AI analyzes text (Gemini 2.5 Flash)
        ↓
Detects crisis severity (low/medium/high/critical)
        ↓
Shows Emergency Popup
        ↓
User clicks "Call for Help Now" (or auto-calls if critical)
        ↓
AI generates voice message
        ↓
Plivo initiates calls to close contacts
        ↓
Recipients receive automated call with TTS message
```

### Voice Message Example

When someone picks up the call, they hear:

> "This is an automated emergency alert. Your contact [Name] may need immediate support based on concerning patterns detected in their mental health app. Please reach out to them as soon as possible. This is a high priority situation."

The message is **AI-generated** based on the specific crisis context and personalized for each situation.

---

## 🔒 Privacy & Consent

### User Consent Handling

- **Critical Severity (suicidal ideation)**: Auto-calls without asking (assumes opt-in via app settings)
- **High Severity (severe distress)**: Asks user confirmation before calling
- **Medium Severity (moderate concern)**: Requires explicit consent

### Data Storage

All calls are logged in the database with:
- Timestamp
- Recipient details
- Call status (initiated, completed, failed)
- Crisis context (encrypted)
- User consent status

### Compliance

⚠️ **Important Legal Considerations:**
- **NOT calling 911 directly** - this is for privacy and legal compliance
- Instead, recommends appropriate crisis hotlines
- User can manually call emergency services if needed
- All automated calls are to user's pre-approved contacts only

---

## 💰 Pricing After Free Trial

### Plivo Pricing (Pay-as-you-go)

- **Outbound Calls (US)**: ~$0.02/minute
- **Phone Number Rental**: ~$1/month
- **Text-to-Speech**: Included

**Example Cost Calculation:**
- 10 crisis calls per month
- Average 2 minutes per call
- Cost: 10 × 2 × $0.02 = **$0.40/month** + $1 rental = **$1.40/month**

### Free Alternatives (Limitations)

There are **NO truly free unlimited options** for voice calling APIs. All telephony services charge because they use real phone networks. However:

- **Twilio Trial**: $15 credit (same as Plivo)
- **Sinch Trial**: Limited free credits
- **Vonage Trial**: Limited minutes

Plivo offers **best pricing** compared to alternatives (30-40% cheaper than Twilio).

---

## 🚧 Known Limitations (Trial Account)

### Trial Account Restrictions

1. **Verified Numbers Only**: Can only call phone numbers you verify in Plivo Console
   - Solution: Verify test numbers before demo
   
2. **No International Calling**: Limited to local country during trial
   - Solution: Upgrade to paid account for international support
   
3. **Call Recording**: Available but requires webhook configuration
   - Currently disabled for simplicity
   
4. **Concurrent Calls**: Limited to 2-3 simultaneous calls in trial
   - Sufficient for most crisis scenarios

---

## 🐛 Troubleshooting

### Issue: "Voice calling service is not configured"

**Solution:**
- Check if Plivo credentials are in `.env` file
- Verify credentials are correct (no extra spaces)
- Restart backend after adding credentials

### Issue: "Invalid phone number" errors

**Solution:**
- Phone numbers must be in E.164 format: `+1234567890`
- No spaces, dashes, or parentheses
- Must include country code (+ sign)

### Issue: Calls not connecting

**Solution:**
- **Trial accounts**: Verify recipient's number in Plivo Console
- Check Plivo account credits haven't run out
- View call logs in Plivo Console for error details

### Issue: "User consent required" error

**Solution:**
- This is for medium/high severity (not critical)
- User must click "Yes, Call Now" confirmation button
- Critical severity auto-calls without asking

### Check Backend Logs

```bash
# View recent logs
tail -n 100 /var/log/supervisor/backend.out.log | grep -i "plivo\|call\|crisis"

# Monitor live logs
tail -f /var/log/supervisor/backend.out.log
```

---

## 🎉 Feature Summary

### What's New

✅ **AI-Powered Voice Calling**
- Automatically calls emergency contacts during crisis
- AI-generated personalized voice messages
- Text-to-speech for clear communication

✅ **Smart Consent System**
- Auto-call for critical situations
- Ask permission for less severe cases
- User always in control

✅ **Intelligent Fallback**
- Calls close contacts first
- Recommends crisis hotlines if no contacts
- Never leaves user without resources

✅ **Real-time Status Updates**
- Shows call initiation progress
- Displays success/failure for each call
- Provides detailed call logs

✅ **Cost-Effective**
- FREE trial with $15 credit
- Only ~$0.02/minute after trial
- Pay only for what you use

---

## 📞 Support

### Need Help?

1. **Plivo Support**: https://support.plivo.com
2. **Documentation**: https://www.plivo.com/docs/voice/
3. **Trial Account Help**: https://support.plivo.com/hc/en-us/articles/360041203772

### Common Questions

**Q: Can I use this in production without payment?**  
A: No, trial credit will run out. Need paid account for production use.

**Q: Can it call international numbers?**  
A: Yes, but costs vary by country. Trial may be limited to local country.

**Q: Is it HIPAA compliant?**  
A: Plivo offers HIPAA compliance in paid plans. Trial is for testing only.

**Q: What if user doesn't have contacts saved?**  
A: System recommends appropriate crisis hotlines based on severity.

---

## ✨ Next Steps

1. ✅ Sign up for Plivo trial account
2. ✅ Add credentials to `.env` file
3. ✅ Restart backend
4. ✅ Add test emergency contact
5. ✅ Test crisis detection
6. ✅ Try automated calling feature
7. 🎯 Deploy to production when ready

**Congratulations!** Your mental health app now has life-saving automated crisis calling capability! 🚑💙
