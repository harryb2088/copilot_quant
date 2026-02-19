"""
Market Calendar Module

Provides NYSE market hours and US holiday detection for trading orchestration.

Features:
- Detect if market is currently open
- Get current market state (PRE_MARKET, TRADING, POST_MARKET, CLOSED)
- US holiday calendar (NYSE holidays)
- Market session times (9:30 AM - 4:00 PM ET)
- Pre-market and post-market detection
"""

import logging
from datetime import datetime, time, timedelta
from enum import Enum
from typing import List, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class MarketState(Enum):
    """Market state enumeration"""

    PRE_MARKET = "pre_market"  # Before 9:30 AM ET on trading day
    TRADING = "trading"  # 9:30 AM - 4:00 PM ET
    POST_MARKET = "post_market"  # After 4:00 PM ET on trading day
    CLOSED = "closed"  # Weekend or holiday


class MarketCalendar:
    """
    NYSE Market Calendar with holiday detection.

    Provides market state detection based on NYSE trading hours:
    - Regular trading: 9:30 AM - 4:00 PM ET
    - Pre-market: 4:00 AM - 9:30 AM ET
    - Post-market: 4:00 PM - 8:00 PM ET

    Includes US market holidays (NYSE observance).

    Example:
        >>> calendar = MarketCalendar()
        >>> state = calendar.get_market_state()
        >>> if state == MarketState.TRADING:
        ...     print("Market is open for trading")
        >>> is_open = calendar.is_market_open()
    """

    # NYSE regular trading hours (Eastern Time)
    MARKET_OPEN_TIME = time(9, 30)  # 9:30 AM
    MARKET_CLOSE_TIME = time(16, 0)  # 4:00 PM

    # Extended hours
    PRE_MARKET_START = time(4, 0)  # 4:00 AM
    POST_MARKET_END = time(20, 0)  # 8:00 PM

    # Timezone
    MARKET_TIMEZONE = ZoneInfo("America/New_York")

    def __init__(self, timezone: Optional[str] = None):
        """
        Initialize market calendar.

        Args:
            timezone: Optional timezone string (e.g., "America/New_York").
                     Defaults to US Eastern Time.
        """
        if timezone:
            self.timezone = ZoneInfo(timezone)
        else:
            self.timezone = self.MARKET_TIMEZONE

        logger.info(f"MarketCalendar initialized with timezone: {self.timezone}")

    def _get_us_market_holidays(self, year: int) -> List[datetime]:
        """
        Get list of NYSE market holidays for a given year.

        NYSE observes the following holidays:
        - New Year's Day
        - Martin Luther King Jr. Day (3rd Monday in January)
        - Presidents' Day (3rd Monday in February)
        - Good Friday (Friday before Easter)
        - Memorial Day (last Monday in May)
        - Juneteenth (June 19)
        - Independence Day (July 4)
        - Labor Day (1st Monday in September)
        - Thanksgiving Day (4th Thursday in November)
        - Christmas Day (December 25)

        Args:
            year: Year to get holidays for

        Returns:
            List of datetime objects representing holidays
        """
        holidays = []

        # New Year's Day (or observed date if weekend)
        new_years = datetime(year, 1, 1, tzinfo=self.timezone)
        holidays.append(self._adjust_for_weekend(new_years))

        # Martin Luther King Jr. Day (3rd Monday in January)
        mlk_day = self._nth_weekday(year, 1, 0, 3)  # 0 = Monday
        holidays.append(mlk_day)

        # Presidents' Day (3rd Monday in February)
        presidents_day = self._nth_weekday(year, 2, 0, 3)
        holidays.append(presidents_day)

        # Good Friday - requires Easter calculation
        easter = self._calculate_easter(year)
        good_friday = easter - timedelta(days=2)
        holidays.append(good_friday)

        # Memorial Day (last Monday in May)
        memorial_day = self._last_weekday(year, 5, 0)
        holidays.append(memorial_day)

        # Juneteenth (June 19, observed if weekend)
        juneteenth = datetime(year, 6, 19, tzinfo=self.timezone)
        holidays.append(self._adjust_for_weekend(juneteenth))

        # Independence Day (July 4, observed if weekend)
        independence_day = datetime(year, 7, 4, tzinfo=self.timezone)
        holidays.append(self._adjust_for_weekend(independence_day))

        # Labor Day (1st Monday in September)
        labor_day = self._nth_weekday(year, 9, 0, 1)
        holidays.append(labor_day)

        # Thanksgiving (4th Thursday in November)
        thanksgiving = self._nth_weekday(year, 11, 3, 4)  # 3 = Thursday
        holidays.append(thanksgiving)

        # Christmas (December 25, observed if weekend)
        christmas = datetime(year, 12, 25, tzinfo=self.timezone)
        holidays.append(self._adjust_for_weekend(christmas))

        return holidays

    def _nth_weekday(self, year: int, month: int, weekday: int, n: int) -> datetime:
        """
        Find the nth occurrence of a weekday in a given month.

        Args:
            year: Year
            month: Month (1-12)
            weekday: Weekday (0=Monday, 6=Sunday)
            n: Which occurrence (1=first, 2=second, etc.)

        Returns:
            datetime object for the nth weekday
        """
        first_day = datetime(year, month, 1, tzinfo=self.timezone)
        first_weekday = first_day.weekday()

        # Calculate offset to first occurrence of desired weekday
        offset = (weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=offset)

        # Add weeks to get to nth occurrence
        nth_occurrence = first_occurrence + timedelta(weeks=n - 1)

        return nth_occurrence

    def _last_weekday(self, year: int, month: int, weekday: int) -> datetime:
        """
        Find the last occurrence of a weekday in a given month.

        Args:
            year: Year
            month: Month (1-12)
            weekday: Weekday (0=Monday, 6=Sunday)

        Returns:
            datetime object for the last weekday
        """
        # Start from last day of month
        if month == 12:
            last_day = datetime(year + 1, 1, 1, tzinfo=self.timezone) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1, tzinfo=self.timezone) - timedelta(days=1)

        # Work backwards to find the last occurrence of the weekday
        while last_day.weekday() != weekday:
            last_day -= timedelta(days=1)

        return last_day

    def _calculate_easter(self, year: int) -> datetime:
        """
        Calculate Easter Sunday using the Computus algorithm (Anonymous Gregorian algorithm).

        Args:
            year: Year to calculate Easter for

        Returns:
            datetime object for Easter Sunday
        """
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        day_offset = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * day_offset) // 451
        month = (h + day_offset - 7 * m + 114) // 31
        day = ((h + day_offset - 7 * m + 114) % 31) + 1

        return datetime(year, month, day, tzinfo=self.timezone)

    def _adjust_for_weekend(self, date: datetime) -> datetime:
        """
        Adjust holiday observation if it falls on a weekend.
        If Saturday, observe on Friday. If Sunday, observe on Monday.

        Args:
            date: The original holiday date

        Returns:
            Adjusted date for NYSE observance
        """
        if date.weekday() == 5:  # Saturday
            return date - timedelta(days=1)
        elif date.weekday() == 6:  # Sunday
            return date + timedelta(days=1)
        return date

    def is_holiday(self, date: Optional[datetime] = None) -> bool:
        """
        Check if a given date is a market holiday.

        Args:
            date: Date to check. Defaults to today.

        Returns:
            True if the date is a market holiday
        """
        if date is None:
            date = datetime.now(self.timezone)

        # Ensure date has timezone
        if date.tzinfo is None:
            date = date.replace(tzinfo=self.timezone)
        else:
            date = date.astimezone(self.timezone)

        # Get holidays for this year
        holidays = self._get_us_market_holidays(date.year)

        # Check if date matches any holiday (compare date only, not time)
        date_only = date.date()
        for holiday in holidays:
            if holiday.date() == date_only:
                return True

        return False

    def is_weekend(self, date: Optional[datetime] = None) -> bool:
        """
        Check if a given date is a weekend.

        Args:
            date: Date to check. Defaults to today.

        Returns:
            True if the date is Saturday or Sunday
        """
        if date is None:
            date = datetime.now(self.timezone)

        # Ensure date has timezone
        if date.tzinfo is None:
            date = date.replace(tzinfo=self.timezone)
        else:
            date = date.astimezone(self.timezone)

        # 5 = Saturday, 6 = Sunday
        return date.weekday() in [5, 6]

    def is_trading_day(self, date: Optional[datetime] = None) -> bool:
        """
        Check if a given date is a trading day (not weekend or holiday).

        Args:
            date: Date to check. Defaults to today.

        Returns:
            True if the date is a trading day
        """
        return not (self.is_weekend(date) or self.is_holiday(date))

    def is_market_open(self, now: Optional[datetime] = None) -> bool:
        """
        Check if the market is currently open for regular trading.

        Args:
            now: Time to check. Defaults to current time.

        Returns:
            True if market is open for regular trading (9:30 AM - 4:00 PM ET)
        """
        if now is None:
            now = datetime.now(self.timezone)

        # Ensure we're in the right timezone
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.timezone)
        else:
            now = now.astimezone(self.timezone)

        # Check if it's a trading day
        if not self.is_trading_day(now):
            return False

        # Check if within trading hours
        current_time = now.time()
        return self.MARKET_OPEN_TIME <= current_time < self.MARKET_CLOSE_TIME

    def get_market_state(self, now: Optional[datetime] = None) -> MarketState:
        """
        Get the current market state.

        Args:
            now: Time to check. Defaults to current time.

        Returns:
            MarketState enum value
        """
        if now is None:
            now = datetime.now(self.timezone)

        # Ensure we're in the right timezone
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.timezone)
        else:
            now = now.astimezone(self.timezone)

        # If not a trading day, market is closed
        if not self.is_trading_day(now):
            return MarketState.CLOSED

        # Check time of day
        current_time = now.time()

        if current_time < self.MARKET_OPEN_TIME:
            return MarketState.PRE_MARKET
        elif current_time < self.MARKET_CLOSE_TIME:
            return MarketState.TRADING
        else:
            return MarketState.POST_MARKET

    def get_next_market_open(self, now: Optional[datetime] = None) -> datetime:
        """
        Get the next market open time.

        Args:
            now: Current time. Defaults to now.

        Returns:
            datetime of next market open (9:30 AM ET)
        """
        if now is None:
            now = datetime.now(self.timezone)

        # Ensure we're in the right timezone
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.timezone)
        else:
            now = now.astimezone(self.timezone)

        # Start from today at market open time
        next_open = datetime.combine(now.date(), self.MARKET_OPEN_TIME, tzinfo=self.timezone)

        # If we're past market open today, start from tomorrow
        if now.time() >= self.MARKET_OPEN_TIME:
            next_open += timedelta(days=1)

        # Keep incrementing until we find a trading day
        while not self.is_trading_day(next_open):
            next_open += timedelta(days=1)

        return next_open

    def get_next_market_close(self, now: Optional[datetime] = None) -> datetime:
        """
        Get the next market close time.

        Args:
            now: Current time. Defaults to now.

        Returns:
            datetime of next market close (4:00 PM ET)
        """
        if now is None:
            now = datetime.now(self.timezone)

        # Ensure we're in the right timezone
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.timezone)
        else:
            now = now.astimezone(self.timezone)

        # Start from today at market close time
        next_close = datetime.combine(now.date(), self.MARKET_CLOSE_TIME, tzinfo=self.timezone)

        # If not a trading day or we're past close time, move to next day
        if not self.is_trading_day(now) or now.time() >= self.MARKET_CLOSE_TIME:
            next_close += timedelta(days=1)
            while not self.is_trading_day(next_close):
                next_close += timedelta(days=1)

        return next_close
