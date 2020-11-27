import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d[%(process)d:%(thread)d:%(name)s:%(lineno)d] %(levelname)s %('
                           'message)s',
                    datefmt='%Y-%m-%d %I:%M:%S')


def backup_postgres_db(host, database_name, port, user, password, test_file):
    """
  Backup postgres db to a file.

   Parameters
   ----------
   host: the host to connect to (default localhost).
   database_name: the name of database.
   port: the port to connect on (default 5432).
   user: the user account to connect as (default admin).
   password: the password for the user account to connect as.
   test_file: the name of the file in which it will be stored back up.

  """
    try:
        process = subprocess.Popen(
            ['pg_dump',
             '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database_name),
             '-Fc',
             '-f', test_file,
             '-v'],
            stdout=subprocess.PIPE
        )
        process.communicate()
        if int(process.returncode) != 0:
            raise RuntimeError('Command failed. Return code : {}'.format(process.returncode))

    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    time = datetime.now()
    time = time.strftime("%m-%d-%Y-%H_%M")
    dump_path = f'backup_datakyt_{time}.sql'


    backup_postgres_db('localhost', 'datakyt', '5432', 'datakyt_admin', 'password', dump_path)
