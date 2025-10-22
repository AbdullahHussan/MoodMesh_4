import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BookOpen, Video, Brain, BookMarked, Lightbulb, Search, Bookmark, BookmarkCheck, Clock, Eye, ArrowLeft, ExternalLink } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Resources = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [resources, setResources] = useState([]);
  const [filteredResources, setFilteredResources] = useState([]);
  const [bookmarkedResources, setBookmarkedResources] = useState([]);
  const [selectedResource, setSelectedResource] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [categorySummary, setCategorySummary] = useState({});

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    fetchResources();
    fetchBookmarks(userData.user_id);
    fetchCategorySummary();
  }, [navigate]);

  useEffect(() => {
    filterResources();
  }, [activeTab, searchQuery, resources]);

  const fetchResources = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/resources`);
      setResources(response.data);
    } catch (error) {
      console.error("Failed to fetch resources", error);
      toast.error("Failed to load resources");
    } finally {
      setLoading(false);
    }
  };

  const fetchBookmarks = async (userId) => {
    try {
      const response = await axios.get(`${API}/resources/bookmarks/${userId}`);
      setBookmarkedResources(response.data);
    } catch (error) {
      console.error("Failed to fetch bookmarks", error);
    }
  };

  const fetchCategorySummary = async () => {
    try {
      const response = await axios.get(`${API}/resources/categories/summary`);
      setCategorySummary(response.data);
    } catch (error) {
      console.error("Failed to fetch category summary", error);
    }
  };

  const filterResources = () => {
    let filtered = resources;

    // Filter by category
    if (activeTab !== "all" && activeTab !== "bookmarks") {
      filtered = filtered.filter(r => r.category === activeTab);
    }

    // Show bookmarks
    if (activeTab === "bookmarks") {
      filtered = bookmarkedResources;
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(r =>
        r.title.toLowerCase().includes(query) ||
        r.description.toLowerCase().includes(query) ||
        r.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    setFilteredResources(filtered);
  };

  const handleResourceClick = async (resource) => {
    setSelectedResource(resource);
    setIsDialogOpen(true);
    
    // Fetch full resource details with updated view count
    try {
      const response = await axios.get(`${API}/resources/${resource.id}`);
      setSelectedResource(response.data);
    } catch (error) {
      console.error("Failed to fetch resource details", error);
    }
  };

  const handleBookmark = async (resourceId) => {
    if (!user) return;

    const isBookmarked = bookmarkedResources.some(r => r.id === resourceId);

    try {
      if (isBookmarked) {
        await axios.delete(`${API}/resources/bookmark/${user.user_id}/${resourceId}`);
        setBookmarkedResources(bookmarkedResources.filter(r => r.id !== resourceId));
        toast.success("Bookmark removed");
      } else {
        await axios.post(`${API}/resources/bookmark`, {
          user_id: user.user_id,
          resource_id: resourceId
        });
        const resource = resources.find(r => r.id === resourceId);
        if (resource) {
          setBookmarkedResources([...bookmarkedResources, resource]);
        }
        toast.success("Resource bookmarked!");
      }
    } catch (error) {
      console.error("Failed to toggle bookmark", error);
      toast.error("Failed to update bookmark");
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "conditions": return <Brain className="w-5 h-5" />;
      case "techniques": return <Lightbulb className="w-5 h-5" />;
      case "videos": return <Video className="w-5 h-5" />;
      case "reading": return <BookOpen className="w-5 h-5" />;
      case "myths": return <BookMarked className="w-5 h-5" />;
      default: return <BookOpen className="w-5 h-5" />;
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case "conditions": return "bg-blue-100 text-blue-700 border-blue-300";
      case "techniques": return "bg-green-100 text-green-700 border-green-300";
      case "videos": return "bg-purple-100 text-purple-700 border-purple-300";
      case "reading": return "bg-orange-100 text-orange-700 border-orange-300";
      case "myths": return "bg-pink-100 text-pink-700 border-pink-300";
      default: return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  const isBookmarked = (resourceId) => {
    return bookmarkedResources.some(r => r.id === resourceId);
  };

  const ResourceCard = ({ resource }) => (
    <Card 
      className="h-full border-2 hover:border-teal-400 transition-all duration-300 hover:shadow-xl cursor-pointer transform hover:-translate-y-1"
      onClick={() => handleResourceClick(resource)}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-full ${getCategoryColor(resource.category)}`}>
              {getCategoryIcon(resource.category)}
            </div>
            <Badge variant="outline" className={getCategoryColor(resource.category)}>
              {resource.category}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => {
              e.stopPropagation();
              handleBookmark(resource.id);
            }}
            className="shrink-0"
          >
            {isBookmarked(resource.id) ? (
              <BookmarkCheck className="w-5 h-5 text-teal-600 fill-teal-600" />
            ) : (
              <Bookmark className="w-5 h-5 text-gray-400" />
            )}
          </Button>
        </div>
        <CardTitle className="text-lg line-clamp-2">{resource.title}</CardTitle>
        <CardDescription className="text-sm line-clamp-3">
          {resource.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          {resource.duration_minutes && (
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{resource.duration_minutes} min</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            <span>{resource.views || 0} views</span>
          </div>
        </div>
        {resource.tags && resource.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {resource.tags.slice(0, 3).map((tag, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-teal-50 to-emerald-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button variant="outline" onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
              Resource Library
            </h1>
            <p className="text-gray-600">Educational content to support your mental health journey</p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search articles, videos, exercises..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 py-6 text-lg"
            />
          </div>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
          <TabsList className="grid grid-cols-3 lg:grid-cols-6 gap-2 h-auto p-2 bg-white shadow-md">
            <TabsTrigger value="all" className="flex items-center gap-2 py-3">
              <BookOpen className="w-4 h-4" />
              <span>All</span>
            </TabsTrigger>
            <TabsTrigger value="conditions" className="flex items-center gap-2 py-3">
              <Brain className="w-4 h-4" />
              <span>Conditions ({categorySummary.conditions || 0})</span>
            </TabsTrigger>
            <TabsTrigger value="techniques" className="flex items-center gap-2 py-3">
              <Lightbulb className="w-4 h-4" />
              <span>Techniques ({categorySummary.techniques || 0})</span>
            </TabsTrigger>
            <TabsTrigger value="videos" className="flex items-center gap-2 py-3">
              <Video className="w-4 h-4" />
              <span>Videos ({categorySummary.videos || 0})</span>
            </TabsTrigger>
            <TabsTrigger value="reading" className="flex items-center gap-2 py-3">
              <BookOpen className="w-4 h-4" />
              <span>Reading ({categorySummary.reading || 0})</span>
            </TabsTrigger>
            <TabsTrigger value="myths" className="flex items-center gap-2 py-3">
              <BookMarked className="w-4 h-4" />
              <span>Myths ({categorySummary.myths || 0})</span>
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Bookmarks Tab */}
        <div className="mb-4">
          <Button
            variant={activeTab === "bookmarks" ? "default" : "outline"}
            onClick={() => setActiveTab("bookmarks")}
            className="flex items-center gap-2"
          >
            <BookmarkCheck className="w-4 h-4" />
            My Bookmarks ({bookmarkedResources.length})
          </Button>
        </div>

        {/* Resources Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
            <p className="mt-4 text-gray-600">Loading resources...</p>
          </div>
        ) : filteredResources.length === 0 ? (
          <Card className="p-12 text-center">
            <BookOpen className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No resources found</h3>
            <p className="text-gray-600">
              {searchQuery ? "Try adjusting your search" : "No resources available in this category"}
            </p>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredResources.map((resource) => (
              <ResourceCard key={resource.id} resource={resource} />
            ))}
          </div>
        )}

        {/* Resource Detail Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            {selectedResource && (
              <>
                <DialogHeader>
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className={getCategoryColor(selectedResource.category)}>
                          {selectedResource.category}
                        </Badge>
                        {selectedResource.difficulty && (
                          <Badge variant="secondary">{selectedResource.difficulty}</Badge>
                        )}
                      </div>
                      <DialogTitle className="text-2xl">{selectedResource.title}</DialogTitle>
                      {selectedResource.author && (
                        <p className="text-sm text-gray-600 mt-1">By {selectedResource.author}</p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleBookmark(selectedResource.id);
                      }}
                    >
                      {isBookmarked(selectedResource.id) ? (
                        <BookmarkCheck className="w-6 h-6 text-teal-600 fill-teal-600" />
                      ) : (
                        <Bookmark className="w-6 h-6 text-gray-400" />
                      )}
                    </Button>
                  </div>
                  <DialogDescription className="text-base">
                    {selectedResource.description}
                  </DialogDescription>
                </DialogHeader>

                <div className="mt-4">
                  <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                    {selectedResource.duration_minutes && (
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{selectedResource.duration_minutes} minutes</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1">
                      <Eye className="w-4 h-4" />
                      <span>{selectedResource.views || 0} views</span>
                    </div>
                  </div>

                  {selectedResource.source_url && (
                    <div className="mb-4">
                      <Button
                        variant="outline"
                        onClick={() => window.open(selectedResource.source_url, '_blank')}
                        className="flex items-center gap-2"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Watch Video
                      </Button>
                    </div>
                  )}

                  <ScrollArea className="h-[400px] pr-4">
                    <div className="prose prose-sm max-w-none">
                      <div style={{ whiteSpace: 'pre-wrap' }}>
                        {selectedResource.content}
                      </div>
                    </div>
                  </ScrollArea>

                  {selectedResource.tags && selectedResource.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t">
                      {selectedResource.tags.map((tag, index) => (
                        <Badge key={index} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Resources;
