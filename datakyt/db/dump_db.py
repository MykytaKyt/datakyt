import subprocess


def backup_postgres_db(host, database_name, port, user, password, dest_file):
    """
  Backup postgres db to a file.
  """
    try:
        process = subprocess.Popen(
            ['pg_dump',
             '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database_name),
             '-Fc',
             '-f', dest_file,
             '-v'],
            stdout=subprocess.PIPE
        )
        output = process.communicate()[0]
        if int(process.returncode) != 0:
            print('Command failed. Return code : {}'.format(process.returncode))
            exit(1)
        return output
    except Exception as e:
        print(e)


if __name__ == '__main__':
    backup_postgres_db('localhost', 'datakyt', '5432', 'datakyt_admin', 'password', 'out2.txt')
