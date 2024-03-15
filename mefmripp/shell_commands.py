import os
import subprocess
import logging 

class ShellCommand(object):
    '''Class to execute shell commands from python'''
    def __init__(self,command,subject=None,disable_iodir=None,workdir=None,output_indicator="-o",input_indicator="-i",outputname=None,input=None,subject_indicator=None,args=None):
        '''Initialize the command'''
        self.command = command

        #for workflow
        self.subject = subject
        self.workdir = workdir
        self.input = input

        #for command        
        self.outputname = outputname
        self.disable_iodir = disable_iodir
        self.output_indicator = output_indicator
        self.input_indicator = input_indicator
        self.subject_indicator = subject_indicator
    
    @property
    def full_command(self):
        '''Return the full command'''
        if self.command is None:
                raise ValueError("command is None")

        full_command = self.command
        if self.subject_indicator is not None:
                full_command = f"{full_command} {self.subject_indicator} {self.subject}"

        if self.disable_iodir is None:
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

        for line in iter(process.stdout.readline, ''): # b'\n'-separated lines
            logger.debug(f"command's stdout: {line.rstrip()}")
        for line in iter(process.stderr.readline, ''):  # b'\n'-separated lines
            logger.error(f"command's stderr: {line.rstrip()}")
        
        process.wait()
        # Close the process's stdout and stderr 
        process.stdout.close() 
        process.stderr.close()

