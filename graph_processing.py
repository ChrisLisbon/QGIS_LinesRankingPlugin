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
import warnings

warnings.filterwarnings('ignore')

INTERMEDIATE_REPLACEMENT = "--_--"


def get_project_path() -> Path:
    return Path(__file__).parent


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


def distance_attr(graph: nx.graph, start: str, dataframe: pd.DataFrame,
                  id_field, main_id=None):
    """ Function for assigning weights to graph edges

    :param graph: graph to process
    :param start: vertex from which to start traversal
    :param dataframe: pandas dataframe with 2 columns: id_field (segment/vertex ID)
        and 'length' (length of this segment)
    :param id_field: field in the dataframe, from which it is required to map identifiers
        to vertices of the graph
    :param main_id: index, which designates the main river in the river network
        (default = None)
    """
    # List of all vertexes that can be reached from the start vertex using BFS
    vert_list = list(nx.bfs_successors(graph, source=start))
    # One of the most remote vertices in the graph (this will be necessary for A*)
    last_vertex = vert_list[-1][-1][0]

    for component in vert_list:
        # The vertex where we are at this iteration
        vertex = component[0]
        # Vertices that are neighboring (which we haven't visited yet)
        neighbors = component[1]

        dist_vertex = int(dataframe['length'][dataframe[id_field] == vertex])

        # Assign the segment length value as a vertex attribute
        attrs = {vertex: {'component': 1, 'size': dist_vertex}}
        nx.set_node_attributes(graph, attrs)

        for n in neighbors:

            # If the main index value is not set
            if main_id is None:
                # Assign weights to the edges of the graph
                # The length of the section in meters (int)
                dist_n = int(dataframe['length'][dataframe[id_field] == n])
                # Otherwise we are dealing with a complex composite index
            else:
                # If the vertex we are at is part of the main river
                if vertex.split(':')[0] == main_id:
                    # And at the same time, the vertex that we "look" at from
                    # the vertex "vertex" also, then
                    if n.split(':')[0] == main_id:
                        # The weight value must be zero
                        dist_n = 0
                    else:
                        dist_n = int(
                            dataframe['length'][dataframe[id_field] == n])
                else:
                    dist_n = int(dataframe['length'][dataframe[id_field] == n])
            attrs = {(vertex, n): {'weight': dist_n},
                     (n, vertex): {'weight': dist_n}}
            nx.set_edge_attributes(graph, attrs)

            # Assign attributes to the nodes of the graph
            attrs = {n: {'component': 1, 'size': dist_n}}
            nx.set_node_attributes(graph, attrs)

        # Look at the surroundings of the vertex where we are located
        offspring = list(nx.bfs_successors(graph, source=vertex, depth_limit=1))
        offspring = offspring[0][1]
        # If the weight value was not assigned, we assign it
        for n in offspring:

            if len(graph.get_edge_data(vertex, n)) == 0:

                ##############################
                # Assigning weights to edges #
                ##############################
                if main_id is None:
                    dist_n = int(dataframe['length'][dataframe[id_field] == n])
                else:
                    if vertex.split(':')[0] == main_id:
                        if n.split(':')[0] == main_id:
                            dist_n = 0
                        else:
                            dist_n = int(
                                dataframe['length'][dataframe[id_field] == n])
                    else:
                        dist_n = int(dataframe['length'][dataframe[id_field] == n])
                attrs = {(vertex, n): {'weight': dist_n},
                         (n, vertex): {'weight': dist_n}}
                nx.set_edge_attributes(graph, attrs)
                ##############################
                # Assigning weights to edges #
                ##############################

            elif len(graph.get_edge_data(n, vertex)) == 0:

                ##############################
                # Assigning weights to edges #
                ##############################
                if main_id is None:
                    dist_n = int(dataframe['length'][dataframe[id_field] == n])
                else:
                    if vertex.split(':')[0] == main_id:
                        if n.split(':')[0] == main_id:
                            dist_n = 0
                        else:
                            dist_n = int(dataframe['length'][dataframe[id_field] == n])
                    else:
                        dist_n = int(dataframe['length'][dataframe[id_field] == n])

                attrs = {(vertex, n): {'weight': dist_n},
                         (n, vertex): {'weight': dist_n}}
                nx.set_edge_attributes(graph, attrs)
                ##############################
                # Assigning weights to edges #
                ##############################

    for vertex in list(graph.nodes()):
        # If the graph is incompletely connected, then we delete the
        # elements that we can't get to
        if graph.nodes[vertex].get('component') is None:
            graph.remove_node(vertex)
        else:
            pass
    return last_vertex


