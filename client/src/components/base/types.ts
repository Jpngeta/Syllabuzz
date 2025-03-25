// Define types for data models
export interface Module {
    _id: string;
    name: string;
    code: string;
    description: string;
    keywords?: string[];
    vector_embedding?: number[];
    created_at?: string;
    updated_at?: string;
  }
  
  export interface Article {
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
  
 // In types.ts
export interface User {
    id: string;
    name: string;
    email: string;
    modules?: string[]; // Make modules optional with ?
    username?: string; // Add username field
  }
  
  export type TabType = 'home' | 'modules' | 'articles' | 'trending' | 'search' | 'module' | 'bookmarks';
  export type InteractionType = 'view' | 'like' | 'bookmark';
  
  // Props interfaces
  export interface ArticleCardProps {
    article: Article;
    moduleId?: string;
    onBookmarkToggle?: (articleId: string, isBookmarked: boolean) => void;
  }
  
  export interface ModuleCardProps {
    module: Module;
    onClick: (moduleId: string) => void;
  }
  
  // Animation component props
  export interface FadeInProps {
    children: React.ReactNode;
  }
  
  // Header props
  export interface HeaderProps {
    searchQuery: string;
    setSearchQuery: (query: string) => void;
    handleSearch: (e: React.FormEvent) => Promise<void>;
    isMenuOpen: boolean;
    setIsMenuOpen: (isOpen: boolean) => void;
    user: User | null;
    darkColors: any;

    
  }
  
  // Sidebar props
  export interface SidebarProps {
    activeTab: TabType;
    setActiveTab: (tab: TabType) => void;
    modules: Module[];
    loadModuleDetails: (moduleId: string) => Promise<void>;
    isMenuOpen: boolean;
    setIsMenuOpen: (isOpen: boolean) => void;
    fetchTrending: () => Promise<Article[]>; // Changed from Promise<void> to Promise<Article[]>
    user: User | null;
    darkColors: any;
  }
  
  // MainContent props
  export interface MainContentProps {
    activeTab: TabType;
    setActiveTab: (tab: TabType) => void;
    modules: Module[];
    articles: Article[];
    trendingArticles: Article[];
    searchQuery: string;
    searchResults: Article[];
    isSearching: boolean;
    currentModule: Module | null;
    moduleRecommendations: Article[];
    isLoading: boolean;
    loadModuleDetails: (moduleId: string) => Promise<void>;
    darkColors: any;
  }
  
  // Footer props
  export interface FooterProps {
    darkColors: any;
  }