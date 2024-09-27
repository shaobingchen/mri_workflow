'''
base.py is a module to define the basic classes for a workflow, including RunMetaData, Component, Work, CommandWork, Workflow, AutoInput

RunMetaData: store the metadata of a run. RunMeradata will be passed from workflow to work and finally to component. to affect the behavior of the run.

Component: represent the input and output of a work.

Work: container to wrap actions.

Workflow: container to wrap works, and itself is also a work
CommandWork: a subclass of Work, to wrap command line as a work.(which is very common action using neuroimaging tools)

AutoInput: a class to indicate a auto input, if first element of work.input_components is AutoInput(). when running, it will be replaced by the element in the auto_input_set.
'''
import os 
import os.path as op
import networkx as nx
from itertools import product
from copy import deepcopy as dc
import inspect
import logging
import shlex
import subprocess

 
class RunMetaData(object):
    '''
    RunMetaData is a class to store the metadata of a run. RunMeradata will be passed from workflow to work and finally to component. to affect the behavior of the run.
    
    Parameters
    ----------
    rootdir : str
        root directory of the run
    subject : str
        subject id for run
    session : str
        session id for run
    logger : logging.Logger
        logger for the run
    overwrite : bool
        delete existing files when running a work
    skip_exist : bool
        skip running a work if all its output files exist
        it is recommanded to use one of overwrite and skip_exist, if neither is setted, will let each action to decide what to decide
        overwrite and skip_exist are exclusive
    preview : bool
        make a test file trees show what the running result looks like, no real calculation is performed, all files's content is 'test'
    name_type : str
        naming convention for output files
        'run_bids_name' : use BIDS naming convention
        'simplified_bids_name' : use BIDS naming convention without subject and session
    broadcast_metadata : bool
        broadcast metadata to all works, this is useful when debug and using juputer notebook to process data 
    

    Attributes
    ----------
            
    subjectdir -> str  @property
        join rootdir and sub-{subject}
        
    sessiondir -> str  @property
        join rootdir and sub-{subject} and ses-{session}
    
    session_place -> str  @property
        join sub-{subject} and ses-{session}    
        
    _work_heap -> list
        list of a work and all its ancestor e.g. if a work work1 is in a workflow workflow1, and workflow1 is in a workflow workflow2, then work_heap of work1 is ['workflow2', 'workflow1', 'work1']
        
    _current_derivatives_place -> list
        joined list of derivatives_place of _work_heap e.g. if a work's _work_heap is ['workflow2', 'workflow1', 'work1'], derivatives_place of workflow1 is ['derivatives1'], derivatives_place of workflow2 is ['derivatives2'], then _current_derivatives_place of work1 is ['derivatives2', 'derivatives1'].
        this is used to indicate the place of a Component in the directory tree before the session_place.
        
    _current_data_place -> list
        joined list of data_place of _work_heap e.g. if a work's _work_heap is ['workflow2', 'workflow1', 'work1'], data_place of workflow1 is ['data1'], data_place of workflow2 is ['data2'], then _current_data_place of work1 is ['data2', 'data1'].
        this is used to indicate the place of a Component in the directory tree after the session_place.
        
    '''
    
    def __init__(self, rootdir: str, subject: str, session: str = None, logger: logging.Logger = None, overwrite: bool = False, skip_exist: bool = False, preview: bool = False, name_type: str = 'run_bids_name', broadcast_metadata: bool = False):
        
        if not op.exists(rootdir):
            raise ValueError(f"rootdir {rootdir} in RunMetaData does not exist")
        else:
            self.rootdir = rootdir
        self.subject = subject
        self.session = session
        self._current_derivatives_place = []
        self._current_data_place = []
        self.logger = logger
        self.overwrite = overwrite
        self.preview = preview
        self.broadcast_metadata = broadcast_metadata
        self.skip_exist = skip_exist
        self._skip = False #do not use this explicitly
        self._work_heap = []
        self.name_type = name_type
        self._current_format = None #do not use this explicitly, will change when commponent using as different work's input
        self.intial = True
        
        if skip_exist and overwrite:
            raise ValueError("skip_exist and overwrite can't both be True")
        
        _logger = logging.getLogger(logger)
        _logger.info(f"create RunMetaData with\n rootdir {rootdir}\n subject {subject}\n session {session}\n logger {logger}\n overwrite {overwrite}\n preview {preview}")
                    
    @property
    def subjectdir(self):
        return op.join(self.rootdir, f'sub-{self.subject}')
    @property
    def sessiondir(self):
        if self.session is None:
            raise ValueError("session is not defined")
        else:
            return op.join(self.rootdir, f'sub-{self.subject}', f'ses{self.session}')
    @property
    def session_place(self):
        if self.session is None:
            return op.join(f'sub-{self.subject}')
        else:
            return op.join(f'sub-{self.subject}', f'ses{self.session}')
        
