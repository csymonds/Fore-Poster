import { useState } from 'react';
import { PencilIcon, TrashIcon, SendIcon, CalendarIcon, PlusIcon, RefreshCwIcon, WifiIcon, AlertCircleIcon, CheckCircleIcon } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { usePosts, useDeletePost, usePostNow } from '@/hooks/usePosts';
import useSSE from '@/hooks/useSSE';
import PostModal from './PostModal';
import { Post } from '@/services/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatDate } from '@/utils/dateUtils';

/**
 * Sort posts by scheduled time
 * @param a First post
 * @param b Second post
 * @returns Sort order: -1 if a is before b, 1 if a is after b, 0 if equal
 */
const sortByScheduledTime = (a: Post, b: Post): number => {
  const dateA = new Date(a.scheduled_time);
  const dateB = new Date(b.scheduled_time);
  return dateA.getTime() - dateB.getTime();
};

const Dashboard = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPost, setSelectedPost] = useState<Post | undefined>(undefined);
  const [activeTab, setActiveTab] = useState('unposted');

  const { data: posts, isLoading, isFetching, error, refetch } = usePosts({ refetchInterval: 3000 });
  const deletePost = useDeletePost();
  const postNow = usePostNow();
  
  const { isConnected: sseConnected } = useSSE();

  const handleEdit = (post: Post) => {
    setSelectedPost(post);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this post?')) {
      try {
        await deletePost.mutateAsync(id);
      } catch (error) {
        console.error('Failed to delete post:', error);
      }
    }
  };

  const handlePostNow = async (id: number) => {
    try {
      await postNow.mutateAsync(id);
    } catch (error) {
      console.error('Failed to post:', error);
    }
  };

  // Filter and sort posts
  const unpostedPosts = posts
    ? [...posts.filter(post => post.status !== 'posted')].sort(sortByScheduledTime)
    : [];
    
  const postedPosts = posts
    ? [...posts.filter(post => post.status === 'posted')].sort((a, b) => 
        // Sort posted posts in reverse chronological order (newest first)
        sortByScheduledTime(b, a)
      )
    : [];

  // Function to render a list of posts
  const renderPosts = (postsList: Post[]) => {
    if (postsList.length === 0) {
      return (
        <div className="text-center py-12 sm:py-16 bg-card rounded-xl shadow-lg border-2 border-indigo-400 dark:border-indigo-500">
          <p className="text-muted-foreground text-base sm:text-lg">
            {activeTab === 'unposted' 
              ? 'No pending posts. Create your first post to get started!' 
              : 'No posted content yet.'}
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {postsList.map((post) => (
          <Card key={post.id} className="bg-card text-card-foreground rounded-xl shadow-lg border-2 border-indigo-400 dark:border-indigo-500">
            <CardHeader className="p-4 sm:p-6 border-b-2 border-indigo-400/30 dark:border-indigo-500/30">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg sm:text-xl font-bold text-foreground">
                  {post.platform === 'x' ? 'Twitter/X' : post.platform}
                </CardTitle>
                <span className={`
        px-3 sm:px-4 py-1 sm:py-1.5 rounded-full text-sm font-semibold
        ${post.status === 'scheduled' ? 'bg-indigo-500 dark:bg-indigo-600 text-white' : ''}
        ${post.status === 'posted' ? 'bg-emerald-500 dark:bg-emerald-600 text-white' : ''}
        ${post.status === 'failed' ? 'bg-rose-500 dark:bg-rose-600 text-white' : ''}
        ${post.status === 'draft' ? 'bg-slate-500 dark:bg-slate-600 text-white' : ''}
      `}>
                  {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-4 sm:p-6">
              {/* Post content */}
              <p className="text-foreground text-base sm:text-lg mb-4 whitespace-pre-wrap">
                {post.content}
              </p>

              {/* Display image if available */}
              {post.image_url && (
                <div className="mb-4">
                  <img 
                    src={post.image_url}
                    alt="Post attachment" 
                    className="rounded-lg max-h-[300px] w-auto object-contain border border-border"
                    onError={(e) => {
                      console.error(`Failed to load image: ${post.image_url}`);
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Calendar/time display */}
              <div className="flex items-center text-muted-foreground mb-6">
                <CalendarIcon className="h-5 w-5 mr-2" />
                <time className="text-sm">{formatDate(post.scheduled_time)}</time>
              </div>

              <div className="grid grid-cols-3 gap-2 sm:gap-3">
                <Button
                  variant="outline"
                  onClick={() => handleEdit(post)}
                  disabled={deletePost.isPending || postNow.isPending}
                  className="border-2 border-indigo-400 dark:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-950"
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                {post.status !== 'posted' && (
                  <Button
                    variant="outline"
                    onClick={() => handlePostNow(post.id)}
                    disabled={deletePost.isPending || postNow.isPending}
                    className="border-2 border-emerald-400 dark:border-emerald-500 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950"
                  >
                    <SendIcon className="h-4 w-4 mr-2" />
                    Post Now
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={() => handleDelete(post.id)}
                  disabled={deletePost.isPending || postNow.isPending}
                  className="border-2 border-rose-400 dark:border-rose-500 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-100">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error instanceof Error) {
    return (
      <Alert variant="destructive" className="m-4">
        <AlertDescription>
          {error.message || 'Failed to load posts'}
        </AlertDescription>
      </Alert>
    );
  }
  
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center">
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Posts</h1>
            {isFetching && (
              <RefreshCwIcon className="ml-3 h-5 w-5 animate-spin text-indigo-600" />
            )}
            {sseConnected && (
              <div className="ml-3 flex items-center text-emerald-600" title="Real-time updates active">
                <WifiIcon className="h-5 w-5" />
                <span className="ml-1 text-xs">Live</span>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => refetch()}
              variant="outline"
              size="sm"
              className="border-indigo-400 dark:border-indigo-500"
              disabled={isFetching}
            >
              <RefreshCwIcon className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              onClick={() => {
                setSelectedPost(undefined);
                setIsModalOpen(true);
              }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 sm:px-6 py-2 sm:py-3 rounded-lg text-base sm:text-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2"
              disabled={deletePost.isPending || postNow.isPending}
            >
              <PlusIcon className="h-5 w-5" />
              New Post
            </Button>
          </div>
        </div>

        {/* Sort information message */}
        <div className="mb-4 text-sm text-muted-foreground flex items-center">
          <CalendarIcon className="h-4 w-4 mr-1" />
          <span>
            {activeTab === 'unposted' 
              ? 'Posts sorted by scheduled time (earliest first)' 
              : 'Posts sorted by posted time (most recent first)'}
          </span>
        </div>

        <Tabs defaultValue="unposted" onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full mb-6 grid grid-cols-2">
            <TabsTrigger 
              value="unposted" 
              className="text-base sm:text-lg py-3"
            >
              Pending Posts
              {unpostedPosts.length > 0 && (
                <span className="ml-2 bg-indigo-600 text-white text-sm px-2 py-0.5 rounded-full">
                  {unpostedPosts.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger 
              value="posted" 
              className="text-base sm:text-lg py-3"
            >
              Posted
              {postedPosts.length > 0 && (
                <span className="ml-2 bg-emerald-600 text-white text-sm px-2 py-0.5 rounded-full">
                  {postedPosts.length}
                </span>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="unposted" className="mt-4">
            {renderPosts(unpostedPosts)}
          </TabsContent>

          <TabsContent value="posted" className="mt-4">
            {renderPosts(postedPosts)}
          </TabsContent>
        </Tabs>

        <PostModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedPost(undefined);
          }}
          post={selectedPost}
        />
      </div>
    </div>
  );
};

export default Dashboard;