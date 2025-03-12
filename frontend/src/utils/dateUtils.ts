/**
 * Date and time utilities for the application
 */

/**
 * Formats a date string in a user-friendly format
 */
export const formatDate = (dateString: string): string => {
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

// The optimal posting times (in 24-hour format)
export const OPTIMAL_POSTING_TIMES = [
  { hour: 7, minute: 0, name: 'Morning' },   // 7:00 AM
  { hour: 11, minute: 0, name: 'Noon' },     // 11:00 AM
  { hour: 18, minute: 0, name: 'Evening' }   // 6:00 PM
];

/**
 * Creates a Date object for a specific hour and minute on a given day
 */
export const createTimeSlot = (
  baseDate: Date, 
  hour: number, 
  minute: number
): Date => {
  const date = new Date(baseDate);
  date.setHours(hour, minute, 0, 0);
  return date;
};

/**
 * Checks if a date is in the past
 */
export const isPast = (date: Date): boolean => {
  return date < new Date();
};

/**
 * Checks if two time slots are on the same day and within 30 minutes of each other
 */
export const areTimeSlotsClose = (
  slot1: Date, 
  slot2: Date, 
  minutesThreshold = 30
): boolean => {
  // Check if dates are on the same day
  const sameDay = 
    slot1.getFullYear() === slot2.getFullYear() &&
    slot1.getMonth() === slot2.getMonth() &&
    slot1.getDate() === slot2.getDate();
  
  if (!sameDay) return false;
  
  // Calculate time difference in minutes
  const diffMs = Math.abs(slot1.getTime() - slot2.getTime());
  const diffMinutes = diffMs / (1000 * 60);
  
  return diffMinutes <= minutesThreshold;
};

/**
 * Finds the next available optimal time slot
 * 
 * @param scheduledPosts Array of already scheduled posts (ISO date strings)
 * @param currentTime Current time (defaults to now)
 * @returns A Date object for the next available optimal time slot
 */
export const findNextOptimalTimeSlot = (
  scheduledPosts: string[],
  currentTime: Date = new Date()
): Date => {
  // Convert all scheduled posts to Date objects for easier comparison
  const scheduledTimes = scheduledPosts.map(post => new Date(post));
  
  // Start with today
  let targetDay = new Date(currentTime);
  let daysToLookAhead = 0;
  const MAX_DAYS_TO_LOOK = 7; // Limit search to 7 days to avoid infinite loop
  
  while (daysToLookAhead < MAX_DAYS_TO_LOOK) {
    // Check each optimal time slot for the current day
    for (const timeSlot of OPTIMAL_POSTING_TIMES) {
      const slotTime = createTimeSlot(targetDay, timeSlot.hour, timeSlot.minute);
      
      // Skip past time slots
      if (isPast(slotTime)) continue;
      
      // Check if this slot conflicts with any existing scheduled post
      const isConflicting = scheduledTimes.some(scheduledTime => 
        areTimeSlotsClose(slotTime, scheduledTime)
      );
      
      if (!isConflicting) {
        return slotTime;
      }
    }
    
    // Move to the next day
    targetDay.setDate(targetDay.getDate() + 1);
    daysToLookAhead++;
  }
  
  // If all slots are taken in the next week, default to tomorrow morning
  const tomorrow = new Date(currentTime);
  tomorrow.setDate(tomorrow.getDate() + 1);
  return createTimeSlot(tomorrow, OPTIMAL_POSTING_TIMES[0].hour, OPTIMAL_POSTING_TIMES[0].minute);
}; 