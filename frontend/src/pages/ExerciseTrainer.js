import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Dumbbell, Play, Square, Camera, CameraOff, CheckCircle, AlertCircle, ArrowLeft, Trophy, Flame, Target, TrendingUp, Activity } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ExerciseTrainer = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [targetReps, setTargetReps] = useState(10);
  const [useAICoach, setUseAICoach] = useState(true);
  const [isExercising, setIsExercising] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const [completedReps, setCompletedReps] = useState(0);
  const [timer, setTimer] = useState(0);
  const [cameraActive, setCameraActive] = useState(false);
  const [formFeedback, setFormFeedback] = useState([]);
  const [progress, setProgress] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [sessionResults, setSessionResults] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState("all");
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const poseDetectionRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const repCountStateRef = useRef({ 
    lastPosition: null, 
    repInProgress: false,
    positionConfidence: 0
  });

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    if (!storedUser) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    loadExercises();
    loadProgress(userData.user_id);
  }, [navigate]);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      stopCamera();
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, []);

  const loadExercises = async () => {
    try {
      const response = await axios.get(`${API}/exercises/list`);
      setExercises(response.data.exercises);
    } catch (error) {
      console.error("Failed to load exercises", error);
      toast.error("Failed to load exercises");
    }
  };

  const loadProgress = async (userId) => {
    try {
      const response = await axios.get(`${API}/exercises/progress/${userId}`);
      setProgress(response.data);
    } catch (error) {
      console.error("Failed to load progress", error);
    }
  };

  const startSession = async () => {
    try {
      const response = await axios.post(`${API}/exercises/session/start`, {
        user_id: user.user_id,
        exercise_id: selectedExercise.id,
        target_reps: targetReps,
        used_ai_coach: useAICoach
      });
      
      setCurrentSession(response.data);
      setIsExercising(true);
      setCompletedReps(0);
      setTimer(0);
      setFormFeedback([]);
      
      // Start timer
      timerIntervalRef.current = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
      
      // Start camera if AI coach is enabled
      if (useAICoach) {
        await startCamera();
      }
      
      toast.success("Session started! Let's go!");
    } catch (error) {
      console.error("Failed to start session", error);
      toast.error("Failed to start session");
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraActive(true);
        
        // Wait for video to be ready then initialize pose detection
        videoRef.current.onloadedmetadata = () => {
          initPoseDetection();
        };
      }
    } catch (error) {
      console.error("Camera access denied", error);
      toast.error("Camera access required for AI Coach");
      setUseAICoach(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject;
      const tracks = stream.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
      setCameraActive(false);
    }
    
    if (poseDetectionRef.current) {
      poseDetectionRef.current = null;
    }
  };

  const initPoseDetection = async () => {
    // Load MediaPipe Pose via CDN
    if (typeof window.Pose === 'undefined') {
      toast.error("Pose detection library not loaded. Please refresh the page.");
      console.error("MediaPipe Pose not found on window object");
      return;
    }
    
    try {
      const pose = new window.Pose({
        locateFile: (file) => {
          return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
        }
      });
      
      pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        enableSegmentation: false,
        smoothSegmentation: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
      });
      
      pose.onResults(onPoseResults);
      poseDetectionRef.current = pose;
      
      // Ensure canvas is properly sized
      if (canvasRef.current) {
        canvasRef.current.width = 640;
        canvasRef.current.height = 480;
      }
      
      // Start detection loop
      detectPose();
      toast.success("AI Coach activated!");
    } catch (error) {
      console.error("Failed to initialize pose detection", error);
      toast.error("Failed to initialize AI Coach: " + error.message);
    }
  };

  const detectPose = async () => {
    if (!poseDetectionRef.current || !videoRef.current) {
      return;
    }
    
    try {
      await poseDetectionRef.current.send({ image: videoRef.current });
    } catch (error) {
      console.error("Pose detection error:", error);
    }
    
    // Continue loop regardless of isExercising to maintain smooth video
    requestAnimationFrame(detectPose);
  };

  const onPoseResults = (results) => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw video
    if (videoRef.current) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    }
    
    // Draw pose landmarks if detected
    if (results.poseLandmarks) {
      drawLandmarks(ctx, results.poseLandmarks);
      
      // Analyze form and count reps only if exercising
      if (isExercising && selectedExercise) {
        analyzeFormAndCountReps(results.poseLandmarks);
      }
    } else {
      // No pose detected - show message
      ctx.fillStyle = 'rgba(255, 0, 0, 0.7)';
      ctx.fillRect(10, 10, 300, 50);
      ctx.fillStyle = 'white';
      ctx.font = 'bold 18px Arial';
      ctx.fillText('⚠️ No body detected', 20, 40);
    }
    
    // Draw overlay UI (rep counter, feedback)
    drawOverlayUI(ctx);
  };

  const drawLandmarks = (ctx, landmarks) => {
    // Draw connections
    const connections = [
      [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], // Arms
      [11, 23], [12, 24], [23, 24], // Torso
      [23, 25], [24, 26], [25, 27], [26, 28], // Legs
      [27, 29], [27, 31], [28, 30], [28, 32] // Feet
    ];
    
    // Determine line color based on form feedback
    const isGoodForm = formFeedback.some(f => f.includes('Perfect') || f.includes('Great') || f.includes('Excellent'));
    const isBadForm = formFeedback.some(f => f.includes('incorrect') || f.includes('Wrong') || f.includes('too'));
    
    ctx.strokeStyle = isGoodForm ? '#00FF00' : isBadForm ? '#FF4444' : '#FFFF00';
    ctx.lineWidth = 3;
    ctx.shadowBlur = 10;
    ctx.shadowColor = ctx.strokeStyle;
    
    connections.forEach(([start, end]) => {
      const startPoint = landmarks[start];
      const endPoint = landmarks[end];
      
      if (startPoint && endPoint && startPoint.visibility > 0.5 && endPoint.visibility > 0.5) {
        ctx.beginPath();
        ctx.moveTo(startPoint.x * canvasRef.current.width, startPoint.y * canvasRef.current.height);
        ctx.lineTo(endPoint.x * canvasRef.current.width, endPoint.y * canvasRef.current.height);
        ctx.stroke();
      }
    });
    
    // Draw key points
    ctx.shadowBlur = 15;
    [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28].forEach(idx => {
      const point = landmarks[idx];
      if (point && point.visibility > 0.5) {
        // Outer glow
        ctx.fillStyle = ctx.strokeStyle;
        ctx.beginPath();
        ctx.arc(
          point.x * canvasRef.current.width,
          point.y * canvasRef.current.height,
          8, 0, 2 * Math.PI
        );
        ctx.fill();
        
        // Inner dot
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(
          point.x * canvasRef.current.width,
          point.y * canvasRef.current.height,
          4, 0, 2 * Math.PI
        );
        ctx.fill();
      }
    });
    
    ctx.shadowBlur = 0;
  };

  const drawOverlayUI = (ctx) => {
    if (!isExercising) return;
    
    const canvas = canvasRef.current;
    
    // Draw rep counter (top right)
    const progress = completedReps / targetReps;
    const counterBg = progress >= 1 ? '#10B981' : progress >= 0.5 ? '#3B82F6' : '#6366F1';
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(canvas.width - 180, 10, 170, 100);
    
    ctx.fillStyle = counterBg;
    ctx.fillRect(canvas.width - 180, 10, 170, 8);
    ctx.fillRect(canvas.width - 180, 10, 170 * progress, 8);
    
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 48px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(completedReps, canvas.width - 95, 65);
    
    ctx.font = '16px Arial';
    ctx.fillText(`of ${targetReps} reps`, canvas.width - 95, 90);
    
    // Draw form feedback (bottom center)
    if (formFeedback.length > 0) {
      const feedback = formFeedback[formFeedback.length - 1];
      const isGood = feedback.includes('Perfect') || feedback.includes('Great') || feedback.includes('Excellent') || feedback.includes('Good');
      const isBad = feedback.includes('incorrect') || feedback.includes('Wrong') || feedback.includes('too');
      
      const bgColor = isGood ? 'rgba(16, 185, 129, 0.9)' : isBad ? 'rgba(239, 68, 68, 0.9)' : 'rgba(251, 191, 36, 0.9)';
      const icon = isGood ? '✓' : isBad ? '✗' : '⚠';
      
      ctx.font = '18px Arial';
      const textWidth = ctx.measureText(feedback).width;
      const boxWidth = textWidth + 80;
      const boxX = (canvas.width - boxWidth) / 2;
      
      ctx.fillStyle = bgColor;
      ctx.fillRect(boxX, canvas.height - 80, boxWidth, 60);
      
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 24px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(icon, boxX + 15, canvas.height - 45);
      
      ctx.font = '18px Arial';
      ctx.fillText(feedback, boxX + 50, canvas.height - 45);
    }
    
    // Draw timer (top left)
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(10, 10, 120, 50);
    
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(formatTime(timer), 20, 43);
    
    ctx.textAlign = 'start'; // Reset
  };

  const calculateAngle = (a, b, c) => {
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    
    if (angle > 180.0) {
      angle = 360 - angle;
    }
    
    return angle;
  };

  const analyzeFormAndCountReps = (landmarks) => {
    if (!selectedExercise || completedReps >= targetReps) return;
    
    const exerciseId = selectedExercise.id;
    
    // Exercise-specific rep counting logic
    if (exerciseId === 'push-ups') {
      analyzePushUps(landmarks);
    } else if (exerciseId === 'squats') {
      analyzeSquats(landmarks);
    } else if (exerciseId === 'jumping-jacks') {
      analyzeJumpingJacks(landmarks);
    } else if (exerciseId === 'lunges') {
      analyzeLunges(landmarks);
    } else if (exerciseId === 'high-knees') {
      analyzeHighKnees(landmarks);
    } else {
      // Generic movement detection for other exercises
      analyzeGenericMovement(landmarks);
    }
  };

  const analyzePushUps = (landmarks) => {
    // Calculate elbow angles
    const leftElbowAngle = calculateAngle(
      landmarks[11], // left shoulder
      landmarks[13], // left elbow
      landmarks[15]  // left wrist
    );
    
    const rightElbowAngle = calculateAngle(
      landmarks[12], // right shoulder
      landmarks[14], // right elbow
      landmarks[16]  // right wrist
    );
    
    const avgElbowAngle = (leftElbowAngle + rightElbowAngle) / 2;
    
    // Check body alignment (back should be straight)
    const shoulder = landmarks[11];
    const hip = landmarks[23];
    const knee = landmarks[25];
    const backAngle = calculateAngle(shoulder, hip, knee);
    
    // Rep counting logic
    if (avgElbowAngle < 100 && !repCountStateRef.current.repInProgress) {
      // Down position
      repCountStateRef.current.repInProgress = true;
      repCountStateRef.current.lastPosition = 'down';
      
      if (avgElbowAngle < 90) {
        setFormFeedback(["Perfect depth! ✓"]);
      } else {
        setFormFeedback(["Good! Go a bit lower"]);
      }
      
      // Check form
      if (backAngle < 160) {
        setFormFeedback(["Keep your back straight!"]);
      }
    } else if (avgElbowAngle > 160 && repCountStateRef.current.lastPosition === 'down') {
      // Up position - count rep
      setCompletedReps(prev => {
        const newCount = prev + 1;
        if (newCount >= targetReps) {
          setTimeout(() => completeSession(), 500);
        }
        return newCount;
      });
      repCountStateRef.current.repInProgress = false;
      repCountStateRef.current.lastPosition = 'up';
      setFormFeedback(["Excellent rep! ✓"]);
      toast.success(`Rep ${completedReps + 1} completed!`, { duration: 1000 });
    }
    
    // Continuous form feedback
    if (avgElbowAngle > 120 && avgElbowAngle < 160 && !repCountStateRef.current.repInProgress) {
      if (backAngle < 160) {
        setFormFeedback(["⚠ Keep back straight"]);
      } else {
        setFormFeedback(["Ready for next rep"]);
      }
    }
  };

  const analyzeSquats = (landmarks) => {
    // Calculate knee angles
    const leftKneeAngle = calculateAngle(
      landmarks[23], // left hip
      landmarks[25], // left knee
      landmarks[27]  // left ankle
    );
    
    const rightKneeAngle = calculateAngle(
      landmarks[24], // right hip
      landmarks[26], // right knee
      landmarks[28]  // right ankle
    );
    
    const avgKneeAngle = (leftKneeAngle + rightKneeAngle) / 2;
    
    // Rep counting
    if (avgKneeAngle < 110 && !repCountStateRef.current.repInProgress) {
      repCountStateRef.current.repInProgress = true;
      repCountStateRef.current.lastPosition = 'down';
      setFormFeedback(["Nice squat depth!"]);
    } else if (avgKneeAngle > 160 && repCountStateRef.current.lastPosition === 'down') {
      setCompletedReps(prev => {
        const newCount = prev + 1;
        if (newCount >= targetReps) {
          setTimeout(() => completeSession(), 500);
        }
        return newCount;
      });
      repCountStateRef.current.repInProgress = false;
      repCountStateRef.current.lastPosition = 'up';
      setFormFeedback(["Excellent! ✓"]);
      toast.success(`Rep ${completedReps + 1} completed!`, { duration: 1000 });
    }
  };

  const analyzeJumpingJacks = (landmarks) => {
    // Check arm and leg positions
    const leftWrist = landmarks[15];
    const rightWrist = landmarks[16];
    const leftAnkle = landmarks[27];
    const rightAnkle = landmarks[28];
    const nose = landmarks[0];
    
    // Arms up check (wrists above shoulders)
    const armsUp = leftWrist.y < nose.y && rightWrist.y < nose.y;
    
    // Legs apart check
    const legDistance = Math.abs(leftAnkle.x - rightAnkle.x);
    const legsApart = legDistance > 0.2;
    
    if (armsUp && legsApart && !repCountStateRef.current.repInProgress) {
      repCountStateRef.current.repInProgress = true;
      repCountStateRef.current.lastPosition = 'open';
    } else if (!armsUp && !legsApart && repCountStateRef.current.lastPosition === 'open') {
      setCompletedReps(prev => {
        const newCount = prev + 1;
        if (newCount >= targetReps) {
          setTimeout(() => completeSession(), 500);
        }
        return newCount;
      });
      repCountStateRef.current.repInProgress = false;
      repCountStateRef.current.lastPosition = 'closed';
      toast.success(`Rep ${completedReps + 1} completed!`, { duration: 1000 });
    }
  };

  const analyzeLunges = (landmarks) => {
    // Simplified lunge detection - check knee angles
    const leftKneeAngle = calculateAngle(landmarks[23], landmarks[25], landmarks[27]);
    const rightKneeAngle = calculateAngle(landmarks[24], landmarks[26], landmarks[28]);
    
    const minKneeAngle = Math.min(leftKneeAngle, rightKneeAngle);
    
    if (minKneeAngle < 100 && !repCountStateRef.current.repInProgress) {
      repCountStateRef.current.repInProgress = true;
      repCountStateRef.current.lastPosition = 'down';
    } else if (minKneeAngle > 160 && repCountStateRef.current.lastPosition === 'down') {
      setCompletedReps(prev => {
        const newCount = prev + 1;
        if (newCount >= targetReps) {
          setTimeout(() => completeSession(), 500);
        }
        return newCount;
      });
      repCountStateRef.current.repInProgress = false;
      toast.success(`Rep ${completedReps + 1} completed!`, { duration: 1000 });
    }
  };

  const analyzeHighKnees = (landmarks) => {
    // Check if knee is raised to hip level
    const leftKnee = landmarks[25];
    const rightKnee = landmarks[26];
    const leftHip = landmarks[23];
    const rightHip = landmarks[24];
    
    const leftKneeRaised = leftKnee.y < leftHip.y;
    const rightKneeRaised = rightKnee.y < rightHip.y;
    
    if ((leftKneeRaised || rightKneeRaised) && repCountStateRef.current.lastPosition !== 'raised') {
      setCompletedReps(prev => {
        const newCount = prev + 1;
        if (newCount >= targetReps) {
          setTimeout(() => completeSession(), 500);
        }
        return newCount;
      });
      repCountStateRef.current.lastPosition = 'raised';
      setTimeout(() => {
        repCountStateRef.current.lastPosition = null;
      }, 500);
      toast.success(`Rep ${completedReps + 1} completed!`, { duration: 1000 });
    }
  };

  const analyzeGenericMovement = (landmarks) => {
    // Generic movement detection based on overall body movement
    const currentCentroid = {
      x: landmarks.reduce((sum, l) => sum + l.x, 0) / landmarks.length,
      y: landmarks.reduce((sum, l) => sum + l.y, 0) / landmarks.length
    };
    
    if (repCountStateRef.current.lastPosition) {
      const movement = Math.abs(currentCentroid.y - repCountStateRef.current.lastPosition.y);
      
      if (movement > 0.05 && !repCountStateRef.current.repInProgress) {
        repCountStateRef.current.repInProgress = true;
        setTimeout(() => {
          setCompletedReps(prev => {
            const newCount = prev + 1;
            if (newCount >= targetReps) {
              setTimeout(() => completeSession(), 500);
            }
            return newCount;
          });
          repCountStateRef.current.repInProgress = false;
          toast.success(`Rep ${completedReps + 1} completed!`, { duration: 1000 });
        }, 1000);
      }
    }
    
    repCountStateRef.current.lastPosition = currentCentroid;
  };

  const completeSession = async () => {
    try {
      // Stop timer
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      
      // Stop camera
      stopCamera();
      
      const response = await axios.post(`${API}/exercises/session/complete`, {
        session_id: currentSession.session_id,
        completed_reps: completedReps >= targetReps ? targetReps : completedReps,
        duration_seconds: timer,
        form_accuracy: useAICoach ? 85 : null // Placeholder accuracy
      });
      
      setSessionResults(response.data);
      setShowResults(true);
      setIsExercising(false);
      
      // Refresh progress
      loadProgress(user.user_id);
    } catch (error) {
      console.error("Failed to complete session", error);
      toast.error("Failed to save session");
    }
  };

  const manualIncrement = () => {
    if (completedReps < targetReps) {
      setCompletedReps(prev => prev + 1);
    }
  };

  const manualDecrement = () => {
    if (completedReps > 0) {
      setCompletedReps(prev => prev - 1);
    }
  };

  const cancelSession = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    stopCamera();
    setIsExercising(false);
    setSelectedExercise(null);
    setCompletedReps(0);
    setTimer(0);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const filteredExercises = categoryFilter === 'all' 
    ? exercises 
    : exercises.filter(ex => ex.category === categoryFilter);

  const getCategoryColor = (category) => {
    const colors = {
      strength: 'bg-red-100 text-red-700 border-red-300',
      cardio: 'bg-orange-100 text-orange-700 border-orange-300',
      yoga: 'bg-purple-100 text-purple-700 border-purple-300',
      flexibility: 'bg-green-100 text-green-700 border-green-300'
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  };

  const getDifficultyColor = (difficulty) => {
    const colors = {
      beginner: 'bg-green-500',
      intermediate: 'bg-yellow-500',
      advanced: 'bg-red-500'
    };
    return colors[difficulty] || 'bg-gray-500';
  };

  if (!user) return null;

  // Exercise session view
  if (isExercising && selectedExercise) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-3xl font-bold text-gray-900">{selectedExercise.name}</h2>
            <Button variant="destructive" onClick={cancelSession}>
              <Square className="w-4 h-4 mr-2" />
              Stop Session
            </Button>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Camera/Video Feed */}
            <div className="lg:col-span-2">
              <Card>
                <CardContent className="p-6">
                  {useAICoach && cameraActive ? (
                    <div className="relative">
                      <video 
                        ref={videoRef} 
                        className="hidden"
                        width="640" 
                        height="480"
                      />
                      <canvas 
                        ref={canvasRef}
                        width="640"
                        height="480"
                        className="w-full rounded-lg border-2 border-teal-400"
                      />
                      <div className="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded-full text-sm flex items-center gap-2">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                        AI Coach Active
                      </div>
                      {formFeedback.length > 0 && (
                        <div className="absolute bottom-4 left-4 right-4 bg-black bg-opacity-75 text-white p-3 rounded-lg">
                          {formFeedback[formFeedback.length - 1]}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-gray-900 rounded-lg flex items-center justify-center" style={{height: '480px'}}>
                      <iframe
                        width="100%"
                        height="100%"
                        src={selectedExercise.video_url}
                        title={selectedExercise.name}
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                        className="rounded-lg"
                      />
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Stats Panel */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Progress</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <div className="text-6xl font-bold text-teal-600">{completedReps}</div>
                    <div className="text-gray-600">of {targetReps} reps</div>
                    <div className="w-full bg-gray-200 rounded-full h-3 mt-3">
                      <div 
                        className="bg-teal-500 h-3 rounded-full transition-all duration-300"
                        style={{width: `${(completedReps / targetReps) * 100}%`}}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Time:</span>
                    <span className="font-semibold">{formatTime(timer)}</span>
                  </div>

                  {!useAICoach && (
                    <div className="flex gap-2">
                      <Button 
                        onClick={manualDecrement}
                        variant="outline"
                        className="flex-1"
                        disabled={completedReps === 0}
                      >
                        -
                      </Button>
                      <Button 
                        onClick={manualIncrement}
                        className="flex-1 bg-teal-600 hover:bg-teal-700"
                        disabled={completedReps >= targetReps}
                      >
                        +
                      </Button>
                    </div>
                  )}

                  <Button 
                    onClick={completeSession}
                    className="w-full bg-green-600 hover:bg-green-700"
                    size="lg"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Complete Session
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Form Tips</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {selectedExercise.form_tips.slice(0, 3).map((tip, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Exercise selection view
  if (selectedExercise && !isExercising) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
        <div className="max-w-4xl mx-auto">
          <Button 
            variant="outline" 
            onClick={() => setSelectedExercise(null)}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Exercises
          </Button>

          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <iframe
                    width="100%"
                    height="300"
                    src={selectedExercise.video_url}
                    title={selectedExercise.name}
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className="rounded-lg"
                  />
                </div>

                <div>
                  <h2 className="text-3xl font-bold mb-2">{selectedExercise.name}</h2>
                  <div className="flex gap-2 mb-4">
                    <Badge className={getCategoryColor(selectedExercise.category)}>
                      {selectedExercise.category}
                    </Badge>
                    <Badge className="capitalize">
                      {selectedExercise.difficulty}
                    </Badge>
                  </div>
                  <p className="text-gray-700 mb-4">{selectedExercise.description}</p>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-teal-600" />
                      <span className="font-semibold">Target:</span>
                      <span>{selectedExercise.target_muscles.join(', ')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Flame className="w-4 h-4 text-orange-600" />
                      <span className="font-semibold">Calories:</span>
                      <span>~{selectedExercise.calories_per_rep} per rep</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Form Tips</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {selectedExercise.form_tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Start Your Session</CardTitle>
              <CardDescription>Configure your workout and let's begin!</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-3">
                  Target Reps: <span className="text-2xl font-bold text-teal-600">{targetReps}</span>
                </label>
                <Slider 
                  value={[targetReps]}
                  onValueChange={(val) => setTargetReps(val[0])}
                  min={5}
                  max={50}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>5</span>
                  <span>50</span>
                </div>
              </div>

              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Camera className="w-5 h-5 text-teal-600" />
                    <div>
                      <div className="font-semibold">AI Coach</div>
                      <div className="text-sm text-gray-600">Real-time form tracking & rep counting</div>
                    </div>
                  </div>
                  <Button
                    variant={useAICoach ? "default" : "outline"}
                    onClick={() => setUseAICoach(!useAICoach)}
                  >
                    {useAICoach ? "Enabled" : "Disabled"}
                  </Button>
                </div>

                {!useAICoach && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-yellow-800">
                      Without AI Coach, you'll manually track your reps using +/- buttons. 
                      A timer will still track your workout duration.
                    </p>
                  </div>
                )}
              </div>

              <Button 
                onClick={startSession}
                className="w-full bg-teal-600 hover:bg-teal-700"
                size="lg"
              >
                <Play className="w-5 h-5 mr-2" />
                Start Workout
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Results Modal */}
        <Dialog open={showResults} onOpenChange={setShowResults}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="text-2xl flex items-center gap-2">
                <Trophy className="w-6 h-6 text-yellow-500" />
                Workout Complete!
              </DialogTitle>
              <DialogDescription>Great job on completing your exercise session!</DialogDescription>
            </DialogHeader>

            {sessionResults && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-teal-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-teal-600">
                      {sessionResults.completed_reps}
                    </div>
                    <div className="text-sm text-gray-600">Reps</div>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {formatTime(sessionResults.duration_seconds)}
                    </div>
                    <div className="text-sm text-gray-600">Duration</div>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-orange-600">
                      {sessionResults.calories_burned}
                    </div>
                    <div className="text-sm text-gray-600">Calories</div>
                  </div>
                  <div className="bg-yellow-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-yellow-600">
                      +{sessionResults.stars_awarded}
                    </div>
                    <div className="text-sm text-gray-600">Stars</div>
                  </div>
                </div>

                {sessionResults.form_accuracy && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-green-900">Form Accuracy</span>
                      <span className="text-2xl font-bold text-green-600">
                        {sessionResults.form_accuracy}%
                      </span>
                    </div>
                  </div>
                )}

                <Button 
                  onClick={() => {
                    setShowResults(false);
                    setSelectedExercise(null);
                  }}
                  className="w-full"
                >
                  Done
                </Button>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  // Main exercise library view
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <Button 
              variant="outline" 
              onClick={() => navigate("/dashboard")}
              className="mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
            <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-3">
              <Dumbbell className="w-10 h-10 text-teal-600" />
              Exercise Trainer
            </h1>
            <p className="text-gray-600 mt-2">AI-powered form tracking and rep counting</p>
          </div>
        </div>

        {/* Progress Summary */}
        {progress && progress.total_sessions > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-teal-600" />
                Your Progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-teal-600">{progress.total_sessions}</div>
                  <div className="text-sm text-gray-600">Sessions</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{progress.total_reps}</div>
                  <div className="text-sm text-gray-600">Total Reps</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{progress.total_calories}</div>
                  <div className="text-sm text-gray-600">Calories</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{progress.total_minutes}</div>
                  <div className="text-sm text-gray-600">Minutes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{progress.exercises_tried}</div>
                  <div className="text-sm text-gray-600">Exercises</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">{progress.current_streak}</div>
                  <div className="text-sm text-gray-600">Day Streak</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Category Filter */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {['all', 'strength', 'cardio', 'yoga'].map(category => (
            <Button
              key={category}
              variant={categoryFilter === category ? "default" : "outline"}
              onClick={() => setCategoryFilter(category)}
              className="capitalize"
            >
              {category}
            </Button>
          ))}
        </div>

        {/* Exercise Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredExercises.map(exercise => (
            <Card 
              key={exercise.id}
              className="cursor-pointer hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
              onClick={() => setSelectedExercise(exercise)}
            >
              <CardContent className="p-0">
                <div className="relative">
                  <img 
                    src={exercise.thumbnail_url} 
                    alt={exercise.name}
                    className="w-full h-48 object-cover rounded-t-lg"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/400x300?text=' + exercise.name;
                    }}
                  />
                  <div className={`absolute top-2 right-2 w-3 h-3 rounded-full ${getDifficultyColor(exercise.difficulty)}`} />
                </div>
                <div className="p-4">
                  <h3 className="text-xl font-bold mb-2">{exercise.name}</h3>
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {exercise.description}
                  </p>
                  <div className="flex items-center justify-between">
                    <Badge className={getCategoryColor(exercise.category)}>
                      {exercise.category}
                    </Badge>
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <Flame className="w-4 h-4 text-orange-500" />
                      <span>{exercise.calories_per_rep}/rep</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ExerciseTrainer;
