from import_data.common import *

"""
Function that records the log - initiate logger
"""
def setup_logging(log_inst_name):
    
    logger = logging.getLogger(log_inst_name)
    
    # If there is a logger handler corresponding to the name passed as a parameter, delete the logger and then create a new handler.   
    if logger.hasHandlers():
        for handler in logger.handlers[:]:
            # After checking whether it is a FileHandler object or a TimedRotatingFileHandler object, if either type is correct, DELETE the handler.
            if isinstance(handler, logging.FileHandler) or isinstance(handler, logging.handlers.TimedRotatingFileHandler):
                logger.removeHandler(handler)
                handler.close()
    
    log_filename = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.handlers.TimedRotatingFileHandler(f'./data/log/{log_filename}.log', when="midnight", backupCount=10)
    file_handler.setFormatter(logging.Formatter('[ %(asctime)s ] %(levelname)s : %(message)s'))

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger