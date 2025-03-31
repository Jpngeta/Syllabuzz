import React from 'react';
import { 
  BookOpen, 
  Search, 
  Menu, 
  X,
  LogOut
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { HeaderProps } from '../base/types';
import { useAuth } from '../auth/AuthProvider';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';

const Header: React.FC<HeaderProps> = ({
  searchQuery,
  setSearchQuery,
  handleSearch,
  isMenuOpen,
  setIsMenuOpen,
  darkColors
}) => {
  const { logout, user, isLoading } = useAuth();
  
  const handleLogout = async () => {
    try {
      await logout();
      // Redirect is handled by the AuthProvider
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
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
          <h1 className="text-xl font-bold title-font" style={{ color: darkColors.primary }}>Syllabuzz</h1>
        </div>
        
        <div className="hidden md:block w-1/3">
          <form onSubmit={handleSearch} className="relative">
            <Search 
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" 
              style={{ color: darkColors.textSecondary }} 
            />
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
            {!isLoading && user && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <div className="flex items-center gap-2 cursor-pointer">
                    <Avatar className="border-2" style={{ borderColor: darkColors.primary }}>
                      <AvatarFallback style={{ backgroundColor: darkColors.primary, color: darkColors.textPrimary }}>
                        {user?.name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                      </AvatarFallback>
                    </Avatar>
                    <span className="font-medium" style={{ color: darkColors.textPrimary }}>
                      {user?.name || user?.username || 'User'}
                    </span>
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem className="opacity-70 cursor-default">
                    <span className="text-xs">{user?.email}</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="cursor-pointer">
                    <LogOut className="w-4 h-4 mr-2" />
                    <span>Logout</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            {!isLoading && !user && (
              <Button
                variant="outline"
                onClick={() => window.location.href = '/login'}
                style={{ 
                  borderColor: darkColors.primary,
                  color: darkColors.primary
                }}
              >
                Login
              </Button>
            )}
          </div>
        </div>
      </div>
      
      {/* Mobile Search */}
      <div className="md:hidden px-4 pb-3">
        <form onSubmit={handleSearch} className="relative">
          <Search 
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" 
            style={{ color: darkColors.textSecondary }} 
          />
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
    </header>
  );
};

export default Header;