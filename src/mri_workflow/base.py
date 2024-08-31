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
    def __init__(self, rootdir, subject, session = None, logger = None, overwright = None, preview = False):
        
        if not op.exists(rootdir):
            raise ValueError(f"rootdir {rootdir} in RunMetaData does not exist")
        else:
            self.rootdir = rootdir
        self.subject = subject
        self.session = session
        self._current_derivatives_place = []
        self._recursive_deepth = 0
        self.logger = logger
        self.overwright = overwright
        self.preview = preview
        
        _logger = logging.getLogger(logger)
        _logger.info(f"create RunMetaData with\n rootdir {rootdir}\n subject {subject}\n session {session}\n logger {logger}\n overwright {overwright}\n preview {preview}")
                
    
    @property
    def subjectdir(self):
        return op.join(self.rootdir, self.subject)
    @property
    def sessiondir(self):
        if self.session is None:
            raise ValueError("session is not defined")
        else:
            return op.join(self.rootdir, self.subject, self.session)
    @property
    def session_place(self):
        if self.session is None:
            return op.join(self.subject)
        else:
            return op.join(self.subject, self.session)
class Component(object):
    def __init__(self, desc = None, suffix = None, datatype = None, run_metadata = None, use_extension = False, extension = None, task = None, space = None, echo = None, type = 'run_full_path'):
        
        self.desc = desc
        self.datatype = datatype
        self.suffix = suffix
        self.run_metadata = run_metadata        
        self.extension = extension
        self.use_extension = use_extension
        self.task = task
        self.space = space
        self.echo = echo        
        self.type = type        
            
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
    
    @property
    def run_dir(self):
        if self.run_metadata is None:
            raise ValueError("run_metadata is not defined")
        else:
            return op.join(self.run_metadata.rootdir, *self.run_metadata._current_derivatives_place, self.run_metadata.session_place, self.datatype)
         
    def run_full_path(self, extension = False):
        return op.join(self.run_dir, self.run_bids_name(extension))
    
    def use_name(self, extension = False):
        '''
        the name really give to action
        '''
        match self.type:
            case 'run_full_path':
                return self.run_full_path(extension)
            case 'run_bids_name':
                return self.run_bids_name(extension)           
            case _:
                raise ValueError(f"unknown type {self.type} from {self.bids_name}")
            
    bids_order = {
        'bold': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'dir', 'run', 'echo', 'part', 'chunk', 'space', 'desc'],
        'MP2RAGE': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'flip', 'inv', 'part', 'chunk', 'space', 'desc'],
        'T1w': ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'part', 'chunk', 'space', 'desc'],
        'fmap': ['sub', 'ses', 'acq', 'run', 'gre', 'chunk', 'space', 'desc']
    } 
 
    def _bids_name_generator(self, dic, extension):
        
        ordered_dic = {key: dic[key] for key in Component.bids_order['bold'] if key in dic}
        
        #this true/false judgement can be nested
        if extension or self.use_extension:
            __extension = True
        else:
            __extension = False
            
        if __extension:
            if extension is None:
                raise ValueError(f"extension of {self.bids_name} is not defined, but needed")
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
            
    def bids_name(self, extension = False):
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
        with open(self.run_full_path(extension = True), 'w') as f:
            f.write('test')            
            
    
    def remove_file(self):
        '''
        delete file
        '''
        if op.exists(self.run_full_path(extension = True)):
            os.remove(self.run_full_path(extension = True))

class Initial_component(Component):
    pass

class Work(object):
    '''
    Work is container to wrap actions for a work flow
    input and out put should be a list of components
    '''
    def __init__(self, name, input_components = None, output_components = None, action = None, derivatives_place = None):
        
        self.name = name
                      
        if self._test_component_list(input_components):
            self.input_components = input_components
            
        
        if self._test_component_list(output_components):
            self.output_components = output_components
            
        self.action = action
        
        if derivatives_place is None:
            self.derivatives_place = []
            
        else:
            if not isinstance(derivatives_place, list):
                raise ValueError(f"derivatives_place of {self.name} should be a list")
            else:
                self.derivatives_place = derivatives_place
    
                
    def _test_component_list(self, list_or_set):
        if not isinstance(self, Workflow) and not isinstance(list_or_set, list):
            raise ValueError(f"{self.name} is not a Workflow,  components container should be a list")        
        elif not isinstance(list_or_set, set) and isinstance(self, Workflow):                
            raise ValueError(f"{self.name} is a Workflow, component container of should be a set")
        
        return True 
    
        
        
    @property    
    def all_components(self) -> set:
        return set(self.input_components + self.output_components)
    
    def _pre_run(self, run_metadata):
        
        this_run_metadata = dc(run_metadata)
        this_run_metadata._recursive_deepth += 1
        this_run_metadata._current_derivatives_place = this_run_metadata._current_derivatives_place + self.derivatives_place
        
        logger = logging.getLogger(run_metadata.logger)
        logger.info(f"run {self.name}, recursive deepth is {this_run_metadata._recursive_deepth}")
        
                
        for component in self.output_components:
            component.run_metadata = this_run_metadata
            
            if not op.exists(component.run_dir):
                os.makedirs(component.run_dir)
                logger.warning(f"create directory {component.run_dir}")
                
        for component in self.output_components:
            if op.exists(component.run_full_path(extension = True)):
                logger.warning(f"file {component.run_full_path(extension = True)} exist before running.")
                if run_metadata.overwright:            
                    component.remove_file()
                    logger.warning(f"remove pre-exist file {component.run_full_path(extension = True)} because overwrite has been setted")
                    
        for component in self.input_components:
            if not op.exists(component.run_full_path(extension = True)):
                raise ValueError(f"input component {component.run_full_path(extension = True)} of work {self.name} does not exist")       
        
        if self.action is None:            
            raise ValueError(f"action of {self.bids_name} is not defined")               
        
        return this_run_metadata
        
    def run(self, run_metadata):
        
        this_run_metadata = self._pre_run(run_metadata)
        
        logger = logging.getLogger(run_metadata.logger)
            
            
        if run_metadata.preview:
                            
            for component in self.output_components:
                
                component.make_test_file()
                logger.info(f"make test file {component.run_full_path(extension = True)}")
                              
        elif 'run_metadata' in inspect.signature(self.action).parameters:
            
            _run_input_components = [component.use_name(extension = True) for component in self.input_components]
            _run_output_components = [component.use_name() for component in self.output_components]
            
            logger.info(f"start running action {self.action.__name__} {_run_input_components, _run_output_components} of work {self.name} with run metadata")
            
            self.action(_run_input_components, _run_output_components, this_run_metadata)
            
            logger.info(f"finish running action {self.action.__name__} of work {self.name}")
            
            
        elif 'command_list' in inspect.signature(self.action).parameters:
            
            def _process_item(self, item):
                
                if isinstance(item, Component):
                    if item in self.input_list:
                        return item.use_name(extension=True)
                    elif item in self.output_list:
                        return item.use_name()
                elif isinstance(item, str):                    
                    return item
                else:
                    raise ValueError(f"item {item} of {self.name} is not a Component or a string")
            
            _run_command_list = [_process_item(item) for item in self.command_list]
            
            logger.info(f"start running action {self.action.__name__} {[_run_command_list]} of work {self.name} with command list")
            
                        
        else:
            
            _run_input_components = [component.use_name(extension = True) for component in self.input_components]
            _run_output_components = [component.use_name() for component in self.output_components]
            
            logger.info(f"start running action {self.action.__name__} {_run_input_components, _run_output_components} of work {self.name}")
            
            self.action(_run_input_components, _run_output_components)
            
            logger.info(f"finish running action {self.action.__name__} of work {self.name}")
            
    
        
    def add_action(self, action):
        self.action = action
    
