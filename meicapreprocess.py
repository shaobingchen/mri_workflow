from src.neuroworkflow.base import Component, Work, Workflow, RunMetaData, CommandWork
import actions
from config import *
import actions
import logging
import time




test_meta_data = RunMetaData('/home/sbc/data/test_dataset', '001', logger = 'test_log')


logger = logging.getLogger('test_log')
logger.setLevel(logging.DEBUG)
filehandler = logging.FileHandler(os.path.join(test_meta_data.rootdir, f"{test_meta_data.subject}_{time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())}.log"))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)

 
echos = range(4)

origin_epi_list = Component.init_multi_components([{'echo': echo_number+1 } for echo_number in echos], suffix = 'bold', datatype = 'func', extension = 'nii', run_metadata = test_meta_data)
copied_origin_epi_list = Component.init_multi_components_from(origin_epi_list, desc = 'copied', space = 'origin', use_extension = True)

copy_epis = [Work(f'copy_epi_{echo_number + 1}',
                  [origin_epi_list[echo_number]],
                  [copied_origin_epi_list[echo_number]],
                  action = actions.copy_file
                  ) for echo_number in echos]

set_matrix = [CommandWork(f'set_matrix_{echo_number + 1}',
                          [copied_origin_epi_list[echo_number]],
                          [],
                          command_list=['nifti_tool', '-mod_hdr', '-mod_field', 'sform_code', '1', '-mod_field', 'qform_code', '1', '-infiles', copied_origin_epi_list[echo_number], '-overwrite']
                          ) for echo_number in echos]

despiked_epi_list = Component.init_multi_components_from(copied_origin_epi_list, desc = 'despiked', use_extension = False)

despike = [CommandWork(f'despike_epi_{echo_number + 1}',
                       [copied_origin_epi_list[echo_number]],
                       [despiked_epi_list[echo_number]],
                       ['3dDespike', '-overwrite', '-prefix', despiked_epi_list[echo_number], copied_origin_epi_list[echo_number]]
                       )for echo_number in echos]

base_mask_echo1 = Component.init_from(despiked_epi_list[0],
                                      desc = 'motionbase'
                                      )

motion_base = CommandWork(f'generate_motion_base',
                          [despiked_epi_list[0]],
                          [base_mask_echo1],
                          ['3dcalc', '-a', despiked_epi_list[0], '-expr', 'a', '-prefix', base_mask_echo1]
                          )

motion_estimate_dfile = Component.init_from(despiked_epi_list[0],
                                            desc = 'motion_estimate',
                                            extension = '1D'
                                            )

motion_estimate_matrix = Component.init_from(despiked_epi_list[0], desc = 'motion_estimate', extension = 'aff12.1D')

motion_estmite = CommandWork(f'motion_estimate',
                             [despiked_epi_list[0]],
                             [motion_estimate_dfile, motion_estimate_matrix],
                             ['3dvolreg', '-tshift', 'quintic', '-1Dmatrix_save', motion_estimate_matrix, '-1Dfile', motion_estimate_dfile, '-prefix', motion_estimate_matrix, '-base', base_mask_echo1, despiked_epi_list[0]]
                             ) 


preprocess = Workflow('preprocess', copy_epis + set_matrix + despike + [motion_base, motion_estmite], derivatives_place = ['mepreprocess'])
preprocess.run(test_meta_data)













# origin_epi_list = Component.init_multi_components([{'echo': echo_number+1 } for echo_number in echos], suffix = 'bold', datatype = 'func', extension = 'nii', run_metadata = test_meta_data)

# print([epi.bids_name() for epi in origin_epi_list])

# for component in origin_epi_list:
#     os.makedirs(component.run_dir, exist_ok = True)
#     component.make_test_file()
    
# origin_json_list = Component.init_multi_components_from(origin_epi_list, extension = 'json')

# for component in origin_json_list:
#     os.makedirs(component.run_dir, exist_ok = True)
#     component.make_test_file()
    
# slicetime_list = Component.init_multi_components_from(origin_epi_list, desc = 'slicetime', extension = '1D')

# get_slicetime = [Work(f'get_slicetime_{echo_number}', [origin_epi_list[echo_number]], [slicetime_list[echo_number]], action= action.get_slicetime) for echo_number in echos]

# workflow = Workflow('test_workflow', get_slicetime, derivatives_place = ['mepreprocess'])

# workflow.run(test_meta_data)

# despiked_epi_list = Component.init_multi_components_from(origin_epi_list, desc = 'despiked')
# motion_estimate_matrix_list = Component.init_multi_components_from(origin_epi_list, desc = 'motion_estimate', suffix = 'mat')
# motion_estimate_parameter_list = Component.init_multi_components_from(origin_epi_list, desc = 'motion_estimate', suffix = 'para')




# despike = [Work(f'despike_epi_{echo_number}', [origin_epi_list[echo_number]], [despiked_epi_list[echo_number]]) for echo_number in range(4)]







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