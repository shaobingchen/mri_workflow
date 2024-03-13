import logging
import os


def setup_logging(logdir):

    try:
        #add log level COMMAND
        COMMAND_LEVEL = 25
        logging.addLevelName(COMMAND_LEVEL, "COMMAND")
        def command(self, message, *args, **kws):
            if self.isEnabledFor(COMMAND_LEVEL):
                self._log(COMMAND_LEVEL, message, args, **kws)
        logging.Logger.command=command

        logger = logging.getLogger("logger")
        logger.setLevel("DEBUG")


        #config handler for log file
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        DEBUG_handler=logging.FileHandler(os.path.join(logdir,"DEBUG"))
        INFO_handler=logging.FileHandler(os.path.join(logdir,"INFO"))
        
    except Exception :
        print(f"Logging setup failed: {Exception}")
        raise
    return logger