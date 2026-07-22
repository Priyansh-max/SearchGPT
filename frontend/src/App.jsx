import React, { useEffect, useRef, useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';
import LandingPage from './components/LandingPage';
import ChatInterface from './components/ChatInterface';
import AdminDashboard from './components/AdminDashboard';
import SignIn from './components/SignIn';
import AuthCallback from './components/AuthCallback';
import Onboarding from './components/Onboarding';
import ToastStack from './components/ToastStack';
import { useToasts } from './hooks/useToasts';
import { runPlaygroundQuery, formatPlaygroundResponse } from './services/api';

const DEVELOPER_SOON_MESSAGE = 'Developer dashboard and API keys are coming soon.';

const DeveloperComingSoonRoute = ({ showToast }) => {
  const navigate = useNavigate();

  useEffect(() => {
    showToast(DEVELOPER_SOON_MESSAGE, 'info');
    navigate('/', { replace: true });
  }, [navigate, showToast]);

  return null;
};

function App() {
  const navigate = useNavigate();
  const { toasts, showToast, removeToast } = useToasts();

  // State management
  const [query, setQuery] = useState('');
  const [selectedTool, setSelectedTool] = useState('search');
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState("");
  const inFlightRef = useRef(false);
  
  // Mock user name - can be replaced with actual user info from auth system
  const userName = "SearchGPT";
  const handleDevelopersLocked = () => showToast(DEVELOPER_SOON_MESSAGE, 'info');
  
  // Handle initial search from landing page — go to playground then send
  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim() || inFlightRef.current) return;
    navigate('/c');
    sendMessage(query);
  };
  
  // Handle sending messages from chat page
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!query.trim() || inFlightRef.current) return;

    sendMessage(query);
  };
  
  // Handle key press in textarea
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        return;
      } else {
        e.preventDefault(); // prevent newline
        if (query.trim() && !inFlightRef.current) {
          sendMessage(query);
        }
      }
    }
  };
  
  
  // Common message sending logic
  const sendMessage = async (text) => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;

    const userMessage = {
      id: Date.now(),
      text,
      isUser: true,
      tool: selectedTool || 'search',
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Show typing indicator and set loading state
    setIsTyping(true);
    setIsLoading(true);
    setLoadingStartTime(Date.now());
    
    try {
      const tool = selectedTool || 'search';
      const loadingByTool = {
        search: 'Searching and ranking sources',
        scraper: 'Extracting clean page content',
        analyzer: 'Researching and synthesizing context',
        news: 'Finding recent coverage',
      };
      setLoadingMessage(loadingByTool[tool] || 'Running playground query');

      const response = await runPlaygroundQuery({ query: text, tool, synthesize: true, maxSources: 5 });
      const formatted = formatPlaygroundResponse(response);

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: formatted.text,
        isUser: false,
        sources: formatted.sources,
        images: formatted.images,
        meta: formatted.meta,
        raw: formatted.raw,
      }]);

    } catch (error) {
      console.error('API error:', error);
      
      const detail = error.message || 'Request failed';
      const isDemoBusy = detail.includes('Demo is at capacity');
      const politeError = isDemoBusy
        ? detail
        : `I could not complete that request. Please try again or select a different tool.\n\nError details: ${detail}`;

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: politeError,
        isUser: false,
        meta: isDemoBusy ? { mode_label: 'Demo busy', tier: 'demo' } : undefined,
      }]);
    } finally {
      // Hide typing indicator and loading state
      setIsTyping(false);
      setIsLoading(false);
      setLoadingStartTime(null);
      setLoadingMessage("");
      
      inFlightRef.current = false;

      // Clear the input
      setQuery('');
    }
  };
  
  // Reset chat (new chat) without reloading
  const handleResetChat = () => {
    setMessages([]);
    setQuery('');
    setIsTyping(false);
    setIsLoading(false);
    setLoadingStartTime(null);
    setLoadingMessage('');
    inFlightRef.current = false;
  };



  return (
    <div className="min-h-screen">
      <ToastStack toasts={toasts} onDismiss={removeToast} />
      <Routes>
        <Route
          path="/"
          element={
            <LandingPage
              query={query}
              setQuery={setQuery}
              handleSearch={handleSearch}
              handleKeyPress={handleKeyPress}
              selectedTool={selectedTool}
              setSelectedTool={setSelectedTool}
              userName={userName}
            />
          }
        />
        <Route
          path="/c"
          element={
            <ChatInterface
              messages={messages}
              isTyping={isTyping}
              isLoading={isLoading}
              loadingStartTime={loadingStartTime}
              loadingMessage={loadingMessage}
              query={query}
              setQuery={setQuery}
              handleSendMessage={handleSendMessage}
              handleKeyPress={handleKeyPress}
              selectedTool={selectedTool}
              setSelectedTool={setSelectedTool}
              onResetChat={handleResetChat}
              onDevelopersLocked={handleDevelopersLocked}
            />
          }
        />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/developers" element={<DeveloperComingSoonRoute showToast={showToast} />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/keys" element={<DeveloperComingSoonRoute showToast={showToast} />} />
      </Routes>
    </div>
  );
}

export default App;
