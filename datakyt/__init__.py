import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d[%(process)d:%(thread)d:%(name)s:%(lineno)d] %(levelname)s %('
                           'message)s',
                    datefmt='%Y-%m-%d %I:%M:%S')
