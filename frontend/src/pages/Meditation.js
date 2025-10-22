import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  Brain,
  Wind,
  Sparkles,
  Play,
  Pause,
  CheckCircle,
  Clock,
  Star,
  ArrowLeft,
  Heart,
  Moon,
  Focus,
  Zap,
  Activity,
  Award,
  TrendingUp,
  Lightbulb
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Meditation = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [breathingExercises, setBreathingExercises] = useState([]);
  const [meditationSessions, setMeditationSessions] = useState([]);
  const [progress, setProgress] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedContent, setSelectedContent] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [breathPhase, setBreathPhase] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const timerRef = useRef(null);
  const audioContextRef = useRef(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    
    fetchBreathingExercises();
    fetchMeditationSessions();
    fetchProgress(userData.user_id);
    fetchRecommendations(userData.user_id);
  }, [navigate]);

  const fetchBreathingExercises = async () => {
    try {
      const response = await axios.get(`${API}/meditation/exercises`);
      setBreathingExercises(response.data.exercises);
    } catch (error) {
      console.error("Failed to fetch breathing exercises", error);
      toast.error("Failed to load breathing exercises");
    }
  };

  const fetchMeditationSessions = async () => {
    try {
      const response = await axios.get(`${API}/meditation/sessions`);
      setMeditationSessions(response.data.sessions);
    } catch (error) {
      console.error("Failed to fetch meditation sessions", error);
      toast.error("Failed to load meditation sessions");
    }
  };

  const fetchProgress = async (userId) => {
    try {
      const response = await axios.get(`${API}/meditation/progress/${userId}`);
      setProgress(response.data);
    } catch (error) {
      console.error("Failed to fetch progress", error);
    }
  };

  const fetchRecommendations = async (userId) => {
    try {
      const response = await axios.get(`${API}/meditation/recommendations/${userId}`);
      setRecommendations(response.data.recommendations);
    } catch (error) {
      console.error("Failed to fetch recommendations", error);
    }
  };

  const playTone = (frequency, duration) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    const context = audioContextRef.current;
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = "sine";

    gainNode.gain.setValueAtTime(0.3, context.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + duration);

    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + duration);
  };

  const startSession = async (content, type) => {
    try {
      const duration = type === "breathing" ? content.duration : content.duration * 60;
      
      const response = await axios.post(`${API}/meditation/start`, {
        user_id: user.user_id,
        session_type: type,
        content_id: content.id,
        duration: duration
      });
      
      setCurrentSessionId(response.data.id);
      setSelectedContent({ ...content, type });
      setCurrentTime(0);
      setIsPlaying(true);
      playTone(528, 0.3); // Start tone
      
      if (type === "breathing") {
        startBreathingTimer(content);
      } else {
        startMeditationTimer(duration);
      }
    } catch (error) {
      console.error("Failed to start session", error);
      toast.error("Failed to start session");
    }
  };

  const startBreathingTimer = (exercise) => {
    const pattern = exercise.pattern.split("-").map(Number);
    const phases = ["Breathe In", "Hold", "Breathe Out", "Hold"];
    let phaseIndex = 0;
    let secondsInPhase = 0;

    timerRef.current = setInterval(() => {
      setCurrentTime(prev => {
        const newTime = prev + 1;
        
        if (newTime >= exercise.duration) {
          completeSession();
          return prev;
        }
        
        secondsInPhase++;
        
        // Check if we need to move to next phase
        if (secondsInPhase >= pattern[phaseIndex]) {
          secondsInPhase = 0;
          phaseIndex = (phaseIndex + 1) % pattern.length;
          
          // Play tone at phase change
          if (phaseIndex === 0) {
            playTone(528, 0.2); // In breath
          } else if (phaseIndex === 2) {
            playTone(440, 0.2); // Out breath
          }
        }
        
        setBreathPhase(`${phases[phaseIndex]} (${pattern[phaseIndex] - secondsInPhase}s)`);
        
        return newTime;
      });
    }, 1000);
  };

  const startMeditationTimer = (totalSeconds) => {
    timerRef.current = setInterval(() => {
      setCurrentTime(prev => {
        const newTime = prev + 1;
        
        if (newTime >= totalSeconds) {
          completeSession();
          return prev;
        }
        
        // Play soft chime every minute
        if (newTime % 60 === 0 && newTime > 0) {
          playTone(528, 0.1);
        }
        
        return newTime;
      });
    }, 1000);
  };

  const pauseSession = () => {
    setIsPlaying(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const resumeSession = () => {
    setIsPlaying(true);
    if (selectedContent.type === "breathing") {
      startBreathingTimer(selectedContent);
    } else {
      const totalSeconds = selectedContent.duration * 60;
      startMeditationTimer(totalSeconds);
    }
  };

  const completeSession = async () => {
    setIsPlaying(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    try {
      playTone(528, 0.5); // Completion tone
      
      const response = await axios.post(`${API}/meditation/complete`, {
        session_id: currentSessionId
      });
      
      toast.success(`🎉 Session completed! +${response.data.stars_earned} wellness stars`);
      
      // Refresh progress
      fetchProgress(user.user_id);
      
      // Reset
      setTimeout(() => {
        setSelectedContent(null);
        setCurrentTime(0);
        setCurrentSessionId(null);
        setBreathPhase("");
      }, 2000);
    } catch (error) {
      console.error("Failed to complete session", error);
      toast.error("Failed to mark session as complete");
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "stress_relief": return <Heart className="w-5 h-5" />;
      case "sleep": return <Moon className="w-5 h-5" />;
      case "focus": return <Focus className="w-5 h-5" />;
      case "anxiety": return <Sparkles className="w-5 h-5" />;
      default: return <Brain className="w-5 h-5" />;
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case "stress_relief": return "bg-rose-100 text-rose-700 border-rose-300";
      case "sleep": return "bg-indigo-100 text-indigo-700 border-indigo-300";
      case "focus": return "bg-amber-100 text-amber-700 border-amber-300";
      case "anxiety": return "bg-purple-100 text-purple-700 border-purple-300";
      default: return "bg-teal-100 text-teal-700 border-teal-300";
    }
  };

  const filteredMeditations = selectedCategory === "all" 
    ? meditationSessions 
    : meditationSessions.filter(s => s.category === selectedCategory);

  if (!user) return null;

  // Session Player View
  if (selectedContent) {
    const totalSeconds = selectedContent.type === "breathing" 
      ? selectedContent.duration 
      : selectedContent.duration * 60;
    const progressPercentage = (currentTime / totalSeconds) * 100;

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-6">
        <Card className="w-full max-w-2xl shadow-2xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl">
                {selectedContent.type === "breathing" ? selectedContent.name : selectedContent.title}
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => {
                pauseSession();
                setSelectedContent(null);
                setCurrentTime(0);
              }}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Exit
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Progress Circle */}
            <div className="flex justify-center">
              <div className="relative w-64 h-64">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="128"
                    cy="128"
                    r="120"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="8"
                  />
                  <circle
                    cx="128"
                    cy="128"
                    r="120"
                    fill="none"
                    stroke="url(#gradient)"
                    strokeWidth="8"
                    strokeDasharray={`${2 * Math.PI * 120}`}
                    strokeDashoffset={`${2 * Math.PI * 120 * (1 - progressPercentage / 100)}`}
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#8b5cf6" />
                      <stop offset="100%" stopColor="#ec4899" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-5xl font-bold text-gray-900">
                    {formatTime(totalSeconds - currentTime)}
                  </div>
                  {selectedContent.type === "breathing" && breathPhase && (
                    <div className="text-lg text-gray-600 mt-2 animate-pulse">
                      {breathPhase}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg">
              <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-amber-500" />
                Current Step
              </h3>
              <ScrollArea className="h-32">
                <ul className="space-y-2">
                  {selectedContent.instructions.map((instruction, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <span className="text-purple-500 mt-1">•</span>
                      <span>{instruction}</span>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </div>

            {/* Controls */}
            <div className="flex justify-center gap-4">
              {isPlaying ? (
                <Button 
                  onClick={pauseSession}
                  size="lg"
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                >
                  <Pause className="w-5 h-5 mr-2" />
                  Pause
                </Button>
              ) : (
                <Button 
                  onClick={resumeSession}
                  size="lg"
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                >
                  <Play className="w-5 h-5 mr-2" />
                  Resume
                </Button>
              )}
              <Button 
                onClick={completeSession}
                variant="outline"
                size="lg"
              >
                <CheckCircle className="w-5 h-5 mr-2" />
                Complete
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main Meditation Dashboard
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/dashboard")}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Meditation & Breathing</h1>
              <p className="text-gray-600">Find calm and clarity through guided practices</p>
            </div>
          </div>
        </div>

        {/* Progress Stats */}
        {progress && progress.total_sessions > 0 && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold">{progress.total_sessions}</div>
                    <div className="text-sm opacity-90">Total Sessions</div>
                  </div>
                  <Activity className="w-8 h-8 opacity-80" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-pink-500 to-pink-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold">{progress.total_minutes}</div>
                    <div className="text-sm opacity-90">Minutes Practiced</div>
                  </div>
                  <Clock className="w-8 h-8 opacity-80" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold">{progress.current_streak}</div>
                    <div className="text-sm opacity-90">Day Streak</div>
                  </div>
                  <Zap className="w-8 h-8 opacity-80" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold">{progress.total_sessions * 2}</div>
                    <div className="text-sm opacity-90">Stars Earned</div>
                  </div>
                  <Award className="w-8 h-8 opacity-80" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-6 h-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-900">Recommended For You</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              {recommendations.map((rec, index) => {
                const content = rec.content;
                return (
                  <Card 
                    key={index}
                    className="border-2 border-purple-200 hover:border-purple-400 transition-all hover:shadow-lg cursor-pointer"
                    onClick={() => startSession(content, rec.type)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <Badge className="mb-2 bg-purple-100 text-purple-700 border-purple-300">
                            {rec.type === "breathing" ? "Breathing" : "Meditation"}
                          </Badge>
                          <CardTitle className="text-lg">
                            {rec.type === "breathing" ? content.name : content.title}
                          </CardTitle>
                        </div>
                        <Sparkles className="w-5 h-5 text-purple-500" />
                      </div>
                      <CardDescription className="text-sm mt-2">
                        {rec.reason}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="w-4 h-4" />
                        <span>
                          {rec.type === "breathing" 
                            ? `${Math.floor(content.duration / 60)} min`
                            : `${content.duration} min`
                          }
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Breathing Exercises */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Wind className="w-6 h-6 text-teal-600" />
            <h2 className="text-2xl font-bold text-gray-900">Quick Breathing Exercises</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {breathingExercises.map((exercise) => (
              <Card 
                key={exercise.id}
                className="border-2 hover:border-teal-400 transition-all hover:shadow-lg cursor-pointer"
                onClick={() => startSession(exercise, "breathing")}
              >
                <CardHeader>
                  <div className="flex items-center justify-between mb-2">
                    <Badge className="bg-teal-100 text-teal-700 border-teal-300">
                      {Math.floor(exercise.duration / 60)} min
                    </Badge>
                    <Wind className="w-5 h-5 text-teal-600" />
                  </div>
                  <CardTitle className="text-lg">{exercise.name}</CardTitle>
                  <CardDescription className="text-sm mt-2">
                    {exercise.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-gray-700">Benefits:</div>
                    <div className="flex flex-wrap gap-1">
                      {exercise.benefits.slice(0, 2).map((benefit, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {benefit}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Meditation Sessions */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Brain className="w-6 h-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-900">Guided Meditation Sessions</h2>
            </div>
            <div className="flex gap-2">
              <Button
                variant={selectedCategory === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory("all")}
              >
                All
              </Button>
              <Button
                variant={selectedCategory === "stress_relief" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory("stress_relief")}
              >
                Stress Relief
              </Button>
              <Button
                variant={selectedCategory === "sleep" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory("sleep")}
              >
                Sleep
              </Button>
              <Button
                variant={selectedCategory === "focus" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory("focus")}
              >
                Focus
              </Button>
              <Button
                variant={selectedCategory === "anxiety" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory("anxiety")}
              >
                Anxiety
              </Button>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredMeditations.map((session) => (
              <Card 
                key={session.id}
                className="border-2 hover:border-purple-400 transition-all hover:shadow-lg cursor-pointer"
                onClick={() => startSession(session, "meditation")}
              >
                <CardHeader>
                  <div className="flex items-center justify-between mb-2">
                    <Badge className={getCategoryColor(session.category)}>
                      {session.duration} min
                    </Badge>
                    {getCategoryIcon(session.category)}
                  </div>
                  <CardTitle className="text-lg">{session.title}</CardTitle>
                  <CardDescription className="text-sm mt-2">
                    {session.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Star className="w-4 h-4 text-yellow-500" />
                    <span className="font-medium">{session.goal}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Meditation;
