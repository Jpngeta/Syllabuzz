import React, { useState, useEffect } from 'react';
import { 
  Code, 
  FileText, 
  ChevronRight,
  Star
} from 'lucide-react';
import { 
  Card, 
  CardContent, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ModuleCardProps } from './types';
import { authService } from '../../services/authService';
import { useAuth } from '../auth/AuthProvider';

const ModuleCard: React.FC<ModuleCardProps> = ({ module, onClick, onStarToggle }) => {
  const { user } = useAuth();
  const [isStarred, setIsStarred] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Define the dark color palette
  const darkColors = {
    primary: '#FF6B6B',
    secondary: '#4ECDC4',
    tertiary: '#FFD166',
    quaternary: '#6A0572',
    surface: '#F7F9FC',
    textPrimary: '#2D3748',
    textSecondary: '#4A5568',
  };

  // Check if module is starred when component mounts
  useEffect(() => {
    const checkStarredStatus = async () => {
      if (user && module._id) {
        try {
          const isStarred = await authService.isModuleStarred(module._id);
          setIsStarred(isStarred);
        } catch (error) {
          // If there's an error checking, default to false
          setIsStarred(false);
        }
      }
    };
    
    checkStarredStatus();
  }, [user, module._id]);

  // Toggle star status
  const handleStarToggle = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click event

    if (!user) {
      // Optionally handle non-authenticated users
      return;
    }

    setIsLoading(true);
    
    try {
      if (isStarred) {
        // Unstar the module
        await authService.unstarModule(module._id);
        setIsStarred(false);
        // Notify parent component
        if (onStarToggle) {
          onStarToggle(module._id, false);
        }
      } else {
        // Star the module
        await authService.starModule(module._id);
        setIsStarred(true);
        // Notify parent component
        if (onStarToggle) {
          onStarToggle(module._id, true);
        }
      }
    } catch (error) {
      console.error('Error toggling module star status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full transition-all hover-scale">
      <Card 
        className="h-full border hover:shadow-lg cursor-pointer transition-all duration-300" 
        onClick={() => onClick(module._id)}
        style={{ 
          backgroundColor: isStarred ? darkColors.quaternary + '33' : darkColors.surface, // Light purple background if starred
          borderColor: darkColors.primary, 
          borderLeftWidth: '4px' 
        }}
      >
        <CardHeader className="flex flex-row justify-between items-start">
          <CardTitle className="flex items-center gap-2 font-bold title-font" style={{ color: darkColors.primary }}>
            <Code className="w-5 h-5" />
            {module.name} - {module.code}
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm"
            className="p-1 hover:bg-opacity-20 -mt-1 -mr-2"
            onClick={handleStarToggle}
            disabled={isLoading}
            aria-label={isStarred ? "Unstar module" : "Star module"}
            style={{ color: isStarred ? darkColors.tertiary : darkColors.textSecondary }}
          >
            <Star className="w-5 h-5" fill={isStarred ? darkColors.tertiary : "none"} />
          </Button>
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
};

export default ModuleCard;