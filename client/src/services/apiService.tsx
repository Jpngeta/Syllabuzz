import { Article, Module, InteractionType } from './types';

// Fetch modules from API
export const fetchModules = async (): Promise<Module[]> => {
  try {
    const response = await fetch('/api/modules');
    const data = await response.json();
    return data.modules;
  } catch (error) {
    console.error('Error fetching modules:', error);
    return [];
  }
};

// Fetch articles from API
export const fetchArticles = async (category: string | null = null): Promise<Article[]> => {
  try {
    let url = '/api/articles';
    if (category) {
      url += `?category=${category}`;
    }
    const response = await fetch(url);
    const data = await response.json();
    return data.articles;
  } catch (error) {
    console.error('Error fetching articles:', error);
    return [];
  }
};

// Fetch trending articles from API
export const fetchTrending = async (): Promise<Article[]> => {
  try {
    const response = await fetch('/api/trending');
    const data = await response.json();
    return data.trending;
  } catch (error) {
    console.error('Error fetching trending articles:', error);
    return [];
  }
};

// Search articles
export const searchArticles = async (query: string): Promise<Article[]> => {
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    return data.articles;
  } catch (error) {
    console.error('Error searching articles:', error);
    return [];
  }
};

// Get module details
export const getModuleDetails = async (moduleId: string): Promise<Module | null> => {
  try {
    const response = await fetch(`/api/modules/${moduleId}`);
    const data = await response.json();
    return data.module;
  } catch (error) {
    console.error('Error getting module details:', error);
    return null;
  }
};

// Get module recommendations
export const getModuleRecommendations = async (moduleId: string): Promise<Article[]> => {
  try {
    const response = await fetch(`/api/modules/${moduleId}/recommendations`);
    const data = await response.json();
    return data.recommendations;
  } catch (error) {
    console.error('Error getting module recommendations:', error);
    return [];
  }
};

// Record user interaction with an article
export const recordInteraction = async (
  userId: string,
  articleId: string,
  type: InteractionType = 'view',
  moduleId: string | null = null
): Promise<boolean> => {
  try {
    const token = localStorage.getItem('auth_token');
    
    await fetch('/api/interaction', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify({
        user_id: userId,
        article_id: articleId,
        module_id: moduleId,
        type: type
      })
    });
    return true;
  } catch (error) {
    console.error('Error recording interaction:', error);
    return false;
  }
};

// Format date helper function
export const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};