import React from 'react';
import { 
  Home, 
  Code, 
  Newspaper, 
  TrendingUp, 
  Bookmark 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { SidebarProps } from '../base/types';

const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  modules,
  loadModuleDetails,
  isMenuOpen,
  setIsMenuOpen,
  fetchTrending,
  user,
  darkColors
}) => {
  // Mobile menu
  const MobileMenu = () => (
    isMenuOpen && (
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
          onClick={() => {
            setActiveTab('trending'); 
            fetchTrending();
            setIsMenuOpen(false);
          }}
          style={{ color: activeTab === 'trending' ? darkColors.primary : darkColors.textPrimary }}
        >
          <TrendingUp className="w-4 h-4 mr-2" /> Trending
        </Button>
        <Button 
          variant="ghost" 
          className="justify-start hover:bg-opacity-20 transition-colors" 
          onClick={() => {
            setActiveTab('bookmarks'); 
            setIsMenuOpen(false);
          }}
          style={{ color: activeTab === 'bookmarks' ? darkColors.primary : darkColors.textPrimary }}
        >
          <Bookmark className="w-4 h-4 mr-2" /> Bookmarks
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
    )
  );

  // Desktop sidebar
  const DesktopSidebar = () => (
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
      <Button 
        variant={activeTab === 'bookmarks' ? 'default' : 'ghost'} 
        className="w-full justify-start transition-colors font-medium"
        onClick={() => setActiveTab('bookmarks')}
        style={{ 
          backgroundColor: activeTab === 'bookmarks' ? darkColors.primary : 'transparent',
          color: activeTab === 'bookmarks' ? darkColors.textPrimary : darkColors.textPrimary
        }}
      >
        <Bookmark className="w-4 h-4 mr-2" /> Bookmarks
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
        <div className="space-y-1 overflow-auto" style={{ maxHeight: '30rem', maxWidth: '100%' }}>
          {modules.map((module) => (
            <Button 
              key={module._id} 
              variant="ghost" 
              className="w-full justify-start transition-colors font-medium"
              onClick={() => loadModuleDetails(module._id)}
              style={{ color: darkColors.textPrimary }}
            >
              {module.code} - {module.name}
            </Button>
          ))}               
        </div>
      </div>
    </aside>
  );

  return (
    <>
      <MobileMenu />
      <DesktopSidebar />
    </>
  );
};

export default Sidebar;