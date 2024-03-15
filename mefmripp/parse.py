import argparse
import os
import os.path as op
from re import match

def create_args():
    parser = argparse.ArgumentParser(description="meica preprocess script")
    parser.add_argument("--niftifileroot","-n", help = "(required, str, niftifile root, inside are subjects...) ", type=str, required=True)
    parser.add_argument("--outputdir","-o",default=None, help = "outputdir for bids dataset", type=str)
    #dataset structure
    parser.add_argument("--subjectslist","-s",default = None, help = "(str, \"sub-s001,sub-s002\") ",type=str)
    parser.add_argument("--anatfoldername","-a",default = "anat", help = "anat list, \"anat\", if more than one is input, mp2rage mode is automatically selected...",type=str)
    parser.add_argument("--funcfoldername","-f",default = "func", help = "func list, \"rest,task1,task2\", runs you want to process",type=str)
    parser.add_argument("--logdir",default= None, help = "log file's directory", type=str)
    #optional processing
    parser.add_argument("--freesurferflag","-fs", action="store_true", help = "recon-all, default not")
    parser.add_argument("--freesurferoutputdir", default = None, help = "freesurfer output don't set will be automatically set to be \"niftifileroot/derivatives/freesurfer\"")
    parser.add_argument("--ciftifyflag","-cs", action="store_true", help = "ciftify_recon_all, default not")
    parser.add_argument("--ciftifyoutputdir", default = None, help = "ciftify output")
    parser.add_argument("--fsLRrerun", action="store_true", help = "re-run ciftify_subject_fmri, default nots")
    parser.add_argument("--multithread","-mt", action="store_true", help = "multithread, default not")
    #customed arguments
    parser.add_argument("--fsbot", default = 0.01, help = "bandpass filter low pass freq")
    parser.add_argument("--fstop", default = 0.1, help = "bandpass filter high pass freq")
    parser.add_argument("--smkernal", default = 6, help = "smooth kernal, FWHM(mm)")
    parser.add_argument("--outputspace", default = "MNI152,fsaverage,fsLR", help = "Outputspace, MNI152,fsaverage,fsLR",type=str)
    parser.add_argument("--tedpca", default="kundu-stabilize", help = "tedana option for tedpca")
    
    # parser.add_argument('--nuisanceflag', action="store_true", help = 'nuisance regress, default not')
    # parser.add_argument('--filterflag', action="store_true", help = 'bandpass filter or not, recommand in rs-fmri, default not')
    # parser.add_argument('--meicasmkernal', default = 12, help = 'meica smooth kernal, FWHM(mm)')

    args=parser.parse_args()
    set_default_dir(args)
    #parse subjectslist
    get_subjectlist(args)

    return args

def set_default_dir(args):
    "set default dir for outputdir, logdir, freesurferoutputdir, ciftifyoutputdir"
    #set freesurfer output dir
    if args.freesurferflag and args.freesurferoutputdir is None:
        args.freesurferoutputdir = op.join(args.niftifileroot,"derivatives","freesurfer")

    #set ciftify output dir
    if args.ciftifyflag and args.ciftifyoutputdir is None:
        args.ciftifyoutputdir = op.join(args.niftifileroot,"derivatives","ciftify")
    
    #set output dir
    if args.outputdir is None:
        args.outputdir = op.join(args.niftifileroot,"derivatives","preprocessed")
    
    #set log dir
    if args.logdir is None:
        args.logdir = op.join(args.niftifileroot,"derivatives","log")


def get_subjectlist(args):
    "parse subjectslist"
    if args.subjectslist is None:
        args.subjectslist = [f for f in os.listdir(args.niftifileroot) if match("sub-*",f)]
    else:
        args.subjectslist = args.subjectslist.split(",")

    if args.subjectslist is None:
        raise argparse.ArgumentTypeError("subjectslist is None")
    return args


def is_dir(dir_string):
    if not op.isdir(dir_string):
        raise argparse.ArgumentTypeError(f"{dir_string} do not exist")