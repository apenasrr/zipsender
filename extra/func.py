from __future__ import annotations

from pathlib import Path
from shutil import copy


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


def copy_extra(extra_name: str, extra_path: Path, folder_path_project: Path):

    extra_path_dest = folder_path_project.parent / (
        extra_name + extra_path.suffix
    )
    copy(str(extra_path), str(extra_path_dest))


def include(
    extra_name: str, folder_path_project: Path, folder_path_output: Path
):

    extra_path = find_extra(extra_name, folder_path_project)

    if not extra_path:
        return
    copy_extra(extra_name, extra_path, folder_path_output)


def include_list(
    list_extra_name: list[str],
    folder_path_project: Path,
    folder_path_output: Path,
):

    for extra_name in list_extra_name:
        include(
            extra_name=extra_name,
            folder_path_project=folder_path_project,
            folder_path_output=folder_path_output,
        )
