# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os


def setup_logging(conf):
    """
    Initialize the logging module settings
    :param conf: dict, Initialize parameters
    :return:
    """
    level = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING,
             "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}

    console = conf['console']  # console output
    console_level = conf['console_level']  # choose console log level to print
    file = conf['file']  # local log file output
    file_level = conf['file_level']  # choose log file level to save
    logfile = conf['log_file']  # local log file save position
    backup_count = conf['backup_count']  # count of local log files
    max_size = conf['max_size']  # size of each local log file
    format_string = conf['format_string']  # log message format

    log = logging.getLogger('ak_modbus')
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter(format_string, datefmt='%Y-%d-%m %H:%M:%S')

    if file:
        # create logs directory if doesn't exist
        dir_path = os.path.dirname(logfile)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # instantiate a rotate file handler to output log file
        fh = logging.handlers.RotatingFileHandler(filename=logfile, mode='a', maxBytes=max_size,
                                                  backupCount=backup_count, encoding='utf-8')
        fh.setLevel(level[file_level])
        fh.setFormatter(formatter)
        log.addHandler(fh)

    if console:
        # instantiate a stream handler to output log file in console
        ch = logging.StreamHandler()
        ch.setLevel(level[console_level])
        ch.setFormatter(formatter)
        log.addHandler(ch)
