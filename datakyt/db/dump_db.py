import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d[%(process)d:%(thread)d:%(name)s:%(lineno)d] %(levelname)s %('
                           'message)s',
                    datefmt='%Y-%m-%d %I:%M:%S')


def backup_postgres_db(database_name, host,  port, user, password, backup_file_path):
    """
  Backup postgres db to a file.

   Parameters
   ----------
   host: the host to connect to .
   database_name: the name of database.
   port: the port to connect on .
   user: the user account to connect as .
   password: the password for the user account to connect as.
   backup_file_path: the name of the file in which it will be stored back up.

  """
    try:
        process = subprocess.Popen(
            ['pg_dump',
             '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database_name),
             '-Fc',
             '-f', backup_file_path,
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
    backup_postgres_db('datakyt', 'localhost', '5432', 'datakyt_admin', 'password', dump_path)
