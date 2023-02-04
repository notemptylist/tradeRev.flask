"""Some document collections will have a strict structure.
"""
import json
from datetime import timedelta
from enum import Enum
from datetime import datetime
from .utils import date_fmt

class LogEntryType(Enum):
    Import = "Import" # import of transactions
    Profits = "Profits" # Update of profits
    Trades = "Trades" # Creation or update of trades

class UtilityLogEntry():

    def __init__(self, logtype: LogEntryType, timestamp: datetime = None, message: str = None, author: str = None ):
        """
        Parameters:
        logtype (LogEntryType): One of the enumerated log entry types.
        timestamp (datetime): Timestamp of the event.
        message (str): Arbitrary message describing the event.
        author (str): Identifier of the person or system that initiated the event.
        """
        self.logtype = logtype
        self.timestamp = timestamp or datetime.utcnow()
        self.author = author
        self.message = message

    def to_doc(self):
        """Build the document object.
        """
        return {
            'logtype': self.logtype.value,
            'timestamp': self.timestamp,
            'author': self.author,
            'message': self.message
        }


def get_dates_between(start, end):
    """Generate a list of dates between two dates, including start and end.
    """
    if isinstance(start, str):
        start = datetime.strptime(start, date_fmt)
    if isinstance(end, str):
        end = datetime.strptime(end, date_fmt)

    date_list = []
    current = start
    while current <= end:
        date_list.append(current.strftime(date_fmt))
        current += timedelta(days=1)
    return date_list

class TradingWeek():

    def __init__(self, monday: str):
        """Construct a trading week representation
        """
        self.start_date = monday
        # to get friday's date we add 4 days to monday
        monday_dt = datetime.strptime(monday, date_fmt)
        friday = monday_dt + timedelta(days=4)
        self.weekdays = get_dates_between(monday, friday) 
        self.end_date = datetime.strftime(friday, date_fmt)
        self.tags = []
        self.memos = []

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def to_doc(self):
        """Return a JSON serializeable dictionary representation
        """
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'tags': self.tags,
            'memos': self.memos,
            }

    def from_dict(self, d: dict):
        self.start_date = d['start_date']
        self.end_date = d['end_date']
        self.tags = d['tags']
        self.memos = d['memos']
        self.weekdays = d['weekdays']

    def to_update(self):
        """Return an update document
        """
        update = { "$set" : { 
            'end_date': self.end_date,
            'tags' : self.tags,
            'memos': self.memos,
            'weekdays': self.weekdays,
            }
        }
        return update

