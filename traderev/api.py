from flask import abort, Blueprint, current_app as app
from traderev import db

bp = Blueprint("api", __name__, url_prefix="/api")


def _flatten_dict(mappings, field):
    """Takes in a list of dictionaries and returns a list of
    values which are keyed by `field`.
    """
    return [d[field] for d in mappings]

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
    # Can't think of another place to do this
    db.db.trades.create_index("symbol", background=True)
    db.db.trades.create_index("openingdate", background=True)
    db.db.trades.create_index("closingdate", background=True)
    # TODO:
    # 1. select from transactions all opening transactions
    # 2. select all transaction ids from trades.openingtransactions sub document
    # 3. create trade document
    # 4. insert into trades collection
    # 5. select closing transactions (check for expiration transactions)
    # 6. update trades documents with closing transactions
    opening_trans_trades = db.get_trades_opening_transaction_ids()
    opening_ids = _flatten_dict(opening_trans_trades, "id")
    opening_trans = db.get_opening_transactions()
    inserted_count = 0
    for tr in opening_trans:
        # TODO: Move this logic to db.py, add an agregation stage to filter these out.
        if tr['id'] in opening_ids:
            app.logger.debug("Transaction with ID (%s) already tracked in trades collection.", tr['id'])
            continue
        totalfees = tr['optregfee'] + tr['regfee'] + tr['additionalfee'] + \
            tr['cdscfee'] + tr['othercharges'] + tr['rfee'] + tr['secfee']
        trade_doc = {
            "symbol": tr['symbol'],
            "underlying": tr['underlying'],
            "putcall": tr['putcall'],
            "openingdate": tr['transactiondate'],
            "closingdate": 0,
            "openingprice": tr['cost'],
            "closingprice": 0,
            "profitdollars": 0,
            "profitpercent": 0,
            "totalcommission": tr['commission'],
            "totalfees": totalfees,
            "openingtransactions": [{
                "id": tr['id'],
                "amount": tr['amount']
            }],
            "closingtransactions": [],
            "openamount": tr['amount']
        }
        res = db.create_trade(trade_doc)
        if res:
            inserted_count += 1
            app.logger.debug("Inserted trade %s", res.inserted_id)

    closing_trans_trades = db.get_trades_closing_transaction_ids()
    closing_ids = _flatten_dict(closing_trans_trades, "id")
    all_closing_trans = db.get_closing_transactions()
    updated_count = 0
    for tr in all_closing_trans:
        # TODO: Another way to do this is to select trades which are still in 'open' state
        # and query for transactions which match the symbol of these trades.
        if tr['id'] in closing_ids:
            app.logger.debug("Transaction with ID (%s) already tracked in trades collection.", tr['id'])
            continue
        # ideally only a single trade is open per symbol, this works for options.
        trade = db.get_open_trade_for_symbol(tr['symbol'])
        if not trade:
            app.logger.info("No open trade found for this closing transaction: %s", tr)
            continue
        # app.logger.debug("Found an open trade to close : %s", trade)
        db.close_trade_with_transaction(trade['_id'], tr)
        updated_count += 1

    return f"Inserted {inserted_count} new trades\nUpdated {updated_count} trades."
