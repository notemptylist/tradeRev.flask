from copy import deepcopy
from datetime import datetime
from flask import current_app, g
from flask_pymongo import PyMongo
from werkzeug.local import LocalProxy
from .utils import flatten_dict, date_fmt
from bson import ObjectId
from bson.errors import InvalidId
from .schemas import TradingWeek

def get_db():
    """Configuration method to return a db instance

    """
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = PyMongo(current_app).db

    return db

db = LocalProxy(get_db)
convert_transactiondate = {
    "$addFields": {
        "openDate": {
            "$dateToString": {
                "format": date_fmt,
                "date": {
                    "$toDate": "$transactiondate"
                }
            }
        }
    }
}
convert_closing_date = {
        "$addFields": {
            "closeDate": {
                "$dateToString": {
                    "date": "$closingdate",
                    "format": f"{date_fmt}"
                }
            }
        }
    }
def get_transaction_by_id(trans_id):
    """Get one transaction by Id.

    This Id is not the mongodb ObjectId, but rather the transaction id as
    defined by the broker API.
    Masks the _id field from output.
    
    Parameters
    ----------
        trans_id : int
    """
    res = db.transactions.find_one({"id": trans_id}, {"_id": 0})
    return res

def get_all_transactions():
    """Get all transactions in the collection
    Masks the _id field.
    """
    res = db.transactions.find({}, {"_id": 0}) \
    .sort([("transactiondate", -1)])
    return res

def get_transactions_by_date(day: str):
    """Get all transactions occuring on the specified day.

    Appends a new field called 'opendate' to each document.

    Parameters
    ----------
        day : str
    """
    match_date = {"$match": {"openDate": f"{day}"}}
    project = {"$project": {"_id": 0}}
    pipeline = [convert_transactiondate, match_date, project]
    res = db.transactions.aggregate(pipeline)
    return res

def get_all_trades():
    """Get all trades in the trades collection.
    """
    return db.trades.find()

def get_trade_by_id(trade_id: str):
    """Get all trades in the trades collection.
    """
    try:
        trade_id = ObjectId(trade_id)
    except InvalidId:
        return None 
    return db.trades.find_one({"_id": trade_id})


def get_opened_trades_by_date(day: str):
    """Get all trades opened on the specified day.

    Appends a new field named 'openDate' to each document.

    Parameters
    ----------
        day : str
    """
    date_convert = {
        "$addFields": {
            "openDate": {
                "$dateToString": {
                    "date": "$openingdate",
                    "format": f"{date_fmt}"
                }
            }
        }
    }
    match_date = {"$match": {"openDate": f"{day}"}}
    pipeline = [date_convert, match_date]
    res = db.trades.aggregate(pipeline)
    return res

def get_closed_trades_by_date_range(start: datetime, end: datetime):
    """Get all trades closed between start and end dates.

    Parameters
    ----------
        start : datetime
        end : datetime
    """
    valid_date = {"$match" : {"closingdate": {"$ne": 0}}}
    match_date = {"$match": {"closingdate": {"$gte": start, "$lte": end}}}

    pipeline = [valid_date, match_date]
    res = db.trades.aggregate(pipeline)
    return list(res)

def get_closed_trades_by_date(day: str):
    """Get all trades closed on the specified day.

    Appends a new field called 'closeDate' to each document.

    Parameters
    ----------
        day : str
    """
    valid_date = {"$match": {"closingdate": {"$ne": 0}}}
    match_date = {"$match": {"closeDate": f"{day}"}}
    project = {"$project": {"_id": 0}}
    pipeline = [valid_date, convert_closing_date, match_date, project]
    res = db.trades.aggregate(pipeline)
    return list(res)

def get_opening_transactions():
    """Get all transactions with openingeffect equal to 'OPENING'
    """
    return get_transactions_by_effect("OPENING")

def get_closing_transactions():
    """Get all transactions with openingeffect equal to 'CLOSING'
    """
    return get_transactions_by_effect("CLOSING")

def get_transactions_by_effect(effect: str):
    """Get transactions with matching positioneffect, mask _id in projection."""
    project = {"$project" : {"_id" : 0}}
    match_open = {"$match" : {"positioneffect": effect}}
    pipeline = [convert_transactiondate, match_open, project]
    res = db.transactions.aggregate(pipeline)
    return list(res)

def get_trades_opening_transaction_ids():
    """Get the transaction ids of trades which are mentioned
    in the openingtransactions subdocument of trades.
    """
    unwind = {"$unwind": "$openingtransactions"}
    newroot = {"$replaceRoot": {"newRoot": "$openingtransactions"}}
    project = {"$project": {"id": 1}}
    pipeline = [unwind, newroot, project]
    res = db.trades.aggregate(pipeline)
    return list(res)

def get_trades_closing_transaction_ids():
    """Get the transaction ids of trades which are mentioned
    in the closingtransactions subdocument of trades.
    """
    unwind = {"$unwind": "$closingtransactions"}
    newroot = {"$replaceRoot": {"newRoot": "$closingtransactions"}}
    project = {"$project": {"id": 1}}
    pipeline = [unwind, newroot, project]
    res = db.trades.aggregate(pipeline)
    return list(res)

