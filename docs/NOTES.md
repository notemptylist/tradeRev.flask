
**Trades** 

Trades technically come to be once an opening transaction is made.  
The symbol and opening date are the unique trade key. 

This works for options trades.
(Unless we want to consider subsequent opening transactions as updates to the existing trade.)


**Utility functions**

Regular batch jobs are required as new transactions and trades are added or created, as some of the information required for these tasks will not be immediately available at the time of import.

- Create and update trades by compbining open and close transactions.
- Calculate and Update the profit calculation for trades.
- Update trades with expired options ( we don't get a transaction record for these).

It would be a good idea to keep a log tracking the execution of these.

**Tags and Memos**

Entries and exits in trades and transactions can be labeled/tagged with specific tags. Memos can be used to provide reasons, explanations, including the emotional state at the time and other notes or feedback.  
Memos should also be applicable to weeks, days, trades and even transactions.  It is entirely possible to have memos on non-trading days, such as 'Sideways market, no opportunities today'.  
This means days and weeks need to have their own entities in the database which are not directly attached to trades or transactions.  This has the potential to simplify the data model quite a bit.
Since tags and memos are mutable and applicable to otherwise immutable objects like weeks and days, it makes sense to store these in a separate collection (or multiple collections).
An example of a memo document in db.memos collection:
{
    _id:         ObjectId("63dda881b706c26fa395e5e3"),
    parent_type: "trade",
    parent_id:   Long("39412538560"),
    timestamp:   ISODate("2021-12-15T20:36:09.000Z"),
    text:        "This is a sample memo text", 
}

**OHLC data**
Market data for traded symbols is assumed to be collected and available via a service outside of traderev.  Traderev should be able to receive this data in bulk and by stream. Since this data is only needed by the UI layer, resampling and shaping should be done by the OHLC service.



