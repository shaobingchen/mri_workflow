import parse
import log
from shell_commands import *
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
         
         #anat process
         
if __name__ == "__main__":
    main()