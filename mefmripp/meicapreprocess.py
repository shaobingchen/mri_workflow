import parse
import log
#confige the logging

def main():
   
   args = parse.create_args()
   logger = log.setup_logging(args.logdir)

   if args.multithread:
      pass
   else:
      pass
if __name__ == "__main__":
    main()