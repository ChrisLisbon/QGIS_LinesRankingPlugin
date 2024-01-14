from pathlib import Path
import numpy as np

from core.constants import INTERMEDIATE_REPLACEMENT
from core.load import load_attributes_file_as_adjacency_list, \
    adjacency_list_to_desired_format
from core.paths import get_project_path

DATA_EXAMPLE = Path(get_project_path(), 'example_data', 'data_example.csv')


def test_adjacency_list_loading():
    """ Loading tabular data from csv file """
    adjacency_list = load_attributes_file_as_adjacency_list(DATA_EXAMPLE)

    assert isinstance(adjacency_list, np.ndarray)
    assert len(adjacency_list) == 8728
    assert adjacency_list[0, 0] == '1'
    assert adjacency_list[0, 1] == '819'


def test_adjacency_list_preparation():
    """ Test that adjacency list correctly converted into list """
    adjacency_list = load_attributes_file_as_adjacency_list(DATA_EXAMPLE)
    lines = adjacency_list_to_desired_format(adjacency_list)

    assert len(lines) == len(adjacency_list)
    assert lines[0] == '1 819'


def test_adjacency_list_preparation_with_non_int_indices():
    """ Desired format should not have ' ' in name """
    adjacency_list = np.array([['index 1', 'index 2'], ['index 1', 'RandomName']])
    lines = adjacency_list_to_desired_format(adjacency_list)

    assert len(lines) == 2
    assert f'index{INTERMEDIATE_REPLACEMENT}1 index{INTERMEDIATE_REPLACEMENT}2' == lines[0]

