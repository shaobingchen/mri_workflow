import argparse
import json
import os
from os import path as op

class Configuartion(dict):
    #def __init__(self, initial_dic):
    #    super().__init__(initial_dic)
        
    def set_required_arg(self, key, value):
        if value is None :
            if key not in self or self[key] is None:
                raise ValueError(f"{key} is required")
        else:
            self[key] = value
    
    def test_required_args(self, requried_arguments):
        for key in requried_arguments:
            if self[key] is None:
                raise ValueError(f"{key} is required")

def get_config(args):

    if args.config is None: 
        config=Configuartion()
    else:
        with open(args.config, "r") as f:
            config=Configuartion(json.load(f))

    for arg in vars(args):
        if arg not in config:
            config[arg] = getattr(args, arg)
        
        requried_arguments = ("niftifileroot", "condi", "subjectslist")

    config.test_required_args(requried_arguments)

        
    return config

def config_generator(dic,config_path):
    #using dictionary generate json file

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
        "niftifileroot": "niftifileroot",
        "condi": "condi",
        "subjectslist": "subjectslist",
        "despike_flag": True,
        "slicetiming_flag": True,
    }

    config_generator(dic, config_path)