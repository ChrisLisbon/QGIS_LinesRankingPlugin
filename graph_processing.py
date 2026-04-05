# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Lines Ranking
                                 A QGIS plugin
                              -------------------
        begin                : 2020-07-07
        copyright            : (C) 2020 by Julia Borisova, Mikhail Sarafanov
        email                : yulashka.htm@yandex.ru, mik_sar@mail.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from pathlib import Path
from typing import Union, List

import numpy as np
import pandas as pd
import networkx as nx
from networkx.exception import NetworkXException
import warnings

warnings.filterwarnings('ignore')

INTERMEDIATE_REPLACEMENT = "--_--"


def get_project_path() -> Path:
    return Path(__file__).parent


def get_length_by_id(dataframe: pd.DataFrame, id_field: str, vertex: str) -> int:
    matched_values = dataframe.loc[
        dataframe[id_field].astype(str) == str(vertex),
        'length'
    ]

    matched_values = matched_values.dropna()

    if matched_values.empty:
        raise KeyError(f'No length found for {id_field}={vertex}')

    return int(float(matched_values.iloc[0]))


def load_attributes_file_as_adjacency_list(attributes_file: Union[str, Path]) -> np.ndarray:
    """Load tabular data with columns fid, fid_2, geometry - points layer."""
    data = pd.read_csv(attributes_file, dtype={'fid': str, 'fid_2': str})
    adjacency_list = data[['fid', 'fid_2']]
    adjacency_list = np.array(adjacency_list)

    return adjacency_list


def adjacency_list_to_desired_format(adjacency_list: Union[np.ndarray, List]):
    """Function for bringing the adjacency list to the right format."""
    lines = []
    for i in adjacency_list:
        i_0 = str(i[0])
        i_1 = str(i[1])

        trigger = ' ' in i_0
        if trigger is True:
            i_0 = i_0.replace(' ', INTERMEDIATE_REPLACEMENT)

        trigger = ' ' in i_1
        if trigger is True:
            i_1 = i_1.replace(' ', INTERMEDIATE_REPLACEMENT)

        string = i_0 + ' ' + i_1
        lines.append(string)

    return lines


def distance_attr(graph: nx.Graph, start: str, dataframe: pd.DataFrame,
                  id_field, main_id=None):
    """Function for assigning weights to graph edges.

    :param graph: graph to process
    :param start: vertex from which to start traversal
    :param dataframe: pandas dataframe with 2 columns: id_field (segment/vertex ID)
        and 'length' (length of this segment)
    :param id_field: field in the dataframe, from which it is required to map identifiers
        to vertices of the graph
    :param main_id: index, which designates the main river in the river network
        (default = None)
    """
    try:
        vert_list = list(nx.bfs_successors(graph, source=start))
    except NetworkXException as ex:
        raise ValueError(
            f'NetworkXException: {ex}. This is most likely because '
            f'the layer is torn. Please try varying the "Snapping '
            f'threshold" parameter'
        )

    last_vertex = vert_list[-1][-1][0]

    for component in vert_list:
        vertex = component[0]
        neighbors = component[1]

        dist_vertex = get_length_by_id(dataframe, id_field, vertex)

        attrs = {vertex: {'component': 1, 'size': dist_vertex}}
        nx.set_node_attributes(graph, attrs)

        for n in neighbors:
            if main_id is None:
                dist_n = get_length_by_id(dataframe, id_field, n)
            else:
                if vertex.split(':')[0] == main_id:
                    if n.split(':')[0] == main_id:
                        dist_n = 0
                    else:
                        dist_n = get_length_by_id(dataframe, id_field, n)
                else:
                    dist_n = get_length_by_id(dataframe, id_field, n)

            attrs = {
                (vertex, n): {'weight': dist_n},
                (n, vertex): {'weight': dist_n}
            }
            nx.set_edge_attributes(graph, attrs)

            attrs = {n: {'component': 1, 'size': dist_n}}
            nx.set_node_attributes(graph, attrs)

        offspring = list(nx.bfs_successors(graph, source=vertex, depth_limit=1))
        offspring = offspring[0][1]

        for n in offspring:
            edge_data_forward = graph.get_edge_data(vertex, n)
            edge_data_backward = graph.get_edge_data(n, vertex)

            if edge_data_forward is None or len(edge_data_forward) == 0:
                if main_id is None:
                    dist_n = get_length_by_id(dataframe, id_field, n)
                else:
                    if vertex.split(':')[0] == main_id:
                        if n.split(':')[0] == main_id:
                            dist_n = 0
                        else:
                            dist_n = get_length_by_id(dataframe, id_field, n)
                    else:
                        dist_n = get_length_by_id(dataframe, id_field, n)

                attrs = {
                    (vertex, n): {'weight': dist_n},
                    (n, vertex): {'weight': dist_n}
                }
                nx.set_edge_attributes(graph, attrs)

            elif edge_data_backward is None or len(edge_data_backward) == 0:
                if main_id is None:
                    dist_n = get_length_by_id(dataframe, id_field, n)
                else:
                    if vertex.split(':')[0] == main_id:
                        if n.split(':')[0] == main_id:
                            dist_n = 0
                        else:
                            dist_n = get_length_by_id(dataframe, id_field, n)
                    else:
                        dist_n = get_length_by_id(dataframe, id_field, n)

                attrs = {
                    (vertex, n): {'weight': dist_n},
                    (n, vertex): {'weight': dist_n}
                }
                nx.set_edge_attributes(graph, attrs)

    for vertex in list(graph.nodes()):
        if graph.nodes[vertex].get('component') is None:
            graph.remove_node(vertex)

    return last_vertex


