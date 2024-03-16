from shell_commands import ShellCommand

#freesurfer instance
freesurfer = ShellCommand("recon-all -all ")
freesurfer.subject_indicator = "-subject"
freesurfer.output_indicator = "-sd"
freesurfer.outputname = "freesurfer"

#ciftify instance
ciftify = ShellCommand("ciftify_recon_all ")
ciftify.subject_indicator = " "
ciftify.input_indicator = "--fs-subjects-dir"
ciftify.output_indicator = "--ciftify-work-dir"
ciftify.outputname = "ciftify"
ciftify.fill_order = "OIS"


#segment class
class Segment(ShellCommand):
    "segment"
    def __init__(self, *arguments, methods="fast" , **kwargs):
        super().__init__(*arguments,**kwargs)

        match methods:
            case "fast":
                self.command="fast "
                self.input_indicator = ""
                self.output_indicator = "-o"
            case "freesurfer":
                pass
                    
            case "ants":
                pass

            case _:
                import logging
                logger = logging.getLogger(self.subject)
                logger.error(f"segment method {methods} not supported")
                raise ValueError(f"segment method {methods} not supported")
    
    def execute(self):
        match self.methods:
            case "fast":
                super().execute()
            case "freesurfer":

            case "ants":
                pass
            case _:
                raise ValueError(f"segment method {self.methods} not supported")

        