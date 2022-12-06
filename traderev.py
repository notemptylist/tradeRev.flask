import database as db
from flask import abort, Flask, jsonify
import pymongo

app = Flask(__name__)

@app.route("/transactions/", methods=["GET"])
def get_transactions():
    res = db.trans_col.find({}, {"_id": 0}) \
    .limit(10) \
    .sort([("transactiondate", pymongo.DESCENDING)])

    trans = {"transactions": list(res)}
    return trans

@app.route("/transactions/<int:trans_id>", methods=["GET"])
def get_transaction_by_id(trans_id):
    """Get one transaction by Id.

    This Id is not the mongodb ObjectId, but rather the transaction id as defined by the broker API.
    """
    res = db.trans_col.find_one({"id": trans_id}, {"_id": 0})
    if not res:
        abort(404)

    return res

@app.route("/daily/<date>", methods=["GET"])
def get_transaction_by_date(date):
    """List transactions by date.
    """
    # Convert from timestamp string to date
    dateconvert = {
        "$addFields": {
            "openDate": {
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
    match_date = { "$match" : { "openDate" : f"{date}" }}
    pipeline = [dateconvert, match_date, project]
    res = db.trans_col.aggregate(pipeline)
    if not res:
        abort(404)
    return jsonify(list(res))