import os
from flask import Flask, jsonify, abort
from .db import get_db

def create_app(test_config=None):
    """Flask app factory"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev",
    )
    if test_config: 
        app.config.from_mapping(test_config)
    else:
        app.config.from_pyfile('config.py', silent=True)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    @app.route("/transactions/", methods=["GET"])
    def get_transactions():
        db = get_db()
        res = db.transactions.find({}, {"_id": 0}) \
        .limit(10) \
        .sort([("transactiondate", -1)])

        trans = {"transactions": list(res)}
        return trans

    @app.route("/transactions/<int:trans_id>", methods=["GET"])
    def get_transaction_by_id(trans_id):
        """Get one transaction by Id.

        This Id is not the mongodb ObjectId, but rather the transaction id as defined by the broker API.
        """
        res = get_db().transactions.find_one({"id": trans_id}, {"_id": 0})
        if not res:
            abort(404)

        return res

    @app.route("/transactions/daily/<date>", methods=["GET"])
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
        res = get_db().transactions.aggregate(pipeline)
        if not res:
            abort(404)
        return jsonify(list(res))

    return app