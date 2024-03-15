import os
import subprocess
import logging 

class ShellCommand(object):
    '''Class to execute shell commands from python'''
    def __init__(self,command,subject,workdir=None,output_indicator="-o",input_indicator="-i",outputname=None,input=None):
        '''Initialize the command'''
        self.command = command
        self.subject = subject
        self.workdir = workdir
        self.outputname = outputname
        self.input = input
        self.output_indicator = output_indicator
        self.input_indicator = input_indicator
    
    @property
    def full_command(self):
        '''Return the full command'''
        full_command = self.command
        if self.input is not None:
            full_command = f"{full_command} {self.input_indicator} {self.input}"
        if self.outputname is not None:
            full_command = f"{full_command} {self.output_indicator} {os.path.join(self.workdir,self.outputname)}"
        return full_command

    def __str__(self):
        return self.full_command

    def execute(self):
        '''Execute the command'''

        logger = logging.getLogger(self.subject)
        logger.info(f"Command {self.full_command} start")
        process = subprocess.Popen(self.full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

        for line in iter(process.stdout.readline, b''): # b'\n'-separated lines
            logger.debug(f"command's stdout: {line}")
        for line in iter(process.stderr.readline, b''):  # b'\n'-separated lines
            logger.error(f"command's stderr: {line}")

        process.wait()
        # Close the process's stdout and stderr 
        process.stdout.close() 
        process.stderr.close()

