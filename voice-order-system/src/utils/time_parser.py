"""
Relative time expression parser.

Converts relative time expressions to absolute ISO 8601 timestamps.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class TimeParser:
    """
    Parses relative time expressions and converts to ISO 8601 timestamps.
    
    Supports:
    - "in 30 minutes", "in 2 hours"
    - "tomorrow", "today"
    - "at 5pm", "at 17:00"
    - "tomorrow at 3pm"
    """

    def __init__(self, timezone: str = "Asia/Kolkata"):
        """
        Initialize time parser.

        Args:
            timezone: Timezone for timestamp conversion (default: Asia/Kolkata for India)
        """
        self.timezone = ZoneInfo(timezone)
        logger.info("TimeParser initialized with timezone=%s", timezone)

    def parse(self, time_expression: str) -> Optional[str]:
        """
        Parse relative time expression to ISO 8601 timestamp.

        Args:
            time_expression: Natural language time expression

        Returns:
            ISO 8601 timestamp string or None if parsing fails
        """
        if not time_expression:
            return None

        time_expr = time_expression.lower().strip()
        now = datetime.now(self.timezone)

        try:
            # Pattern: "in X minutes/hours"
            match = re.search(r'in\s+(\d+)\s+(minute|minutes|hour|hours)', time_expr)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                if 'minute' in unit:
                    target_time = now + timedelta(minutes=value)
                else:  # hours
                    target_time = now + timedelta(hours=value)
                
                return target_time.isoformat()

            # Pattern: "tomorrow"
            if 'tomorrow' in time_expr:
                target_time = now + timedelta(days=1)
                
                # Check for time specification
                time_match = re.search(r'at\s+(\d+)\s*(am|pm)?', time_expr)
                if time_match:
                    hour = int(time_match.group(1))
                    period = time_match.group(2)
                    
                    if period == 'pm' and hour < 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    
                    target_time = target_time.replace(hour=hour, minute=0, second=0, microsecond=0)
                else:
                    # Default to noon
                    target_time = target_time.replace(hour=12, minute=0, second=0, microsecond=0)
                
                return target_time.isoformat()

            # Pattern: "today at X"
            if 'today' in time_expr:
                time_match = re.search(r'at\s+(\d+)\s*(am|pm)?', time_expr)
                if time_match:
                    hour = int(time_match.group(1))
                    period = time_match.group(2)
                    
                    if period == 'pm' and hour < 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    
                    target_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                    return target_time.isoformat()

            # Pattern: "at Xpm/am" (today)
            time_match = re.search(r'at\s+(\d+)\s*(am|pm)', time_expr)
            if time_match:
                hour = int(time_match.group(1))
                period = time_match.group(2)
                
                if period == 'pm' and hour < 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                
                target_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # If time has passed today, assume tomorrow
                if target_time < now:
                    target_time += timedelta(days=1)
                
                return target_time.isoformat()

            # Pattern: "at HH:MM" (24-hour format)
            time_match = re.search(r'at\s+(\d+):(\d+)', time_expr)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                
                target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If time has passed today, assume tomorrow
                if target_time < now:
                    target_time += timedelta(days=1)
                
                return target_time.isoformat()

            logger.warning("Could not parse time expression: %s", time_expression)
            return None

        except Exception as e:
            logger.error("Error parsing time expression '%s': %s", time_expression, e)
            return None
