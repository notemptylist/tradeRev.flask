import time
import pandas as pd
from datetime import datetime, timedelta
from flask import abort, Blueprint, current_app as app, make_response, request
from traderev import db
from traderev.utils import (compute_basic_stats,
        date_fmt,
        flatten_dict,
        week_range,
        weeks_of_year,
        )
from traderev.schemas import LogEntryType, UtilityLogEntry, TradingWeek

bp = Blueprint("api", __name__, url_prefix="/api")
@bp.route("/transactions", methods=["GET"])
def transactions():
    res = db.get_all_transactions()
    return list(res)

@bp.route("/transactions/<int:trans_id>", methods=["GET"])
def transaction_by_id(trans_id):
    """Returns a single document representing the transaction specified by ID"""
    try:
        trans_id = int(trans_id)
    except ValueError:
        abort(400)
    res = db.get_transaction_by_id(trans_id)
    if not res:
        abort(404)
    return res

@bp.route("/transactions/daily", methods=["GET"])
def transaction_by_date():
    """List transactions by date.
    """
    try:
        day = request.args['day']
        day = datetime.strptime(day, date_fmt).date()
    except (ValueError, KeyError):
        abort(400)
    res = db.get_transactions_by_date(day)
    if not res:
        abort(404)
    return list(res)

@bp.route("/trades", methods=["GET"])
def get_all_trades():
    """Return all trades.
    """
    res = db.get_all_trades()
    if not res:
        abort(404)
    return list(res)

@bp.route("/trades/<string:trade_id>", methods=["GET"])
def get_trade_by_id(trade_id):
    """Return trade by ID.
    """
    res = db.get_trade_by_id(trade_id)
    if not res:
        abort(404)
    return res 

@bp.route("/trades/daily", methods=["GET"])
def trades_by_date():
    """List trades by specified date.
    """
    try:
        day = request.args['day']
        day = datetime.strptime(day, date_fmt).date()
    except (ValueError, KeyError):
        abort(400)
    if 'opened' in request.args:
        res = db.get_opened_trades_by_date(day)
    elif 'closed' in request.args:
        res = db.get_closed_trades_by_date(day)
    else:
        abort(400)
    if not res:
        abort(404)
    return list(res)

@bp.route("/trades/v2", methods=["POST"])
def update_trades_v2():
    """An alternative way to proces trades.

        1. Go through all transactions in date order
        2. Insert a trade when an opening transaction is encountered.
        3. Close when encountering a closing transaction for the same symbol.
    """
    start_time = time.time()
    # Can't think of another place to do this
    db.db.trades.create_index("symbol", background=True)
    db.db.trades.create_index("openingdate", background=True)
    db.db.trades.create_index("closingdate", background=True)
    if request.data:
        try:
            page_size = request.get_json()['page_size']
        except KeyError:
            page_size = 100
    else:
        page_size = 100
    page = 1
    keep_going = True
    while keep_going:
        ids_to_mark  = []
        ordered_trans = db.get_transactions_in_order(skip=0, limit=page_size)
        app.logger.debug("Processing page: %d", page)
        keep_going = False
        for tr in ordered_trans:
            # should always mark it as processed, nothing else could be done with it
            ids_to_mark.append(tr['id'])
            if tr['positioneffect'] == "OPENING":
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
            elif tr['positioneffect'] == "CLOSING":
                # find the matching open trade for it
                trade = db.get_open_trade_for_symbol(tr['symbol'])
                if trade:
                    db.close_trade_with_transaction(trade['_id'], tr)
                else:
                    app.logger.info("No open trade found for this closing transaction: %d", tr['id'])

        if ids_to_mark:
            keep_going = True
            app.logger.info(f"Marking {len(ids_to_mark)} ids as processed.")
            db.mark_processed_transaction_bulk(ids_to_mark)
        page += 1
    time_elapsed = time.time() - start_time
    return f"Processed {page} pages of {page_size} in {time_elapsed}"

