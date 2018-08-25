import os
import datetime
import unittest

# from psycopg2 import sql
from psycopg2.extensions import AsIs

from pg_sqlite_export import PgSqliteExport

EXPECTED_HEADER = "PRAGMA foreign_keys=0;\nBEGIN;\n"
EXPECTED_FOOTER = "COMMIT;"
EXPECTED_BODY = "DELETE FROM \"tbl1\";\n" \
				"INSERT INTO \"tbl1\" VALUES (1, 'a', '2018-08-20', 123.45);\n" \
				"INSERT INTO \"tbl1\" VALUES (2, 'b', '2018-08-21', 2000.00);\n" \
				"INSERT INTO \"tbl1\" VALUES (3, 'c', '2018-08-22', 999.99);\n" \
				"DELETE FROM \"tbl2\";\n" \
				"INSERT INTO \"tbl2\" VALUES (100, 'abc', NULL, 123.4560);\n" \
				"INSERT INTO \"tbl2\" VALUES (200, 'def', '2018-08-20', 987.6500);\n" \
				"INSERT INTO \"tbl2\" VALUES (100, 'xyz', NULL, NULL);\n"


class TestPgSqliteExport(unittest.TestCase):
	def setUp(self):
		self.testee = PgSqliteExport(db_name='test', 
                            user='test',
                            pw='test',
                            host='localhost',
                            port='5432')

	def tearDown(self):
		self.testee._close()

	def drop_test_tables(self, tables):
		sql = "DROP TABLE IF EXISTS %(tbl)s;"
		curs = self.testee.db.cursor()
		for table in tables:
			curs.execute(sql, {'tbl': AsIs(table)})

	def get_all_test_tables(self):
		sql = """
			SELECT table_name 
			  FROM information_schema.tables
			 WHERE table_catalog = 'test'
			   AND table_schema = 'public';
		"""
		curs = self.testee.db.cursor()
		curs.execute(sql)
		tables = [tbl[0] for tbl in curs]
		curs.close()
		return tables

	def setup_test_data(self):
		test_tables = self.get_all_test_tables()
		self.drop_test_tables(test_tables)
		sql = """
			CREATE TABLE tbl1 (
				x INTEGER PRIMARY KEY, 
				y TEXT, 
				dt DATE, 
				n NUMERIC
			);
			CREATE TABLE tbl2 (
				col1 INTEGER NOT NULL, 
				col2 TEXT NOT NULL DEFAULT '', 
				col3 DATE DEFAULT now(), 
				col4 NUMERIC(12,4), 
				PRIMARY KEY(col1, col2)
			);
			INSERT INTO tbl1 VALUES 
				(1, 'a', '2018-08-20'::date, 123.45), 
				(2, 'b', '2018-08-21'::date, 2000.00), 
				(3, 'c', '2018-08-22'::date, 999.99);
			INSERT INTO tbl2 VALUES 
				(100, 'abc', NULL, 123.456), 
				(200, 'def', '2018-08-20'::date, 987.65), 
				(100, 'xyz', NULL, NULL);
		"""
		curs = self.testee.db.cursor()
		curs.execute(sql)
		curs.close()

	def get_output_file_path(self):
		cwd = os.getcwd()
		output_file = '{cwd}/pgdb_export.sql'.format(cwd=cwd)
		return output_file

	def read_file_contents(self, file_path):
		input_file = open(file_path, 'r')
		file_contents = ''
		for line in input_file:
			file_contents += line
		return file_contents

	def test_name(self):
		self.assertEqual('pg_sqlite_export', self.testee.__name__())

	def test_db_connection_open(self):
		db_is_closed = 0
		self.assertEqual(db_is_closed, self.testee.db.closed, 
			'The database connection is not open.')

	def test_db_connection_closed(self):
		db_is_closed = 1
		self.testee._close()
		self.assertEqual(db_is_closed, self.testee.db.closed,
			'The database connection is not closed.')

	def test_create_output_file(self):
		output_file = self.get_output_file_path()
		try:
			os.unlink(output_file)
		except OSError as ex:
			pass
		self.testee._create_output_file()
		self.assertTrue(os.path.exists(output_file), 
			'The output file at the path {path} does not exist.'.format(path=output_file))

	def test_output_file_header(self):
		self.testee._create_output_file()
		output_file = self.get_output_file_path()
		actual_header = self.read_file_contents(output_file)
		self.assertMultiLineEqual(EXPECTED_HEADER, actual_header)

	def test_get_all_tables(self):
		self.setup_test_data()
		self.testee._get_all_tables()
		actual_tables = self.testee.tables
		expected_tables = ['tbl1', 'tbl2']
		self.assertItemsEqual(expected_tables, actual_tables)

	def test_convert_dates(self):
		unconverted_date = datetime.date(2018, 8, 1)
		expected_date = '2018-08-01'
		actual_date = self.testee._convert_dates(unconverted_date)
		self.assertEqual(expected_date, actual_date)

	def test_format_line(self):
		table = 'test_table'
		values = (1, 'abc', datetime.date(2018, 8, 1), 123.45)
		expected_line = "INSERT INTO \"test_table\" VALUES (1, 'abc', '2018-08-01', 123.45);\n"
		actual_line = self.testee._format_line(table, values)
		self.assertEqual(expected_line, actual_line)

	def test_write_sql(self):
		stmt = "INSERT INTO \"test_table\" VALUES (1, 'abc', '2018-08-01', 123.45);\n"
		self.testee._create_output_file()
		self.testee._write_sql(stmt)
		expected_contents = '{hdr}{stmt}'.format(hdr=EXPECTED_HEADER, stmt=stmt)
		actual_contents = self.read_file_contents(self.get_output_file_path())
		self.assertMultiLineEqual(expected_contents, actual_contents)

	def test_write_deletes(self):
		stmt = "DELETE FROM \"test_table\";\n"
		self.testee._create_output_file()
		self.testee._write_deletes('test_table')
		expected_contents = '{hdr}{stmt}'.format(hdr=EXPECTED_HEADER, stmt=stmt)
		actual_contents = self.read_file_contents(self.get_output_file_path())
		self.assertMultiLineEqual(expected_contents, actual_contents)

	def test_write_footer(self):
		self.testee._create_output_file()
		self.testee._write_footer()
		expected_contents = '{hdr}{ftr}'.format(hdr=EXPECTED_HEADER, ftr=EXPECTED_FOOTER)
		actual_contents = self.read_file_contents(self.get_output_file_path())
		self.assertMultiLineEqual(expected_contents, actual_contents)

	def test_end_to_end(self):
		self.testee.export_pg_data()
		expected_contents = '{hdr}{body}{ftr}'.format(hdr=EXPECTED_HEADER, body=EXPECTED_BODY, ftr=EXPECTED_FOOTER)
		actual_contents = self.read_file_contents(self.get_output_file_path())
		self.maxDiff = None
		self.assertMultiLineEqual(expected_contents, actual_contents)		

if __name__ == '__main__':
    run_tests = raw_input("WARNING! These tests will drop all public tables in the test database. Continue? (y/N):")
    if run_tests.lower() == 'y' or run_tests.lower() == 'yes':
		unittest.main()
