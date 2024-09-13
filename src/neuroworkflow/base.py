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
    RunMetaData is a class to store the metadata of a run
    '''
    def __init__(self, rootdir, subject, session = None, logger = None, overwrite = False, skip_exist = False, preview = False, name_type = 'run_bids_name' ):
        
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
    def __init__(self, desc = None, suffix = None, datatype = None, run_metadata = None, use_extension = False, extension = None, task = None, space = None, echo = None, data_place = None):
        
        self.desc = desc
        self.datatype = datatype
        self.suffix = suffix
        self.run_metadata = run_metadata        
        self.extension = extension
        self.use_extension = use_extension
        self.task = task
        self.space = space
        self.echo = echo 
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
        get 
        '''
        if name_type is None:
            name_type = self.run_metadata.name_type
            
        _temp_name = None
        
        match name_type:
            
            case 'run_bids_name':
                _temp_name = self.run_bids_name(extension)
            case 'simplified_bids_name':
                _temp_name = self.simplified_bids_name(extension)         
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
            return self.name_for_run(**self.run_metadata._current_format)

    bids_order = {
        'bold': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'dir', 'run', 'echo', 'part', 'chunk', 'space', 'desc'],
        'MP2RAGE': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'flip', 'inv', 'part', 'chunk', 'space', 'desc'],
        'T1w': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'part', 'chunk', 'space', 'desc'],
        'fmap': ['sub', 'ses', 'acq', 'run', 'gre', 'chunk', 'space', 'desc']
    }            

 
    def _bids_name_generator(self, dic, extension):
        
        
        ordered_dic = {key: dic[key] for key in Component.bids_order[self.suffix] if key in dic}
        
        #this true/false judgement can be nested
        if extension or self.use_extension:
            __extension = True
        else:
            __extension = False
            
        if __extension:
            if extension is None:
                raise ValueError(f"extension of {self.simplified_bids_name} is not defined, but needed")
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
        
        # #this true/false judgement can be nested
        # if extension or self.use_extension:
        #     __extension = True
        # else:
        #     __extension = False
                               
        return self._bids_name_generator(dic, extension)   
    
    @property        
    def simplified_bids_name(self):
        '''
        generage file identity (run_bids_name without metadata)
        '''
        # #this true/false judgement can be nested
        # if extension or self.use_extension:
        #     __extension = True
        # else:
        #     __extension = False
            
        dic = dc(self.__dict__)          
        
        return self._bids_name_generator(dic, True)     
    
    
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
    input and out put should be a list of components
    '''
    def __init__(self, name, input_components = None, output_components = None, action = None, derivatives_place = None, data_place = None, input_format:list[dict] = None, output_format:list[dict] = None):
        
        self.name = name
                      
        if isinstance(input_components,list):
            self.input_components_list = input_components
            self.input_components_set = set(input_components)
        elif isinstance(input_components,set):
            self.input_components_set = input_components
        else:
            raise ValueError(f"input_components of {self.name} should be a list or set")
        
        if isinstance(output_components, list):
            self.output_components_list = output_components
            self.output_components_set = set(output_components)
        elif isinstance(output_components, set):
            self.output_components_set = output_components
        else:
            raise ValueError(f"output_components of {self.name} should be a list or set")
                    
            
        self.action = action
        
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
                logger.debug(f"set input component {component.simplified_bids_name} 's format as {self.input_format[index]}")          
                component.run_metadata._current_format = self.input_format[index]
                
            if not op.exists(component.use_name()):
                raise ValueError(f"input component {component.use_name()} of work {self.name} does not exist")    
            
        if not self.output_components_set:
            logger.error(f"list of output_components {self.name} is empty, eventhough this work update component in input_components and don't generate new file, it should be added to output_components")    
                        
        for component in self.output_components_set:
            transform_run_metadata = dc(run_metadata)
            component.run_metadata = transform_run_metadata
            
            if self.output_format is None:
                pass
            elif len(self.output_format) != len(self.output_components_list):
                raise ValueError(f"output format {self.output_format} of {self.name} don't match the output components {self.output_components_list}")
            else:
                logger.debug(f"set output component {component.simplified_bids_name} 's format as {self.output_format[index]}")
                component.run_metadata._current_format = self.output_format[index]
            
            if not op.exists(component.run_dir()):
                os.makedirs(component.run_dir())
                logger.warning(f"create directory {component.run_dir()}")
        
        _all_output_component_exist = True        
        for component in self.output_components_set:
            
            if op.exists(component.use_name()):                         
                if component not in self.input_components_set: 
                    
                    logger.warning(f"file {component.use_name()} exist before running, and it not in input components.") 
                    if run_metadata.overwrite: 
                        
                        component.remove_file()
                        logger.warning(f"remove pre-exist file {component.use_name()} because overwrite has been setted")
            
            else:
                _all_output_component_exist = False

                
        if  _all_output_component_exist and not self.output_components_set.issubset(self.input_components_set):
            run_metadata._skip = True
            logger.warning(f"skip running {self.name} because all output components are exist, if a output is also a exist input, this may redo a work") 
           
                    
            


        if self.action is None:            
            raise ValueError(f"action of {self.simplified_bids_name} is not defined")               
        
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

        elif self.action.__name__  == '_run_shell_command':
            
            def _process_item(self, item):
                if isinstance(item, Component):
                    if item in self.input_components_set:
                        return item.use_name()
                    elif item in self.output_components_set:
                        return item.use_name()
                    else:
                        raise ValueError(f"component {item.simplified_bids_name} of {self.name} is not in either input_components or output_components")
                elif isinstance(item, str):                    
                    return item
                
                elif isinstance(item, list):
                    
                    component_position_list = [index for index, item in enumerate(item) if isinstance(item, Component)]
                    len_component_list = len(component_position_list) - 1
                    
                    if len(component_position_list) == 0:
                        self.run_metadata.logger.error(f"no component is given in a list of command arguments when running {self.name} with command list {self.command_list}")
                    if len(component_position_list) > 1:
                        self.run_metadata.logger.error(f"multiple components are given in a list of command arguments when running {self.name} with command list {self.command_list}")
                        raise ValueError(f"multiple components are given in a list of command arguments when running {self.name} with command list {self.command_list}")
                    component_position = component_position_list[0]
                    
                    name_prefix, name_surfix, final_prefix, final_surfix = None, None, None, None
                                            
                    if component_position == 1:
                        final_prefix = item[0]
                    elif component_position == 2:
                        final_prefix, name_prefix = item[0], item[1]
                    
                    if len_component_list - component_position == 1:
                        final_surfix = item[-1]
                    elif len_component_list - component_position == 2:
                        name_surfix, final_surfix = item[-2], item[-1]
                        
                    return item[component_position].name_for_run(name_prefix = name_prefix, name_surfix = name_surfix, final_prefix = final_prefix, final_surfix = final_surfix)
                
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
        logger.info(f"start running command {command} inside _run_shell_command")
        
        
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
        
        
        logger.info(f"finish running command {command} inside _run_shell_command")
        
        
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
    
    def __init__(self, name, work_list = None, output_component_mannual = None, **kwargs):
        
        if work_list is None:
            self.worklist = []
        else:
            self.work_list = work_list
            
                        
        input_components = self.get_input_components
        output_components = self.get_output_components
        
        super().__init__(name, input_components, output_components, **kwargs)
        
        if output_component_mannual is None:
            self.output_components_mannual = set()
        else:
            self.output_components_mannual = output_component_mannual
        
        
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
                        raise ValueError(f"input component {input_component.simplified_bids_name} of work {work.name} is not in any output components of any work")
                    elif len(matched_works) == 1:
                        matched_work = matched_works[0]
                    elif len(matched_works) > 1: #test if they are in the same branch, if not, they are conflict, if yes,only keep the last one
                        matched_works.sort(key = cmp_to_key(ancestor_test))
                        print(f"input component {input_component.simplified_bids_name} of work {work.name} is in output components of multiple works {[matched_work.name for matched_work in matched_works]} in same branch, only keep the last one {matched_works[-1].name}")
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



            
            
            
            