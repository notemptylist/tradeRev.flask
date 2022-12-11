### REST api endoints

---

**Transactions**

Operations which we need:
1. Retrieve transactions
> GET /api/transactions -> [ ]
2. Retrieve transactions by ID (_transactionid_ not _id)
> GET /api/transactions/\<id\> -> { single transaction with id = \<id\>}  
3. Retrieve transactions by date 
> GET /api/transactions/daily/<2006-01-02> -> [ transactions where transactiondate is on specified date ] 
---

**Trades**  
Trades are created from existing transactions.  

1. Update trades from existing transactions.
> POST /api/trades
2. Retrieve all trades
> GET /api/trades -> [ ]
3. Retrieve trades by ID 
> GET /api/trades/\<id\> -> { single trade with id = \<id\>}
4. Retrieve trades opened on specified date
> GET /api/trades/daily/<2006-01-02> -> [ trades which were **opened** on date ]

---
**Stats** 

1. Transactions per day
> GET /api/stats/<2006-01-02> -> Count of transaction made that day  

TBD

