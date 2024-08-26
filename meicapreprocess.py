from base_3 import *
from config import *

test_meta_data = RunMetaData('/rootdir', 's001')


initial_epis = [Component(f'origin_epi_echo_{echo_number}', space = 'origin', desc = 'origin', suffix = 'bold', echo = echo_number, datatype = 'func') for echo_number in range(4)]

despiked_epis = [Component.init_from(initial_epi, name = f'{initial_epi.name}_despiked', desc = 'despiked') for initial_epi in initial_epis]

def despike_func(input_file, output_file):
    print(f'despike_func {input_file} {output_file}')

despike = [Work(f'despike_epi_{echo_number}', [initial_epis[echo_number]], [despiked_epis[echo_number]], derivatives_place=['despike']) for echo_number in range(4)]

despike[0].add_action(despike_func)

for work in despike:
    work.run(test_meta_data, [])