def write_file(content, file_path):
    """
    Writes the given content to a file.

    Args:
        content (str): The content to write.
        file_path (str): The path to the file where the content should be written.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
