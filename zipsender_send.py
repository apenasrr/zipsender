import json
import os
import shutil
import time
from configparser import ConfigParser
from pathlib import Path

import pandas as pd
from tgsender import tgsender
from zipind import zipind_utils

import upload_plan
import zipsender_utils


def gen_data_frame(path_folder):

    list_data = []
    for root, _, files in os.walk(path_folder):
        for file in files:
            d = {}
            file_path = os.path.join(root, file)
            d["file_path"] = file_path
            d["description"] = file
            list_data.append(d)

    df = pd.DataFrame(list_data)
    list_columns = ["file_path", "description"]
    df = df.reindex(list_columns, axis=1)

    return df


def create_description_report(folder_toupload, folder_project_name):

    path_dir_project = os.path.join(folder_toupload, folder_project_name)
    path_dir_project_output = os.path.join(path_dir_project, "output")
    path_description = os.path.join(path_dir_project, "upload_plan.csv")

    df = gen_data_frame(os.path.abspath(path_dir_project_output))
    df.to_csv(path_description, index=False)


def get_personalize_description(
    list_dict_description, list_str_part, custom_description
):

    first_file_description = list_dict_description[0]["description"]

    # set count_parts
    last_file_description = list_dict_description[-1]["description"]
    count_parts_raw = last_file_description.split("-")[-1]
    count_parts_raw2 = int(count_parts_raw.split(".")[0])
    count_parts = f"{count_parts_raw2:02}"

    # set str_part
    if count_parts_raw2 == 1:
        str_part = list_str_part[0]
    else:
        str_part = list_str_part[1]

    d_keys = {"count_parts": count_parts, "str_part": str_part}

    template_content = zipsender_utils.get_txt_content(custom_description)
    description_bottom = zipsender_utils.compile_template(
        d_keys, template_content
    )

    description_personalized = (
        first_file_description + "\n" + description_bottom
    )

    return description_personalized


def update_descriptions(
    list_dict_description,
    description_personalized,
    log_folder_path,
    folder_project_name,
    title_log_file_list,
    project_metadata,
):
    """
    1 - Add a text file with a tree-map of each packages and their internal
    files. (project log)
    2 - set custom description for first file

    Args:
        list_dict_description (list[dict]): Files descriptions
        description_personalized (str): Text to personalize first description
        log_folder_path (str): Path of log_folder
        folder_project_name (str): Name of project folder
        title_log_file_list (str): Description of a text file 'project log'
        project_metadata (dict): project metadata

    Returns:
        list[dict]: Descriptions updates
    """

    def compose_log_description(
        project_name_show, title_log_file_list, project_metadata
    ):

        log_description = f"{project_name_show}\n{title_log_file_list}"
        if "stream_link" in project_metadata.keys():
            # update log_description with watch_online line
            stream_link = project_metadata.get("stream_link")
            line_watch_online = f"Watch Online: {stream_link}"
            log_description = f"{log_description}\n\n{line_watch_online}"
        return log_description

    # body
    # Add project file structure
    folder_project_name = folder_project_name.strip("_")
    path_file_log = os.path.join(log_folder_path, folder_project_name + ".txt")
    project_name_show = folder_project_name.replace("_", " ")

    log_description = compose_log_description(
        project_name_show, title_log_file_list, project_metadata
    )

    dict_log = {"file_path": path_file_log, "description": log_description}
    list_dict_log = [dict_log]

    # personalize first file description
    list_dict_description[0]["description"] = description_personalized

    list_dict_description_updated = list_dict_log + list_dict_description
    return list_dict_description_updated


