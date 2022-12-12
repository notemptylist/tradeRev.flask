from flask import abort, Blueprint, current_app as app
from traderev import db

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/transactions/", methods=["GET"])
def transactions():
    res = db.get_all_transactions()
    return res

@bp.route("/transactions/<int:trans_id>", methods=["GET"])
def transaction_by_id(trans_id):
    """Returns a single document representing the transaction specified by ID"""
    try:
        trans_id = int(trans_id)
    except ValueError:
        return None
    res = db.get_transaction_by_id(trans_id)
    return res

@bp.route("/transactions/daily/<date>", methods=["GET"])
def transaction_by_date(date):
    """List transactions by date.
    """
    from datetime import datetime
    try:
        day = datetime.strptime(date, db.date_fmt).date()
    except ValueError:
        abort(400)
    res = db.get_transactions_by_date(day)
    if not res:
        abort(404)
    return res

@bp.route("/trades", methods=["POST"])
def update_trades():
    """Update trades collection
    """
    # TODO:
    # 1. select from transactions all opening transactions
    # 2. select all transaction ids from trades.openingtransactions sub document
    # 3. create trade document
    # 4. insert into trades collection
    # 5. select closing transactions (check for expiration transactions)
    # 6. update trades documents with closing transactions
    import pprint
    opening_trans_trades = db.get_trades_opening_transaction_ids()
    opening_ids = [doc['id'] for doc in opening_trans_trades]
    opening_trans = db.get_opening_transactions()
    inserted_count = 0
    for tr in opening_trans:
        if tr['id'] in opening_ids:
            app.logger.info("Transaction with ID (%s) already tracked in trades collection.", tr['id'])
            continue
        trade_doc = {
            'symbol': tr['symbol'],
            'underlying': tr['underlying'],
            'putcall': tr['putcall'],
            'openingdate': tr['opendate'],
            'openingtransactions': [{
                'id': tr['id'],
                'amount': tr['amount']
            }],
            'closingtransaction': [],
            'openamount': tr['amount']
        }
        res = db.create_trade(trade_doc)
        if res:
            inserted_count += 1
            app.logger.info("Inserted trade %s", res.inserted_id)

    return f"Inserted {inserted_count} new trades"
