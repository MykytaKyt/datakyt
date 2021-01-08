import psycopg2
import csv
import os
import unittest
from unittest import TestCase


class TestDB(unittest.TestCase):

    @staticmethod
    def insert_csv_file_to_database(path, conn):
        """
      # importing csv file to a database.

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
                cur.execute('INSERT INTO project VALUES (%s, %s)',
                            row
                            )
                cont_of_csv.append([int(row[0]), row[1]])

                conn.commit()
        return cont_of_csv

    @staticmethod
    def select_from_project(conn):
        """
      # Take all information from project table.

       Parameters
       ----------
       conn: the connection of database.
       """
        cur = conn.cursor()
        cur.execute("SELECT * FROM project")
        rows = cur.fetchall()
        cont_of_db = []
        for row in rows:
            cont_of_db.append([row[0], row[1]])
        conn.commit()
        return cont_of_db

    def test_db(self):
        """
        Compares array values from csv file and values
        written in the database
        """
        cont_of_csv = TestDB.insert_csv_file_to_database(csv_file_path, conn)
        cont_of_db = TestDB.select_from_project(conn)

        self.assertEqual(cont_of_csv, cont_of_db)


if __name__ == "__main__":
    csv_file_path = "test_project.csv"
    conn = psycopg2.connect(dbname='datakyt', user='datakyt_admin',
                            password='password', host='localhost')
    cur = conn.cursor()
    unittest.main()
