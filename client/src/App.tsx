import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  BookmarkPlus, 
  ChevronRight, 
  Code, 
  FileText, 
  Newspaper, 
  Search, 
  Star, 
  TrendingUp, 
  User,
  Menu,
  X,
  Calendar,
  Clock,
  ThumbsUp,
  ExternalLink,
  Home,
  Sparkles
} from 'lucide-react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Button 
} from '@/components/ui/button';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Define types for our data models
interface Module {
  _id: string;
  name: string;
  code: string;
  description: string;
  keywords?: string[];
  vector_embedding?: number[];
  created_at?: string;
  updated_at?: string;
}

interface Article {
  _id: string;
  title: string;
  description?: string;
  content?: string;
  url: string;
  image_url?: string;
  source_name: string;
  published_at: string;
  updated_at?: string;
  type: 'news' | 'academic';
  categories?: string[];
  authors?: string[];
  pdf_url?: string;
  arxiv_id?: string;
  relevance_score?: number;
  vector_embedding?: number[];
}

interface User {
  id: string;
  name: string;
  email: string;
  modules: string[];
}

type TabType = 'home' | 'modules' | 'articles' | 'trending' | 'search' | 'module';
type InteractionType = 'view' | 'like' | 'bookmark';

// Props interface for ArticleCard component
interface ArticleCardProps {
  article: Article;
  moduleId?: string;
}

// Props interface for ModuleCard component
interface ModuleCardProps {
  module: Module;
  onClick: (moduleId: string) => void;
}

// Animation component for transitions
const FadeIn = ({ children }) => {
  return (
    <div 
      className="animate-fadeIn opacity-0" 
      style={{ 
        animation: 'fadeIn 0.5s ease forwards',
      }}
    >
      {children}
    </div>
  );
};