class Component(object):
    '''
    Component is a class to represent the input and output of a work, it is characterized by part of parameters such as desc, suffix, datatype, run_metadata.
    
    when writing a workflow,
    a component is characterized by part of parameters such as desc, suffix, datatype. it is a object to represent about a work's input or output which is unrelated to thing in RunMetaData(this part will be included when running), like datatype, suffix, desc, etc.  
      
    when run a workflow,
    a component is usually combined with run_metadata to discribe a actually file. and process informations about it such as full path, name, etc.
    
    Parameters
    ----------
    key-value:
        desc : str
            description of the component
        suffix : str
            suffix of the component e.g. 'bold', 'T1w', 'fmap'
            this is the suffix of bids file name
        datatype : str
            datatype of the component e.g. 'func', 'anat', 'fmap'
            this is the folder name of bids file
        task : str
            task of the component 
        space : str
            space of the component e.g. 'MNI152NLin2009cAsym', 'native'  
        echo : int
            echo of the component
        data_place : list
          
                   
    control
        run_metadata : RunMetaData
            metadata of the run, this is usually not directly setted when initial a component, but passed from work.        
        use_extension : bool
            whether to use extension when generate file name
        extension : str
            extension of the file
        data_place : list
            output place of the comoonent in the directory tree. this attribute accept a list of string, each string is a folder's name. this is used to generate the full path of the file when running a work. this will be combined with run_metadata._current_data_place(place at tail). e.g. ['place1','place2'] will be combined with run_metadata._current_data_place = ['place0'] to generate a full path of the file.
    
    Attributes
    ----------
    run_dir -> str  
        path of the component when running
    name_for_run -> str
        generate file path of the component with RunMetaData. this is the path given to action by default
    run_bids_name -> str
        file name of the component when running with BIDS naming convention
    simplified_bids_name -> str
        simplified file name of the component when running with BIDS naming convention without subject and session
    
    Methods
    -------
    make_test_file -> None
        make a test file whose content is 'test' of the component when running
    delete_file -> None
        delete corresponding file of the component when running
        
    '''
    def __init__(self, desc = None, suffix = None, datatype = None, run_metadata = None, use_extension = False, extension = None, task = None, space = None, echo = None, data_place = None):
        
        self.desc = desc
        self.datatype = datatype
        self.suffix = suffix
        self.run_metadata = run_metadata        
        self.extension = extension
        self.use_extension = use_extension
        self.task = task
        self.space = space
        if echo is None:
            self.echo = None
        else:    
            self.echo = str(echo)
        self.data_place = data_place               
            
    @classmethod
    def init_from(cls, component, **kwargs):
        
        dic = dc(component.__dict__)   
            
        for key, value in kwargs.items():
            dic[key] = value
                             
        return cls(**dic)
    
    @classmethod
    def init_multi_components(cls, list, **kwargs) -> list:
        """
        init a list of components
        list: a list of dictionary, each dictionary should contain the key-value for the multi component
        """
        kwargs_keys = set(kwargs.keys())
        for item in list:
            if not isinstance(item, dict):
                raise ValueError("iterator should return a dictionary")
            if not kwargs_keys.isdisjoint(item):
                duplicate_key = kwargs_keys.intersection(item)
                raise ValueError(f"iterator should not contain key in kwargs, duplicate key is: {duplicate_key}")                
        return [cls(**item, **kwargs) for item in list]    
            
            
    @classmethod
    def init_multi_components_from(cls, components, **kwargs) -> list:
        """
        init a list of components from another list of components
        components: a list of components
        """
        return [cls.init_from(component, **kwargs) for component in components] 
    
    
    def run_dir(self, datatype = True):
        if self.run_metadata is None:
            raise ValueError("run_metadata is not defined")
        else:
            if datatype:
                return op.join(self.run_metadata.rootdir, *self.run_metadata._current_derivatives_place, self.run_metadata.session_place, self.datatype, *self.run_metadata._current_data_place)
            else:
                return op.join(self.run_metadata.rootdir, *self.run_metadata._current_derivatives_place, self.run_metadata.session_place, *self.run_metadata._current_data_place)
    
    
    
    def name_for_run(self, full_path:bool = True, extension:bool = True, name_type:str = None, name_prefix:str = None, name_surfix:str = None,  final_prefix:str = None, final_surfix:str = None, datatype = True):
        '''
        get file name for run
        
        '''
        if name_type is None:
            name_type = self.run_metadata.name_type
            
        _temp_name = None
        
        match name_type:
            
            case 'run_bids_name':
                _temp_name = self.run_bids_name(extension)
            case 'simplified_bids_name':
                _temp_name = self.simplified_bids_name(extension) 
            case 'only_disc':
                if extension:
                    _temp_name = self.desc + '.' + self.extension
                else:
                    _temp_name = self.desc
            case _:
                raise ValueError(f"unknown type {self.name_type} from {self.bids_name}")
        
        
        if name_prefix is not None:
            _temp_name = f"{name_prefix}{_temp_name}"
        
        if name_surfix is not None:
            _temp_name = f"{_temp_name}{name_surfix}"
        
        if full_path:
            _temp_name = op.join(self.run_dir(datatype = datatype), _temp_name)

        if final_prefix is not None:
            _temp_name = f"{final_prefix}{_temp_name}"
        
        if final_surfix is not None:
            _temp_name = f"{_temp_name}{final_surfix}"
        
        return _temp_name
    

    def use_name(self,**kwargs):
        if self.run_metadata._current_format is None:
            return self.name_for_run(**kwargs)
        else:
            return self.name_for_run(**self.run_metadata._current_format, **kwargs)

    bids_order = {
        'bold': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'dir', 'run', 'echo', 'part', 'chunk', 'space', 'desc'],
        'MP2RAGE': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'flip', 'inv', 'part', 'chunk', 'space', 'desc'],
        'T1w': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'part', 'chunk', 'space', 'desc'],
        'fmap': ['sub', 'ses', 'acq', 'run', 'gre', 'chunk', 'space', 'desc']
    }#TODO add more            

 
    def _bids_name_generator(self, dic, extension):
        
        
        ordered_dic = {key: dic[key] for key in Component.bids_order[self.suffix] if key in dic}
        
        #this true/false judgement can be nested
        if extension or self.use_extension:
            __extension = True
        else:
            __extension = False
            
        if __extension:
            if extension is None:
                raise ValueError(f"extension of {self.simplified_bids_name()} is not defined, but needed")
            return f'{"_".join([f"{key}-{value}" for key, value in ordered_dic.items() if value is not None])}_{dic['suffix']}.{dic["extension"]}'
        else:
            return f'{"_".join([f"{key}-{value}" for key, value in ordered_dic.items() if value is not None])}_{dic['suffix']}'
        
           
    def run_bids_name(self, extension = True):
   
        '''
        generage file name for run
        '''
        dic = dc(self.__dict__)
        dic.setdefault('sub', self.run_metadata.subject)
        dic.setdefault('ses', self.run_metadata.session)
                                       
        return self._bids_name_generator(dic, extension)   
    
       
    def simplified_bids_name(self, extension = True):
        '''
        generage file identity (run_bids_name without metadata)
        '''
        # #this true/false judgement can be nested
        # if extension or self.use_extension:
        #     __extension = True
        # else:
        #     __extension = False
            
        dic = dc(self.__dict__)          
        
        return self._bids_name_generator(dic, extension)     
    
    
    def make_test_file(self):
        '''
        make a test file for preview
        '''
        with open(self.use_name(), 'w') as f:
            f.write('test')            
            
    
    def remove_file(self):
        '''
        delete file
        '''
        os.remove(self.use_name())


