import psycopg2
import csv
import os


def insert_csv_file_to_database(path, conn):
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
        cur.close()
        conn.close()

    return cont_of_csv


if __name__ == '__main__':
    path_csv = 'test_project.csv'
    connection = psycopg2.connect(dbname='datakyt', user='datakyt_admin',
                                  password='password', host='localhost')
    cursor = connection.cursor()
