import { useState } from 'react';
import { PencilIcon, TrashIcon, SendIcon, CalendarIcon, PlusIcon } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { usePosts, useDeletePost, usePostNow } from '@/hooks/usePosts';
import PostModal from './PostModal';
import { Post } from '@/services/api';

const Dashboard = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPost, setSelectedPost] = useState<Post | undefined>(undefined);

  const { data: posts, isLoading, error } = usePosts();
  const deletePost = useDeletePost();
  const postNow = usePostNow();

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

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('en-US', {
        dateStyle: 'medium',
        timeStyle: 'short'
      });
    } catch (error) {
      console.error('Failed to format date:', error);
      return dateString;
    }
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
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Posts</h1>
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

        <div className="space-y-6">
          {posts?.map((post) => (
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

          {(!posts || posts.length === 0) && (
            <div className="text-center py-12 sm:py-16 bg-card rounded-xl shadow-lg border-2 border-indigo-400 dark:border-indigo-500">
              <p className="text-muted-foreground text-base sm:text-lg">
                No posts yet. Create your first post to get started!
              </p>
            </div>
          )}
        </div>

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