def get_list_dict_sent_doc(list_log_file_path: list[Path]) -> list[dict]:
    """From file sent log files, returns a list of dictionaries
    with key caption, message_id, file_id.

    Args:
        list_log_file_path (list[Path]):
            List of paths of shipping log files

    Raises:
        Exception:
            If file_id of a log data is invalid according to API

    Returns:
        list[dict]:
            List of dict with keys: caption, message_id, file_id
    """

    list_dict_sent_doc = []
    list_message_file = []

    # Open all JSON files
    for log_file_path in list_log_file_path:
        message_file = json.load(open(log_file_path, encoding="utf-8"))
        list_message_file.append(message_file)

    # Mount List_Dict with needed keys and, in parallel, mount message_id list
    list_message_id = []
    for message_file in list_message_file:
        dict_sent_doc = {}
        dict_sent_doc["caption"] = message_file["caption"]
        message_id = int(message_file["id"])
        dict_sent_doc["message_id"] = message_id
        chat_id = int(message_file["chat"]["id"])
        list_dict_sent_doc.append(dict_sent_doc)
        list_message_id.append(message_id)

    # Capture all updated file_id from the message_id list
    list_message_file_id = tgsender.api.get_messages(chat_id, list_message_id)

    # Complement list_dict with file_id
    for index, message_data in enumerate(list_message_file_id):

        if message_data.document:

            list_dict_sent_doc[index][
                "file_id"
            ] = message_data.document.file_id

        elif message_data.photo:
            list_dict_sent_doc[index]["file_id"] = message_data.photo.file_id
        else:
            raise Exception("File not found")

    return list_dict_sent_doc


def get_list_message_id(list_dict_sent_doc):

    list_message_id = []
    for dict_sent_doc in list_dict_sent_doc:
        message_id = dict_sent_doc["message_id"]
        list_message_id.append(message_id)
    return list_message_id


def send_files_mode_album_doc(
    dir_project_name,
    list_dict_description,
    chat_id,
    chat_id_cache,
    log_project_sent_folder_path,
    sticker=None,
):
    # TODO: Make any file in the report other than document,
    # be sent to the album
    ## If first file is a photo,
    ## it must be separated from the list and not sent inside the album
    ## but only sent at the end, outside the album
    ## This album used supports only document files
    first_dict_description = list_dict_description[0]
    first_file_extension = str(
        Path(first_dict_description.get("file_path")).suffix
    ).lower()
    dict_cover_image = None
    if first_file_extension in [".jpg", ".png", ".gif"]:
        dict_cover_image = list_dict_description[0]
        # Removes the image from the list of files to be sent via album
        list_dict_description = list_dict_description[1:].copy()

    list_log_file_path = tgsender.api.send_files(
        list_dict_description,
        chat_id_cache,
        folder_path_project=Path(log_project_sent_folder_path),
    )

    list_dict_sent_doc = get_list_dict_sent_doc(list_log_file_path)

    # save 'sent files to cache group' metadata
    name_file_sent_1 = dir_project_name + "-report_sent_1" + ".csv"
    path_file_sent_1 = os.path.join(
        log_project_sent_folder_path, name_file_sent_1
    )
    df_files_metadata = pd.DataFrame(list_dict_sent_doc)
    df_files_metadata.to_csv(path_file_sent_1, index=False)

    # forward to the destination group in album format
    #  generate "List Media Doc" to create album
    list_list_dict_sent_doc = zipsender_utils.split_list_in_lists_by_max(
        list_=list_dict_sent_doc, size_max=10
    )

    if sticker:
        tgsender.api.send_sticker(chat_id, sticker)
    # If there is cover image, Send Directly before sending the album
    if dict_cover_image:
        tgsender.api.send_photo(
            chat_id,
            dict_cover_image["file_path"],
            dict_cover_image["description"],
        )

    list_return_send_media_group = []
    for list_dict_sent_doc in list_list_dict_sent_doc:

        # forward from cache group to destination group
        while True:
            try:
                # send to cache group
                list_media_doc = tgsender.api.get_list_media_doc(
                    list_dict_sent_doc
                )
                return_send_media_group = tgsender.api.send_media_group(
                    chat_id=chat_id, list_media=list_media_doc
                )
                list_return_send_media_group.append(return_send_media_group)
                break
            except Exception as e:
                print(e)
                print("\nError. Trying again...")
                time.sleep(5)
                continue

        try:
            # delete messages from cache group
            list_message_id = get_list_message_id(list_dict_sent_doc)
            tgsender.api.delete_messages(
                chat_id=chat_id_cache, list_message_id=list_message_id
            )
        except Exception as e:
            print(e)
            print("\nError while clearing cache group.")

    # save sent album metadata
    stringa = str(list_return_send_media_group)
    name_file_sent_2 = dir_project_name + "-report_sent_2" + ".txt"
    path_file_sent_2 = os.path.join(
        log_project_sent_folder_path, name_file_sent_2
    )
    zipsender_utils.create_txt(path_file_sent_2, str(stringa))


