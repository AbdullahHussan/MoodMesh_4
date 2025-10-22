import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Users, Lock, Globe, Plus, MessageCircle, Trash2, LogOut as LeaveIcon, Brain } from "lucide-react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Communities = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [communities, setCommunities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [joinDialogOpen, setJoinDialogOpen] = useState(false);
  const [selectedCommunity, setSelectedCommunity] = useState(null);

  // Create form
  const [newCommunityName, setNewCommunityName] = useState("");
  const [newCommunityDesc, setNewCommunityDesc] = useState("");
  const [communityType, setCommunityType] = useState("public");
  const [communityPassword, setCommunityPassword] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  // Join form
  const [joinPassword, setJoinPassword] = useState("");
  const [isJoining, setIsJoining] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    fetchCommunities(userData.user_id);
  }, [navigate]);

  const fetchCommunities = async (userId) => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/communities/list/${userId}`);
      setCommunities(response.data);
    } catch (error) {
      console.error("Failed to fetch communities", error);
      toast.error("Failed to load communities");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateCommunity = async () => {
    if (!newCommunityName.trim()) {
      toast.error("Please enter a community name");
      return;
    }
    if (!newCommunityDesc.trim()) {
      toast.error("Please enter a description");
      return;
    }
    if (communityType === "private" && !communityPassword.trim()) {
      toast.error("Please enter a password for private community");
      return;
    }

    setIsCreating(true);
    try {
      await axios.post(`${API}/communities/create`, {
        name: newCommunityName,
        description: newCommunityDesc,
        community_type: communityType,
        password: communityType === "private" ? communityPassword : null,
        creator_id: user.user_id
      });

      toast.success("Community created successfully!");
      setCreateDialogOpen(false);
      setNewCommunityName("");
      setNewCommunityDesc("");
      setCommunityPassword("");
      setCommunityType("public");
      fetchCommunities(user.user_id);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create community");
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinCommunity = async (community) => {
    if (community.community_type === "private") {
      setSelectedCommunity(community);
      setJoinDialogOpen(true);
    } else {
      // Join public community directly
      try {
        await axios.post(`${API}/communities/join`, {
          user_id: user.user_id,
          community_id: community.id
        });
        toast.success("Joined community successfully!");
        fetchCommunities(user.user_id);
      } catch (error) {
        toast.error(error.response?.data?.detail || "Failed to join community");
      }
    }
  };

  const handleJoinPrivate = async () => {
    if (!joinPassword.trim()) {
      toast.error("Please enter the password");
      return;
    }

    setIsJoining(true);
    try {
      await axios.post(`${API}/communities/join`, {
        user_id: user.user_id,
        community_id: selectedCommunity.id,
        password: joinPassword
      });

      toast.success("Joined community successfully!");
      setJoinDialogOpen(false);
      setJoinPassword("");
      setSelectedCommunity(null);
      fetchCommunities(user.user_id);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Incorrect password");
    } finally {
      setIsJoining(false);
    }
  };

  const handleDeleteCommunity = async (communityId) => {
    if (!window.confirm("Are you sure you want to delete this community? All messages will be lost.")) {
      return;
    }

    try {
      await axios.delete(`${API}/communities/${communityId}/${user.user_id}`);
      toast.success("Community deleted successfully");
      fetchCommunities(user.user_id);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete community");
    }
  };

  const handleLeaveCommunity = async (communityId) => {
    if (!window.confirm("Are you sure you want to leave this community?")) {
      return;
    }

    try {
      await axios.post(`${API}/communities/${communityId}/leave?user_id=${user.user_id}`);
      toast.success("Left community successfully");
      fetchCommunities(user.user_id);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to leave community");
    }
  };

  const handleEnterCommunity = (communityId) => {
    navigate(`/community/${communityId}`);
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <Button variant="outline" onClick={() => navigate("/dashboard")} data-testid="back-to-dashboard-communities">
              ← Back to Dashboard
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Users className="w-10 h-10 text-teal-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>Communities</h1>
              <p className="text-gray-600">Connect with supportive communities</p>
            </div>
          </div>

          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-teal-600 hover:bg-teal-700" data-testid="create-community-button">
                <Plus className="w-4 h-4 mr-2" />
                Create Community
              </Button>
            </DialogTrigger>
            <DialogContent data-testid="create-community-dialog">
              <DialogHeader>
                <DialogTitle>Create New Community</DialogTitle>
                <DialogDescription>Set up a new space for support and connection</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label htmlFor="name">Community Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Anxiety Support Group"
                    value={newCommunityName}
                    onChange={(e) => setNewCommunityName(e.target.value)}
                    data-testid="community-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Brief description of your community"
                    value={newCommunityDesc}
                    onChange={(e) => setNewCommunityDesc(e.target.value)}
                    rows={3}
                    data-testid="community-desc-input"
                  />
                </div>
                <div>
                  <Label>Community Type</Label>
                  <RadioGroup value={communityType} onValueChange={setCommunityType} data-testid="community-type-radio">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="public" id="public" data-testid="public-radio" />
                      <Label htmlFor="public" className="flex items-center gap-2 cursor-pointer">
                        <Globe className="w-4 h-4 text-green-600" />
                        Public - Anyone can join
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="private" id="private" data-testid="private-radio" />
                      <Label htmlFor="private" className="flex items-center gap-2 cursor-pointer">
                        <Lock className="w-4 h-4 text-orange-600" />
                        Private - Password required
                      </Label>
                    </div>
                  </RadioGroup>
                </div>
                {communityType === "private" && (
                  <div>
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter password"
                      value={communityPassword}
                      onChange={(e) => setCommunityPassword(e.target.value)}
                      data-testid="community-password-input"
                    />
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button
                  onClick={handleCreateCommunity}
                  disabled={isCreating}
                  className="bg-teal-600 hover:bg-teal-700"
                  data-testid="create-community-submit"
                >
                  {isCreating ? "Creating..." : "Create Community"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading communities...</p>
          </div>
        ) : (
          <>
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <MessageCircle className="w-5 h-5 text-teal-600" />
                Your Communities
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="user-communities-list">
                {communities.filter(c => c.is_member).length === 0 ? (
                  <p className="text-gray-600 col-span-full">You haven't joined any communities yet.</p>
                ) : (
                  communities.filter(c => c.is_member).map((community) => (
                    <Card key={community.id} className="border-2 hover:shadow-lg transition-all" data-testid={`community-card-${community.id}`}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg flex items-center gap-2">
                              {community.community_type === "private" ? (
                                <Lock className="w-4 h-4 text-orange-600" />
                              ) : (
                                <Globe className="w-4 h-4 text-green-600" />
                              )}
                              {community.name}
                            </CardTitle>
                            <CardDescription className="mt-2">{community.description}</CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 mt-3">
                          <Badge variant="secondary" data-testid={`member-count-${community.id}`}>
                            <Users className="w-3 h-3 mr-1" />
                            {community.member_count} members
                          </Badge>
                          {community.creator_id === user.user_id && (
                            <Badge className="bg-purple-600 text-white">Creator</Badge>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <Button
                          onClick={() => handleEnterCommunity(community.id)}
                          className="w-full bg-teal-600 hover:bg-teal-700"
                          data-testid={`enter-community-${community.id}`}
                        >
                          <MessageCircle className="w-4 h-4 mr-2" />
                          Enter Community
                        </Button>
                        <div className="flex gap-2">
                          {community.creator_id === user.user_id ? (
                            <Button
                              variant="destructive"
                              size="sm"
                              className="flex-1"
                              onClick={() => handleDeleteCommunity(community.id)}
                              data-testid={`delete-community-${community.id}`}
                            >
                              <Trash2 className="w-3 h-3 mr-1" />
                              Delete
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              className="flex-1"
                              onClick={() => handleLeaveCommunity(community.id)}
                              data-testid={`leave-community-${community.id}`}
                            >
                              <LeaveIcon className="w-3 h-3 mr-1" />
                              Leave
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </div>

            <div>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Globe className="w-5 h-5 text-green-600" />
                Discover Communities
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="available-communities-list">
                {communities.filter(c => !c.is_member).length === 0 ? (
                  <p className="text-gray-600 col-span-full">No available communities to join.</p>
                ) : (
                  communities.filter(c => !c.is_member).map((community) => (
                    <Card key={community.id} className="border-2 hover:shadow-lg transition-all" data-testid={`available-community-${community.id}`}>
                      <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                          {community.community_type === "private" ? (
                            <Lock className="w-4 h-4 text-orange-600" />
                          ) : (
                            <Globe className="w-4 h-4 text-green-600" />
                          )}
                          {community.name}
                        </CardTitle>
                        <CardDescription className="mt-2">{community.description}</CardDescription>
                        <Badge variant="secondary" className="w-fit mt-2">
                          <Users className="w-3 h-3 mr-1" />
                          {community.member_count} members
                        </Badge>
                      </CardHeader>
                      <CardContent>
                        <Button
                          onClick={() => handleJoinCommunity(community)}
                          className="w-full bg-blue-600 hover:bg-blue-700"
                          data-testid={`join-community-${community.id}`}
                        >
                          Join Community
                        </Button>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </div>
          </>
        )}

        {/* Join Private Community Dialog */}
        <Dialog open={joinDialogOpen} onOpenChange={setJoinDialogOpen}>
          <DialogContent data-testid="join-private-dialog">
            <DialogHeader>
              <DialogTitle>Join Private Community</DialogTitle>
              <DialogDescription>
                {selectedCommunity?.name} is a private community. Please enter the password to join.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="join-password">Password</Label>
              <Input
                id="join-password"
                type="password"
                placeholder="Enter community password"
                value={joinPassword}
                onChange={(e) => setJoinPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleJoinPrivate()}
                data-testid="join-password-input"
              />
            </div>
            <DialogFooter>
              <Button
                onClick={handleJoinPrivate}
                disabled={isJoining}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="join-private-submit"
              >
                {isJoining ? "Joining..." : "Join Community"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <Toaster />
    </div>
  );
};

export default Communities;
