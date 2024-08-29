from base import *
from config import *
# test_metadata = RunMetaData(rootdir= r"/mridir", subject="sub-s001", datatype="func", session="ses-1")
# test_metadata

# config = get_config(None ,"/home/sbc/projects/mefmriprep/config.json")
# for key, value in config.items():
#     print(f"{key} {value}\n")

test_component1 = Component("component1", describe= "testcomponent1", suffix="suffix1")
test_component2 = Component("component2", describe= "testcomponent2", suffix="suffix2")
test_component3 = Component("component3", describe= "testcomponent3", suffix="suffix3")
test_component4 = Component("component4", describe= "testcomponent4", suffix="suffix4")
test_component5 = Component("component5", describe= "testcomponent5", suffix="suffix5")

test_work1 = Work("work1", [test_component1, test_component2], [test_component3, test_component4])
test_work2 = Work("work2", [test_component3, test_component4], [test_component5])

# print(test_work1.all_components)

test_workflow = Workflow('test_workflow', None)
test_workflow.add_work(test_work1)
test_workflow.add_work(test_work2)

def test_action(input_nodes, output_nodes, run_metadata, derivatives_place):
    print(f"input_nodes: {input_nodes}")
    print(f"output_nodes: {output_nodes}")
    print(f"run_metadata: {run_metadata}")
    print(f"derivatives_place: {derivatives_place}")
    print("action has been executed")
    
test_work1.add_action(test_action)
test_work2.add_action(test_action)

#print(test_workflow.all_components)
test_workflow.draw_graph() 

test_workflow.run(None)