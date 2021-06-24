import os
from zipsender_zip import folder_tozip
from configparser import ConfigParser


def main():

    config = ConfigParser()
    config.read('config.ini')
    default_config = dict(config['default'])

    # Define variables
    folder_tozip = default_config.get('folder_tozip')

    # get folders list
    list_folders = os.listdir(folder_tozip)

    # get folders to auth
    list_folder_to_auth = []
    for folder_name in list_folders:
        folder_path_from = os.path.join(folder_tozip, folder_name)
        if folder_name[0] != '_':
            list_folder_to_auth.append(folder_name)

    # set auth folders
    for folder_to_auth in list_folder_to_auth:
        folder_path_from = os.path.join(folder_tozip, folder_to_auth)
        folder_name_to = '_' + folder_to_auth
        folder_path_to = os.path.join(folder_tozip, folder_name_to)
        os.rename(folder_path_from, folder_path_to)


if __name__ == "__main__":
    main()