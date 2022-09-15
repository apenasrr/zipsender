from __future__ import annotations

import os
import shutil
from pathlib import Path


def find_extra(extra_name: str, folder_path_project: Path) -> Path | None:

    list_found = [
        x for x in folder_path_project.iterdir() if x.stem == extra_name
    ]
    if len(list_found) != 0:
        if len(list_found) > 1:
            print(f"Multiple {extra_name}s found.")
        extra_path = list_found[0]
    else:
        extra_path = None
    return extra_path


def format_image(cover_path: Path) -> Path:
    """If image is webm, convert to JPG

    Args:
        cover_path (Path): _description_

    Returns:
        Path: _description_
    """

    if cover_path.suffix == ".webm":
        cover_path_formated = cover_path.parent / cover_path.stem + ".jpg"
        os.system(
            f"ffmpeg -i {str(cover_path.absolute())} {str(cover_path_formated)}"
        )
        return cover_path_formated
    return cover_path


def update(
    list_dict_description: list[dict],
    folder_toupload: Path,
    folder_project_name: str,
) -> list[dict]:
    """Update upload Plan with Cover Image and Project Description txt file,
    if they exist

    Args:
        list_dict_description (list[dict]): Upload plan
        folder_toupload (Path): Folder where all projects are ready to be sent
        folder_project_name (Path): Project folder name

    Returns:
        list[dict]: Upload plan updated
    """

    folder_toupload_project = folder_toupload / folder_project_name

    description_txt_path = folder_toupload_project / "description.txt"

    description_txt_caption = "Read more: " + folder_project_name.strip(
        "_"
    ).replace("_", " ")

    # find cover file
    cover_path = find_extra("cover", folder_toupload_project)

    list_dict_description_updated = list_dict_description.copy()

    # include in uploadplan
    ## description
    if description_txt_path.exists():
        description_file_name_personal = (
            "read_more-" + str(folder_project_name.strip("_")) + ".txt"
        )
        description_txt_path_personal = (
            folder_toupload_project / description_file_name_personal
        )
        shutil.copy(
            str(description_txt_path), str(description_txt_path_personal)
        )
        dict_description = [
            {
                "file_output": description_txt_path_personal,
                "description": description_txt_caption,
            }
        ]
        list_dict_description_updated = (
            dict_description + list_dict_description_updated
        )
    else:
        pass

    ## cover
    if cover_path:
        # If image is webm, convert to JPG
        cover_path = format_image(cover_path)

        cover_caption = folder_project_name.strip("_").replace("_", " ")
        dict_cover = [
            {
                "file_output": cover_path,
                "description": cover_caption,
            }
        ]
        list_dict_description_updated = (
            dict_cover + list_dict_description_updated
        )
    else:
        pass

    return list_dict_description_updated
