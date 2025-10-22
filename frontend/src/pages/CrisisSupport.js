import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { Shield, Heart, Phone, Users, Edit, Trash2, Plus, Save, Globe, AlertCircle } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CRISIS_HOTLINES = {
  "United States": [
    { name: "988 Suicide & Crisis Lifeline", number: "988", available: "24/7" },
    { name: "Crisis Text Line", number: "Text HOME to 741741", available: "24/7" },
    { name: "SAMHSA National Helpline", number: "1-800-662-4357", available: "24/7" }
  ],
  "United Kingdom": [
    { name: "Samaritans", number: "116 123", available: "24/7" },
    { name: "PAPYRUS (under 35)", number: "0800 068 4141", available: "9am-midnight" },
    { name: "Shout Crisis Text Line", number: "Text SHOUT to 85258", available: "24/7" }
  ],
  "Canada": [
    { name: "Canada Suicide Prevention Service", number: "1-833-456-4566", available: "24/7" },
    { name: "Kids Help Phone", number: "1-800-668-6868", available: "24/7" },
    { name: "Crisis Text Line", number: "Text TALK to 686868", available: "24/7" }
  ],
  "Australia": [
    { name: "Lifeline", number: "13 11 14", available: "24/7" },
    { name: "Kids Helpline", number: "1800 55 1800", available: "24/7" },
    { name: "Beyond Blue", number: "1300 22 4636", available: "24/7" }
  ],
  "India": [
    { name: "AASRA", number: "91-9820466726", available: "24/7" },
    { name: "Sneha India", number: "91-44-24640050", available: "24/7" },
    { name: "Vandrevala Foundation", number: "1860-2662-345", available: "24/7" }
  ],
  "International": [
    { name: "Befrienders Worldwide", number: "Visit befrienders.org", available: "Varies by country" },
    { name: "International Association for Suicide Prevention", number: "Visit iasp.info/resources", available: "Varies by country" }
  ]
};

