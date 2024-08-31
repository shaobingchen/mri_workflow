import subprocess
import shlex
from src.mri_workflow.base import Component, Work, Workflow, RunMetaData, CommandWork
import os
import shutil




def copy_file(input_file, output_file):
    shutil.copyfile(input_file, output_file)

    
    