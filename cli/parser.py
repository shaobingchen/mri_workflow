import argparse
import os.path as op

def parser():
    parser = argparse.ArgumentParser(description="meica preprocess script")
    parser.add_argument("--niftifileroot","-n", help = "(required, str, niftifile root, inside are subjects...) ", type=str, required=True)
    parser.add_argument("--outputdir","-o",default=None, help = "outputdir for bids dataset", type=str)
    #dataset structure
    parser.add_argument("--subjectslist","-s",default = None, help = "(str, \"sub-s001,sub-s002\") ",type=str)
    parser.add_argument("--anatlist","-a",default = "anat", help = "anat list, \"anat\", if more than one is input, mp2rage mode is automatically selected...",type=str)
    parser.add_argument("--funclist","-f",default = "rest", help = "func list, \"rest,task1,task2\", runs you want to process",type=str)
    #optional processing
    parser.add_argument("--freesurferflag","-fs", action="store_true", help = "recon-all, default not")
    parser.add_argument("--freesurferoutputdir", default = None, help = "freesurfer output don't set will be automatically set to be \"niftifileroot/derivatives/freesurfer\"")
    parser.add_argument("--ciftifyflag","-cs", action="store_true", help = "ciftify_recon_all, default not")
    parser.add_argument("--ciftifyoutputdir", default = None, help = "ciftify output")
    parser.add_argument("--fsLRrerun", action="store_true", help = "re-run ciftify_subject_fmri, default nots")
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

    #set freesurfer output dir
    if args.freesurferflag and args.freesurferoutputdir is None:
        args.freesurferoutputdir = op.join(args.niftifileroot,"derivatives","freesurfer")

    #set ciftify output dir
    if args.ciftifyflag and args.ciftifyoutputdir is None:
        args.ciftifyoutputdir = op.join(args.niftifileroot,"derivatives","ciftify")

    return parser