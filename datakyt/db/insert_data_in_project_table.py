import csv
import os


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
