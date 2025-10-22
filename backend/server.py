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


# ===== RESOURCE LIBRARY ENDPOINTS =====

# Comprehensive educational content
EDUCATIONAL_RESOURCES = [
    # MENTAL HEALTH CONDITIONS - Articles
    {
        "id": "anxiety-understanding",
        "title": "Understanding Anxiety Disorders",
        "category": "conditions",
        "subcategory": "anxiety",
        "content_type": "article",
        "description": "A comprehensive guide to understanding anxiety disorders, their symptoms, causes, and treatment options.",
        "content": """# Understanding Anxiety Disorders

Anxiety disorders are among the most common mental health conditions, affecting millions of people worldwide. While it's normal to feel anxious occasionally, anxiety disorders involve more than temporary worry or fear.

## Types of Anxiety Disorders

**Generalized Anxiety Disorder (GAD)**: Persistent and excessive worry about various aspects of daily life.

**Panic Disorder**: Recurring unexpected panic attacks - sudden periods of intense fear that may include heart palpitations, sweating, and feelings of impending doom.

**Social Anxiety Disorder**: Intense fear of social situations and being judged by others.

**Specific Phobias**: Extreme fear of specific objects or situations (heights, flying, spiders, etc.).

## Common Symptoms

- Excessive worrying
- Restlessness or feeling on edge
- Difficulty concentrating
- Sleep disturbances
- Physical symptoms: rapid heartbeat, sweating, trembling, fatigue

## Causes

Anxiety disorders can result from a combination of factors:
- Genetics and family history
- Brain chemistry
- Life experiences and trauma
- Chronic stress
- Other medical conditions

## Treatment Options

Anxiety disorders are highly treatable through:
- Cognitive Behavioral Therapy (CBT)
- Exposure therapy
- Medication (SSRIs, SNRIs, benzodiazepines)
- Mindfulness and relaxation techniques
- Lifestyle changes (exercise, sleep, nutrition)

## When to Seek Help

If anxiety interferes with daily activities, relationships, or quality of life, it's important to seek professional help. Early intervention leads to better outcomes.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 8,
        "difficulty": "beginner",
        "tags": ["anxiety", "mental health", "disorders", "treatment"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "depression-guide",
        "title": "Depression: Symptoms, Causes, and Hope",
        "category": "conditions",
        "subcategory": "depression",
        "content_type": "article",
        "description": "Everything you need to know about depression, from recognizing symptoms to finding effective treatment.",
        "content": """# Depression: Symptoms, Causes, and Hope

Depression is more than just feeling sad or going through a rough patch. It's a serious mental health condition that affects how you think, feel, and handle daily activities.

## Understanding Depression

Clinical depression (Major Depressive Disorder) is characterized by persistent feelings of sadness, hopelessness, and loss of interest in activities once enjoyed.

## Common Symptoms

**Emotional Symptoms:**
- Persistent sad, anxious, or empty mood
- Feelings of hopelessness or pessimism
- Irritability
- Loss of interest in hobbies and activities
- Feelings of guilt or worthlessness

**Physical Symptoms:**
- Changes in appetite or weight
- Sleep disturbances (insomnia or oversleeping)
- Fatigue and decreased energy
- Physical aches and pains
- Difficulty concentrating and making decisions

## Types of Depression

- **Major Depressive Disorder**: Severe symptoms that interfere with daily life
- **Persistent Depressive Disorder**: Long-lasting depression (2+ years)
- **Seasonal Affective Disorder (SAD)**: Depression during specific seasons
- **Postpartum Depression**: Occurs after childbirth
- **Bipolar Depression**: Part of bipolar disorder cycles

## Causes and Risk Factors

- Biological factors and brain chemistry
- Genetics and family history
- Traumatic life events
- Chronic stress and medical conditions
- Substance use

## Treatment and Recovery

**Psychotherapy:**
- Cognitive Behavioral Therapy (CBT)
- Interpersonal Therapy (IPT)
- Problem-solving therapy

**Medication:**
- Antidepressants (SSRIs, SNRIs, etc.)
- May take 2-4 weeks to show effects

**Lifestyle Changes:**
- Regular exercise
- Healthy sleep habits
- Social connection
- Stress management techniques

## Hope and Recovery

Depression is treatable. With proper care, the vast majority of people with depression improve. Recovery is possible, and many people go on to lead fulfilling lives.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 10,
        "difficulty": "beginner",
        "tags": ["depression", "mental health", "treatment", "symptoms"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "ptsd-overview",
        "title": "PTSD: Understanding Post-Traumatic Stress",
        "category": "conditions",
        "subcategory": "ptsd",
        "content_type": "article",
        "description": "Learn about PTSD, its symptoms, triggers, and effective treatment approaches for trauma recovery.",
        "content": """# Understanding PTSD (Post-Traumatic Stress Disorder)

PTSD is a mental health condition triggered by experiencing or witnessing a terrifying event. It's a natural response to trauma that, for some people, doesn't resolve on its own.

## What Causes PTSD?

Traumatic events that may lead to PTSD include:
- Combat exposure
- Physical or sexual assault
- Accidents
- Natural disasters
- Childhood abuse
- Witnessing violence or death
- Medical emergencies

## Core Symptoms

**Re-experiencing:**
- Flashbacks and intrusive memories
- Nightmares
- Severe emotional distress when reminded of trauma

**Avoidance:**
- Avoiding thoughts, feelings, or conversations about the trauma
- Avoiding places, activities, or people that remind you of the event

**Negative Changes in Thinking and Mood:**
- Negative thoughts about yourself or the world
- Feelings of detachment
- Inability to experience positive emotions
- Memory problems related to the trauma

**Changes in Physical and Emotional Reactions:**
- Being easily startled
- Hypervigilance
- Self-destructive behavior
- Sleep problems
- Difficulty concentrating

## Treatment Options

**Trauma-Focused Therapies:**
- Cognitive Processing Therapy (CPT)
- Prolonged Exposure Therapy
- Eye Movement Desensitization and Reprocessing (EMDR)

**Medications:**
- SSRIs and SNRIs for depression and anxiety symptoms
- Sleep medications if needed

**Complementary Approaches:**
- Mindfulness and meditation
- Yoga and physical exercise
- Support groups

## Recovery is Possible

While PTSD can be debilitating, effective treatments exist. Many people with PTSD recover fully with proper care and support. Healing is not linear, but progress is achievable.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 12,
        "difficulty": "intermediate",
        "tags": ["ptsd", "trauma", "mental health", "treatment"],
        "views": 0,
        "bookmarks": 0
    },
    
    # CBT TECHNIQUES
    {
        "id": "cbt-thought-records",
        "title": "CBT: Thought Record Exercise",
        "category": "techniques",
        "subcategory": "cbt",
        "content_type": "exercise",
        "description": "Learn to identify and challenge negative thought patterns using cognitive behavioral therapy techniques.",
        "content": """# Thought Record Exercise (CBT)

Thought records are a fundamental CBT tool for identifying and challenging negative automatic thoughts.

## How to Use a Thought Record

**Step 1: Identify the Situation**
When you notice a change in mood, write down what happened:
- Where were you?
- Who were you with?
- What were you doing?

**Step 2: Notice Your Emotions**
Identify and rate the emotions you felt (0-100%):
- Sad, anxious, angry, frustrated, etc.

**Step 3: Identify Automatic Thoughts**
What went through your mind?
- "I'm such a failure"
- "Everyone thinks I'm stupid"
- "This always happens to me"

**Step 4: Find the Evidence**
Evidence FOR the thought:
- What facts support this thought?

Evidence AGAINST the thought:
- What facts contradict this thought?
- Would I say this to a friend?

**Step 5: Generate Alternative Thoughts**
Create a more balanced perspective:
- What's another way to view this situation?
- What would I tell a friend in this situation?

**Step 6: Re-rate Your Emotion**
After examining the evidence, re-rate your emotion (0-100%)
Notice if the intensity has decreased.

## Example

**Situation**: Sent a text to friend, no response after 2 hours

**Emotion**: Anxious (80%), Sad (60%)

**Automatic Thought**: "They're ignoring me. They must hate me."

**Evidence For**: They haven't responded yet

**Evidence Against**: 
- They're usually busy during work hours
- They've been a good friend for years
- They responded yesterday
- I sometimes take hours to respond too

**Alternative Thought**: "They're probably busy. They'll respond when they can. This doesn't mean they hate me."

**Re-rated Emotion**: Anxious (30%), Sad (20%)

## Practice Daily

Use thought records whenever you notice intense emotions. Over time, this process becomes automatic.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 15,
        "difficulty": "beginner",
        "tags": ["cbt", "cognitive therapy", "exercises", "thought patterns"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "dbt-distress-tolerance",
        "title": "DBT: Distress Tolerance Skills",
        "category": "techniques",
        "subcategory": "dbt",
        "content_type": "exercise",
        "description": "Master DBT distress tolerance techniques to survive crisis situations without making them worse.",
        "content": """# DBT Distress Tolerance Skills

Distress tolerance skills help you cope with painful situations when you can't make things better right away. The goal is to get through a crisis without making it worse.

## The TIPP Skills (For Intense Emotions)

**T - Temperature**
Change your body temperature to calm intense emotions:
- Hold ice cubes in your hands
- Splash cold water on your face
- Take a cold shower
- Hold your breath and put your face in ice water (30 seconds)

**I - Intense Exercise**
Engage in vigorous physical activity:
- Run or jog
- Jump jacks or burpees
- Dancing
- Fast-paced walking
- Boxing

**P - Paced Breathing**
Slow your breathing:
- Breathe in for 4 counts
- Hold for 4 counts
- Breathe out for 6-8 counts
- Focus on lengthening your exhale

**P - Paired Muscle Relaxation**
Tense and release muscle groups while breathing:
- Breathe in while tensing muscles (5 seconds)
- Breathe out while releasing tension
- Notice the difference

## The ACCEPTS Skills (Distraction)

**A - Activities**: Engage in activities that require concentration
**C - Contributing**: Help others or volunteer
**C - Comparisons**: Compare to times you've coped before
**E - Emotions**: Create opposite emotions (watch comedy when sad)
**P - Pushing away**: Put the situation out of your mind temporarily
**T - Thoughts**: Occupy your mind with other thoughts (puzzles, counting)
**S - Sensations**: Use strong sensations (hold ice, listen to loud music)

## IMPROVE the Moment

**I - Imagery**: Imagine peaceful scenes
**M - Meaning**: Find purpose in your pain
**P - Prayer**: Use prayer or meditation
**R - Relaxation**: Practice relaxation techniques
**O - One thing**: Focus on the present moment
**V - Vacation**: Take a brief mental or physical break
**E - Encouragement**: Give yourself supportive self-talk

## Self-Soothing with Five Senses

**Vision**: Look at beautiful images
**Hearing**: Listen to soothing music
**Smell**: Use calming scents (lavender, vanilla)
**Taste**: Savor flavors mindfully
**Touch**: Take a warm bath, pet an animal

## When to Use These Skills

- During a crisis
- When emotions feel overwhelming
- When you can't solve the problem immediately
- When you need to prevent impulsive actions

Remember: These skills don't solve problems, but they help you survive the moment without making things worse.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 20,
        "difficulty": "intermediate",
        "tags": ["dbt", "distress tolerance", "crisis management", "coping skills"],
        "views": 0,
        "bookmarks": 0
    },
    
    # VIDEO RESOURCES
    {
        "id": "anxiety-management-video",
        "title": "5 Evidence-Based Strategies for Managing Anxiety",
        "category": "videos",
        "subcategory": "anxiety",
        "content_type": "video",
        "description": "A mental health professional explains practical, science-backed techniques for reducing anxiety.",
        "content": "This video covers grounding techniques, cognitive restructuring, exposure principles, and lifestyle factors that reduce anxiety.",
        "author": "Dr. Sarah Johnson, Clinical Psychologist",
        "source_url": "https://www.youtube.com/watch?v=WWloIAQpMcQ",
        "duration_minutes": 15,
        "difficulty": "beginner",
        "tags": ["anxiety", "video", "coping strategies", "evidence-based"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "depression-recovery-video",
        "title": "The Science of Depression and Recovery",
        "category": "videos",
        "subcategory": "depression",
        "content_type": "video",
        "description": "Understanding the neuroscience behind depression and what research shows about effective treatments.",
        "content": "Learn about neuroplasticity, the role of neurotransmitters, and how different treatments work at the brain level.",
        "author": "Dr. Michael Chen, Neuroscientist",
        "source_url": "https://www.youtube.com/watch?v=NOAgplgTxfc",
        "duration_minutes": 18,
        "difficulty": "intermediate",
        "tags": ["depression", "video", "neuroscience", "treatment"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "mindfulness-basics-video",
        "title": "Introduction to Mindfulness Meditation",
        "category": "videos",
        "subcategory": "mindfulness",
        "content_type": "video",
        "description": "A beginner-friendly guide to mindfulness practice and its mental health benefits.",
        "content": "Practical instruction on mindfulness techniques, common challenges, and tips for building a sustainable practice.",
        "author": "Dr. Lisa Martinez, Mindfulness Teacher",
        "source_url": "https://www.youtube.com/watch?v=6p_yaNFSYao",
        "duration_minutes": 12,
        "difficulty": "beginner",
        "tags": ["mindfulness", "meditation", "video", "beginners"],
        "views": 0,
        "bookmarks": 0
    },
    
    # READING RECOMMENDATIONS
    {
        "id": "book-feeling-good",
        "title": "Feeling Good: The New Mood Therapy",
        "category": "reading",
        "subcategory": "self-help",
        "content_type": "book",
        "description": "Dr. David Burns' classic guide to using cognitive behavioral therapy to overcome depression.",
        "content": """# Feeling Good: The New Mood Therapy
**Author**: David D. Burns, M.D.

## Overview
This groundbreaking book introduces cognitive behavioral therapy (CBT) techniques in an accessible format for general readers. It has helped millions understand and overcome depression and anxiety.

## Key Concepts

**Cognitive Distortions**: Learn to identify 10 common thinking errors that fuel negative emotions.

**Mood-Thought Connection**: Understand how thoughts influence feelings and behaviors.

**Practical Exercises**: Hands-on techniques for challenging negative thoughts and building self-esteem.

## What You'll Learn
- How to identify automatic negative thoughts
- Techniques for cognitive restructuring
- Methods for overcoming procrastination
- Strategies for handling criticism
- Ways to defeat guilt and build self-esteem

## Who Should Read This
- People experiencing depression or low mood
- Those interested in CBT techniques
- Anyone wanting to improve their emotional well-being
- Mental health professionals

## Why It's Recommended
Research has shown that reading and applying the techniques in this book can be as effective as therapy for mild to moderate depression. It's evidence-based, practical, and has stood the test of time since its first publication in 1980.""",
        "author": "David D. Burns, M.D.",
        "difficulty": "beginner",
        "tags": ["cbt", "depression", "self-help", "book recommendation"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "book-body-keeps-score",
        "title": "The Body Keeps the Score",
        "category": "reading",
        "subcategory": "trauma",
        "content_type": "book",
        "description": "Dr. Bessel van der Kolk's revolutionary understanding of trauma and pathways to recovery.",
        "content": """# The Body Keeps the Score: Brain, Mind, and Body in the Healing of Trauma
**Author**: Bessel van der Kolk, M.D.

## Overview
A pioneering exploration of how trauma reshapes the brain, mind, and body, and revolutionary approaches to treatment and healing.

## Key Insights

**Trauma's Impact**: How traumatic experiences are stored in the body and affect physical and mental health.

**Beyond Talk Therapy**: Why traditional talk therapy isn't always enough for trauma healing.

**Innovative Treatments**: Exploration of EMDR, neurofeedback, yoga, and other body-based therapies.

## Main Themes
- The neuroscience of trauma
- How trauma affects development
- The role of relationships in healing
- Body-based approaches to recovery
- The importance of safety and trust

## What Makes It Important
This book synthesizes decades of clinical experience and research, offering hope and practical pathways for trauma survivors. It has transformed how mental health professionals understand and treat trauma.

## Who Should Read This
- Trauma survivors seeking understanding
- Mental health professionals
- Anyone interested in the mind-body connection
- People supporting loved ones with PTSD

## Key Takeaway
Healing from trauma involves the body and nervous system, not just the mind. Recovery is possible through various pathways that honor this reality.""",
        "author": "Bessel van der Kolk, M.D.",
        "difficulty": "intermediate",
        "tags": ["trauma", "ptsd", "neuroscience", "book recommendation"],
        "views": 0,
        "bookmarks": 0
    },
    
    # MYTH-BUSTING
    {
        "id": "myth-just-snap-out",
        "title": "Myth: 'Just Snap Out of It' - Depression is a Choice",
        "category": "myths",
        "subcategory": "depression",
        "content_type": "myth",
        "description": "Debunking the harmful myth that depression is simply a matter of willpower or attitude.",
        "content": """# Myth: Depression is Just Sadness - You Can 'Snap Out of It'

## The Myth
"Depression is just feeling sad. If you tried harder or thought more positively, you'd feel better. It's a choice."

## The Truth
Depression is a serious medical condition, not a character flaw or a choice. It involves complex changes in brain chemistry, neural pathways, and physical functioning.

## The Science

**Brain Chemistry**: Depression involves alterations in neurotransmitters (serotonin, dopamine, norepinephrine) that regulate mood, sleep, appetite, and energy.

**Structural Changes**: Brain imaging shows actual differences in the hippocampus, prefrontal cortex, and other regions in people with depression.

**Genetic Component**: Depression has a hereditary component, with genetics accounting for about 40% of the risk.

**Physical Illness**: Depression is associated with inflammation, hormonal changes, and other biological factors.

## Why This Myth is Harmful

- **Increases Shame**: Makes people feel they're failing if they can't "just be happy"
- **Delays Treatment**: People may not seek help, thinking they should handle it alone
- **Worsens Isolation**: Sufferers may hide their struggles to avoid judgment
- **Misses Root Causes**: Ignores the biological and environmental factors at play

## What Actually Helps

- **Professional Treatment**: Therapy and/or medication
- **Lifestyle Changes**: Exercise, sleep, nutrition (as part of treatment, not instead of it)
- **Support Systems**: Understanding from loved ones
- **Time and Patience**: Recovery isn't linear and takes time
- **Self-Compassion**: Treating yourself with kindness, not criticism

## Bottom Line
Telling someone with depression to "snap out of it" is like telling someone with a broken leg to "just walk normally." Depression is a real illness that requires real treatment, and recovery is possible with proper care.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 6,
        "difficulty": "beginner",
        "tags": ["myths", "depression", "mental health", "stigma"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "myth-therapy-weakness",
        "title": "Myth: Therapy is for Weak People",
        "category": "myths",
        "subcategory": "therapy",
        "content_type": "myth",
        "description": "Challenging the stigma that seeking mental health treatment is a sign of weakness.",
        "content": """# Myth: Seeking Therapy Means You're Weak

## The Myth
"Strong people handle their problems alone. Needing therapy means you're weak, damaged, or can't handle life."

## The Truth
Seeking therapy is actually a sign of strength, self-awareness, and commitment to personal growth. It takes courage to be vulnerable and work on yourself.

## Reality Check

**Therapy is Self-Care**: Just as you'd see a doctor for physical illness, seeing a therapist for mental health is responsible self-care.

**Everyone Struggles**: Mental health challenges don't discriminate. They affect people of all backgrounds, including the most successful and resilient individuals.

**Professional Athletes Use Coaches**: Top performers in every field seek guidance to improve. Mental health is no different.

**Asking for Help is Strength**: It takes more courage to admit you need support than to struggle in silence.

## Who Goes to Therapy?

- **High Achievers**: CEOs, athletes, artists who want to perform at their best
- **People in Transition**: Those navigating life changes, careers, relationships
- **Trauma Survivors**: People working through difficult experiences
- **Anyone**: People seeking personal growth, better relationships, or stress management

## What Therapy Actually Is

Therapy is a partnership where you work with a trained professional to:
- Understand yourself better
- Develop healthier coping strategies
- Process difficult experiences
- Build stronger relationships
- Achieve your goals

## The Real Weakness?

Suffering in silence when help is available. Letting pride or stigma prevent you from improving your life. Staying stuck instead of taking action.

## Notable People Who've Been Open About Therapy

- Dwayne "The Rock" Johnson
- Lady Gaga
- Michael Phelps
- Kristen Bell
- Prince Harry
- Many successful people across all fields

## Bottom Line
Therapy isn't a sign of weakness—it's a tool for becoming the best version of yourself. The strongest people are those who recognize when they need support and have the courage to seek it.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 7,
        "difficulty": "beginner",
        "tags": ["myths", "therapy", "stigma", "mental health"],
        "views": 0,
        "bookmarks": 0
    },
    {
        "id": "myth-meds-forever",
        "title": "Myth: Mental Health Medication is Forever",
        "category": "myths",
        "subcategory": "medication",
        "content_type": "myth",
        "description": "Clarifying misconceptions about psychiatric medication and long-term use.",
        "content": """# Myth: If You Start Medication, You'll Need It Forever

## The Myth
"Once you start taking psychiatric medication, you'll be dependent on it for life. Your brain will stop working without it."

## The Truth
Many people use psychiatric medication temporarily as part of their treatment plan. Others benefit from longer-term use. Both approaches are valid, and the decision depends on individual circumstances.

## The Facts

**Treatment Duration Varies**: 
- Some people take medication for a few months during a crisis
- Others use it for several years during recovery
- Some find long-term use most beneficial for stability
- All approaches are legitimate

**Not Addictive**: Most psychiatric medications (SSRIs, SNRIs, mood stabilizers) are not addictive, though some require careful discontinuation.

**Combined with Therapy**: Medication often works best alongside therapy, which provides skills that last beyond medication use.

**Individual Response**: Everyone's brain chemistry and life circumstances are different, requiring personalized treatment approaches.

## When Medication Might Be Short-Term

- Situational depression or anxiety
- Acute stress reactions
- Postpartum depression
- First episode of mild to moderate symptoms

## When Long-Term Use Might Be Beneficial

- Recurrent depression or anxiety
- Bipolar disorder
- Chronic conditions
- When symptoms return after discontinuation

## The Medical Model

Think of it like diabetes or high blood pressure:
- Some people need treatment temporarily
- Others benefit from ongoing management
- Both are medical conditions requiring appropriate care
- No shame in either scenario

## Working with Your Doctor

**Regular Reviews**: Medication should be regularly evaluated for effectiveness and necessity.

**Informed Decisions**: Work with your psychiatrist to make decisions based on your symptoms, history, and preferences.

**Tapering**: If discontinuing, proper tapering under medical supervision prevents withdrawal effects.

## What Actually Happens

Many people successfully taper off medications after:
- Their symptoms have been stable for an extended period
- They've developed coping skills through therapy
- Life stressors have improved
- They have strong support systems in place

## Bottom Line
Psychiatric medication is a tool, not a life sentence. The goal is to support your well-being, whether that means short-term use, long-term management, or something in between. You and your doctor can work together to find what's right for you.""",
        "author": "MoodMesh Clinical Team",
        "duration_minutes": 8,
        "difficulty": "intermediate",
        "tags": ["myths", "medication", "treatment", "mental health"],
        "views": 0,
        "bookmarks": 0
    }
]

@api_router.get("/resources")
async def get_all_resources(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    content_type: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all educational resources with optional filtering"""
    try:
        # Check if resources are already in database
        count = await db.resources.count_documents({})
        
        # Seed resources if not already present
        if count == 0:
            for resource in EDUCATIONAL_RESOURCES:
                doc = resource.copy()
                doc['created_at'] = datetime.now(timezone.utc).isoformat()
                await db.resources.insert_one(doc)
        
        # Build query
        query = {}
        if category:
            query['category'] = category
        if subcategory:
            query['subcategory'] = subcategory
        if content_type:
            query['content_type'] = content_type
        if search:
            query['$or'] = [
                {'title': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}},
                {'tags': {'$regex': search, '$options': 'i'}}
            ]
        
        # Fetch resources
        resources = await db.resources.find(query, {"_id": 0}).to_list(1000)
        
        return resources
    except Exception as e:
        logging.error(f"Error fetching resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/resources/{resource_id}")
async def get_resource_by_id(resource_id: str):
    """Get a single resource by ID and increment view count"""
    try:
        resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Increment view count
        await db.resources.update_one(
            {"id": resource_id},
            {"$inc": {"views": 1}}
        )
        resource['views'] = resource.get('views', 0) + 1
        
        return resource
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/resources/bookmark")
async def bookmark_resource(bookmark_data: ResourceBookmarkCreate):
    """Bookmark a resource for a user"""
    try:
        # Check if already bookmarked
        existing = await db.resource_bookmarks.find_one({
            "user_id": bookmark_data.user_id,
            "resource_id": bookmark_data.resource_id
        })
        
        if existing:
            return {"message": "Already bookmarked", "success": True}
        
        # Create bookmark
        bookmark = ResourceBookmark(
            user_id=bookmark_data.user_id,
            resource_id=bookmark_data.resource_id
        )
        
        doc = bookmark.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.resource_bookmarks.insert_one(doc)
        
        # Increment bookmark count on resource
        await db.resources.update_one(
            {"id": bookmark_data.resource_id},
            {"$inc": {"bookmarks": 1}}
        )
        
        return {"message": "Resource bookmarked successfully", "success": True, "bookmark_id": bookmark.id}
    except Exception as e:
        logging.error(f"Error bookmarking resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/resources/bookmark/{user_id}/{resource_id}")
async def remove_bookmark(user_id: str, resource_id: str):
    """Remove a bookmark"""
    try:
        result = await db.resource_bookmarks.delete_one({
            "user_id": user_id,
            "resource_id": resource_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        
        # Decrement bookmark count on resource
        await db.resources.update_one(
            {"id": resource_id},
            {"$inc": {"bookmarks": -1}}
        )
        
        return {"message": "Bookmark removed successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error removing bookmark: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/resources/bookmarks/{user_id}")
async def get_user_bookmarks(user_id: str):
    """Get all bookmarked resources for a user"""
    try:
        # Get bookmark records
        bookmarks = await db.resource_bookmarks.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(1000)
        
        if not bookmarks:
            return []
        
        # Get resource IDs
        resource_ids = [b['resource_id'] for b in bookmarks]
        
        # Fetch full resource details
        resources = await db.resources.find(
            {"id": {"$in": resource_ids}},
            {"_id": 0}
        ).to_list(1000)
        
        return resources
    except Exception as e:
        logging.error(f"Error fetching user bookmarks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/resources/categories/summary")
async def get_categories_summary():
    """Get summary of all categories with resource counts"""
    try:
        # Ensure resources are seeded
        count = await db.resources.count_documents({})
        if count == 0:
            for resource in EDUCATIONAL_RESOURCES:
                doc = resource.copy()
                doc['created_at'] = datetime.now(timezone.utc).isoformat()
                await db.resources.insert_one(doc)
        
        # Get counts by category
        pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await db.resources.aggregate(pipeline).to_list(100)
        
        summary = {
            "conditions": 0,
            "techniques": 0,
            "videos": 0,
            "reading": 0,
            "myths": 0
        }
        
        for result in results:
            category = result['_id']
            if category in summary:
                summary[category] = result['count']
        
        return summary
    except Exception as e:
        logging.error(f"Error fetching categories summary: {str(e)}")
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


# ==================== Music Therapy Models ====================

class SpotifyAuthResponse(BaseModel):
    auth_url: str

class SpotifyTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    
class SpotifyProfile(BaseModel):
    id: str
    display_name: str
    product: str  # "free" or "premium"
    is_premium: bool

class BuiltInAudio(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: str  # "nature", "white_noise", "binaural_beats"
    duration: int  # in seconds
    audio_url: str
    tags: List[str] = []
    
class AudioJournal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood: str
    journal_text: str
    voice_recording_url: Optional[str] = None
    music_played: Optional[str] = None  # Track/sound played during journaling
    music_source: Optional[str] = None  # "spotify" or "builtin"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MusicHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    track_name: str
    artist: str
    source: str  # "spotify" or "builtin"
    mood_context: Optional[str] = None
    duration_played: int  # in seconds
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Built-in Audio Library (seeded on first request)
BUILTIN_AUDIO_LIBRARY = [
    # Nature Sounds
    {
        "id": "nature_ocean_waves",
        "title": "Ocean Waves",
        "description": "Gentle ocean waves lapping on the shore - perfect for relaxation and sleep",
        "category": "nature",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2022/05/13/audio_4d8b25d52f.mp3",
        "tags": ["calming", "sleep", "relaxation", "water"]
    },
    {
        "id": "nature_rain",
        "title": "Rain on Leaves",
        "description": "Soft rain falling on leaves in a peaceful forest",
        "category": "nature",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2022/03/10/audio_c610232532.mp3",
        "tags": ["calming", "sleep", "focus", "rain"]
    },
    {
        "id": "nature_forest",
        "title": "Forest Birds",
        "description": "Morning birdsong in a tranquil forest setting",
        "category": "nature",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2022/03/15/audio_4dedf2bf94.mp3",
        "tags": ["energizing", "morning", "nature", "birds"]
    },
    {
        "id": "nature_stream",
        "title": "Mountain Stream",
        "description": "Gentle babbling brook flowing through mountains",
        "category": "nature",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2022/05/27/audio_bb630cc098.mp3",
        "tags": ["calming", "focus", "water", "meditation"]
    },
    {
        "id": "nature_thunder",
        "title": "Distant Thunder",
        "description": "Calming thunderstorm in the distance with light rain",
        "category": "nature",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2021/08/09/audio_0625c1539c.mp3",
        "tags": ["sleep", "calming", "rain", "storm"]
    },
    
    # White Noise
    {
        "id": "white_noise_pure",
        "title": "Pure White Noise",
        "description": "Classic white noise for blocking distractions and improving focus",
        "category": "white_noise",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2022/10/06/audio_2b15854229.mp3",
        "tags": ["focus", "sleep", "concentration", "blocking"]
    },
    {
        "id": "white_noise_pink",
        "title": "Pink Noise",
        "description": "Softer than white noise, ideal for deep sleep and relaxation",
        "category": "white_noise",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2023/07/02/audio_141851fa41.mp3",
        "tags": ["sleep", "deep-sleep", "calming"]
    },
    {
        "id": "white_noise_brown",
        "title": "Brown Noise",
        "description": "Deep, rumbling noise for enhanced focus and stress relief",
        "category": "white_noise",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2023/06/29/audio_db2b42ba1d.mp3",
        "tags": ["focus", "stress-relief", "concentration"]
    },
    
    # Binaural Beats
    {
        "id": "binaural_meditation",
        "title": "Theta Waves (6Hz) - Deep Meditation",
        "description": "Binaural beats at 6Hz for deep meditation and creativity",
        "category": "binaural_beats",
        "duration": 1800,
        "audio_url": "https://cdn.pixabay.com/audio/2022/11/18/audio_1e5d5c0c85.mp3",
        "tags": ["meditation", "creativity", "deep-state", "theta"]
    },
    {
        "id": "binaural_focus",
        "title": "Beta Waves (15Hz) - Focus & Alertness",
        "description": "Binaural beats at 15Hz for concentration and mental clarity",
        "category": "binaural_beats",
        "duration": 1800,
        "audio_url": "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe02c21.mp3",
        "tags": ["focus", "concentration", "alertness", "beta"]
    },
    {
        "id": "binaural_sleep",
        "title": "Delta Waves (2Hz) - Deep Sleep",
        "description": "Binaural beats at 2Hz for deep, restorative sleep",
        "category": "binaural_beats",
        "duration": 3600,
        "audio_url": "https://cdn.pixabay.com/audio/2024/08/06/audio_c24c5f5622.mp3",
        "tags": ["sleep", "deep-sleep", "recovery", "delta"]
    },
    {
        "id": "binaural_anxiety",
        "title": "Alpha Waves (10Hz) - Anxiety Relief",
        "description": "Binaural beats at 10Hz for relaxation and anxiety reduction",
        "category": "binaural_beats",
        "duration": 1800,
        "audio_url": "https://cdn.pixabay.com/audio/2023/02/28/audio_7142cf4b0e.mp3",
        "tags": ["anxiety-relief", "relaxation", "calming", "alpha"]
    }
]

# ==================== Music Therapy Endpoints ====================

# Spotify OAuth endpoints
@api_router.get("/music/spotify/login")
async def spotify_login():
    """Get Spotify OAuth authorization URL"""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        sp_oauth = SpotifyOAuth(
            client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
            client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.environ.get('REDIRECT_URI'),
            scope="user-read-playback-state user-modify-playback-state user-read-private streaming playlist-read-private user-top-read user-read-recently-played"
        )
        
        auth_url = sp_oauth.get_authorize_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logging.error(f"Error generating Spotify auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/music/spotify/callback")
async def spotify_callback(code: str):
    """Handle Spotify OAuth callback and exchange code for tokens"""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        sp_oauth = SpotifyOAuth(
            client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
            client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.environ.get('REDIRECT_URI'),
            scope="user-read-playback-state user-modify-playback-state user-read-private streaming playlist-read-private user-top-read user-read-recently-played"
        )
        
        token_info = sp_oauth.get_access_token(code, as_dict=True, check_cache=False)
        
        return {
            "access_token": token_info["access_token"],
            "refresh_token": token_info["refresh_token"],
            "expires_in": token_info["expires_in"]
        }
    except Exception as e:
        logging.error(f"Error in Spotify callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/music/spotify/refresh")
async def spotify_refresh_token(refresh_token: str):
    """Refresh Spotify access token"""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        sp_oauth = SpotifyOAuth(
            client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
            client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.environ.get('REDIRECT_URI')
        )
        
        token_info = sp_oauth.refresh_access_token(refresh_token)
        
        return {
            "access_token": token_info["access_token"],
            "expires_in": token_info.get("expires_in", 3600)
        }
    except Exception as e:
        logging.error(f"Error refreshing Spotify token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@api_router.get("/music/spotify/profile")
async def get_spotify_profile(access_token: str):
    """Get Spotify user profile and check premium status"""
    try:
        import spotipy
        
        sp = spotipy.Spotify(auth=access_token)
        profile = sp.me()
        
        return {
            "id": profile["id"],
            "display_name": profile.get("display_name", profile["id"]),
            "product": profile.get("product", "free"),
            "is_premium": profile.get("product", "free") == "premium"
        }
    except Exception as e:
        logging.error(f"Error getting Spotify profile: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid access token")

@api_router.get("/music/spotify/search")
async def search_spotify(q: str, access_token: str, limit: int = 20):
    """Search Spotify tracks"""
    try:
        import spotipy
        
        sp = spotipy.Spotify(auth=access_token)
        results = sp.search(q=q, limit=limit, type='track')
        
        tracks = []
        for item in results['tracks']['items']:
            tracks.append({
                "id": item["id"],
                "name": item["name"],
                "artist": ", ".join([artist["name"] for artist in item["artists"]]),
                "album": item["album"]["name"],
                "duration_ms": item["duration_ms"],
                "uri": item["uri"],
                "preview_url": item.get("preview_url"),
                "image_url": item["album"]["images"][0]["url"] if item["album"]["images"] else None
            })
        
        return {"tracks": tracks}
    except Exception as e:
        logging.error(f"Error searching Spotify: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/music/spotify/recommendations")
async def get_spotify_recommendations(access_token: str, seed_genres: str = "ambient,chill,sleep", limit: int = 20):
    """Get Spotify track recommendations based on genres"""
    try:
        import spotipy
        
        sp = spotipy.Spotify(auth=access_token)
        
        # Convert comma-separated string to list
        genres = seed_genres.split(',')
        
        results = sp.recommendations(seed_genres=genres, limit=limit)
        
        tracks = []
        for item in results['tracks']:
            tracks.append({
                "id": item["id"],
                "name": item["name"],
                "artist": ", ".join([artist["name"] for artist in item["artists"]]),
                "album": item["album"]["name"],
                "duration_ms": item["duration_ms"],
                "uri": item["uri"],
                "preview_url": item.get("preview_url"),
                "image_url": item["album"]["images"][0]["url"] if item["album"]["images"] else None
            })
        
        return {"tracks": tracks}
    except Exception as e:
        logging.error(f"Error getting Spotify recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Built-in Audio Library endpoints
@api_router.get("/music/library")
async def get_builtin_audio_library(category: Optional[str] = None):
    """Get built-in audio library (nature sounds, white noise, binaural beats)"""
    try:
        # Seed database if empty
        existing = await db.builtin_audio.count_documents({})
        if existing == 0:
            await db.builtin_audio.insert_many(BUILTIN_AUDIO_LIBRARY)
        
        # Filter by category if provided
        query = {"category": category} if category else {}
        
        audio_items = await db.builtin_audio.find(query, {"_id": 0}).to_list(100)
        
        # Group by category
        categorized = {
            "nature": [],
            "white_noise": [],
            "binaural_beats": []
        }
        
        for item in audio_items:
            categorized[item["category"]].append(item)
        
        return categorized
    except Exception as e:
        logging.error(f"Error getting audio library: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mood-based recommendations
@api_router.get("/music/recommendations/{user_id}")
async def get_music_recommendations(user_id: str):
    """Get AI-powered music recommendations based on recent mood logs"""
    try:
        # Get recent mood logs (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_logs = await db.mood_logs.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        if not recent_logs:
            # Default recommendations for new users
            return {
                "mood_analysis": "Welcome! We don't have enough data yet to analyze your mood patterns.",
                "builtin_recommendations": [
                    {
                        "id": "nature_ocean_waves",
                        "title": "Ocean Waves",
                        "category": "nature",
                        "reason": "Great starting point for relaxation"
                    },
                    {
                        "id": "binaural_meditation",
                        "title": "Theta Waves (6Hz) - Deep Meditation",
                        "category": "binaural_beats",
                        "reason": "Perfect for beginners to meditation"
                    }
                ],
                "spotify_genres": ["ambient", "chill", "meditation"],
                "spotify_search_suggestions": ["meditation music", "calm piano", "nature sounds"]
            }
        
        # Analyze mood patterns using Gemini
        mood_texts = [log["mood_text"] for log in recent_logs]
        analysis_prompt = f"""Analyze these recent mood entries and recommend music therapy:

Mood entries: {', '.join(mood_texts)}

Provide:
1. Brief mood analysis (1-2 sentences)
2. Top 3 builtin audio categories that would help (choose from: nature sounds, white noise, binaural beats)
3. Top 3 Spotify genres for their mood (e.g., ambient, chill, sleep, focus, energizing)
4. Top 3 Spotify search suggestions

Format as JSON:
{{
    "mood_analysis": "...",
    "builtin_categories": ["category1", "category2", "category3"],
    "spotify_genres": ["genre1", "genre2", "genre3"],
    "spotify_searches": ["search1", "search2", "search3"]
}}"""
        
        response = model.generate_content(analysis_prompt)
        
        # Parse AI response
        import json
        ai_analysis = json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
        
        # Get relevant built-in audio
        builtin_recs = []
        for category in ai_analysis.get("builtin_categories", ["nature", "white_noise", "binaural_beats"])[:3]:
            category_items = await db.builtin_audio.find(
                {"category": category},
                {"_id": 0}
            ).limit(2).to_list(2)
            
            for item in category_items:
                builtin_recs.append({
                    "id": item["id"],
                    "title": item["title"],
                    "category": item["category"],
                    "audio_url": item["audio_url"],
                    "duration": item["duration"],
                    "tags": item["tags"]
                })
        
        return {
            "mood_analysis": ai_analysis.get("mood_analysis", ""),
            "builtin_recommendations": builtin_recs[:5],
            "spotify_genres": ai_analysis.get("spotify_genres", ["ambient", "chill"]),
            "spotify_search_suggestions": ai_analysis.get("spotify_searches", ["meditation music"])
        }
    except Exception as e:
        logging.error(f"Error getting music recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Audio Journaling endpoints
@api_router.post("/music/journal/create")
async def create_audio_journal(
    user_id: str,
    mood: str,
    journal_text: str,
    voice_recording_url: Optional[str] = None,
    music_played: Optional[str] = None,
    music_source: Optional[str] = None
):
    """Create an audio journal entry"""
    try:
        journal = AudioJournal(
            user_id=user_id,
            mood=mood,
            journal_text=journal_text,
            voice_recording_url=voice_recording_url,
            music_played=music_played,
            music_source=music_source
        )
        
        doc = journal.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        
        await db.audio_journals.insert_one(doc)
        
        # Award wellness stars
        await db.user_profiles.update_one(
            {"user_id": user_id},
            {"$inc": {"wellness_stars": 3}}
        )
        
        return {
            "message": "Audio journal created successfully",
            "journal_id": journal.id,
            "stars_earned": 3
        }
    except Exception as e:
        logging.error(f"Error creating audio journal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/music/journal/{user_id}")
async def get_audio_journals(user_id: str, limit: int = 50):
    """Get user's audio journal entries"""
    try:
        journals = await db.audio_journals.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"journals": journals}
    except Exception as e:
        logging.error(f"Error getting audio journals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/music/journal/entry/{journal_id}")
async def get_audio_journal_entry(journal_id: str):
    """Get specific audio journal entry"""
    try:
        journal = await db.audio_journals.find_one(
            {"id": journal_id},
            {"_id": 0}
        )
        
        if not journal:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        
        return journal
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting audio journal entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Music History tracking
@api_router.post("/music/history/save")
async def save_music_history(
    user_id: str,
    track_name: str,
    artist: str,
    source: str,
    mood_context: Optional[str] = None,
    duration_played: int = 0
):
    """Save music listening history"""
    try:
        history = MusicHistory(
            user_id=user_id,
            track_name=track_name,
            artist=artist,
            source=source,
            mood_context=mood_context,
            duration_played=duration_played
        )
        
        doc = history.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        
        await db.music_history.insert_one(doc)
        
        return {"message": "Music history saved successfully"}
    except Exception as e:
        logging.error(f"Error saving music history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/music/history/{user_id}")
async def get_music_history(user_id: str, limit: int = 50):
    """Get user's music listening history"""
    try:
        history = await db.music_history.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"history": history}
    except Exception as e:
        logging.error(f"Error getting music history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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