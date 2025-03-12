import { useState, useEffect, useRef } from 'react';
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
import { Input } from '@/components/ui/input';
import { CalendarIcon, X, Loader2, SunIcon, Clock3Icon, MoonIcon } from 'lucide-react';
import { Post, PostsApi } from '@/services/api';
import { useCreatePost, useUpdatePost, usePosts } from '@/hooks/usePosts';
import { 
  OPTIMAL_POSTING_TIMES, 
  findNextOptimalTimeSlot, 
  createTimeSlot 
} from '@/utils/dateUtils';

interface PostModalProps {
  isOpen: boolean;
  onClose: () => void;
  post?: Post;
}

const PostModal: React.FC<PostModalProps> = ({ isOpen, onClose, post }) => {
  const [content, setContent] = useState('');
  const [scheduledTime, setScheduledTime] = useState<Date>(new Date());
  const [imageUrl, setImageUrl] = useState<string | null | undefined>(undefined);
  const [imageFilename, setImageFilename] = useState<string | null | undefined>(undefined);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch all posts to determine optimal scheduling
  const { data: allPosts } = usePosts();

  // Maximum file size: 16MB
  const MAX_FILE_SIZE = 16 * 1024 * 1024;

  // Find the next available optimal time slot when modal opens
  useEffect(() => {
    if (isOpen && !post) {
      if (allPosts) {
        // Get scheduled times of all unposted posts
        const scheduledTimes = allPosts
          .filter(p => p.status !== 'posted')
          .map(p => p.scheduled_time);
        
        // Find the next available optimal time slot
        const nextSlot = findNextOptimalTimeSlot(scheduledTimes);
        setScheduledTime(nextSlot);
      } else {
        // Default to next optimal time if posts aren't loaded yet
        const now = new Date();
        const optimalTimes = OPTIMAL_POSTING_TIMES.map(slot => 
          createTimeSlot(now, slot.hour, slot.minute)
        );
        
        // Find the first time slot in the future
        const futureSlot = optimalTimes.find(time => time > now);
        if (futureSlot) {
          setScheduledTime(futureSlot);
        } else {
          // If all today's slots are past, use tomorrow morning
          const tomorrow = new Date(now);
          tomorrow.setDate(tomorrow.getDate() + 1);
          setScheduledTime(createTimeSlot(
            tomorrow, 
            OPTIMAL_POSTING_TIMES[0].hour, 
            OPTIMAL_POSTING_TIMES[0].minute
          ));
        }
      }
    }
  }, [isOpen, post, allPosts]);

  // Reset form when modal opens/closes or post changes
  useEffect(() => {
    if (isOpen) {
      if (post) {
        // Editing existing post
        setContent(post.content);
        setScheduledTime(new Date(post.scheduled_time));
        setImageUrl(post.image_url);
        setImageFilename(post.image_filename);
      } else {
        // Creating new post - content was reset before
        setContent('');
        // Note: scheduledTime is set by the optimal time slot effect
        setImageUrl(undefined);
        setImageFilename(undefined);
      }
      setIsUploading(false);
      setUploadError(null);
    }
  }, [isOpen, post]);

  const createPost = useCreatePost();
  const updatePost = useUpdatePost();

  const handleTimeSlotSelect = (slot: typeof OPTIMAL_POSTING_TIMES[0]) => {
    const now = new Date();
    let targetDate = new Date(scheduledTime); // Keep the date part
    
    // Create time slot for today
    const todaySlot = createTimeSlot(now, slot.hour, slot.minute);
    
    // If today's slot is in the past, use tomorrow
    if (todaySlot < now) {
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      targetDate = createTimeSlot(tomorrow, slot.hour, slot.minute);
    } else {
      // Use today's slot
      targetDate = todaySlot;
    }
    
    setScheduledTime(targetDate);
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    setUploadError('');
    
    if (files && files.length > 0) {
      const file = files[0];
      
      // Check file size
      if (file.size > MAX_FILE_SIZE) {
        setUploadError(`File size exceeds ${MAX_FILE_SIZE / (1024 * 1024)}MB limit`);
        event.target.value = ''; // Reset file input
        return;
      }
      
      setIsUploading(true);
      try {
        const response = await PostsApi.uploadImage(file);
        setImageUrl(response.url);
        setImageFilename(response.filename);
        setUploadError('');
      } catch (error) {
        setUploadError('Failed to upload image');
        console.error('Image upload error:', error);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const handleRemoveImage = () => {
    setImageUrl(undefined);
    setImageFilename(undefined);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isUploading) {
      alert("Please wait for image upload to complete before saving");
      return;
    }
    
    try {
      const payload = {
        content,
        scheduled_time: scheduledTime.toISOString(),
        platform: 'x',
        status: 'scheduled' as const,
        // If we're editing a post and image was removed, explicitly set to null
        // This ensures the database removes the image references
        image_url: (post && post.image_url && imageUrl === undefined) ? null : imageUrl,
        image_filename: (post && post.image_filename && imageFilename === undefined) ? null : imageFilename
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
            <Label htmlFor="image">Image</Label>
            <div className="flex flex-col gap-2">
              <Input
                ref={fileInputRef}
                type="file"
                id="image"
                accept="image/*"
                onChange={handleImageUpload}
                disabled={isUploading}
                className="cursor-pointer"
              />

              {isUploading && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Uploading...</span>
                </div>
              )}

              {uploadError && (
                <div className="text-red-500 text-sm">{uploadError}</div>
              )}

              {imageUrl && (
                <div className="relative mt-2">
                  <img 
                    src={imageUrl}
                    alt="Preview" 
                    className="w-full h-auto rounded-md border border-border object-cover max-h-[200px]" 
                    onError={(e) => {
                      console.error(`Failed to load image: ${imageUrl}`);
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                  <button
                    type="button"
                    onClick={handleRemoveImage}
                    className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="scheduled-time">Schedule Time</Label>
            
            {/* Quick Time Slot Selectors */}
            <div className="flex flex-wrap gap-2 mb-2">
              <Button 
                type="button" 
                size="sm"
                variant="outline"
                className="flex items-center gap-1 border-indigo-400 dark:border-indigo-500"
                onClick={() => handleTimeSlotSelect(OPTIMAL_POSTING_TIMES[0])}
              >
                <SunIcon className="h-4 w-4" />
                <span>Morning</span>
              </Button>
              <Button 
                type="button" 
                size="sm"
                variant="outline"
                className="flex items-center gap-1 border-indigo-400 dark:border-indigo-500"
                onClick={() => handleTimeSlotSelect(OPTIMAL_POSTING_TIMES[1])}
              >
                <Clock3Icon className="h-4 w-4" />
                <span>Noon</span>
              </Button>
              <Button 
                type="button" 
                size="sm"
                variant="outline"
                className="flex items-center gap-1 border-indigo-400 dark:border-indigo-500"
                onClick={() => handleTimeSlotSelect(OPTIMAL_POSTING_TIMES[2])}
              >
                <MoonIcon className="h-4 w-4" />
                <span>Evening</span>
              </Button>
            </div>

            {/* Show which optimal slot was selected */}
            {!post && (
              <p className="text-xs text-muted-foreground mb-2">
                We've scheduled your post for the next available optimal time slot. Feel free to adjust.
              </p>
            )}
            
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
              disabled={createPost.isPending || updatePost.isPending || isUploading}
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