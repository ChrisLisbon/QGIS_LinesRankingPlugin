import networkx as nx
import pandas as pd


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
