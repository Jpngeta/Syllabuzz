import React from 'react';
import { Search, X } from 'lucide-react';

interface ModuleSearchProps {
  onSearch: (query: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  darkColors: any;
}

const ModuleSearch: React.FC<ModuleSearchProps> = ({ 
  onSearch, 
  searchQuery, 
  setSearchQuery, 
  darkColors 
}) => {
  // Handle search input changes
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearch(query);
  };

  // Clear the search
  const clearSearch = () => {
    setSearchQuery('');
    onSearch('');
  };

  return (
    <div className="w-full mb-6 animate-fadeIn">
      <div className="relative">
        <Search 
          className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" 
          style={{ color: darkColors.textSecondary }} 
        />
        <input
          type="text"
          placeholder="Search modules by name or code..."
          className="w-full pl-10 pr-10 py-3 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
          style={{ 
            backgroundColor: darkColors.surface,
            borderColor: darkColors.primary,
            color: darkColors.textPrimary
          }}
          value={searchQuery}
          onChange={handleSearchChange}
        />
        {searchQuery && (
          <button
            className="absolute right-3 top-1/2 transform -translate-y-1/2 hover:bg-gray-100 p-1 rounded-full transition-colors"
            onClick={clearSearch}
            style={{ color: darkColors.textSecondary }}
            aria-label="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ModuleSearch;