class Work(object):
    '''
    Work is container to wrap actions for a work flow
    
    Parameters
    ----------
    name : str
        name of the work
    input_components : list[Component]
        list of input components
    output_components : list
        list of output components
    action : function
        action to run
    derivatives_place : list
        intermediate place of the output components before session_place in the directory tree.(see _current_derivatives_place in RunMetadata)
    data_place : list
        intermediate place of the output components after session_place in the directory tree.(see _current_data_place in RunMetadata)
    input_format : list[dict]
        this list should have the same length as input_components, each element of the list is a dictionary to describe the parameters of the input components.
        this is used when default format is not suitable for the input components.
    output_format : list[dict]
        this list should have the same length as output_components, each element of the list is a dictionary to describe the parameters of the output components.
        this is used when default format is not suitable for the output components.
    append_auto_input : bool
        append first element of output_components_list of work to _auto_input_set for other work's auto 
    preserve_auto_input : bool
        preserve the components in _auto_input_set even though it is used by this work
    
    Attributes
    ----------
    input_components_list : list
        should be same as input_components_list
    output_components_list : list
        should be same as output_components_list
    input_components_set : set
        set(input_components_list)
    output_components_set : set
        set(output_components_list)
    all_components : set
        input_components_set | output_components_set
    
    Methods
    -------
    run : MetaData -> None
        run this work by executing action, most of other parameters are served for this method. more details see the method's __doc__
                
    '''
    def __init__(self, name, input_components:list[Component] = None, output_components:list[Component] = None, action = None, derivatives_place = None, data_place = None, input_format:list[dict] = None, output_format:list[dict] = None, append_auto_input = True, preserve_auto_input = False):
        
        self.name = name
        if input_components is not None:
                          
            if isinstance(input_components,list):
                self.input_components_list = input_components
                self.input_components_set = set(input_components)
            else:
                raise ValueError(f"input_components of {self.name} should be a list or set")
        
        if output_components is not None:
            if isinstance(output_components, list):
                self.output_components_list = output_components
                self.output_components_set = set(output_components)

            else:
                raise ValueError(f"output_components of {self.name} should be a list or set")
                    
            
        self.action = action
        self.append_auto_input = append_auto_input
        self.preserve_auto_input = preserve_auto_input
        
        if data_place is None:
            self.data_place = []
        else:
            if not isinstance(data_place, list):
                raise ValueError(f"data_place of {self.name} should be a list")
            else:
                self.data_place = data_place
        
        
        if derivatives_place is None:
            self.derivatives_place = []            
        else:
            if not isinstance(derivatives_place, list):
                raise ValueError(f"derivatives_place of {self.name} should be a list")
            else:
                self.derivatives_place = derivatives_place
        
        self.input_format = input_format
        self.output_format = output_format
    
                
    def _test_component_list(self, list_or_set):
        if not isinstance(self, Workflow) and not isinstance(list_or_set, list):
            raise ValueError(f"{self.name} is not a Workflow,  components container should be a list")        
        elif not isinstance(list_or_set, set) and isinstance(self, Workflow):                
            raise ValueError(f"{self.name} is a Workflow, component container of should be a set")
        
        return True 
                    
    @property    
    def all_components(self) -> set:
        return self.input_components_set | self.output_components_set
    
    def _pre_run(self, run_metadata):
        ''' 
        some preprocessing before running a work
        add derivatives_place and data_place of work to _current_derivatives_place and _current_data_place of run_metadata
        then distribute run_metadata's deep copy to output_components
        
        Controls: control flags is in run_metadata
        --------
        overwrite
        remove pre-exist file in output_components. if the pre-exist file is in input_components, it will not be removed.
        skip_exist
        set _skip flag to True if all output components are exist, this will skip run action in run 
        remove pre-exist file in output_components if part of them are exist        
        '''
        run_metadata._work_heap.append(self.name)
        run_metadata._current_derivatives_place = run_metadata._current_derivatives_place + self.derivatives_place
        run_metadata._current_data_place = run_metadata._current_data_place + self.data_place
        
        logger = logging.getLogger(run_metadata.logger)
        logger.info(f"run {self.name}, work_heap is {run_metadata._work_heap}")
        
        if not self.input_components_set:
            logger.error(f"list of input_components {self.name} is empty.")
        
        for index, component in enumerate(self.input_components_list):
            
            if self.input_format is None:
                pass
            elif len(self.input_format) != len(self.input_components_list):
                raise ValueError(f"input format {self.input_format} of {self.name} don't match the input components {self.input_components_list}")     
            else:
                logger.debug(f"set input component {component.simplified_bids_name()} 's format as {self.input_format[index]}")          
                component.run_metadata._current_format = self.input_format[index]
                
            if not op.exists(component.use_name()):
                raise ValueError(f"input component {component.use_name()} of work {self.name} does not exist")    
            
        if not self.output_components_set:
            logger.error(f"list of output_components {self.name} is empty, eventhough this work update component in input_components and don't generate new file, it should be added to output_components")    
                        
        for index, component in enumerate(self.output_components_set):
            transform_run_metadata = dc(run_metadata)
            component.run_metadata = transform_run_metadata
            
            if self.output_format is None:
                pass
            elif len(self.output_format) != len(self.output_components_list):
                raise ValueError(f"output format {self.output_format} of {self.name} don't match the output components {self.output_components_list}")
            else:
                logger.debug(f"set output component {component.simplified_bids_name()} 's format as {self.output_format[index]}")
                component.run_metadata._current_format = self.output_format[index]
            
            if not op.exists(component.run_dir()):
                os.makedirs(component.run_dir())
                logger.warning(f"create directory {component.run_dir()}")
        
        _all_output_component_exist = True     
        _existed_component_set = set()   
        
        for component in self.output_components_set:
            
            if op.exists(component.use_name()): 
                _existed_component_set.add(component)              
            
            else:
                _all_output_component_exist = False        

        for component in _existed_component_set - self.input_components_set:
            
            logger.warning(f"file {component.use_name()} exist before running, and it not in input components.")
            if run_metadata.overwrite:                                         
                
                component.remove_file()
                logger.warning(f"remove pre-exist file {component.use_name()} because overwrite has been setted")
            elif run_metadata.skip_exist and not _all_output_component_exist:
                
                logger.warning(f"file {component.use_name()} exist before running, and not all output of this work exist. will remove this file and run this work")
                component.remove_file()
                                            
        if  run_metadata.skip_exist and _all_output_component_exist and not self.output_components_set.issubset(self.input_components_set):
            run_metadata._skip = True
            logger.warning(f"skip running {self.name} because all output components are exist, if a output is also a exist input, this may redo a work") 

        if self.action is None:            
            raise ValueError(f"action of {self.simplified_bids_name()} is not defined")               
        
        return run_metadata
                                
    def run(self, run_metadata):
        
        run_metadata = self._pre_run(run_metadata)
        
        logger = logging.getLogger(run_metadata.logger)
        
        if run_metadata._skip:
            logger.debug(f"_skip flag is {run_metadata._skip}, skip running {self.name}")
            return
            
        if run_metadata.preview:
                            
            for component in self.output_components_set:
                
                component.make_test_file()
                logger.info(f"make test file {component.use_name()}")
                
        elif run_metadata.broadcast_metadata:
            pass

        elif self.action.__name__  == '_run_shell_command':
                    
            def _process_item(self, item):
                if isinstance(item, Component):
                    if item in self.input_components_set:
                        return item.use_name()
                    elif item in self.output_components_set:
                        return item.use_name()
                    else:
                        raise ValueError(f"component {item.simplified_bids_name()} of {self.name} is not in either input_components or output_components")
                    
                elif isinstance(item, AutoInput):
                    
                    if item.dict:
                        raise ValueError(f"when running {self.name}, a non-empty AutoInput is given. auto_input need a empty AutoInput in command_list, the match part should put in input_components")
                    else:
                        return self.input_components_list[0].use_name()
                    
                elif isinstance(item, str):                    
                    return item
                
                elif isinstance(item, list):
                                        
                    component_position_list = [index for index, item in enumerate(item) if isinstance(item, (Component, dict))]# unfinished
                                        
                    len_component_list = len(component_position_list) - 1
                    
                    if len(component_position_list) == 0:
                        self.run_metadata.logger.error(f"no component is given in a list of command arguments when running {self.name} with command list {self.command_list}")
                    if len(component_position_list) > 1:
                        self.run_metadata.logger.error(f"multiple components are given in a list of command arguments when running {self.name} with command list {self.command_list}")
                        raise ValueError(f"multiple components are given in a list of command arguments when running {self.name} with command list {self.command_list}")
                    component_position = component_position_list[0]
                    
                    if isinstance(item[component_position], AutoInput):
                        if item[component_position]:
                            raise ValueError(f"when running {self.name}, a non-empty AutoInput is given in {item}. auto_input need a empty AutoInput in command_list, the match part should put in input_components")
                        
                        item[component_position] = self.input_components_list[0]
                    
                    name_prefix, name_surfix, final_prefix, final_surfix = None, None, None, None
                                            
                    if component_position == 1:
                        final_prefix = item[0]
                    elif component_position == 2:
                        final_prefix, name_prefix = item[0], item[1]
                    
                    if len_component_list - component_position == 1:
                        final_surfix = item[-1]
                    elif len_component_list - component_position == 2:
                        name_surfix, final_surfix = item[-2], item[-1]
                        
                    return item[component_position].use_name(name_prefix = name_prefix, name_surfix = name_surfix, final_prefix = final_prefix, final_surfix = final_surfix)
                
                elif isinstance(item, (int, float, complex)):
                    
                    return str(item)
                                                                                
                else:
                    raise ValueError(f"item {item} of {self.name} is not a Component, string, list or number")
                            
            _run_command_list = [_process_item(self, item) for item in self.command_list]
            
            logger.info(f"start running action {self.action.__name__} {_run_command_list} of work {self.name} with command list")
            
            self.action(_run_command_list, run_metadata) #give a dp run_metadata
            
            logger.info(f"finish running action {self.action.__name__} of work {self.name}")
                              
        elif 'run_metadata' in inspect.signature(self.action).parameters:

            _run_input_components = [component.use_name() for component in self.input_components_set]
            _run_output_components = [component.use_name() for component in self.output_components_set]
            
            logger.info(f"start running action {self.action.__name__} {_run_input_components, _run_output_components} of work {self.name} with run metadata")
            
            self.action(_run_input_components, _run_output_components, run_metadata) #give a dp run_metadata
            # try:
            #     self.action(_run_input_components, _run_output_components, run_metadata)
            # except Exception as e:
                
            #     logging.getLogger(run_metadata.logger).error(f"error when running {self.name} with error {e}")
                        
            #     raise RuntimeError(f"error when running {self.name} with error {e}")
            
            logger.info(f"finish running action {self.action.__name__} of work {self.name}")
            
                                
        else:
            
            _run_input_components = [component.use_name() for component in self.input_components_list]
            _run_output_components = [component.use_name() for component in self.output_components_list]
            
            logger.info(f"start running action {self.action.__name__} {_run_input_components, _run_output_components} of work {self.name}")
            
            self.action(_run_input_components, _run_output_components)
            # try:
            #     self.action(_run_input_components, _run_output_components)
                
            # except Exception as e:
                
            #     logging.getLogger(run_metadata.logger).error(f"error when running {self.name} with error {e}")
                        
            #     raise RuntimeError(f"error when running {self.name} with error {e}")
                
            logger.info(f"finish running action {self.action.__name__} of work {self.name}")
            
    
        
    def add_action(self, action):
        self.action = action
    
