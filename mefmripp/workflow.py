from shell_commands import ShellCommand

class Workflow(object):
    '''Class to form a series of commands'''

    def __init__(self,*commands,workdir=None):
        if len(commands) > 0:
            self.commands = commands
        else:
            self.commands = []
        self.workdir = workdir

        #check if all commands are ShellCommand objects
        for command in self.commands:
            if not isinstance(command,ShellCommand):
                raise TypeError(f"{command} is not a ShellCommand object")

    def add_command(self,command):
        if isinstance(command,ShellCommand):
            self.commands.append(command)
        else:
            raise TypeError(f"{command} is not a ShellCommand object")
    
    def run(self):
        for command in self.commands:
            command.excute()
