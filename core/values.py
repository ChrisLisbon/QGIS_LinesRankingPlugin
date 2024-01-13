from typing import List

import networkx as nx
import numpy as np
import pandas as pd


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
