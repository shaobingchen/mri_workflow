from workflow import Workflow
from actions import *

class Anat_Freesurfer_Workflow(Workflow):
    "workflow for anat processing using freesurfer"
    def __init__(self,*arguments,**kwargs):

        super().__init__(*arguments,**kwargs)
        self.workflow_name = "Anat_Freesurfer_Workflow"

        self.add_action(freesurfer)

        if self.args.ciftifyflag:
            self.add_action(ciftify)
