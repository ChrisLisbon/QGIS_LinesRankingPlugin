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

import warnings

from core.load import load_attributes_file_as_adjacency_list, \
    adjacency_list_to_desired_format
from core.main import distance_attr

warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import networkx as nx


# Function for assigning 'rank' and 'offspring' attributes to graph vertices
def rank_set(G, start, last_vertex):
    # Traversing a graph with attribute assignment
    # G           --- graph as a networkx object
    # vertex      --- vertex from which the graph search begins
    # kernel_path --- list of vertexes that are part of the main path that the search is being built from
    def bfs_attributes(G, vertex, kernel_path):

        # Creating a copy of the graph
        G_copy = G.copy()

        # Deleting all edges that are associated with the reference vertexes
        for kernel_vertex in kernel_path:
            # Leaving the reference vertex from which we start the crawl
            if kernel_vertex == vertex:
                pass
            else:
                # For all other vertexes, we delete edges
                kernel_n = list(nx.bfs_successors(G_copy, source=kernel_vertex,
                                                  depth_limit=1))
                kernel_n = kernel_n[0][1]
                for i in kernel_n:
                    try:
                        G_copy.remove_edge(i, kernel_vertex)
                    except Exception:
                        pass

        # The obtained subgraph is isolated from all reference vertices, except the one
        # from which the search begins at this iteration
        # Breadth-first search
        all_neighbors = list(nx.bfs_successors(G_copy, source=vertex))

        ############################################################################
        #                               Attention!                                 #
        # Labels are not assigned on an isolated subgraph, but on the source graph #
        ############################################################################
        for component in all_neighbors:
            v = component[0]  # The vertex where we are at this iteration
            neighbors = component[
                1]  # Vertices that are neighboring (which we haven't visited yet)

            # Value of the 'rank' attribute in the considering vertex
            att = G.nodes[v].get('rank')
            if att != None:
                # The value of the attribute to be assigned to neighboring vertices
                att_number = att + 1

            # We look at all the closest first offspring
            first_n = list(nx.bfs_successors(G, source=v, depth_limit=1))
            first_n = first_n[0][1]

            # Assigning ranks to vertices
            for i in first_n:
                # If the neighboring vertex is the main node in this iteration, then skip it
                # vertex - the reference point from which we started the search
                if i == vertex:
                    pass
                else:
                    current_i_rank = G.nodes[i].get('rank')
                    # If the rank value has not yet been assigned, then assign it
                    if current_i_rank == None:
                        attrs = {i: {'rank': att_number}}
                        nx.set_node_attributes(G, attrs)
                    # If the rank in this node is already assigned
                    else:
                        # The algorithm either "looks back" at vertices that it has already visited
                        # In this case we don't do anything
                        # Either the algorithm "came up" to the main path (kernel path) in the graph
                        if any(i == bearing_v for bearing_v in kernel_path):
                            G.remove_edge(v, i)
                        else:
                            pass

            # Additional "search"
            for neighbor in neighbors:
                # We look at all the closest first offspring
                first_n = list(
                    nx.bfs_successors(G, source=neighbor, depth_limit=1))
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
                            G.remove_edge(neighbor, i)
                        else:
                            pass

                            # Finding the shortest path A* - building a route around which we will build the next searchs

    a_path = list(
        nx.astar_path(G, source=start, target=last_vertex, weight='weight'))

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
            v_prev_neighborhood = list(
                nx.bfs_successors(G, source=v_prev, depth_limit=1))
            v_prev_neighborhood = v_prev_neighborhood[0][1]
            v_next_neighborhood = list(
                nx.bfs_successors(G, source=v_next, depth_limit=1))
            v_next_neighborhood = v_next_neighborhood[0][1]

            # If the next and previous vertices are connected to each other without an intermediary
            # in the form of vertex V, then vertex V is excluded from the reference path
            if any(v_next == VPREV for VPREV in v_prev_neighborhood):
                if any(v_prev == VNEXT for VNEXT in v_next_neighborhood):
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
        # Assign the attribute rank value - 1 to the starting vertex. The further away, the greater the value
        attrs = {v: {'rank': rank}}
        nx.set_node_attributes(G, attrs)
        rank += 1

    # The main route is ready, then we will iteratively move from each node
    for index, vertex in enumerate(a_path):
        # Starting vertex
        if index == 0:
            next_vertex = a_path[index + 1]

            # Disconnect vertices
            G.remove_edge(vertex, next_vertex)

            # Subgraph BFS block
            bfs_attributes(G, vertex=vertex, kernel_path=a_path)

            # Connect vertices back
            G.add_edge(vertex, next_vertex)


        # Finishing vertex
        elif index == (len(a_path) - 1):
            prev_vertex = a_path[index - 1]

            # Disconnect vertices
            G.remove_edge(prev_vertex, vertex)

            # Subgraph BFS block
            bfs_attributes(G, vertex=vertex, kernel_path=a_path)

            # Connect vertices back
            G.add_edge(prev_vertex, vertex)

        # Vertices that are not the first or last in the reference path
        else:
            prev_vertex = a_path[index - 1]
            next_vertex = a_path[index + 1]

            # Disconnect vertices
            # Previous with current vertex
            try:
                G.remove_edge(prev_vertex, vertex)
            except Exception:
                pass
            # Current with next vertex
            try:
                G.remove_edge(vertex, next_vertex)
            except Exception:
                pass

            # Subgraph BFS block
            bfs_attributes(G, vertex=vertex, kernel_path=a_path)

            # Connect vertices back
            try:
                G.add_edge(prev_vertex, vertex)
                G.add_edge(vertex, next_vertex)
            except Exception:
                pass

    # Attribute assignment block - number of descendants
    vert_list = list(nx.bfs_successors(G, source=start))
    for component in vert_list:
        vertex = component[0]  # The vertex where we are at this iteration
        neighbors = component[
            1]  # Vertices that are neighboring (which we haven't visited yet)

        # Adding an attribute - the number of descendants of this vertex
        n_offspring = len(neighbors)
        attrs = {vertex: {'offspring': n_offspring}}
        nx.set_node_attributes(G, attrs)


