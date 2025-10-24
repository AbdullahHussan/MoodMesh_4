import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  AlertTriangle, Phone, MessageSquare, Heart, Shield, 
  X, UserPlus, ExternalLink, Clock, MapPin 
} from "lucide-react";

const EmergencyPopup = ({ 
  isOpen, 
  onClose, 
  emergencyData, 
  severity = "high", 
  onAddContacts,
  userId
}) => {
  const [copied, setCopied] = useState(null);

  if (!isOpen || !emergencyData) return null;

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const makeCall = (number) => {
    // Remove non-numeric characters for tel: link
    const cleanNumber = number.replace(/[^0-9+]/g, '');
    window.location.href = `tel:${cleanNumber}`;
  };

  const sendSMS = (number) => {
    const cleanNumber = number.replace(/[^0-9+]/g, '');
    window.location.href = `sms:${cleanNumber}`;
  };

  // Determine popup styling based on severity
  const getSeverityStyles = () => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-500',
          headerBg: 'bg-red-100',
          icon: <AlertTriangle className="w-8 h-8 text-red-600 animate-pulse" />,
          badgeColor: 'bg-red-600'
        };
      case 'high':
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-500',
          headerBg: 'bg-orange-100',
          icon: <AlertTriangle className="w-8 h-8 text-orange-600" />,
          badgeColor: 'bg-orange-600'
        };
      case 'medium':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-500',
          headerBg: 'bg-yellow-100',
          icon: <Heart className="w-8 h-8 text-yellow-600" />,
          badgeColor: 'bg-yellow-600'
        };
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-500',
          headerBg: 'bg-blue-100',
          icon: <Shield className="w-8 h-8 text-blue-600" />,
          badgeColor: 'bg-blue-600'
        };
    }
  };

  const styles = getSeverityStyles();
  const isBlocking = severity === 'critical' || severity === 'high';

  return (
    <div 
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${
        isBlocking ? 'bg-black bg-opacity-70' : 'bg-black bg-opacity-40'
      }`}
      onClick={!isBlocking ? onClose : undefined}
    >
      <Card 
        className={`max-w-4xl w-full max-h-[90vh] overflow-hidden ${styles.bg} border-4 ${styles.border} shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <CardHeader className={`${styles.headerBg} relative`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {styles.icon}
              <div>
                <CardTitle className="text-2xl font-bold text-gray-900">
                  Emergency Support Available
                </CardTitle>
                <CardDescription className="text-gray-700 mt-1">
                  {emergencyData.urgent_message}
                </CardDescription>
              </div>
            </div>
            {!isBlocking && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="absolute top-4 right-4"
              >
                <X className="w-5 h-5" />
              </Button>
            )}
          </div>
          <Badge className={`${styles.badgeColor} text-white mt-2 w-fit`}>
            {severity.toUpperCase()} PRIORITY
          </Badge>
        </CardHeader>

        <ScrollArea className="max-h-[calc(90vh-200px)]">
          <CardContent className="p-6 space-y-6">
            
            {/* Close Contacts Section */}
            {emergencyData.has_close_contacts && emergencyData.close_contacts.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Heart className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Your Close Contacts</h3>
                </div>
                <div className="grid gap-3">
                  {emergencyData.close_contacts.map((contact, idx) => (
                    <Card key={idx} className="bg-white border-purple-200 hover:border-purple-400 transition-colors">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="font-semibold text-gray-900">{contact.name}</p>
                            <p className="text-sm text-gray-600">{contact.relationship}</p>
                            <p className="text-sm font-mono text-gray-700 mt-1">{contact.phone}</p>
                            {contact.email && (
                              <p className="text-sm text-gray-600">{contact.email}</p>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => makeCall(contact.phone)}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              <Phone className="w-4 h-4 mr-1" />
                              Call
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => sendSMS(contact.phone)}
                            >
                              <MessageSquare className="w-4 h-4 mr-1" />
                              Text
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ) : (
              <Card className="bg-purple-50 border-purple-300">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <UserPlus className="w-5 h-5 text-purple-600 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-1">No Close Contacts Added</h4>
                      <p className="text-sm text-gray-700 mb-3">
                        Adding close contacts makes it easier to reach out when you need support.
                      </p>
                      <Button 
                        size="sm" 
                        onClick={onAddContacts}
                        className="bg-purple-600 hover:bg-purple-700"
                      >
                        <UserPlus className="w-4 h-4 mr-2" />
                        Add Close Contacts Now
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Crisis Hotlines Section */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-red-600" />
                <h3 className="text-lg font-semibold text-gray-900">24/7 Crisis Hotlines</h3>
              </div>
              <div className="grid gap-3">
                {emergencyData.crisis_hotlines.map((hotline, idx) => (
                  <Card key={idx} className="bg-white border-red-200 hover:border-red-400 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-semibold text-gray-900">{hotline.name}</p>
                          <p className="text-lg font-mono text-red-600 mt-1">{hotline.number}</p>
                          <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {hotline.available}
                            </span>
                            <span className="flex items-center gap-1">
                              <MapPin className="w-4 h-4" />
                              {hotline.country}
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => makeCall(hotline.number)}
                            className="bg-red-600 hover:bg-red-700"
                          >
                            <Phone className="w-4 h-4 mr-1" />
                            Call
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyToClipboard(hotline.number, `hotline-${idx}`)}
                          >
                            {copied === `hotline-${idx}` ? '✓ Copied' : 'Copy'}
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* AI Recommended Resources */}
            {emergencyData.ai_recommended_resources && emergencyData.ai_recommended_resources.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Recommended Actions</h3>
                </div>
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="p-4">
                    <ul className="space-y-2">
                      {emergencyData.ai_recommended_resources.map((resource, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-blue-600 font-bold mt-0.5">•</span>
                          <span className="text-gray-800">{resource}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Follow-up Resources */}
            {emergencyData.follow_up_resources && emergencyData.follow_up_resources.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <ExternalLink className="w-5 h-5 text-teal-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Additional Support</h3>
                </div>
                <Card className="bg-teal-50 border-teal-200">
                  <CardContent className="p-4">
                    <ul className="space-y-2">
                      {emergencyData.follow_up_resources.map((resource, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-teal-600 font-bold mt-0.5">→</span>
                          <span className="text-gray-800 text-sm">{resource}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              {isBlocking && (
                <Button
                  onClick={onClose}
                  className="flex-1 bg-gray-600 hover:bg-gray-700"
                >
                  I've Got Support
                </Button>
              )}
              <Button
                onClick={onAddContacts}
                variant="outline"
                className="flex-1"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Manage Contacts
              </Button>
            </div>
          </CardContent>
        </ScrollArea>
      </Card>
    </div>
  );
};

export default EmergencyPopup;
