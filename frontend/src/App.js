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
import { Brain, MessageCircle, Star, Sparkles, Heart, Users, Send, LogOut, Bot, TrendingUp, Trophy, Shield, Phone, Wind, BookOpen, Lightbulb, RefreshCw, MessageSquare, Activity } from "lucide-react";
import Communities from "@/pages/Communities";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import HomePage from "@/pages/HomePage";
import Analytics from "@/pages/Analytics";
import Achievements from "@/pages/Achievements";
import CrisisSupport from "@/pages/CrisisSupport";
import Meditation from "@/pages/Meditation";
import Resources from "@/pages/Resources";
import AITrainer from "@/pages/AITrainer";
import CrisisButton from "@/components/CrisisButton";
import EmergencyPopup from "@/components/EmergencyPopup";
import useCrisisDetection from "@/hooks/useCrisisDetection";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const socket = io(BACKEND_URL);

// Dashboard
const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [achievementCount, setAchievementCount] = useState(0);

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
    fetchAchievementCount(userData.user_id);
  }, [navigate]);

  const fetchProfile = async (userId) => {
    try {
      const response = await axios.get(`${API}/profile/${userId}`);
      setProfile(response.data);
    } catch (error) {
      console.error("Failed to fetch profile", error);
    }
  };

  const fetchAchievementCount = async (userId) => {
    try {
      const response = await axios.get(`${API}/achievements/${userId}`);
      setAchievementCount(response.data.earned_count);
    } catch (error) {
      console.error("Failed to fetch achievement count", error);
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

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
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

          <Link to="/meditation" className="block" data-testid="meditation-card">
            <Card className="h-full border-2 hover:border-indigo-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-indigo-100 rounded-full">
                    <Wind className="w-8 h-8 text-indigo-600" />
                  </div>
                  <CardTitle className="text-xl">Meditation & Breathing</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Practice guided meditation and breathing exercises for stress relief and mindfulness.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Link to="/achievements" className="block" data-testid="achievements-card">
            <Card className="h-full border-2 hover:border-yellow-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1 relative overflow-hidden">
              {achievementCount > 0 && (
                <div className="absolute top-3 right-3 bg-yellow-500 text-white text-xs font-bold rounded-full w-8 h-8 flex items-center justify-center animate-pulse">
                  {achievementCount}
                </div>
              )}
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-yellow-100 rounded-full">
                    <Trophy className="w-8 h-8 text-yellow-600" />
                  </div>
                  <CardTitle className="text-xl">Achievements</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Unlock badges and celebrate your progress on your wellness journey.
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

          <Link to="/crisis-support" className="block" data-testid="crisis-support-card">
            <Card className="h-full border-2 border-purple-300 hover:border-purple-500 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1 bg-gradient-to-br from-purple-50 to-blue-50">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-purple-100 rounded-full">
                    <Shield className="w-8 h-8 text-purple-600" />
                  </div>
                  <CardTitle className="text-xl">Crisis Support</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Access emergency hotlines, create your safety plan, and manage crisis resources. You're not alone.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Link to="/resources" className="block" data-testid="resources-card">
            <Card className="h-full border-2 hover:border-orange-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-orange-100 rounded-full">
                    <BookOpen className="w-8 h-8 text-orange-600" />
                  </div>
                  <CardTitle className="text-xl">Resource Library</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Explore educational articles, videos, and exercises on mental health topics and coping strategies.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Link to="/ai-trainer" className="block" data-testid="ai-trainer-card">
            <Card className="h-full border-2 hover:border-pink-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1 bg-gradient-to-br from-orange-50 to-pink-50">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 bg-gradient-to-r from-orange-500 to-pink-500 rounded-full">
                    <Activity className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-xl">AI Trainer</CardTitle>
                </div>
                <CardDescription className="text-sm">
                  Real-time squat detection with AI pose analysis. Get instant form feedback with visual guidance.
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

  // Initialize crisis detection hook
  const {
    showEmergencyPopup,
    emergencyData,
    crisisSeverity,
    analyzeText,
    closeEmergencyPopup
  } = useCrisisDetection(user?.user_id);

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
      // Analyze mood text for crisis in background
      analyzeText(moodText, 'mood_log', null, true).catch(err => 
        console.error('Crisis analysis error:', err)
      );

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

  const handleCloseEmergencyPopup = () => {
    closeEmergencyPopup();
  };

  const handleAddContacts = () => {
    closeEmergencyPopup();
    navigate("/crisis-support");
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
      
      {/* AI-Powered Emergency Popup */}
      <EmergencyPopup
        isOpen={showEmergencyPopup}
        onClose={handleCloseEmergencyPopup}
        emergencyData={emergencyData}
        severity={crisisSeverity}
        onAddContacts={handleAddContacts}
        userId={user?.user_id}
      />
      
      <Toaster />
    </div>
  );
};

// AI Therapist Chat - Enhanced Version with AI Learning & Crisis Detection
const AITherapist = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showCrisisModal, setShowCrisisModal] = useState(false);
  const [crisisSeverity, setCrisisSeverity] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [showTechniques, setShowTechniques] = useState(false);
  const [suggestedTechniques, setSuggestedTechniques] = useState([]);
  const [moodContext, setMoodContext] = useState(null);
  const [showInsights, setShowInsights] = useState(false);
  const [insights, setInsights] = useState(null);
  const [showMoodCheckIn, setShowMoodCheckIn] = useState(false);

  // Initialize crisis detection hook
  const {
    showEmergencyPopup,
    emergencyData,
    crisisSeverity: aiCrisisSeverity,
    analyzeText,
    closeEmergencyPopup
  } = useCrisisDetection(user?.user_id);

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
      const history = response.data.map(chat => ({
        role: chat.user_message ? 'user' : 'therapist',
        content: chat.user_message || chat.therapist_response,
        user_message: chat.user_message,
        therapist_response: chat.therapist_response,
        techniques: chat.suggested_techniques || [],
        moodContext: chat.mood_context
      }));
      
      // Flatten to show as conversation
      const flatHistory = response.data.map(chat => ([
        { role: 'user', content: chat.user_message, techniques: [], moodContext: null },
        { role: 'therapist', content: chat.therapist_response, techniques: chat.suggested_techniques || [], moodContext: chat.mood_context }
      ])).flat();
      
      setMessages(flatHistory);
      
      // Set session ID from last message
      if (response.data.length > 0) {
        setSessionId(response.data[response.data.length - 1].session_id);
      }
    } catch (error) {
      console.error("Failed to load chat history", error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMsg = { role: 'user', content: inputMessage, techniques: [], moodContext: null };
    const messageToAnalyze = inputMessage;
    setMessages(prev => [...prev, userMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      // First, analyze message for crisis with AI learning
      const conversationHistory = messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content
      }));
      
      // Run crisis analysis in background (don't await to not block chat)
      analyzeText(
        messageToAnalyze,
        'chat',
        { conversation_history: conversationHistory, session_id: sessionId },
        true
      ).catch(err => console.error('Crisis analysis error:', err));

      // Continue with normal therapist response
      const response = await axios.post(`${API}/therapist/chat`, {
        user_id: user.user_id,
        message: messageToAnalyze,
        session_id: sessionId
      });

      // Set session ID if this is first message
      if (!sessionId && response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      const therapistMsg = { 
        role: 'therapist', 
        content: response.data.therapist_response,
        techniques: response.data.suggested_techniques || [],
        moodContext: response.data.mood_context
      };
      setMessages(prev => [...prev, therapistMsg]);
      
      // Store suggested techniques for display
      if (response.data.suggested_techniques && response.data.suggested_techniques.length > 0) {
        setSuggestedTechniques(response.data.suggested_techniques);
      }
      
      // Store mood context
      if (response.data.mood_context) {
        setMoodContext(response.data.mood_context);
      }
      
      // Check if crisis was detected (legacy check)
      if (response.data.crisis_detected) {
        setCrisisSeverity(response.data.crisis_severity);
        setShowCrisisModal(true);
      }
    } catch (error) {
      toast.error("Failed to get response from therapist");
      setMessages(prev => [...prev, { 
        role: 'therapist', 
        content: "I apologize, I'm having trouble connecting right now. Please try again in a moment.",
        techniques: [],
        moodContext: null
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseEmergencyPopup = () => {
    closeEmergencyPopup();
  };

  const handleAddContacts = () => {
    closeEmergencyPopup();
    navigate("/crisis-support");
  };

  const loadInsights = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/therapist/insights/${user.user_id}`);
      setInsights(response.data);
      setShowInsights(true);
    } catch (error) {
      toast.error("Failed to load insights");
    } finally {
      setIsLoading(false);
    }
  };

  const submitMoodCheckIn = async (rating, emotions, note) => {
    try {
      await axios.post(`${API}/therapist/mood-checkin`, {
        user_id: user.user_id,
        mood_rating: rating,
        emotions: emotions,
        note: note
      });
      toast.success("Mood check-in saved!");
      setShowMoodCheckIn(false);
    } catch (error) {
      toast.error("Failed to save mood check-in");
    }
  };

  const startNewSession = () => {
    setSessionId(null);
    setMessages([]);
    setSuggestedTechniques([]);
    setMoodContext(null);
    toast.success("New therapy session started");
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto h-[calc(100vh-3rem)] flex gap-4">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          <div className="mb-4 flex items-center justify-between">
            <Button variant="outline" onClick={() => navigate("/dashboard")} data-testid="back-to-dashboard-therapist">
              ← Back to Dashboard
            </Button>
            <div className="flex gap-2 items-center">
              <Badge className="bg-purple-600 text-white px-4 py-2" data-testid="therapist-badge">
                <Bot className="w-4 h-4 mr-2" />
                Professional AI Therapist
              </Badge>
              <Button variant="outline" size="sm" onClick={startNewSession} title="Start new session">
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <Card className="flex-1 border-2 border-purple-200 flex flex-col shadow-xl" data-testid="therapist-chat-card">
            <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-pink-50">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl flex items-center gap-2">
                    <Bot className="w-7 h-7 text-purple-600" />
                    AI Mental Health Companion
                  </CardTitle>
                  <CardDescription>24/7 evidence-based therapy support with CBT, DBT & mindfulness techniques</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={loadInsights}>
                    <Brain className="w-4 h-4 mr-2" />
                    Insights
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setShowMoodCheckIn(true)}>
                    <Heart className="w-4 h-4 mr-2" />
                    Check-in
                  </Button>
                </div>
              </div>
              {moodContext && (
                <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-xs text-blue-700 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    I've reviewed your recent {moodContext.recent_mood_count} mood logs to provide personalized support
                  </p>
                </div>
              )}
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0">
              <ScrollArea className="flex-1 p-6" data-testid="therapist-messages">
                <div className="space-y-4">
                  {messages.length === 0 && (
                    <div className="text-center py-12" data-testid="welcome-message">
                      <Bot className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-700 mb-2">Welcome to Your Therapy Session</h3>
                      <p className="text-gray-600 max-w-md mx-auto mb-4">
                        I'm your AI mental health companion, trained in CBT, DBT, and mindfulness-based therapies. 
                        I'll provide personalized support based on your mood patterns and history.
                      </p>
                      <div className="flex gap-2 justify-center flex-wrap">
                        <Badge variant="outline" className="bg-white">Crisis Detection</Badge>
                        <Badge variant="outline" className="bg-white">Mood-Aware</Badge>
                        <Badge variant="outline" className="bg-white">CBT/DBT Techniques</Badge>
                      </div>
                    </div>
                  )}
                  {messages.map((msg, idx) => (
                    <div key={idx}>
                      <div 
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        data-testid={`therapist-msg-${idx}`}
                      >
                        <div className={`max-w-2xl ${
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
                      
                      {/* Show therapeutic techniques after therapist message */}
                      {msg.role === 'therapist' && msg.techniques && msg.techniques.length > 0 && (
                        <div className="mt-2 ml-12 space-y-2">
                          {msg.techniques.map((technique, tIdx) => (
                            <div key={tIdx} className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200 max-w-xl">
                              <div className="flex items-start gap-2">
                                <Lightbulb className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                                <div>
                                  <h4 className="font-semibold text-purple-900 text-sm">
                                    {technique.technique_name} 
                                    <Badge variant="outline" className="ml-2 text-xs">{technique.technique_type}</Badge>
                                  </h4>
                                  <p className="text-xs text-gray-700 mt-1">{technique.description}</p>
                                  <div className="mt-2">
                                    <p className="text-xs font-semibold text-gray-700 mb-1">Try this:</p>
                                    <ol className="text-xs text-gray-600 space-y-1 pl-4 list-decimal">
                                      {technique.steps.map((step, sIdx) => (
                                        <li key={sIdx}>{step}</li>
                                      ))}
                                    </ol>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
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
                          <span className="text-xs text-gray-500">Analyzing and generating therapeutic response...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              <div className="p-4 border-t bg-white">
                <div className="flex gap-2">
                  <Input
                    placeholder="Share what's on your mind... I'm here to listen and support you."
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
                  Evidence-based therapy support • Crisis detection enabled • Your conversation is confidential
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar with Quick Info */}
        <div className="w-80 space-y-4 hidden lg:block">
          {suggestedTechniques.length > 0 && (
            <Card className="border-2 border-purple-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-purple-600" />
                  Suggested Techniques
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {suggestedTechniques.map((technique, idx) => (
                  <div key={idx} className="p-3 bg-purple-50 rounded-lg">
                    <h4 className="font-semibold text-sm text-purple-900">{technique.technique_name}</h4>
                    <Badge variant="outline" className="mt-1 text-xs">{technique.technique_type}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <Card className="border-2 border-blue-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-600" />
                Emergency Resources
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button 
                onClick={() => window.open('tel:988')}
                className="w-full bg-red-600 hover:bg-red-700"
                size="sm"
              >
                <Phone className="w-4 h-4 mr-2" />
                Crisis Hotline: 988
              </Button>
              <Button 
                onClick={() => window.open('sms:741741')}
                variant="outline"
                className="w-full"
                size="sm"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Text: 741741
              </Button>
              <p className="text-xs text-gray-600 mt-2">
                24/7 free, confidential support for people in distress
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 border-green-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-green-600" />
                Session Info
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Messages:</span>
                  <span className="font-semibold">{messages.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Session:</span>
                  <span className="font-semibold">{sessionId ? 'Active' : 'New'}</span>
                </div>
                {moodContext && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Mood logs analyzed:</span>
                    <span className="font-semibold">{moodContext.recent_mood_count}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Crisis Resources Modal */}
      {showCrisisModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <CardHeader className="bg-gradient-to-r from-purple-100 to-blue-100">
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Shield className="w-8 h-8 text-purple-600" />
                Crisis Support Resources
              </CardTitle>
              <CardDescription>
                I'm concerned about what you've shared. You're not alone, and help is available right now.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                  <h3 className="font-bold text-red-900 mb-2 flex items-center gap-2">
                    <Phone className="w-5 h-5" />
                    Immediate Help Available
                  </h3>
                  <div className="space-y-2 text-red-800">
                    <p><strong>US Crisis Line:</strong> Call or text <span className="font-bold text-xl">988</span></p>
                    <p><strong>Emergency:</strong> Call <span className="font-bold text-xl">911</span></p>
                    <p><strong>Crisis Text Line:</strong> Text HOME to <span className="font-bold">741741</span></p>
                  </div>
                </div>

                {crisisSeverity === 'high' && (
                  <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-lg">
                    <p className="font-semibold text-amber-900">
                      If you're in immediate danger or having thoughts of hurting yourself right now, 
                      please call 988 or 911 immediately, or go to your nearest emergency room.
                    </p>
                  </div>
                )}

                <div className="space-y-2">
                  <h4 className="font-semibold text-gray-900">Additional Support:</h4>
                  <Button 
                    onClick={() => {
                      setShowCrisisModal(false);
                      navigate('/crisis-support');
                    }}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    View Full Crisis Resources & Safety Plan
                  </Button>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">What Helps Right Now:</h4>
                  <ul className="list-disc list-inside space-y-1 text-blue-800 text-sm">
                    <li>Reach out to someone you trust</li>
                    <li>Use grounding techniques (5-4-3-2-1: 5 things you see, 4 you hear, 3 you touch, 2 you smell, 1 you taste)</li>
                    <li>Go to a safe, public place</li>
                    <li>Remove immediate access to harmful means</li>
                    <li>Remember: This feeling is temporary, even if it doesn't feel like it now</li>
                  </ul>
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={() => setShowCrisisModal(false)}
                    variant="outline"
                    className="flex-1"
                  >
                    Continue Conversation
                  </Button>
                  <Button 
                    onClick={() => window.open('tel:988')}
                    className="flex-1 bg-red-600 hover:bg-red-700"
                  >
                    <Phone className="w-4 h-4 mr-2" />
                    Call 988 Now
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Insights Modal */}
      {showInsights && insights && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <CardHeader className="bg-gradient-to-r from-purple-100 to-blue-100">
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Brain className="w-8 h-8 text-purple-600" />
                Your Therapy Insights
              </CardTitle>
              <CardDescription>
                AI-powered analysis of your mental health journey
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <p className="text-sm text-gray-600">Total Sessions</p>
                    <p className="text-2xl font-bold text-purple-900">{insights.total_sessions}</p>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-gray-600">Conversations</p>
                    <p className="text-2xl font-bold text-blue-900">{insights.total_conversations}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-gray-600">Mood Logs</p>
                    <p className="text-2xl font-bold text-green-900">{insights.total_mood_logs}</p>
                  </div>
                  <div className="p-4 bg-pink-50 rounded-lg">
                    <p className="text-sm text-gray-600">Check-ins</p>
                    <p className="text-2xl font-bold text-pink-900">{insights.total_checkins}</p>
                  </div>
                </div>

                <div className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border-2 border-purple-200">
                  <h3 className="font-bold text-lg text-purple-900 mb-3 flex items-center gap-2">
                    <Sparkles className="w-5 h-5" />
                    AI Analysis
                  </h3>
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap text-gray-700 leading-relaxed">{insights.ai_insights}</p>
                  </div>
                </div>

                <Button 
                  onClick={() => setShowInsights(false)}
                  className="w-full bg-purple-600 hover:bg-purple-700"
                >
                  Close Insights
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Mood Check-in Modal */}
      {showMoodCheckIn && <MoodCheckInModal onClose={() => setShowMoodCheckIn(false)} onSubmit={submitMoodCheckIn} />}
      
      {/* AI-Powered Emergency Popup */}
      <EmergencyPopup
        isOpen={showEmergencyPopup}
        onClose={handleCloseEmergencyPopup}
        emergencyData={emergencyData}
        severity={aiCrisisSeverity}
        onAddContacts={handleAddContacts}
        userId={user?.user_id}
      />
      
      <Toaster />
    </div>
  );
};

// Mood Check-in Modal Component
const MoodCheckInModal = ({ onClose, onSubmit }) => {
  const [rating, setRating] = useState(5);
  const [selectedEmotions, setSelectedEmotions] = useState([]);
  const [note, setNote] = useState("");

  const emotions = [
    "Happy", "Sad", "Anxious", "Calm", "Angry", "Peaceful", 
    "Stressed", "Energized", "Tired", "Hopeful", "Frustrated", "Content"
  ];

  const toggleEmotion = (emotion) => {
    setSelectedEmotions(prev => 
      prev.includes(emotion) 
        ? prev.filter(e => e !== emotion)
        : [...prev, emotion]
    );
  };

  const handleSubmit = () => {
    if (selectedEmotions.length === 0) {
      toast.error("Please select at least one emotion");
      return;
    }
    onSubmit(rating, selectedEmotions, note);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="bg-gradient-to-r from-purple-100 to-pink-100">
          <CardTitle className="flex items-center gap-2">
            <Heart className="w-6 h-6 text-purple-600" />
            Quick Mood Check-in
          </CardTitle>
          <CardDescription>How are you feeling right now?</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold mb-3">Rate your mood (1-10)</label>
              <div className="flex items-center gap-4">
                <input 
                  type="range" 
                  min="1" 
                  max="10" 
                  value={rating}
                  onChange={(e) => setRating(parseInt(e.target.value))}
                  className="flex-1"
                />
                <span className="text-2xl font-bold text-purple-600 w-12 text-center">{rating}</span>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Very Low</span>
                <span>Very High</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Select your emotions</label>
              <div className="flex flex-wrap gap-2">
                {emotions.map(emotion => (
                  <Badge
                    key={emotion}
                    variant={selectedEmotions.includes(emotion) ? "default" : "outline"}
                    className={`cursor-pointer transition-all ${
                      selectedEmotions.includes(emotion) 
                        ? 'bg-purple-600 text-white' 
                        : 'hover:bg-purple-100'
                    }`}
                    onClick={() => toggleEmotion(emotion)}
                  >
                    {emotion}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Quick note (optional)</label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Anything specific on your mind?"
                className="w-full p-3 border rounded-lg resize-none"
                rows="3"
              />
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleSubmit} className="flex-1 bg-purple-600 hover:bg-purple-700">
                Save Check-in
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
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

const AppWithCrisisButton = () => {
  const location = window.location;
  const showCrisisButton = !['/login', '/register', '/'].includes(location.pathname);
  
  return (
    <>
      {showCrisisButton && <CrisisButton />}
    </>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AppWithCrisisButton />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/mood-log" element={<MoodLogPage />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/meditation" element={<Meditation />} />
          <Route path="/achievements" element={<Achievements />} />
          <Route path="/ai-therapist" element={<AITherapist />} />
          <Route path="/communities" element={<Communities />} />
          <Route path="/community/:communityId" element={<CommunityRoom />} />
          <Route path="/crisis-support" element={<CrisisSupport />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/ai-trainer" element={<AITrainer />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;