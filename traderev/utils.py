import pandas as pd
from typing import Any, Dict, List, Tuple
from datetime import datetime, timedelta
from dateutil.rrule import rrule, WEEKLY
from flask.json import JSONEncoder
from bson import ObjectId

class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return JSONEncoder.default(self, obj)

date_fmt = "%Y-%m-%d"
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
    date_fmt_slashes = "%Y/%m/%d"

    if isinstance(day, str):
        try:
            day = datetime.strptime(day, date_fmt)
        except ValueError:
            day = datetime.strptime(day, date_fmt_slashes)
    week_start = day - timedelta(day.weekday())
    week_end = week_start + timedelta(days=5)

    return (week_start, week_end)

def compute_basic_stats(df: pd.DataFrame):
    """Computes basic trade statistics from a pandas dataframe.

    Parameters
    ----------
        df : pd.DataFrame

    Returns
    -------
        dict: A dictionary with statistics data
    """
    stats = {}
    stats['total_trades'] = df.shape[0]
    stats['gross_pnl'] = df['profitdollars'].sum()
    stats['call_count'] = len(df[df['putcall'] == 'CALL'])
    stats['put_count'] = len(df[df['putcall'] == 'PUT'])
    stats['total_commission'] = df['totalcommission'].sum()
    stats['total_fees'] = df['totalfees'].sum()

    stats['max_gain_dollars'] = df['profitdollars'].max()
    stats['max_gain_percent'] = df['profitpercent'].max()
    stats['max_loss_dollars'] = 0
    stats['max_loss_percent'] = 0
    stats['avg_loss_percent'] = 0
    stats['avg_loss_dollars'] = 0
    stats['avg_gain_dollars'] = 0
    stats['avg_gain_percent'] = 0

    any_wins = df['profitdollars'] > 0
    winning_trades = df[any_wins]
    stats['win_rate'] = len(winning_trades) / df.shape[0] * 100
    gross_profit = winning_trades['profitdollars'].sum()
    if any(any_wins):
        stats['avg_gain_dollars'] = winning_trades['profitdollars'].mean()
        stats['avg_gain_percent'] = winning_trades['profitpercent'].mean()

    any_loses = df['profitdollars'] < 0
    losing_trades = df[any_loses]
    gross_loss = losing_trades['profitdollars'].sum()
    if any(any_loses):
        stats['max_loss_dollars'] = losing_trades['profitdollars'].min()
        stats['max_loss_percent'] = losing_trades['profitpercent'].min()
        stats['avg_loss_dollars'] = losing_trades['profitdollars'].mean()
        stats['avg_loss_percent'] = losing_trades['profitpercent'].mean()

    stats['profit_factor'] = gross_profit / gross_loss
    stats['total_pnl'] = stats['gross_pnl'] - stats['total_commission'] - stats['total_fees']
    return stats

def weeks_of_year(year: int, until: datetime) -> List[datetime]:
    """Return a list of Monday dates within the given year, up to given date.

    Parameters
    ----------
        year : int Year in int format.
        until : datetime of ending date.
    Returns:
        list[datetime]
    """
    first = datetime(year, 1, 1)
    num_weeks = len(list(rrule(WEEKLY, dtstart=first, until=until)))
    return [datetime.fromisocalendar(year, w, 1) for w in range(1, num_weeks)]