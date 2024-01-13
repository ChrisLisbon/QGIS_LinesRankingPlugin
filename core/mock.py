import pandas as pd

from core.constants import INTERMEDIATE_REPLACEMENT


def get_toy_adjacency_list():
    adjacency_list = [['Final', 'Middle first'], ['Final', 'Middle second'],
                      ['Middle first', 'Final'],
                      ['Middle first', 'Middle second'],
                      ['Middle second', 'Final'],
                      ['Middle second', 'Middle first'],
                      ['Middle first', 'Tail first'],
                      ['Middle first', 'Tail second'],
                      ['Middle first', 'Tail third'],
                      ['Tail first', 'Middle first'],
                      ['Tail first', 'Tail second'],
                      ['Tail first', 'Tail third'],
                      ['Tail second', 'Middle first'],
                      ['Tail second', 'Tail first'],
                      ['Tail third', 'Middle first'],
                      ['Tail third', 'Tail first']]
    return adjacency_list


def get_toy_length_table():
    len_dataframe = pd.DataFrame(
        {'id': ['Final', f'Middle{INTERMEDIATE_REPLACEMENT}first',
                f'Middle{INTERMEDIATE_REPLACEMENT}second',
                f'Tail{INTERMEDIATE_REPLACEMENT}first',
                f'Tail{INTERMEDIATE_REPLACEMENT}second',
                f'Tail{INTERMEDIATE_REPLACEMENT}third'],
         'length': [100, 150, 150, 250, 200, 200]})

    return len_dataframe
