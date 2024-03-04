import logging

def setup_logging(logdir):

    try:
        #add log level COMMAND
        COMMAND_LEVEL = 25
        logging.addLevelName(COMMAND_LEVEL, "COMMAND")
        def command(self, message, *args, **kws):
            if self.isEnabledFor(COMMAND_LEVEL):
                self._log(COMMAND_LEVEL, message, args, **kws)
        logging.logger.command=command

        logger = logging.getLogger()
        logger.setLevel()
        #config handler for log file
        file_handler=logging.FileHandler()
        
        
    except Exception :
        print(f"Logging setup failed: {Exception}")
        raise
    return logger