import logging



def configure_and_get_logger(filename, levelname=logging.DEBUG):
    '''
    return logger which will log in following format on console as well as log on a file.

    2018-12-30 15:10:26,618 DEBUG - debug message
    2018-12-30 15:10:26,620 INFO - info message
    2018-12-30 15:10:26,695 WARNING - warn message
    2018-12-30 15:10:26,697 ERROR - error message
    2018-12-30 15:10:26,773 CRITICAL - critical message
    '''

    #create or get a log file with filename
    logging.basicConfig(filename=filename ,level=levelname, format="%(asctime)s - %(levelname)s - %(message)s")

    # create logger
    logger = logging.getLogger(filename)
    logger.setLevel(levelname)

    # create console handler and set level to levelname
    ch = logging.StreamHandler()
    ch.setLevel(levelname)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    return logger
