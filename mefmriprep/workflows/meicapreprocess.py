from ..cli.parser import parser
from ..utils import log
#confige the logging

def main():
   
   parser=parser()
   args = parser.parse_args()
   #logger = utils.log.setup_logging()
   if args.multithread:
      pass
   else:
      pass
   print(args.logdir)
