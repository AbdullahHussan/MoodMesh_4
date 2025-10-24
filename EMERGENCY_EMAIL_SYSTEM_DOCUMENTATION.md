# Emergency Email Alert System - Documentation

## ⚠️ CRITICAL INFORMATION

This system sends alerts to **REAL AUTHORITIES** (currently configured as: `abdullahdeveloper4@gmail.com`, will be changed to actual emergency services).

**False positives are NOT acceptable** - they waste emergency resources and can have serious legal/ethical consequences.

---

## 🎯 System Philosophy

**Ultra-Conservative Approach**: Better to show a popup with support resources than to alert authorities unnecessarily.

---

## 📋 Decision Logic

### When Emails ARE Sent to Authorities:

Emails are **ONLY** sent when **ALL** of these conditions are met:

1. ✅ **Severity = CRITICAL** (not high, medium, or low)
2. ✅ **AND** Either:
   - **Explicit imminent threat detected** (keywords like "going to kill myself now", "overdosing", "about to jump", etc.)
   - **OR** Sustained critical pattern (2+ critical incidents in last 24 hours)
3. ✅ **AND** No authority alert sent in last **4 hours** (cooldown period)
4. ✅ **AND** Crisis text is NOT 70%+ similar to recent alerts (not a repeat)

### When Emails ARE NOT Sent:

- ❌ Severity is "high", "medium", or "low" → **Popup support only**
- ❌ Already alerted authorities within last 4 hours → **Cooldown active**
- ❌ Text is too similar to recent alert → **Likely repeat/venting**
- ❌ No explicit threat AND no sustained pattern → **Insufficient evidence**

---

## 🔍 Explicit Critical Keywords

The system looks for these phrases to identify **imminent threats**:

```
- "going to kill myself"
- "about to kill myself"  
- "killing myself now"
- "going to end my life"
- "about to end my life"
- "ending my life now"
- "suicide tonight"
- "suicide today"
- "suicide right now"
- "overdose now"
- "overdosing"
- "taking pills"
- "going to jump"
- "about to jump"
- "gun"
- "hanging myself"
```

---

## ⏱️ Cooldown System

**4-hour cooldown** between authority alerts for the same user.

**Why?**
- Prevents alert fatigue for emergency responders
- Allows time for initial intervention to take effect
- Reduces false positives from repeated venting

**Exception**: If severity escalates dramatically or explicit threat language appears.

---

## 📊 What Gets Logged

Every evaluation is logged to the database with:

```javascript
{
  "alert_id": "uuid",
  "user_id": "user_id",
  "severity": "critical", // or high, medium, low
  "crisis_context": "User's text...",
  "email_sent": true, // or false
  "decision_reason": "✓ CRITICAL severity + explicit imminent threat detected",
  "alert_email": "abdullahdeveloper4@gmail.com", // or null if not sent
  "timestamp": "2025-01-XX...",
  "ai_message": "AI-generated intervention message for authorities"
}
```

---

## 🔄 Decision Flow

```
User sends concerning text
    ↓
AI analyzes → Assigns severity (low/medium/high/critical)
    ↓
IF severity != "critical" → STOP, show popup only
    ↓
Check last authority alert time
    ↓
IF alerted within 4 hours → STOP, cooldown active
    ↓
Check for explicit imminent threat keywords
    ↓
IF no explicit keywords → Check for sustained pattern (2+ critical in 24h)
    ↓
IF no pattern → STOP, insufficient evidence
    ↓
Check text similarity to recent alerts
    ↓
IF >70% similar → STOP, likely repeat
    ↓
✅ ALL CHECKS PASSED → Send email to authorities + Log decision
```

---

## 📧 Email Content

When an email IS sent, it includes:

1. **Verified header**: Confirms this passed strict checks
2. **Incident details**: User ID, timestamp, severity
3. **Crisis context**: The concerning text
4. **AI risk assessment**: Generated intervention message
5. **Recommended actions**: For emergency responders
6. **Emergency resources**: 988, Crisis Text Line, etc.