def rank_set(graph, start, last_vertex, set_progress_funk = None):
    """
    Function for assigning 'rank' and 'offspring' attributes to graph vertices
    Traversing a graph with attribute assignment
    """
    def bfs_attributes(graph, vertex, kernel_path):
        """

        :param graph: graph as a networkx object
        :param vertex: vertex from which the graph search begins
        :param kernel_path: list of vertexes that are part of the main path
            that the search is being built from
        """
        # Creating a copy of the graph
        graph_copy = graph.copy()

        # Deleting all edges that are associated with the reference vertexes
        for kernel_vertex in kernel_path:
            # Leaving the reference vertex from which we start the crawl
            if kernel_vertex == vertex:
                pass
            else:
                # For all other vertexes, we delete edges
                kernel_n = list(nx.bfs_successors(graph_copy, source=kernel_vertex, depth_limit=1))
                kernel_n = kernel_n[0][1]
                for i in kernel_n:
                    try:
                        graph_copy.remove_edge(i, kernel_vertex)
                    except Exception:
                        pass

        # The obtained subgraph is isolated from all reference vertices,
        # except the one from which the search begins at this iteration
        # Breadth-first search
        all_neighbors = list(nx.bfs_successors(graph_copy, source=vertex))

        #####################################################
        #  Labels are not assigned on an isolated subgraph, #
        #               but on the source graph             #
        #####################################################
        for component in all_neighbors:
            # The vertex where we are at this iteration
            v = component[0]
            # Vertices that are neighboring (which we haven't visited yet)
            neighbors = component[1]

            # Value of the 'rank' attribute in the considering vertex
            att = graph.nodes[v].get('rank')
            if att is not None:
                # The value of the attribute to be assigned to neighboring vertices
                att_number = att + 1

            # We look at all the closest first offspring
            first_n = list(nx.bfs_successors(graph, source=v, depth_limit=1))
            first_n = first_n[0][1]

            # Assigning ranks to vertices
            for i in first_n:
                # If the neighboring vertex is the main node in this iteration, then skip it
                # vertex - the reference point from which we started the search
                if i == vertex:
                    pass
                else:
                    current_i_rank = graph.nodes[i].get('rank')
                    # If the rank value has not yet been assigned, then assign it
                    if current_i_rank == None:
                        attrs = {i: {'rank': att_number}}
                        nx.set_node_attributes(graph, attrs)
                    # If the rank in this node is already assigned
                    else:
                        # The algorithm either "looks back" at vertices that it has already visited
                        # In this case we don't do anything
                        # Either the algorithm "came up" to the main path (kernel path) in the graph
                        if any(i == bearing_v for bearing_v in kernel_path):
                            graph.remove_edge(v, i)
                        else:
                            pass

            # Additional "search"
            for neighbor in neighbors:
                # We look at all the closest first offspring
                first_n = list(nx.bfs_successors(graph, source=neighbor, depth_limit=1))
                first_n = first_n[0][1]

                for i in first_n:
                    # If the neighboring vertex is the main node in this iteration, then skip it
                    # vertex - the reference point from which we started the search
                    if i == vertex:
                        pass
                    else:
                        # The algorithm either "looks back" at vertices that it has already visited
                        # In this case we don't do anything
                        # Either the algorithm "came up" to the main path (kernel path) in the graph
                        if any(i == bearing_v for bearing_v in kernel_path):
                            graph.remove_edge(neighbor, i)
                        else:
                            pass

    # Finding the shortest path A* - building a route around which we will build the next searchs
    a_path = list(nx.astar_path(graph, source=start, target=last_vertex, weight='weight'))

    ##############################
    #   Route validation block   #
    ##############################
    true_a_path = []
    for index, V in enumerate(a_path):
        if index == 0:
            true_a_path.append(V)
        elif index == (len(a_path) - 1):
            true_a_path.append(V)
        else:
            # Previous and next vertices for the reference path (a_path)
            v_prev = a_path[index - 1]
            v_next = a_path[index + 1]

            # Which vertexes are adjacent to this one
            v_prev_neighborhood = list(nx.bfs_successors(graph, source=v_prev, depth_limit=1))
            v_prev_neighborhood = v_prev_neighborhood[0][1]
            v_next_neighborhood = list(nx.bfs_successors(graph, source=v_next, depth_limit=1))
            v_next_neighborhood = v_next_neighborhood[0][1]

            # If the next and previous vertices are connected to each other without an intermediary
            # in the form of vertex V, then vertex V is excluded from the reference path
            if any(v_next == vprev for vprev in v_prev_neighborhood):
                if any(v_prev == vnext for vnext in v_next_neighborhood):
                    pass
                else:
                    true_a_path.append(V)
            else:
                true_a_path.append(V)

    ##############################
    #   Route validation block   #
    ##############################
    # Verification completed
    a_path = true_a_path
    rank = 1
    for v in a_path:
        # Assign the attribute rank value - 1 to the starting vertex.
        # The further away, the greater the value
        attrs = {v: {'rank': rank}}
        nx.set_node_attributes(graph, attrs)
        rank += 1

    # The main route is ready, then we will iteratively move from each node
    all_f = len(a_path)
    for index, vertex in enumerate(a_path):

        if set_progress_funk is not None:
            progress = 58 + (index * 30) / all_f
            set_progress_funk(progress)

        # Starting vertex
        if index == 0:
            next_vertex = a_path[index + 1]

            # Disconnect vertices
            graph.remove_edge(vertex, next_vertex)

            # Subgraph BFS block
            bfs_attributes(graph, vertex=vertex, kernel_path=a_path)

            # Connect vertices back
            graph.add_edge(vertex, next_vertex)

        # Finishing vertex
        elif index == (len(a_path) - 1):
            prev_vertex = a_path[index - 1]

            # Disconnect vertices
            graph.remove_edge(prev_vertex, vertex)

            # Subgraph BFS block
            bfs_attributes(graph, vertex=vertex, kernel_path=a_path)

            # Connect vertices back
            graph.add_edge(prev_vertex, vertex)

        # Vertices that are not the first or last in the reference path
        else:
            prev_vertex = a_path[index - 1]
            next_vertex = a_path[index + 1]

            # Disconnect vertices
            # Previous with current vertex
            try:
                graph.remove_edge(prev_vertex, vertex)
            except Exception as ex:
                pass
            # Current with next vertex
            try:
                graph.remove_edge(vertex, next_vertex)
            except Exception as ex:
                pass

            # Subgraph BFS block
            bfs_attributes(graph, vertex=vertex, kernel_path=a_path)

            # Connect vertices back
            try:
                graph.add_edge(prev_vertex, vertex)
                graph.add_edge(vertex, next_vertex)
            except Exception as ex:
                pass

    # Attribute assignment block - number of descendants
    vert_list = list(nx.bfs_successors(graph, source=start))
    for component in vert_list:
        # The vertex where we are at this iteration
        vertex = component[0]
        # Vertices that are neighboring (which we haven't visited yet)
        neighbors = component[1]

        # Adding an attribute - the number of descendants of this vertex
        n_offspring = len(neighbors)
        attrs = {vertex: {'offspring': n_offspring}}
        nx.set_node_attributes(graph, attrs)


