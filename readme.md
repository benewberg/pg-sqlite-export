# Postgres SQLite Exporter

Export all Postgres table data in a given database as INSERT statements compatible with SQLite3 into a file.
This file can then be imported into an SQLite database, containing the same schema.

Similar to Postgres's `pg_dump` command, but compatible with SQLite3.
This utility mimics the behavior of the official SQLite3 CLI's `.mode INSERT` command.

Usage:

```
from pg_sqlite_export import PgSqliteExport

db = 'test'
user = 'test'
pw = 'test'
host = 'localhost'
port = '5432'

xptr = PgSqliteExport(db_name=db, user=user, pw=pw, host=host, port=port)
xptr.export_pg_data()
```

The output file will be written to the current working directory and be named pgdb_export.sql.

Create test data in Postgres test database:
```
CREATE TABLE tbl1 (
	x INTEGER PRIMARY KEY, 
	y TEXT, 
	dt DATE, 
	n NUMERIC
);
INSERT INTO tbl1 VALUES 
	(1, 'a', '2018-08-20'::date, 123.45), 
	(2, 'b', '2018-08-21'::date, 2000.00), 
	(3, 'c', '2018-08-22'::date, 999.99);

CREATE TABLE tbl2 (
	col1 INTEGER NOT NULL, 
	col2 TEXT NOT NULL DEFAULT '', 
	col3 DATE DEFAULT now(), 
	col4 NUMERIC(12,4), 
	PRIMARY KEY(col1, col2)
);
INSERT INTO tbl2 VALUES 
	(100, 'abc', NULL, 123.456), 
	(200, 'def', '2018-08-20'::date, 987.65), 
	(100, 'xyz', NULL, NULL);
```

Expected output using the above sample data:
```
PRAGMA foreign_keys=0;
BEGIN;
DELETE FROM "tbl1";
INSERT INTO "tbl1" VALUES (1, 'a', '2018-08-20', 123.45);
INSERT INTO "tbl1" VALUES (2, 'b', '2018-08-21', 2000.00);
INSERT INTO "tbl1" VALUES (3, 'c', '2018-08-22', 999.99);
DELETE FROM "tbl2";
INSERT INTO "tbl2" VALUES (100, 'abc', NULL, 123.456);
INSERT INTO "tbl2" VALUES (200, 'def', '2018-08-20', 987.65);
INSERT INTO "tbl2" VALUES (100, 'xyz', NULL, NULL);
COMMIT;
```