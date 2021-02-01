import csv


def insert_csv_file_to_database(path, conn):
    """
    importing csv file to a database.
    Parameters
    ----------
    path: the path to csv file .
    conn: the connection of database.
    """
    cur = conn.cursor()
    array_values_from_file = []
    with open(path, 'r') as f:

        reader = csv.reader(f)
        for row in reader:
            array_values_from_file.append([int(row[0]), row[1]])
            # insert_query = "INSERT INTO project VALUES {}".format(f"({row[0]}, '{row[1]}')")
            cur.execute(insert_query)
        conn.commit()

        return array_values_from_file