def rank_set(graph, start, last_vertex, set_progress_funk=None):
    """
    Function for assigning 'rank' and 'offspring' attributes to graph vertices.
    Traversing a graph with attribute assignment.
    """
    def bfs_attributes(graph, vertex, kernel_path):
        """

        :param graph: graph as a networkx object
        :param vertex: vertex from which the graph search begins
        :param kernel_path: list of vertexes that are part of the main path
            that the search is being built from
        """
        graph_copy = graph.copy()

        for kernel_vertex in kernel_path:
            if kernel_vertex == vertex:
                pass
            else:
                kernel_n = list(nx.bfs_successors(graph_copy, source=kernel_vertex, depth_limit=1))
                kernel_n = kernel_n[0][1]
                for i in kernel_n:
                    try:
                        graph_copy.remove_edge(i, kernel_vertex)
                    except Exception:
                        pass

        all_neighbors = list(nx.bfs_successors(graph_copy, source=vertex))

        for component in all_neighbors:
            v = component[0]
            neighbors = component[1]

            att = graph.nodes[v].get('rank')
            if att is not None:
                att_number = att + 1

            first_n = list(nx.bfs_successors(graph, source=v, depth_limit=1))
            first_n = first_n[0][1]

            for i in first_n:
                if i == vertex:
                    pass
                else:
                    current_i_rank = graph.nodes[i].get('rank')
                    if current_i_rank is None:
                        attrs = {i: {'rank': att_number}}
                        nx.set_node_attributes(graph, attrs)
                    else:
                        if any(i == bearing_v for bearing_v in kernel_path):
                            graph.remove_edge(v, i)
                        else:
                            pass

            for neighbor in neighbors:
                first_n = list(nx.bfs_successors(graph, source=neighbor, depth_limit=1))
                first_n = first_n[0][1]

                for i in first_n:
                    if i == vertex:
                        pass
                    else:
                        if any(i == bearing_v for bearing_v in kernel_path):
                            graph.remove_edge(neighbor, i)
                        else:
                            pass

    a_path = list(nx.astar_path(graph, source=start, target=last_vertex, weight='weight'))

    true_a_path = []
    for index, v_current in enumerate(a_path):
        if index == 0:
            true_a_path.append(v_current)
        elif index == (len(a_path) - 1):
            true_a_path.append(v_current)
        else:
            v_prev = a_path[index - 1]
            v_next = a_path[index + 1]

            v_prev_neighborhood = list(nx.bfs_successors(graph, source=v_prev, depth_limit=1))
            v_prev_neighborhood = v_prev_neighborhood[0][1]
            v_next_neighborhood = list(nx.bfs_successors(graph, source=v_next, depth_limit=1))
            v_next_neighborhood = v_next_neighborhood[0][1]

            if any(v_next == vprev for vprev in v_prev_neighborhood):
                if any(v_prev == vnext for vnext in v_next_neighborhood):
                    pass
                else:
                    true_a_path.append(v_current)
            else:
                true_a_path.append(v_current)

    a_path = true_a_path
    rank = 1
    for v in a_path:
        attrs = {v: {'rank': rank}}
        nx.set_node_attributes(graph, attrs)
        rank += 1

    all_f = len(a_path)
    for index, vertex in enumerate(a_path):
        if set_progress_funk is not None:
            progress = 58 + (index * 30) / all_f
            set_progress_funk(progress)

        if index == 0:
            next_vertex = a_path[index + 1]

            graph.remove_edge(vertex, next_vertex)
            bfs_attributes(graph, vertex=vertex, kernel_path=a_path)
            graph.add_edge(vertex, next_vertex)

        elif index == (len(a_path) - 1):
            prev_vertex = a_path[index - 1]

            graph.remove_edge(prev_vertex, vertex)
            bfs_attributes(graph, vertex=vertex, kernel_path=a_path)
            graph.add_edge(prev_vertex, vertex)

        else:
            prev_vertex = a_path[index - 1]
            next_vertex = a_path[index + 1]

            try:
                graph.remove_edge(prev_vertex, vertex)
            except Exception:
                pass

            try:
                graph.remove_edge(vertex, next_vertex)
            except Exception:
                pass

            bfs_attributes(graph, vertex=vertex, kernel_path=a_path)

            try:
                graph.add_edge(prev_vertex, vertex)
                graph.add_edge(vertex, next_vertex)
            except Exception:
                pass

    vert_list = list(nx.bfs_successors(graph, source=start))
    for component in vert_list:
        vertex = component[0]
        neighbors = component[1]

        n_offspring = len(neighbors)
        attrs = {vertex: {'offspring': n_offspring}}
        nx.set_node_attributes(graph, attrs)


