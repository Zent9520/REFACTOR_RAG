from dataclasses import dataclass


@dataclass(slots=True)
class TempFileResult:

    file_path: str

    file_size: int