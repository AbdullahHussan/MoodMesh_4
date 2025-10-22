import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Trophy, Lock, Flame, Heart, Users, Sparkles, Star, Target } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Achievements = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [achievements, setAchievements] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    fetchAchievements(userData.user_id);
  }, [navigate]);

  const fetchAchievements = async (userId) => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/achievements/${userId}`);
      setAchievements(response.data);
    } catch (error) {
      console.error("Failed to fetch achievements", error);
      toast.error("Failed to load achievements");
    } finally {
      setIsLoading(false);
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case "bronze": return "from-amber-600 to-amber-800";
      case "silver": return "from-gray-400 to-gray-600";
      case "gold": return "from-yellow-400 to-yellow-600";
      case "platinum": return "from-purple-400 to-purple-600";
      default: return "from-gray-400 to-gray-600";
    }
  };

  const getTierBadgeColor = (tier) => {
    switch (tier) {
      case "bronze": return "bg-amber-100 text-amber-800 border-amber-300";
      case "silver": return "bg-gray-100 text-gray-800 border-gray-300";
      case "gold": return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "platinum": return "bg-purple-100 text-purple-800 border-purple-300";
      default: return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "mood_logging": return <Heart className="w-4 h-4" />;
      case "streaks": return <Flame className="w-4 h-4" />;
      case "therapy": return <Sparkles className="w-4 h-4" />;
      case "community": return <Users className="w-4 h-4" />;
      case "special": return <Star className="w-4 h-4" />;
      default: return <Trophy className="w-4 h-4" />;
    }
  };

  const getCategoryName = (category) => {
    switch (category) {
      case "mood_logging": return "Mood Logging";
      case "streaks": return "Consistency";
      case "therapy": return "Self-Care";
      case "community": return "Community";
      case "special": return "Special";
      default: return "Other";
    }
  };

  const filterAchievements = (achievementsList) => {
    if (filter === "all") return achievementsList;
    return achievementsList.filter(a => a.category === filter);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading achievements...</p>
        </div>
      </div>
    );
  }

  if (!user || !achievements) return null;

  const allAchievements = [...achievements.earned, ...achievements.locked];
  const filteredEarned = filterAchievements(achievements.earned);
  const filteredLocked = filterAchievements(achievements.locked);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <Button variant="outline" onClick={() => navigate("/dashboard")} data-testid="back-to-dashboard">
            ← Back to Dashboard
          </Button>
          <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 text-base">
            <Trophy className="w-4 h-4 mr-2" />
            {achievements.earned_count} / {achievements.total_achievements} Unlocked
          </Badge>
        </div>

        {/* Page Title */}
        <div className="mb-8 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-3" style={{ fontFamily: 'EB Garamond, serif' }}>
            🏆 Your Achievements
          </h1>
          <p className="text-gray-600 text-lg mb-4">
            Celebrate your progress on your mental wellness journey
          </p>
          <div className="max-w-md mx-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Overall Progress</span>
              <span className="text-sm font-bold text-purple-600">{achievements.completion_percentage}%</span>
            </div>
            <Progress value={achievements.completion_percentage} className="h-3" />
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="border-2 border-teal-200 bg-gradient-to-br from-teal-50 to-teal-100">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-teal-700">Mood Logs</p>
                  <p className="text-2xl font-bold text-teal-900">{achievements.stats.total_mood_logs}</p>
                </div>
                <Heart className="w-8 h-8 text-teal-600 opacity-50" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-orange-100">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-orange-700">Best Streak</p>
                  <p className="text-2xl font-bold text-orange-900">{achievements.stats.longest_streak} days</p>
                </div>
                <Flame className="w-8 h-8 text-orange-600 opacity-50" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-purple-100">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-700">Therapy Chats</p>
                  <p className="text-2xl font-bold text-purple-900">{achievements.stats.total_therapist_sessions}</p>
                </div>
                <Sparkles className="w-8 h-8 text-purple-600 opacity-50" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-blue-100">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-700">Communities</p>
                  <p className="text-2xl font-bold text-blue-900">{achievements.stats.total_communities_joined}</p>
                </div>
                <Users className="w-8 h-8 text-blue-600 opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Tabs defaultValue="all" className="mb-6" onValueChange={setFilter}>
          <TabsList className="grid grid-cols-6 w-full max-w-3xl mx-auto">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="mood_logging">Mood</TabsTrigger>
            <TabsTrigger value="streaks">Streaks</TabsTrigger>
            <TabsTrigger value="therapy">Therapy</TabsTrigger>
            <TabsTrigger value="community">Community</TabsTrigger>
            <TabsTrigger value="special">Special</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Earned Achievements */}
        {filteredEarned.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Trophy className="w-6 h-6 text-yellow-500" />
              Earned Achievements ({filteredEarned.length})
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredEarned.map((achievement) => (
                <Card 
                  key={achievement.id}
                  className="border-2 hover:shadow-xl transition-all duration-300 relative overflow-hidden"
                  data-testid={`achievement-earned-${achievement.id}`}
                >
                  <div className={`absolute top-0 left-0 right-0 h-2 bg-gradient-to-r ${getTierColor(achievement.tier)}`} />
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-5xl">{achievement.icon}</div>
                        <div>
                          <CardTitle className="text-lg flex items-center gap-2">
                            {achievement.name}
                            {getCategoryIcon(achievement.category)}
                          </CardTitle>
                          <Badge className={`mt-1 border ${getTierBadgeColor(achievement.tier)}`}>
                            {achievement.tier}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2">{achievement.description}</p>
                    <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
                      <Target className="w-4 h-4" />
                      Completed!
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Locked Achievements */}
        {filteredLocked.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Lock className="w-6 h-6 text-gray-400" />
              Locked Achievements ({filteredLocked.length})
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredLocked.map((achievement) => (
                <Card 
                  key={achievement.id}
                  className="border-2 border-gray-200 bg-gray-50 opacity-75 hover:opacity-100 transition-all duration-300 relative overflow-hidden"
                  data-testid={`achievement-locked-${achievement.id}`}
                >
                  <div className="absolute top-0 left-0 right-0 h-2 bg-gray-300" />
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-5xl grayscale">{achievement.icon}</div>
                        <div>
                          <CardTitle className="text-lg flex items-center gap-2 text-gray-600">
                            {achievement.name}
                            <Lock className="w-4 h-4" />
                          </CardTitle>
                          <Badge className={`mt-1 border ${getTierBadgeColor(achievement.tier)}`}>
                            {achievement.tier}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-500 mb-3">{achievement.description}</p>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-gray-600">
                        <span>Progress</span>
                        <span className="font-medium">{achievement.progress} / {achievement.target}</span>
                      </div>
                      <Progress 
                        value={(achievement.progress / achievement.target) * 100} 
                        className="h-2"
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {filteredEarned.length === 0 && filteredLocked.length === 0 && (
          <Card className="border-2 border-gray-200">
            <CardContent className="py-12 text-center">
              <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No achievements in this category yet</h3>
              <p className="text-gray-500">Try a different filter or start earning achievements!</p>
            </CardContent>
          </Card>
        )}

        {/* Motivational Message */}
        {achievements.completion_percentage < 100 && (
          <Card className="mt-8 border-2 border-purple-200 bg-gradient-to-r from-purple-50 to-pink-50">
            <CardContent className="py-8">
              <div className="text-center">
                <Trophy className="w-12 h-12 text-purple-600 mx-auto mb-3" />
                <h3 className="text-xl font-bold text-gray-900 mb-2">Keep Going! 💪</h3>
                <p className="text-gray-600">
                  You've unlocked {achievements.earned_count} out of {achievements.total_achievements} achievements. 
                  {achievements.completion_percentage < 25 && " Your journey has just begun!"}
                  {achievements.completion_percentage >= 25 && achievements.completion_percentage < 50 && " You're making great progress!"}
                  {achievements.completion_percentage >= 50 && achievements.completion_percentage < 75 && " You're more than halfway there!"}
                  {achievements.completion_percentage >= 75 && " You're almost there!"}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Completion Celebration */}
        {achievements.completion_percentage === 100 && (
          <Card className="mt-8 border-2 border-yellow-300 bg-gradient-to-r from-yellow-50 to-orange-50">
            <CardContent className="py-8">
              <div className="text-center">
                <div className="text-6xl mb-4">🎉🏆🎉</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Achievement Master!</h3>
                <p className="text-gray-700 text-lg">
                  Congratulations! You've unlocked all achievements! Your dedication to mental wellness is truly inspiring.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      <Toaster />
    </div>
  );
};

export default Achievements;
