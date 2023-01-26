
### REST API endoints

---

## Resources

1. Transactions - Transactions are the individual processed orders.
1. Trades - Trades are the result of a group of transactions (Sell + Buy, Buy + Sell)
1. Stats - Statistics for days and weeks.
1. Weeks - Calendar weeks in which transactions and trades occur.
1. Days - Days in which transactions and trades occur.

Other endpoints
1. Utils - A collection of APIs which don't map well to the other resources.

### Transactions

With the exception of tags, individual properties of Transactions are immutable.

1. Retrieve all transactions.   
```GET /api/transactions -> [ ]```
3. Retrieve a single transaction by ID (_transactionid_ not _id).   
```GET /api/transactions/{id} -> a single transaction with id = {id} ``` 
1. Retrieve transactions by date.  
```GET /api/transactions/daily?day={2006-01-02} -> [ transactions where transactiondate is on specified date ] ```
1. Add a tag to a transaction by ID.  
```POST /api/transactions/{id}/tags  <- { 'tag': 'foobar'} ```
1. Remove a tag from a transaction.  
```DELETE /api/transactions/{id}/tags <- { 'tag': 'tagtoremove' }```
---

### Trades

Trades are formed from existing transactions.  With the exception of tags, individual properties of Trades are immutable.

1. Run a batch job to update trades from existing transactions.  
```POST /api/trades```
3. Retrieve all trades.  
```GET /api/trades -> [ ]```
4. Retrieve trades by ID.   
```GET /api/trades/{id} -> single trade with id = {id}```
5. Retrieve trades opened on specified date.  
```GET /api/trades/daily?day={2006-01-02} -> [ trades which were **closed** on date ]```
6. Retrieve trades closed between two dates.  
```GET /api/trades/dayrange?from=2006-01-02&to=2006-02-01```
7. Run a batch job to update the profit fiels of all trades.  
```POST /api/trades/profits```
8. Add a tag to a trade by ID.  
```POST /api/trades/{id}/tags  <- { 'tag': 'important'}``` 
9. Remove a tag from a trade object.     
```DELETE /api/trades/{id}/tags <- { 'tag': 'extraneous' }```

---

### Stats

1. Compute statistics for the day.   
```GET /api/stats/daily?day={2006-01-02}```
1. Compute and return weekly stats for the week containing the specified day.  
```GET /api/stats/weekly?week={2006-01-02}```
1. TBD

---

### Weeks

Weeks are identified by the Monday date.  
```
    { 
      'start_date': '2022-01-01',
      'end_date': '2022-01-05',
      'tags': ['tag1', 'superb', 'red'],
      'memos':[
          {
            'id': 123123123123,
            'timestamp': '2022-01-01:12:30',
            'memo': 'This is a memo',
          },
        ]
    }            
```
1. Get one week.  
```GET /api/weeks/{week_day}```
3. Get a list of weeks for the given year.  
```GET /api/weeks/yearly?year=2022 -> [list of weeks]```
1. Get the week containing a single date.  
```GET /api/weeks/daily?day=2022-01-06```
1. Add a tag to a specific week.    
```POST /api/weeks/{week_day}/tags <- {'tag': 'foobar'}```
1. Remove a specific tag from a week.  
```DELETE /api/weeks/{week_day}/tags <- {'tag': 'tagtoremove'}```
1. Add a memo to a specific week.    
```POST /api/weeks/{week_day}/memos <- {'memo': 'A sample memo' }```
1. Remove a memo from a specific week by memo id.  
```DELETE /api/weeks/{week_day}/memos/<id>```
---

### Days

```
    {
      'day': '2022-01-03',
      'tags': ['green', 'range']
       'memos':[
          {
            'id': 1266623123,
            'timestamp': '2022-01-01:01:30',
            'memo': 'This is was a range day',
          },
        ]
    }
```

1. Get a specific trading day.  
```GET /api/days/{2022-01-06}```
1. Add a tag to a specific day.  
```POST /api/days/{day}/tags <- {'tag': 'foobar'}```
1. Remove a specific tag from a day.  
```DELETE /api/days/{day}/tags <- {'tag': 'tagtoremove'}```
1. Add a memo to a specific day.  
```POST /api/days/{day}/memos <- {'memo': 'A sample memo' }```
1. Remove a memo from a specific day by memo id.  
```DELETE /api/days/{day}/memos/<id>```


---

### Utils

1. Create and return a date based table of contents.  
```POST /utils/datetoc -> [{'year':2022, 'month': 10}, ...]```
1. Get entries from the utilitylog.  
```GET /utils/log?type={import|profits|trades}?count=5```

