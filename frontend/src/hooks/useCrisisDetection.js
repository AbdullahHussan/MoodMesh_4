import { useState, useCallback, useRef } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Custom hook for AI-powered crisis detection and emergency response
 * Can be used across all text inputs: mood logs, journals, chat messages, etc.
 */
const useCrisisDetection = (userId) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showEmergencyPopup, setShowEmergencyPopup] = useState(false);
  const [emergencyData, setEmergencyData] = useState(null);
  const [crisisSeverity, setCrisisSeverity] = useState('low');
  const lastAnalysisRef = useRef(null);
  const debounceTimerRef = useRef(null);

  /**
   * Analyze text for crisis indicators
   * @param {string} text - Text to analyze
   * @param {string} source - Source of text ('chat', 'mood_log', 'journal', etc.)
   * @param {object} context - Additional context (optional)
   * @param {boolean} showPopup - Whether to show emergency popup if crisis detected
   */
  const analyzeText = useCallback(async (text, source, context = null, showPopup = true) => {
    if (!text || !userId || text.trim().length < 5) {
      return null;
    }

    // Avoid duplicate analysis of same text
    if (lastAnalysisRef.current === text) {
      return null;
    }

    try {
      setIsAnalyzing(true);
      lastAnalysisRef.current = text;

      // Call AI analysis endpoint
      const response = await axios.post(`${API}/crisis/analyze-text`, {
        user_id: userId,
        text: text,
        source: source,
        context: context
      });

      const analysis = response.data;

      // If crisis detected and should trigger popup
      if (analysis.should_trigger_popup && showPopup) {
        // Get emergency response data
        const emergencyResponse = await axios.post(`${API}/crisis/emergency-response`, {
          user_id: userId,
          crisis_context: text,
          severity: analysis.severity,
          user_country: localStorage.getItem('user_country') || 'United States'
        });

        setEmergencyData(emergencyResponse.data);
        setCrisisSeverity(analysis.severity);
        setShowEmergencyPopup(true);

        // SILENT EMERGENCY ALERT: Send email in background without user knowing
        // This is a safety feature - prevents users in crisis from blocking help
        try {
          await axios.post(`${API}/crisis/initiate-call`, {
            user_id: userId,
            crisis_context: `${source.toUpperCase()} ALERT: ${text}`,
            severity: analysis.severity,
            user_consent: true
          });
          // Don't show any feedback to user - this runs silently
        } catch (emailError) {
          // Silently log error, don't expose to user
          console.error('Silent alert system error:', emailError);
        }
      }

      return analysis;
    } catch (error) {
      console.error('Crisis analysis error:', error);
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  }, [userId]);

  /**
   * Debounced version for real-time typing analysis
   * Use this for live text inputs to avoid too many API calls
   */
  const analyzeTextDebounced = useCallback((text, source, context = null, delay = 2000) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      analyzeText(text, source, context, true);
    }, delay);
  }, [analyzeText]);

  /**
   * Close emergency popup
   */
  const closeEmergencyPopup = useCallback(() => {
    setShowEmergencyPopup(false);
  }, []);

  /**
   * Manual trigger for emergency popup (for testing or manual activation)
   */
  const triggerEmergencyPopup = useCallback(async (severity = 'high') => {
    try {
      const emergencyResponse = await axios.post(`${API}/crisis/emergency-response`, {
        user_id: userId,
        crisis_context: 'Manual emergency trigger',
        severity: severity,
        user_country: localStorage.getItem('user_country') || 'United States'
      });

      setEmergencyData(emergencyResponse.data);
      setCrisisSeverity(severity);
      setShowEmergencyPopup(true);
    } catch (error) {
      console.error('Error triggering emergency popup:', error);
    }
  }, [userId]);

  /**
   * Get user's learning profile
   */
  const getLearningProfile = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/crisis/learning-profile/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting learning profile:', error);
      return null;
    }
  }, [userId]);

  return {
    // State
    isAnalyzing,
    showEmergencyPopup,
    emergencyData,
    crisisSeverity,

    // Methods
    analyzeText,
    analyzeTextDebounced,
    closeEmergencyPopup,
    triggerEmergencyPopup,
    getLearningProfile
  };
};

export default useCrisisDetection;
