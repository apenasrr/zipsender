import datetime
import logging
import os
import sys
import zipfile

# import py7zr
# import rarfile


def save_txt(str_content, str_name):

    # UTF-8 can't handle with the follow caracter in a folder name: 
    text_file = open(f"{str_name}.txt", "w", encoding="utf_16")
    text_file.write(str_content)
    text_file.close()


def extzip_haspwd(file_path):
    zipfile_ = zipfile.ZipFile(file_path)
    for zinfo in zipfile_.infolist():
        is_encrypted = zinfo.flag_bits & 0x1
        if is_encrypted:
            return True
    return False


def zip_haspwd(file_path):

    dot_extension = os.path.splitext(file_path)[1]
    extension = dot_extension.strip(".")
    if extension == "rar":
        has_pwd = rarfile.RarFile(file_path).needs_password()
    elif extension == "zip":
        has_pwd = extzip_haspwd(file_path)
    elif extension == "7z":
        has_pwd = py7zr.SevenZipFile(file_path).needs_password()
    else:
        return False
    return has_pwd


def get_size_group(list_, size_max):
    def round_up(number_):
        if round(number_) == number_:
            return number_
        else:
            return int(number_) + 1

    def get_qt_group(size, max_):
        if size <= max_:
            qt_group = 1
        else:
            qt_group = round_up((size - 1) // max_) + 1
        return qt_group

    size = len(list_)
    qt_group = get_qt_group(size, size_max)
    size_group = round_up(size / qt_group)
    return int(size_group)


def split_list_in_lists(list_, size_group):

    list_of_list = []
    list_cache = []
    for i in list_:
        list_cache.append(i)
        if len(list_cache) == size_group:
            list_of_list.append(list_cache)
            list_cache = []
    if len(list_cache) != 0:
        list_of_list.append(list_cache)
    return list_of_list


def split_list_in_lists_by_max(list_, size_max):

    size_group = get_size_group(list_, size_max)
    list_of_list = split_list_in_lists(list_, size_group)
    return list_of_list


def add_log(status, msg):
    with open("log.txt", "a", encoding="utf-8") as log_file:
        today_ = datetime.datetime.today()
        datetime_ = today_.replace(microsecond=0)
        log_file.write(f"{datetime_},{status},{msg}\n")


def add_path_script_folders(list_folders_name):

    list_repo_dont_found = []
    for folder_name in list_folders_name:
        path_script_folder = os.path.abspath(os.path.join("..", folder_name))
        existence = os.path.isdir(path_script_folder)
        if existence is False:
            list_repo_dont_found.append(path_script_folder)
        else:
            sys.path.append(path_script_folder)

    # alert in case of not found repositories
    qt_not_found = len(list_repo_dont_found)
    if qt_not_found != 0:
        if qt_not_found > 1:
            repo = "repositories"
        else:
            repo = "repository"
        str_list_repo_dont_found = "\n".join(list_repo_dont_found)
        logging.error(
            f"The {repo} below could not be found. "
            + "Make sure it exists with the proper folder "
            + f"name.\n{str_list_repo_dont_found}\n"
        )
        exit()


def get_list_folder_to_zip_ready(list_folder_to_zip):
    list_ = []
    for folder_to_zip in list_folder_to_zip:
        if folder_to_zip[0] == "_":
            list_.append(folder_to_zip)
    return list_


def get_folder_to_zip_ready(list_folder_to_zip_ready):

    if len(list_folder_to_zip_ready) == 0:
        return False
    else:
        return list_folder_to_zip_ready[0]


def compile_template(d_keys, template_content):

    for key in d_keys.keys():
        template_content = template_content.replace(
            "{" + key + "}", d_keys[key]
        )
    output_content = template_content
    return output_content


def get_txt_content(file_path):

    list_encode = ["utf-8", "ISO-8859-1"]  # utf8, ansi
    for encode in list_encode:
        try:
            file = open(file_path, "r", encoding=encode)
            file_content = file.readlines()
            file_content = "".join(file_content)
            file.close()
            return file_content
        except:
            continue

    file = open(file_path, "r", encoding=encode)
    file_content = file.readlines()
    raise Exception("encode", f"Cannot open file: {file_path}")
