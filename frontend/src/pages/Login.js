import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Brain, Sparkles, LogIn } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!username.trim()) {
      toast.error("Please enter your username");
      return;
    }
    if (!password) {
      toast.error("Please enter your password");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, {
        username: username.trim(),
        password: password
      });

      // Store token and user data
      localStorage.setItem("moodmesh_token", response.data.access_token);
      localStorage.setItem("moodmesh_user", JSON.stringify({
        user_id: response.data.user_id,
        username: response.data.username
      }));

      toast.success("Welcome back!");
      navigate("/dashboard");
    } catch (error) {
      const errorMsg = error.response?.data?.detail || "Login failed. Please check your credentials.";
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="relative">
              <Brain className="w-16 h-16 text-teal-600" strokeWidth={1.5} />
              <Sparkles className="w-6 h-6 text-yellow-500 absolute -top-1 -right-1 animate-pulse" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'EB Garamond, serif' }}>
            Welcome Back
          </h1>
          <p className="text-gray-600">Sign in to continue your wellness journey</p>
        </div>

        <Card className="border-2 border-teal-200 shadow-xl" data-testid="login-card">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-2">
              <LogIn className="w-6 h-6 text-teal-600" />
              Login
            </CardTitle>
            <CardDescription>Enter your credentials to access your account</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="text-base"
                  data-testid="login-username-input"
                  autoComplete="username"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="text-base"
                  data-testid="login-password-input"
                  autoComplete="current-password"
                />
              </div>
              <Button 
                type="submit"
                className="w-full bg-teal-600 hover:bg-teal-700 text-white py-6 text-lg"
                disabled={isLoading}
                data-testid="login-submit-button"
              >
                {isLoading ? "Logging in..." : "Login"}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-600">
                Don't have an account?{" "}
                <Link to="/register" className="text-teal-600 hover:text-teal-700 font-semibold" data-testid="register-link">
                  Register here
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
      <Toaster />
    </div>
  );
};

export default Login;
