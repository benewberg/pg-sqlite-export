# Postgres SQLite Exporter

Export all Postgres table data in a given database as INSERT statements compatible with SQLite3 into a file.
This file can then be imported into an SQLite database, containing the same schema.

This utility mimics the behavior of the official SQLite3 CLI's `.mode INSERT` command.

Usage:

```
from pg_sqlite_exporter import PgSQLiteExporter

db = 'my_db'
user = 'user_name'
pw = 'my_pw'
host = '127.0.0.1'
port = '5432'

xptr = PgSQLiteExporter(db_name=db, user=user, pw=pw, host=host, port=port)
xptr.export_pg_data()
```

The output file will be written to the current working directory and be named pgdb_export.sql.


create table tbl1 (x integer primary key, y text, dt date, n numeric);
insert into tbl1 values (1, 'a', '2018-08-20'::date, 123.45), (2, 'b', '2018-08-21'::date, 2000.00), (3, 'c', '2018-08-22'::date, 999.99);

create table tbl2 (col1 integer not null, col2 text not null default '', col3 date default now(), col4 numeric, primary key(col1, col2));
insert into tbl2 values (100, 'abc', NULL, 123.456), (200, 'def', '2018-08-20'::date, 987.65), (100, 'xyz', NULL, NULL);