def set_values(graph, considering_rank: int, vert_list: List):
    # For each vertex in the list
    for vertex in vert_list:

        # If value has already been assigned, then skip it
        if graph.nodes[vertex].get('value') == 1:
            pass
        else:
            # Defining descendants
            offspring = list(nx.bfs_successors(graph, source=vertex, depth_limit=1))
            # We use only the nearest neighbors to this vertex (first descendants)
            offspring = offspring[0][1]

            # The cycle of determining the values at the vertices of a descendant
            last_values = []
            last_values_strahler = []
            for child in offspring:
                # We only need descendants whose rank value is greater than that of the vertex
                if graph.nodes[child].get('rank') > considering_rank:
                    if graph.nodes[child].get('value') is not None:
                        last_values.append(graph.nodes[child].get('value'))
                    if graph.nodes[child].get('value_strahler') is not None:
                        last_values_strahler.append(graph.nodes[child].get('value_strahler'))

            last_values = np.array(last_values)
            sum_values = np.sum(last_values)

            # If the amount is not equal to 0, the attribute is assigned
            if sum_values != 0:
                max_v = max(last_values_strahler)
                if len(last_values_strahler) < 2:
                    # Only one parent - Strahler order remain the same
                    nx.set_node_attributes(graph, {vertex: {'value': sum_values,
                                                            'value_strahler': max_v}})
                else:
                    # At least two parents must have the same biggest
                    number_of_biggest_values = len(list(filter(lambda x: x == max_v, last_values_strahler)))
                    if number_of_biggest_values >= 2:
                        nx.set_node_attributes(graph,
                                               {vertex: {'value': sum_values,
                                                         'value_strahler': max_v + 1}})
                    else:
                        # Remain the same
                        nx.set_node_attributes(graph,
                                               {vertex: {'value': sum_values,
                                                         'value_strahler': max_v}})