def set_values(graph, start, considering_rank, vert_list):
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
            for child in offspring:
                # We only need descendants whose rank value is greater than that of the vertex
                if graph.nodes[child].get('rank') > considering_rank:
                    if graph.nodes[child].get('value') != None:
                        last_values.append(graph.nodes[child].get('value'))
                    else:
                        pass
                else:
                    pass

            last_values = np.array(last_values)
            sum_values = np.sum(last_values)

            # If the amount is not equal to 0, the attribute is assigned
            if sum_values != 0:
                attrs = {vertex: {'value': sum_values}}
                nx.set_node_attributes(graph, attrs)
            else:
                pass


# Function for iteratively assigning the value attribute
def iter_set_values(graph, start):
    # Vertices and corresponding attribute values
    ranks_list = []
    vertices_list = []
    offspring_list = []
    for vertex in list(graph.nodes()):
        ranks_list.append(graph.nodes[vertex].get('rank'))
        vertices_list.append(vertex)
        att_offspring = graph.nodes[vertex].get('offspring')

        if att_offspring == None:
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
        attrs = {vertex: {'value': 1}}
        nx.set_node_attributes(graph, attrs)

        # For each rank, we begin to assign attributes
    for considering_rank in range(max_rank, 0, -1):
        # List of vertices of suitable rank
        vert_list = list(df['vertices'][df['ranks'] == considering_rank])
        set_values(graph, start, considering_rank, vert_list)

        # Assigning the "distance" attribute to the graph vertices
    # List of all vertexes that can be reached from the start vertex using BFS
    vert_list = list(nx.bfs_successors(graph, source=start))
    for component in vert_list:
        vertex = component[0]  # The vertex where we are at this iteration
        neighbors = component[
            1]  # Vertices that are neighboring (which we haven't visited yet)

        # If we are at the closing vertex
        if vertex == start:
            # Length of this segment
            att_vertex_size = graph.nodes[vertex].get('size')
            # Adding the value of the distance attribute
            attrs = {vertex: {'distance': att_vertex_size}}
            nx.set_node_attributes(graph, attrs)
        else:
            pass

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
        distance = graph.nodes[vertex].get('distance')
        dataframe.append([vertex, rank, value, distance])

    dataframe = pd.DataFrame(dataframe, columns=['id', 'Rank', 'Value', 'Distance'])
    return dataframe


def overall_call(original_file, attributes_file, start_point_id, length_path, set_progress_funk):
    """ Function which calls all above defined methods """

    # Read file with attributes and interpret it as adjacency list
    adjacency_list = load_attributes_file_as_adjacency_list(attributes_file)
    lines = adjacency_list_to_desired_format(adjacency_list)
    graph_to_parse = nx.parse_adjlist(lines, nodetype=str)

    # Read file with calculated length of segments
    l_dataframe = pd.read_csv(length_path)
    l_dataframe = l_dataframe.astype({'id': 'str'})

    # Core functionality - perform calculations
    last_vertex = distance_attr(graph_to_parse, str(start_point_id), l_dataframe)
    rank_set(graph_to_parse, str(start_point_id), str(last_vertex), set_progress_funk)
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
                                                    int(data_merged.iloc[i]['Value']),
                                                    int(data_merged.iloc[i]['Distance'])]
    return df_dict
