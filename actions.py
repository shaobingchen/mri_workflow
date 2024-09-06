import subprocess
import shlex
from src.neuroworkflow.base import Component, Work, Workflow, RunMetaData, CommandWork
import os
import shutil




def copy_file(input_file, output_file):
    shutil.copyfile(input_file[0], output_file[0])

def get_slice_time(input_file, output_file):
    import json
    with open(input_file[0], 'r') as f:
        data = json.load(f)
        
    slice_time = data['SliceTiming']
    
    with open(output_file[0], 'w') as f:
        for timing in slice_time:
            f.write(f'{timing}\n')