import * as React from "react"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={`flex min-h-20 w-full rounded-md border-2 border-indigo-400 dark:border-indigo-500 
          bg-background px-3 py-2 text-sm shadow-sm transition-colors
          placeholder:text-muted-foreground 
          focus-visible:outline-none focus-visible:ring-2 
          focus-visible:ring-indigo-400 dark:focus-visible:ring-indigo-500 
          disabled:cursor-not-allowed disabled:opacity-50 
          ${className}`}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }