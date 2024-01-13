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
import pandas as pd
import networkx as nx
import warnings

from core.convert import make_dataframe
from core.load import load_attributes_file_as_adjacency_list, \
    adjacency_list_to_desired_format
from core.main import distance_attr, rank_set
from core.values import iter_set_values

warnings.filterwarnings('ignore')


def overall_call(original_file, attributes_file, start_point_id, length_path, set_progress_funk):
    """ Function which calls all above defined methods for graph ranking task

    :param original_file: example: 'D:original_temp.csv'
    :param attributes_file: example: 'D:\Ob\points_temp.csv'
    :param start_point_id: example: '3327'
    :param length_path: example: 'D:\Ob\attributes_temp.csv'
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
                                                    int(data_merged.iloc[i]['Value']),
                                                    int(data_merged.iloc[i]['Distance'])]
    return df_dict
