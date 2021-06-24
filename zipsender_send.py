from utils import add_path_script_folders
list_folders_name = ['Telegram_filesender']
add_path_script_folders(list_folders_name)
import telegram_filesender

import pandas as pd
import os
import shutil
import time
import utils
from configparser import ConfigParser


def gen_data_frame(path_folder):

    list_data = []
    for root, dirs, files in os.walk(path_folder):
        for file in files:
            d = {}
            file_path = os.path.join(root, file)
            d['file_output'] = file_path
            d['description'] = file
            list_data.append(d)

    df = pd.DataFrame(list_data)
    list_columns = ['file_output', 'description']
    df = df.reindex(list_columns, axis=1)

    return df


def create_description_report(folder_toupload, dir_project_name):

    path_dir_project = os.path.join(folder_toupload, dir_project_name)
    path_dir_project_output = os.path.join(path_dir_project, 'output')
    path_description = os.path.join(path_dir_project, 'descriptions.xlsx')

    df = gen_data_frame(os.path.abspath(path_dir_project_output))
    df.to_excel(path_description, index=False)
    folder_path_description = os.path.join(folder_toupload, dir_project_name)
    return folder_path_description


def get_personalize_description(list_dict_description, list_str_part, custom_description):

    first_file_description = list_dict_description[0]['description']

    # set count_parts
    last_file_description = list_dict_description[-1]['description']
    count_parts_raw = last_file_description.split('-')[-1]
    count_parts_raw2 = int(count_parts_raw.split('.')[0])
    count_parts = f'{count_parts_raw2:02}'

    # set str_part
    if count_parts_raw2 == 1:
        str_part = list_str_part[0]
    else:
        str_part = list_str_part[1]


    d_keys = {'count_parts': count_parts,
              'str_part': str_part}


    template_content = utils.get_txt_content(custom_description)
    description_bottom = utils.compile_template(d_keys, template_content)

    description_personalized = first_file_description + '\n' + description_bottom

    return description_personalized


def update_descriptions(list_dict_description, description_personalized):

    list_dict_description[0]['description'] = description_personalized
    return list_dict_description


def main():

    config = ConfigParser()
    config.read('config.ini')
    default_config = dict(config['default'])

    # Define variables
    folder_toupload = default_config.get('folder_toupload')
    folder_uploaded = default_config.get('folder_uploaded')
    chat_id = int(default_config.get('chat_id'))
    part_singular = default_config.get('part_singular')
    part_plural = default_config.get('part_plural')
    custom_description = default_config.get('custom_description')
    list_str_part = [part_singular, part_plural]

    while True:
        # get list of folders
        list_folder_to_upload = os.listdir(folder_toupload)
        list_folder_to_upload_ready = utils.get_list_folder_to_zip_ready(list_folder_to_upload)

        # get first folder ready to upload
        dir_project_name = utils.get_folder_to_zip_ready(list_folder_to_upload_ready)
        if dir_project_name is False:
            # wait for new folder to appear, trying periodically
            time.sleep(5)
            continue

        # create description.xlsx
        folder_path_description = create_description_report(folder_toupload, dir_project_name)
        list_dict_description = telegram_filesender.get_list_desc(folder_path_description)

        # set custom description for first file
        first_description_personalized = get_personalize_description(list_dict_description, list_str_part, custom_description)
        list_dict_description = update_descriptions(list_dict_description, first_description_personalized)

        # send files via telegram API
        telegram_filesender.send_files(list_dict_description, chat_id)

        # move project 'zipped folder' to 'uploaded folder'
        path_dir_project = os.path.join(folder_toupload, dir_project_name)
        shutil.move(path_dir_project, folder_uploaded)

        # log messages
        utils.add_log(status='uploaded', msg=dir_project_name)
        print("Upload completed: ", dir_project_name)


if __name__ == "__main__":
    main()