---

## 🛠️ Implementation Details

### Backend Function: `should_send_emergency_email()`

Location: `/app/backend/server.py`

**Returns**: `(bool, str)` - (should_send, reason)

**Checks performed**:
1. Severity threshold check
2. Recent alert history query
3. Cooldown period verification
4. Explicit keyword detection
5. Sustained pattern analysis (learning profile)
6. Text similarity comparison

### API Endpoint: `/api/crisis/initiate-call`

**Modified behavior**:
- OLD: Always sent email on every call
- NEW: Evaluates with `should_send_emergency_email()` first
- Logs decision reasoning regardless of outcome

---

## 📈 Monitoring & Analytics

Track these metrics to tune the system:

1. **Email send rate**: How many authorities alerts per day/week
2. **False positive rate**: Alerts that didn't require intervention
3. **Missed critical incidents**: Should have alerted but didn't
4. **Cooldown effectiveness**: Are 4 hours appropriate?
5. **Keyword coverage**: Are we missing important phrases?

---

## 🔧 Configuration

### Adjustable Parameters

```python
# Cooldown period (currently 4 hours)
recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=4)

# Sustained pattern threshold (currently 2 critical in 24h)
if len(recent_critical) < 2:
    # Don't send

# Text similarity threshold (currently 70%)
if overlap > 0.7:
    # Don't send (too similar)
```

### To Make More Strict:
- Increase cooldown to 6-8 hours
- Require 3+ critical incidents instead of 2
- Add more verification steps

### To Make Less Strict:
- Allow "high" severity to trigger (NOT RECOMMENDED)
- Reduce cooldown to 2 hours
- Require only 1 critical incident

**⚠️ CAUTION**: Any loosening of restrictions must be carefully considered given we're alerting real authorities.

---

## 🧪 Testing Recommendations

### Test Scenarios:

1. **Low/Medium/High Severity**: Confirm NO email sent (popup only)
2. **Critical without explicit keywords**: Confirm NO email (or only with pattern)
3. **Critical with explicit keywords**: Confirm email sent
4. **Repeat alerts**: Confirm cooldown prevents duplicate emails
5. **Similar text**: Confirm text similarity check works
6. **Sustained pattern**: Confirm 2+ critical in 24h triggers alert

---

## 📱 User Experience

**What user sees**:
- Emergency popup with support resources
- Close contacts displayed
- Crisis hotline numbers
- AI-recommended immediate actions

**What user DOESN'T see**:
- Whether email was sent to authorities
- Decision reasoning
- Cooldown status
- Learning profile analysis

**Why hidden?**: Prevents user in crisis from avoiding help or being further distressed.

---

## 🚨 Important Notes

1. **Email address**: Currently `abdullahdeveloper4@gmail.com` - **must be updated** to real emergency service address before production

2. **Legal considerations**: Ensure compliance with:
   - HIPAA (if applicable)
   - Local mental health reporting laws
   - User consent and privacy policies

3. **Ethical responsibility**: This system can save lives but also has serious consequences if misused

4. **Regular audits**: Review alert logs monthly to identify patterns and tune system

5. **Human oversight**: Alerts should be reviewed by trained professionals, not relied on blindly

---

## 🔐 Security & Privacy

- All alerts are logged in MongoDB (`crisis_alert_logs` collection)
- User IDs are pseudonymous
- Crisis text is stored securely
- Decision reasons provide audit trail
- No PII shared unless explicitly necessary for intervention

---

## 📞 Support & Feedback

If you notice:
- False positives (unnecessary alerts)
- Missed critical situations
- Cooldown too long/short
- Keyword gaps

→ Review logs in `crisis_alert_logs` collection and adjust parameters accordingly.

---

## Version History

- **v2.0** (Current): Ultra-conservative authority alerts with multi-layer verification
- **v1.0**: Always sent email on popup trigger (deprecated - too many false positives)

---

**Last Updated**: January 2025
**Maintained By**: Mental Health App Development Team
