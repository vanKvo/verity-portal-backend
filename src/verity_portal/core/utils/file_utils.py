import io
import os
import tempfile
import logging
from typing import Any, List
import pandas as pd
from numbers_parser import Document

logger = logging.getLogger(__name__)

def parse_file_to_df(filename: str, stream: io.BytesIO | Any, nrows: int | None = None) -> pd.DataFrame:
    """Parses seekable binary upload streams into DataFrames based on file extension.

    Args:
        filename: The original upload string filename (e.g. 'roster.numbers').
        stream: The seekable binary BytesIO file stream container or SpooledTemporaryFile.
        nrows: Optional number of rows to read (useful for extracting just headers).

    Returns:
        A loaded Pandas DataFrame containing sheet values.

    Raises:
        ValueError: If a numbers spreadsheet table structure is empty or missing.
    """
    fn: str = filename.lower()
    stream.seek(0)
    
    if fn.endswith(('.xlsx', '.xls')):
        return pd.read_excel(stream, nrows=nrows)
    elif fn.endswith('.numbers'):
        with tempfile.NamedTemporaryFile(suffix=".numbers", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name
        try:
            doc: Document = Document(tmp_path)
            sheets: List[Any] = doc.sheets
            if not sheets or not sheets[0].tables:
                raise ValueError("Invalid Numbers file: no sheets or tables found")
            table: Any = sheets[0].tables[0]
            data: List[List[Any]] = []
            
            # numbers_parser doesn't natively support nrows, so we slice
            limit = (nrows + 1) if nrows is not None else None
            
            for i, row in enumerate(table.rows()):
                if limit and i >= limit:
                    break
                data.append([cell.value if cell.value is not None else "" for cell in row])
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data[1:], columns=data[0])
        finally:
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.error(f"Cannot remove the temporary file path: {e}")
    else:
        return pd.read_csv(stream, nrows=nrows)

def extract_headers_from_file(filename: str, stream: io.BytesIO | Any) -> List[str]:
    """Extracts column headers from an uploaded file stream.

    Args:
        filename: The original upload string filename.
        stream: The seekable binary file stream container.

    Returns:
        A list of clean column header strings.
    """
    df = parse_file_to_df(filename, stream, nrows=1)
    headers = list(df.columns)
    return [str(h).strip() for h in headers if h is not None]
