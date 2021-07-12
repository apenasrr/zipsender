from utils import add_path_script_folders
list_folders_name = ['Telegram_filesender']
add_path_script_folders(list_folders_name)
import telegram_filesender
import api_telegram

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
    send_album = int(default_config.get('send_album'))
    list_str_part = [part_singular, part_plural]

    if send_album != 0 and send_album != 1:
        print('\nConfig send_album unrecognized.\n')
        return

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
        if send_album == 1:
            send_files_mode_album_doc(list_dict_description, chat_id, 'me')
        else:
            telegram_filesender.send_files(list_dict_description, chat_id)

        # move project 'zipped folder' to 'uploaded folder'
        path_dir_project = os.path.join(folder_toupload, dir_project_name)
        shutil.move(path_dir_project, folder_uploaded)

        # log messages
        utils.add_log(status='uploaded', msg=dir_project_name)
        print("Upload completed: ", dir_project_name)


def get_list_dict_sent_doc(return_send_files):

    list_dict_sent_doc = []

    for message_file in return_send_files:
        dict_sent_doc = {}
        dict_sent_doc['file_id'] = message_file['document']["file_id"]
        dict_sent_doc['caption'] = message_file['caption']
        dict_sent_doc['message_id'] = int(message_file['message_id'])
        list_dict_sent_doc.append(dict_sent_doc)
    return list_dict_sent_doc


def get_list_message_id(list_dict_sent_doc):

    list_message_id = []
    for dict_sent_doc in list_dict_sent_doc:
        message_id = dict_sent_doc['message_id']
        list_message_id.append(message_id)
    return list_message_id


def send_files_mode_album_doc(list_dict_description, chat_id, chat_id_cache):

    return_send_files = telegram_filesender.send_files(list_dict_description,
                                                       chat_id_cache)
    list_dict_sent_doc = get_list_dict_sent_doc(return_send_files)

    # forward to the destination group in album format
    #  generate "List Media Doc" to create album
    list_list_dict_sent_doc = \
        utils.split_list_in_lists_by_max(list_=list_dict_sent_doc, size_max=10)

    for list_dict_sent_doc in list_list_dict_sent_doc:
        # send to cache group
        list_media_doc = api_telegram.get_list_media_doc(list_dict_sent_doc)

        # forward from cache group to destination group
        api_telegram.send_media_group(chat_id=chat_id,
                                      list_media=list_media_doc)

        # delete messages from cache group
        list_message_id = get_list_message_id(list_dict_sent_doc)
        api_telegram.delete_messages(chat_id=chat_id_cache,
                                     list_message_id=list_message_id)

    return return_send_files


if __name__ == "__main__":
    main()
