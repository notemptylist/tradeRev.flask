import pandas as pd
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
    stats['max_gain_dollars'] = df['profitdollars'].max()
    stats['max_gain_percent'] = df['profitpercent'].max()
    stats['max_loss_dollars'] = df['profitdollars'].min()
    stats['max_loss_percent'] = df['profitpercent'].min()
    stats['pandl'] = df['profitdollars'].sum()
    stats['win_rate'] = len(df[df['profitdollars'] > 0]) / df.shape[0] * 100
    stats['call_count'] = len(df[df['putcall'] == 'CALL'])
    stats['put_count'] = len(df[df['putcall'] == 'PUT'])
    stats['total_commission'] = df['totalcommission'].sum()
    stats['total_fees'] = df['totalfees'].sum()
    if any(df['profitdollars'] <0):
        stats['avg_loss_dollars'] = df[df['profitdollars'] < 0]['profitdollars'].mean()
        stats['avg_loss_percent'] = df[df['profitpercent'] < 0]['profitpercent'].mean()
    stats['truepnl'] = stats['pandl'] - stats['total_commission'] - stats['total_fees']
    return stats