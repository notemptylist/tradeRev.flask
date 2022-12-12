from flask import abort, Blueprint
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
    # 2. create trade document
    # 3. insert into trades collection
    # 4. select closing transactions (check for expiration transactions)
    # 5. update trades documents with closing transactions
