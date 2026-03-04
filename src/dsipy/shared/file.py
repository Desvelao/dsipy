import typer
import os
from pathlib import Path
from typing import List


def get_local_files_from_inputs(inputs: List[Path], filter_func) -> List[Path]:
    files = []
    for input_path in inputs:
        if not input_path.exists():
            typer.secho(f"Input path does not exist: {input_path}", fg=typer.colors.RED)
            continue
        if not input_path.is_file() and not input_path.is_dir():
            typer.secho(
                f"Input path is not a file or directory: {input_path}",
                fg=typer.colors.RED,
            )
            continue
        if input_path.is_file() and filter_func(input_path):
            files.append(input_path)
        if input_path.is_dir():
            for root, _, dir_files in os.walk(input_path):
                for f in dir_files:
                    filepath = Path(root) / f
                    if filter_func(filepath):
                        files.append(filepath)
    return files
