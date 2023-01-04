from typing import Any, Dict, List, Tuple
from datetime import datetime, timedelta

def flatten_dict(mappings: List[Dict], field: str) -> List[Any]:
    """Takes in a list of dictionaries and returns a list of
    values which are keyed by `field`.

    Parameters
    ----------
        mappings : A list of dictionaries.
        field : A string representing the key to select.

    Returns
    -------
        list : A list of values
    """
    return [d[field] for d in mappings]

def week_range(day: str) -> Tuple[datetime, datetime]:
    """Returns a range of dates defining a week which contains the day.

    Parameters
    ----------
        day : str (expected to be in 'YYYY-MM-DD' or 'YYYY/MM/DD' format)

    Returns
    -------
        tuple : A tuple with two datetime objects
    """
    date_fmt_dashes = "%Y-%m-%d"
    date_fmt_slashes = "%Y/%m/%d"

    if isinstance(day, str):
        try:
            day = datetime.strptime(day, date_fmt_dashes)
        except ValueError:
            day = datetime.strptime(day, date_fmt_slashes)
    week_start = day.date() - timedelta(day.weekday())
    week_end = week_start + timedelta(days=5)

    return (week_start, week_end) 