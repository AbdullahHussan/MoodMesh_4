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
8. If a question is about serious self-harm or emergency, recommend professional help immediately

Response format:
- Start with empathy and validation
- Provide therapeutic insights
- Offer practical coping strategies
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
            therapist_response=therapist_response
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