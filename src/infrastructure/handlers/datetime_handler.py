from datetime import datetime, timezone, timedelta

class DateTimeHandler:
    BRAZIL_TZ = timezone(timedelta(hours=-3))  # Brazil GMT-3
    UTC_TZ = timezone.utc
    
    @staticmethod
    def now() -> datetime:
        """Get current time in Brazil (GMT-3)"""
        return datetime.now(DateTimeHandler.BRAZIL_TZ)
    
    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC time"""
        return datetime.now(DateTimeHandler.UTC_TZ)

    @staticmethod
    def to_brazil(dt: datetime) -> datetime:
        """Convert any aware datetime to São Paulo time"""
        return dt.astimezone(DateTimeHandler.BRAZIL_TZ)