from shell_commands import ShellCommand
class Workflow(object):
    '''Class to form a series of commands'''

    def __init__(self, *commands, workdir=None):
        self.commands = list(commands)
        self.workdir = workdir

        # Check if all commands are ShellCommand objects
        if not all(isinstance(command, ShellCommand) for command in self.commands):
            raise TypeError("All commands must be ShellCommand objects")

    def add_command(self, command):
        self._check_command_type(command)
        self.commands.append(command)

    def _check_command_type(self, command):
        if not isinstance(command, ShellCommand):
            raise TypeError(f"{command} is not a ShellCommand object")

    def run(self):
        for command in self.commands:
            command.workdir = self.workdir
            command.execute()