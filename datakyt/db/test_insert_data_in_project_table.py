import psycopg2
import csv
import os
import unittest


class TestDB(unittest.TestCase):

    @staticmethod
    def insert_csv_file_to_database(path, conn):
        """
        importing csv file to a database.
        Parameters
        ----------
        path: the path to csv file .
        conn: the connection of database.
        """
        cur = conn.cursor()
        with open(os.path.join(path), 'r') as f:
            reader = csv.reader(f)
            next(reader)
            cont_of_csv = []
            for row in reader:
                cur.execute('INSERT INTO PROJECT VALUES(%s,%s)',
                            row)
                cont_of_csv.append([int(row[0]), row[1]])
                conn.commit()

        return cont_of_csv

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
        path_csv = 'test_project.csv'
        connection = psycopg2.connect("dbname=datakyt user=datakyt_admin password= password host=localhost")
        elem_of_csv = TestDB.insert_csv_file_to_database(path_csv, connection)
        elem_of_table = TestDB.take_all_from_table(connection)
        self.assertEqual(elem_of_csv, elem_of_table)


if __name__ == '__main__':
    unittest.main()
