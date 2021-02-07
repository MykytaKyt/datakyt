import sqlite3
import unittest
import os
from sqlite3 import Error
from insert_data_in_project_table import insert_csv_file_to_database


class TestDB(unittest.TestCase):

    @staticmethod
    def create_connection(db_file):
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)

        return conn

    @staticmethod
    def create_table(conn, create_table_sql):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    @staticmethod
    def create_database():
        path_to_db = r'test_data/test_database.db'

        sql_create_projects_table = """ CREATE TABLE project(
                                             id SMALLSERIAL  PRIMARY KEY,
                                             name text  NOT NULL
                                        );"""

        sql_create_offices_table = """CREATE TABLE office(
                                             id SMALLSERIAL  PRIMARY KEY,
                                             city text       NOT NULL
                                    );"""

        sql_create_employees_table = """CREATE TABLE employee(
                                            id SMALLSERIAL  PRIMARY KEY,
                                            name text       NOT NULL,
                                            email char(65)  UNIQUE,
                                            phone varchar(65) UNIQUE,
                                            project_id	SMALLSERIAL CONSTRAINT project_id_fk REFERENCES project (id)
                                            ON DELETE CASCADE,
                                            office_id	SMALLSERIAL CONSTRAINT office_id_fk REFERENCES office (id)
                                            ON DELETE CASCADE
                                         );"""

        sql_create_equipment_type_table = """CREATE TABLE equipment_type(
                                          id          SMALLSERIAL     PRIMARY KEY,
                                          name        text            UNIQUE
                                          );"""

        sql_create_equipment_table = """CREATE TABLE equipment(
                                        id                  SMALLSERIAL    PRIMARY KEY,
                                        name                text           NOT NULL,
                                        warranty            integer        NOT NULL,
                                        cost                money          NOT NULL CHECK (cost > 0),
                                        status              varchar(10)    NOT NULL
                                             CONSTRAINT status_check CHECK(status IN('issued','on reserve','in repair','broken')),
                                        description         text,
                                        purchase_date       date           NOT NULL,
                                        serial_number       varchar(65)    NOT NULL,
                                        equipment_type_id	SMALLSERIAL
                                            CONSTRAINT equipment_type_id_fk REFERENCES equipment_type(id) ON DELETE CASCADE
                                        );"""

        sql_create_equipment_part_table = """CREATE TABLE equipment_part(
                                        id              SMALLSERIAL     PRIMARY KEY,
                                        name            text            UNIQUE,
                                        equipment_id	SMALLSERIAL
                                             CONSTRAINT equipment_id_fk REFERENCES equipment(id) ON DELETE CASCADE
                                        );"""

        sql_create_software_table = """CREATE TABLE software(
                                        id      SMALLSERIAL	 PRIMARY KEY,
                                        name    text         NOT NULL
                                        );"""

        sql_create_software_license_table = """CREATE TABLE software_license(
                                        id                  SMALLSERIAL	PRIMARY KEY,
                                        software_id         SMALLSERIAL
                                            CONSTRAINT software_id_fk REFERENCES software(id) ON DELETE CASCADE,
                                        product_key         text        UNIQUE,
                                        date_of_purchase    date        NOT NULL,
                                        date_of_expiry	    date        NOT NULL
                                        );"""

        sql_create_employee_sw_license_table = """CREATE TABLE employee_sw_license(
                                            id                  SMALLSERIAL 	PRIMARY KEY,
                                            date_of_issue       date            NOT NULL,
                                            employee_id         SMALLSERIAL
                                                CONSTRAINT employee_id_fk REFERENCES employee(id) ON DELETE CASCADE,
                                            software_license_id	SMALLSERIAL
                                                CONSTRAINT software_license_id_fk REFERENCES software_license(id) ON DELETE CASCADE
                                            );"""
        sql_create_furniture_type_table = """CREATE TABLE furniture_type(
                                            id      SMALLSERIAL     PRIMARY KEY,
                                            type    text            UNIQUE
                                            );"""

        sql_create_furniture_table = """CREATE TABLE furniture(
                                            id                  SMALLSERIAL	PRIMARY KEY,
                                            furniture_type_id   SMALLSERIAL
                                                CONSTRAINT furniture_type_id_fk REFERENCES furniture_type (id) ON DELETE CASCADE,
                                            name                text        NOT NULL,
                                            warranty            integer	    NOT NULL,
                                            cost                money 	    NOT NULL CHECK (cost > 0)
                                            );"""

        sql_create_employee_furniture_table = """CREATE TABLE employee_furniture(
                                            id	            SMALLSERIAL     PRIMARY KEY,
                                            date_of_issue   date            NOT NULL,
                                            furniture_id    SMALLSERIAL
                                                CONSTRAINT furniture_id_fk REFERENCES furniture (id) ON DELETE CASCADE,
                                            employee_id	    SMALLSERIAL
                                                CONSTRAINT employee_id_fk REFERENCES employee (id) ON DELETE CASCADE
                                            );"""

        sql_create_employee_equipment_table = """CREATE TABLE employee_equipment(
                                            id                  SMALLSERIAL     PRIMARY KEY,
                                            employee_id         SMALLSERIAL
                                                CONSTRAINT employee_id_fk REFERENCES employee(id) ON DELETE CASCADE,
                                            equipment_id        SMALLSERIAL
                                                CONSTRAINT equipment_id_fk REFERENCES equipment(id) ON DELETE CASCADE,
                                            date_of_issue       date            NOT NULL,
                                            day_of_return       date
                                            );"""

        # create a database connection
        conn = TestDB.create_connection(path_to_db)

        # create tables
        if conn is not None:
            # create projects table
            TestDB.create_table(conn, sql_create_projects_table)

            # create office table
            TestDB.create_table(conn, sql_create_offices_table)

            # create employee table
            TestDB.create_table(conn, sql_create_employees_table)

            # create equipment_type table
            TestDB.create_table(conn, sql_create_equipment_type_table)

            # create equipment table
            TestDB.create_table(conn, sql_create_equipment_table)

            # create equipment_part table
            TestDB.create_table(conn, sql_create_equipment_part_table)

            # create software table
            TestDB.create_table(conn, sql_create_software_table)

            # create software_license table
            TestDB.create_table(conn, sql_create_software_license_table)

            # create employee_sw_license table
            TestDB.create_table(conn, sql_create_employee_sw_license_table)

            # create furniture_type table
            TestDB.create_table(conn, sql_create_furniture_type_table)

            # create furniture table
            TestDB.create_table(conn, sql_create_furniture_table)

            # create employee_furniture table
            TestDB.create_table(conn, sql_create_employee_furniture_table)

            # create employee_equipment table
            TestDB.create_table(conn, sql_create_employee_equipment_table)

        else:
            print("Error! cannot create the database connection.")

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

    @staticmethod
    def drop_database(path):
        table = ['project', 'office', 'employee', 'equipment_type', 'equipment', 'equipment_part',
                 'software', 'software_license', 'employee_sw_license', 'furniture_type', 'furniture',
                 'employee_furniture', 'employee_equipment']
        conn = TestDB.create_connection(path)
        c = conn.cursor()
        for t in table:
            c.execute(f'DROP TABLE {t};')


    def test_db(self):
        """
        Compares array values from csv file and values
        written in the database
        """
        dirname = os.path.dirname(__file__)
        path_to_csv = os.path.join(dirname, 'test_data/test_project.csv')
        path_to_db = os.path.join(dirname, 'test_data/test_database.db')
        TestDB.drop_database(path_to_db)
        TestDB.create_database()
        connection = TestDB.create_connection(path_to_db)
        elem_of_csv = insert_csv_file_to_database(path_to_csv, connection)
        elem_of_table = TestDB.take_all_from_table(connection)
        self.assertEqual(elem_of_csv, elem_of_table)






if __name__ == '__main__':
    unittest.main()

