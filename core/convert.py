import pandas as pd

from core.constants import INTERMEDIATE_REPLACEMENT


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
