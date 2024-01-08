import networkx as nx
import pandas as pd


def distance_attr(graph: nx.graph, start: str, dataframe: pd.DataFrame,
                  id_field, main_id=None):
    """ Function for assigning weights to graph edges """
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
