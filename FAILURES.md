\# Known Failure Modes



1\. \*\*Process crash during an in-flight DM\*\*

&#x20;  

&#x20;  A DM job is persisted in the database before being placed in the in-memory queue. If the process crashes while a job is being processed, the job may require recovery or reconciliation depending on the exact point of failure.



2\. \*\*External acceptance followed by local failure\*\*

&#x20;  

&#x20;  PseudoGram may accept a DM while the application fails before persisting the returned PseudoGram DM ID. This can make the local database temporarily differ from the external delivery state. The idempotency key reduces the risk of sending the same DM twice.



3\. \*\*External API delivery-state mismatch\*\*

&#x20;  

&#x20;  If PseudoGram is temporarily unavailable while delivery status is being reconciled, the local DM status may temporarily differ from the actual external status.



4\. \*\*Statistics during active processing\*\*

&#x20;  

&#x20;  `/stats` is calculated from the current database state. During active processing, counts can change between requests and may temporarily differ from the final external delivery state until queued and accepted DMs are reconciled.

