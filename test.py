
from base import *
from config import *
test_metadata = RunMetaData(rootdir= r"/mridir", subject="sub-s001", datatype="func", session="ses-1")
test_metadata

config = get_config(None ,"/home/sbc/projects/mefmriprep/config.json")
for key, value in config.items():
    print(f"{key} {value}\n")

test_node1 = Node("node1", describe= "testnode1", suffix="suffix1")
test_node2 = Node("node2", describe= "testnode2", suffix="suffix2")
test_node3 = Node("node3", describe= "testnode3", suffix="suffix3")
test_node4 = Node("node4", describe= "testnode4", suffix="suffix4")
test_node5 = Node("node5", describe= "testnode5", suffix="suffix5")

test_work1 = Work("work1", [test_node1, test_node2], [test_node3, test_node4])
test_work2 = Work("work2", [test_node3, test_node4], [test_node5])

def action1(input_nodes, output_nodes, run_metadata, config, derivatives_path=['test_workdir']):
    print(join_derivatives_path(derivatives_path, run_metadata))

test_work1.action = action1
test_work2.action = action1

test_workflow = Workflow('testworkflow', ['testplace'])
print(test_work1)
test_workflow.add_work(test_work1)
#test_workflow.add_work(test_work2)
test_workflow.run(test_metadata, config)

test_workflow.draw_graph()


workflow1 = Workflow("workflow1", [])
workflow2 = Workflow("workflow2", [])
workflow1.add_work(test_work1)
workflow2.add_work(test_work2)
merged_workflow = Workflow.merge_workflow(workflow1, workflow2)
merged_workflow.run(test_metadata, config)
get_common_nodes_name(workflow1, workflow2)

workflow1.__hash__()