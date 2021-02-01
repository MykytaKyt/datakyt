import sqlite3
import unittest
from insert_data_in_project_table import insert_csv_file_to_database


class TestDB(unittest.TestCase):

    @staticmethod
    def take_all_from_table(conn):
        """
        Take all information from project table.
        Parameters
        ----------
        conn: the connection of database.
        """
        cur = conn.cursor()
        cont_of_table = []
        cur.execute('SELECT * FROM project')
        for row in cur:
            cont_of_table.append([row[0], row[1]])
        conn.commit()

        return cont_of_table

    def test_db(self):
        """
        Compares array values from csv file and values
        written in the database
        """
        path_to_csv = 'test_project.csv'
        path_to_db = 'test_database.db'
        connection = sqlite3.connect(path_to_db)
        elem_of_csv = insert_csv_file_to_database(path_to_csv, connection)
        elem_of_table = TestDB.take_all_from_table(connection)
        self.assertEqual(elem_of_csv, elem_of_table)


if __name__ == '__main__':
    unittest.main()
