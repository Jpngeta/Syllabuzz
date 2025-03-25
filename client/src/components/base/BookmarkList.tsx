import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import { useAuth } from '../auth/AuthProvider';
import ArticleCard from '../layout/ArticleCard';
import { Button } from '@/components/ui/button';

import { Loader2, BookmarkIcon } from 'lucide-react';
import { toast } from "sonner"


const BookmarkList: React.FC = () => {
  const { user } = useAuth();
  const [bookmarks, setBookmarks] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [page, setPage] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const pageSize = 12;

  // Fetch bookmarks on component mount and when user changes
  useEffect(() => {
    if (user) {
      fetchBookmarks();
    } else {
      setIsLoading(false);
    }
  }, [user]);

  // Fetch bookmarks from API
  const fetchBookmarks = async (reset: boolean = true) => {
    try {
      setIsLoading(true);
      const currentPage = reset ? 0 : page;
      
      if (reset) {
        setBookmarks([]);
        setPage(0);
      }
      
      const response = await authService.getBookmarks(pageSize, currentPage * pageSize);
      
      if (response.bookmarks.length < pageSize) {
        setHasMore(false);
      } else {
        setHasMore(true);
        setPage(currentPage + 1);
      }
      
      // If resetting, replace bookmarks, otherwise append
      if (reset) {
        setBookmarks(response.bookmarks);
      } else {
        setBookmarks(prev => [...prev, ...response.bookmarks]);
      }
    } catch (error) {
      toast("Failed to fetch bookmarks",
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Load more bookmarks
  const loadMore = () => {
    fetchBookmarks(false);
  };

  // Handle bookmark removal
  const handleBookmarkToggle = (articleId: string, isBookmarked: boolean) => {
    if (!isBookmarked) {
      // Remove from UI if unbookmarked
      setBookmarks(prev => prev.filter(bookmark => bookmark.article._id !== articleId));
    }
  };

  // If user not authenticated, show message
  if (!user) {
    return (
      <div className="text-center py-12">
        <BookmarkIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <h2 className="text-2xl font-bold mb-2">Authentication Required</h2>
        <p className="text-gray-500 mb-4">Please log in to view your saved articles</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold mb-6 flex items-center">
        <BookmarkIcon className="w-6 h-6 mr-2" />
        Your Saved Articles
      </h2>
      
      {isLoading && bookmarks.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin mr-2" />
          <span>Loading your saved articles...</span>
        </div>
      ) : bookmarks.length === 0 ? (
        <div className="text-center py-12 border rounded-lg bg-gray-50">
          <BookmarkIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-xl font-medium mb-2">No Saved Articles</h3>
          <p className="text-gray-500 mb-4">You haven't saved any articles yet</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bookmarks.map((bookmark) => (
              <ArticleCard 
                key={bookmark.bookmark_id} 
                article={bookmark.article} 
                onBookmarkToggle={handleBookmarkToggle}
              />
            ))}
          </div>
          
          {hasMore && (
            <div className="flex justify-center mt-8">
              <Button 
                onClick={loadMore} 
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                {isLoading ? 'Loading...' : 'Load More'}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BookmarkList;