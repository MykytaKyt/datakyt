import os
import psycopg2
import logging
import pandas as pd

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d[%(process)d:%(thread)d:%(name)s:%(lineno)d] %(levelname)s %('
                           'message)s',
                    datefmt='%Y-%m-%d %I:%M:%S')


def execute_query(query: str, connection, is_select_query=False):
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        if is_select_query:
            result = pd.DataFrame(cursor.fetchall())
            if len(result):
                result.columns = [desc[0] for desc in cursor.description]
            cursor.close()
            return result
    except Exception as exception:
        LOG.error(f'{exception}:\n{query}')


def export_to_csv(data: pd.DataFrame, filepath: str, index=False, header=True):
    try:
        data.to_csv(filepath, index=index, header=header)
        LOG.info(f'Exported to {filepath}')
    except Exception as exception:
        LOG.error(exception)


if __name__ == '__main__':
    project_dir = os.getcwd()
    data_dir_path = os.path.join(project_dir, 'queries')
    data_dir_path = os.path.join(data_dir_path, 'tests')
    export_file_path = os.path.join(data_dir_path, 'test_export.csv')
    connection = psycopg2.connect(dbname='datakyt', user='datakyt_admin', host='localhost', password='')
    result = execute_query(query='select current_date', connection=connection, is_select_query=True)
    print(result)
    result = execute_query(query='select * from project', connection=connection, is_select_query=True)
    export_to_csv(data=result, filepath=export_file_path)