import networkx as nx
import bids
import os
from itertools import product
import matplotlib.pyplot as plt

class MyFile(object):

    def __init__(self, file_dir):
        self.file_dir = file_dir

    def set_file_dir(self, directory):
        if directory is None or not isinstance(directory, str):
            raise ValueError("Invalid directory. Please provide a valid string path.")
        self.file_dir = directory
    
    @property
    def file_name(self):
        if self.file_dir is None:
            raise ValueError("directory hasn't been set")
        return os.path.basename(self.file_dir)

class RunMetaData(object):

    def __init__(self, rootdir, subject, session = None, datatype = None):
        if datatype is None:
            raise ValueError("datatype is required")
        
        self.rootdir = rootdir
        self.subject = subject
        self. session = session
        self.datatype = datatype
    
    @property
    def directory_path(self):
        return os.path.join(self.rootdir, self.__join_temp_place)
    
    def set_derivatives_place(self, derivatives_place):
        self.derivatives_place = derivatives_place

    @property
    def __join_temp_place(self):
        if self.session is None:
            return os.path.join(self.subject, self.datatype)
        else:
            return os.path.join(self.subject, self.session, self.datatype)

    @property
    def derivatives_path(self):   
        if isinstance(self.derivatives_place, str):
            if os.path.exists(self.derivatives_place):
                return self.derivatives_place
            else:
                return os.path.join(self.rootdir, self.derivatives_place, self.__join_temp_place)
        elif isinstance(self.derivatives_place, list):
            return os.path.join(self.rootdir, *self.derivatives_place, self.__join_temp_place)
        else:
            raise ValueError("derivatives_place can only be str or list")
    
               
#TODO class for parse filename 
    

class Node(object):
    def __init__(self, node_name, describe = None ,suffix = None, derivatives_place = None):
        self.name = node_name
        self.describe = describe
        self.surffix = suffix
        self.derivative_place = derivatives_place
        self.files = []
    
    def __hash__(self):
        return hash((self.name, self.derivative_place))

    def __eq__(self, another) -> bool:
        if isinstance(another, Node):
            return (self.name == another.name and self.derivative_place == another.derivative_place)
        return False
    
    def add_file(self, file_dir):
        self.files.append(MyFile(file_dir))
        
    
    
class Work(object):

    def __init__(self, name, input_nodes = None, output_nodes = None,action = None):
        self.name = name
        if not isinstance(input_nodes, list):
            input_nodes = [input_nodes]
        self.input_nodes = input_nodes
        if not isinstance(output_nodes, list):
            output_nodes = [output_nodes]
        self.output_nodes = output_nodes
        self.action = action

    @property
    def get_add_node(self):
        return self.input_nodes + self.output_nodes
    
    
    def run(self, run_metadata: RunMetaData):
        if self.action is None:
            raise ValueError(f"action for {self.name} has not been defined")
        self.action(self.input_nodes, self.output_nodes, run_metadata)

def get_common_nodes(workflow1, workflow2):
    return set(workflow1.nodes()) & set(workflow2.nodes())

def get_common_works(workflow1, workflow2):
    return set(workflow1.work()) & set(workflow2.work())

def get_common_nodes_name(workflow1, workflow2):
    return {node.name for node in get_common_nodes(workflow1, workflow2)}

def get_common_works_name(workflow1, workflow2):
    return {work.name for work in get_common_works(workflow1, workflow2)}

class Workflow(nx.DiGraph):
    
    def __init__(self, incoming_graph_data=None, **attr):
         super().__init__(incoming_graph_data, **attr)
         self.works = []

    def add_work(self, work: Work):

        self.add_nodes_from(work.get_add_node)
        self.add_edges_from(list(product(work.input_nodes, work.output_nodes)))
        self.works.append(work)

    def run(self,run_metadata: RunMetaData):
        for work in self.works:
            work.run(run_metadata)
        
    def draw_graph(self, file_name = "workflow.png"):

        nx.draw(self, with_labels=True, labels= {node: node.name for node in self.nodes()}, node_color='lightblue', node_size=700, arrowstyle='-|>', arrowsize=20)
        plt.savefig(file_name)
        
    def add_workflow(self, workflow: 'Workflow'):
        self.add_node(workflow)

    #TODO add workflow to workflow    
    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, another) -> bool:
        if isinstance(another, Workflow):
            return set(self.nodes()) == set(another.nodes()) and set(self.edges()) == set(another.edges())
        return False
        
    @classmethod
    def merge_workflow(cls, *workflows):
        new_workflow = cls()
        for workflow in workflows:
            new_workflow.add_nodes_from(workflow.nodes())
            new_workflow.add_edges_from(workflow.edges())
            new_workflow.works += workflow.works
        return new_workflow
    