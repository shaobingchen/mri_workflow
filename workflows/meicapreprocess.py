from ..cli import parser
import utils.log 
#confige the logging

def main():
   
   args = parser.parser.parse_args()
   #logger = utils.log.setup_logging()
   if args.multithread:
      pass
   else:
      pass
   print(args.logdir)
