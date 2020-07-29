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
warnings.filterwarnings('ignore')
import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd
import random
import time
import networkx as nx

# Function for bringing the adjacency list to the right format
def prepare(list_of_adjacencies):
    lines = []
    for i in list_of_adjacencies:
        i_0 = str(i[0])
        i_1 = str(i[1])
        string = i_0 + ' ' + i_1
        lines.append(string)
    return(lines)

# Function for assigning weights to graph edges
def distance_attr(G, start, dataframe):
    # List of all vertexes that can be reached from the start vertex using BFS
    vert_list = list(nx.bfs_successors(G, source=start))
    # One of the most remote vertices in the graph (this will be necessary for A*)
    last_vertex = vert_list[-1][-1][0]

    for component in vert_list:
        vertex = component[0]  # The vertex where we are at this iteration
        neighbors = component[1]  # Vertices that are neighboring (which we haven't visited yet)

        dist_vertex = int(dataframe['length'][dataframe['id'] == vertex])
        # Assign the segment length value as a vertex attribute
        attrs = {vertex: {'component': 1, 'size': dist_vertex}}
        nx.set_node_attributes(G, attrs)

        for n in neighbors:
            # Assign weights to the edges of the graph
            # The length of the section in meters (int)
            dist_n = int(dataframe['length'][dataframe['id'] == n])
            attrs = {(vertex, n): {'weight': dist_n},
                     (n, vertex): {'weight': dist_n}}
            nx.set_edge_attributes(G, attrs)

            # Assign attributes to the nodes of the graph
            attrs = {n: {'component': 1, 'size': dist_n}}
            nx.set_node_attributes(G, attrs)

        # Look at the surroundings of the vertex where we are located
        offspring = list(nx.bfs_successors(G, source=vertex, depth_limit=1))
        offspring = offspring[0][1]
        # If the weight value was not assigned, we assign it
        for n in offspring:

            if len(G.get_edge_data(vertex, n)) == 0:
                dist_n = int(dataframe['length'][dataframe['id'] == n])
                attrs = {(vertex, n): {'weight': dist_n},
                         (n, vertex): {'weight': dist_n}}
                nx.set_edge_attributes(G, attrs)
            elif len(G.get_edge_data(n, vertex)) == 0:
                dist_n = int(dataframe['length'][dataframe['id'] == n])
                attrs = {(vertex, n): {'weight': dist_n},
                         (n, vertex): {'weight': dist_n}}
                nx.set_edge_attributes(G, attrs)

    for vertex in list(G.nodes()):
        # If the graph is incompletely connected, then we delete the elements that we can't get to
        if G.nodes[vertex].get('component') == None:
            G.remove_node(vertex)
        else:
            pass
    return (last_vertex)

# Function for assigning 'rank' and 'offspring' attributes to graph vertices
def rank_set(G, start, last_vertex, set_progress_funk):

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
                kernel_n = list(nx.bfs_successors(G_copy, source=kernel_vertex, depth_limit=1))
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
            neighbors = component[1]  # Vertices that are neighboring (which we haven't visited yet)

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
                first_n = list(nx.bfs_successors(G, source=neighbor, depth_limit=1))
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

    a_path = list(nx.astar_path(G, source=start, target=last_vertex, weight='weight'))

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
            V_prev = a_path[index - 1]
            V_next = a_path[index + 1]

            # Which vertexes are adjacent to this one
            V_prev_neighborhood = list(nx.bfs_successors(G, source=V_prev, depth_limit=1))
            V_prev_neighborhood = V_prev_neighborhood[0][1]
            V_next_neighborhood = list(nx.bfs_successors(G, source=V_next, depth_limit=1))
            V_next_neighborhood = V_next_neighborhood[0][1]

            # If the next and previous vertices are connected to each other without an intermediary
            # in the form of vertex V, then vertex V is excluded from the reference path
            if any(V_next == VPREV for VPREV in V_prev_neighborhood):
                if any(V_prev == VNEXT for VNEXT in V_next_neighborhood):
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
    RANK = 1
    for v in a_path:
        # Assign the attribute rank value - 1 to the starting vertex. The further away, the greater the value
        attrs = {v: {'rank': RANK}}
        nx.set_node_attributes(G, attrs)
        RANK += 1

    # The main route is ready, then we will iteratively move from each node
    all_f = len(a_path)
    for index, vertex in enumerate(a_path):

        progress = 58 + (index * 30) / all_f
        set_progress_funk(progress)

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
            G.remove_edge(prev_vertex, vertex)
            G.remove_edge(vertex, next_vertex)

            # Subgraph BFS block
            bfs_attributes(G, vertex=vertex, kernel_path=a_path)

            # Connect vertices back
            G.add_edge(prev_vertex, vertex)
            G.add_edge(vertex, next_vertex)

    # Attribute assignment block - number of descendants
    vert_list = list(nx.bfs_successors(G, source=start))
    for component in vert_list:
        vertex = component[0]  # The vertex where we are at this iteration
        neighbors = component[1]  # Vertices that are neighboring (which we haven't visited yet)

        # Adding an attribute - the number of descendants of this vertex
        n_offspring = len(neighbors)
        attrs = {vertex: {'offspring': n_offspring}}
        nx.set_node_attributes(G, attrs)

