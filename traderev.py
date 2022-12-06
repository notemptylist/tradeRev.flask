import database as db
from flask import Flask, jsonify
import pymongo

app = Flask(__name__)

@app.route("/transactions")
def get_transactions():
    res = db.trans_col.find({}, {"_id": 0}) \
    .limit(10) \
    .sort([("transactiondate", pymongo.DESCENDING)])

    trans = {"transactions": list(res)}
    return jsonify(trans)