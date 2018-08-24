import unittest

from pg_sqlite_export import PgSqliteExport


class TestPgSqliteExport(unittest.TestCase):
	def setUp(self):
		self.testee = PgSqliteExport(db_name='test', 
                            user='test',
                            pw='test',
                            host='localhost',
                            port='5432')

	def tearDown(self):
		self.testee._close()

	def test_name(self):
		self.assertEqual('pg_sqlite_export', self.testee.__name__())


if __name__ == '__main__':
    unittest.main()