# Function for determining the order of river segments similar to the Shreve method
# In addition, the "distance" attribute is assigned
def set_values(G, start, iteration):
    # List of all vertexes that can be reached from the start vertex using BFS
    vert_list = list(nx.bfs_successors(G, source=start))

    # Cycle search of the graph by labeling the vertices
    # Each component is a subgraph
    for component in vert_list:
        vertex = component[0]  # The vertex where we are at this iteration
        neighbors = component[1]  # Vertices that are neighboring (which we haven't visited yet)

        att_rank = G.nodes[vertex].get('rank')
        att_offspring = G.nodes[vertex].get('offspring')

        # For the closing segment, perform the following procedure:
        if att_rank == 1:

            # Length of this segment
            att_vertex_size = G.nodes[vertex].get('size')
            # Adding the value of the distance attribute
            attrs = {vertex: {'distance': att_vertex_size}}
            nx.set_node_attributes(G, attrs)

            # Defining descendants
            offspring = list(nx.bfs_successors(G, source=vertex, depth_limit=1))
            # We use only the nearest neighbors to this vertex (first descendants)
            offspring = offspring[0][1]

            # Writing the values of the value attributes for all descendants to the list
            last_values = []
            for child in offspring:
                if G.nodes[child].get('value') != None:
                    last_values.append(G.nodes[child].get('value'))
                else:
                    last_values.append(0)

            last_values = np.array(last_values)
            sum_values = np.sum(last_values)

            # If the amount is not equal to 0, the attribute is assigned
            if sum_values != 0:
                attrs = {vertex: {'value': sum_values}}
                nx.set_node_attributes(G, attrs)
            # Otherwise, the algorithm just hasn't reached it yet, so skip it
            else:
                pass

        # For each neighbor, we assign an attribute
        for i in neighbors:
            # Value of attributes in the considering vertex
            att_rank = G.nodes[i].get('rank')
            att_offspring = G.nodes[i].get('offspring')

            # If no descendants were found for a vertex at the previous stage, it is assigned the value 1
            if att_offspring == None:
                attrs = {i: {'value': 1}}
                nx.set_node_attributes(G, attrs)
                # If a vertex has descendants, we should define the values of the "value" attribute in them
            else:
                # We search for all descendants
                offspring = list(nx.bfs_successors(G, source=i, depth_limit=1))
                # We use only the nearest neighbors to this vertex (first descendants)
                offspring = offspring[0][1]

                # The cycle of determining the values at the vertices of a descendant
                last_values = []
                for child in offspring:
                    # We only need descendants whose rank value is greater than that of the vertex in question
                    if G.nodes[child].get('rank') > att_rank:
                        if G.nodes[child].get('value') != None:
                            last_values.append(G.nodes[child].get('value'))
                        else:
                            pass
                    else:
                        pass

                last_values = np.array(last_values)
                sum_values = np.sum(last_values)

                # If the amount is not equal to 0, the attribute is assigned
                if sum_values != 0:
                    attrs = {i: {'value': sum_values}}
                    nx.set_node_attributes(G, attrs)
                # Otherwise, the algorithm just hasn't reached it yet, so skip it
                else:
                    pass

            # This calculation is made only in the first iteration
            if iteration == 0:
                vertex_distance = G.nodes[vertex].get('distance')

                # Adding the value of the distance attribute
                i_size = G.nodes[i].get('size')
                attrs = {i: {'distance': (vertex_distance + i_size)}}
                nx.set_node_attributes(G, attrs)

# Function for iteratively assigning the value attribute
def iter_set_values(G, start):
    # Defining the maximum value of the rank in this graph
    ranks = []
    for vertex in list(G.nodes()):
        ranks.append(G.nodes[vertex].get('rank'))
    max_rank = max(ranks)

    # We must integrate exactly as many times as there are ranks in the graph
    for iteration in range(0, max_rank):
        set_values(G, start, iteration)

# Creating a dataset where each vertex of the graph is a string
def make_dataframe(G):
    dataframe = []
    for vertex in list(G.nodes()):
        rank = G.nodes[vertex].get('rank')
        value = G.nodes[vertex].get('value')
        distance = G.nodes[vertex].get('distance')
        dataframe.append([vertex, rank, value, distance])

    dataframe = pd.DataFrame(dataframe, columns = ['fid', 'Rank', 'Value', 'Distance'])
    return(dataframe)


def overall_call(original_file, attributes_file, start_point_id, length_path, set_progress_funk):
    data = pd.read_csv(attributes_file)
    list_of_adjacencies = data[['fid', 'fid_2']]
    list_of_adjacencies = np.array(list_of_adjacencies)
    lines = prepare(list_of_adjacencies)
    G = nx.parse_adjlist(lines, nodetype=str)
    l_dataframe = pd.read_csv(length_path)
    l_dataframe = l_dataframe.astype({'id': 'str'})
    last_vertex = distance_attr(G, str(start_point_id), l_dataframe)
    rank_set(G, str(start_point_id), str(last_vertex), set_progress_funk)
    iter_set_values(G, str(start_point_id))
    dataframe = make_dataframe(G)
    print(dataframe.head(5))
    rivers = pd.read_csv(original_file)
    rivers = rivers.astype({'fid': 'str'})
    data_merged = pd.merge(rivers, dataframe, on='fid')
    rows_count = data_merged.shape[0]
    df_dict = {}
    for i in range(rows_count):
        df_dict[int(data_merged.iloc[i]['fid'])] = [int(data_merged.iloc[i]['Rank']), int(data_merged.iloc[i]['Value']), int(data_merged.iloc[i]['Distance'])]
    return df_dict