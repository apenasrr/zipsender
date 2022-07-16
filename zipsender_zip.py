from zipsender_utils import add_path_script_folders, zip_haspwd

list_folders_name = ["zipind"]
add_path_script_folders(list_folders_name)
import copy
import json
import os
import shutil
import time
from configparser import ConfigParser

import zipind_core
import zipind_utils

import content_tree
import zipsender_utils
from tree_directory import get_tree_directory


def get_list_folder_to_zip_ready(list_folder_to_zip):

    list_ = []
    for folder_to_zip in list_folder_to_zip:
        if folder_to_zip[0] == "_":
            list_.append(folder_to_zip)
    return list_


def get_folder_to_zip_approved(list_folders_path_approved):

    if len(list_folders_path_approved) == 0:
        return False
    else:
        folder_path_approved = list_folders_path_approved[0]
        folder_name_approved = os.path.basename(folder_path_approved)
        return folder_name_approved


def sanitize_folder(folder_path):

    folder_path_raw = zipind_utils.normalize_string_to_link(folder_path)
    folder_path_sanitize = folder_path_raw.strip("_")

    return folder_path_sanitize


def get_path_dir_output(folder_zipped, folder_path_input):

    folder_project = sanitize_folder(folder_path=folder_path_input)
    path_dir_output = os.path.join(folder_zipped, folder_project)
    zipind_utils.ensure_folder_existence([path_dir_output])
    path_dir_output = os.path.join(folder_zipped, folder_project, "output")
    zipind_utils.ensure_folder_existence([path_dir_output])
    return path_dir_output


def get_path_dir_project_toupload_auth(path_dir_project_toupload):

    name_dir_project = os.path.basename(path_dir_project_toupload)

    # auth caracter
    name_dir_project_auth = "_" + name_dir_project

    folder_toupload = os.path.abspath(
        os.path.join(path_dir_project_toupload, "..")
    )
    project_toupload_auth = os.path.join(
        folder_toupload, name_dir_project_auth
    )

    return project_toupload_auth


def set_project_toupload_auth(path_dir_output):

    path_dir_project_toupload = os.path.abspath(
        os.path.join(path_dir_output, "..")
    )
    path_dir_project_toupload_auth = get_path_dir_project_toupload_auth(
        path_dir_project_toupload
    )

    msg_rename_fail = (
        "Unable to rename folder.\n"
        + "Make sure the folder or any of its files is not open"
    )
    msg_rename_ok = "\nFolder rename done.\n"
    alert_flag = 0
    while True:
        try:
            os.rename(
                path_dir_project_toupload, path_dir_project_toupload_auth
            )
            if alert_flag == 1:
                print(msg_rename_ok)
            else:
                pass
            break
        except:
            if alert_flag == 0:
                print(msg_rename_fail)
                alert_flag = 1
            else:
                time.sleep(2)


def get_list_path_folder(path_folder_root, list_folder_name):

    list_path_folder = []
    for folder_name in list_folder_name:
        path_folder = os.path.join(path_folder_root, folder_name)
        list_path_folder.append(path_folder)
    return list_path_folder


def set_unauth_folder(folder_path):

    folder_name = os.path.basename(folder_path)
    folder_path_root_draft = os.path.join(folder_path, "..")
    folder_path_root = os.path.abspath(folder_path_root_draft)

    if folder_name[0] == "_":
        new_folder_name = folder_name[1:]
        new_folder_path = os.path.join(folder_path_root, new_folder_name)
        os.rename(folder_path, new_folder_path)
    else:
        pass


def set_unauth_folders(list_folders_path_rejected):

    if len(list_folders_path_rejected) > 0:
        for folders_path_rejected in list_folders_path_rejected:
            set_unauth_folder(folder_path=folders_path_rejected)


def ensure_folders_sanatize(list_folders_path_rejected):

    if len(list_folders_path_rejected) > 0:
        # remove authorization character from rejected folders
        set_unauth_folders(list_folders_path_rejected)
        input("\nAfter correcting, press something to continue.\n")
        return True
    else:
        return False


def revert_original_folder_name(folder_path):

    folder_name = os.path.basename(folder_path)
    if folder_name[0] == "_":
        folder_path_root_draft = os.path.join(folder_path, "..")
        folder_path_root = os.path.abspath(folder_path_root_draft)
        folder_name_new = folder_name[1:]
        folder_path_new = os.path.join(folder_path_root, folder_name_new)
        os.rename(folder_path, folder_path_new)
        return folder_path_new
    else:
        return False


def get_folder_structure(path_folder):

    list_path_file = []
    for root, _, files in os.walk(path_folder):
        for file in files:
            path_file = os.path.join(root, file)
            list_path_file.append(path_file)
    return list_path_file