class CommandWork(Work):
    '''
    class to wrap command line as a work
    '''
    
    def __init__(self, name, input_components=None, output_components=None, action=None, derivatives_place=None, command_list = None):
        
        super().__init__(name, input_components, output_components, action, derivatives_place)
        if command_list is None:
            self.command_list = []
        else:
            self.command_list = command_list
        
        self.action = self._run_shell_command
        
        
    def _run_shell_command(command_list: list, run_metadata: RunMetaData):
    
        command = shlex.join(command_list)
        logger = logging.getLogger(run_metadata.logger)
        logger.info(f"start running command {command} inside _run_shell_command")
        
        
        try:
            process = subprocess.Popen(
                command_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr separately
                text=True  # Return strings instead of bytes
            )
            
            # Wait for the process to complete and capture output
            stdout, stderr = process.communicate()
            
            for line in stdout.splitlines:
                logger.debug(line)
                
            for line in stderr.splitlines:
                logger.error(line)
            
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
        
        finally:
            logger.info(f"finish running command {command} inside _run_shell_command")
            
        
    

class Workflow(Work):
    
    def __init__(self, name, work_list = None, derivatives_place = None, output_component_mannual = None):
        
        if work_list is None:
            self.worklist = []
        else:
            self.work_list = work_list
            
                        
        input_components = self.get_input_components
        output_components = self.get_output_components
        
        super().__init__(name, input_components, output_components, derivatives_place = derivatives_place)
        
        if output_component_mannual is None:
            self.output_components_mannual = set()
        else:
            self.output_components_mannual = output_component_mannual
        
        
    def add_work(self, work):
        self.worklist.append(work)
        self.input_components.update(work.input_components)
        self.output_components.update(work.output_components)
    
    @property    
    def cp_directed_graph(self):
        '''
        create a directed graph with components as nodes and works as edges        
        '''
        G = nx.DiGraph()    
        G.add_nodes_from(self.all_components)
        
        for work in self.worklist:
            G.add_edges_from(product(work.input_components, work.output_components))
        
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
        '''
        G = nx.DiGraph()
        
        for work in self.worklist:
            G.add_node(work)
            #TODO may exchange the order work.input_components and G.nodes, to pre-construct a dictinary for the input_components to accelerate the process
            for input_component in work.input_components:
                for already_in_work in G.nodes:
                    matching_components = [
                        output_component
                        for output_component in already_in_work.output_components
                        if input_component == output_component
                    ]
                    if matching_components:
                        G.add_edge(already_in_work, work, components=matching_components)
        
        return G
    
    @property
    def get_output_components(self):
        '''
        get output components of a workflow
        this will return a set of components that are the output of any work that contains the workflow 
        '''
        return {component for work in self.work_list for component in work.output_components}
    
    @property
    def get_input_components(self):
        ''' 
        get input components of a workflow
        '''
        all_input_component = {component for work in self.work_list for component in work.input_components}
        
        return all_input_component.difference(self.get_output_components)
        
                
        
    def run(self, run_metadata):
        
        this_run_metadata = dc(run_metadata)
        this_run_metadata._recursive_deepth += 1
        this_run_metadata._current_derivatives_place = this_run_metadata._current_derivatives_place + self.derivatives_place
        logger = logging.getLogger(run_metadata.logger)
        logger.info(f"run {self.name}, recursive deepth is {this_run_metadata._recursive_deepth}")
        logger.info(f"work_list is {[work.name for work in self.work_list]}")
        
        for work in self.work_list:
              
            work.run(this_run_metadata)  
                
    
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
            self.input_components = self.get_input_components
            return func(self, *args, ** kwargs)
        return wrapper

        
        
        
        



            
            
            
            