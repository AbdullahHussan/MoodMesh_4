import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Brain, 
  Heart, 
  Users, 
  Sparkles, 
  MessageCircle, 
  Shield, 
  Clock, 
  TrendingUp,
  CheckCircle2,
  Star,
  ArrowRight,
  Bot,
  Moon,
  Sun,
  Smile
} from "lucide-react";

const HomePage = () => {
  const navigate = useNavigate();
  const [hoveredFeature, setHoveredFeature] = useState(null);

  const features = [
    {
      icon: Heart,
      title: "Mood Tracking",
      description: "Log your daily emotions and receive personalized AI-powered coping strategies to help you navigate life's challenges.",
      color: "from-pink-500 to-rose-500",
      bgColor: "bg-pink-50",
      iconColor: "text-pink-600"
    },
    {
      icon: Bot,
      title: "AI Therapist",
      description: "Chat with our professional AI therapist trained specifically for mental health support, available 24/7 whenever you need guidance.",
      color: "from-purple-500 to-indigo-500",
      bgColor: "bg-purple-50",
      iconColor: "text-purple-600"
    },
    {
      icon: Users,
      title: "Support Communities",
      description: "Join or create safe, supportive communities. Connect with others who understand your journey and share experiences.",
      color: "from-blue-500 to-cyan-500",
      bgColor: "bg-blue-50",
      iconColor: "text-blue-600"
    },
    {
      icon: Shield,
      title: "Privacy First",
      description: "Your mental health journey is personal. We ensure complete confidentiality with encrypted data and secure authentication.",
      color: "from-emerald-500 to-teal-500",
      bgColor: "bg-emerald-50",
      iconColor: "text-emerald-600"
    }
  ];

  const benefits = [
    {
      icon: Clock,
      title: "Available 24/7",
      description: "Access support whenever you need it, day or night"
    },
    {
      icon: Sparkles,
      title: "AI-Powered Insights",
      description: "Get personalized strategies powered by advanced AI"
    },
    {
      icon: TrendingUp,
      title: "Track Your Progress",
      description: "Monitor your wellness journey and celebrate growth"
    },
    {
      icon: MessageCircle,
      title: "Real-Time Support",
      description: "Instant community chat for immediate connection"
    }
  ];

  const steps = [
    {
      number: "01",
      title: "Create Your Account",
      description: "Sign up in seconds and start your wellness journey",
      icon: Smile
    },
    {
      number: "02",
      title: "Log Your Mood",
      description: "Share how you're feeling and get AI-powered coping strategies",
      icon: Heart
    },
    {
      number: "03",
      title: "Connect & Grow",
      description: "Join communities, chat with AI therapist, and track your progress",
      icon: Users
    }
  ];

  const stats = [
    { value: "10,000+", label: "Active Users" },
    { value: "50,000+", label: "Mood Logs" },
    { value: "100+", label: "Communities" },
    { value: "24/7", label: "AI Support" }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 z-50" data-testid="homepage-nav">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-teal-500 to-emerald-500 rounded-xl">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 bg-clip-text text-transparent" style={{ fontFamily: 'EB Garamond, serif' }}>
                MoodMesh
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Button 
                variant="ghost" 
                onClick={() => navigate("/login")}
                className="text-gray-700 hover:text-teal-600"
                data-testid="nav-login-button"
              >
                Sign In
              </Button>
              <Button 
                onClick={() => navigate("/register")}
                className="bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white shadow-lg"
                data-testid="nav-register-button"
              >
                Get Started Free
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 bg-gradient-to-br from-teal-50 via-blue-50 to-purple-50 relative overflow-hidden" data-testid="hero-section">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-teal-200 rounded-full opacity-20 blur-3xl"></div>
          <div className="absolute -bottom-1/2 -left-1/4 w-96 h-96 bg-purple-200 rounded-full opacity-20 blur-3xl"></div>
        </div>

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <Badge className="bg-teal-100 text-teal-700 border-0 px-4 py-2 text-sm font-medium" data-testid="hero-badge">
                <Sparkles className="w-4 h-4 mr-2 inline" />
                AI-Powered Mental Health Support
              </Badge>
              
              <h1 className="text-5xl lg:text-6xl font-bold leading-tight text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }} data-testid="hero-title">
                Your Mental Health{" "}
                <span className="bg-gradient-to-r from-teal-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Matters
                </span>
              </h1>
              
              <p className="text-xl text-gray-600 leading-relaxed" data-testid="hero-description">
                Welcome to MoodMesh – your compassionate companion for mental wellness. 
                Get AI-powered support, connect with caring communities, and track your journey 
                to better mental health. You're not alone.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  size="lg"
                  onClick={() => navigate("/register")}
                  className="bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white px-8 py-6 text-lg shadow-xl hover:shadow-2xl transition-all"
                  data-testid="hero-cta-button"
                >
                  Start Your Journey
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <Button 
                  size="lg"
                  variant="outline"
                  onClick={() => navigate("/login")}
                  className="border-2 border-teal-600 text-teal-600 hover:bg-teal-50 px-8 py-6 text-lg"
                  data-testid="hero-signin-button"
                >
                  Sign In
                </Button>
              </div>

              <div className="flex items-center gap-6 pt-4">
                {stats.slice(0, 3).map((stat, idx) => (
                  <div key={idx} className="text-center">
                    <div className="text-2xl font-bold text-teal-600" data-testid={`stat-value-${idx}`}>{stat.value}</div>
                    <div className="text-sm text-gray-600" data-testid={`stat-label-${idx}`}>{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative" data-testid="hero-image">
              <div className="relative rounded-3xl overflow-hidden shadow-2xl">
                <img 
                  src="https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&q=80" 
                  alt="Mental wellness meditation" 
                  className="w-full h-[500px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-teal-900/30 to-transparent"></div>
              </div>
              
              {/* Floating card */}
              <Card className="absolute -bottom-6 -left-6 bg-white/95 backdrop-blur-sm border-0 shadow-xl max-w-xs" data-testid="hero-floating-card">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-gradient-to-br from-teal-500 to-emerald-500 rounded-xl">
                      <Heart className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">AI Therapist Available</p>
                      <p className="text-sm text-gray-600">Get instant support 24/7</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white" data-testid="features-section">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="bg-purple-100 text-purple-700 border-0 px-4 py-2 mb-4" data-testid="features-badge">
              Features That Care
            </Badge>
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'EB Garamond, serif' }} data-testid="features-title">
              Everything You Need for Your{" "}
              <span className="text-teal-600">Mental Wellness</span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto" data-testid="features-subtitle">
              Comprehensive tools and support designed with your well-being in mind
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <Card 
                  key={idx}
                  className={`border-2 hover:border-teal-300 transition-all duration-300 cursor-pointer transform hover:-translate-y-2 hover:shadow-2xl ${
                    hoveredFeature === idx ? 'shadow-2xl border-teal-300' : 'shadow-md'
                  }`}
                  onMouseEnter={() => setHoveredFeature(idx)}
                  onMouseLeave={() => setHoveredFeature(null)}
                  data-testid={`feature-card-${idx}`}
                >
                  <CardHeader>
                    <div className={`w-16 h-16 rounded-2xl ${feature.bgColor} flex items-center justify-center mb-4`}>
                      <Icon className={`w-8 h-8 ${feature.iconColor}`} />
                    </div>
                    <CardTitle className="text-2xl mb-2">{feature.title}</CardTitle>
                    <CardDescription className="text-base text-gray-600 leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-gray-50 to-teal-50" data-testid="how-it-works-section">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="bg-blue-100 text-blue-700 border-0 px-4 py-2 mb-4" data-testid="how-it-works-badge">
              Simple & Effective
            </Badge>
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'EB Garamond, serif' }} data-testid="how-it-works-title">
              Your Journey to Wellness{" "}
              <span className="text-teal-600">Starts Here</span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto" data-testid="how-it-works-subtitle">
              Getting started is easy. Three simple steps to better mental health.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={idx} className="relative" data-testid={`step-${idx}`}>
                  <Card className="border-2 border-gray-200 hover:border-teal-300 transition-all h-full bg-white hover:shadow-xl">
                    <CardHeader className="text-center pb-6">
                      <div className="text-7xl font-bold text-teal-100 mb-4" style={{ fontFamily: 'EB Garamond, serif' }}>
                        {step.number}
                      </div>
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-teal-500 to-emerald-500 flex items-center justify-center mx-auto mb-4">
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      <CardTitle className="text-xl mb-3">{step.title}</CardTitle>
                      <CardDescription className="text-base">
                        {step.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                  {idx < steps.length - 1 && (
                    <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2 z-10">
                      <ArrowRight className="w-8 h-8 text-teal-300" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-6 bg-white" data-testid="benefits-section">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="relative" data-testid="benefits-image">
              <img 
                src="https://images.unsplash.com/photo-1579208575657-c595a05383b7?w=800&q=80" 
                alt="Support and care" 
                className="rounded-3xl shadow-2xl w-full h-[500px] object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-teal-900/20 to-transparent rounded-3xl"></div>
            </div>

            <div className="space-y-8">
              <div>
                <Badge className="bg-emerald-100 text-emerald-700 border-0 px-4 py-2 mb-4" data-testid="benefits-badge">
                  Why Choose MoodMesh
                </Badge>
                <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'EB Garamond, serif' }} data-testid="benefits-title">
                  We Care About{" "}
                  <span className="text-teal-600">Your Well-Being</span>
                </h2>
                <p className="text-lg text-gray-600 leading-relaxed" data-testid="benefits-description">
                  MoodMesh is more than just an app – it's a compassionate companion designed 
                  to support you through life's challenges with empathy, understanding, and cutting-edge technology.
                </p>
              </div>

              <div className="space-y-6">
                {benefits.map((benefit, idx) => {
                  const Icon = benefit.icon;
                  return (
                    <div key={idx} className="flex items-start gap-4" data-testid={`benefit-${idx}`}>
                      <div className="p-3 bg-teal-100 rounded-xl flex-shrink-0">
                        <Icon className="w-6 h-6 text-teal-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg text-gray-900 mb-1">{benefit.title}</h3>
                        <p className="text-gray-600">{benefit.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-teal-600 via-blue-600 to-purple-600 relative overflow-hidden" data-testid="cta-section">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-4xl lg:text-5xl font-bold text-white mb-6" style={{ fontFamily: 'EB Garamond, serif' }} data-testid="cta-title">
            Ready to Start Your Wellness Journey?
          </h2>
          <p className="text-xl text-teal-50 mb-8 leading-relaxed" data-testid="cta-description">
            Join thousands of people who have found support, connection, and healing through MoodMesh. 
            Your path to better mental health starts today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg"
              onClick={() => navigate("/register")}
              className="bg-white text-teal-600 hover:bg-gray-100 px-8 py-6 text-lg shadow-xl hover:shadow-2xl transition-all"
              data-testid="cta-register-button"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button 
              size="lg"
              variant="outline"
              onClick={() => navigate("/login")}
              className="border-2 border-white text-white hover:bg-white/10 px-8 py-6 text-lg"
              data-testid="cta-login-button"
            >
              Sign In
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12 px-6" data-testid="footer">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-teal-500 to-emerald-500 rounded-xl">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <span className="text-2xl font-bold text-white" style={{ fontFamily: 'EB Garamond, serif' }}>
                  MoodMesh
                </span>
              </div>
              <p className="text-gray-400 leading-relaxed mb-4">
                Your compassionate companion for mental wellness. AI-powered support, 
                caring communities, and personalized guidance for your mental health journey.
              </p>
              <div className="flex gap-4">
                {stats.map((stat, idx) => (
                  <div key={idx} className="text-center">
                    <div className="text-lg font-bold text-teal-400">{stat.value}</div>
                    <div className="text-xs text-gray-500">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold text-white mb-4">Features</h3>
              <ul className="space-y-2 text-sm">
                <li className="hover:text-teal-400 cursor-pointer transition-colors">Mood Tracking</li>
                <li className="hover:text-teal-400 cursor-pointer transition-colors">AI Therapist</li>
                <li className="hover:text-teal-400 cursor-pointer transition-colors">Communities</li>
                <li className="hover:text-teal-400 cursor-pointer transition-colors">Wellness Stars</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-white mb-4">Support</h3>
              <ul className="space-y-2 text-sm">
                <li className="hover:text-teal-400 cursor-pointer transition-colors">Help Center</li>
                <li className="hover:text-teal-400 cursor-pointer transition-colors">Privacy Policy</li>
                <li className="hover:text-teal-400 cursor-pointer transition-colors">Terms of Service</li>
                <li className="hover:text-teal-400 cursor-pointer transition-colors">Contact Us</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-500">
            <p>© 2024 MoodMesh. All rights reserved. Made with ❤️ for better mental health.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
