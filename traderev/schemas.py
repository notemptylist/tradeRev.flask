"""Some document collections will have a strict structure.
"""
from enum import Enum
from datetime import datetime

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

    def toDoc(self):
        """Build the document object.
        """
        return {
            "logtype": self.logtype.value,
            "timestamp": self.timestamp,
            "author": self.author,
            "message": self.message
        }