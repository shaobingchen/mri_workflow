from shell_commands import ShellCommand
import os
import logging

class Workflow(object):
    '''Class to form a series of commands'''

    def __init__(self, *actions, subject=None, workdir=None, entry_point=None, workflow_name=None, args=None):
        self.actions = list(actions)
        self.subject = subject
        self.workdir = workdir
        self.entry_point = entry_point
        self.outpoint = None
        self.workflow_name = workflow_name
        self.args=args
        self.logger = logging.getLogger(self.subject)

        # Check if all commands are ShellCommand objects
        if not all(isinstance(command, ShellCommand) for command in self.actions):
            raise TypeError("All commands must be ShellCommand objects")
        
        if subject is None:
            raise ValueError("subject must be specified")

        if workdir is None:
            raise ValueError("workdir must be specified")
        
        if entry_point is None:
            self.logger.warning("entry_point is not specified, this may be fine, but need notice")
        

    def add_action(self, actions):
        self._check_command_type(actions)
        self.actions.append(actions)

    def _check_command_type(self, actions):
        if not isinstance(actions, ShellCommand):
            self.logger.warning(f"{actions} is not a ShellCommand object, maybe a python script")

    def run(self):
        last_action_outputdir = self.entry_point
        logger = logging.getLogger(self.subject)

        logger.info(f"Start workflow {self.workflow_name}")

        #create workdir 
        if not os.path.exists(self.workdir):
            os.makedirs(self.workdir)
        else:
            logger.warning(f"{self.workdir} used for {self.workflow_name} already exists, may overwrite")
        #execute actions
        for action in self.actions:

            action.subject = self.subject
            action.input = last_action_outputdir
            action.workdir = self.workdir
            action.args = self.args

            action.execute()

            last_action_outputdir = action.outputdir

        self.outpoint = last_action_outputdir

        return self.outpoint
