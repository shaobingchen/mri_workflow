from base_3 import *
from config import *
import action



test_meta_data = RunMetaData('/rootdir', 's001')
echos = range(4)

origin_epi_list = Component.init_multi_components([{'echo': echo_number} for echo_number in echos], space = 'origin', desc = 'origin', suffix = 'bold')
initial_json_list = Component.init_multi_components_from(origin_epi_list, desc = 'origin', extension = 'json')

slicetime_list = Component.init_multi_components_from(origin_epi_list, desc = 'slicetime', extension = '1D')
get_slicetime = [Work(f'get_slicetime_{echo_number}', [origin_epi_list[echo_number]], [slicetime_list[echo_number]], action= get_slicetime_func) for echo_number in echos]




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