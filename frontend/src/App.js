import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { io } from "socket.io-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Brain, MessageCircle, Star, Sparkles, Heart, Users, Send, LogOut, Bot, TrendingUp, Trophy } from "lucide-react";
import Communities from "@/pages/Communities";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import HomePage from "@/pages/HomePage";
import Analytics from "@/pages/Analytics";
import Achievements from "@/pages/Achievements";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const socket = io(BACKEND_URL);

// Dashboard
const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    fetchProfile(userData.user_id);
  }, [navigate]);

  const fetchProfile = async (userId) => {
    try {
      const response = await axios.get(`${API}/profile/${userId}`);
      setProfile(response.data);
    } catch (error) {
      console.error("Failed to fetch profile", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("moodmesh_user");
    localStorage.removeItem("moodmesh_token");
    navigate("/login");
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <Brain className="w-12 h-12 text-teal-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>MoodMesh</h1>
              <p className="text-gray-600">Welcome back, {user.username}!</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-full shadow-md" data-testid="wellness-stars-display">
              <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
              <span className="font-semibold">{profile?.wellness_stars || 0} Stars</span>
            </div>
            <Button variant="outline" onClick={handleLogout} data-testid="logout-button">
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Link to="/mood-log" className="block" data-testid="mood-log-card">
            <Card className="h-full border-2 hover:border-teal-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-teal-100 rounded-full">
                    <Heart className="w-8 h-8 text-teal-600" />
                  </div>
                  <CardTitle className="text-xl">Log Your Mood</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Share how you're feeling and receive personalized AI-powered coping strategies.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Link to="/analytics" className="block" data-testid="analytics-card">
            <Card className="h-full border-2 hover:border-emerald-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-emerald-100 rounded-full">
                    <TrendingUp className="w-8 h-8 text-emerald-600" />
                  </div>
                  <CardTitle className="text-xl">Analytics</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  View insights and patterns from your mood logs with AI-powered analysis.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Link to="/ai-therapist" className="block" data-testid="ai-therapist-card">
            <Card className="h-full border-2 hover:border-purple-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-purple-100 rounded-full">
                    <Bot className="w-8 h-8 text-purple-600" />
                  </div>
                  <CardTitle className="text-xl">AI Therapist</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Chat with a professional AI therapist for personalized mental health support and guidance.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Link to="/communities" className="block" data-testid="communities-card">
            <Card className="h-full border-2 hover:border-blue-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-blue-100 rounded-full">
                    <Users className="w-8 h-8 text-blue-600" />
                  </div>
                  <CardTitle className="text-xl">Communities</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Join or create supportive communities. Connect with others who understand.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>

        <Card className="mt-6 border-2" data-testid="profile-summary">
          <CardHeader>
            <CardTitle className="text-xl">Your Wellness Journey</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Avatar className="w-16 h-16">
                <AvatarFallback className="bg-teal-600 text-white text-2xl">
                  {user.username.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <h3 className="text-xl font-semibold">{user.username}</h3>
                <p className="text-gray-600">Wellness Stars: {profile?.wellness_stars || 0}</p>
              </div>
              <Badge className="bg-gradient-to-r from-teal-500 to-emerald-500 text-white px-4 py-2 text-base">
                Active Member
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
      <Toaster />
    </div>
  );
};

// Mood Log Page
const MoodLogPage = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [moodText, setMoodText] = useState("");
  const [aiSuggestion, setAiSuggestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [recentLogs, setRecentLogs] = useState([]);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    fetchRecentLogs(userData.user_id);
  }, [navigate]);

  const fetchRecentLogs = async (userId) => {
    try {
      const response = await axios.get(`${API}/mood/logs/${userId}`);
      setRecentLogs(response.data.slice(0, 5));
    } catch (error) {
      console.error("Failed to fetch logs", error);
    }
  };

  const handleSubmit = async () => {
    if (!moodText.trim()) {
      toast.error("Please describe your mood");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/mood/log`, {
        user_id: user.user_id,
        mood_text: moodText
      });
      setAiSuggestion(response.data.ai_suggestion);
      toast.success("Mood logged! +1 Wellness Star ⭐");
      setMoodText("");
      fetchRecentLogs(user.user_id);
    } catch (error) {
      toast.error("Failed to log mood");
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Button variant="outline" onClick={() => navigate("/dashboard")} data-testid="back-to-dashboard">
            ← Back to Dashboard
          </Button>
        </div>

        <Card className="mb-6 border-2 border-teal-200" data-testid="mood-log-form">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Heart className="w-6 h-6 text-teal-600" />
              How are you feeling?
            </CardTitle>
            <CardDescription>Share your emotions and receive personalized support</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="I'm feeling..."
              value={moodText}
              onChange={(e) => setMoodText(e.target.value)}
              rows={4}
              className="text-base"
              data-testid="mood-input"
            />
            <Button 
              onClick={handleSubmit} 
              className="w-full bg-teal-600 hover:bg-teal-700 text-white py-6 text-lg"
              disabled={isLoading}
              data-testid="submit-mood-button"
            >
              {isLoading ? "Getting AI Support..." : "Submit & Get Support"}
            </Button>
          </CardContent>
        </Card>

        {aiSuggestion && (
          <Card className="mb-6 border-2 border-yellow-200 bg-gradient-to-br from-yellow-50 to-amber-50" data-testid="ai-suggestion-card">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-yellow-600" />
                AI Coping Strategy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-800 text-base leading-relaxed" data-testid="ai-suggestion-text">{aiSuggestion}</p>
            </CardContent>
          </Card>
        )}

        {recentLogs.length > 0 && (
          <Card className="border-2" data-testid="recent-logs">
            <CardHeader>
              <CardTitle className="text-xl">Recent Mood Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentLogs.map((log) => (
                  <div key={log.id} className="p-4 bg-white rounded-lg border" data-testid={`mood-log-${log.id}`}>
                    <p className="text-gray-800 font-medium mb-1">{log.mood_text}</p>
                    <p className="text-sm text-gray-600">{new Date(log.timestamp).toLocaleDateString()}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      <Toaster />
    </div>
  );
};

// AI Therapist Chat
const AITherapist = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    loadChatHistory(userData.user_id);
  }, [navigate]);

  const loadChatHistory = async (userId) => {
    try {
      const response = await axios.get(`${API}/therapist/history/${userId}`);
      const history = response.data.map(chat => ([
        { role: 'user', content: chat.user_message },
        { role: 'therapist', content: chat.therapist_response }
      ])).flat();
      setMessages(history);
    } catch (error) {
      console.error("Failed to load chat history", error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMsg = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/therapist/chat`, {
        user_id: user.user_id,
        message: inputMessage
      });

      const therapistMsg = { role: 'therapist', content: response.data.therapist_response };
      setMessages(prev => [...prev, therapistMsg]);
    } catch (error) {
      toast.error("Failed to get response from therapist");
      setMessages(prev => [...prev, { 
        role: 'therapist', 
        content: "I apologize, I'm having trouble connecting right now. Please try again in a moment." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 p-6">
      <div className="max-w-4xl mx-auto h-[calc(100vh-3rem)] flex flex-col">
        <div className="mb-4 flex items-center justify-between">
          <Button variant="outline" onClick={() => navigate("/dashboard")} data-testid="back-to-dashboard-therapist">
            ← Back to Dashboard
          </Button>
          <Badge className="bg-purple-600 text-white px-4 py-2" data-testid="therapist-badge">
            <Bot className="w-4 h-4 mr-2" />
            Professional AI Therapist
          </Badge>
        </div>

        <Card className="flex-1 border-2 border-purple-200 flex flex-col shadow-xl" data-testid="therapist-chat-card">
          <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-pink-50">
            <CardTitle className="text-2xl flex items-center gap-2">
              <Bot className="w-7 h-7 text-purple-600" />
              AI Therapist Chat
            </CardTitle>
            <CardDescription>A safe, confidential space for mental health support. This AI is trained to discuss only therapy-related topics.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            <ScrollArea className="flex-1 p-6" data-testid="therapist-messages">
              <div className="space-y-4">
                {messages.length === 0 && (
                  <div className="text-center py-12" data-testid="welcome-message">
                    <Bot className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">Welcome to Your Therapy Session</h3>
                    <p className="text-gray-600 max-w-md mx-auto">
                      I'm here to provide professional mental health support. Feel free to share what's on your mind.
                      I only discuss therapy and mental wellness topics.
                    </p>
                  </div>
                )}
                {messages.map((msg, idx) => (
                  <div 
                    key={idx} 
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    data-testid={`therapist-msg-${idx}`}
                  >
                    <div className={`max-w-lg ${
                      msg.role === 'user' 
                        ? 'bg-purple-600 text-white rounded-2xl rounded-tr-sm' 
                        : 'bg-white border-2 border-purple-200 text-gray-800 rounded-2xl rounded-tl-sm'
                    } px-5 py-3 shadow-md`}>
                      {msg.role === 'therapist' && (
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="w-4 h-4 text-purple-600" />
                          <span className="text-xs font-semibold text-purple-600">AI Therapist</span>
                        </div>
                      )}
                      <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start" data-testid="typing-indicator">
                    <div className="bg-white border-2 border-purple-200 rounded-2xl rounded-tl-sm px-5 py-3 shadow-md">
                      <div className="flex items-center gap-2">
                        <Bot className="w-4 h-4 text-purple-600" />
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
            <div className="p-4 border-t bg-white">
              <div className="flex gap-2">
                <Input
                  placeholder="Share what's on your mind..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
                  disabled={isLoading}
                  className="flex-1"
                  data-testid="therapist-input"
                />
                <Button 
                  onClick={sendMessage} 
                  className="bg-purple-600 hover:bg-purple-700"
                  disabled={isLoading}
                  data-testid="send-therapist-message"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2 text-center">
                This AI therapist only responds to mental health and therapy-related questions
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
      <Toaster />
    </div>
  );
};

// Community Chat Room
const CommunityRoom = () => {
  const navigate = useNavigate();
  const { communityId } = window.location.pathname.match(/\/community\/(?<communityId>[^/]+)/)?.groups || {};
  const [user, setUser] = useState(null);
  const [community, setCommunity] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isCheckingMembership, setIsCheckingMembership] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);

    if (!communityId) {
      navigate("/communities");
      return;
    }

    // Check membership first
    checkMembershipAndJoin(userData, communityId);

    return () => {
      if (communityId && userData) {
        socket.emit("leave_room", { room_id: communityId, username: userData.username, user_id: userData.user_id });
        socket.off("receive_message");
        socket.off("user_joined");
        socket.off("user_left");
        socket.off("join_error");
        socket.off("message_error");
      }
    };
  }, [navigate, communityId]);

  const checkMembershipAndJoin = async (userData, commId) => {
    try {
      const response = await axios.get(`${API}/communities/${commId}/check-membership/${userData.user_id}`);
      
      if (!response.data.is_member) {
        toast.error("You must join this community first");
        navigate("/communities");
        return;
      }

      setCommunity({
        name: response.data.community_name,
        type: response.data.community_type
      });

      // Join room
      socket.emit("join_room", { 
        room_id: commId, 
        username: userData.username,
        user_id: userData.user_id
      });
      setIsConnected(true);

      // Load previous messages
      const messagesResponse = await axios.get(`${API}/chat/messages/${commId}`);
      setMessages(messagesResponse.data);

      // Listen for messages
      socket.on("receive_message", (data) => {
        setMessages(prev => [...prev, data]);
      });

      socket.on("user_joined", (data) => {
        toast.success(data.message);
      });

      socket.on("user_left", (data) => {
        toast.info(data.message);
      });

      socket.on("join_error", (data) => {
        toast.error(data.message);
        navigate("/communities");
      });

      socket.on("message_error", (data) => {
        toast.error(data.message);
      });

    } catch (error) {
      console.error("Membership check failed", error);
      toast.error("Failed to verify membership");
      navigate("/communities");
    } finally {
      setIsCheckingMembership(false);
    }
  };

  const sendMessage = () => {
    if (!messageText.trim()) return;

    socket.emit("send_message", {
      room_id: communityId,
      user_id: user.user_id,
      username: user.username,
      message: messageText
    });

    setMessageText("");
  };

  if (!user || isCheckingMembership) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
      <div className="max-w-4xl mx-auto h-[calc(100vh-3rem)] flex flex-col">
        <div className="mb-4">
          <Button variant="outline" onClick={() => navigate("/communities")} data-testid="back-to-communities">
            ← Back to Communities
          </Button>
        </div>

        <Card className="flex-1 border-2 border-blue-200 flex flex-col" data-testid="community-room-chat">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Users className="w-6 h-6 text-blue-600" />
                  {community?.name || "Community Chat"}
                </CardTitle>
                <CardDescription>A safe space for support and encouragement</CardDescription>
              </div>
              {isConnected && (
                <Badge className="bg-green-500 text-white" data-testid="connection-status">Connected</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            <ScrollArea className="flex-1 p-4" data-testid="chat-messages">
              <div className="space-y-3">
                {messages.length === 0 && (
                  <div className="text-center py-12 text-gray-500">
                    <Users className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                    <p>No messages yet. Start the conversation!</p>
                  </div>
                )}
                {messages.map((msg) => (
                  <div 
                    key={msg.id} 
                    className={`flex ${msg.user_id === user.user_id ? 'justify-end' : 'justify-start'}`}
                    data-testid={`chat-message-${msg.id}`}
                  >
                    <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                      msg.user_id === user.user_id 
                        ? 'bg-teal-600 text-white' 
                        : 'bg-white border-2 border-gray-200 text-gray-800'
                    }`}>
                      <p className="font-semibold text-sm mb-1">{msg.username}</p>
                      <p>{msg.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
            <div className="p-4 border-t bg-white">
              <div className="flex gap-2">
                <Input
                  placeholder="Type your message..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  className="flex-1"
                  data-testid="message-input"
                />
                <Button 
                  onClick={sendMessage} 
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="send-message-button"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      <Toaster />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/mood-log" element={<MoodLogPage />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/ai-therapist" element={<AITherapist />} />
          <Route path="/communities" element={<Communities />} />
          <Route path="/community/:communityId" element={<CommunityRoom />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;