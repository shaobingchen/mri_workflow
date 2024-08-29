from base import *
from config import *
import action



test_meta_data = RunMetaData('/home/sbc/data/test', 's001', preview = True) 
echos = range(4)

origin_epi_list = Component.init_multi_components([{'echo': echo_number} for echo_number in echos], space = 'origin', desc = 'origin', suffix = 'bold', datatype = 'func', extension = 'nii', run_metadata = test_meta_data)

for component in origin_epi_list:
    os.makedirs(component.run_dir, exist_ok = True)
    component.make_test_file()
    
origin_json_list = Component.init_multi_components_from(origin_epi_list, desc = 'origin', extension = 'json')

for component in origin_json_list:
    os.makedirs(component.run_dir, exist_ok = True)
    component.make_test_file()
    
slicetime_list = Component.init_multi_components_from(origin_epi_list, desc = 'slicetime', extension = '1D')

get_slicetime = [Work(f'get_slicetime_{echo_number}', [origin_epi_list[echo_number]], [slicetime_list[echo_number]], action= action.get_slicetime, derivatives_place=['test2'], ) for echo_number in echos]

workflow = Workflow('test_workflow', get_slicetime, derivatives_place = ['test1'])

workflow.run(test_meta_data)




despiked_epi_list = Component.init_multi_components_from(origin_epi_list, desc = 'despiked')
motion_estimate_matrix_list = Component.init_multi_components_from(origin_epi_list, desc = 'motion_estimate', suffix = 'mat')
motion_estimate_parameter_list = Component.init_multi_components_from(origin_epi_list, desc = 'motion_estimate', suffix = 'para')




despike = [Work(f'despike_epi_{echo_number}', [origin_epi_list[echo_number]], [despiked_epi_list[echo_number]]) for echo_number in range(4)]







# <<<<<<<<<<<< test using original tools 

# initial_epis = [Component(f'origin_epi_echo_{echo_number}', space = 'origin', desc = 'origin', suffix = 'bold', echo = echo_number, datatype = 'func') for echo_number in range(4)]

# despiked_epis = [Component.init_from(initial_epi, name = f'{initial_epi.name}_despiked', desc = 'despiked') for initial_epi in initial_epis]

# def despike_func(input_file, output_file, runmetadata):
#     print(f'despike_func {input_file} {output_file}')

# despike = [Work(f'despike_epi_{echo_number}', [initial_epis[echo_number]], [despiked_epis[echo_number]], derivatives_place=['despike']) for echo_number in range(4)]

# for work in despike:
#     work.add_action(despike_func)

# for work in despike:
#     work.run(test_meta_data)

# >>>>>>>>>>> test using original tools 