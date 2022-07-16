import os
import sys

import pandas as pd

import tree_directory


def get_list_dict_tasks(dict_tasks):

    tasks = dict_tasks["tasks"]
    list_dict = []
    for task in tasks:
        archive = task[0]

        list_file = task[1]
        for file in list_file:
            dict_data = {}
            dict_data["archive"] = os.path.basename(archive)
            dict_data["file_path"] = file
            list_dict.append(dict_data)
    return list_dict


def join_folders(row):

    list_folders = list(row)
    list_folders = [folder for folder in list_folders if folder is not None]
    if list_folders:
        return os.path.join(*list_folders)
    else:
        return None


def get_serie_folder_path_relative(serie_folder_path, max_depth=0):
    """Returns the path of the relative folder of the root folder in common
    to all the file paths in the series

    Args:
        serie_folder_path (pandas.Series): Series to be parsed
    """

    def check_col_unique_values(serie):

        serie_unique = serie.drop_duplicates(keep="first")
        list_unique_values = serie_unique.unique().tolist()
        qt_unique_values = len(list_unique_values)
        if qt_unique_values == 1:
            return True
        else:
            return False

    # create dataframe with columns as sequencial integer and folders as values
    df = serie_folder_path.str.split("\\", expand=True)
    len_cols = len(df.columns)

    list_index_col_root = []
    for n_col in range(len_cols - 1):
        serie = df.iloc[:, n_col]
        # check for column with more than 1 unique value (folder root)
        col_has_one_unique_value = check_col_unique_values(serie)
        if col_has_one_unique_value:
            # name col is a sequencial integer
            name_col = df.columns[n_col]
            list_index_col_root.append(name_col)
        else:
            break
    if len(list_index_col_root) == 0:
        raise ValueError("No root folder found")

    df.drop(list_index_col_root, axis=1, inplace=True)
    if max_depth != 0:
        df = df.iloc[:, :max_depth]
    serie_folder_path_relative = df.apply(join_folders, axis=1)
    return serie_folder_path_relative


def parse_dict_to_list_tree(dict_, deep=0, list_string=[]):

    deep += 1
    list_file_name = []
    list_folder_name = []
    for key_, value_ in dict_.items():
        if isinstance(value_, str):
            list_file_name.append(key_)
        else:
            list_folder_name.append(key_)

    if len(list_file_name) > 0:
        string_files = (
            f'{"+" * deep} ' + f'\n{"+" * deep} '.join(list_file_name) + "\n"
        )
        list_string.append(string_files)
    for folder_name in list_folder_name:
        string_folder_title = "=" * deep + " " + folder_name
        list_string.append(string_folder_title)
        list_string = parse_dict_to_list_tree(
            dict_[folder_name], deep, list_string
        )
    return list_string


def main(dict_tasks):

    list_dict = get_list_dict_tasks(dict_tasks)
    df_raw = pd.DataFrame(list_dict)

    serie_path_relativa = get_serie_folder_path_relative(df_raw["file_path"])
    df_relative = df_raw.copy()
    df_relative["file_path_relative"] = serie_path_relativa
    df_relative.drop("file_path", axis=1, inplace=True)
    serie_content_relative = df_relative.apply(join_folders, axis=1)

    list_content = serie_content_relative.to_list()

    dict_tree_directory = tree_directory.get_tree_directory(list_content)

    list_tree = parse_dict_to_list_tree(
        dict_tree_directory, deep=0, list_string=[]
    )
    string_tree = "\n".join(list_tree)
    return string_tree
