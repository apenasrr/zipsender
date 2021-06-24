import os
import sys
import logging


def add_path_script_folders(list_folders_name):

    list_repo_dont_found = []
    for folder_name in list_folders_name:
        path_script_folder = os.path.abspath(
            os.path.join('..', folder_name))
        existence = os.path.isdir(path_script_folder)
        if existence is False:
            list_repo_dont_found.append(path_script_folder)
        else:
            sys.path.append(path_script_folder)

    # alert in case of not found repositories
    qt_not_found = len(list_repo_dont_found)
    if qt_not_found != 0:
        if qt_not_found > 1:
            repo = 'repositories'
        else:
            repo = 'repository'
        str_list_repo_dont_found = '\n'.join(list_repo_dont_found)
        logging.error(f'The {repo} below could not be found. ' +
                        'Make sure it exists with the proper folder ' +
                        f'name.\n{str_list_repo_dont_found}\n')
        exit()


def get_list_folder_to_zip_ready(list_folder_to_zip):
    list_ = []
    for folder_to_zip in list_folder_to_zip:
        if folder_to_zip[0] == '_':
            list_.append(folder_to_zip)
    return list_


def get_folder_to_zip_ready(list_folder_to_zip_ready):

    if len(list_folder_to_zip_ready) == 0:
        return False
    else:
        return list_folder_to_zip_ready[0]


def compile_template(d_keys, template_content):

    for key in d_keys.keys():
        template_content = \
            template_content.replace('{' + key + '}', d_keys[key])
    output_content = template_content
    return output_content


def get_txt_content(file_path):

    list_encode = ['utf-8', 'ISO-8859-1'] # utf8, ansi
    for encode in list_encode:
        try:
            file = open(file_path, 'r', encoding=encode)
            file_content = file.readlines()
            file_content = ''.join(file_content)
            file.close()
            return file_content
        except:
            continue

    file = open(file_path, 'r', encoding=encode)
    file_content = file.readlines()
    raise Exception('encode', f'Cannot open file: {file_path}')
