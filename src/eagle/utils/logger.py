import logging
import os
class Logger:
    def __init__(self, file):
        self.logger = logging.getLogger()
        stream_handler = logging.StreamHandler()
        self.file_name = os.path.basename(file)

        if len(self.logger.handlers) == 0:
            # StreamHandler
            formatter = logging.Formatter(u'[%(levelname)s] %(asctime)s  %(message)s')
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            self.logger.addHandler(stream_handler)
            self.logger.setLevel(logging.INFO)

    def info(self, msg):
        self.logger.info("%s (%s)" % (str(msg), self.file_name))

    def error(self, msg):
        self.logger.error("%s (%s)" % (str(msg), self.file_name))

    def warning(self, msg):
        self.logger.warning("%s (%s)" % (str(msg), self.file_name))
