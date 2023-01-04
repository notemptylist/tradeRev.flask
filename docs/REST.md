### REST api endoints

---

**Transactions**

Operations which we need:  
1. Retrieve all transactions
> GET /api/transactions -> [ ]
2. Retrieve a single transaction by ID (_transactionid_ not _id)
> GET /api/transactions/\<id\> -> { single transaction with id = \<id\>}  
3. Retrieve transactions by date 
> GET /api/transactions/daily/<2006-01-02> -> [ transactions where transactiondate is on specified date ] 
---

**Trades**  
Trades are created from existing transactions.  

1. Run a batch job to update trades from existing transactions.
> POST /api/trades
2. Retrieve all trades
> GET /api/trades -> [ ]
3. Retrieve trades by ID 
> GET /api/trades/\<id\> -> { single trade with id = \<id\>}
4. Retrieve trades opened on specified date
> GET /api/trades/daily/<2006-01-02> -> [ trades which were **opened** on date ]
5. Retrieve trades opened between two dates
> GET /api/trades/dayrange?from=2006-01-02&to=2006-02-01
6. Run a batch job to update the profit fiels of all trades.
> POST /api/trades/profits

---
**Stats** 

1. Compute statistics for the day.
> GET /api/stats/daily/<2006-01-02>
2. Compute and return weekly stats for the week containing the specified day.
> GET /api/stats/weekly<2006-01-02>
3. TBD

