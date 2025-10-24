import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import * as tf from "@tensorflow/tfjs";
import * as posenet from "@tensorflow-models/posenet";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Camera, Play, Square, RotateCcw, Trophy, ArrowLeft, Activity } from "lucide-react";
import { Progress } from "@/components/ui/progress";

const AITrainer = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [isExercising, setIsExercising] = useState(false);
  const [isPoseDetecting, setIsPoseDetecting] = useState(false);
  const [repCount, setRepCount] = useState(0);
  const [targetReps, setTargetReps] = useState(10);
  const [formQuality, setFormQuality] = useState(100);
  const [squatPhase, setSquatPhase] = useState("standing"); // standing, squatting
  const [timer, setTimer] = useState(0);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [currentAngle, setCurrentAngle] = useState(180); // For debug display
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const poseNetRef = useRef(null);
  const animationFrameRef = useRef(null);
  const timerIntervalRef = useRef(null);
  
  // Squat detection state
  const previousKneeAngleRef = useRef(180);
  const minKneeAngleRef = useRef(180);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    if (!storedUser) {
      navigate("/login");
      return;
    }
    
    loadPoseNet();
    
    return () => {
      cleanup();
    };
  }, [navigate]);

  useEffect(() => {
    if (isExercising && !timerIntervalRef.current) {
      timerIntervalRef.current = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
    } else if (!isExercising && timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [isExercising]);

  const loadPoseNet = async () => {
    try {
      setIsLoading(true);
      toast.info("Loading AI Trainer model...");
      
      // Load PoseNet model
      const net = await posenet.load({
        architecture: "MobileNetV1",
        outputStride: 16,
        inputResolution: { width: 640, height: 480 },
        multiplier: 0.75,
      });
      
      poseNetRef.current = net;
      setIsLoading(false);
      toast.success("AI Trainer ready!");
    } catch (error) {
      console.error("Error loading PoseNet:", error);
      toast.error("Failed to load AI Trainer. Please refresh the page.");
      setIsLoading(false);
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setIsPoseDetecting(true);
          detectPose();
          toast.success("Camera activated!");
        };
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
      toast.error("Could not access camera. Please check permissions.");
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    setIsPoseDetecting(false);
  };

  const detectPose = async () => {
    if (!videoRef.current || !poseNetRef.current || !canvasRef.current) {
      return;
    }

    try {
      // Estimate pose from video
      const pose = await poseNetRef.current.estimateSinglePose(
        videoRef.current,
        {
          flipHorizontal: false,
          decodingMethod: "single-person",
        }
      );

      // Draw pose on canvas
      drawPose(pose);
      
      // Analyze squat form if exercising
      if (isExercising) {
        analyzeSquat(pose);
      }
    } catch (error) {
      console.error("Pose detection error:", error);
    }

    // Continue detection loop
    animationFrameRef.current = requestAnimationFrame(detectPose);
  };

  const drawPose = (pose) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const video = videoRef.current;
    
    if (!ctx || !video) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw video frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Check pose confidence
    if (pose.score < 0.3) {
      drawOverlayText(ctx, "⚠️ No Body Detected", canvas.width / 2, 50, "red");
      return;
    }

    // Determine line color based on form quality
    const lineColor = formQuality >= 80 ? "#10b981" : "#ef4444"; // green or red
    const pointColor = formQuality >= 80 ? "#34d399" : "#f87171";

    // Draw skeleton
    drawSkeleton(ctx, pose.keypoints, lineColor, pointColor);
    
    // Draw overlay UI
    drawOverlayUI(ctx, canvas.width, canvas.height);
  };

  const drawSkeleton = (ctx, keypoints, lineColor, pointColor) => {
    // Define skeleton connections for arms, torso, and legs
    const connections = [
      // Torso
      ["leftShoulder", "rightShoulder"],
      ["leftShoulder", "leftHip"],
      ["rightShoulder", "rightHip"],
      ["leftHip", "rightHip"],
      
      // Left arm
      ["leftShoulder", "leftElbow"],
      ["leftElbow", "leftWrist"],
      
      // Right arm
      ["rightShoulder", "rightElbow"],
      ["rightElbow", "rightWrist"],
      
      // Left leg
      ["leftHip", "leftKnee"],
      ["leftKnee", "leftAnkle"],
      
      // Right leg
      ["rightHip", "rightKnee"],
      ["rightKnee", "rightAnkle"],
    ];

    // Create keypoint map
    const keypointMap = {};
    keypoints.forEach(kp => {
      keypointMap[kp.part] = kp;
    });

    // Draw connections (lines)
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 4;
    ctx.shadowColor = lineColor;
    ctx.shadowBlur = 10;

    connections.forEach(([start, end]) => {
      const startKp = keypointMap[start];
      const endKp = keypointMap[end];
      
      if (startKp && endKp && startKp.score > 0.3 && endKp.score > 0.3) {
        ctx.beginPath();
        ctx.moveTo(startKp.position.x, startKp.position.y);
        ctx.lineTo(endKp.position.x, endKp.position.y);
        ctx.stroke();
      }
    });

    // Draw keypoints (circles)
    ctx.fillStyle = pointColor;
    ctx.shadowBlur = 15;
    
    keypoints.forEach(kp => {
      if (kp.score > 0.3) {
        ctx.beginPath();
        ctx.arc(kp.position.x, kp.position.y, 6, 0, 2 * Math.PI);
        ctx.fill();
      }
    });
    
    // Reset shadow
    ctx.shadowBlur = 0;
  };

  const drawOverlayUI = (ctx, width, height) => {
    // Timer (top-left)
    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(10, 10, 120, 50);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 24px Arial";
    ctx.fillText(formatTime(timer), 25, 43);

    // Rep counter (top-right)
    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(width - 130, 10, 120, 50);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 24px Arial";
    ctx.fillText(`${repCount}/${targetReps}`, width - 110, 43);

    // Debug: Knee angle display (left side, middle)
    if (isExercising) {
      ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
      ctx.fillRect(10, height / 2 - 40, 140, 80);
      ctx.fillStyle = "#fff";
      ctx.font = "bold 14px Arial";
      ctx.textAlign = "left";
      ctx.fillText("Knee Angle:", 20, height / 2 - 15);
      ctx.font = "bold 28px Arial";
      ctx.fillText(`${currentAngle.toFixed(0)}°`, 20, height / 2 + 20);
      ctx.font = "bold 12px Arial";
      ctx.fillStyle = squatPhase === "squatting" ? "#fbbf24" : "#10b981";
      ctx.fillText(squatPhase.toUpperCase(), 20, height / 2 + 35);
    }

    // Form quality indicator (bottom-center)
    const formText = formQuality >= 80 ? "✓ Good Form" : "✗ Check Form";
    const formBgColor = formQuality >= 80 ? "rgba(16, 185, 129, 0.9)" : "rgba(239, 68, 68, 0.9)";
    
    ctx.fillStyle = formBgColor;
    ctx.fillRect(width / 2 - 100, height - 70, 200, 50);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 20px Arial";
    ctx.textAlign = "center";
    ctx.fillText(formText, width / 2, height - 38);
    ctx.textAlign = "left";

    // Body detected indicator (top-center)
    ctx.fillStyle = "rgba(16, 185, 129, 0.8)";
    ctx.fillRect(width / 2 - 90, 10, 180, 35);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 16px Arial";
    ctx.textAlign = "center";
    ctx.fillText("✓ Body Detected", width / 2, 33);
    ctx.textAlign = "left";
  };

  const drawOverlayText = (ctx, text, x, y, color) => {
    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(x - 150, y - 25, 300, 40);
    ctx.fillStyle = color;
    ctx.font = "bold 20px Arial";
    ctx.textAlign = "center";
    ctx.fillText(text, x, y);
    ctx.textAlign = "left";
  };

  const analyzeSquat = (pose) => {
    const keypoints = pose.keypoints;
    
    // Get required keypoints
    const leftHip = keypoints.find(kp => kp.part === "leftHip");
    const leftKnee = keypoints.find(kp => kp.part === "leftKnee");
    const leftAnkle = keypoints.find(kp => kp.part === "leftAnkle");
    const rightHip = keypoints.find(kp => kp.part === "rightHip");
    const rightKnee = keypoints.find(kp => kp.part === "rightKnee");
    const rightAnkle = keypoints.find(kp => kp.part === "rightAnkle");

    // Check if all required keypoints are detected
    if (!leftHip || !leftKnee || !leftAnkle || !rightHip || !rightKnee || !rightAnkle) {
      return;
    }

    if (leftHip.score < 0.2 || leftKnee.score < 0.2 || leftAnkle.score < 0.2 ||
        rightHip.score < 0.2 || rightKnee.score < 0.2 || rightAnkle.score < 0.2) {
      return;
    }

    // Calculate knee angles for both legs
    const leftKneeAngle = calculateAngle(leftHip.position, leftKnee.position, leftAnkle.position);
    const rightKneeAngle = calculateAngle(rightHip.position, rightKnee.position, rightAnkle.position);
    
    // Average knee angle
    const avgKneeAngle = (leftKneeAngle + rightKneeAngle) / 2;
    
    // Update current angle for display
    setCurrentAngle(avgKneeAngle);

    // Debug logging (optional - comment out in production)
    console.log(`Knee Angle: ${avgKneeAngle.toFixed(1)}°, Phase: ${squatPhase}, Min: ${minKneeAngleRef.current.toFixed(1)}°`);

    // Track minimum knee angle during squat
    if (avgKneeAngle < minKneeAngleRef.current) {
      minKneeAngleRef.current = avgKneeAngle;
    }

    // More forgiving thresholds for better detection
    const STANDING_ANGLE = 150; // Standing position (more forgiving)
    const SQUAT_ANGLE = 120; // Squat position threshold (more forgiving)
    const MIN_SQUAT_DEPTH = 130; // Minimum depth to count as a squat

    // Determine form quality based on squat depth
    if (squatPhase === "squatting") {
      // Good squat: knee angle between 60-110 degrees
      if (minKneeAngleRef.current >= 60 && minKneeAngleRef.current <= 110) {
        setFormQuality(100);
      } else if (minKneeAngleRef.current > 110 && minKneeAngleRef.current <= 130) {
        setFormQuality(85); // Acceptable
      } else {
        setFormQuality(70); // Shallow but still counting
      }
    }

    // Detect squat phases with more forgiving thresholds
    if (squatPhase === "standing" && avgKneeAngle < SQUAT_ANGLE) {
      // Entered squat position
      console.log("🔽 Squatting phase started");
      setSquatPhase("squatting");
      minKneeAngleRef.current = avgKneeAngle;
    } else if (squatPhase === "squatting" && avgKneeAngle > STANDING_ANGLE) {
      // Returned to standing position - count the rep
      console.log(`🔼 Standing phase - Min angle was: ${minKneeAngleRef.current.toFixed(1)}°`);
      
      // Check if squat was deep enough (more forgiving threshold)
      if (minKneeAngleRef.current <= MIN_SQUAT_DEPTH) {
        setRepCount(prev => {
          const newCount = prev + 1;
          console.log(`✅ Rep ${newCount} counted!`);
          
          // Check if target reached
          if (newCount >= targetReps) {
            completeSession();
          } else {
            toast.success(`Rep ${newCount} completed! 🎯`);
          }
          
          return newCount;
        });
      } else {
        console.log(`❌ Squat too shallow: ${minKneeAngleRef.current.toFixed(1)}° > ${MIN_SQUAT_DEPTH}°`);
        toast.warning("Squat too shallow. Go deeper!");
        setFormQuality(60);
      }
      
      setSquatPhase("standing");
      minKneeAngleRef.current = 180;
    }

    previousKneeAngleRef.current = avgKneeAngle;
  };

  const calculateAngle = (a, b, c) => {
    // Calculate angle at point b formed by points a, b, c
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180 / Math.PI);
    
    if (angle > 180) {
      angle = 360 - angle;
    }
    
    return angle;
  };

  const startSession = async () => {
    if (!isPoseDetecting) {
      await startCamera();
    }
    
    setIsExercising(true);
    setRepCount(0);
    setTimer(0);
    setFormQuality(100);
    setSquatPhase("standing");
    setSessionComplete(false);
    minKneeAngleRef.current = 180;
    previousKneeAngleRef.current = 180;
    
    toast.success("Session started! Begin your squats!");
  };

  const completeSession = () => {
    setIsExercising(false);
    setSessionComplete(true);
    
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    
    toast.success(`🎉 Session complete! ${repCount + 1} squats in ${formatTime(timer)}!`, {
      duration: 5000,
    });
  };

  const resetSession = () => {
    setRepCount(0);
    setTimer(0);
    setFormQuality(100);
    setSquatPhase("standing");
    setIsExercising(false);
    setSessionComplete(false);
    minKneeAngleRef.current = 180;
    previousKneeAngleRef.current = 180;
    
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
  };

  const cleanup = () => {
    stopCamera();
    
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate("/dashboard")}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
          
          <div className="flex items-center gap-3">
            <Activity className="w-10 h-10 text-orange-600" />
            <h1 className="text-3xl font-bold text-gray-900">AI Trainer</h1>
          </div>
          
          <div className="w-32" /> {/* Spacer for alignment */}
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Camera Feed - Large Column */}
          <div className="lg:col-span-2">
            <Card className="border-2 border-orange-200">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Camera className="w-6 h-6 text-orange-600" />
                    <CardTitle>Live Camera Feed</CardTitle>
                  </div>
                  {isPoseDetecting && (
                    <Badge className="bg-green-500 text-white animate-pulse">
                      <div className="w-2 h-2 bg-white rounded-full mr-2" />
                      Active
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: "4/3" }}>
                  {/* Video Element (hidden) */}
                  <video
                    ref={videoRef}
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ display: "none" }}
                    playsInline
                  />
                  
                  {/* Canvas for pose visualization */}
                  <canvas
                    ref={canvasRef}
                    className="absolute inset-0 w-full h-full object-contain"
                  />
                  
                  {/* Waiting State */}
                  {!isPoseDetecting && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-white">
                      <Camera className="w-20 h-20 mb-4 opacity-50" />
                      <p className="text-lg mb-2">Camera Ready</p>
                      <p className="text-sm opacity-75">Click "Start Session" to begin</p>
                    </div>
                  )}
                </div>

                {/* Session Complete Overlay */}
                {sessionComplete && (
                  <div className="mt-4 p-6 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg text-white text-center">
                    <Trophy className="w-12 h-12 mx-auto mb-3" />
                    <h3 className="text-2xl font-bold mb-2">Session Complete! 🎉</h3>
                    <p className="text-lg mb-1">{repCount} Squats</p>
                    <p className="text-sm opacity-90">Time: {formatTime(timer)}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Controls & Stats */}
          <div className="space-y-6">
            {/* Stats Card */}
            <Card className="border-2 border-orange-200">
              <CardHeader>
                <CardTitle className="text-lg">Session Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-600">Progress</span>
                    <span className="text-sm font-semibold">{repCount}/{targetReps} reps</span>
                  </div>
                  <Progress value={(repCount / targetReps) * 100} className="h-3" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-orange-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Timer</p>
                    <p className="text-2xl font-bold text-orange-600">{formatTime(timer)}</p>
                  </div>
                  
                  <div className="bg-pink-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Reps</p>
                    <p className="text-2xl font-bold text-pink-600">{repCount}</p>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Form Quality</p>
                  <div className="flex items-center gap-2">
                    <Progress value={formQuality} className="flex-1 h-2" />
                    <span className="text-sm font-semibold text-emerald-600">{formQuality}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Controls Card */}
            <Card className="border-2 border-orange-200">
              <CardHeader>
                <CardTitle className="text-lg">Controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-sm text-gray-600 mb-2 block">Target Reps</label>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setTargetReps(Math.max(5, targetReps - 5))}
                      disabled={isExercising}
                    >
                      -5
                    </Button>
                    <span className="text-2xl font-bold text-orange-600 min-w-[50px] text-center">
                      {targetReps}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setTargetReps(Math.min(50, targetReps + 5))}
                      disabled={isExercising}
                    >
                      +5
                    </Button>
                  </div>
                </div>

                <div className="space-y-2 pt-3 border-t">
                  {!isExercising ? (
                    <Button
                      onClick={startSession}
                      disabled={isLoading}
                      className="w-full bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 text-white"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Start Session
                    </Button>
                  ) : (
                    <Button
                      onClick={completeSession}
                      className="w-full bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white"
                    >
                      <Square className="w-4 h-4 mr-2" />
                      Stop Session
                    </Button>
                  )}

                  <Button
                    onClick={resetSession}
                    variant="outline"
                    className="w-full"
                    disabled={!sessionComplete && repCount === 0}
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Instructions Card */}
            <Card className="border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-pink-50">
              <CardHeader>
                <CardTitle className="text-lg">How to Squat</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-orange-500 font-bold">1.</span>
                    <span>Stand with feet shoulder-width apart</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-500 font-bold">2.</span>
                    <span>Keep your back straight and chest up</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-500 font-bold">3.</span>
                    <span>Lower down until thighs are parallel to ground</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-500 font-bold">4.</span>
                    <span>Push through heels to return to standing</span>
                  </li>
                  <li className="flex items-start gap-2 mt-3 pt-3 border-t border-orange-200">
                    <span className="text-green-500">✓</span>
                    <span className="font-semibold">Green lines = Good form</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500">✗</span>
                    <span className="font-semibold">Red lines = Check your form</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AITrainer;