def iter_set_values(graph, start):
    """ Function for iteratively assigning the value attribute """
    # Vertices and corresponding attribute values
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

    # Largest rank value in a graph
    max_rank = max(ranks_list)

    # Creating pandas dataframe
    df = pd.DataFrame({'ranks': ranks_list,
                       'vertices': vertices_list,
                       'offspring': offspring_list})

    # We assign value = 1 to all vertices of the graph that have no offspring
    value_1_list = list(df['vertices'][df['offspring'] == 0])
    for vertex in value_1_list:
        attrs = {vertex: {'value': 1, 'value_strahler': 1}}
        nx.set_node_attributes(graph, attrs)

    # For each rank, we begin to assign attributes
    for considering_rank in range(max_rank, 0, -1):
        # List of vertices of suitable rank
        vert_list = list(df['vertices'][df['ranks'] == considering_rank])
        set_values(graph, considering_rank, vert_list)

    # Assigning the "distance" attribute to the graph vertices
    # List of all vertexes that can be reached from the start vertex using BFS
    vert_list = list(nx.bfs_successors(graph, source=start))
    for component in vert_list:
        # The vertex where we are at this iteration
        vertex = component[0]
        # Vertices that are neighboring (which we haven't visited yet)
        neighbors = component[1]

        # If we are at the closing vertex
        if vertex == start:
            # Length of this segment
            att_vertex_size = graph.nodes[vertex].get('size')
            # Adding the value of the distance attribute
            attrs = {vertex: {'distance': att_vertex_size}}
            nx.set_node_attributes(graph, attrs)

        vertex_distance = graph.nodes[vertex].get('distance')
        # For each neighbor, we assign an attribute
        for i in neighbors:
            # Adding the value of the distance attribute
            i_size = graph.nodes[i].get('size')
            attrs = {i: {'distance': (vertex_distance + i_size)}}
            nx.set_node_attributes(graph, attrs)


def make_dataframe(graph):
    """ Create dataframe (table) from graph with calculated """
    dataframe = []
    for vertex in list(graph.nodes()):
        rank = graph.nodes[vertex].get('rank')
        value = graph.nodes[vertex].get('value')
        value_strahler = graph.nodes[vertex].get('value_strahler')
        distance = graph.nodes[vertex].get('distance')

        if INTERMEDIATE_REPLACEMENT in str(vertex):
            vertex = str(vertex).replace(INTERMEDIATE_REPLACEMENT, ' ')

        dataframe.append([vertex, rank, value, value_strahler, distance])

    dataframe = pd.DataFrame(dataframe, columns=['fid', 'Rank', 'ValueShreve',
                                                 'ValueStrahler', 'Distance'])
    return dataframe


def overall_call(original_file, attributes_file, start_point_id, length_path, set_progress_funk):
    """ Function which calls all above defined methods for graph ranking task

    :param original_file: example: "D:original_temp.csv"
    :param attributes_file: example: "D:\Ob\points_temp.csv"
    :param start_point_id: example: "3327"
    :param length_path: example: "D:\Ob\attributes_temp.csv"
    :param set_progress_funk: function to display progress bar
    """

    # Read file with attributes and interpret it as adjacency list
    adjacency_list = load_attributes_file_as_adjacency_list(attributes_file)
    lines = adjacency_list_to_desired_format(adjacency_list)
    graph_to_parse = nx.parse_adjlist(lines, nodetype=str)

    # Read file with calculated length of segments
    l_dataframe = pd.read_csv(length_path)
    l_dataframe = l_dataframe.astype({'id': 'str'})

    # Core functionality - perform calculations
    # First - assign ranks
    last_vertex = distance_attr(graph_to_parse, str(start_point_id),
                                l_dataframe, id_field='id')

    # Second - assign offspring
    rank_set(graph_to_parse, str(start_point_id), str(last_vertex),
             set_progress_funk)

    # Third - assign order
    iter_set_values(graph_to_parse, str(start_point_id))

    # Convert ranked graph into table
    dataframe = make_dataframe(graph_to_parse)
    rivers = pd.read_csv(original_file)
    rivers = rivers.astype({'fid': 'str'})
    data_merged = pd.merge(rivers, dataframe, on='fid')
    rows_count = data_merged.shape[0]

    df_dict = {}
    for i in range(rows_count):
        df_dict[int(data_merged.iloc[i]['fid'])] = [int(data_merged.iloc[i]['Rank']),
                                                    int(data_merged.iloc[i]['ValueShreve']),
                                                    int(data_merged.iloc[i]['ValueStrahler']),
                                                    int(data_merged.iloc[i]['Distance'])]
    return df_dict
