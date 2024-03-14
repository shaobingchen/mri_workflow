import logging
import os


def setup_logging(logdir,subject):

    ##add log level COMMAND
    #COMMAND_LEVEL = 25
    #logging.addLevelName(COMMAND_LEVEL, "COMMAND")
    #def command(self, message, *args, **kws):
    #    if self.isEnabledFor(COMMAND_LEVEL):
    #        self._log(COMMAND_LEVEL, message, args, **kws)
    #logging.Logger.command=command

    try:

        logger = logging.getLogger(subject)
        logger.setLevel("DEBUG")
        subject_logdir=os.path.join(logdir,subject)

        #config handler for log file
        if not os.path.exists(subject_logdir):
            os.makedirs(subject_logdir)
        
        #set format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

        #create haddler
        DEBUG_handler=logging.FileHandler(os.path.join(subject_logdir,"DEBUG"),mode='w')
        INFO_handler=logging.FileHandler(os.path.join(subject_logdir,"INFO"),mode='w')
        ERROR_handler=logging.FileHandler(os.path.join(subject_logdir,"ERROR"),mode='w')
        ERROR_handler_stream = logging.StreamHandler()

        #set format
        DEBUG_handler.setFormatter(formatter)
        INFO_handler.setFormatter(formatter)
        ERROR_handler.setFormatter(formatter)

        #set level
        DEBUG_handler.setLevel("DEBUG")
        INFO_handler.setLevel("INFO")
        ERROR_handler.setLevel("ERROR")
        ERROR_handler_stream.setLevel("ERROR")

        #add handler to logger
        logger.addHandler(DEBUG_handler)
        logger.addHandler(INFO_handler)
        logger.addHandler(ERROR_handler)
        logger.addHandler(ERROR_handler_stream)

    except Exception :
        print(f"Logging setup failed: {Exception}")
        raise
    return logger