@bp.route("/trades", methods=["POST"])
def update_trades():
    """Update trades collection
    """
    start_time = time.time()
    # Can't think of another place to do this
    db.db.trades.create_index("symbol", background=True)
    db.db.trades.create_index("openingdate", background=True)
    db.db.trades.create_index("closingdate", background=True)
    opening_trans_trades = db.get_trades_opening_transaction_ids()
    opening_ids = flatten_dict(opening_trans_trades, "id")
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
    closing_ids = flatten_dict(closing_trans_trades, "id")
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
    elapsed_time = time.time() - start_time
    message = [
        f"Inserted {inserted_count} new trades",
        f"Updated {updated_count} trades",
        f"Elapsed {elapsed_time:.2f}s",
    ]
    event_entry = UtilityLogEntry(logtype=LogEntryType("Trades"),
                                  timestamp=datetime.utcnow(),
                                  author="/trades API",
                                  message=message)
    db.add_utility_event(event_entry)
    return message

@bp.route("/trades/profits", methods=["POST"])
def update_trade_profits():
    res = db.update_trades_profits()
    output = [
        f"Matched {res.matched_count} trades",
        f"Updated {res.modified_count} trades",
    ]
    event_entry = UtilityLogEntry(logtype=LogEntryType("Profits"),
                                  timestamp=datetime.utcnow(),
                                  author="/trades/profits API",
                                  message=output)
    db.add_utility_event(event_entry)
    return output

@bp.route("/stats/daily/<day>", methods=["GET"])
def daily_stats(day):
    try:
        day = datetime.strptime(day, date_fmt).date()
    except ValueError:
        abort(400)
    trades = db.get_closed_trades_by_date(day)
    if not trades:
        abort(404)
    df = pd.DataFrame(trades)
    stats = {}
    return compute_basic_stats(df)

@bp.route("/stats/weekly", methods=["GET"])
def weekly_stats():
    try:
        week_day = request.args['week']
    except KeyError:
        abort(400)
    try:
        start_date, end_date = week_range(week_day)
    except ValueError:
        abort(400)
    app.logger.debug(f"Grabbing stats between {start_date} and {end_date}")
    trades = db.get_closed_trades_by_date_range(start_date, end_date)
    if not len(trades):
        abort(404)
    df = pd.DataFrame(trades)
    return compute_basic_stats(df)

@bp.route("/utils/datetoc", methods=["POST"])
def make_date_toc():
    res = db.make_trades_toc()
    return make_response(list(res), 202)

@bp.route("/utils/log", methods=["GET"])
def utility_log():
    event_type = request.args['type']
    try:
        event_count = int(request.args['count'])
    except (ValueError, KeyError):
        abort(400)
    if event_count <1:
        abort(400)
    res = db.get_utility_events(event_type, event_count)
    return list(res)

@bp.route("/weeks/<day>", methods=["GET"])
def get_week_by_date(day):
    res = db.get_week_by_date(day)
    if not res:
        abort(404)
    return res

@bp.route("/weeks/yearly", methods=["GET"])
def get_weeks_by_year():
    try:
        year = int(request.args['year'] )
    except (ValueError, KeyError):
        abort(400)

    # If current year then only return up to next week.
    # Otherwise return the full year.
    today = datetime.utcnow().date()
    if today.year == year:
        nextweek = today + timedelta(days=7-today.weekday())
        mondays = weeks_of_year(year, nextweek)
    else:
        mondays = weeks_of_year(year, datetime(year, 12, 31))
    res = []
    for monday in mondays:
        monday_str = datetime.strftime(monday, date_fmt)
        week_obj = TradingWeek(monday_str)
        db_week = db.get_week_by_date(monday_str)
        if db_week:
            week_obj.from_dict(db_week)
        else:
            # lets persist the newly created week object.
            db.upsert_week(week_obj)
        res.append(week_obj.to_doc())
    return res

@bp.route("/weeks/<day>/tags", methods=["POST"])
def add_tag_to_week(day):
    try:
        tag = request.args['tag']
    except KeyError:
        abort(400)
    res = db.get_week_by_date(day)
    week = TradingWeek(day)
    # result from DB is a dictionary, we can construct the object from it.
    if res:
        week.from_dict(res)
    week.add_tag(tag)
    res = db.upsert_week(week)
    if res.modified_count:
        return make_response([], 201)
    return []

