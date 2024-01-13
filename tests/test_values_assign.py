from pathlib import Path
import pandas as pd
import networkx as nx

from core.constants import INTERMEDIATE_REPLACEMENT
from core.convert import make_dataframe
from core.load import load_attributes_file_as_adjacency_list, \
    adjacency_list_to_desired_format
from core.main import distance_attr, rank_set
from core.mock import get_toy_length_table, get_toy_adjacency_list
from core.paths import get_project_path
from core.values import iter_set_values

DATA_EXAMPLE = Path(get_project_path(), 'example_data', 'data_example.csv')
DATA_LENGTH = Path(get_project_path(), 'example_data', 'data_example_length.csv')


def prepare_graph_with_ranks():
    adjacency_list = load_attributes_file_as_adjacency_list(DATA_EXAMPLE)
    lines = adjacency_list_to_desired_format(adjacency_list)
    graph_to_parse: nx.Graph = nx.parse_adjlist(lines, nodetype=str)

    l_dataframe = pd.read_csv(DATA_LENGTH)
    l_dataframe = l_dataframe.astype({'id': 'str'})

    last_vertex = distance_attr(graph_to_parse, '1', l_dataframe, 'id')
    rank_set(graph_to_parse, '1', last_vertex)

    return graph_to_parse, '1', last_vertex


def test_values_assignment_performed_correctly():
    """ Check that distance ranking performed correctly on the graph """
    ranked_graph, start_vertex, last_vertex = prepare_graph_with_ranks()
    iter_set_values(ranked_graph, start_vertex)

    # Check attributes on first node
    assert ranked_graph.nodes[start_vertex]
    assert ranked_graph.nodes[start_vertex]['value'] == 744
    assert ranked_graph.nodes[start_vertex]['offspring'] == 3

    # Check attributes on last node
    assert ranked_graph.nodes[last_vertex]
    assert ranked_graph.nodes[last_vertex]['value'] == 1

    # Convert in dataframe (table form is a final one)
    dataframe = make_dataframe(ranked_graph)

    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 3336
    assert dataframe.iloc[0]['Value'] == 744


def test_toy_example():
    """ Check algorithm correctness on the very simple case """
    adjacency_list = get_toy_adjacency_list()
    lines = adjacency_list_to_desired_format(adjacency_list)
    graph_to_parse: nx.Graph = nx.parse_adjlist(lines, nodetype=str)

    l_dataframe = get_toy_length_table()
    last_vertex = distance_attr(graph_to_parse, 'Final', l_dataframe, 'id')
    rank_set(graph_to_parse, 'Final', last_vertex)

    iter_set_values(graph_to_parse, 'Final')
    dataframe = make_dataframe(graph_to_parse)

    assert len(dataframe) == 6
    assert dataframe.iloc[0]['Value Shreve'] == 4
    assert dataframe.iloc[0]['Value Strahler'] == 2
    assert dataframe.iloc[0]['Rank'] == 1
