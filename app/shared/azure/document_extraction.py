from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument


@dataclass
class DocumentExtraction:
    file_name: str
    file_path: str
    file_extension: str

    markdown: str
    text: str

    metadata: dict[str, Any]

    document: DoclingDocument


class DocumentExtractor:
    """
    Generic document extractor.

    Supported formats:
    - PDF
    - DOCX
    """

    _converter = DocumentConverter()

    @staticmethod
    def extract(file_path: str) -> DocumentExtraction:
        """
        Extract document content using Docling.

        Args:
            file_path: Local file path.

        Returns:
            DocumentExtraction
        """

        path = Path(file_path)

        result = DocumentExtractor._converter.convert(file_path)

        document = result.document

        markdown = document.export_to_markdown()

        text = document.export_to_text()

        metadata = {
            "title": getattr(document, "title", None),
            "origin": getattr(document, "origin", None),
            "num_pages": getattr(document, "num_pages", None),
        }

        return DocumentExtraction(
            file_name=path.name,
            file_path=str(path),
            file_extension=path.suffix.lower(),
            markdown=markdown,
            text=text,
            metadata=metadata,
            document=document,
        )