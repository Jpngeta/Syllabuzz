import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  ThumbsUp, 
  BookmarkPlus, 
  ExternalLink,
  Star,
  Check,
  Bookmark
} from 'lucide-react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from "sonner"
import { authService } from '../../services/authService';
import { useAuth } from '../auth/AuthProvider';
import { ArticleCardProps } from '../base/types';
import { formatDate, recordInteraction } from '../../services/apiService';

const ArticleCard: React.FC<ArticleCardProps> = ({ article, moduleId, onBookmarkToggle }) => {
  const { user } = useAuth();
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Define the dark color palette
  const darkColors = {
    primary: '#FF6B6B',
    secondary: '#4ECDC4',
    tertiary: '#FFD166',
    quaternary: '#6A0572',
    textPrimary: '#2D3748',
    textSecondary: '#4A5568',
  };
  
  // Check if article is bookmarked when component mounts
  useEffect(() => {
    const checkBookmarkStatus = async () => {
      if (user && article._id) {
        try {
          const isBookmarked = await authService.isArticleBookmarked(article._id);
          setIsBookmarked(isBookmarked);
        } catch (error) {
          // If there's an error checking, default to false
          setIsBookmarked(false);
        }
      }
    };
    
    checkBookmarkStatus();
  }, [user, article._id]);
  
  // Open article in new tab
  const openArticle = (): void => {
    if (user) {
      // Record view interaction
      recordView();
    }
    window.open(article.url, '_blank');
  };
  
  // Record view interaction
  const recordView = async (): Promise<void> => {
    if (user) {
      recordInteraction(user.id, article._id, 'view', moduleId || null);
    }
  };
  
  // Like article
  const likeArticle = async (e: React.MouseEvent): Promise<void> => {
    e.stopPropagation(); // Prevent opening the article
    
    if (!user) {
      toast(
         "Authentication Required"
      );
      return;
    }
    
    try {
      setIsLoading(true);
      await authService.likeArticle(article._id, moduleId);
      setIsLiked(true);
      toast("Article Liked");
    } catch (error) {
      toast("Failed to like article");
    } finally {
      setIsLoading(false);
    }
  };
  
  // Bookmark article
  const bookmarkArticle = async (e: React.MouseEvent): Promise<void> => {
    e.stopPropagation(); // Prevent opening the article
    
    if (!user) {
      toast("Authentication Required");
      return;
    }
    
    try {
      setIsLoading(true);
      
      if (isBookmarked) {
        // Remove bookmark if already bookmarked
        await authService.removeBookmark(article._id);
        setIsBookmarked(false);
        toast("Article Unsaved");
        
        // Call the callback if provided
        if (onBookmarkToggle) {
          onBookmarkToggle(article._id, false);
        }
      } else {
        // Add bookmark
        await authService.bookmarkArticle(article._id, moduleId);
        setIsBookmarked(true);
        toast("Article Saved");
        
        // Call the callback if provided
        if (onBookmarkToggle) {
          onBookmarkToggle(article._id, true);
        }
      }
    } catch (error) {
      toast('Failed to save article');
    } finally {
      setIsLoading(false);
    }
  };
  
  const hasImage = article.image_url && article.image_url.trim() !== '';
    
  return (
    <div className="h-full transition-all hover:scale-105">
      <Card 
        className="h-full border hover:shadow-lg cursor-pointer transition-all duration-300" 
        onClick={openArticle}
        style={{ 
          backgroundColor: darkColors.textPrimary === '#2D3748' ? '#F7F9FC' : '#2D3748', 
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
          <CardTitle className="text-lg line-clamp-2 font-bold" style={{ color: darkColors.textPrimary }}>
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
            onClick={likeArticle}
            disabled={isLoading || isLiked}
            className="hover:bg-opacity-20 transition-colors flex items-center gap-1"
            style={{ 
              color: isLiked ? darkColors.primary : darkColors.quaternary, 
              opacity: isLiked ? 0.7 : 1
            }}
          >
            {isLiked ? <Check className="w-4 h-4" /> : <ThumbsUp className="w-4 h-4" />}
            {isLiked ? 'Liked' : 'Like'}
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={bookmarkArticle}
            disabled={isLoading}
            className="hover:bg-opacity-20 transition-colors flex items-center gap-1"
            style={{ 
              color: isBookmarked ? darkColors.primary : darkColors.primary, 
              opacity: isBookmarked ? 0.7 : 1
            }}
          >
            {isBookmarked ? 
              <Bookmark className="w-4 h-4" fill={darkColors.primary} /> : 
              <BookmarkPlus className="w-4 h-4" />
            }
            {isBookmarked ? 'Saved' : 'Save'}
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            asChild
            className="hover:bg-opacity-20 transition-colors"
            style={{ color: darkColors.secondary }}
          >
            <a href={article.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
              <ExternalLink className="w-4 h-4 mr-1" /> View
            </a>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ArticleCard;