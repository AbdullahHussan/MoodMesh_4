import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { TrendingUp, Clock, Lightbulb, Flame, Award, Calendar } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Analytics = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    fetchAnalytics(userData.user_id);
  }, [navigate]);

  const fetchAnalytics = async (userId) => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/mood/analytics/${userId}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error("Failed to fetch analytics", error);
      toast.error("Failed to load analytics data");
    } finally {
      setIsLoading(false);
    }
  };

  // Prepare hourly data for chart
  const prepareHourlyData = () => {
    if (!analytics?.hourly_distribution) return [];
    
    const hourlyData = [];
    for (let hour = 0; hour < 24; hour++) {
      const count = analytics.hourly_distribution[hour] || 0;
      const hour12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
      const period = hour < 12 ? 'AM' : 'PM';
      hourlyData.push({
        hour: `${hour12}${period}`,
        count: count,
        fullHour: hour
      });
    }
    return hourlyData;
  };

  // Color palette
  const COLORS = ['#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#22c55e', '#84cc16', '#eab308', '#f59e0b', '#f97316', '#ef4444'];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your insights...</p>
        </div>
      </div>
    );
  }

  if (!user || !analytics) return null;

  const hourlyData = prepareHourlyData();
  const maxHourlyCount = Math.max(...hourlyData.map(d => d.count), 1);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <Button variant="outline" onClick={() => navigate("/dashboard")} data-testid="back-to-dashboard">
              ← Back to Dashboard
            </Button>
          </div>
          <Badge className="bg-gradient-to-r from-teal-500 to-emerald-500 text-white px-4 py-2 text-base">
            <TrendingUp className="w-4 h-4 mr-2" />
            Analytics Dashboard
          </Badge>
        </div>

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'EB Garamond, serif' }}>
            Your Mood Insights
          </h1>
          <p className="text-gray-600 text-lg">Understanding your emotional patterns and progress</p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <Card className="border-2 border-teal-200 bg-gradient-to-br from-teal-50 to-teal-100" data-testid="total-logs-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-teal-700">Total Mood Logs</p>
                  <p className="text-3xl font-bold text-teal-900">{analytics.total_logs}</p>
                </div>
                <Calendar className="w-10 h-10 text-teal-600 opacity-50" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-orange-100" data-testid="current-streak-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-orange-700">Current Streak</p>
                  <p className="text-3xl font-bold text-orange-900">{analytics.current_streak} days</p>
                </div>
                <Flame className="w-10 h-10 text-orange-600 opacity-50" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-purple-100" data-testid="longest-streak-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-700">Longest Streak</p>
                  <p className="text-3xl font-bold text-purple-900">{analytics.longest_streak} days</p>
                </div>
                <Award className="w-10 h-10 text-purple-600 opacity-50" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-blue-100" data-testid="insights-count-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-700">AI Insights</p>
                  <p className="text-3xl font-bold text-blue-900">{analytics.insights.length}</p>
                </div>
                <Lightbulb className="w-10 h-10 text-blue-600 opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Mood Trend Over Time */}
          <Card className="border-2" data-testid="mood-trend-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-teal-600" />
                Mood Logging Trend (Last 30 Days)
              </CardTitle>
              <CardDescription>Your daily mood logging activity</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics.mood_trend && analytics.mood_trend.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={analytics.mood_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="count" 
                      stroke="#14b8a6" 
                      strokeWidth={2}
                      dot={{ fill: '#14b8a6', r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <p>No data available yet. Start logging your moods!</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Time of Day Pattern */}
          <Card className="border-2" data-testid="hourly-pattern-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" />
                Time of Day Patterns
              </CardTitle>
              <CardDescription>When you're most likely to log your mood</CardDescription>
            </CardHeader>
            <CardContent>
              {hourlyData.some(d => d.count > 0) ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={hourlyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="hour" 
                      tick={{ fontSize: 10 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                      {hourlyData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.count > maxHourlyCount * 0.5 ? '#3b82f6' : '#93c5fd'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <p>No time pattern data yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Common Emotions & Insights */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Common Emotions */}
          <Card className="border-2" data-testid="common-emotions-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
                Most Common Words
              </CardTitle>
              <CardDescription>Frequently mentioned in your mood logs</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics.common_emotions && analytics.common_emotions.length > 0 ? (
                <div className="space-y-3">
                  {analytics.common_emotions.map((emotion, index) => (
                    <div key={index} className="flex items-center gap-3" data-testid={`emotion-${index}`}>
                      <Badge 
                        className="px-3 py-1 text-base font-semibold" 
                        style={{ 
                          backgroundColor: COLORS[index % COLORS.length],
                          color: 'white'
                        }}
                      >
                        #{index + 1}
                      </Badge>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-gray-800 capitalize">{emotion.word}</span>
                          <span className="text-sm text-gray-600">{emotion.count}x</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="h-2 rounded-full transition-all duration-500"
                            style={{ 
                              width: `${(emotion.count / analytics.common_emotions[0].count) * 100}%`,
                              backgroundColor: COLORS[index % COLORS.length]
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <p>Not enough data to show common themes yet</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Insights */}
          <Card className="border-2 border-yellow-200 bg-gradient-to-br from-yellow-50 to-amber-50" data-testid="insights-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-600" />
                AI-Generated Insights
              </CardTitle>
              <CardDescription>Personalized observations about your patterns</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics.insights && analytics.insights.length > 0 ? (
                <div className="space-y-3">
                  {analytics.insights.map((insight, index) => (
                    <div 
                      key={index} 
                      className="p-4 bg-white rounded-lg border-2 border-yellow-200 shadow-sm"
                      data-testid={`insight-${index}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-1">
                          <Lightbulb className="w-5 h-5 text-yellow-600 fill-yellow-200" />
                        </div>
                        <p className="text-gray-800 leading-relaxed">{insight}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-600">
                  <div className="text-center">
                    <Lightbulb className="w-12 h-12 text-yellow-400 mx-auto mb-3" />
                    <p>Keep logging your moods to unlock insights!</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Motivational Message */}
        {analytics.total_logs === 0 && (
          <Card className="mt-6 border-2 border-teal-200 bg-gradient-to-r from-teal-50 to-emerald-50">
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <TrendingUp className="w-16 h-16 text-teal-600 mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Start Your Journey!</h3>
                <p className="text-gray-600 mb-4">
                  Begin logging your moods to unlock powerful insights about your emotional patterns.
                </p>
                <Button 
                  onClick={() => navigate("/mood-log")}
                  className="bg-teal-600 hover:bg-teal-700 text-white"
                >
                  Log Your First Mood
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      <Toaster />
    </div>
  );
};

export default Analytics;
