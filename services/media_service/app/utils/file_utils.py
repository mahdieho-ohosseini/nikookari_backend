from pathlib import Path
from uuid import uuid4


def get_file_extension(filename: str | None) -> str | None:
    if not filename:
        return None

    suffix = Path(filename).suffix.lower()

    if not suffix:
        return None

    return suffix.replace(".", "")


def generate_stored_filename(original_filename: str | None) -> str:
    extension = get_file_extension(original_filename)

    unique_name = uuid4().hex

    if extension:
        return f"{unique_name}.{extension}"

    return unique_name