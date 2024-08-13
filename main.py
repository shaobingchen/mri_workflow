import argparse
import os
import inspect
from config import *
import logging


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='add arguments to overwirte the configuration')
    parser.add_argument('--config', '-c', type=str, default=os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), 'config.json') help='the path to the configuration file') #should change when this file or this code is moved

    metadata = parser.add_argument_group(description='metadata', help='arguments about metadata such as niftirootdir, subject, session')
    metadata.add_argument('--niftirootdir', '-n', type=str, help='the root directory of nifti files')
    metadata.add_argument('--subject', '-s', type=str, help='the subject name')
    metadata.add_argument('--session', '-e', type=str, help='the session name')
    metadata.add_argument('--task', '-t', type=str, help='the task name')
    
    workflow = parser.add_argument_group(description='workflow', help='arguments for control workflow')
    workflow.add_argument('--despike', action='store_true', help='whether to despike the functional image')
    workflow.add_argument('--slicetiming', action='store_true', help='whether to do slicetiming correction')

    args = parser.parse_args()

    config = get_config(args)

    #unfinished
    handler = logging.FileHandler(os.path.join(config['logdir'], 'main.log'))
    main_logger = logging.getLogger("main",
                                    level=logging.DEBUG,
                                    handlers=[logging.StreamHandler()])
    

