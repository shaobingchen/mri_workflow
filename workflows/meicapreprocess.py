import cli.parser as parser
import utils.log 
#confige the logging

def main():
   
   args = parser.parser.parse_args()
   logger = utils.log.getloging()
   anatlist = parser.get_anat_list()
   
   if args.multithread:
      pass
   else
      