class CommandWork(Work):
    '''
    class to wrap command line as a work
    '''
    
    def __init__(self, name, input_components=None, output_components=None, command_list = None, save_stdout_to = None, stdout_to_log = True, env = None, **kwargs):
        
        super().__init__(name, input_components, output_components, self._run_shell_command, **kwargs)
        if command_list is None:
            self.command_list = []
        else:
            self.command_list = command_list
        self.save_stdout_to = save_stdout_to
        self.stdout_to_log = stdout_to_log
        
        if env is None:
            self.env = None
        else:
            self.env = os.environ.copy()
            self.env.update(env)
        
    def _run_shell_command(self, command_list: list, run_metadata: RunMetaData):
    
        command = shlex.join(command_list)
        logger = logging.getLogger(run_metadata.logger)
        logger.debug(f"start running command {command} inside _run_shell_command")
        
        
        try:
            process = subprocess.Popen(
                command_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr separately
                text=True,  # Return strings instead of bytes
                env=self.env
            )
            
            # Wait for the process to complete and capture output
            stdout, stderr = process.communicate()
            
            if self.save_stdout_to is not None:
                with open(self.save_stdout_to.use_name(), 'w') as f:
                    f.write(stdout)
            
            if self.stdout_to_log:
                for line in stdout.splitlines():
                    logger.debug(line)
                
            for line in stderr.splitlines():
                logger.debug(line) #tools like afni use stderr print normal information
            
            # Check the return code
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, command, stdout, stderr)


        except subprocess.CalledProcessError as e:
            # Handle command execution errors
            raise Exception(
                f"""
                Error executing command: {command}
                Return code: {e.returncode}
                Error output: {e.stderr}
                """
            )
        except OSError as e:
            # Handle OS-level errors (e.g., command not found)
            raise Exception(f"OS error when trying to execute {command}: {e}")

        except Exception as e:
            # Handle all other exceptions
            raise Exception(f"unexpected error executing command: {command}: {e}")
        
        
        logger.debug(f"finish running command {command} inside _run_shell_command")
        
        
        # process = subprocess.Popen(
        #     command_list,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,  # Capture stderr separately
        #     text=True  # Return strings instead of bytes
        # )
        
        # # Wait for the process to complete and capture output
        # stdout, stderr = process.communicate()
        
        # for line in stdout.splitlines():
        #     logger.debug(line)
            
        # for line in stderr.splitlines():
        #     logger.debug(line)
        
        # # Check the return code
        # if process.returncode != 0:
        #     raise subprocess.CalledProcessError(
        #         process.returncode, command, stdout, stderr)
    
    