def set_values(graph, considering_rank: int, vert_list: List):
    for vertex in vert_list:
        if graph.nodes[vertex].get('value') == 1:
            pass
        else:
            offspring = list(nx.bfs_successors(graph, source=vertex, depth_limit=1))
            offspring = offspring[0][1]

            last_values = []
            last_values_strahler = []
            for child in offspring:
                if graph.nodes[child].get('rank') > considering_rank:
                    if graph.nodes[child].get('value') is not None:
                        last_values.append(graph.nodes[child].get('value'))
                    if graph.nodes[child].get('value_strahler') is not None:
                        last_values_strahler.append(graph.nodes[child].get('value_strahler'))

            last_values = np.array(last_values)
            sum_values = np.sum(last_values)

            if sum_values != 0:
                max_v = max(last_values_strahler)
                if len(last_values_strahler) < 2:
                    nx.set_node_attributes(
                        graph,
                        {vertex: {'value': sum_values, 'value_strahler': max_v}}
                    )
                else:
                    number_of_biggest_values = len(
                        list(filter(lambda x: x == max_v, last_values_strahler))
                    )
                    if number_of_biggest_values >= 2:
                        nx.set_node_attributes(
                            graph,
                            {vertex: {'value': sum_values, 'value_strahler': max_v + 1}}
                        )
                    else:
                        nx.set_node_attributes(
                            graph,
                            {vertex: {'value': sum_values, 'value_strahler': max_v}}
                        )


