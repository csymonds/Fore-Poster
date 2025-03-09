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
import { CalendarIcon, ImageIcon, X, Loader2 } from 'lucide-react';
import { Post, PostsApi } from '@/services/api';
import { useCreatePost, useUpdatePost } from '@/hooks/usePosts';

interface PostModalProps {
  isOpen: boolean;
  onClose: () => void;
  post?: Post;
}

const PostModal: React.FC<PostModalProps> = ({ isOpen, onClose, post }) => {
  const [content, setContent] = useState('');
  const [scheduledTime, setScheduledTime] = useState<Date>(new Date());
  const [imageUrl, setImageUrl] = useState<string | undefined>(undefined);
  const [imageFilename, setImageFilename] = useState<string | undefined>(undefined);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
        // Creating new post
        setContent('');
        setScheduledTime(new Date());
        setImageUrl(undefined);
        setImageFilename(undefined);
      }
      setIsUploading(false);
      setUploadError(null);
    }
  }, [isOpen, post]);

  const createPost = useCreatePost();
  const updatePost = useUpdatePost();

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      console.log(`Attempting to upload file: ${file.name}, size: ${file.size} bytes`);
      
      // Direct upload without using the hook - this gives us more control
      const response = await PostsApi.uploadImage(file);
      console.log("Upload successful:", response);
      
      // Update state with upload response
      setImageUrl(response.url);
      setImageFilename(response.filename);
      
      // Verify the image URL works by trying to load it
      try {
        await fetch(response.url, { method: 'HEAD' });
        console.log("Verified image URL is accessible:", response.url);
      } catch (fetchError) {
        console.warn("Image URL may not be directly accessible:", fetchError);
        // We'll still use the URL provided by the server, but logged the warning
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } finally {
      setIsUploading(false);
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
      // When updating a post and the image has been removed,
      // explicitly set image fields to null to remove them in the database
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

      console.log("Submitting post with payload:", payload);

      if (post) {
        const result = await updatePost.mutateAsync({ 
          id: post.id, 
          post: payload 
        });
        console.log("Post updated successfully:", result);
      } else {
        const result = await createPost.mutateAsync(payload);
        console.log("Post created successfully:", result);
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