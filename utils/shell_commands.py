import os
import subprocess

class ShellCommand(object):
    '''Class to execute shell commands from python'''
    def __init__(self,command):
        '''Initialize the command'''
        self.command = command

    def run(self):
        '''Execute the command'''
        subprocess.run(self.command, shell=True)

if __name__ == '__main__':
    # Example usage
    command = ShellCommand('ls')
    command.run()