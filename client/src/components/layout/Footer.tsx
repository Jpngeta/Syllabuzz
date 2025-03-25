import React from 'react';
import { BookOpen } from 'lucide-react';
import { FooterProps } from '../base/types';

const Footer: React.FC<FooterProps> = ({ darkColors }) => {
  return (
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
            <span className="font-bold title-font" style={{ color: darkColors.primary }}>Syllabuzz</span>
          </div>
          
          <div className="text-sm" style={{ color: darkColors.textSecondary }}>
            © {new Date().getFullYear()} Syllabuzz. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;