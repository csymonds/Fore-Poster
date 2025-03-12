import { 
  formatDate, 
  createTimeSlot, 
  isPast, 
  areTimeSlotsClose, 
  findNextOptimalTimeSlot,
  OPTIMAL_POSTING_TIMES
} from '../dateUtils';

// Mock the current date for consistent testing
const mockDate = new Date('2023-05-15T12:00:00Z'); // Monday, noon UTC
const originalDate = global.Date;

beforeAll(() => {
  // @ts-ignore - Mock implementation
  global.Date = class extends Date {
    constructor(date) {
      if (date) {
        // @ts-ignore
        return new originalDate(date);
      }
      return mockDate;
    }
  };
});

afterAll(() => {
  global.Date = originalDate;
});

describe('dateUtils', () => {
  describe('formatDate', () => {
    it('formats date strings correctly', () => {
      const formatted = formatDate('2023-05-15T08:30:00Z');
      expect(formatted).toContain('May 15');
      expect(formatted).toContain('8:30 AM');
    });
  });

  describe('createTimeSlot', () => {
    it('creates a time slot with the specified hour and minute', () => {
      const baseDate = new Date('2023-05-15');
      const timeSlot = createTimeSlot(baseDate, 8, 30);
      
      expect(timeSlot.getHours()).toBe(8);
      expect(timeSlot.getMinutes()).toBe(30);
      expect(timeSlot.getSeconds()).toBe(0);
      expect(timeSlot.getDate()).toBe(15);
      expect(timeSlot.getMonth()).toBe(4); // May is month 4 (0-indexed)
    });
  });

  describe('isPast', () => {
    it('returns true for past dates', () => {
      const pastDate = new Date('2023-05-15T10:00:00Z'); // 2 hours before mock date
      expect(isPast(pastDate)).toBe(true);
    });

    it('returns false for future dates', () => {
      const futureDate = new Date('2023-05-15T14:00:00Z'); // 2 hours after mock date
      expect(isPast(futureDate)).toBe(false);
    });
  });

  describe('areTimeSlotsClose', () => {
    it('returns true for slots on the same day within the threshold', () => {
      const slot1 = new Date('2023-05-15T10:00:00Z');
      const slot2 = new Date('2023-05-15T10:15:00Z'); // 15 minutes apart
      
      expect(areTimeSlotsClose(slot1, slot2, 30)).toBe(true);
    });

    it('returns false for slots on the same day outside the threshold', () => {
      const slot1 = new Date('2023-05-15T10:00:00Z');
      const slot2 = new Date('2023-05-15T11:00:00Z'); // 1 hour apart
      
      expect(areTimeSlotsClose(slot1, slot2, 30)).toBe(false);
    });

    it('returns false for slots on different days', () => {
      const slot1 = new Date('2023-05-15T10:00:00Z');
      const slot2 = new Date('2023-05-16T10:00:00Z'); // Same time, different day
      
      expect(areTimeSlotsClose(slot1, slot2, 30)).toBe(false);
    });
  });

  describe('findNextOptimalTimeSlot', () => {
    it('finds the next available slot when none are scheduled', () => {
      const scheduledPosts: string[] = [];
      const nextSlot = findNextOptimalTimeSlot(scheduledPosts, mockDate);
      
      // Since our mock date is noon, the next optimal slot should be 6pm
      expect(nextSlot.getHours()).toBe(OPTIMAL_POSTING_TIMES[2].hour); // 6pm
      expect(nextSlot.getMinutes()).toBe(OPTIMAL_POSTING_TIMES[2].minute);
      expect(nextSlot.getDate()).toBe(mockDate.getDate());
    });

    it('skips occupied slots and finds the next available one', () => {
      // Create scheduled posts at 6pm today
      const sixPmToday = new Date(mockDate);
      sixPmToday.setHours(OPTIMAL_POSTING_TIMES[2].hour, OPTIMAL_POSTING_TIMES[2].minute, 0, 0);
      
      const scheduledPosts = [sixPmToday.toISOString()];
      const nextSlot = findNextOptimalTimeSlot(scheduledPosts, mockDate);
      
      // Next slot should be 7am tomorrow (since 6pm today is occupied)
      const tomorrowMorning = new Date(mockDate);
      tomorrowMorning.setDate(tomorrowMorning.getDate() + 1);
      tomorrowMorning.setHours(OPTIMAL_POSTING_TIMES[0].hour, OPTIMAL_POSTING_TIMES[0].minute, 0, 0);
      
      expect(nextSlot.getDate()).toBe(tomorrowMorning.getDate());
      expect(nextSlot.getHours()).toBe(OPTIMAL_POSTING_TIMES[0].hour);
    });

    it('handles multiple scheduled posts and finds the next available slot', () => {
      // Schedule posts for 6pm today and 7am tomorrow
      const sixPmToday = new Date(mockDate);
      sixPmToday.setHours(OPTIMAL_POSTING_TIMES[2].hour, OPTIMAL_POSTING_TIMES[2].minute, 0, 0);
      
      const tomorrow = new Date(mockDate);
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      const sevenAmTomorrow = new Date(tomorrow);
      sevenAmTomorrow.setHours(OPTIMAL_POSTING_TIMES[0].hour, OPTIMAL_POSTING_TIMES[0].minute, 0, 0);
      
      const scheduledPosts = [
        sixPmToday.toISOString(),
        sevenAmTomorrow.toISOString()
      ];
      
      const nextSlot = findNextOptimalTimeSlot(scheduledPosts, mockDate);
      
      // Next slot should be 11am tomorrow
      expect(nextSlot.getDate()).toBe(tomorrow.getDate());
      expect(nextSlot.getHours()).toBe(OPTIMAL_POSTING_TIMES[1].hour); // 11am
    });
  });
}); 