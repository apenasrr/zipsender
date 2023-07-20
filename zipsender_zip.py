import copy
import os
import shutil
import time
from configparser import ConfigParser
from pathlib import Path

from zipind import zipind_core, zipind_utils

import content_tree
import extra
import zipsender_utils
from zipsender_utils import zip_haspwd


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


def get_folder_path_output(folder_zipped, folder_path_input):
    folder_project = sanitize_folder(folder_path=folder_path_input)
    folder_path_output = Path(folder_zipped) / folder_project
    zipind_utils.ensure_folder_existence([folder_path_output])
    folder_path_output = Path(folder_zipped) / folder_project / "output"
    zipind_utils.ensure_folder_existence([folder_path_output])
    return folder_path_output


def get_folder_path_project_toupload_auth(folder_path_project_toupload):
    folder_name_project = os.path.basename(folder_path_project_toupload)

    # auth caracter
    folder_name_project_auth = "_" + folder_name_project

    folder_toupload = os.path.abspath(
        os.path.join(folder_path_project_toupload, "..")
    )
    project_toupload_auth = os.path.join(
        folder_toupload, folder_name_project_auth
    )

    return project_toupload_auth


def set_project_toupload_auth(folder_path_output: Path):
    folder_path_project_toupload = folder_path_output.parent.absolute()
    folder_path_project_toupload_auth = get_folder_path_project_toupload_auth(
        folder_path_project_toupload
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
                folder_path_project_toupload, folder_path_project_toupload_auth
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


def get_list_folder_path(folder_path_root, list_folder_name):
    list_folder_path = []
    for folder_name in list_folder_name:
        folder_path = os.path.join(folder_path_root, folder_name)
        list_folder_path.append(folder_path)
    return list_folder_path


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


def revert_original_folder_name(folder_path: str) -> bool:
    """Remove underline at the beginning of the folder name

    Args:
        folder_path (str): folder path

    Returns:
        bool: False If folder does not start with underline
    """

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


def get_folder_structure(folder_path):
    list_file_path = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            list_file_path.append(file_path)
    return list_file_path


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
    def get_list_zip_file_path(list_file_path):
        list_zip_file_path = []
        for file_path in list_file_path:
            dot_extension = os.path.splitext(file_path)[1]
            extension = dot_extension.strip(".")
            if extension in ["zip", "rar", "7z"]:
                list_zip_file_path.append(file_path)
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


def move_config_to_parent_folder_path_output(
    folder_path_input: Path, folder_path_output: Path
) -> None:
    config_path_orgn = Path(folder_path_input) / ".config"
    config_path_dest = Path(folder_path_output).parent.absolute() / ".config"
    if config_path_orgn.exists():
        config_path_orgn.rename(config_path_dest)


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
    delete_after_zip = int(default_config.get("delete_after_zip"))

    zipind_utils.ensure_folder_existence(
        [folder_tozip, folder_zipped, folder_toupload, log_folder_path]
    )

    while True:
        # get list of folders
        list_folder_to_zip = os.listdir(folder_tozip)
        list_folder_to_zip_ready = get_list_folder_to_zip_ready(
            list_folder_to_zip
        )
        list_folder_path_to_zip_ready = get_list_folder_path(
            folder_path_root=folder_tozip,
            list_folder_name=list_folder_to_zip_ready,
        )

        # test path_max and separates approved from rejected
        (
            list_folders_path_approved,
            list_folders_path_rejected,
        ) = zipind_utils.test_folders_has_path_too_long(
            list_folder_path_to_zip_ready, max_path
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
        folder_path_input = Path(folder_tozip) / folder_input_name
        folder_path_input = revert_original_folder_name(folder_path_input)
        folder_input_name = Path(folder_path_input).name

        # define destination folder.: toupload
        folder_path_output = get_folder_path_output(
            folder_toupload, folder_input_name
        )

        move_config_to_parent_folder_path_output(
            folder_path_input, folder_path_output
        )

        extra.include_list(
            ["cover", "description"],
            Path(folder_path_input),
            folder_path_output,
        )

        # Creates grouped files for independent compression
        # project description include as caption in read_more post
        dict_tasks = zipind_core.get_dict_tasks(
            folder_path_input, mb_per_file, folder_path_output, mode
        )
        # save log dict_tasks
        save_log_folder_structure(
            folder_input_name, dict_tasks, log_folder_path
        )

        # Start Compression
        zipind_core.zipind_process(dict_tasks, mode)

        # move from original folder to zipped
        time.sleep(3)
        shutil.move(folder_path_input, folder_zipped)

        if delete_after_zip == 1:
            # remove project folder after zip
            time.sleep(3)
            shutil.rmtree(str(Path(folder_zipped) / folder_input_name))

        # rename zipped project folder, adding authorization character
        set_project_toupload_auth(Path(folder_path_output))

        print("Zip finished: ", folder_input_name)


if __name__ == "__main__":
    main()
