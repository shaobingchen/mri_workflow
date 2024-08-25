import os 
import os.path as op
import networkx as nx
from itertools import product

class Component(object):
    def __init__(self, name, describe = None, suffix = None, folder = None):
        self.name = name
        self.describe = describe
        self.folder = folder
    

class Initial_component(Component):
    pass

class Work(object):
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
        print(self.action)
        if self.action is None:
            raise ValueError(f"action of {self.name} is not defined")
        
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
        G = nx.DiGraph()    
        G.add_nodes_from(self.all_components)
        
        for work in self.worklist:
            G.add_edges_from(product(work.input_components, work.output_components))
        
        return G
    
    def draw_graph(self, file_name = "workflow.png"):
        
        import matplotlib.pyplot as plt
        
        nx.draw(self.cp_directed_graph, with_labels=True, labels= {component: component.name for work in self.worklist for component in work.all_components}, node_color='lightblue', node_size=700, arrowstyle='-|>', arrowsize=20)
        plt.savefig(file_name)
        
        
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
    def __init__(self, rootdir, subject, datatype, session = None):
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
    def datatypedir(self):
        if self.session is None:
            return op.join(self.rootdir, self.subject, self.datatype)
        else:   
            return op.join(self.rootdir, self.subject, self.session, self.datatype)