def save_log_folder_structure(folder_name, dict_tasks, log_folder_path):

    dict_tasks_log = copy.deepcopy(dict_tasks)
    folder_name_sanitize = sanitize_folder(folder_name)
    log_file_path = get_log_file_path(folder_name_sanitize, log_folder_path)

    string_tree = content_tree.main(dict_tasks_log)
    zipsender_utils.save_txt(string_tree, log_file_path)


def get_log_file_path(folder_name, log_folder_path):

    folder_destiny = log_folder_path
    log_file_path = os.path.join(folder_destiny, folder_name)
    return log_file_path


def format_list_file_path(list_file_path):

    list_file_path_formatted = []
    for file_path in list_file_path:
        deep_level = file_path.count("\\")
        file_path_format = " " * deep_level + file_path
        list_file_path_formatted.append(file_path_format)

    str_folder_structure = "\n".join(list_file_path_formatted)
    return str_folder_structure


def test_zipfiles_in_one_folder(folder_path):
    def get_list_zip_file_path(list_path_file):

        list_zip_file_path = []
        for path_file in list_path_file:
            dot_extension = os.path.splitext(path_file)[1]
            extension = dot_extension.strip(".")
            if extension in ["zip", "rar", "7z"]:
                list_zip_file_path.append(path_file)
        return list_zip_file_path

    def get_list_file_with_pwd(list_zip_file_path):

        list_file_with_pwd = []
        for zip_file_path in list_zip_file_path:
            haspwd = zip_haspwd(zip_file_path)
            if haspwd:
                list_file_with_pwd.append(zip_file_path)
        return list_file_with_pwd

    list_file_path = get_folder_structure(folder_path)
    list_zip_file_path = get_list_zip_file_path(list_file_path)
    if len(list_zip_file_path) == 0:
        return True

    list_zip_file_path_with_pwd = get_list_file_with_pwd(list_zip_file_path)

    if len(list_zip_file_path_with_pwd) == 0:
        # TODO: Alert that zip file in the project.
        #       Ask if you want to check again or accept as you are.
        if accept_zipfiles(list_zip_file_path):
            return True
        else:
            return False
    else:
        # TODO: warn that there is a zip file with password
        return False


def test_zipfiles(list_folders_path_approved):

    for folder_path in list_folders_path_approved:
        if test_zipfiles_in_one_folder(folder_path) is False:
            return False
    return True


def main():

    config = ConfigParser()
    config.read("config.ini")
    default_config = dict(config["default"])

    # Define variables
    folder_tozip = default_config.get("folder_tozip")
    folder_zipped = default_config.get("folder_zipped")
    folder_toupload = default_config.get("folder_toupload")
    mb_per_file = int(default_config.get("mb_per_file"))
    max_path = int(default_config.get("max_path"))
    mode = default_config.get("mode")
    log_folder_path = default_config.get("log_folder_path")

    zipind_utils.ensure_folder_existence(
        [folder_tozip, folder_zipped, folder_toupload, log_folder_path]
    )

    while True:
        # get list of folders
        list_folder_to_zip = os.listdir(folder_tozip)
        list_folder_to_zip_ready = get_list_folder_to_zip_ready(
            list_folder_to_zip
        )
        list_path_folder_to_zip_ready = get_list_path_folder(
            path_folder_root=folder_tozip,
            list_folder_name=list_folder_to_zip_ready,
        )

        # test path_max and separates approved from rejected
        (
            list_folders_path_approved,
            list_folders_path_rejected,
        ) = zipind_utils.test_folders_has_path_too_long(
            list_path_folder_to_zip_ready, max_path
        )

        # ensures that authorized folders are approved in the path_max test
        if ensure_folders_sanatize(list_folders_path_rejected):
            continue

        # if test_zipfiles(list_folders_path_approved) is False:
        #     continue

        # get first item from the list of approved folders
        folder_input_name = get_folder_to_zip_approved(
            list_folders_path_approved
        )
        if folder_input_name is False:
            time.sleep(5)
            continue

        # reverse original name of project folder
        folder_path_input = os.path.join(folder_tozip, folder_input_name)
        folder_path_input = revert_original_folder_name(folder_path_input)
        folder_input_name = os.path.basename(folder_path_input)

        # define destination folder.: toupload
        path_dir_output = get_path_dir_output(
            folder_toupload, folder_input_name
        )

        # zip to destination folder

        # Creates grouped files for independent compression
        dict_tasks = zipind_core.get_dict_tasks(
            folder_path_input, mb_per_file, path_dir_output, mode
        )
        # save log dict_tasks
        save_log_folder_structure(
            folder_input_name, dict_tasks, log_folder_path
        )

        # Start Compression
        zipind_core.zipind_process(dict_tasks, mode)

        time.sleep(4)

        # move from original folder to zipped
        shutil.move(folder_path_input, folder_zipped)

        # rename zipped project folder, adding authorization character
        set_project_toupload_auth(path_dir_output)

        print("Zip finished: ", folder_input_name)


if __name__ == "__main__":
    main()