// Enhanced version of the App component with dark mode and fun font
const App: React.FC = () => {
  // State management with TypeScript types
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
  const [user, setUser] = useState<User | null>(null);
  
  // Dark mode theme colors
  const darkColors =  {
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

  
  
  
  // Fetch initial data
  useEffect(() => {
    fetchModules();
    fetchArticles();
    fetchTrending();
    
    // Mock user for demo
    setUser({
      id: '1234',
      name: 'John Doe',
      email: 'john@example.com',
      modules: []
    });
    
    // Add custom CSS for animations and custom font
    const style = document.createElement('style');
    style.innerHTML = `

      @import url('https://fonts.googleapis.com/css2?family=DynaPuff:wght@400;600;800&display=swap');
       @import url('https://fonts.googleapis.com/css2?family=Kablammo:wght@400;600;800&display=swap');
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
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);
  
  // Fetch modules
  const fetchModules = async (): Promise<void> => {
    try {
      const response = await fetch('/api/modules');
      const data = await response.json();
      setModules(data.modules);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching modules:', error);
      setIsLoading(false);
    }
  };
  
  // Fetch articles
  const fetchArticles = async (category: string | null = null): Promise<void> => {
    try {
      let url = '/api/articles';
      if (category) {
        url += `?category=${category}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      setArticles(data.articles);
    } catch (error) {
      console.error('Error fetching articles:', error);
    }
  };
  
  // Fetch trending articles
  const fetchTrending = async (): Promise<void> => {
    try {
      const response = await fetch('/api/trending');
      const data = await response.json();
      setTrendingArticles(data.trending);
    } catch (error) {
      console.error('Error fetching trending articles:', error);
    }
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
  
  // Record user interaction with an article
  const recordInteraction = async (
    articleId: string, 
    type: InteractionType = 'view', 
    moduleId: string | null = null
  ): Promise<void> => {
    if (!user) return;
    
    try {
      await fetch('/api/interaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: user.id,
          article_id: articleId,
          module_id: moduleId,
          type: type
        })
      });
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  };
  
  // Format date
  const formatDate = (dateString: string): string => {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };
  
  // Article Card Component with enhanced design and image support
  const ArticleCard: React.FC<ArticleCardProps> = ({ article, moduleId }) => {
    const recordView = (): void => {
      recordInteraction(article._id, 'view', moduleId || null);
      window.open(article.url, '_blank');
    };
    
    const recordLike = (e: React.MouseEvent): void => {
      e.stopPropagation();
      recordInteraction(article._id, 'like', moduleId || null);
    };
    
    const recordBookmark = (e: React.MouseEvent): void => {
      e.stopPropagation();
      recordInteraction(article._id, 'bookmark', moduleId || null);
    };
    
    const hasImage = article.image_url && article.image_url.trim() !== '';
    
    return (
      <div className="h-full transition-all hover-scale">
        <Card 
          className="h-full border hover:shadow-lg cursor-pointer transition-all duration-300" 
          onClick={recordView}
          style={{ 
            backgroundColor: darkColors.surface, 
            borderColor: article.type === 'academic' ? darkColors.primary : darkColors.secondary,
            borderWidth: '2px'
          }}
        >
          {hasImage && (
            <div className="w-full h-40 overflow-hidden">
              <img 
                src={article.image_url || '/api/placeholder/400/320'} 
                alt={article.title}
                className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                onError={(e) => {
                  e.currentTarget.src = '/api/placeholder/400/320';
                }}
              />
            </div>
          )}
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <Badge 
                variant={article.type === 'academic' ? 'secondary' : 'default'} 
                className="mb-2"
                style={{ 
                  backgroundColor: article.type === 'academic' ? darkColors.primary : darkColors.secondary,
                  color: darkColors.textPrimary
                }}
              >
                {article.type === 'academic' ? 'Academic' : 'News'}
              </Badge>
              {article.relevance_score && (
                <Badge 
                  variant="outline" 
                  className="flex items-center gap-1"
                  style={{ borderColor: darkColors.tertiary, color: darkColors.tertiary }}
                >
                  <Star className="w-3 h-3" /> 
                  {(article.relevance_score * 100).toFixed(0)}%
                </Badge>
              )}
            </div>
            <CardTitle className="text-lg line-clamp-2 font-bold title-font" style={{ color: darkColors.textPrimary }}>
              {article.title}
            </CardTitle>
            <CardDescription className="flex items-center gap-1 text-xs" style={{ color: darkColors.textSecondary }}>
              <Calendar className="w-3 h-3" /> {formatDate(article.published_at)}
              <span className="mx-1">•</span>
              <span>{article.source_name}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm line-clamp-3" style={{ color: darkColors.textSecondary }}>
              {article.description || 'No description available.'}
            </p>
          </CardContent>
          <CardFooter className="flex justify-between pt-2">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={recordLike}
              className="hover:bg-opacity-20 transition-colors"
              style={{ color: darkColors.quaternary }}
            >
              <ThumbsUp className="w-4 h-4 mr-1" /> Like
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={recordBookmark}
              className="hover:bg-opacity-20 transition-colors"
              style={{ color: darkColors.primary }}
            >
              <BookmarkPlus className="w-4 h-4 mr-1" /> Save
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              asChild
              className="hover:bg-opacity-20 transition-colors"
              style={{ color: darkColors.secondary }}
            >
              <a href={article.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4 mr-1" /> View
              </a>
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  };

  // Module Card Component with enhanced design
  const ModuleCard: React.FC<ModuleCardProps> = ({ module, onClick }) => (
    <div className="h-full transition-all hover-scale">
      <Card 
        className="h-full border hover:shadow-lg cursor-pointer transition-all duration-300" 
        onClick={() => onClick(module._id)}
        style={{ 
          backgroundColor: darkColors.surface, 
          borderColor: darkColors.primary, 
          borderLeftWidth: '4px' 
        }}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-bold title-font" style={{ color: darkColors.primary }}>
            <Code className="w-5 h-5" />
            {module.name } - {module.code}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm line-clamp-3" style={{ color: darkColors.textSecondary }}>{module.description}</p>
        </CardContent>
        <CardFooter className="flex justify-between">
          <div className="flex items-center text-sm" style={{ color: darkColors.textSecondary }}>
            <FileText className="w-4 h-4 mr-1" />
            <span>{module.keywords?.length || 0} keywords</span>
          </div>
          <Button 
            variant="ghost" 
            size="sm"
            className="hover:bg-opacity-20"
            style={{ color: darkColors.primary }}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
  
  return (
    <div className="flex flex-col min-h-screen" style={{ backgroundColor: darkColors.background }}>
      {/* Header */}
      <header 
        className="border-b sticky top-0 z-10" 
        style={{ 
          backgroundColor: darkColors.surface,
          borderColor: darkColors.border,
          boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
        }}
      >
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2 animate-slideIn">
            <BookOpen className="w-6 h-6" style={{ color: darkColors.primary }} />
            <h1 className="text-xl font-bold title-font" style={{ color: darkColors.primary }}>CS Content Hub</h1>
          </div>
          
          <div className="hidden md:block w-1/3">
            <form onSubmit={handleSearch} className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" style={{ color: darkColors.textSecondary }} />
              <Input
                type="text"
                placeholder="Search articles and papers..."
                className="w-full pl-10 border-2 focus:ring-2 focus:border-transparent transition-all"
                style={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  borderColor: darkColors.primary,
                  borderRadius: '0.5rem',
                  color: darkColors.textPrimary
                }}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>
          </div>
          
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="icon"
              className="md:hidden"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              style={{ color: darkColors.textPrimary }}
            >
              {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
            
            <div className="hidden md:flex items-center gap-2">
              <Avatar className="border-2" style={{ borderColor: darkColors.primary }}>
                <AvatarFallback style={{ backgroundColor: darkColors.primary, color: darkColors.textPrimary }}>
                  {user?.name?.charAt(0) || 'U'}
                </AvatarFallback>
              </Avatar>
              <span className="font-medium" style={{ color: darkColors.textPrimary }}>{user?.name || 'Guest'}</span>
            </div>
          </div>
        </div>
        
        {/* Mobile Search */}
        <div className="md:hidden px-4 pb-3">
          <form onSubmit={handleSearch} className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" style={{ color: darkColors.textSecondary }} />
            <Input
              type="text"
              placeholder="Search articles and papers..."
              className="w-full pl-10 border-2 focus:ring-2 focus:border-transparent transition-all"
              style={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderColor: darkColors.primary,
                borderRadius: '0.5rem',
                color: darkColors.textPrimary
              }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
        </div>
        
        {/* Mobile Menu */}
        {isMenuOpen && (
          <div 
            className="md:hidden border-t p-4 flex flex-col gap-2 animate-fadeIn" 
            style={{ 
              backgroundColor: darkColors.surface,
              borderColor: darkColors.border 
            }}
          >
            <Button 
              variant="ghost" 
              className="justify-start hover:bg-opacity-20 transition-colors" 
              onClick={() => {setActiveTab('home'); setIsMenuOpen(false);}}
              style={{ color: activeTab === 'home' ? darkColors.primary : darkColors.textPrimary }}
            >
              <Home className="w-4 h-4 mr-2" /> Home
            </Button>
            <Button 
              variant="ghost" 
              className="justify-start hover:bg-opacity-20 transition-colors" 
              onClick={() => {setActiveTab('modules'); setIsMenuOpen(false);}}
              style={{ color: activeTab === 'modules' ? darkColors.primary : darkColors.textPrimary }}
            >
              <Code className="w-4 h-4 mr-2" /> Modules
            </Button>
            <Button 
              variant="ghost" 
              className="justify-start hover:bg-opacity-20 transition-colors" 
              onClick={() => {setActiveTab('articles'); setIsMenuOpen(false);}}
              style={{ color: activeTab === 'articles' ? darkColors.primary : darkColors.textPrimary }}
            >
              <Newspaper className="w-4 h-4 mr-2" /> Articles
            </Button>
            <Button 
              variant="ghost" 
              className="justify-start hover:bg-opacity-20 transition-colors" 
              onClick={() => {setActiveTab('trending'); setIsMenuOpen(false);}}
              style={{ color: activeTab === 'trending' ? darkColors.primary : darkColors.textPrimary }}
            >
              <TrendingUp className="w-4 h-4 mr-2" /> Trending
            </Button>
            <Separator className="my-2" style={{ backgroundColor: darkColors.border }} />
            <div className="flex items-center gap-2 p-2">
              <Avatar className="border-2" style={{ borderColor: darkColors.primary }}>
                <AvatarFallback style={{ backgroundColor: darkColors.primary, color: darkColors.textPrimary }}>
                  {user?.name?.charAt(0) || 'U'}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium" style={{ color: darkColors.textPrimary }}>{user?.name || 'Guest'}</p>
                <p className="text-xs" style={{ color: darkColors.textSecondary }}>{user?.email || ''}</p>
              </div>
            </div>
          </div>
        )}
      </header>
      
      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar Navigation (Desktop) */}
          <aside className="hidden md:block w-64 space-y-2 animate-slideIn">
            <Button 
              variant={activeTab === 'home' ? 'default' : 'ghost'} 
              className="w-full justify-start transition-colors font-medium"
              onClick={() => setActiveTab('home')}
              style={{ 
                backgroundColor: activeTab === 'home' ? darkColors.primary : 'transparent',
                color: activeTab === 'home' ? darkColors.textPrimary : darkColors.textPrimary
              }}
            >
              <Home className="w-4 h-4 mr-2" /> Home
            </Button>
            <Button 
              variant={activeTab === 'modules' ? 'default' : 'ghost'} 
              className="w-full justify-start transition-colors font-medium"
              onClick={() => setActiveTab('modules')}
              style={{ 
                backgroundColor: activeTab === 'modules' ? darkColors.primary : 'transparent',
                color: activeTab === 'modules' ? darkColors.textPrimary : darkColors.textPrimary
              }}
            >
              <Code className="w-4 h-4 mr-2" /> Modules
            </Button>
            <Button 
              variant={activeTab === 'articles' ? 'default' : 'ghost'} 
              className="w-full justify-start transition-colors font-medium"
              onClick={() => setActiveTab('articles')}
              style={{ 
                backgroundColor: activeTab === 'articles' ? darkColors.primary : 'transparent',
                color: activeTab === 'articles' ? darkColors.textPrimary : darkColors.textPrimary
              }}
            >
              <Newspaper className="w-4 h-4 mr-2" /> Articles
            </Button>
            <Button 
              variant={activeTab === 'trending' ? 'default' : 'ghost'} 
              className="w-full justify-start transition-colors font-medium"
              onClick={() => {
                setActiveTab('trending');
                fetchTrending();
              }}
              style={{ 
                backgroundColor: activeTab === 'trending' ? darkColors.primary : 'transparent',
                color: activeTab === 'trending' ? darkColors.textPrimary : darkColors.textPrimary
              }}
            >
              <TrendingUp className="w-4 h-4 mr-2" /> Trending
            </Button>
            
            <Separator className="my-4" style={{ backgroundColor: darkColors.border }} />
            
            <div 
              className="p-4 rounded-lg border-2" 
              style={{ 
                borderColor: darkColors.primary, 
                backgroundColor: darkColors.surface,
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.2)'
              }}
            >
              <h3 className="font-bold mb-2 title-font" style={{ color: darkColors.primary }}>Modules</h3>
              <div className="space-y-1 overflow-y-auto" style={{ maxHeight: '20rem' }}>
                {modules.map((module, index) => (
                  <Button 
                    key={module._id} 
                    variant="ghost" 
                    className="w-full justify-start transition-colors font-medium"
                    onClick={() => loadModuleDetails(module._id)}
                    style={{ color: darkColors.textPrimary }}
                  >
                    {module.code}
                  </Button>
                ))}               
              </div>
            </div>
          </aside>
          
          {/* Main Content Area */}
          <div className="flex-1">
            {/* Home Tab */}
            {activeTab === 'home' && (
              <FadeIn>
                <div className="space-y-8">
                  <section>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.primary }}>
                        Welcome to CS Content Hub
                      </h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="hover-scale transition-all duration-300">
                        <Card 
                          className="bg-gradient-to-br text-white h-full glow-effect" 
                          style={{ 
                            background: `linear-gradient(135deg, ${darkColors.primary}CC, ${darkColors.quaternary})`,
                          }}
                        >
                          <CardHeader>
                            <CardTitle className="flex items-center title-font">
                              <Code className="w-5 h-5 mr-2" /> Explore CS Modules
                            </CardTitle>
                            <CardDescription className="text-white/90">
                              Discover computer science topics
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <p>Browse our collection of CS modules to find learning resources tailored to your interests.</p>
                          </CardContent>
                          <CardFooter>
                            <Button 
                              variant="secondary" 
                              onClick={() => setActiveTab('modules')}
                              className="font-medium"
                              style={{ backgroundColor: 'white', color: darkColors.primary }}
                            >
                              Browse Modules
                            </Button>
                          </CardFooter>
                        </Card>
                      </div>
                      
                      <div className="hover-scale transition-all duration-300">
                        <Card 
                          className="bg-gradient-to-br text-white h-full glow-effect"
                          style={{ 
                            background: `linear-gradient(135deg, ${darkColors.secondary}CC, ${darkColors.primary})`,
                          }}
                        >
                          <CardHeader>
                            <CardTitle className="flex items-center title-font">
                              <Newspaper className="w-5 h-5 mr-2" /> Latest Articles
                            </CardTitle>
                            <CardDescription className="text-white/90">
                              Stay updated with CS news
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <p>Get the latest news, articles, and academic papers in computer science and technology.</p>
                          </CardContent>
                          <CardFooter>
                            <Button 
                              variant="secondary" 
                              onClick={() => setActiveTab('articles')}
                              className="font-medium"
                              style={{ backgroundColor: 'white', color: darkColors.secondary }}
                            >
                              Read Articles
                            </Button>
                          </CardFooter>
                        </Card>
                      </div>
                      
                      <div className="hover-scale transition-all duration-300">
                        <Card 
                          className="bg-gradient-to-br text-white h-full glow-effect"
                          style={{ 
                            background: `linear-gradient(135deg, ${darkColors.tertiary}CC, ${darkColors.quaternary})`,
                          }}
                        >
                          <CardHeader>
                            <CardTitle className="flex items-center title-font">
                              <TrendingUp className="w-5 h-5 mr-2" /> Trending Now
                            </CardTitle>
                            <CardDescription className="text-white/90">
                              What's popular in CS
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <p>Discover the most popular and trending topics in the computer science community.</p>
                          </CardContent>
                          <CardFooter>
                            <Button 
                              variant="secondary" 
                              onClick={() => setActiveTab('trending')}
                              className="font-medium"
                              style={{ backgroundColor: 'white', color: darkColors.tertiary }}
                            >
                              View Trending
                            </Button>
                          </CardFooter>
                        </Card>
                      </div>
                    </div>
                  </section>
                  
                  <section>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-bold title-font" style={{ color: darkColors.secondary }}>Recent Articles</h2>
                      <Button 
                        variant="link" 
                        onClick={() => setActiveTab('articles')}
                        style={{ color: darkColors.secondary }}
                      >
                        View All →
                      </Button>
                    </div>
                    {isLoading ? (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {[...Array(3)].map((_, i) => (
                          <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                            <CardHeader>
                              <Skeleton className="h-4 w-16 mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                              <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                              <Skeleton className="h-4 w-28" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            </CardHeader>
                            <CardContent>
                              <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            </CardContent>
                            <CardFooter>
                              <Skeleton className="h-9 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            </CardFooter>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {articles.slice(0, 6).map((article, index) => (
                          <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                            <ArticleCard article={article} />
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                  
                  <section>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-bold title-font" style={{ color: darkColors.primary }}>Featured Modules</h2>
                      <Button 
                        variant="link" 
                        onClick={() => setActiveTab('modules')}
                        style={{ color: darkColors.primary }}
                      >
                        View All →
                      </Button>
                    </div>
                    {isLoading ? (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {[...Array(3)].map((_, i) => (
                          <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                            <CardHeader>
                              <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            </CardHeader>
                            <CardContent>
                              <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            </CardContent>
                            <CardFooter>
                              <Skeleton className="h-4 w-24" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            </CardFooter>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {modules.slice(0, 6).map((module, index) => (
                          <div key={module._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                            <ModuleCard 
                              module={module} 
                              onClick={loadModuleDetails} 
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                </div>
              </FadeIn>
            )}
            
            {/* Modules Tab */}
            {activeTab === 'modules' && (
              <FadeIn>
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.primary }}>CS Modules</h2>
                  </div>
                  
                  {isLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[...Array(6)].map((_, i) => (
                        <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                          <CardHeader>
                            <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardHeader>
                          <CardContent>
                            <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardContent>
                          <CardFooter>
                            <Skeleton className="h-4 w-24" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardFooter>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {modules.map((module, index) => (
                        <div key={module._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                          <ModuleCard 
                            module={module} 
                            onClick={loadModuleDetails} 
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </FadeIn>
            )}
            
            {/* Articles Tab */}
            {activeTab === 'articles' && (
              <FadeIn>
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.secondary }}>Articles & Papers</h2>
                    
                    <Tabs defaultValue="all" className="w-64">
                      <TabsList className="w-full" style={{ backgroundColor: `${darkColors.secondary}33` }}>
                        <TabsTrigger 
                          value="all" 
                          onClick={() => fetchArticles()}
                          className="data-[state=active]:text-white transition-all"
                          style={{ 
                            backgroundColor: "transparent",
                            "--tw-bg-opacity": "1",
                            "--secondary": darkColors.secondary,
                            "--tw-text-opacity": "1",
                            "--tw-white": darkColors.textPrimary,
                            "[data-state=active]:backgroundColor": darkColors.secondary
                          }}
                        >
                          All
                        </TabsTrigger>
                        <TabsTrigger 
                          value="news" 
                          onClick={() => fetchArticles('technology')}
                          className="data-[state=active]:text-white transition-all"
                          style={{ 
                            backgroundColor: "transparent",
                            "--tw-bg-opacity": "1",
                            "--secondary": darkColors.secondary,
                            "--tw-text-opacity": "1",
                            "--tw-white": darkColors.textPrimary,
                            "[data-state=active]:backgroundColor": darkColors.secondary
                          }}
                        >
                          News
                        </TabsTrigger>
                        <TabsTrigger 
                          value="academic" 
                          onClick={() => fetchArticles('academic')}
                          className="data-[state=active]:text-white transition-all"
                          style={{ 
                            backgroundColor: "transparent",
                            "--tw-bg-opacity": "1",
                            "--secondary": darkColors.secondary,
                            "--tw-text-opacity": "1",
                            "--tw-white": darkColors.textPrimary,
                            "[data-state=active]:backgroundColor": darkColors.secondary
                          }}
                        >
                          Academic
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>
                  
                  {articles.length === 0 ? (
                    <Alert 
                      className="border-2 animate-pulse" 
                      style={{ 
                        backgroundColor: darkColors.surface, 
                        borderColor: darkColors.secondary,
                        color: darkColors.textPrimary
                      }}
                    >
                      <AlertTitle className="font-bold title-font">No articles found</AlertTitle>
                      <AlertDescription>
                        Try a different category or check back later for new content.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {articles.map((article, index) => (
                        <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                          <ArticleCard article={article} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </FadeIn>
            )}
            
            {/* Trending Tab */}
            {activeTab === 'trending' && (
              <FadeIn>
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold flex items-center gap-2 title-font" style={{ color: darkColors.tertiary }}>
                      <Sparkles className="w-6 h-6" /> Trending Content
                    </h2>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={fetchTrending}
                      className="border-2 font-medium transition-all"
                      style={{ borderColor: darkColors.tertiary, color: darkColors.tertiary }}
                    >
                      Refresh
                    </Button>
                  </div>
                  
                  {trendingArticles.length === 0 ? (
                    <Alert 
                      className="border-2 animate-pulse" 
                      style={{ 
                        backgroundColor: darkColors.surface, 
                        borderColor: darkColors.tertiary,
                        color: darkColors.textPrimary
                      }}
                    >
                      <AlertTitle className="font-bold title-font">No trending articles yet</AlertTitle>
                      <AlertDescription>
                        Check back later for trending content based on user interactions.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {trendingArticles.map((article, index) => (
                        <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                          <ArticleCard article={article} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </FadeIn>
            )}
            
            {/* Search Results Tab */}
            {activeTab === 'search' && (
              <FadeIn>
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.tertiary }}>Search Results</h2>
                    <p style={{ color: darkColors.textSecondary }} className="flex items-center">
                      <Search className="w-4 h-4 mr-1" />
                      Found <span className="font-bold mx-1">{searchResults.length}</span> results for "{searchQuery}"
                    </p>
                  </div>
                  
                  {isSearching ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[...Array(6)].map((_, i) => (
                        <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                          <CardHeader>
                            <Skeleton className="h-4 w-16 mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                            <Skeleton className="h-4 w-28" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardHeader>
                          <CardContent>
                            <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardContent>
                          <CardFooter>
                            <Skeleton className="h-9 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardFooter>
                        </Card>
                      ))}
                    </div>
                  ) : searchResults.length === 0 ? (
                    <Alert 
                      className="border-2 animate-pulse" 
                      style={{ 
                        backgroundColor: darkColors.surface, 
                        borderColor: darkColors.tertiary,
                        color: darkColors.textPrimary
                      }}
                    >
                      <AlertTitle className="font-bold title-font">No results found</AlertTitle>
                      <AlertDescription>
                        Try a different search term or browse our content categories.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {searchResults.map((article, index) => (
                        <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                          <ArticleCard article={article} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </FadeIn>
            )}
            
            {/* Module Detail Tab */}
            {activeTab === 'module' && currentModule && (
              <FadeIn>
                <div className="space-y-6">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="mb-4 border-2 transition-all flex items-center gap-1"
                    onClick={() => setActiveTab('modules')}
                    style={{ borderColor: darkColors.primary, color: darkColors.primary }}
                  >
                    ← Back to Modules
                  </Button>
                  
                  <div 
                    className="rounded-lg border-2 p-6 transition-all hover:shadow-md" 
                    style={{ 
                      backgroundColor: darkColors.surface,
                      borderColor: darkColors.primary, 
                      borderLeftWidth: '6px',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.2)'
                    }}
                  >
                    <h1 className="text-2xl font-bold mb-2 title-font" style={{ color: darkColors.primary }}>{currentModule.name}</h1>
                    <p style={{ color: darkColors.textSecondary }} className="mb-4">{currentModule.description}</p>
                    
                    {currentModule.keywords && currentModule.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {currentModule.keywords.map((keyword, index) => (
                          <Badge 
                            key={index} 
                            variant="outline" 
                            className="animate-fadeIn border-2 font-medium"
                            style={{ 
                              animationDelay: `${index * 0.1}s`,
                              borderColor: darkColors.primary,
                              color: darkColors.primary
                            }}
                          >
                            {keyword}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-8">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2 title-font" style={{ color: darkColors.secondary }}>
                      <BookOpen className="w-5 h-5" /> Recommended Articles
                    </h2>
                    
                    {moduleRecommendations.length === 0 ? (
                      <Alert 
                        className="border-2 animate-pulse" 
                        style={{ 
                          backgroundColor: darkColors.surface, 
                          borderColor: darkColors.secondary,
                          color: darkColors.textPrimary
                        }}
                      >
                        <AlertTitle className="font-bold title-font">No recommendations yet</AlertTitle>
                        <AlertDescription>
                          We're still finding relevant content for this module. Check back soon!
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {moduleRecommendations.map((article, index) => (
                          <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                            <ArticleCard 
                              article={article} 
                              moduleId={currentModule._id} 
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </FadeIn>
            )}
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer 
        className="border-t mt-8" 
        style={{ 
          backgroundColor: darkColors.surface,
          borderColor: darkColors.border
        }}
      >
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <BookOpen className="w-5 h-5" style={{ color: darkColors.primary }} />
              <span className="font-bold title-font" style={{ color: darkColors.primary }}>CS Content Hub</span>
            </div>
            
            <div className="text-sm" style={{ color: darkColors.textSecondary }}>
              © {new Date().getFullYear()} CS Content Hub. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;