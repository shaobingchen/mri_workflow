import logging
import os


def setup_logging(logdir):

    ##add log level COMMAND
    #COMMAND_LEVEL = 25
    #logging.addLevelName(COMMAND_LEVEL, "COMMAND")
    #def command(self, message, *args, **kws):
    #    if self.isEnabledFor(COMMAND_LEVEL):
    #        self._log(COMMAND_LEVEL, message, args, **kws)
    #logging.Logger.command=command

    try:

        logger = logging.getLogger("logger")
        logger.setLevel("DEBUG")

        #config handler for log file
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        #create haddler
        DEBUG_handler=logging.FileHandler(os.path.join(logdir,"DEBUG"))
        INFO_handler=logging.FileHandler(os.path.join(logdir,"INFO"))
        ERROR_handler=logging.FileHandler(os.path.join(logdir,"ERROR"))
        ERROR_handler_stream = logging.StreamHandler()        
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