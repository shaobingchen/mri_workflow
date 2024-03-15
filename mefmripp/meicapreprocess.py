import parse
import log
from shell_commands import *
from workflow import Workflow
import os
from actions import *
#confige the logging

def main():
   
   args = parse.create_args()
   if args.multithread:
      #TODO: multithread
      pass
   else:
      for subject in args.subjectslist:
         #setup logger
         logger = log.setup_logging(args.logdir,subject)
         logger.debug(f"{subject} start processing...")
         
         #get subject's anat list
         args.anatlist = os.listdir(os.path.join(args.niftifileroot,subject,args.anatfoldername))
         #get subject's func list

         #anat process
         anatworkflow = Workflow(workflow_name="anatworkflow", 
                                 subject=subject, 
                                 workdir=os.path.join(args.niftifileroot,"derivative"), 
                                 entry_point=os.path.join(args.niftifileroot,subject,args.anatfoldername,args.anatlist[0]))
         anatworkflow.add_command(freesurfer)
         anatworkflow.run()
         
if __name__ == "__main__":
    main()