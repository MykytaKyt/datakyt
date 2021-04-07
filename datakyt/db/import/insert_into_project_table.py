import csv
import pandas as pd


def insert_into_project_table(path, conn):
    """
    importing csv file to a database, with column
    id and name.
    Parameters
    ----------
    path: the path to csv file .
    conn: the connection of database.


    """
    cur = conn.cursor()
    df = pd.read_csv(path)
    array_values_from_file = []
    with open(path, 'r') as f:

        reader = csv.reader(f)
        for row in reader:
            if len(row) == df.shape[1]:
                array_values_from_file.append([int(row[0]), row[1]])
                insert_query = "INSERT INTO project VALUES {}".format(f"({row[0]}, '{row[1]}')")
                cur.execute(insert_query)
        conn.commit()

    return array_values_from_file
