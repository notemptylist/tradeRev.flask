from flask import current_app, g
from flask_pymongo import PyMongo
from werkzeug.local import LocalProxy
from typing import List

def get_db():
    """Configuration method to return a db instance

    """
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = PyMongo(current_app).db

    return db

db = LocalProxy(get_db)
date_fmt = "%Y-%m-%d"
dateconvert = {
    "$addFields": {
        "opendate": {
            "$dateToString": {
                "format": date_fmt,
                "date": {
                    "$toDate": "$transactiondate"
                }
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
    trans : int
    """
    res = db.transactions.find({"id": trans_id}, {"_id": 0})
    return res

def get_all_transactions():
    """Get all transactions in the collection
    Masks the _id field.
    """
    res = db.transactions.find({}, {"_id": 0}) \
    .sort([("transactiondate", -1)])
    return list(res)

def get_transactions_by_date(day):
    """Get all transactions occuring on the specified day.

    Appends a new field called 'opendate' to each document.

    Parameters
    ----------
    day : string
    """
    # Convert from timestamp string to date

    # drop the _id field so we don't have to encode the ObjectId
    project = {"$project": {"_id": 0}}
    match_date = {"$match": {"opendate": f"{day}"}}
    pipeline = [dateconvert, match_date, project]
    res = get_db().transactions.aggregate(pipeline)
    return list(res)

def get_opening_transactions():
    """Get all transactions with openingeffect equal to 'OPENING'
    """
    return get_transactions_by_effect("OPENING")

def get_closing_transactions():
    """Get all transactions with openingeffect equal to 'CLOSING'
    """
    return get_transactions_by_effect("CLOSING")

def get_transactions_by_effect(effect):
    """Get transactions with matching positioneffect, mask _id in projection."""
    project = {"$project" : {"_id" : 0}}
    match_open = {"$match" : {"positioneffect": effect}}
    pipeline = [dateconvert, match_open, project]
    # XXX: remove limit
    # limit = {"$limit": 100}
    # pipeline = [dateconvert, match_open, limit, project]
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

def get_open_trade_for_symbol(symbol):
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
                'id': tr['id'],
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
