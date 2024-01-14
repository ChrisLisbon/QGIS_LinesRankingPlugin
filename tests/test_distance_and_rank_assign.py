from pathlib import Path
import pandas as pd
import networkx as nx

from graph_processing import get_project_path, load_attributes_file_as_adjacency_list, \
    adjacency_list_to_desired_format, distance_attr, rank_set

DATA_EXAMPLE = Path(get_project_path(), 'example_data', 'data_example.csv')
DATA_LENGTH = Path(get_project_path(), 'example_data', 'data_example_length.csv')


def test_assignment_performed_correctly_without_main_river():
    """ Check that distance ranking performed correctly on the graph """
    adjacency_list = load_attributes_file_as_adjacency_list(DATA_EXAMPLE)
    lines = adjacency_list_to_desired_format(adjacency_list)
    graph_to_parse: nx.Graph = nx.parse_adjlist(lines, nodetype=str)

    l_dataframe = pd.read_csv(DATA_LENGTH)
    l_dataframe = l_dataframe.astype({'id': 'str'})

    # Check that last vertex was founded correctly
    last_vertex = distance_attr(graph_to_parse, '1', l_dataframe, 'id')

    assert last_vertex == '2959'

    # Assign ranks
    rank_set(graph_to_parse, '1', last_vertex)

    assert graph_to_parse.nodes['1']['rank'] == 1
    assert graph_to_parse.nodes[last_vertex]['rank'] == 294
