import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Brain, Sparkles, UserPlus } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Register = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (!username.trim()) {
      toast.error("Please enter a username");
      return;
    }
    if (username.trim().length < 3) {
      toast.error("Username must be at least 3 characters long");
      return;
    }
    if (!password) {
      toast.error("Please enter a password");
      return;
    }
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters long");
      return;
    }
    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/auth/register`, {
        username: username.trim(),
        password: password
      });

      // Store token and user data
      localStorage.setItem("moodmesh_token", response.data.access_token);
      localStorage.setItem("moodmesh_user", JSON.stringify({
        user_id: response.data.user_id,
        username: response.data.username
      }));

      toast.success("Account created successfully! Welcome to MoodMesh!");
      navigate("/dashboard");
    } catch (error) {
      const errorMsg = error.response?.data?.detail || "Registration failed. Please try again.";
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
            Join MoodMesh
          </h1>
          <p className="text-gray-600">Create an account to start your wellness journey</p>
        </div>

        <Card className="border-2 border-teal-200 shadow-xl" data-testid="register-card">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-2">
              <UserPlus className="w-6 h-6 text-teal-600" />
              Register
            </CardTitle>
            <CardDescription>Create a new account to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Choose a username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="text-base"
                  data-testid="register-username-input"
                  autoComplete="username"
                />
                <p className="text-xs text-gray-500">At least 3 characters</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Create a password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="text-base"
                  data-testid="register-password-input"
                  autoComplete="new-password"
                />
                <p className="text-xs text-gray-500">At least 6 characters</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="text-base"
                  data-testid="register-confirm-password-input"
                  autoComplete="new-password"
                />
              </div>
              <Button 
                type="submit"
                className="w-full bg-teal-600 hover:bg-teal-700 text-white py-6 text-lg"
                disabled={isLoading}
                data-testid="register-submit-button"
              >
                {isLoading ? "Creating Account..." : "Create Account"}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-600">
                Already have an account?{" "}
                <Link to="/login" className="text-teal-600 hover:text-teal-700 font-semibold" data-testid="login-link">
                  Login here
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

export default Register;
