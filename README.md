# install
```
pip install neuroworkfow
```
# overview
provide a way to format code for processing neural data, get researches rid of file finding, name jointing and other dirty works when writing data process workflow.

Offer tools for quick inspecting pipline such as:

- generate a pseudo dataset to simplify how to arrange a dataset to run a pipline or how a data set looks like after running
- generate a subpipline from a existing pipline, this is useful when only partially result is needed or using some intermediate result. 
# usage
to write a data processing pipline using neuroworkflow, one need use three basic object: component, work and workflow. when run a processing pipline, one need additionally provide metadata which provide prossesed information such as subject, session and other setting.
## Component
component is the representation of a file. 
### initial
when writing pipline, one need add propertis of a component to define a component. like
```
example_component = Component(suffix = 'bold', datatype = 'func', extension = 'nii')
```
some of the available properties are

|property|function|example|
|:--------:|:--------:|:----:|
|desc|describe | smooth6mm
datatype| data type|func
suffix|suffix|bold    
extension|extension|nii.gz
task|task|eyesopen
space|space|MNI152
echo |echo|2
data_place|folder to place|echo_2
use_extension|force using extension|true

when running, component will generate a file's name and directory according to its property, metadata and it's position in the whole pipline.
### init_from
to simplify the initialization of a component, one can use init from to initialize a component
```
example_epi_json = Component.init_from(origin_epi_list, extension = 'json')
```
this will init a 

### init_multi


# Work
a work is the representation of a processing step. 
### initial
when writing pipline, one need add components to a work's input_components and output_components indicate what to process and what will be generated, add action as the processs.

```

copy_epis = Work(f'copy_epi',
                  [origin_epi_list],
                  [copied_origin_epi_list],
                  action = copy_file
                  )
```
and the copy_file is 
```
def copy_file(input_file, output_file):
    shutil.copyfile(input_file[0], output_file[0])
```
a action should accept two (input_file, output_file) or three (input_file, output_file, run_meta_data) parameters.

### CommandWork
