from flask import abort, Blueprint

from traderev.db import get_db

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/transactions/", methods=["GET"])
def get_transactions():
    db = get_db()
    res = db.transactions.find({}, {"_id": 0}) \
    .limit(10) \
    .sort([("transactiondate", -1)])

    return list(res)

@bp.route("/transactions/<int:trans_id>", methods=["GET"])
def get_transaction_by_id(trans_id):
    """Get one transaction by Id.

    This Id is not the mongodb ObjectId, but rather the transaction id as defined by the broker API.
    """
    res = get_db().transactions.find_one({"id": trans_id}, {"_id": 0})
    if not res:
        abort(404)

    return res

@bp.route("/transactions/daily/<date>", methods=["GET"])
def get_transaction_by_date(date):
    """List transactions by date.
    """
    # Convert from timestamp string to date
    dateconvert = {
        "$addFields": {
            "opendate": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": {
                        "$toDate": "$transactiondate"
                    }
                }
            }
        }
    }
    #match_open = {"$match" : { "positioneffect": "OPENING" }}

    # drop the _id field so we don't have to encode the ObjectId
    project = { "$project" : { "_id" : 0 }}
    match_date = { "$match" : { "opendate" : f"{date}" }}
    pipeline = [dateconvert, match_date, project]
    res = get_db().transactions.aggregate(pipeline)
    if not res:
        abort(404)
    return list(res)

@bp.route("/trades", methods=["POST"])
def update_trades():
    """Update trades collection
    """
    # TODO:
    # 1. select from transactions all opening transactions
    # 2. create trade document
    # 3. insert into trades collection
    # 4. select closing transactions (check if expiration transactions )