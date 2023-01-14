
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