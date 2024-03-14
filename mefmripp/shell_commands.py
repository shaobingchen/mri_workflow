import os
import subprocess
import logging 

class ShellCommand(object):
    '''Class to execute shell commands from python'''
    def __init__(self,command,subject,workdir=None):
        '''Initialize the command'''
        self.command = command
        self.subject = subject
        self.workdir = workdir

    def __str__(self):
        return self.command

    def execute(self):
        '''Execute the command'''

        logger = logging.getLogger(self.subject)
        logger.info(f"Command {self.command} start")
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)


        for line in iter(process.stdout.readline, ''): # b'\n'-separated lines
            logger.debug(f"command's stdout: {line}")
        for line in iter(process.stderr.readline, ''):  # b'\n'-separated lines
            logger.error(f"command's stderr: {line}")

        # Close the process's stdout and stderr 
        process.stdout.close() 
        process.stderr.close()

