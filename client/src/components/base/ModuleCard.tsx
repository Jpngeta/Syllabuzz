import React from 'react';
import { 
  Code, 
  FileText, 
  ChevronRight 
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

const ModuleCard: React.FC<ModuleCardProps> = ({ module, onClick }) => {
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

  return (
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
            {module.name} - {module.code}
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
};

export default ModuleCard;