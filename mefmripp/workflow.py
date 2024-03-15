from shell_commands import ShellCommand
import os
import logging

class Workflow(object):
    '''Class to form a series of commands'''

    def __init__(self, *commands, subject=None, workdir=None, entry_point=None, workflow_name=None, args=None):
        self.commands = list(commands)
        self.subject = subject
        self.workdir = workdir
        self.entry_point = entry_point
        self.outpoint = None
        self.workflow_name = workflow_name
        self.args=args

        # Check if all commands are ShellCommand objects
        if not all(isinstance(command, ShellCommand) for command in self.commands):
            raise TypeError("All commands must be ShellCommand objects")
        
        if subject is None:
            raise ValueError("subject must be specified")

        if workdir is None:
            raise ValueError("workdir must be specified")
        
        if entry_point is None:
            logger = logging.getLogger(self.subject)
            logger.warning("entry_point is not specified, this may be fine, but need notice")
        

    def add_command(self, command):
        self._check_command_type(command)
        self.commands.append(command)

    def _check_command_type(self, command):
        if not isinstance(command, ShellCommand):
            raise TypeError(f"{command} is not a ShellCommand object")

    def run(self):
        last_command_outputdir = self.entry_point
        logger = logging.getLogger(self.subject)

        logger.info(f"Start workflow {self.workflow_name}")
        for command in self.commands:

            command.subject = self.subject
            command.input = last_command_outputdir
            command.workdir = self.workdir
            command.args = self.args

            command.execute()

            last_command_outputdir = command.workdir

        self.outpoint = last_command_outputdir

        return self.outpoint
