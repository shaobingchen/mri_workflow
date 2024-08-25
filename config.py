import argparse
import json
import os
from os import path as op

class Configuartion(dict):
    '''
    a class to store and manage configuration
    '''
    #def __init__(self, initial_dic):
    #    super().__init__(initial_dic)
    def add_requried_args(self, requied_arguments):
        self.requried_arguments = requied_arguments

        
    def set_required_arg(self, key, value):
        if value is None :
            if key not in self or self[key] is None:
                raise ValueError(f"{key} is required")
        else:
            self[key] = value
    
    def test_required_args(self, requried_arguments = None):
        '''
        test whether the required arguments are seted
        '''
        try:
            if requried_arguments is None:
                requried_arguments = self.requried_arguments
        except Exception as e:
            print(f"No required argument is tested, because {e}")    
        else:
            for key in requried_arguments:
                if self[key] is None:
                    raise ValueError(f"{key} is required")

def get_config(args, config_path = None):
    '''
    initial configuration from args and config.json
    args will overwrite the config.json
    '''
    if config_path:
        #use only for test
        with open(config_path, "r") as f:
            config = Configuartion(json.load(f))
    else:
        if args.config is None: 
            config=Configuartion()
        else:
            with open(args.config, "r") as f:
                config=Configuartion(json.load(f))

        for arg in vars(args):
            if arg not in config:
                config[arg] = getattr(args, arg)

    config.test_required_args()

        
    return config

def config_generator(dic,config_path):
    '''
    using dictionary generate json file
    '''
    if op.exists(config_path):
        print(f"{op.abspath(config_path)} already exists.")
        overwrite = input("Do you want to overwrite the file? Enter 'yes' or 'no': ")

        while overwrite.lower() not in ['yes', 'no' ,'y' ,'n']:
            overwrite = input("Invalid input. Please enter 'yes' or 'no': ")

        if overwrite.lower() in ('no', 'n'):
            print("File not overwritten. exit with 1.")
            exit(1)       
        
    with open(config_path, 'w') as f:
        json.dump(dic, f, indent=4)
        print(f'write into {op.abspath(config_path)}')

if __name__ == "__main__":
    
    config_path = "./config.json"
    dic = {
        "rootdir": "rootdir",
        "condi": "condi",
        "subjectslist": "subjectslist",
        "despike_flag": True,
        "slicetiming_flag": True,
    }

    config_generator(dic, config_path)