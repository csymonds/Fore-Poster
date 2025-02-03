import { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { CalendarIcon } from 'lucide-react';
import { Post } from '@/services/api';
import { useCreatePost, useUpdatePost } from '@/hooks/usePosts';

interface PostModalProps {
  isOpen: boolean;
  onClose: () => void;
  post?: Post;
}

const PostModal: React.FC<PostModalProps> = ({ isOpen, onClose, post }) => {
  const [content, setContent] = useState('');
  const [scheduledTime, setScheduledTime] = useState<Date>(new Date());

  // Reset form when modal opens/closes or post changes
  useEffect(() => {
    if (isOpen) {
      if (post) {
        // Editing existing post
        setContent(post.content);
        setScheduledTime(new Date(post.scheduled_time));
      } else {
        // Creating new post
        setContent('');
        setScheduledTime(new Date());
      }
    }
  }, [isOpen, post]);

  const createPost = useCreatePost();
  const updatePost = useUpdatePost();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        content,
        scheduled_time: scheduledTime.toISOString(),
        platform: 'x',
        status: 'scheduled' as const
      };

      if (post) {
        await updatePost.mutateAsync({ 
          id: post.id, 
          post: payload 
        });
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
      <DialogContent className="sm:max-w-[425px] bg-card">
        <DialogHeader>
          <DialogTitle className="text-foreground">{post ? 'Edit Post' : 'Create Post'}</DialogTitle>
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
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="scheduled-time">Schedule Time</Label>
            <div className="relative">
              <DatePicker
                selected={scheduledTime}
                onChange={(date: Date | null) => date && setScheduledTime(date)}
                showTimeSelect
                timeFormat="HH:mm"
                timeIntervals={15}
                dateFormat="MMMM d, yyyy h:mm aa"
                className="w-full rounded-md border-2 border-indigo-400 dark:border-indigo-500 
                  bg-background text-foreground px-3 py-2 text-sm shadow-sm
                  focus-visible:outline-none focus-visible:ring-2 
                  focus-visible:ring-indigo-400 dark:focus-visible:ring-indigo-500"
                wrapperClassName="w-full"
                popperClassName="react-datepicker-popper"
                calendarClassName="bg-card border-2 border-indigo-400 dark:border-indigo-500 text-foreground"
                dayClassName={() => "text-foreground hover:bg-indigo-100 dark:hover:bg-indigo-900"}
                timeClassName={() => "text-foreground"}
              />
              <CalendarIcon className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="border-2 border-indigo-400 dark:border-indigo-500"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createPost.isPending || updatePost.isPending}
              className="bg-indigo-500 hover:bg-indigo-600 text-white"
            >
              {createPost.isPending || updatePost.isPending ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default PostModal;