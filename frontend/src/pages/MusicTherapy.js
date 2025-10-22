import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { 
  Music, Play, Pause, Volume2, Search, Sparkles, 
  Mic, MicOff, Save, History, Heart, Waves, 
  Wind, Brain, Home, Moon, Sun, Focus, Cloud
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MusicTherapy = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  
  // Spotify state
  const [spotifyConnected, setSpotifyConnected] = useState(false);
  const [spotifyAccessToken, setSpotifyAccessToken] = useState(null);
  const [spotifyProfile, setSpotifyProfile] = useState(null);
  
  // Built-in audio library state
  const [builtinAudio, setBuiltinAudio] = useState({ nature: [], white_noise: [], binaural_beats: [] });
  const [currentAudio, setCurrentAudio] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);
  
  // Recommendations state
  const [recommendations, setRecommendations] = useState(null);
  const [spotifyTracks, setSpotifyTracks] = useState([]);
  
  // Audio journal state
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [journalText, setJournalText] = useState("");
  const [journalMood, setJournalMood] = useState("");
  const [audioJournals, setAudioJournals] = useState([]);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  
  // History state
  const [musicHistory, setMusicHistory] = useState([]);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    
    // Check for Spotify callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const error = urlParams.get("error");
    
    if (error) {
      // Spotify returned an error
      const errorDescription = urlParams.get("error_description") || "Authorization failed";
      toast.error(`Spotify Error: ${errorDescription}`);
      window.history.replaceState({}, document.title, "/music");
    } else if (code) {
      handleSpotifyCallback(code);
      window.history.replaceState({}, document.title, "/music");
    }
    
    // Check for existing Spotify token
    const storedSpotifyToken = localStorage.getItem("spotify_access_token");
    if (storedSpotifyToken) {
      setSpotifyAccessToken(storedSpotifyToken);
      setSpotifyConnected(true);
      fetchSpotifyProfile(storedSpotifyToken);
    }
    
    // Load built-in audio library
    fetchBuiltinAudio();
    
    // Load recommendations
    fetchRecommendations(userData.user_id);
    
    // Load audio journals
    fetchAudioJournals(userData.user_id);
    
    // Load music history
    fetchMusicHistory(userData.user_id);
  }, [navigate]);
  
  useEffect(() => {
    // Setup audio element
    if (!audioRef.current) {
      audioRef.current = new Audio();
      audioRef.current.crossOrigin = "anonymous";
      audioRef.current.addEventListener("ended", () => setIsPlaying(false));
      audioRef.current.addEventListener("error", (e) => {
        console.error("Audio playback error:", e);
        setIsPlaying(false);
        toast.error("Failed to play audio. Please try another track.");
      });
    }
  }, []);

  // Spotify functions
  const handleSpotifyLogin = async () => {
    try {
      const response = await axios.get(`${API}/music/spotify/login`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      console.error("Spotify login error:", error);
      const errorMessage = error.response?.data?.detail || "Failed to connect to Spotify";
      toast.error(errorMessage);
    }
  };

  const handleSpotifyCallback = async (code) => {
    try {
      const response = await axios.get(`${API}/music/spotify/callback?code=${code}`);
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem("spotify_access_token", access_token);
      localStorage.setItem("spotify_refresh_token", refresh_token);
      
      setSpotifyAccessToken(access_token);
      setSpotifyConnected(true);
      
      await fetchSpotifyProfile(access_token);
      
      toast.success("Connected to Spotify!");
    } catch (error) {
      console.error("Spotify callback error:", error);
      const errorMessage = error.response?.data?.detail || "Failed to connect to Spotify. Please check your Spotify app credentials.";
      toast.error(errorMessage);
    }
  };

  const fetchSpotifyProfile = async (token) => {
    try {
      const response = await axios.get(`${API}/music/spotify/profile?access_token=${token}`);
      setSpotifyProfile(response.data);
    } catch (error) {
      console.error("Error fetching Spotify profile:", error);
    }
  };

  const searchSpotify = async () => {
    if (!searchQuery.trim() || !spotifyAccessToken) return;
    
    try {
      const response = await axios.get(
        `${API}/music/spotify/search?q=${encodeURIComponent(searchQuery)}&access_token=${spotifyAccessToken}`
      );
      setSearchResults(response.data.tracks);
    } catch (error) {
      console.error("Spotify search error:", error);
      toast.error("Search failed");
    }
  };

  const getSpotifyRecommendations = async (genres) => {
    if (!spotifyAccessToken) return;
    
    try {
      const response = await axios.get(
        `${API}/music/spotify/recommendations?access_token=${spotifyAccessToken}&seed_genres=${genres.join(',')}`
      );
      setSpotifyTracks(response.data.tracks);
    } catch (error) {
      console.error("Spotify recommendations error:", error);
    }
  };

  // Built-in audio functions
  const fetchBuiltinAudio = async () => {
    try {
      const response = await axios.get(`${API}/music/library`);
      setBuiltinAudio(response.data);
    } catch (error) {
      console.error("Error fetching audio library:", error);
    }
  };

  const playBuiltinAudio = (audio) => {
    if (audioRef.current) {
      if (currentAudio?.id === audio.id && isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.src = audio.audio_url;
        audioRef.current.load(); // Ensure the new source is loaded
        
        audioRef.current.play()
          .then(() => {
            setCurrentAudio(audio);
            setIsPlaying(true);
            
            // Save to history
            saveToHistory(audio.title, "Built-in Audio", "builtin", audio.duration);
          })
          .catch((error) => {
            console.error("Playback failed:", error);
            toast.error("Unable to play this audio. It may not be available.");
            setIsPlaying(false);
          });
      }
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  // Recommendations
  const fetchRecommendations = async (userId) => {
    try {
      const response = await axios.get(`${API}/music/recommendations/${userId}`);
      setRecommendations(response.data);
      
      // If Spotify is connected, get Spotify recommendations too
      if (spotifyAccessToken && response.data.spotify_genres) {
        await getSpotifyRecommendations(response.data.spotify_genres);
      }
    } catch (error) {
      console.error("Error fetching recommendations:", error);
    }
  };

  // Audio journaling
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        const audioUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio(audioUrl);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      toast.success("Recording started");
    } catch (error) {
      console.error("Recording error:", error);
      toast.error("Failed to start recording. Please allow microphone access.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      toast.success("Recording stopped");
    }
  };

  const saveAudioJournal = async () => {
    if (!journalText.trim() && !recordedAudio) {
      toast.error("Please add some text or a voice recording");
      return;
    }

    try {
      await axios.post(`${API}/music/journal/create`, {
        user_id: user.user_id,
        mood: journalMood || "Neutral",
        journal_text: journalText,
        voice_recording_url: recordedAudio,
        music_played: currentAudio?.title,
        music_source: currentAudio ? "builtin" : null
      });

      toast.success("Audio journal saved! +3 wellness stars");
      
      // Reset form
      setJournalText("");
      setJournalMood("");
      setRecordedAudio(null);
      
      // Reload journals
      fetchAudioJournals(user.user_id);
    } catch (error) {
      console.error("Error saving journal:", error);
      toast.error("Failed to save journal");
    }
  };

  const fetchAudioJournals = async (userId) => {
    try {
      const response = await axios.get(`${API}/music/journal/${userId}`);
      setAudioJournals(response.data.journals);
    } catch (error) {
      console.error("Error fetching journals:", error);
    }
  };

  // Music history
  const saveToHistory = async (trackName, artist, source, duration) => {
    try {
      await axios.post(`${API}/music/history/save`, {
        user_id: user.user_id,
        track_name: trackName,
        artist: artist,
        source: source,
        duration_played: duration
      });
    } catch (error) {
      console.error("Error saving history:", error);
    }
  };

  const fetchMusicHistory = async (userId) => {
    try {
      const response = await axios.get(`${API}/music/history/${userId}`);
      setMusicHistory(response.data.history);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const getMoodIcon = (category) => {
    switch (category) {
      case 'nature': return <Waves className="w-5 h-5" />;
      case 'white_noise': return <Wind className="w-5 h-5" />;
      case 'binaural_beats': return <Brain className="w-5 h-5" />;
      default: return <Music className="w-5 h-5" />;
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-teal-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate("/")} data-testid="back-button">
              <Home className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
            <div>
              <h1 className="text-4xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
                Music & Sound Therapy 🎵
              </h1>
              <p className="text-gray-600">Heal through the power of sound</p>
            </div>
          </div>
          
          {/* Spotify Connection Status */}
          {!spotifyConnected ? (
            <Button onClick={handleSpotifyLogin} className="bg-green-600 hover:bg-green-700">
              <Music className="w-4 h-4 mr-2" />
              Connect Spotify
            </Button>
          ) : (
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-md">
              <Music className="w-5 h-5 text-green-600" />
              <span className="font-semibold">{spotifyProfile?.display_name || "Connected"}</span>
              <Badge variant={spotifyProfile?.is_premium ? "default" : "secondary"}>
                {spotifyProfile?.is_premium ? "Premium" : "Free"}
              </Badge>
            </div>
          )}
        </div>

        {/* Currently Playing */}
        {currentAudio && (
          <Card className="mb-6 bg-gradient-to-r from-purple-100 to-blue-100">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => playBuiltinAudio(currentAudio)}
                    className="rounded-full"
                  >
                    {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                  </Button>
                  <div>
                    <h3 className="font-semibold">{currentAudio.title}</h3>
                    <p className="text-sm text-gray-600">{currentAudio.description}</p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={stopAudio}>
                  <Volume2 className="w-5 h-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Tabs */}
        <Tabs defaultValue="recommendations" className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6">
            <TabsTrigger value="recommendations">
              <Sparkles className="w-4 h-4 mr-2" />
              For You
            </TabsTrigger>
            <TabsTrigger value="browse">
              <Music className="w-4 h-4 mr-2" />
              Browse
            </TabsTrigger>
            <TabsTrigger value="builtin">
              <Waves className="w-4 h-4 mr-2" />
              Sounds
            </TabsTrigger>
            <TabsTrigger value="journal">
              <Mic className="w-4 h-4 mr-2" />
              Journal
            </TabsTrigger>
            <TabsTrigger value="history">
              <History className="w-4 h-4 mr-2" />
              History
            </TabsTrigger>
          </TabsList>

          {/* Recommendations Tab */}
          <TabsContent value="recommendations">
            <Card>
              <CardHeader>
                <CardTitle>Personalized Recommendations</CardTitle>
                <CardDescription>Based on your recent mood logs</CardDescription>
              </CardHeader>
              <CardContent>
                {recommendations ? (
                  <div className="space-y-6">
                    {/* Mood Analysis */}
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <h3 className="font-semibold mb-2">Mood Analysis</h3>
                      <p className="text-gray-700">{recommendations.mood_analysis}</p>
                    </div>

                    {/* Built-in Recommendations */}
                    <div>
                      <h3 className="font-semibold mb-3">Recommended Sounds</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {recommendations.builtin_recommendations?.map((audio) => (
                          <Card key={audio.id} className="hover:shadow-lg transition-shadow">
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="p-2 bg-blue-100 rounded-lg">
                                    {getMoodIcon(audio.category)}
                                  </div>
                                  <div>
                                    <h4 className="font-semibold">{audio.title}</h4>
                                    <p className="text-xs text-gray-500 capitalize">{audio.category.replace('_', ' ')}</p>
                                  </div>
                                </div>
                                <Button
                                  variant="outline"
                                  size="icon"
                                  onClick={() => playBuiltinAudio(audio)}
                                >
                                  <Play className="w-4 h-4" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>

                    {/* Spotify Recommendations */}
                    {spotifyConnected && spotifyTracks.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-3">Spotify Recommendations</h3>
                        <ScrollArea className="h-96">
                          <div className="space-y-2">
                            {spotifyTracks.map((track) => (
                              <Card key={track.id} className="hover:shadow-md transition-shadow">
                                <CardContent className="p-3">
                                  <div className="flex items-center gap-3">
                                    {track.image_url && (
                                      <img src={track.image_url} alt={track.name} className="w-12 h-12 rounded" />
                                    )}
                                    <div className="flex-1">
                                      <h4 className="font-semibold text-sm">{track.name}</h4>
                                      <p className="text-xs text-gray-500">{track.artist}</p>
                                    </div>
                                    {track.preview_url && (
                                      <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => {
                                          if (audioRef.current) {
                                            audioRef.current.src = track.preview_url;
                                            audioRef.current.play();
                                            setIsPlaying(true);
                                          }
                                        }}
                                      >
                                        Preview
                                      </Button>
                                    )}
                                  </div>
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        </ScrollArea>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-center text-gray-500">Loading recommendations...</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Browse Tab */}
          <TabsContent value="browse">
            <Card>
              <CardHeader>
                <CardTitle>Browse by Mood</CardTitle>
                <CardDescription>Search and explore music</CardDescription>
              </CardHeader>
              <CardContent>
                {spotifyConnected ? (
                  <div className="space-y-4">
                    {/* Search Bar */}
                    <div className="flex gap-2">
                      <Input
                        placeholder="Search for music..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && searchSpotify()}
                      />
                      <Button onClick={searchSpotify}>
                        <Search className="w-4 h-4 mr-2" />
                        Search
                      </Button>
                    </div>

                    {/* Mood Categories */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {[
                        { name: "Calming", icon: <Moon className="w-5 h-5" />, genres: ["ambient", "chill", "meditation"] },
                        { name: "Energizing", icon: <Sun className="w-5 h-5" />, genres: ["pop", "dance", "electronic"] },
                        { name: "Focus", icon: <Focus className="w-5 h-5" />, genres: ["classical", "instrumental", "study"] },
                        { name: "Sleep", icon: <Cloud className="w-5 h-5" />, genres: ["ambient", "sleep", "lullaby"] }
                      ].map((mood) => (
                        <Button
                          key={mood.name}
                          variant="outline"
                          className="h-20 flex-col"
                          onClick={() => getSpotifyRecommendations(mood.genres)}
                        >
                          {mood.icon}
                          <span className="mt-2">{mood.name}</span>
                        </Button>
                      ))}
                    </div>

                    {/* Search Results */}
                    {searchResults.length > 0 && (
                      <ScrollArea className="h-96 mt-4">
                        <div className="space-y-2">
                          {searchResults.map((track) => (
                            <Card key={track.id} className="hover:shadow-md transition-shadow">
                              <CardContent className="p-3">
                                <div className="flex items-center gap-3">
                                  {track.image_url && (
                                    <img src={track.image_url} alt={track.name} className="w-12 h-12 rounded" />
                                  )}
                                  <div className="flex-1">
                                    <h4 className="font-semibold text-sm">{track.name}</h4>
                                    <p className="text-xs text-gray-500">{track.artist}</p>
                                  </div>
                                  {track.preview_url && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => {
                                        if (audioRef.current) {
                                          audioRef.current.src = track.preview_url;
                                          audioRef.current.play();
                                          setIsPlaying(true);
                                        }
                                      }}
                                    >
                                      Preview
                                    </Button>
                                  )}
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </ScrollArea>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Music className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-500 mb-4">Connect Spotify to browse and search music</p>
                    <Button onClick={handleSpotifyLogin} className="bg-green-600 hover:bg-green-700">
                      Connect Spotify
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Built-in Sounds Tab */}
          <TabsContent value="builtin">
            <div className="space-y-6">
              {/* Nature Sounds */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Waves className="w-5 h-5 text-blue-600" />
                    Nature Sounds
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {builtinAudio.nature?.map((audio) => (
                      <Card key={audio.id} className="hover:shadow-lg transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold">{audio.title}</h4>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => playBuiltinAudio(audio)}
                              className={currentAudio?.id === audio.id && isPlaying ? "bg-blue-100" : ""}
                            >
                              {currentAudio?.id === audio.id && isPlaying ? (
                                <Pause className="w-4 h-4" />
                              ) : (
                                <Play className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{audio.description}</p>
                          <div className="flex flex-wrap gap-1">
                            {audio.tags?.map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* White Noise */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Wind className="w-5 h-5 text-gray-600" />
                    White Noise
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {builtinAudio.white_noise?.map((audio) => (
                      <Card key={audio.id} className="hover:shadow-lg transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold">{audio.title}</h4>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => playBuiltinAudio(audio)}
                              className={currentAudio?.id === audio.id && isPlaying ? "bg-gray-100" : ""}
                            >
                              {currentAudio?.id === audio.id && isPlaying ? (
                                <Pause className="w-4 h-4" />
                              ) : (
                                <Play className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{audio.description}</p>
                          <div className="flex flex-wrap gap-1">
                            {audio.tags?.map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Binaural Beats */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-600" />
                    Binaural Beats
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {builtinAudio.binaural_beats?.map((audio) => (
                      <Card key={audio.id} className="hover:shadow-lg transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold">{audio.title}</h4>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => playBuiltinAudio(audio)}
                              className={currentAudio?.id === audio.id && isPlaying ? "bg-purple-100" : ""}
                            >
                              {currentAudio?.id === audio.id && isPlaying ? (
                                <Pause className="w-4 h-4" />
                              ) : (
                                <Play className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{audio.description}</p>
                          <div className="flex flex-wrap gap-1">
                            {audio.tags?.map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Audio Journal Tab */}
          <TabsContent value="journal">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Create Journal */}
              <Card>
                <CardHeader>
                  <CardTitle>Create Audio Journal</CardTitle>
                  <CardDescription>Write or record your thoughts with music</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Current Mood</label>
                    <Input
                      placeholder="How are you feeling?"
                      value={journalMood}
                      onChange={(e) => setJournalMood(e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Journal Entry</label>
                    <Textarea
                      placeholder="Write your thoughts..."
                      value={journalText}
                      onChange={(e) => setJournalText(e.target.value)}
                      rows={6}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Voice Recording</label>
                    <div className="flex gap-2">
                      {!isRecording ? (
                        <Button onClick={startRecording} variant="outline" className="flex-1">
                          <Mic className="w-4 h-4 mr-2" />
                          Start Recording
                        </Button>
                      ) : (
                        <Button onClick={stopRecording} variant="destructive" className="flex-1">
                          <MicOff className="w-4 h-4 mr-2" />
                          Stop Recording
                        </Button>
                      )}
                    </div>
                    {recordedAudio && (
                      <audio src={recordedAudio} controls className="w-full mt-2" />
                    )}
                  </div>

                  {currentAudio && (
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-gray-600">Playing: {currentAudio.title}</p>
                    </div>
                  )}

                  <Button onClick={saveAudioJournal} className="w-full">
                    <Save className="w-4 h-4 mr-2" />
                    Save Journal (+3 stars)
                  </Button>
                </CardContent>
              </Card>

              {/* Previous Journals */}
              <Card>
                <CardHeader>
                  <CardTitle>Previous Journals</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-96">
                    <div className="space-y-3">
                      {audioJournals.map((journal) => (
                        <Card key={journal.id} className="p-3">
                          <div className="flex items-start justify-between mb-2">
                            <Badge>{journal.mood}</Badge>
                            <span className="text-xs text-gray-500">
                              {new Date(journal.timestamp).toLocaleDateString()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 mb-2">{journal.journal_text}</p>
                          {journal.voice_recording_url && (
                            <audio src={journal.voice_recording_url} controls className="w-full mt-2" />
                          )}
                          {journal.music_played && (
                            <p className="text-xs text-gray-500 mt-2">
                              🎵 Listened to: {journal.music_played}
                            </p>
                          )}
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>Listening History</CardTitle>
                <CardDescription>Your music therapy journey</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-2">
                    {musicHistory.map((item) => (
                      <Card key={item.id} className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {item.source === 'spotify' ? (
                              <Music className="w-5 h-5 text-green-600" />
                            ) : (
                              getMoodIcon(item.source)
                            )}
                            <div>
                              <h4 className="font-semibold text-sm">{item.track_name}</h4>
                              <p className="text-xs text-gray-500">{item.artist}</p>
                            </div>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(item.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MusicTherapy;