def get_project_metadata(folder_path_description):

    # body
    project_metadata_path = Path(folder_path_description) / ".config"
    if project_metadata_path.exists():
        project_metadata = zipsender_utils.load_json(project_metadata_path)
    else:
        project_metadata = {}
    return project_metadata


def main():

    config = ConfigParser()
    config.read("config.ini", "UTF-8")
    default_config = dict(config["default"])

    # Define variables
    folder_toupload = default_config.get("folder_toupload")
    folder_uploaded = default_config.get("folder_uploaded")
    chat_id = int(default_config.get("chat_id"))
    chat_id_cache = default_config.get("chat_id_cache")
    chat_id_cache = "me" if chat_id_cache is None else int(chat_id_cache)
    time_limit = int(default_config.get("time_limit", 50))
    sticker = default_config.get("sticker")
    part_singular = default_config.get("part_singular")
    part_plural = default_config.get("part_plural")
    custom_description = default_config.get("custom_description")
    send_album = int(default_config.get("send_album"))
    log_sent_folder_path = default_config.get("log_project_sent_folder_path")
    list_str_part = [part_singular, part_plural]
    title_log_file_list = default_config.get("title_log_file_list")

    zipind_utils.ensure_folder_existence([log_sent_folder_path])

    if send_album != 0 and send_album != 1:
        print("\nConfig send_album unrecognized.\n")
        return

    tgsender.api.ensure_connection()

    while True:
        # get list of folders
        list_folder_to_upload = os.listdir(folder_toupload)
        list_folder_to_upload_ready = (
            zipsender_utils.get_list_folder_to_zip_ready(list_folder_to_upload)
        )
        # get first folder ready to upload
        folder_project_name = zipsender_utils.get_folder_to_zip_ready(
            list_folder_to_upload_ready
        )
        if folder_project_name is False:
            # wait for new folder to appear, trying periodically
            time.sleep(5)
            continue

        # create upload_plan.csv
        create_description_report(folder_toupload, folder_project_name)

        folder_path_description = os.path.join(
            folder_toupload, folder_project_name
        )

        list_dict_description = tgsender.get_data_upload_plan(
            Path(folder_path_description)
        )

        # Add a text file with a tree-map of each packages and their internal
        #     files. (project log)
        #     And set custom description for for first file
        first_description_personalized = get_personalize_description(
            list_dict_description, list_str_part, custom_description
        )

        project_metadata = get_project_metadata(folder_path_description)

        list_dict_description = update_descriptions(
            list_dict_description,
            first_description_personalized,
            log_sent_folder_path,
            folder_project_name,
            title_log_file_list,
            project_metadata,
        )

        # Update upload plan with cover and project description in txt
        list_dict_description = upload_plan.update(
            list_dict_description,
            Path(folder_toupload),
            folder_project_name,
        )

        log_project_sent_folder_path = (
            Path(log_sent_folder_path) / folder_project_name
        )
        if not log_project_sent_folder_path.exists():
            log_project_sent_folder_path.mkdir()

        # send files via telegram API
        if send_album == 1:
            send_files_mode_album_doc(
                folder_project_name,
                list_dict_description,
                chat_id,
                chat_id_cache,
                log_project_sent_folder_path,
                sticker,
            )
        else:
            log_folder_project = (
                Path(log_sent_folder_path) / folder_project_name
            )
            if not log_folder_project.exists():
                log_folder_project.mkdir()

            tgsender.api.send_files(
                list_dict_description, chat_id, time_limit, log_folder_project
            )

        # move project 'zipped folder' to 'uploaded folder'
        path_dir_project = os.path.join(folder_toupload, folder_project_name)
        shutil.move(path_dir_project, folder_uploaded)

        # log messages
        zipsender_utils.add_log(status="uploaded", msg=folder_project_name)
        print("Upload completed: ", folder_project_name)


if __name__ == "__main__":

    main()
