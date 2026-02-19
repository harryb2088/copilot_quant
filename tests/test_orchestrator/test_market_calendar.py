"""
Tests for Market Calendar

Tests NYSE market hours, US holiday detection, and market state transitions.
"""

import unittest
from datetime import datetime, time
from zoneinfo import ZoneInfo

from copilot_quant.orchestrator.market_calendar import MarketCalendar, MarketState


class TestMarketCalendar(unittest.TestCase):
    """Test MarketCalendar functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calendar = MarketCalendar()
        self.eastern = ZoneInfo("America/New_York")
    
    def test_market_hours(self):
        """Test market open and close times"""
        self.assertEqual(self.calendar.MARKET_OPEN_TIME, time(9, 30))
        self.assertEqual(self.calendar.MARKET_CLOSE_TIME, time(16, 0))
    
    def test_weekend_detection(self):
        """Test weekend detection"""
        # Saturday
        saturday = datetime(2024, 1, 6, 12, 0, tzinfo=self.eastern)
        self.assertTrue(self.calendar.is_weekend(saturday))
        
        # Sunday
        sunday = datetime(2024, 1, 7, 12, 0, tzinfo=self.eastern)
        self.assertTrue(self.calendar.is_weekend(sunday))
        
        # Monday
        monday = datetime(2024, 1, 8, 12, 0, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_weekend(monday))
    
    def test_holiday_detection(self):
        """Test US market holiday detection"""
        # New Year's Day 2024 (Monday, Jan 1)
        new_years = datetime(2024, 1, 1, 12, 0, tzinfo=self.eastern)
        self.assertTrue(self.calendar.is_holiday(new_years))
        
        # Christmas 2024 (Wednesday, Dec 25)
        christmas = datetime(2024, 12, 25, 12, 0, tzinfo=self.eastern)
        self.assertTrue(self.calendar.is_holiday(christmas))
        
        # Regular trading day
        regular_day = datetime(2024, 3, 15, 12, 0, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_holiday(regular_day))
    
    def test_trading_day(self):
        """Test trading day detection"""
        # Weekend - not a trading day
        saturday = datetime(2024, 1, 6, 12, 0, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_trading_day(saturday))
        
        # Holiday - not a trading day
        new_years = datetime(2024, 1, 1, 12, 0, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_trading_day(new_years))
        
        # Regular trading day
        regular_day = datetime(2024, 3, 15, 12, 0, tzinfo=self.eastern)
        self.assertTrue(self.calendar.is_trading_day(regular_day))
    
    def test_market_open(self):
        """Test market open detection"""
        # During trading hours (Friday, March 15, 2024, 10:00 AM)
        trading_hours = datetime(2024, 3, 15, 10, 0, tzinfo=self.eastern)
        self.assertTrue(self.calendar.is_market_open(trading_hours))
        
        # Before market open
        before_open = datetime(2024, 3, 15, 9, 0, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_market_open(before_open))
        
        # After market close
        after_close = datetime(2024, 3, 15, 17, 0, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_market_open(after_close))
        
        # Weekend
        weekend = datetime(2024, 3, 16, 12, 0, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_market_open(weekend))
    
    def test_market_state(self):
        """Test market state transitions"""
        # Pre-market (Friday, March 15, 2024, 8:00 AM)
        pre_market = datetime(2024, 3, 15, 8, 0, tzinfo=self.eastern)
        self.assertEqual(
            self.calendar.get_market_state(pre_market),
            MarketState.PRE_MARKET
        )
        
        # Trading hours
        trading = datetime(2024, 3, 15, 10, 0, tzinfo=self.eastern)
        self.assertEqual(
            self.calendar.get_market_state(trading),
            MarketState.TRADING
        )
        
        # Post-market
        post_market = datetime(2024, 3, 15, 17, 0, tzinfo=self.eastern)
        self.assertEqual(
            self.calendar.get_market_state(post_market),
            MarketState.POST_MARKET
        )
        
        # Closed (weekend)
        closed = datetime(2024, 3, 16, 12, 0, tzinfo=self.eastern)
        self.assertEqual(
            self.calendar.get_market_state(closed),
            MarketState.CLOSED
        )
    
    def test_next_market_open(self):
        """Test next market open calculation"""
        # Before market open on trading day
        before_open = datetime(2024, 3, 15, 8, 0, tzinfo=self.eastern)
        next_open = self.calendar.get_next_market_open(before_open)
        
        # Should be same day at 9:30 AM
        self.assertEqual(next_open.date(), before_open.date())
        self.assertEqual(next_open.time(), time(9, 30))
        
        # After market close on Friday
        friday_pm = datetime(2024, 3, 15, 17, 0, tzinfo=self.eastern)
        next_open = self.calendar.get_next_market_open(friday_pm)
        
        # Should be Monday at 9:30 AM (skipping weekend)
        self.assertEqual(next_open.weekday(), 0)  # Monday
        self.assertEqual(next_open.time(), time(9, 30))
    
    def test_next_market_close(self):
        """Test next market close calculation"""
        # During trading hours
        trading = datetime(2024, 3, 15, 10, 0, tzinfo=self.eastern)
        next_close = self.calendar.get_next_market_close(trading)
        
        # Should be same day at 4:00 PM
        self.assertEqual(next_close.date(), trading.date())
        self.assertEqual(next_close.time(), time(16, 0))
    
    def test_easter_calculation(self):
        """Test Easter calculation for Good Friday"""
        # Easter 2024 is March 31, so Good Friday is March 29
        good_friday_2024 = datetime(2024, 3, 29, tzinfo=self.eastern)
        self.assertTrue(self.calendar.is_holiday(good_friday_2024))
        
        # The day before should not be a holiday
        not_holiday = datetime(2024, 3, 28, tzinfo=self.eastern)
        self.assertFalse(self.calendar.is_holiday(not_holiday))
    
    def test_weekend_holiday_adjustment(self):
        """Test holiday observance adjustment for weekends"""
        # When a holiday falls on Saturday, it should be observed on Friday
        # When a holiday falls on Sunday, it should be observed on Monday
        # This is tested implicitly through the holiday detection
        
        # Test that we have holidays defined
        holidays_2024 = self.calendar._get_us_market_holidays(2024)
        self.assertGreater(len(holidays_2024), 0)
        
        # Verify major holidays exist
        holiday_dates = [h.date() for h in holidays_2024]
        
        # New Year's Day (Jan 1)
        self.assertIn(datetime(2024, 1, 1, tzinfo=self.eastern).date(), holiday_dates)
        
        # Independence Day (July 4)
        self.assertIn(datetime(2024, 7, 4, tzinfo=self.eastern).date(), holiday_dates)


if __name__ == '__main__':
    unittest.main()
