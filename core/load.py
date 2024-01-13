from pathlib import Path
from typing import Union, List

import numpy as np
import pandas as pd

from core.constants import INTERMEDIATE_REPLACEMENT


def load_attributes_file_as_adjacency_list(attributes_file: Union[str, Path]) -> np.ndarray:
    """ Load tabular data with columns fid, fid_2, geometry - points layer """
    data = pd.read_csv(attributes_file, dtype={'fid': str, 'fid_2': str})
    adjacency_list = data[['fid', 'fid_2']]
    adjacency_list = np.array(adjacency_list)

    return adjacency_list


def adjacency_list_to_desired_format(adjacency_list: Union[np.ndarray, List]):
    """ Function for bringing the adjacency list to the right format """
    lines = []
    for i in adjacency_list:
        i_0 = str(i[0])
        i_1 = str(i[1])

        # Block for checking spaces in a line
        # Left part
        trigger = ' ' in i_0
        if trigger is True:
            i_0 = i_0.replace(' ', INTERMEDIATE_REPLACEMENT)

        # Right part
        trigger = ' ' in i_1
        if trigger is True:
            i_1 = i_1.replace(' ', INTERMEDIATE_REPLACEMENT)

        string = i_0 + ' ' + i_1
        lines.append(string)
    return lines
