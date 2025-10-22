from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
import socketio
import bcrypt
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configure Gemini AI
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-flash')

# Socket.IO setup
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '720'))

security = HTTPBearer()

# Create FastAPI app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Authentication Models
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    username: str
    password_hash: str
    wellness_stars: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Models
class MoodLogCreate(BaseModel):
    user_id: str
    mood_text: str

class MoodLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood_text: str
    ai_suggestion: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    username: str
    wellness_stars: int = 0

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    user_id: str
    username: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TherapistChatMessage(BaseModel):
    user_id: str
    message: str

class TherapistChatResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_message: str
    therapist_response: str
    crisis_detected: bool = False
    crisis_severity: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommunityCreate(BaseModel):
    name: str
    description: str
    community_type: str  # "public" or "private"
    password: Optional[str] = None
    creator_id: str

class Community(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    community_type: str
    password_hash: Optional[str] = None
    creator_id: str
    member_ids: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommunityJoin(BaseModel):
    user_id: str
    community_id: str
    password: Optional[str] = None

class CommunityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    community_type: str
    creator_id: str
    member_count: int
    is_member: bool = False
    created_at: datetime

# Crisis Support Models
class EmergencyContact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    phone: str
    relationship: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmergencyContactCreate(BaseModel):
    user_id: str
    name: str
    phone: str
    relationship: str
    email: Optional[str] = None

class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    email: Optional[str] = None

class SafetyPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    warning_signs: List[str] = []
    coping_strategies: List[str] = []
    contacts_to_call: List[str] = []
    professional_contacts: List[str] = []
    safe_environment_steps: List[str] = []
    reasons_to_live: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SafetyPlanCreate(BaseModel):
    user_id: str
    warning_signs: List[str] = []
    coping_strategies: List[str] = []
    contacts_to_call: List[str] = []
    professional_contacts: List[str] = []
    safe_environment_steps: List[str] = []
    reasons_to_live: List[str] = []

class CrisisDetectionResponse(BaseModel):
    is_crisis: bool
    severity: str  # "low", "medium", "high"
    detected_keywords: List[str]
    follow_up_question: Optional[str] = None

# Meditation & Breathing Exercise Models
class BreathingExercise(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    duration: int  # in seconds
    pattern: str  # e.g., "4-4-4-4" for box breathing
    description: str
    instructions: List[str]
    benefits: List[str]

class MeditationContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    duration: int  # in minutes
    category: str  # stress_relief, sleep, focus, anxiety
    description: str
    instructions: List[str]
    goal: str

class MeditationSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_type: str  # "breathing" or "meditation"
    content_id: str
    duration: int  # in seconds or minutes
    completed: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MeditationSessionStart(BaseModel):
    user_id: str
    session_type: str
    content_id: str
    duration: int

class MeditationSessionComplete(BaseModel):
    session_id: str

# Resource Library Models
class Resource(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    category: str  # conditions, techniques, videos, reading, myths
    subcategory: Optional[str] = None  # anxiety, depression, cbt, dbt, etc.
    content_type: str  # article, video, exercise, book, myth
    description: str
    content: str  # Full content/article text or exercise instructions
    author: Optional[str] = None
    source_url: Optional[str] = None  # External link for videos or articles
    duration_minutes: Optional[int] = None  # For videos or exercises
    difficulty: Optional[str] = None  # beginner, intermediate, advanced
    tags: List[str] = []
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    views: int = 0
    bookmarks: int = 0

class ResourceBookmark(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    resource_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResourceBookmarkCreate(BaseModel):
    user_id: str
    resource_id: str

# JWT Helper Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# API Routes
@api_router.get("/")
async def root():
    return {"message": "MoodMesh API - Mental Health Support Platform"}

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    try:
        # Check if username already exists
        existing_user = await db.users.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Validate username
        if len(user_data.username.strip()) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
        
        # Validate password
        if len(user_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
        # Hash password
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=user_data.username.strip(),
            password_hash=password_hash,
            wellness_stars=0
        )
        
        # Save to database
        doc = user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        
        # Create user profile for backward compatibility
        profile = UserProfile(
            user_id=user_id,
            username=user_data.username.strip(),
            wellness_stars=0
        )
        await db.user_profiles.insert_one(profile.model_dump())
        
        # Generate JWT token
        access_token = create_access_token({"user_id": user_id, "username": user_data.username.strip()})
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            username=user_data.username.strip()
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    try:
        # Find user
        user = await db.users.find_one({"username": user_data.username})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify password
        if not bcrypt.checkpw(user_data.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Generate JWT token
        access_token = create_access_token({"user_id": user['user_id'], "username": user['username']})
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user['user_id'],
            username=user['username']
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/verify")
async def verify_token_endpoint(current_user: dict = Depends(get_current_user)):
    return {
        "valid": True,
        "user_id": current_user['user_id'],
        "username": current_user['username']
    }

@api_router.post("/mood/log", response_model=MoodLog)
async def log_mood(mood_input: MoodLogCreate):
    try:
        # Generate AI coping strategy using Gemini Flash
        prompt = f"""You are a compassionate mental health assistant. A user is feeling: '{mood_input.mood_text}'.
        
        Provide a brief, personalized coping strategy (2-3 sentences) that includes:
        1. Validation of their feelings
        2. One specific actionable technique they can try right now
        
        Keep it warm, supportive, and practical."""
        
        response = model.generate_content(prompt)
        ai_suggestion = response.text.strip()
        
        # Create mood log
        mood_log = MoodLog(
            user_id=mood_input.user_id,
            mood_text=mood_input.mood_text,
            ai_suggestion=ai_suggestion
        )
        
        # Save to MongoDB
        doc = mood_log.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.mood_logs.insert_one(doc)
        
        # Update user wellness stars
        profile = await db.user_profiles.find_one({"user_id": mood_input.user_id})
        if profile:
            await db.user_profiles.update_one(
                {"user_id": mood_input.user_id},
                {"$inc": {"wellness_stars": 1}}
            )
        
        return mood_log
    except Exception as e:
        logging.error(f"Error logging mood: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/mood/logs/{user_id}", response_model=List[MoodLog])
async def get_mood_logs(user_id: str):
    logs = await db.mood_logs.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    for log in logs:
        if isinstance(log['timestamp'], str):
            log['timestamp'] = datetime.fromisoformat(log['timestamp'])
    return logs

@api_router.get("/mood/analytics/{user_id}")
async def get_mood_analytics(user_id: str):
    try:
        # Get all mood logs for the user
        logs = await db.mood_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        
        if not logs:
            return {
                "total_logs": 0,
                "mood_trend": [],
                "hourly_distribution": {},
                "common_emotions": [],
                "insights": [],
                "current_streak": 0,
                "longest_streak": 0
            }
        
        # Parse timestamps
        for log in logs:
            if isinstance(log['timestamp'], str):
                log['timestamp'] = datetime.fromisoformat(log['timestamp'])
        
        # Sort by timestamp
        logs.sort(key=lambda x: x['timestamp'])
        
        # 1. Total logs
        total_logs = len(logs)
        
        # 2. Mood trend by date (last 30 days)
        mood_trend = {}
        for log in logs:
            date_key = log['timestamp'].strftime('%Y-%m-%d')
            if date_key not in mood_trend:
                mood_trend[date_key] = 0
            mood_trend[date_key] += 1
        
        # Convert to list format for frontend
        trend_list = [{"date": date, "count": count} for date, count in sorted(mood_trend.items())]
        
        # 3. Hourly distribution (time of day patterns)
        hourly_dist = {}
        for log in logs:
            hour = log['timestamp'].hour
            if hour not in hourly_dist:
                hourly_dist[hour] = 0
            hourly_dist[hour] += 1
        
        # 4. Common emotions/keywords (extract from mood_text)
        all_words = []
        stop_words = {'i', 'am', 'feel', 'feeling', 'im', 'the', 'a', 'an', 'and', 'or', 'but', 'to', 'of', 'in', 'on', 'at', 'for', 'with', 'is', 'was', 'are', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'my', 'me', 'so', 'very', 'really', 'just', 'like', 'about', 'today', 'yesterday'}
        
        for log in logs:
            words = log['mood_text'].lower().split()
            filtered_words = [w.strip('.,!?;:') for w in words if len(w) > 3 and w.lower() not in stop_words]
            all_words.extend(filtered_words)
        
        # Count word frequency
        from collections import Counter
        word_counts = Counter(all_words)
        common_emotions = [{"word": word, "count": count} for word, count in word_counts.most_common(10)]
        
        # 5. Calculate streaks
        dates_logged = sorted(set(log['timestamp'].date() for log in logs))
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        today = datetime.now(timezone.utc).date()
        
        if dates_logged:
            # Current streak
            if dates_logged[-1] == today or dates_logged[-1] == today - timedelta(days=1):
                current_streak = 1
                for i in range(len(dates_logged) - 2, -1, -1):
                    if dates_logged[i] == dates_logged[i + 1] - timedelta(days=1):
                        current_streak += 1
                    else:
                        break
            
            # Longest streak
            for i in range(1, len(dates_logged)):
                if dates_logged[i] == dates_logged[i - 1] + timedelta(days=1):
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)
        
        # 6. Generate AI insights
        insights = []
        
        # Most active hour
        if hourly_dist:
            peak_hour = max(hourly_dist, key=hourly_dist.get)
            peak_hour_12 = peak_hour if peak_hour <= 12 else peak_hour - 12
            am_pm = "AM" if peak_hour < 12 else "PM"
            insights.append(f"You're most likely to log your mood around {peak_hour_12}:00 {am_pm}")
        
        # Recent activity
        recent_logs = [log for log in logs if log['timestamp'] >= datetime.now(timezone.utc) - timedelta(days=7)]
        if recent_logs:
            insights.append(f"You've logged {len(recent_logs)} moods in the past week. Great consistency!")
        
        # Common themes
        if common_emotions:
            top_emotion = common_emotions[0]['word']
            insights.append(f"'{top_emotion}' appears frequently in your mood logs. This might be a key theme to explore.")
        
        # Streak motivation
        if current_streak >= 3:
            insights.append(f"You're on a {current_streak}-day logging streak! Keep it up!")
        elif current_streak == 0 and longest_streak > 0:
            insights.append(f"Your longest streak was {longest_streak} days. You can beat that!")
        
        # Activity pattern
        if len(mood_trend) >= 7:
            recent_7_days = list(mood_trend.values())[-7:]
            avg_logs = sum(recent_7_days) / 7
            if avg_logs > 1:
                insights.append(f"You're averaging {avg_logs:.1f} mood logs per day. Self-reflection is powerful!")
        
        return {
            "total_logs": total_logs,
            "mood_trend": trend_list[-30:],  # Last 30 days
            "hourly_distribution": hourly_dist,
            "common_emotions": common_emotions,
            "insights": insights,
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }
    except Exception as e:
        logging.error(f"Error getting mood analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/achievements/{user_id}")
async def get_achievements(user_id: str):
    try:
        # Get user activity data
        mood_logs = await db.mood_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        therapist_chats = await db.therapist_chats.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        communities = await db.communities.find({"member_ids": user_id}, {"_id": 0}).to_list(1000)
        chat_messages = await db.chat_messages.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        
        # Parse timestamps for mood logs
        for log in mood_logs:
            if isinstance(log['timestamp'], str):
                log['timestamp'] = datetime.fromisoformat(log['timestamp'])
        
        mood_logs.sort(key=lambda x: x['timestamp'])
        
        # Calculate statistics
        total_mood_logs = len(mood_logs)
        total_therapist_sessions = len(therapist_chats)
        total_communities_joined = len(communities)
        total_community_messages = len(chat_messages)
        
        # Calculate streaks
        dates_logged = sorted(set(log['timestamp'].date() for log in mood_logs))
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        today = datetime.now(timezone.utc).date()
        
        if dates_logged:
            # Current streak
            if dates_logged[-1] == today or dates_logged[-1] == today - timedelta(days=1):
                current_streak = 1
                for i in range(len(dates_logged) - 2, -1, -1):
                    if dates_logged[i] == dates_logged[i + 1] - timedelta(days=1):
                        current_streak += 1
                    else:
                        break
            
            # Longest streak
            for i in range(1, len(dates_logged)):
                if dates_logged[i] == dates_logged[i - 1] + timedelta(days=1):
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)
        
        # Calculate time patterns
        early_bird_count = sum(1 for log in mood_logs if 5 <= log['timestamp'].hour < 9)
        night_owl_count = sum(1 for log in mood_logs if 22 <= log['timestamp'].hour or log['timestamp'].hour < 5)
        
        # Define all achievements
        achievements = [
            # Mood Logging Achievements
            {
                "id": "first_step",
                "name": "First Step",
                "description": "Log your first mood",
                "icon": "🌱",
                "category": "mood_logging",
                "tier": "bronze",
                "progress": min(total_mood_logs, 1),
                "target": 1,
                "earned": total_mood_logs >= 1
            },
            {
                "id": "getting_started",
                "name": "Getting Started",
                "description": "Log 5 moods",
                "icon": "🌿",
                "category": "mood_logging",
                "tier": "bronze",
                "progress": min(total_mood_logs, 5),
                "target": 5,
                "earned": total_mood_logs >= 5
            },
            {
                "id": "committed",
                "name": "Committed",
                "description": "Log 10 moods",
                "icon": "🌳",
                "category": "mood_logging",
                "tier": "silver",
                "progress": min(total_mood_logs, 10),
                "target": 10,
                "earned": total_mood_logs >= 10
            },
            {
                "id": "dedicated",
                "name": "Dedicated",
                "description": "Log 25 moods",
                "icon": "🎋",
                "category": "mood_logging",
                "tier": "silver",
                "progress": min(total_mood_logs, 25),
                "target": 25,
                "earned": total_mood_logs >= 25
            },
            {
                "id": "wellness_champion",
                "name": "Wellness Champion",
                "description": "Log 50 moods",
                "icon": "🏆",
                "category": "mood_logging",
                "tier": "gold",
                "progress": min(total_mood_logs, 50),
                "target": 50,
                "earned": total_mood_logs >= 50
            },
            {
                "id": "mindfulness_master",
                "name": "Mindfulness Master",
                "description": "Log 100 moods",
                "icon": "👑",
                "category": "mood_logging",
                "tier": "platinum",
                "progress": min(total_mood_logs, 100),
                "target": 100,
                "earned": total_mood_logs >= 100
            },
            
            # Streak Achievements
            {
                "id": "streak_starter",
                "name": "Streak Starter",
                "description": "Maintain a 3-day streak",
                "icon": "🔥",
                "category": "streaks",
                "tier": "bronze",
                "progress": min(longest_streak, 3),
                "target": 3,
                "earned": longest_streak >= 3
            },
            {
                "id": "week_warrior",
                "name": "Week Warrior",
                "description": "Maintain a 7-day streak",
                "icon": "⚡",
                "category": "streaks",
                "tier": "silver",
                "progress": min(longest_streak, 7),
                "target": 7,
                "earned": longest_streak >= 7
            },
            {
                "id": "consistency_king",
                "name": "Consistency King",
                "description": "Maintain a 14-day streak",
                "icon": "💪",
                "category": "streaks",
                "tier": "gold",
                "progress": min(longest_streak, 14),
                "target": 14,
                "earned": longest_streak >= 14
            },
            {
                "id": "month_master",
                "name": "Month Master",
                "description": "Maintain a 30-day streak",
                "icon": "🎯",
                "category": "streaks",
                "tier": "platinum",
                "progress": min(longest_streak, 30),
                "target": 30,
                "earned": longest_streak >= 30
            },
            
            # AI Therapist Achievements
            {
                "id": "seeking_help",
                "name": "Seeking Help",
                "description": "Start your first therapy session",
                "icon": "🤝",
                "category": "therapy",
                "tier": "bronze",
                "progress": min(total_therapist_sessions, 1),
                "target": 1,
                "earned": total_therapist_sessions >= 1
            },
            {
                "id": "regular_visitor",
                "name": "Regular Visitor",
                "description": "Complete 5 therapy sessions",
                "icon": "💬",
                "category": "therapy",
                "tier": "silver",
                "progress": min(total_therapist_sessions, 5),
                "target": 5,
                "earned": total_therapist_sessions >= 5
            },
            {
                "id": "therapy_advocate",
                "name": "Therapy Advocate",
                "description": "Complete 10 therapy sessions",
                "icon": "💙",
                "category": "therapy",
                "tier": "gold",
                "progress": min(total_therapist_sessions, 10),
                "target": 10,
                "earned": total_therapist_sessions >= 10
            },
            
            # Community Achievements
            {
                "id": "community_member",
                "name": "Community Member",
                "description": "Join your first community",
                "icon": "👥",
                "category": "community",
                "tier": "bronze",
                "progress": min(total_communities_joined, 1),
                "target": 1,
                "earned": total_communities_joined >= 1
            },
            {
                "id": "social_butterfly",
                "name": "Social Butterfly",
                "description": "Send 10 community messages",
                "icon": "🦋",
                "category": "community",
                "tier": "silver",
                "progress": min(total_community_messages, 10),
                "target": 10,
                "earned": total_community_messages >= 10
            },
            {
                "id": "support_giver",
                "name": "Support Giver",
                "description": "Send 50 community messages",
                "icon": "❤️",
                "category": "community",
                "tier": "gold",
                "progress": min(total_community_messages, 50),
                "target": 50,
                "earned": total_community_messages >= 50
            },
            
            # Special Achievements
            {
                "id": "early_bird",
                "name": "Early Bird",
                "description": "Log 10 moods in the morning (5-9 AM)",
                "icon": "🌅",
                "category": "special",
                "tier": "silver",
                "progress": min(early_bird_count, 10),
                "target": 10,
                "earned": early_bird_count >= 10
            },
            {
                "id": "night_owl",
                "name": "Night Owl",
                "description": "Log 10 moods at night (10 PM - 5 AM)",
                "icon": "🦉",
                "category": "special",
                "tier": "silver",
                "progress": min(night_owl_count, 10),
                "target": 10,
                "earned": night_owl_count >= 10
            },
            {
                "id": "explorer",
                "name": "Explorer",
                "description": "Use all 4 main features (Mood Log, Analytics, AI Therapist, Communities)",
                "icon": "🧭",
                "category": "special",
                "tier": "gold",
                "progress": sum([
                    1 if total_mood_logs > 0 else 0,
                    1 if total_therapist_sessions > 0 else 0,
                    1 if total_communities_joined > 0 else 0,
                    1  # Analytics (they're viewing this)
                ]),
                "target": 4,
                "earned": total_mood_logs > 0 and total_therapist_sessions > 0 and total_communities_joined > 0
            }
        ]
        
        # Separate earned and locked achievements
        earned_achievements = [a for a in achievements if a["earned"]]
        locked_achievements = [a for a in achievements if not a["earned"]]
        
        # Calculate total stats
        total_achievements = len(achievements)
        earned_count = len(earned_achievements)
        completion_percentage = int((earned_count / total_achievements) * 100)
        
        return {
            "earned": earned_achievements,
            "locked": locked_achievements,
            "total_achievements": total_achievements,
            "earned_count": earned_count,
            "completion_percentage": completion_percentage,
            "stats": {
                "total_mood_logs": total_mood_logs,
                "total_therapist_sessions": total_therapist_sessions,
                "total_communities_joined": total_communities_joined,
                "total_community_messages": total_community_messages,
                "current_streak": current_streak,
                "longest_streak": longest_streak
            }
        }
    except Exception as e:
        logging.error(f"Error getting achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/profile/create", response_model=UserProfile)
async def create_profile(username: str, user_id: Optional[str] = None):
    if not user_id:
        user_id = str(uuid.uuid4())
    
    profile = UserProfile(user_id=user_id, username=username, wellness_stars=0)
    doc = profile.model_dump()
    
    # Check if profile exists
    existing = await db.user_profiles.find_one({"user_id": user_id})
    if existing:
        return UserProfile(**existing)
    
    await db.user_profiles.insert_one(doc)
    return profile

@api_router.get("/profile/{user_id}", response_model=UserProfile)
async def get_profile(user_id: str):
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(**profile)

@api_router.get("/chat/messages/{room_id}", response_model=List[ChatMessage])
async def get_chat_messages(room_id: str):
    messages = await db.chat_messages.find({"room_id": room_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    for msg in messages:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    return messages

@api_router.post("/therapist/chat", response_model=TherapistChatResponse)
async def therapist_chat(chat_input: TherapistChatMessage):
    try:
        # Check for crisis keywords first
        crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end my life', 'want to die', 
            'self-harm', 'hurt myself', 'cut myself', 'harm myself', 
            'no reason to live', 'better off dead', "can't go on", 
            'end it all', 'take my life', 'overdose'
        ]
        
        message_lower = chat_input.message.lower()
        detected_keywords = [keyword for keyword in crisis_keywords if keyword in message_lower]
        crisis_detected = len(detected_keywords) > 0
        crisis_severity = None
        
        if crisis_detected:
            # Determine severity
            high_severity_keywords = ['kill myself', 'end my life', 'suicide', 'suicidal', 'take my life', 'overdose']
            medium_severity_keywords = ['want to die', 'better off dead', 'no reason to live', "can't go on"]
            
            if any(keyword in message_lower for keyword in high_severity_keywords):
                crisis_severity = "high"
            elif any(keyword in message_lower for keyword in medium_severity_keywords):
                crisis_severity = "medium"
            else:
                crisis_severity = "low"
        
        # System prompt to ensure it acts as a professional therapist
        system_instruction = """You are a professional, licensed therapist specializing in mental health support. 
        
STRICT GUIDELINES:
1. ONLY respond to mental health, emotional wellness, therapy, and psychology-related questions
2. If the user asks about anything unrelated (politics, sports, coding, general knowledge, etc.), politely redirect them back to mental health topics
3. Use empathetic, warm, and professional language
4. Provide evidence-based therapeutic techniques when appropriate
5. Acknowledge feelings and validate emotions
6. Ask clarifying questions to understand the user better
7. Never diagnose conditions - only provide support and coping strategies
8. If a question is about serious self-harm or emergency, acknowledge their pain, ask gentle follow-up questions to understand their current state, and the system will show crisis resources

Response format:
- Start with empathy and validation
- Provide therapeutic insights
- Ask clarifying questions when appropriate
- Keep responses conversational (3-4 sentences)

Remember: You are ONLY a mental health therapist. Politely decline any non-therapy topics."""

        # Get conversation history for context
        history = await db.therapist_chats.find(
            {"user_id": chat_input.user_id}
        ).sort("timestamp", -1).limit(5).to_list(5)
        
        # Build conversation context
        conversation_context = ""
        if history:
            conversation_context = "\n\nRecent conversation history:\n"
            for chat in reversed(history):
                conversation_context += f"User: {chat['user_message']}\nTherapist: {chat['therapist_response']}\n\n"
        
        # Combine system instruction with context
        full_prompt = f"""{system_instruction}

{conversation_context}
Current user message: {chat_input.message}

Provide a therapeutic response:"""
        
        response = model.generate_content(full_prompt)
        therapist_response = response.text.strip()
        
        # Create chat record
        chat_record = TherapistChatResponse(
            user_id=chat_input.user_id,
            user_message=chat_input.message,
            therapist_response=therapist_response,
            crisis_detected=crisis_detected,
            crisis_severity=crisis_severity
        )
        
        # Save to MongoDB
        doc = chat_record.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.therapist_chats.insert_one(doc)
        
        return chat_record
    except Exception as e:
        logging.error(f"Error in therapist chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/therapist/history/{user_id}", response_model=List[TherapistChatResponse])
async def get_therapist_history(user_id: str):
    history = await db.therapist_chats.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    for chat in history:
        if isinstance(chat['timestamp'], str):
            chat['timestamp'] = datetime.fromisoformat(chat['timestamp'])
    return history

# Community Routes
@api_router.post("/communities/create", response_model=Community)
async def create_community(community_data: CommunityCreate):
    try:
        # Validate community type
        if community_data.community_type not in ["public", "private"]:
            raise HTTPException(status_code=400, detail="Invalid community type. Must be 'public' or 'private'")
        
        # Validate password for private communities
        if community_data.community_type == "private" and not community_data.password:
            raise HTTPException(status_code=400, detail="Password is required for private communities")
        
        # Hash password if private
        password_hash = None
        if community_data.community_type == "private" and community_data.password:
            password_hash = bcrypt.hashpw(community_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create community
        community = Community(
            name=community_data.name,
            description=community_data.description,
            community_type=community_data.community_type,
            password_hash=password_hash,
            creator_id=community_data.creator_id,
            member_ids=[community_data.creator_id]  # Creator is automatically a member
        )
        
        doc = community.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.communities.insert_one(doc)
        
        return community
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating community: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/communities/list/{user_id}", response_model=List[CommunityResponse])
async def list_communities(user_id: str):
    try:
        # Get all public communities + private communities user is a member of
        communities = await db.communities.find({}, {"_id": 0}).to_list(1000)
        
        response_list = []
        for comm in communities:
            # Parse timestamp
            if isinstance(comm['created_at'], str):
                comm['created_at'] = datetime.fromisoformat(comm['created_at'])
            
            # Only show public communities OR private communities user is a member of
            if comm['community_type'] == 'public' or user_id in comm.get('member_ids', []):
                is_member = user_id in comm.get('member_ids', [])
                response_list.append(CommunityResponse(
                    id=comm['id'],
                    name=comm['name'],
                    description=comm['description'],
                    community_type=comm['community_type'],
                    creator_id=comm['creator_id'],
                    member_count=len(comm.get('member_ids', [])),
                    is_member=is_member,
                    created_at=comm['created_at']
                ))
        
        return response_list
    except Exception as e:
        logging.error(f"Error listing communities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/communities/join")
async def join_community(join_data: CommunityJoin):
    try:
        # Get community
        community = await db.communities.find_one({"id": join_data.community_id}, {"_id": 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if already a member
        if join_data.user_id in community.get('member_ids', []):
            return {"message": "Already a member", "success": True}
        
        # Verify password for private communities
        if community['community_type'] == 'private':
            if not join_data.password:
                raise HTTPException(status_code=400, detail="Password is required for private communities")
            
            if not bcrypt.checkpw(join_data.password.encode('utf-8'), community['password_hash'].encode('utf-8')):
                raise HTTPException(status_code=403, detail="Incorrect password")
        
        # Add user to member_ids
        await db.communities.update_one(
            {"id": join_data.community_id},
            {"$addToSet": {"member_ids": join_data.user_id}}
        )
        
        return {"message": "Successfully joined community", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error joining community: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/communities/{community_id}/check-membership/{user_id}")
async def check_membership(community_id: str, user_id: str):
    try:
        community = await db.communities.find_one({"id": community_id}, {"_id": 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        is_member = user_id in community.get('member_ids', [])
        return {
            "is_member": is_member,
            "community_name": community['name'],
            "community_type": community['community_type']
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error checking membership: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/communities/user/{user_id}", response_model=List[CommunityResponse])
async def get_user_communities(user_id: str):
    try:
        # Get communities where user is a member
        communities = await db.communities.find(
            {"member_ids": user_id},
            {"_id": 0}
        ).to_list(1000)
        
        response_list = []
        for comm in communities:
            if isinstance(comm['created_at'], str):
                comm['created_at'] = datetime.fromisoformat(comm['created_at'])
            
            response_list.append(CommunityResponse(
                id=comm['id'],
                name=comm['name'],
                description=comm['description'],
                community_type=comm['community_type'],
                creator_id=comm['creator_id'],
                member_count=len(comm.get('member_ids', [])),
                is_member=True,
                created_at=comm['created_at']
            ))
        
        return response_list
    except Exception as e:
        logging.error(f"Error getting user communities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/communities/{community_id}/{user_id}")
async def delete_community(community_id: str, user_id: str):
    try:
        # Get community
        community = await db.communities.find_one({"id": community_id}, {"_id": 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is creator
        if community['creator_id'] != user_id:
            raise HTTPException(status_code=403, detail="Only the creator can delete this community")
        
        # Delete community
        await db.communities.delete_one({"id": community_id})
        
        # Delete all messages in this community
        await db.chat_messages.delete_many({"room_id": community_id})
        
        return {"message": "Community deleted successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting community: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/communities/{community_id}/remove-member")
async def remove_member(community_id: str, creator_id: str, member_id: str):
    try:
        # Get community
        community = await db.communities.find_one({"id": community_id}, {"_id": 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is creator
        if community['creator_id'] != creator_id:
            raise HTTPException(status_code=403, detail="Only the creator can remove members")
        
        # Can't remove creator
        if member_id == creator_id:
            raise HTTPException(status_code=400, detail="Creator cannot be removed")
        
        # Remove member
        await db.communities.update_one(
            {"id": community_id},
            {"$pull": {"member_ids": member_id}}
        )
        
        return {"message": "Member removed successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error removing member: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/communities/{community_id}/leave")
async def leave_community(community_id: str, user_id: str):
    try:
        # Get community
        community = await db.communities.find_one({"id": community_id}, {"_id": 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Creator cannot leave their own community
        if community['creator_id'] == user_id:
            raise HTTPException(status_code=400, detail="Creator cannot leave. Delete the community instead.")
        
        # Remove member
        await db.communities.update_one(
            {"id": community_id},
            {"$pull": {"member_ids": user_id}}
        )
        
        return {"message": "Left community successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error leaving community: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Crisis Support Routes
@api_router.post("/crisis/safety-plan", response_model=SafetyPlan)
async def create_or_update_safety_plan(plan_data: SafetyPlanCreate):
    try:
        # Check if safety plan already exists
        existing_plan = await db.safety_plans.find_one({"user_id": plan_data.user_id}, {"_id": 0})
        
        if existing_plan:
            # Update existing plan
            update_data = plan_data.model_dump()
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            await db.safety_plans.update_one(
                {"user_id": plan_data.user_id},
                {"$set": update_data}
            )
            
            updated_plan = await db.safety_plans.find_one({"user_id": plan_data.user_id}, {"_id": 0})
            if isinstance(updated_plan['created_at'], str):
                updated_plan['created_at'] = datetime.fromisoformat(updated_plan['created_at'])
            if isinstance(updated_plan['updated_at'], str):
                updated_plan['updated_at'] = datetime.fromisoformat(updated_plan['updated_at'])
            
            return SafetyPlan(**updated_plan)
        else:
            # Create new safety plan
            safety_plan = SafetyPlan(**plan_data.model_dump())
            doc = safety_plan.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            
            await db.safety_plans.insert_one(doc)
            return safety_plan
    except Exception as e:
        logging.error(f"Error creating/updating safety plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crisis/safety-plan/{user_id}", response_model=Optional[SafetyPlan])
async def get_safety_plan(user_id: str):
    try:
        plan = await db.safety_plans.find_one({"user_id": user_id}, {"_id": 0})
        if not plan:
            return None
        
        if isinstance(plan['created_at'], str):
            plan['created_at'] = datetime.fromisoformat(plan['created_at'])
        if isinstance(plan['updated_at'], str):
            plan['updated_at'] = datetime.fromisoformat(plan['updated_at'])
        
        return SafetyPlan(**plan)
    except Exception as e:
        logging.error(f"Error getting safety plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crisis/emergency-contacts", response_model=EmergencyContact)
async def create_emergency_contact(contact_data: EmergencyContactCreate):
    try:
        contact = EmergencyContact(**contact_data.model_dump())
        doc = contact.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        
        await db.emergency_contacts.insert_one(doc)
        return contact
    except Exception as e:
        logging.error(f"Error creating emergency contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crisis/emergency-contacts/{user_id}", response_model=List[EmergencyContact])
async def get_emergency_contacts(user_id: str):
    try:
        contacts = await db.emergency_contacts.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        for contact in contacts:
            if isinstance(contact['created_at'], str):
                contact['created_at'] = datetime.fromisoformat(contact['created_at'])
        
        return [EmergencyContact(**contact) for contact in contacts]
    except Exception as e:
        logging.error(f"Error getting emergency contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/crisis/emergency-contacts/{contact_id}", response_model=EmergencyContact)
async def update_emergency_contact(contact_id: str, update_data: EmergencyContactUpdate):
    try:
        contact = await db.emergency_contacts.find_one({"id": contact_id}, {"_id": 0})
        if not contact:
            raise HTTPException(status_code=404, detail="Emergency contact not found")
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if update_dict:
            await db.emergency_contacts.update_one(
                {"id": contact_id},
                {"$set": update_dict}
            )
        
        updated_contact = await db.emergency_contacts.find_one({"id": contact_id}, {"_id": 0})
        if isinstance(updated_contact['created_at'], str):
            updated_contact['created_at'] = datetime.fromisoformat(updated_contact['created_at'])
        
        return EmergencyContact(**updated_contact)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating emergency contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/crisis/emergency-contacts/{contact_id}")
async def delete_emergency_contact(contact_id: str):
    try:
        result = await db.emergency_contacts.delete_one({"id": contact_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Emergency contact not found")
        
        return {"message": "Emergency contact deleted successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting emergency contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crisis/detect", response_model=CrisisDetectionResponse)
async def detect_crisis(message: str):
    try:
        # Crisis keywords to detect
        crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end my life', 'want to die', 
            'self-harm', 'hurt myself', 'cut myself', 'harm myself', 
            'no reason to live', 'better off dead', "can't go on", 
            'end it all', 'take my life', 'overdose'
        ]
        
        message_lower = message.lower()
        detected = [keyword for keyword in crisis_keywords if keyword in message_lower]
        
        is_crisis = len(detected) > 0
        severity = "low"
        follow_up = None
        
        if is_crisis:
            # Determine severity based on keywords
            high_severity_keywords = ['kill myself', 'end my life', 'suicide', 'suicidal', 'take my life', 'overdose']
            medium_severity_keywords = ['want to die', 'better off dead', 'no reason to live', "can't go on"]
            
            if any(keyword in message_lower for keyword in high_severity_keywords):
                severity = "high"
                follow_up = "I'm really concerned about what you're sharing. Are you having thoughts of hurting yourself right now? It's important that we get you immediate support."
            elif any(keyword in message_lower for keyword in medium_severity_keywords):
                severity = "medium"
                follow_up = "I hear that you're going through a really difficult time. Have you been having thoughts about ending your life? I want to make sure you have the support you need."
            else:
                severity = "low"
                follow_up = "Thank you for sharing that with me. Can you tell me more about what you're experiencing? I want to understand better so I can provide you with the right support."
        
        return CrisisDetectionResponse(
            is_crisis=is_crisis,
            severity=severity,
            detected_keywords=detected,
            follow_up_question=follow_up
        )
    except Exception as e:
        logging.error(f"Error detecting crisis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Meditation & Breathing Exercise Routes

# Seed initial data for breathing exercises and meditation sessions
BREATHING_EXERCISES = [
    {
        "id": "box_breathing",
        "name": "Box Breathing",
        "duration": 240,  # 4 minutes
        "pattern": "4-4-4-4",
        "description": "A simple yet powerful technique used by Navy SEALs to stay calm under pressure",
        "instructions": [
            "Breathe in through your nose for 4 seconds",
            "Hold your breath for 4 seconds",
            "Exhale through your mouth for 4 seconds",
            "Hold empty for 4 seconds",
            "Repeat the cycle"
        ],
        "benefits": [
            "Reduces stress and anxiety",
            "Improves focus and concentration",
            "Lowers blood pressure",
            "Promotes relaxation"
        ]
    },
    {
        "id": "breathing_478",
        "name": "4-7-8 Breathing",
        "duration": 180,  # 3 minutes
        "pattern": "4-7-8",
        "description": "A natural tranquilizer for the nervous system, perfect before sleep",
        "instructions": [
            "Breathe in quietly through your nose for 4 seconds",
            "Hold your breath for 7 seconds",
            "Exhale completely through your mouth for 8 seconds",
            "This completes one breath cycle",
            "Repeat 3-4 times"
        ],
        "benefits": [
            "Promotes better sleep",
            "Reduces anxiety",
            "Manages stress responses",
            "Calms racing thoughts"
        ]
    },
    {
        "id": "deep_belly",
        "name": "Deep Belly Breathing",
        "duration": 300,  # 5 minutes
        "pattern": "slow-deep",
        "description": "Diaphragmatic breathing to activate your body's relaxation response",
        "instructions": [
            "Place one hand on your chest and one on your belly",
            "Breathe in slowly through your nose, feeling your belly rise",
            "Your chest should remain relatively still",
            "Exhale slowly through your mouth",
            "Continue for 5-10 minutes"
        ],
        "benefits": [
            "Activates the parasympathetic nervous system",
            "Reduces muscle tension",
            "Improves oxygen flow",
            "Decreases heart rate"
        ]
    },
    {
        "id": "alternate_nostril",
        "name": "Alternate Nostril Breathing",
        "duration": 300,  # 5 minutes
        "pattern": "alternate",
        "description": "A yogic breathing technique to balance the mind and body",
        "instructions": [
            "Sit comfortably with your spine straight",
            "Close your right nostril with your right thumb",
            "Breathe in through your left nostril",
            "Close your left nostril with your ring finger",
            "Release your thumb and breathe out through your right nostril",
            "Breathe in through the right nostril",
            "Close the right nostril and breathe out through the left",
            "This completes one cycle"
        ],
        "benefits": [
            "Balances left and right brain hemispheres",
            "Reduces stress and anxiety",
            "Improves respiratory function",
            "Enhances mental clarity"
        ]
    },
    {
        "id": "resonant_breathing",
        "name": "Resonant Breathing",
        "duration": 300,  # 5 minutes
        "pattern": "5-5",
        "description": "Breathe at 5 breaths per minute to achieve coherence",
        "instructions": [
            "Breathe in for 5 seconds",
            "Breathe out for 5 seconds",
            "Keep the breathing smooth and even",
            "Continue for 5-10 minutes",
            "Feel your body reach a state of coherence"
        ],
        "benefits": [
            "Maximizes heart rate variability",
            "Reduces stress hormones",
            "Improves emotional regulation",
            "Enhances overall well-being"
        ]
    }
]

MEDITATION_SESSIONS = [
    {
        "id": "stress_relief_5",
        "title": "Quick Stress Relief",
        "duration": 5,
        "category": "stress_relief",
        "description": "A brief meditation to release tension and find calm in the middle of your day",
        "instructions": [
            "Find a comfortable seated position",
            "Close your eyes gently",
            "Take 3 deep breaths, releasing tension with each exhale",
            "Scan your body from head to toe, noticing areas of tension",
            "With each breath, imagine tension melting away",
            "Visualize yourself in a peaceful place",
            "When you're ready, slowly open your eyes"
        ],
        "goal": "Release stress and tension quickly"
    },
    {
        "id": "stress_relief_10",
        "title": "Deep Stress Release",
        "duration": 10,
        "category": "stress_relief",
        "description": "A deeper meditation to let go of stress and restore inner peace",
        "instructions": [
            "Settle into a comfortable position",
            "Close your eyes and take a few natural breaths",
            "Notice the weight of your body being supported",
            "Begin to scan your body, releasing tension as you go",
            "Acknowledge any stressful thoughts without judgment",
            "Imagine stress leaving your body with each exhale",
            "Visualize a wave of calm washing over you",
            "Rest in this peaceful state",
            "Gently return when you're ready"
        ],
        "goal": "Deep relaxation and stress relief"
    },
    {
        "id": "sleep_10",
        "title": "Peaceful Sleep Preparation",
        "duration": 10,
        "category": "sleep",
        "description": "Ease into a restful state perfect for falling asleep",
        "instructions": [
            "Lie down in a comfortable position",
            "Take 3 slow, deep breaths",
            "Allow your body to feel heavy and relaxed",
            "Release the events of the day",
            "Imagine yourself in a safe, comfortable place",
            "Let your breath become natural and effortless",
            "Allow thoughts to drift by like clouds",
            "Feel yourself sinking deeper into relaxation",
            "Drift off whenever you're ready"
        ],
        "goal": "Prepare body and mind for restful sleep"
    },
    {
        "id": "sleep_20",
        "title": "Deep Sleep Meditation",
        "duration": 20,
        "category": "sleep",
        "description": "A longer meditation for deep relaxation and quality sleep",
        "instructions": [
            "Lie comfortably with your arms by your sides",
            "Close your eyes and take several deep breaths",
            "Progressively relax each part of your body",
            "Starting from your toes, move slowly upward",
            "Release all tension, all thoughts, all worries",
            "Imagine yourself floating on calm water",
            "Your breathing is slow and natural",
            "You are safe, peaceful, and ready for sleep",
            "Let go completely and drift into sleep"
        ],
        "goal": "Achieve deep relaxation for quality sleep"
    },
    {
        "id": "focus_5",
        "title": "Quick Focus Boost",
        "duration": 5,
        "category": "focus",
        "description": "Sharpen your concentration and mental clarity",
        "instructions": [
            "Sit upright with your spine straight",
            "Close your eyes and take 3 energizing breaths",
            "Bring your attention to your breath",
            "Count each inhale and exhale up to 10",
            "If your mind wanders, gently return to counting",
            "Feel your mind becoming clearer and more focused",
            "Open your eyes feeling alert and ready"
        ],
        "goal": "Enhance focus and mental clarity"
    },
    {
        "id": "focus_15",
        "title": "Deep Focus Training",
        "duration": 15,
        "category": "focus",
        "description": "Train your mind for sustained concentration and productivity",
        "instructions": [
            "Sit in a comfortable but alert position",
            "Set an intention for your focus practice",
            "Begin by following your natural breath",
            "Notice sensations of breathing in detail",
            "When your mind wanders, note 'thinking' and return",
            "Gradually your concentration will deepen",
            "Feel your mental muscles strengthening",
            "Practice patience with yourself",
            "Return feeling mentally sharp and ready"
        ],
        "goal": "Build sustained concentration skills"
    },
    {
        "id": "anxiety_5",
        "title": "Anxiety SOS",
        "duration": 5,
        "category": "anxiety",
        "description": "Quick relief from anxious feelings and racing thoughts",
        "instructions": [
            "Find a quiet space and sit or lie down",
            "Place one hand on your heart, one on your belly",
            "Take a slow, deep breath in through your nose",
            "Hold for a moment, then exhale slowly",
            "Focus on the physical sensations of breathing",
            "Tell yourself: 'This feeling will pass'",
            "Continue breathing slowly and deeply",
            "Feel your nervous system calming down"
        ],
        "goal": "Rapid anxiety relief and grounding"
    },
    {
        "id": "anxiety_10",
        "title": "Calm Your Anxious Mind",
        "duration": 10,
        "category": "anxiety",
        "description": "Soothe anxiety and find your center of calm",
        "instructions": [
            "Sit comfortably and close your eyes",
            "Notice your anxious thoughts without judgment",
            "Acknowledge: 'I feel anxious, and that's okay'",
            "Begin taking slow, calming breaths",
            "Imagine breathing in peace, breathing out worry",
            "Visualize a safe, peaceful place",
            "Feel yourself becoming grounded and stable",
            "Know that you have the strength to handle this",
            "Open your eyes feeling more centered"
        ],
        "goal": "Reduce anxiety and restore calm"
    },
    {
        "id": "anxiety_15",
        "title": "Deep Anxiety Release",
        "duration": 15,
        "category": "anxiety",
        "description": "A comprehensive practice to release deep anxiety",
        "instructions": [
            "Find a comfortable, safe space",
            "Begin with several grounding breaths",
            "Scan your body for where you hold anxiety",
            "Breathe into those areas with compassion",
            "Acknowledge your worries without fighting them",
            "Imagine releasing anxiety with each exhale",
            "Practice self-compassion and understanding",
            "Visualize yourself calm and capable",
            "Build a sense of inner safety and peace",
            "Return feeling lighter and more grounded"
        ],
        "goal": "Deep release of anxiety and worry"
    },
    {
        "id": "morning_energy",
        "title": "Morning Energy Meditation",
        "duration": 10,
        "category": "focus",
        "description": "Start your day with clarity and positive energy",
        "instructions": [
            "Sit upright in a comfortable position",
            "Take 3 deep, energizing breaths",
            "Set a positive intention for your day",
            "Visualize your day going well",
            "Feel gratitude for the new day",
            "Imagine energy flowing through your body",
            "See yourself handling challenges with ease",
            "Open your eyes feeling energized and ready"
        ],
        "goal": "Energize and prepare for a positive day"
    }
]

@api_router.get("/meditation/exercises")
async def get_breathing_exercises():
    """Get all available breathing exercises"""
    try:
        return {"exercises": BREATHING_EXERCISES}
    except Exception as e:
        logging.error(f"Error getting breathing exercises: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/meditation/sessions")
async def get_meditation_sessions(category: Optional[str] = None):
    """Get all meditation sessions, optionally filtered by category"""
    try:
        sessions = MEDITATION_SESSIONS
        if category:
            sessions = [s for s in sessions if s['category'] == category]
        return {"sessions": sessions}
    except Exception as e:
        logging.error(f"Error getting meditation sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/meditation/start", response_model=MeditationSession)
async def start_meditation_session(session_data: MeditationSessionStart):
    """Start a new meditation or breathing session"""
    try:
        session = MeditationSession(
            user_id=session_data.user_id,
            session_type=session_data.session_type,
            content_id=session_data.content_id,
            duration=session_data.duration,
            completed=False
        )
        
        doc = session.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.meditation_sessions.insert_one(doc)
        
        return session
    except Exception as e:
        logging.error(f"Error starting meditation session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/meditation/complete")
async def complete_meditation_session(completion_data: MeditationSessionComplete):
    """Mark a meditation session as complete and award wellness stars"""
    try:
        # Update session to completed
        result = await db.meditation_sessions.update_one(
            {"id": completion_data.session_id},
            {"$set": {"completed": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get session to get user_id
        session = await db.meditation_sessions.find_one({"id": completion_data.session_id}, {"_id": 0})
        
        if session:
            # Award wellness stars
            await db.user_profiles.update_one(
                {"user_id": session['user_id']},
                {"$inc": {"wellness_stars": 2}}  # Award 2 stars for completing a session
            )
        
        return {"message": "Session completed successfully", "stars_earned": 2}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error completing meditation session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/meditation/progress/{user_id}")
async def get_meditation_progress(user_id: str):
    """Get user's meditation progress and statistics"""
    try:
        # Get all completed sessions
        sessions = await db.meditation_sessions.find(
            {"user_id": user_id, "completed": True},
            {"_id": 0}
        ).to_list(1000)
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_minutes": 0,
                "breathing_sessions": 0,
                "meditation_sessions": 0,
                "favorite_category": None,
                "current_streak": 0,
                "recent_sessions": []
            }
        
        # Parse timestamps
        for session in sessions:
            if isinstance(session['timestamp'], str):
                session['timestamp'] = datetime.fromisoformat(session['timestamp'])
        
        # Sort by timestamp
        sessions.sort(key=lambda x: x['timestamp'])
        
        # Calculate statistics
        total_sessions = len(sessions)
        breathing_sessions = len([s for s in sessions if s['session_type'] == 'breathing'])
        meditation_sessions = len([s for s in sessions if s['session_type'] == 'meditation'])
        
        # Calculate total minutes
        total_seconds = sum(s['duration'] for s in sessions)
        total_minutes = total_seconds // 60
        
        # Find favorite category
        meditation_only = [s for s in sessions if s['session_type'] == 'meditation']
        if meditation_only:
            # Get content_id categories
            categories = []
            for s in meditation_only:
                content = next((m for m in MEDITATION_SESSIONS if m['id'] == s['content_id']), None)
                if content:
                    categories.append(content['category'])
            
            if categories:
                from collections import Counter
                category_counts = Counter(categories)
                favorite_category = category_counts.most_common(1)[0][0]
            else:
                favorite_category = None
        else:
            favorite_category = None
        
        # Calculate streak (consecutive days)
        dates_practiced = sorted(set(s['timestamp'].date() for s in sessions))
        current_streak = 0
        today = datetime.now(timezone.utc).date()
        
        if dates_practiced:
            if dates_practiced[-1] == today or dates_practiced[-1] == today - timedelta(days=1):
                current_streak = 1
                for i in range(len(dates_practiced) - 2, -1, -1):
                    if dates_practiced[i] == dates_practiced[i + 1] - timedelta(days=1):
                        current_streak += 1
                    else:
                        break
        
        # Recent sessions (last 10)
        recent_sessions = []
        for s in sessions[-10:]:
            content = None
            if s['session_type'] == 'breathing':
                content = next((e for e in BREATHING_EXERCISES if e['id'] == s['content_id']), None)
            else:
                content = next((m for m in MEDITATION_SESSIONS if m['id'] == s['content_id']), None)
            
            recent_sessions.append({
                "id": s['id'],
                "type": s['session_type'],
                "title": content['name'] if s['session_type'] == 'breathing' else content['title'] if content else "Unknown",
                "duration": s['duration'],
                "timestamp": s['timestamp'].isoformat()
            })
        
        return {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "breathing_sessions": breathing_sessions,
            "meditation_sessions": meditation_sessions,
            "favorite_category": favorite_category,
            "current_streak": current_streak,
            "recent_sessions": list(reversed(recent_sessions))  # Most recent first
        }
    except Exception as e:
        logging.error(f"Error getting meditation progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/meditation/recommendations/{user_id}")
async def get_meditation_recommendations(user_id: str):
    """Get smart recommendations based on user's recent mood logs"""
    try:
        # Get recent mood logs (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_logs = await db.mood_logs.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(20).to_list(20)
        
        if not recent_logs:
            # Default recommendations for new users
            return {
                "recommendations": [
                    {
                        "type": "breathing",
                        "content": BREATHING_EXERCISES[0],  # Box Breathing
                        "reason": "Start with this foundational breathing technique"
                    },
                    {
                        "type": "meditation",
                        "content": MEDITATION_SESSIONS[0],  # Quick Stress Relief
                        "reason": "A perfect introduction to meditation practice"
                    }
                ]
            }
        
        # Analyze mood text for keywords
        all_mood_text = " ".join([log.get('mood_text', '').lower() for log in recent_logs])
        
        recommendations = []
        
        # Check for stress-related keywords
        stress_keywords = ['stress', 'stressed', 'overwhelm', 'pressure', 'busy', 'anxious', 'worry']
        if any(keyword in all_mood_text for keyword in stress_keywords):
            recommendations.append({
                "type": "breathing",
                "content": BREATHING_EXERCISES[0],  # Box Breathing
                "reason": "Your recent logs show stress - try this calming breathing exercise"
            })
            recommendations.append({
                "type": "meditation",
                "content": next(m for m in MEDITATION_SESSIONS if m['id'] == 'stress_relief_10'),
                "reason": "Deep stress release meditation based on your recent mood"
            })
        
        # Check for anxiety keywords
        anxiety_keywords = ['anxious', 'anxiety', 'nervous', 'panic', 'worried', 'fear']
        if any(keyword in all_mood_text for keyword in anxiety_keywords):
            recommendations.append({
                "type": "breathing",
                "content": BREATHING_EXERCISES[1],  # 4-7-8 Breathing
                "reason": "This breathing technique is excellent for calming anxiety"
            })
            recommendations.append({
                "type": "meditation",
                "content": next(m for m in MEDITATION_SESSIONS if m['id'] == 'anxiety_10'),
                "reason": "Recommended to help soothe your anxious mind"
            })
        
        # Check for sleep-related keywords
        sleep_keywords = ['tired', 'exhaust', 'sleep', 'insomnia', 'can\'t sleep', 'restless']
        if any(keyword in all_mood_text for keyword in sleep_keywords):
            recommendations.append({
                "type": "breathing",
                "content": BREATHING_EXERCISES[1],  # 4-7-8 Breathing (good for sleep)
                "reason": "This technique helps prepare your body for restful sleep"
            })
            recommendations.append({
                "type": "meditation",
                "content": next(m for m in MEDITATION_SESSIONS if m['id'] == 'sleep_10'),
                "reason": "Perfect for easing into a peaceful night's sleep"
            })
        
        # Check for focus-related keywords
        focus_keywords = ['distracted', 'unfocused', 'concentrate', 'focus', 'scattered', 'procrastinat']
        if any(keyword in all_mood_text for keyword in focus_keywords):
            recommendations.append({
                "type": "breathing",
                "content": BREATHING_EXERCISES[4],  # Resonant Breathing
                "reason": "Enhance your focus and mental clarity with this technique"
            })
            recommendations.append({
                "type": "meditation",
                "content": next(m for m in MEDITATION_SESSIONS if m['id'] == 'focus_15'),
                "reason": "Train your mind for better concentration"
            })
        
        # If no specific keywords found, provide general recommendations
        if not recommendations:
            recommendations = [
                {
                    "type": "breathing",
                    "content": BREATHING_EXERCISES[2],  # Deep Belly Breathing
                    "reason": "A great all-around practice for daily wellness"
                },
                {
                    "type": "meditation",
                    "content": MEDITATION_SESSIONS[9],  # Morning Energy
                    "reason": "Start your day with positive energy"
                }
            ]
        
        # Limit to top 3 recommendations
        return {"recommendations": recommendations[:3]}
        
    except Exception as e:
        logging.error(f"Error getting meditation recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Socket.IO events
@sio.event
async def connect(sid, environ):
    logging.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logging.info(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    room_id = data.get('room_id')
    username = data.get('username')
    user_id = data.get('user_id')
    
    # Check if user is a member of the community
    community = await db.communities.find_one({"id": room_id}, {"_id": 0})
    if community and user_id not in community.get('member_ids', []):
        await sio.emit('join_error', {'message': 'You must join the community first'}, room=sid)
        logging.warning(f"{username} attempted to join room {room_id} without membership")
        return
    
    await sio.enter_room(sid, room_id)
    await sio.emit('user_joined', {'username': username, 'message': f"{username} joined the community"}, room=room_id)
    logging.info(f"{username} joined room {room_id}")

@sio.event
async def send_message(sid, data):
    try:
        # Verify user is a member of the community
        community = await db.communities.find_one({"id": data['room_id']}, {"_id": 0})
        if community and data['user_id'] not in community.get('member_ids', []):
            await sio.emit('message_error', {'message': 'You must be a member to send messages'}, room=sid)
            return
        
        message = ChatMessage(
            room_id=data['room_id'],
            user_id=data['user_id'],
            username=data['username'],
            message=data['message']
        )
        
        # Save to MongoDB
        doc = message.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.chat_messages.insert_one(doc)
        
        # Broadcast to room
        await sio.emit('receive_message', message.model_dump(), room=data['room_id'])
    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")

@sio.event
async def leave_room(sid, data):
    room_id = data.get('room_id')
    username = data.get('username')
    await sio.leave_room(sid, room_id)
    await sio.emit('user_left', {'username': username, 'message': f"{username} left the community"}, room=room_id)

# Include router
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()