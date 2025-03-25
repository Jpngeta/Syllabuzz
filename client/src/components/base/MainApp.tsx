import React, { useState, useEffect } from 'react';
import { 
  BookOpen,
  Menu,
  X 
} from 'lucide-react';
import Header from '../layout/Header';
import Sidebar from '../layout/Sidebar';
import MainContent from './MainContent';
import Footer from '../layout/Footer';
import { useAuth } from '../auth/AuthProvider';
import { fetchModules, fetchArticles, fetchTrending } from '../../services/apiService';

// Types
import { Module, Article, TabType } from './types';

// Theme colors
export const darkColors = {
  primary: '#FF6B6B',         // Coral Red (Energetic, attention-grabbing)
  secondary: '#4ECDC4',       // Turquoise (Fresh, modern)
  tertiary: '#FFD166',        // Golden Yellow (Warm, inviting)
  quaternary: '#6A0572',      // Deep Purple (Rich contrast)
  background: '#FFFFFF',      // Crisp White (Clean background)
  surface: '#F7F9FC',         // Ice Blue (Subtle surface variation)
  elevatedSurface: '#FFFFFF', // White for elevated surfaces
  error: '#FF5252',           // Bright Red (Error)
  warning: '#FFB100',         // Golden Orange (Warning)
  success: '#06D6A0',         // Mint Green (Success)
  textPrimary: '#2D3748',     // Deep Blue-Gray (Main text)
  textSecondary: '#4A5568',   // Medium Gray (Secondary text)
  textMuted: '#718096',       // Soft Gray (Hints, placeholders)
  border: '#E2E8F0',          // Soft Gray border
  cardHover: '#EDF2F7',       // Lightest Blue on hover
  gradientOverlay: 'rgba(74, 85, 104, 0.05)', // Subtle overlay
  shadow: 'rgba(0, 0, 0, 0.1)',               // Light shadow
  focus: '#3182CE',           // Blue Focus (Accessibility)
  accent1: '#9B5DE5',         // Lavender (Playful accent)
  accent2: '#00BBF9',         // Sky Blue (Fresh accent)
};

const App: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<TabType>('home');
  const [modules, setModules] = useState<Module[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [trendingArticles, setTrendingArticles] = useState<Article[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Article[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [currentModule, setCurrentModule] = useState<Module | null>(null);
  const [moduleRecommendations, setModuleRecommendations] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  
  const { user } = useAuth();
  
  // Fetch initial data
  useEffect(() => {
    loadInitialData();
    setupCustomStyles();
    
    return () => {
      // Cleanup custom styles
      const styleElement = document.getElementById('syllabuzz-custom-styles');
      if (styleElement) {
        document.head.removeChild(styleElement);
      }
    };
  }, []);
  
  const loadInitialData = async () => {
    try {
      // Fetch modules
      const modulesData = await fetchModules();
      setModules(modulesData);
      
      // Fetch articles
      const articlesData = await fetchArticles();
      setArticles(articlesData);
      
      // Fetch trending
      const trendingData = await fetchTrending();
      setTrendingArticles(trendingData);
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading initial data:', error);
      setIsLoading(false);
    }
  };
  
  const setupCustomStyles = () => {
    const style = document.createElement('style');
    style.id = 'syllabuzz-custom-styles';
    style.innerHTML = `
      @import url('https://fonts.googleapis.com/css2?family=DynaPuff:wght@400;600;800&display=swap');
      @import url('https://fonts.googleapis.com/css2?family=Righteous&display=swap');
      
      /* Apply custom fonts */
      body {
        font-family: 'DynaPuff', sans-serif;
        background-color: ${darkColors.background};
        color: ${darkColors.textPrimary};
      }

      h1, h2, h3, .title-font {
        font-family: 'DynaPuff', sans-serif;
        font-weight: 700;
      }
      
      /* Custom animations */
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      
      @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
      }
      
      @keyframes glowPulse {
        0% { box-shadow: 0 0 5px ${darkColors.primary}80; }
        50% { box-shadow: 0 0 15px ${darkColors.primary}; }
        100% { box-shadow: 0 0 5px ${darkColors.primary}80; }
      }
      
      .animate-fadeIn {
        animation: fadeIn 0.5s ease forwards;
      }
      
      .animate-slideIn {
        animation: slideIn 0.5s ease forwards;
      }
      
      .hover-scale {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
      }
      
      .hover-scale:hover {
        transform: scale(1.03);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
      }
      
      .pulse {
        animation: pulse 2s infinite;
      }
      
      .glow-effect {
        animation: glowPulse 2s infinite;
      }
    `;
    document.head.appendChild(style);
    
    // Force dark mode for whole app
    document.documentElement.classList.add('dark');
    document.body.style.backgroundColor = darkColors.background;
  };
  
  // Search articles
  const handleSearch = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      setSearchResults(data.articles);
      setActiveTab('search');
    } catch (error) {
      console.error('Error searching articles:', error);
    } finally {
      setIsSearching(false);
    }
  };
  
  // Load module details
  const loadModuleDetails = async (moduleId: string): Promise<void> => {
    try {
      setIsLoading(true);
      
      // Fetch module details
      const moduleResponse = await fetch(`/api/modules/${moduleId}`);
      const moduleData = await moduleResponse.json();
      setCurrentModule(moduleData.module);
      
      // Fetch module recommendations
      const recommendationsResponse = await fetch(`/api/modules/${moduleId}/recommendations`);
      const recommendationsData = await recommendationsResponse.json();
      setModuleRecommendations(recommendationsData.recommendations);
      
      setActiveTab('module');
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading module details:', error);
      setIsLoading(false);
    }
  };
  
  return (
    <div className="flex flex-col min-h-screen" style={{ backgroundColor: darkColors.background }}>
      <Header 
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        handleSearch={handleSearch}
        isMenuOpen={isMenuOpen}
        setIsMenuOpen={setIsMenuOpen}
        user={user}
        darkColors={darkColors}
      />
      
      <main className="flex-1 container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          <Sidebar 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            modules={modules}
            loadModuleDetails={loadModuleDetails}
            isMenuOpen={isMenuOpen}
            setIsMenuOpen={setIsMenuOpen}
            fetchTrending={fetchTrending}
            user={user}
            darkColors={darkColors}
          />
          
          <MainContent 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            modules={modules}
            articles={articles}
            trendingArticles={trendingArticles}
            searchQuery={searchQuery}
            searchResults={searchResults}
            isSearching={isSearching}
            currentModule={currentModule}
            moduleRecommendations={moduleRecommendations}
            isLoading={isLoading}
            loadModuleDetails={loadModuleDetails}
            darkColors={darkColors}
          />
        </div>
      </main>
      
      <Footer darkColors={darkColors} />
    </div>
  );
};

export default App;