def iter_set_values(graph, start):
    """Function for iteratively assigning the value attribute."""
    ranks_list = []
    vertices_list = []
    offspring_list = []
    for vertex in list(graph.nodes()):
        ranks_list.append(graph.nodes[vertex].get('rank'))
        vertices_list.append(vertex)
        att_offspring = graph.nodes[vertex].get('offspring')

        if att_offspring is None:
            offspring_list.append(0)
        else:
            offspring_list.append(att_offspring)

    max_rank = max(ranks_list)

    df = pd.DataFrame({
        'ranks': ranks_list,
        'vertices': vertices_list,
        'offspring': offspring_list
    })

    value_1_list = list(df['vertices'][df['offspring'] == 0])
    for vertex in value_1_list:
        attrs = {vertex: {'value': 1, 'value_strahler': 1}}
        nx.set_node_attributes(graph, attrs)

    for considering_rank in range(max_rank, 0, -1):
        vert_list = list(df['vertices'][df['ranks'] == considering_rank])
        set_values(graph, considering_rank, vert_list)

    vert_list = list(nx.bfs_successors(graph, source=start))
    for component in vert_list:
        vertex = component[0]
        neighbors = component[1]

        if vertex == start:
            att_vertex_size = graph.nodes[vertex].get('size')
            attrs = {vertex: {'distance': att_vertex_size}}
            nx.set_node_attributes(graph, attrs)

        vertex_distance = graph.nodes[vertex].get('distance')
        for i in neighbors:
            i_size = graph.nodes[i].get('size')
            attrs = {i: {'distance': (vertex_distance + i_size)}}
            nx.set_node_attributes(graph, attrs)


def make_dataframe(graph):
    """Create dataframe (table) from graph with calculated attributes."""
    dataframe = []
    for vertex in list(graph.nodes()):
        rank = graph.nodes[vertex].get('rank')
        value = graph.nodes[vertex].get('value')
        value_strahler = graph.nodes[vertex].get('value_strahler')
        distance = graph.nodes[vertex].get('distance')

        if INTERMEDIATE_REPLACEMENT in str(vertex):
            vertex = str(vertex).replace(INTERMEDIATE_REPLACEMENT, ' ')

        dataframe.append([vertex, rank, value, value_strahler, distance])

    dataframe = pd.DataFrame(
        dataframe,
        columns=['fid', 'Rank', 'ValueShreve', 'ValueStrahler', 'Distance']
    )
    return dataframe


def overall_call(original_file, attributes_file, start_point_id, length_path, set_progress_funk):
    """Function which calls all above defined methods for graph ranking task.

    :param original_file: example: "D:original_temp.csv"
    :param attributes_file: example: "D:\\Ob\\points_temp.csv"
    :param start_point_id: example: "3327"
    :param length_path: example: "D:\\Ob\\attributes_temp.csv"
    :param set_progress_funk: function to display progress bar
    """
    adjacency_list = load_attributes_file_as_adjacency_list(attributes_file)
    lines = adjacency_list_to_desired_format(adjacency_list)
    graph_to_parse = nx.parse_adjlist(lines, nodetype=str)

    l_dataframe = pd.read_csv(length_path)
    l_dataframe = l_dataframe.astype({'id': 'str'})

    last_vertex = distance_attr(
        graph_to_parse,
        str(start_point_id),
        l_dataframe,
        id_field='id'
    )

    rank_set(
        graph_to_parse,
        str(start_point_id),
        str(last_vertex),
        set_progress_funk
    )

    iter_set_values(graph_to_parse, str(start_point_id))

    dataframe = make_dataframe(graph_to_parse)
    rivers = pd.read_csv(original_file)
    rivers = rivers.astype({'fid': 'str'})
    data_merged = pd.merge(rivers, dataframe, on='fid')
    rows_count = data_merged.shape[0]

    df_dict = {}
    for i in range(rows_count):
        df_dict[int(data_merged.iloc[i]['fid'])] = [
            int(data_merged.iloc[i]['Rank']),
            int(data_merged.iloc[i]['ValueShreve']),
            int(data_merged.iloc[i]['ValueStrahler']),
            int(data_merged.iloc[i]['Distance'])
        ]

    return df_dict
