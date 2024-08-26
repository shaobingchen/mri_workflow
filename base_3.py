import os 
import os.path as op
import networkx as nx
from itertools import product
from copy import deepcopy as dc

class Component(object):
    def __init__(self, name, desc = None, suffix = None, datatype = None, run_metadata = None, extension = None, task = None, space = None, echo = None):
        
        self.name = name
        self.desc = desc
        self.datatype = datatype
        self.suffix = suffix
        self.run_metadata = run_metadata        
        self._current_derivatives_place = [] #TODO use a heap to store the current derivatives place instead of a variable
        self.extension = extension
        self.task = task
        self.space = space
        self.echo = echo        

        
    @property
    def run_dir(self):
        if self.run_metadata is None:
            raise ValueError("run_metadata is not defined")
        else:
            return op.join(self.run_metadata.rootdir, *self._current_derivatives_place, self.run_metadata.session_place, self.datatype)
        
    @property    
    def run_full_path(self):
        return op.join(self.run_dir, self.run_bids_name)
        
    def set_current_derivative_place(self, derivatives_place):
        if self._current_derivatives_place is None:
            self._current_derivatives_place = derivatives_place
        else:
            raise ValueError("current_derivatives_place is being resetting")
    
    @classmethod
    def init_from(cls, component, **kwargs):
        
        dic = dc(component.__dict__)
        dic.pop('_current_derivatives_place', None)#TODO temperal solution, modify when the heap is used     
        if 'name' not in kwargs.keys():
            raise ValueError("name is required when initial component from another component")        
        for key, value in kwargs.items():
            dic[key] = value
                             
        return cls(**dic)

        
        
    @property
    def run_bids_name(self, extention = False):
   
        '''
        generage file name from dictionary
        '''
        dic = dc(self.__dict__)
        dic.setdefault('sub', self.run_metadata.subject)
        dic.setdefault('ses', self.run_metadata.session)
        
        def generate_name(ordered_dic, extention = False):
            if extention:
                return f'{"_".join([f"{key}-{value}" for key, value in ordered_dic.items() if value is not None])}_{dic['suffix']}.{dic["extension"]}'
            else:
                return f'{"_".join([f"{key}-{value}" for key, value in ordered_dic.items() if value is not None])}_{dic['suffix']}'
            
        
        match self.suffix:
            case "bold":
                order = ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'dir', 'run', 'echo', 'part', 'chunk', 'space', 'desc']
                ordered_dic = {key: dic[key] for key in order if key in dic}
                return generate_name(ordered_dic, extention = extention)
                

            case "MP2RAGE":
                order = ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'flip', 'inv', 'part', 'chunk', 'space', 'desc']
                ordered_dic = {key: dic[key] for key in order if key in dic}
                return generate_name(ordered_dic, extention = extention)

            case "T1w":
                order = ['sub', 'ses', 'task', 'acq', 'ce', 'rec', 'run', 'echo', 'part', 'chunk', 'space', 'desc']
                ordered_dic = {key: dic[key] for key in order if key in dic}
                return generate_name(ordered_dic, extention = extention)
            
            case "fmap":
                ['sub', 'ses', 'acq', 'run', 'chunk', 'space', 'desc']
                ordered_dic = {key: dic[key] for key in order if key in dic}
                return generate_name(ordered_dic, extention = extention)
            
            case _: raise ValueError(f"suffix of {self.name} is not defined")
                
                
                
                

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
        
    def run(self, run_metadata, _current_derivatives_place):
        
        if _current_derivatives_place is None:
            _current_derivatives_place = []
            
        if self.derivatives_place is not None:
            _current_derivatives_place = self.derivatives_place + _current_derivatives_place
            
        if self.action is None:
            
            raise ValueError(f"action of {self.name} is not defined")
        
        for component in self.output_components:
            component.run_metadata = run_metadata
            component.set_current_derivative_place(_current_derivatives_place)
        #may not work properly
        self.action(self.input_components, self.output_components, run_metadata, _current_derivatives_place)
        
    def add_action(self, action):
        self.action = action
    
    

class Workflow(Work):
    
    def __init__(self, name, derivatives_place, worklist = None):
        
        if worklist is None:
            self.worklist = []
        else:
            self.worklist = worklist
        
        #TODO find input component by directed graph        
        input_components = []
        output_components = []
        
        super().__init__(name, input_components, output_components, derivatives_place = derivatives_place)
        
        self.output_components_mannual = []
        
    def add_work(self, work):
        self.worklist.append(work)
    
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
                
        
    def run(self, run_metadata, _current_derivatives_place = None):
        for work in self.worklist:

            if _current_derivatives_place is None:
                _current_derivatives_place = []
            if self.derivatives_place is not None:
                _current_derivatives_place = self.derivatives_place + _current_derivatives_place
                
            work.run(run_metadata, _current_derivatives_place = _current_derivatives_place)  
                
    
    @property
    def all_components(self) -> set:
        return {component for work in self.worklist for component in work.all_components}
    

class RunMetaData(object):
    def __init__(self, rootdir, subject, datatype = None, session = None):
        self.rootdir = rootdir
        self.subject = subject
        self.session = session
        self.datatype = datatype
                
    
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



            
            
            
            