def create_trade(trade_doc):
    """Insert a single trade document into collection
    """
    res = db.trades.insert_one(trade_doc)
    return res

def get_open_trade_for_symbol(symbol: str):
    """Get the open trade document for the specified symbol.
    """
    # pick the oldest trade for the symbol which is open
    match = {"$match": {"symbol": symbol, "openamount": {"$gt": 0}}}
    sort = {"$sort": {"openingdate": 1 }}
    limit = {"$limit": 1}
    pipeline = [match, sort, limit]
    res = db.trades.aggregate(pipeline)
    for r in res:
        return r

def close_trade_with_transaction(trade_id, tr):
    """Update the trade document with information from the closing
    transaction.

    Parameters
    ----------
        trade_id : ObjectId of trade
        tr : transaction document
    """
    match = {"_id": trade_id}
    totalfees = tr['optregfee'] + tr['regfee'] + tr['additionalfee'] + \
        tr['cdscfee'] + tr['othercharges'] + tr['rfee'] + tr['secfee']
    update = {
        "$set": {
            "closingdate": tr['transactiondate']
        },
        "$inc": {
            "closingprice": tr['cost'],
            "totalcommission": tr['commission'],
            "totalfees": totalfees,
            "openamount": -tr['amount'],
        },
        "$push": {
            "closingtransactions": {
                "id": tr['id'],
                "amount": tr["amount"]
            }
        },
    }
    db.trades.update_one(match, update)
    return True

def get_transactions_in_order(field='transactiondate', skip=0, limit=None):
    """Return transactions ordered by transactiondate or choicen field.
    Mask the _id field.

    Parameters
    ----------
        field : str A key to sort by
        skip : int Number of records to skip
        limit : int How many records to return

    Returns
    -------
        res : A CommandCursor object
    """
    match = {"processed": { "$ne": 1}}
    res = db.transactions.find(match).sort(field, 1).skip(skip).limit(limit)
    return res

def mark_processed_transaction(trans_id):
    """Mark the transaction as having been processed so it can be filtered out
    """
    update = {"$set": {"processed": 1}}
    res = db.transactions.update_one({"id": trans_id}, update)

def mark_processed_transaction_bulk(trans_ids):
    """Mark the transactions as having been processed.
    """
    match = {"id" : {"$in": trans_ids}}
    update = {"$set": {"processed": 1}}
    return db.transactions.update_many(match, update)

def update_trades_profits():
    """Update the profit fields in trades which are 'closed'
    """
    match = {"openamount" : 0}
    update = [{"$set": {
            "profitdollars": {
                "$sum": ["$openingprice", "$closingprice"]
            }
        }
    }, {"$set": {
            "profitpercent": {
                "$divide": ["$profitdollars", {
                    "$abs": "$openingprice"
                }]
            }
        }
    }]
    return db.trades.update_many(match, update)

def make_trades_toc():
    """Create a collection which serves as a table of contents, organized by year
    and month, for related trades.
    """
    select_dates = {"$match" : {"openingdate": {"$ne": 0}}}
    split_year_month = {
        "$addFields": {
            "year": {
                "$year": "$openingdate"
            },
            "month": {
                "$month": "$openingdate"
            }
        }
    }
    project_dates = {"$project": {"year": 1, "month": 1, "_id": 0}}
    group_dates = {"$group": {"_id": {"year": "$year", "month": "$month"}}}
    sort_dates = {"$sort": {"_id.year": 1, "_id.month": 1}}
    pipeline = [
        select_dates, split_year_month, project_dates, group_dates, sort_dates
    ]
    res = db.trades.aggregate(pipeline)
    flat_list = flatten_dict(list(res), field="_id")

    # TODO: maybe create this permanently and add a unique index
    db.trades_date_toc.drop()
    # NOTE: insert_many() modifies the passed in parameter.
    to_insert = deepcopy(flat_list)
    res = db.trades_date_toc.insert_many(to_insert)
    return flat_list

def add_utility_event(entry):
    """Add the event log entry to the utilitylog collection.
    """
    res = db.utilitylog.insert_one(entry.to_doc())
    return res

def get_utility_events(event_type, event_count):
    """Fetch a number of events of a certain type.
    """
    res = db.utilitylog.find({"logtype": event_type}, {"_id": 0}).sort("timestamp", -1).limit(event_count)
    return res

def get_week_by_date(day):
    """Fetch one week identified by date
    """
    res = db.weeks.find_one({"start_date": day}, {"_id": 0})
    return res

def upsert_week(week: TradingWeek):
    """Insert or update a week document
    """
    update = week.to_update()
    match = {"start_date": week.start_date} 
    return db.weeks.update_one(match, update , upsert=True)

def delete_tag_from_week(day, tag):
    """Delete a single tag from a week document
    """
    match = {"start_date": day}
    update = {"$pull": { "tags": tag}}
    return db.weeks.update_one(match, update)
