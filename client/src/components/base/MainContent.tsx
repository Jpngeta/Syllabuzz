import React, { useState, useEffect } from 'react';
import { 
  Code, 
  Newspaper, 
  TrendingUp, 
  Search, 
  Search as SearchIcon,
  Star, 
  BookOpen,
  Sparkles,
  ChevronLeft
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ArticleCard from '../layout/ArticleCard';
import ModuleCard from './ModuleCard';
import ModuleSearch from './ModuleSearch';
import BookmarkList from './BookmarkList';
import { Module } from './types';
import { MainContentProps } from './types';
import { formatDate } from '../../services/apiService';

// Animation component for transitions
const FadeIn = ({ children }: { children: React.ReactNode }) => (
  <div 
    className="animate-fadeIn opacity-0" 
    style={{ 
      animation: 'fadeIn 0.5s ease forwards',
    }}
  >
    {children}
  </div>
);

const MainContent: React.FC<MainContentProps> = ({
  activeTab,
  setActiveTab,
  modules,
  articles,
  trendingArticles,
  searchQuery,
  searchResults,
  isSearching,
  currentModule,
  moduleRecommendations,
  isLoading,
  loadModuleDetails,
  darkColors
}) => {
  // Render home tab content
  const renderHomeContent = () => (
    <FadeIn>
      <div className="space-y-8">
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.primary }}>
              Welcome to Syllabuzz
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="hover-scale transition-all duration-300">
              <Card 
                className="bg-gradient-to-br text-white h-full glow-effect" 
                style={{ 
                  background: `linear-gradient(135deg, ${darkColors.primary}CC, ${darkColors.quaternary})`,
                }}
              >
                <CardHeader>
                  <CardTitle className="flex items-center title-font">
                    <Code className="w-5 h-5 mr-2" /> Explore CS Modules
                  </CardTitle>
                  <CardDescription className="text-white/90">
                    Discover computer science topics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p>Browse our collection of CS modules to find learning resources tailored to your interests.</p>
                </CardContent>
                <CardFooter>
                  <Button 
                    variant="secondary" 
                    onClick={() => setActiveTab('modules')}
                    className="font-medium"
                    style={{ backgroundColor: 'white', color: darkColors.primary }}
                  >
                    Browse Modules
                  </Button>
                </CardFooter>
              </Card>
            </div>
            
            <div className="hover-scale transition-all duration-300">
              <Card 
                className="bg-gradient-to-br text-white h-full glow-effect"
                style={{ 
                  background: `linear-gradient(135deg, ${darkColors.secondary}CC, ${darkColors.primary})`,
                }}
              >
                <CardHeader>
                  <CardTitle className="flex items-center title-font">
                    <Newspaper className="w-5 h-5 mr-2" /> Latest Articles
                  </CardTitle>
                  <CardDescription className="text-white/90">
                    Stay updated with CS news
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p>Get the latest news, articles, and academic papers in computer science and technology.</p>
                </CardContent>
                <CardFooter>
                  <Button 
                    variant="secondary" 
                    onClick={() => setActiveTab('articles')}
                    className="font-medium"
                    style={{ backgroundColor: 'white', color: darkColors.secondary }}
                  >
                    Read Articles
                  </Button>
                </CardFooter>
              </Card>
            </div>
            
            <div className="hover-scale transition-all duration-300">
              <Card 
                className="bg-gradient-to-br text-white h-full glow-effect"
                style={{ 
                  background: `linear-gradient(135deg, ${darkColors.tertiary}CC, ${darkColors.quaternary})`,
                }}
              >
                <CardHeader>
                  <CardTitle className="flex items-center title-font">
                    <TrendingUp className="w-5 h-5 mr-2" /> Trending Now
                  </CardTitle>
                  <CardDescription className="text-white/90">
                    What's popular in CS
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p>Discover the most popular and trending topics in the computer science community.</p>
                </CardContent>
                <CardFooter>
                  <Button 
                    variant="secondary" 
                    onClick={() => setActiveTab('trending')}
                    className="font-medium"
                    style={{ backgroundColor: 'white', color: darkColors.tertiary }}
                  >
                    View Trending
                  </Button>
                </CardFooter>
              </Card>
            </div>
          </div>
        </section>
        
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold title-font" style={{ color: darkColors.secondary }}>Recent Articles</h2>
            <Button 
              variant="link" 
              onClick={() => setActiveTab('articles')}
              style={{ color: darkColors.secondary }}
            >
              View All →
            </Button>
          </div>
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                  <CardHeader>
                    <Skeleton className="h-4 w-16 mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                    <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                    <Skeleton className="h-4 w-28" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                  </CardContent>
                  <CardFooter>
                    <Skeleton className="h-9 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                  </CardFooter>
                </Card>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {articles.slice(0, 6).map((article, index) => (
                <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                  <ArticleCard article={article} />
                </div>
              ))}
            </div>
          )}
          </section>
          
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold title-font" style={{ color: darkColors.primary }}>Featured Modules</h2>
              <Button 
                variant="link" 
                onClick={() => setActiveTab('modules')}
                style={{ color: darkColors.primary }}
              >
                View All →
              </Button>
            </div>
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[...Array(3)].map((_, i) => (
                  <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                    <CardHeader>
                      <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                    </CardHeader>
                    <CardContent>
                      <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                    </CardContent>
                    <CardFooter>
                      <Skeleton className="h-4 w-24" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                    </CardFooter>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {modules.slice(0, 6).map((module, index) => (
                  <div key={module._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                    <ModuleCard 
                      module={module} 
                      onClick={loadModuleDetails} 
                    />
                  </div>
                ))}
              </div>
            )}
          </section>
          </div>
          </FadeIn>
          );
          
          // Render modules tab content
          const renderModulesContent = () => {
            const [searchQuery, setSearchQuery] = useState<string>('');
            const [filteredModules, setFilteredModules] = useState<Module[]>(modules);
            
            // Filter modules when search query changes
            useEffect(() => {
              if (!searchQuery.trim()) {
                setFilteredModules(modules);
                return;
              }
              
              const query = searchQuery.toLowerCase();
              const filtered = modules.filter(module => 
                module.name.toLowerCase().includes(query) || 
                module.code.toLowerCase().includes(query)
              );
              
              setFilteredModules(filtered);
            }, [searchQuery, modules]);
            
            // Handle search input
            const handleSearch = (query: string) => {
              setSearchQuery(query);
            };
            
            return (
              <FadeIn>
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.primary }}>CS Modules</h2>
                  </div>
                  
                  {/* Add the search component */}
                  <ModuleSearch 
                    onSearch={handleSearch}
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    darkColors={darkColors}
                  />
                  
                  {/* Show search results count when searching */}
                  {searchQuery && (
                    <div className="mb-4 flex items-center" style={{ color: darkColors.textSecondary }}>
                      <Search className="w-4 h-4 mr-2" />
                      <p className="text-sm">
                        Found <span className="font-bold">{filteredModules.length}</span> modules 
                        matching "<span className="font-bold">{searchQuery}</span>"
                      </p>
                    </div>
                  )}
                  
                  {isLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[...Array(6)].map((_, i) => (
                        <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                          <CardHeader>
                            <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardHeader>
                          <CardContent>
                            <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardContent>
                          <CardFooter>
                            <Skeleton className="h-4 w-24" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                          </CardFooter>
                        </Card>
                      ))}
                    </div>
                  ) : filteredModules.length === 0 ? (
                    <div className="text-center py-12 border rounded-lg bg-gray-50">
                      <SearchIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <h3 className="text-xl font-medium mb-2">No Modules Found</h3>
                      <p className="text-gray-500 mb-4">
                        No modules match your search criteria. Try a different search term.
                      </p>
                      <Button
                        variant="outline"
                        onClick={() => setSearchQuery('')}
                        className="mt-2"
                        style={{ borderColor: darkColors.primary, color: darkColors.primary }}
                      >
                        Clear Search
                      </Button>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {filteredModules.map((module, index) => (
                        <div key={module._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                          <ModuleCard 
                            module={module} 
                            onClick={loadModuleDetails}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </FadeIn>
            );
          };
          
          // Render articles tab content
          const renderArticlesContent = () => (
          <FadeIn>
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.secondary }}>Articles & Papers</h2>
                
                <Tabs defaultValue="all" className="w-64">
                  <TabsList className="w-full" style={{ backgroundColor: `${darkColors.secondary}33` }}>
                    <TabsTrigger 
                      value="all"
                      className="data-[state=active]:text-white transition-all"
                      style={{ 
                        backgroundColor: "transparent",
                        "--tw-bg-opacity": "1",
                        "--secondary": darkColors.secondary,
                        "--tw-text-opacity": "1",
                        "--tw-white": darkColors.textPrimary,
                        "[data-state=active]:backgroundColor": darkColors.secondary
                      }}
                    >
                      All
                    </TabsTrigger>
                    <TabsTrigger 
                      value="news"
                      className="data-[state=active]:text-white transition-all"
                      style={{ 
                        backgroundColor: "transparent",
                        "--tw-bg-opacity": "1",
                        "--secondary": darkColors.secondary,
                        "--tw-text-opacity": "1",
                        "--tw-white": darkColors.textPrimary,
                        "[data-state=active]:backgroundColor": darkColors.secondary
                      }}
                    >
                      News
                    </TabsTrigger>
                    <TabsTrigger 
                      value="academic"
                      className="data-[state=active]:text-white transition-all"
                      style={{ 
                        backgroundColor: "transparent",
                        "--tw-bg-opacity": "1",
                        "--secondary": darkColors.secondary,
                        "--tw-text-opacity": "1",
                        "--tw-white": darkColors.textPrimary,
                        "[data-state=active]:backgroundColor": darkColors.secondary
                      }}
                    >
                      Academic
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
              
              {articles.length === 0 ? (
                <Alert 
                  className="border-2 animate-pulse" 
                  style={{ 
                    backgroundColor: darkColors.surface, 
                    borderColor: darkColors.secondary,
                    color: darkColors.textPrimary
                  }}
                >
                  <AlertTitle className="font-bold title-font">No articles found</AlertTitle>
                  <AlertDescription>
                    Try a different category or check back later for new content.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {articles.map((article, index) => (
                    <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                      <ArticleCard article={article} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </FadeIn>
          );
          
          // Render trending tab content
          const renderTrendingContent = () => (
          <FadeIn>
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold flex items-center gap-2 title-font" style={{ color: darkColors.tertiary }}>
                  <Sparkles className="w-6 h-6" /> Trending Content
                </h2>
              </div>
              
              {trendingArticles.length === 0 ? (
                <Alert 
                  className="border-2 animate-pulse" 
                  style={{ 
                    backgroundColor: darkColors.surface, 
                    borderColor: darkColors.tertiary,
                    color: darkColors.textPrimary
                  }}
                >
                  <AlertTitle className="font-bold title-font">No trending articles yet</AlertTitle>
                  <AlertDescription>
                    Check back later for trending content based on user interactions.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {trendingArticles.map((article, index) => (
                    <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                      <ArticleCard article={article} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </FadeIn>
          );
          
          // Render search results tab content
          const renderSearchContent = () => (
          <FadeIn>
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold title-font" style={{ color: darkColors.tertiary }}>Search Results</h2>
                <p style={{ color: darkColors.textSecondary }} className="flex items-center">
                  <Search className="w-4 h-4 mr-1" />
                  Found <span className="font-bold mx-1">{searchResults.length}</span> results for "{searchQuery}"
                </p>
              </div>
              
              {isSearching ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[...Array(6)].map((_, i) => (
                    <Card key={i} className="h-full" style={{ backgroundColor: darkColors.surface }}>
                      <CardHeader>
                        <Skeleton className="h-4 w-16 mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                        <Skeleton className="h-6 w-full mb-2" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                        <Skeleton className="h-4 w-28" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                      </CardHeader>
                      <CardContent>
                        <Skeleton className="h-20 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                      </CardContent>
                      <CardFooter>
                        <Skeleton className="h-9 w-full" style={{ backgroundColor: `${darkColors.textSecondary}40` }} />
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              ) : searchResults.length === 0 ? (
                <Alert 
                  className="border-2 animate-pulse" 
                  style={{ 
                    backgroundColor: darkColors.surface, 
                    borderColor: darkColors.tertiary,
                    color: darkColors.textPrimary
                  }}
                >
                  <AlertTitle className="font-bold title-font">No results found</AlertTitle>
                  <AlertDescription>
                    Try a different search term or browse our content categories.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {searchResults.map((article, index) => (
                    <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                      <ArticleCard article={article} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </FadeIn>
          );
          
          // Render module detail tab content
          const renderModuleDetailContent = () => (
          currentModule && (
            <FadeIn>
              <div className="space-y-6">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mb-4 border-2 transition-all flex items-center gap-1"
                  onClick={() => setActiveTab('modules')}
                  style={{ borderColor: darkColors.primary, color: darkColors.primary }}
                >
                  <ChevronLeft className="w-4 h-4" /> Back to Modules
                </Button>
                
                <div 
                  className="rounded-lg border-2 p-6 transition-all hover:shadow-md" 
                  style={{ 
                    backgroundColor: darkColors.surface,
                    borderColor: darkColors.primary, 
                    borderLeftWidth: '6px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.2)'
                  }}
                >
                  <h1 className="text-2xl font-bold mb-2 title-font" style={{ color: darkColors.primary }}>{currentModule.name}</h1>
                  <p style={{ color: darkColors.textSecondary }} className="mb-4">{currentModule.description}</p>
                  
                  {currentModule.keywords && currentModule.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {currentModule.keywords.map((keyword, index) => (
                        <Badge 
                          key={index} 
                          variant="outline" 
                          className="animate-fadeIn border-2 font-medium"
                          style={{ 
                            animationDelay: `${index * 0.1}s`,
                            borderColor: darkColors.primary,
                            color: darkColors.primary
                          }}
                        >
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="mt-8">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2 title-font" style={{ color: darkColors.secondary }}>
                    <BookOpen className="w-5 h-5" /> Recommended Articles
                  </h2>
                  
                  {moduleRecommendations.length === 0 ? (
                    <Alert 
                      className="border-2 animate-pulse" 
                      style={{ 
                        backgroundColor: darkColors.surface, 
                        borderColor: darkColors.secondary,
                        color: darkColors.textPrimary
                      }}
                    >
                      <AlertTitle className="font-bold title-font">No recommendations yet</AlertTitle>
                      <AlertDescription>
                        We're still finding relevant content for this module. Check back soon!
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {moduleRecommendations.map((article, index) => (
                        <div key={article._id} className="animate-fadeIn" style={{ animationDelay: `${index * 0.1}s` }}>
                          <ArticleCard 
                            article={article} 
                            moduleId={currentModule._id} 
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </FadeIn>
          )
          );
          
          // Render bookmarks tab content
          const renderBookmarksContent = () => (
          <FadeIn>
            <BookmarkList />
          </FadeIn>
          );
          
          // Render content based on active tab
          const renderTabContent = () => {
            switch (activeTab) {
              case 'home':
                return renderHomeContent();
              case 'modules':
                return renderModulesContent();
              case 'articles':
                return renderArticlesContent();
              case 'trending':
                return renderTrendingContent();
              case 'search':
                return renderSearchContent();
              case 'module':
                return renderModuleDetailContent();
              case 'bookmarks':
                return renderBookmarksContent();
              default:
                return renderHomeContent();
            }
          };
          
          return (
            <div className="flex-1">
              {renderTabContent()}
            </div>
          );
          };
          
          export default MainContent;