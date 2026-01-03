# Date utilities
from datetime import datetime
from typing import Optional


def parse_date(date_string: str, format: str = "%Y-%m-%d") -> Optional[datetime]:
    """
    Parse date string to datetime object
    """
    try:
        return datetime.strptime(date_string, format)
    except ValueError:
        return None


def format_date(date: datetime, format: str = "%Y-%m-%d") -> str:
    """
    Format datetime object to string
    """
    return date.strftime(format)
