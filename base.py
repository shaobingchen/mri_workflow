import os 
import os.path as op
import networkx as nx
from itertools import product
from copy import deepcopy as dc
import inspect

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
            print(f"{self.run_metadata.rootdir}, {self.run_metadata._current_derivatives_place}, {self.run_metadata.session_place}, {self.datatype}")
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
        'fmap': ['sub', 'ses', 'acq', 'run', 'chunk', 'space', 'desc']
    } 
 
    def _bids_name_generator(self, dic, extension):
        
        ordered_dic = {key: dic[key] for key in Component.bids_order['bold'] if key in dic}
        
        #this true/false judgement can be nested
        if extension or self.use_extension:
            __extension = True
        else:
            __extension = False
            
        if __extension:
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
                

class Initial_component(Component):
    pass

class Work(object):
    '''
    Work is container to wrap actions for a work flow
    input and out put should be a list of components
    '''
    def __init__(self, name, input_components = None, output_components = None, action = None, derivatives_place = None):
        
        self.name = name
        if not isinstance(input_components, list):
            raise ValueError(f"input_nodes of {self.name} should be a list")
        else:
            self.input_components = input_components
        
        if not isinstance(output_components, list):
            raise ValueError(f"output_nodes of {self.name} should be a list")
        else:
            self.output_components = output_components
            
        self.action = action
        
        if derivatives_place is None:
            self.derivatives_place = []
            
        else:
            if not isinstance(derivatives_place, list):
                raise ValueError(f"derivatives_place of {self.name} should be a list")
            else:
                self.derivatives_place = derivatives_place
        
    @property    
    def all_components(self) -> set:
        return set(self.input_components + self.output_components)
        
    def run(self, run_metadata):
        
        this_run_metadata = dc(run_metadata)
        this_run_metadata._recursive_deepth += 1
        this_run_metadata._current_derivatives_place = this_run_metadata._current_derivatives_place + self.derivatives_place
                
        for component in self.output_components:
            component.run_metadata = this_run_metadata
            
            if not op.exists(component.run_dir):
                os.makedirs(component.run_dir)
    
        if run_metadata.overwright:
            for component in self.output_components:
                if op.exists(component.run_full_path(extension = True)):
                    os.remove(component.run_full_path(extension = True))
                    
        for component in self.input_components:
            if not op.exists(component.run_full_path(extension = True)):
                raise ValueError(f"input component {component.run_full_path(extension = True)} of work {self.name} does not exist")       
             
        if self.metadata.preview:
                            
            for component in self.output_components:
                
                with open(component.run_full_path(extension = True), 'w') as f:
                    f.write('test')
                    
            return 0
            
            
        if self.action is None:            
            raise ValueError(f"action of {self.bids_name} is not defined")        
                        
        if 'run_metadata' in inspect.signature(self.action).parameters:
            
            self.action([component.use_name(extension = True) for component in self.input_components], [component.use_name() for component in self.output_components], run_metadata)
        else:
            self.action([component.use_name(extension = True) for component in self.input_components], [component.use_name() for component in self.output_components])
            
        return 0
    
        
    def add_action(self, action):
        self.action = action
    
    

class Workflow(Work):
    
    def __init__(self, name, derivatives_place, worklist = None, output_component_mannual = None):
        
        if worklist is None:
            self.worklist = []
        else:
            self.worklist = worklist
                        
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
        return {component for work in self.worklist for component in work.output_components}
    
    @property
    def get_input_components(self, component):
        ''' 
        get input components of a component
        '''
        all_input_component = {work.input_components for work in self.worklist if component in work.input_components}
        
        return all_input_component.difference(self.get_output_components)
        
                
        
    def run(self, run_metadata):
        
        this_run_metadata = dc(run_metadata)
        this_run_metadata._recursive_deepth += 1
        this_run_metadata.current_derivatives_place = this_run_metadata.current_derivatives_place + self.derivatives_place
        
        
        for work in self.worklist:
              
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

class RunMetaData(object):
    '''
    RunMetaData is a class to store the metadata of a run
    '''
    def __init__(self, rootdir, subject, datatype = None, session = None, logger = None, overwright = None, preview = False):
        
        self.rootdir = rootdir
        self.subject = subject
        self.session = session
        self.datatype = datatype
        self._current_derivatives_place = []
        self._recursive_deepth = 0
        self.logger = logger
        self.overwright = overwright
        self.preview = preview
                
    
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
        
            
    @property
    def datatypedir(self):
        if self.session is None:
            return op.join(self.rootdir, self.subject, self.datatype)
        else:   
            return op.join(self.rootdir, self.subject, self.session, self.datatype)
        
        



            
            
            
            