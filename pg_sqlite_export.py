import os
import datetime

import psycopg2 as pg
from psycopg2 import sql
from psycopg2.extensions import AsIs


class PgSqliteExport:
    def __init__(self, db_name, user, pw, host, port):
        self.cxn_string = '''dbname={db} 
                             user={user} 
                             password={pw} 
                             host={host} 
                             port={port}
                          '''.format(db=db_name, 
                                     user=user,
                                     pw=pw,
                                     host=host,
                                     port=port)
        self.db = pg.connect(self.cxn_string)
        self.db.autocommit = True
        cwd = os.getcwd()
        self.output_file = '{cwd}/pgdb_export.sql'.format(cwd=cwd)
        self._write_header()

    def __name__(self):
        return 'pg_sqlite_export'
    
    def _close(self):
        self.db.close()
        self._write_footer()

    def export_pg_data(self):
        self._get_all_tables()
        self._get_all_table_data()
        self._close()

    def _get_all_tables(self):
        curs = self.db.cursor()
        stmt = """
            SELECT table_name 
              FROM information_schema.tables 
             WHERE table_schema = 'public' 
               AND table_type = 'BASE TABLE';
        """
        curs.execute(stmt)
        self.tables = [row[0] for row in curs]
        curs.close()

    def _get_all_table_data(self):
        curs = self.db.cursor()
        stmt = """
            SELECT * 
              FROM %(tbl)s;
        """
        for table in self.tables:
            self._write_deletes(table)
            curs.execute(stmt, {'tbl': AsIs(table)})
            results = curs.fetchall()
            for row in results:
                insert_stmt = self._format_line(table, row)
                self._write_sql(insert_stmt)
        curs.close()

    def _convert_dates(self, value):
        if isinstance(value, datetime.date):
            value = value.strftime('%Y-%m-%d')
        # TODO: Add other checks here, like datetime, timestamp, etc
        return value

    def _format_line(self, table, values):
        stmt = sql.SQL("INSERT INTO {tbl} VALUES ({vals});\n").format(
            tbl=sql.Identifier(table), 
            vals=sql.SQL(', ').join(
                sql.Literal(self._convert_dates(element)) for element in values)
            )
        return stmt.as_string(self.db)

    def _write_sql(self, stmt):
        with open(self.output_file, 'a') as file:
            file.write(stmt)
            file.close()

    def _write_header(self):
        stmt = 'PRAGMA foreign_keys=0;\nBEGIN;\n'
        with open(self.output_file, 'w+') as file:
            file.write(stmt)
            file.close()

    def _write_deletes(self, table):
        stmt = sql.SQL('DELETE FROM {tbl};\n').format(tbl=sql.Identifier(table)).as_string(self.db)
        with open(self.output_file, 'a') as file:
            file.write(stmt)
            file.close()

    def _write_footer(self):
        stmt = 'COMMIT;'
        with open(self.output_file, 'a') as file:
            file.write(stmt)
            file.close()
        