'''
base module for build workflow
construct the workflow without specfic rootdir, subject, session, datatype
and this metadatas will process by 
'''
import os
from os import path as op
import networkx as nx
from itertools import product
from config import Configuartion

class RunMetaData(object):

    def __init__(self, rootdir = None, subject = None, config = None, session = None, datatype = None):
        

        self.rootdir = rootdir
        self.rootdir = rootdir
        self.subject = subject
        self. session = session
        self.datatype = datatype
        self.config = config
        
    
        

class Node(object):
    def __init__(self, node_name, describe = None ,suffix = None, folder: list = None):
        self.name = node_name
        self.describe = describe
        self.surffix = suffix
        self.folder = folder
    
    def __hash__(self):
        return hash((self.name, self.folder))

    def __eq__(self, another) -> bool:
        if isinstance(another, Node):
            return (self.name == another.name and self.folder == another.folder)
        return False
    
class InitialNode(Node):
    pass
    
class Work(object):

    def __init__(self, name, input_nodes:list = None, output_nodes:list = None, action = None, derivatives_place = None):
        
        self.name = name
        if not isinstance(input_nodes, list):
            input_nodes = [input_nodes]
        self.input_nodes = input_nodes
        if not isinstance(output_nodes, list):
            output_nodes = [output_nodes]
            
        self.output_nodes = output_nodes
        self.derivatives_place = derivatives_place
        self.action = action
        
        
    def run(self, run_metadata):

        if self.action is None:
            raise ValueError(f"action for {self.name} has not been defined")

        if derivatives_place is None:
            derivatives_place = self.derivatives_place

        self.action(self.input_nodes, self.output_nodes, run_metadata, derivatives_place)  
    
    @property
    def all_node(self):
        return self.input_nodes + self.output_nodes  

        
class Workflow(Work):
    
    def __init__(self, name, derivatives_place: list, worklist: list = []):
        
        super().__init__(name, derivatives_place = derivatives_place)
        self.name = name
        self.derivatives_place = derivatives_place
        self.worklist = worklist            
        self.output_nodes_mannual = []
    
    def add_work(self, work):        
        self.worklist.append(work)
    
    @property
    def node_as_node_network(self):
        
        dg = nx.DiGraph()        
        dg.add_nodes_from(self.all_node)
        for work in self.worklist:
            dg.add_edges_from(list(product(work.input_nodes, work.output_nodes)))
        return dg
    
    #TODO add revursive derivatives_place
    #unfinished
    def run(self, run_metadata: RunMetaData, config: Configuartion):
        for work in self.works:
            if isinstance(work, Work):
                work.run(run_metadata, config, derivatives_place = self.derivatives_place)

            if isinstance(work, Workflow):
                derivatives_place = self.derivatives_place + work.derivatives_place
                work.run(run_metadata, config, derivatives_place)    

    @property    
    def all_node(self):        
        return [node for work in self.worklist for node in work.all_node]
        

    
    