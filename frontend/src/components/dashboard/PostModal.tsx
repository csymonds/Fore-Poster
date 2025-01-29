import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Post, CreatePostPayload } from '@/services/api';
import { useCreatePost, useUpdatePost } from '@/hooks/usePosts';

interface PostModalProps {
  isOpen: boolean;
  onClose: () => void;
  post?: Post;
}

const PostModal = ({ isOpen, onClose, post }: PostModalProps) => {
  const [content, setContent] = useState(post?.content || '');
  const [scheduledTime, setScheduledTime] = useState(post?.scheduled_time || '');
  const createPost = useCreatePost();
  const updatePost = useUpdatePost();
  
  const isOverLimit = content.length > 280;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const payload: CreatePostPayload = {
      content,
      scheduled_time: scheduledTime,
      platform: 'x',
      status: 'draft' // Always start as draft
    };

    try {
      if (post) {
        await updatePost.mutateAsync({ id: post.id, post: payload });
      } else {
        await createPost.mutateAsync(payload);
      }
      onClose();
    } catch (error) {
      console.error('Failed to save post:', error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{post ? 'Edit Post' : 'New Post'}</DialogTitle>
          <DialogDescription>
            Create or schedule a post for X (Twitter)
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              className="resize-none"
              placeholder="What's on your mind?"
            />
            <div className="text-sm text-gray-500">
              {content.length}/280 characters
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="scheduled-time">Schedule Time</Label>
            <Input
              id="scheduled-time"
              type="datetime-local"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
            />
          </div>

          <div className="flex justify-end space-x-2">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isOverLimit || createPost.isPending || updatePost.isPending}
            >
              {createPost.isPending || updatePost.isPending ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Saving...
                </span>
              ) : (
                'Save'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default PostModal;