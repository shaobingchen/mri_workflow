import subprocess
import shlex
from src.neuroworkflow.base import Component, Work, Workflow, RunMetaData, CommandWork
import os
import shutil




def copy_file(input_file, output_file):
    shutil.copyfile(input_file[0], output_file[0])

    
    