const CrisisSupport = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState("United States");
  
  // Safety Plan
  const [safetyPlan, setSafetyPlan] = useState({
    warning_signs: [],
    coping_strategies: [],
    contacts_to_call: [],
    professional_contacts: [],
    safe_environment_steps: [],
    reasons_to_live: []
  });
  const [newWarningSign, setNewWarningSign] = useState("");
  const [newCopingStrategy, setNewCopingStrategy] = useState("");
  const [newContactToCall, setNewContactToCall] = useState("");
  const [newProfessionalContact, setNewProfessionalContact] = useState("");
  const [newSafeStep, setNewSafeStep] = useState("");
  const [newReason, setNewReason] = useState("");
  
  // Emergency Contacts
  const [emergencyContacts, setEmergencyContacts] = useState([]);
  const [showAddContact, setShowAddContact] = useState(false);
  const [newContact, setNewContact] = useState({ name: "", phone: "", relationship: "", email: "" });
  const [editingContact, setEditingContact] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("moodmesh_user");
    const storedToken = localStorage.getItem("moodmesh_token");
    if (!storedUser || !storedToken) {
      navigate("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);
    loadSafetyPlan(userData.user_id);
    loadEmergencyContacts(userData.user_id);
  }, [navigate]);

  const loadSafetyPlan = async (userId) => {
    try {
      const response = await axios.get(`${API}/crisis/safety-plan/${userId}`);
      if (response.data) {
        setSafetyPlan(response.data);
      }
    } catch (error) {
      console.error("Failed to load safety plan", error);
    }
  };

  const saveSafetyPlan = async () => {
    try {
      await axios.post(`${API}/crisis/safety-plan`, {
        user_id: user.user_id,
        ...safetyPlan
      });
      toast.success("Safety plan saved successfully!");
    } catch (error) {
      toast.error("Failed to save safety plan");
      console.error(error);
    }
  };

  const addToList = (listName, value, setValue) => {
    if (!value.trim()) return;
    setSafetyPlan(prev => ({
      ...prev,
      [listName]: [...prev[listName], value.trim()]
    }));
    setValue("");
  };

  const removeFromList = (listName, index) => {
    setSafetyPlan(prev => ({
      ...prev,
      [listName]: prev[listName].filter((_, i) => i !== index)
    }));
  };

  const loadEmergencyContacts = async (userId) => {
    try {
      const response = await axios.get(`${API}/crisis/emergency-contacts/${userId}`);
      setEmergencyContacts(response.data);
    } catch (error) {
      console.error("Failed to load emergency contacts", error);
    }
  };

  const addEmergencyContact = async () => {
    if (!newContact.name || !newContact.phone || !newContact.relationship) {
      toast.error("Name, phone, and relationship are required");
      return;
    }
    
    try {
      await axios.post(`${API}/crisis/emergency-contacts`, {
        user_id: user.user_id,
        ...newContact
      });
      toast.success("Emergency contact added!");
      setNewContact({ name: "", phone: "", relationship: "", email: "" });
      setShowAddContact(false);
      loadEmergencyContacts(user.user_id);
    } catch (error) {
      toast.error("Failed to add emergency contact");
      console.error(error);
    }
  };

  const deleteEmergencyContact = async (contactId) => {
    try {
      await axios.delete(`${API}/crisis/emergency-contacts/${contactId}`);
      toast.success("Emergency contact deleted");
      loadEmergencyContacts(user.user_id);
    } catch (error) {
      toast.error("Failed to delete emergency contact");
      console.error(error);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-teal-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <Button variant="outline" onClick={() => navigate("/dashboard")}>
            ← Back to Dashboard
          </Button>
        </div>

        {/* Header */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-4 bg-purple-100 rounded-full">
              <Shield className="w-12 h-12 text-purple-600" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900">Crisis Support & Resources</h1>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Access immediate help, create your safety plan, and manage emergency contacts. You're not alone.
          </p>
        </div>

        {/* Emergency Warning Banner */}
        <Card className="mb-6 border-2 border-red-300 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-8 h-8 text-red-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-xl font-bold text-red-900 mb-2">If you're in immediate danger</h3>
                <p className="text-red-800 mb-3">
                  Please call emergency services (911 in US, 999 in UK, 000 in Australia) or go to your nearest emergency room.
                  Your life matters, and help is available right now.
                </p>
                <div className="flex gap-3">
                  <Badge className="bg-red-600 text-white">Emergency: 911</Badge>
                  <Badge className="bg-red-600 text-white">Crisis: 988</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Crisis Hotlines */}
          <Card className="border-2 border-purple-200">
            <CardHeader className="bg-gradient-to-r from-purple-50 to-blue-50">
              <CardTitle className="flex items-center gap-2">
                <Phone className="w-6 h-6 text-purple-600" />
                Crisis Hotlines
              </CardTitle>
              <CardDescription>24/7 support is just a call away</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="mb-4">
                <label className="flex items-center gap-2 text-sm font-medium mb-2">
                  <Globe className="w-4 h-4" />
                  Select your country/region:
                </label>
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="w-full p-2 border rounded-md bg-white"
                >
                  {Object.keys(CRISIS_HOTLINES).map(country => (
                    <option key={country} value={country}>{country}</option>
                  ))}
                </select>
              </div>

              <ScrollArea className="h-72">
                <div className="space-y-3">
                  {CRISIS_HOTLINES[selectedCountry].map((hotline, idx) => (
                    <div key={idx} className="p-4 bg-white border-2 border-purple-100 rounded-lg hover:border-purple-300 transition-colors">
                      <h4 className="font-semibold text-gray-900">{hotline.name}</h4>
                      <p className="text-lg font-bold text-purple-600 my-1">{hotline.number}</p>
                      <p className="text-sm text-gray-600">Available: {hotline.available}</p>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Emergency Contacts */}
          <Card className="border-2 border-blue-200">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-teal-50">
              <CardTitle className="flex items-center gap-2">
                <Users className="w-6 h-6 text-blue-600" />
                Emergency Contacts
              </CardTitle>
              <CardDescription>People you can reach out to</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <ScrollArea className="h-72 mb-4">
                <div className="space-y-3">
                  {emergencyContacts.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No emergency contacts yet. Add someone you trust.</p>
                  ) : (
                    emergencyContacts.map(contact => (
                      <div key={contact.id} className="p-4 bg-white border-2 border-blue-100 rounded-lg">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900">{contact.name}</h4>
                            <p className="text-sm text-gray-600">{contact.relationship}</p>
                            <p className="text-blue-600 font-medium mt-1">{contact.phone}</p>
                            {contact.email && <p className="text-sm text-gray-600">{contact.email}</p>}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteEmergencyContact(contact.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>

              {!showAddContact ? (
                <Button onClick={() => setShowAddContact(true)} className="w-full bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Emergency Contact
                </Button>
              ) : (
                <div className="space-y-3 p-4 bg-blue-50 rounded-lg">
                  <Input
                    placeholder="Name *"
                    value={newContact.name}
                    onChange={(e) => setNewContact({...newContact, name: e.target.value})}
                  />
                  <Input
                    placeholder="Phone *"
                    value={newContact.phone}
                    onChange={(e) => setNewContact({...newContact, phone: e.target.value})}
                  />
                  <Input
                    placeholder="Relationship (e.g., Friend, Family) *"
                    value={newContact.relationship}
                    onChange={(e) => setNewContact({...newContact, relationship: e.target.value})}
                  />
                  <Input
                    placeholder="Email (optional)"
                    value={newContact.email}
                    onChange={(e) => setNewContact({...newContact, email: e.target.value})}
                  />
                  <div className="flex gap-2">
                    <Button onClick={addEmergencyContact} className="flex-1 bg-blue-600 hover:bg-blue-700">
                      Save Contact
                    </Button>
                    <Button onClick={() => setShowAddContact(false)} variant="outline" className="flex-1">
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Safety Plan Creator */}
        <Card className="mt-6 border-2 border-teal-200">
          <CardHeader className="bg-gradient-to-r from-teal-50 to-emerald-50">
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Heart className="w-6 h-6 text-teal-600" />
                  My Safety Plan
                </CardTitle>
                <CardDescription>A personalized plan to help you through difficult moments</CardDescription>
              </div>
              <Button onClick={saveSafetyPlan} className="bg-teal-600 hover:bg-teal-700">
                <Save className="w-4 h-4 mr-2" />
                Save Plan
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* Warning Signs */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">⚠️ Warning Signs</h3>
                <p className="text-sm text-gray-600 mb-3">What tells me I might be starting to feel unsafe?</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="E.g., Feeling hopeless, isolating from friends..."
                    value={newWarningSign}
                    onChange={(e) => setNewWarningSign(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addToList('warning_signs', newWarningSign, setNewWarningSign)}
                  />
                  <Button onClick={() => addToList('warning_signs', newWarningSign, setNewWarningSign)}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {safetyPlan.warning_signs.map((sign, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-amber-50 rounded">
                      <span className="text-sm">{sign}</span>
                      <Button variant="ghost" size="sm" onClick={() => removeFromList('warning_signs', idx)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Coping Strategies */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">💪 Coping Strategies</h3>
                <p className="text-sm text-gray-600 mb-3">Things I can do on my own to feel better</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="E.g., Go for a walk, listen to music, deep breathing..."
                    value={newCopingStrategy}
                    onChange={(e) => setNewCopingStrategy(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addToList('coping_strategies', newCopingStrategy, setNewCopingStrategy)}
                  />
                  <Button onClick={() => addToList('coping_strategies', newCopingStrategy, setNewCopingStrategy)}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {safetyPlan.coping_strategies.map((strategy, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="text-sm">{strategy}</span>
                      <Button variant="ghost" size="sm" onClick={() => removeFromList('coping_strategies', idx)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Contacts to Call */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">👥 People to Contact</h3>
                <p className="text-sm text-gray-600 mb-3">Trusted people I can reach out to for support</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="E.g., Mom (555-1234), Best friend Sarah..."
                    value={newContactToCall}
                    onChange={(e) => setNewContactToCall(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addToList('contacts_to_call', newContactToCall, setNewContactToCall)}
                  />
                  <Button onClick={() => addToList('contacts_to_call', newContactToCall, setNewContactToCall)}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {safetyPlan.contacts_to_call.map((contact, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                      <span className="text-sm">{contact}</span>
                      <Button variant="ghost" size="sm" onClick={() => removeFromList('contacts_to_call', idx)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Professional Contacts */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">🏥 Professional Contacts</h3>
                <p className="text-sm text-gray-600 mb-3">Therapists, counselors, or crisis services</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="E.g., Dr. Smith (555-6789), Crisis Line 988..."
                    value={newProfessionalContact}
                    onChange={(e) => setNewProfessionalContact(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addToList('professional_contacts', newProfessionalContact, setNewProfessionalContact)}
                  />
                  <Button onClick={() => addToList('professional_contacts', newProfessionalContact, setNewProfessionalContact)}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {safetyPlan.professional_contacts.map((contact, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-purple-50 rounded">
                      <span className="text-sm">{contact}</span>
                      <Button variant="ghost" size="sm" onClick={() => removeFromList('professional_contacts', idx)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Safe Environment Steps */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">🔒 Making My Environment Safer</h3>
                <p className="text-sm text-gray-600 mb-3">Steps to remove access to harmful means</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="E.g., Lock up medications, remove sharp objects..."
                    value={newSafeStep}
                    onChange={(e) => setNewSafeStep(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addToList('safe_environment_steps', newSafeStep, setNewSafeStep)}
                  />
                  <Button onClick={() => addToList('safe_environment_steps', newSafeStep, setNewSafeStep)}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {safetyPlan.safe_environment_steps.map((step, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-teal-50 rounded">
                      <span className="text-sm">{step}</span>
                      <Button variant="ghost" size="sm" onClick={() => removeFromList('safe_environment_steps', idx)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Reasons to Live */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">💖 Reasons to Keep Going</h3>
                <p className="text-sm text-gray-600 mb-3">Things that make life worth living</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="E.g., My family, my pet, future dreams..."
                    value={newReason}
                    onChange={(e) => setNewReason(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addToList('reasons_to_live', newReason, setNewReason)}
                  />
                  <Button onClick={() => addToList('reasons_to_live', newReason, setNewReason)}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-1">
                  {safetyPlan.reasons_to_live.map((reason, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-pink-50 rounded">
                      <span className="text-sm">{reason}</span>
                      <Button variant="ghost" size="sm" onClick={() => removeFromList('reasons_to_live', idx)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CrisisSupport;
