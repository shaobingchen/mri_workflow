from base_2 import *
from config import *

config = get_config(None ,"/home/sbc/projects/mefmriprep/config.json")
# for key, value in config.items():
#     print(f"{key} {value}\n")

test_metadata = RunMetaData(rootdir= r"/mridir", subject="sub-s001", datatype="func", session="ses-1")
#print(test_metadata)

    