from shell_commands import ShellCommand

#freesurfer instance
freesurfer = ShellCommand("recon-all -all ")
freesurfer.subject_indicator = "-subject"
freesurfer.output_indicator = "-sd"
freesurfer.outputname = "freesurfer"