class Workflow(Work):
    
    def __init__(self, name, work_list = None, output_component_mannual = None, enable_auto_input = False, **kwargs):
        
        if work_list is None:
            self.worklist = []
        else:
            self.work_list = work_list
            
        self.enable_auto_input = enable_auto_input
        # do auto input
        # append first element of output_components_list of work to input_components_list for other work's auto input
        # if a work's auto_input is True, and its input_components_list is empty, then the only one element of auto_input_set will be append to it
        # if its input_components_list is not empty, then using its key-value to match a component in auto_input_set    
        if self.enable_auto_input:
            
            self._auto_input_set = set()  

            for work in self.work_list:
                if not isinstance(work, Workflow):
                    
                                        
                    if isinstance(work.input_components_list[0], AutoInput):                            
                        if not work.input_components_list[0].dict:
                            
                            if len(self._auto_input_set) == 1:
                                work.input_components_list[0] = self._auto_input_set.pop()
                                work.input_components_set.add(work.input_components_list[0])
                                if work.preserve_auto_input:
                                    self._auto_input_set.add(work.input_components_list[0])
                            else:
                                raise ValueError(f"when doing auto_input on work {work.name} , input_components_list is empty, but _auto_input_set {self._auto_input_set} is given, which is expected has length 1")
                        
                        else:
                            _matched_list = [component for component in self._auto_input_set if all(getattr(component, key) == value for key, value in work.input_components_list[0].dict.items())]
                            if len(_matched_list) == 1:
                                work.input_components_list[0] = _matched_list[0]
                                work.input_components_set.add(work.input_components_list[0])
                                if not work.preserve_auto_input:                                    
                                    self._auto_input_set.remove(_matched_list[0])
                                
                            elif len(_matched_list) == 0:
                                raise ValueError(f"when doing auto_input on work {work.name} , first element of input_components is AutoInput, but no matched component in _auto_input_set {[component.simplified_bids_name() for component in self._auto_input_set]} with input_components_list {work.input_components_list[0].dict}")
                            else:
                                raise ValueError(f"when doing auto_input on work {work.name} , first element of input_components is AutoInput, but multiple matched component in _auto_input_set {[component.simplified_bids_name() for component in self._auto_input_set]} with input_components_list {work.input_components_list[0].dict}")
                    
                    if work.append_auto_input:
                        self._auto_input_set.add(work.output_components_list[0])            
                       
        
        super().__init__(name, **kwargs)
        
        self.input_components_set = self.get_input_components
        self.output_components_set = self.get_output_components
        
        if output_component_mannual is None:
            self.output_components_set = self.get_output_components
        else:
            if not isinstance(output_component_mannual, set):
                raise ValueError(f"output_component_mannual of {self.name} should be a set")
            else:
                self.output_components_set = output_component_mannual 
        
        
    def add_work(self, work):
        self.worklist.append(work)
        self.input_components_set.update(work.input_components_set)
        self.output_components_set.update(work.output_components_set)
    
    @property    
    def cp_directed_graph(self):
        '''
        create a directed graph with components as nodes and works as edges        
        '''
        G = nx.DiGraph()    
        G.add_nodes_from(self.all_components)
        
        for work in self.worklist:
            G.add_edges_from(product(work.input_components_set, work.output_components_set))
        
        return G
    
    def draw_graph(self, file_name = "workflow.png"):
        '''
        draw a cp_directed_graph graph 
        '''
        import matplotlib.pyplot as plt
        
        nx.draw(self.cp_directed_graph, with_labels=True, labels= {component: component.name for work in self.worklist for component in work.all_components}, node_color='lightblue', node_size=700, arrowstyle='-|>', arrowsize=20)
        plt.savefig(file_name)
    
    @property
    def work_directed_graph(self):
        '''
        create a directed graph with work as nodes and components as edges
        components are contained in the components attribute of the edge
        if a work's input_component exist in multiple output_component_list of other works, if they are in the same branch, only keep the last one, if they are not in the same branch, conflict occur and raise error
        '''
        directed_graph = nx.DiGraph()
            
        ancestor_test = return_ancestor_test(directed_graph)
        from functools import cmp_to_key
                
        for work in self.worklist:
            directed_graph.add_node(work)
            
            for input_component in work.input_components_set:
                
                matched_works = set()
                
                for already_in_work in directed_graph.nodes:
                    matched_works = [
                        already_in_work
                        for output_component in already_in_work.output_components_set
                        if input_component == output_component
                    ]
                                
                    if len(matched_works) == 0:
                        raise ValueError(f"input component {input_component.simplified_bids_name()} of work {work.name} is not in any output components of any work")
                    elif len(matched_works) == 1:
                        matched_work = matched_works[0]
                    elif len(matched_works) > 1: #test if they are in the same branch, if not, they are conflict, if yes,only keep the last one
                        matched_works.sort(key = cmp_to_key(ancestor_test))
                        print(f"input component {input_component.simplified_bids_name()} of work {work.name} is in output components of multiple works {[matched_work.name for matched_work in matched_works]} in same branch, only keep the last one {matched_works[-1].name}")
                        matched_work = matched_works[-1]
                        
                if directed_graph.has_edge(matched_works, work):
                    directed_graph[matched_work][work]['components'].add(input_component)
                else:
                    directed_graph.add_edge(matched_work, work, components = {input_component})           
                           

        
        return directed_graph
    
    @property
    def get_output_components(self):
        '''
        get output components of a workflow
        this will return a set of components that are the output of any work that contains the workflow 
        '''
        return set().union(*(work.output_components_set for work in self.work_list))
    
    @property
    def get_input_components(self):
        ''' 
        get input components of a workflow
        '''
        all_input_component = set().union(*(work.input_components_set for work in self.work_list))
        
        return all_input_component.difference(self.get_output_components)
        
                
        
    def run(self, run_metadata):
        
        #prevent original run_metadata from being changed
        if run_metadata.intial:
            run_metadata.iniiate = False
            run_metadata = dc(run_metadata)
            
        run_metadata._work_heap.append(self.name)
        run_metadata._current_derivatives_place = run_metadata._current_derivatives_place + self.derivatives_place
        run_metadata._current_data_place = run_metadata._current_data_place + self.data_place
        logger = logging.getLogger(run_metadata.logger)
        logger.info(f"run {self.name}, work_heap is {run_metadata._work_heap}")
        logger.info(f"work_list is {[work.name for work in self.work_list]}")
        
        
        for work in self.work_list:  
            
            transfor_run_metadata = dc(run_metadata) 
            work.run(transfor_run_metadata)
        
        logger.info(f"finish running workflow {self.name}")  
                
    
    @property
    def all_components(self) -> set:
        return {component for work in self.worklist for component in work.all_components}
    
    def update_output_components(func):
        '''
        decorator to update output components
        '''
        def wrapper(self, *args, **kwargs):
            self.output_components = self.get_output_components
            return func(self, *args, ** kwargs)
        return wrapper

    
    def update_input_components(func):
        '''
        decorator to update input components
        '''
        def wrapper(self, *args, **kwargs):
            self.input_components_set = self.get_input_components_set
            return func(self, *args, ** kwargs)
        return wrapper

        
        
        
def return_ancestor_test(graph: nx.DiGraph):
    if not isinstance(graph, nx.DiGraph):
        raise ValueError("graph should be a DiGraph")
    
    def _ancestor_test(work1, work2):
        if nx.has_path(graph, work2, work1):
            return 1
        elif nx.has_path(graph, work1, work2):
            return -1
        else:
            raise ValueError(f"work {work1.name} and work {work2.name} are not in the same branch, conflict")                
    return _ancestor_test        


class AutoInput(object):
    def __init__(self, **kwargs) -> None:
        
        self.dict = kwargs
            
            
            
            