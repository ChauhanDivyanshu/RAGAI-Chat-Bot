"""
Excel/CSV Parser - Spreadsheet Documents
Handles XLSX, XLS, and CSV files
"""
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from app.utils import logger, ExtractionError


class ExcelParser:
    """Parse Excel and CSV files"""
    
    def extract(self, file_path: str, file_type: str = "xlsx") -> Dict:
        """
        Extract data from Excel/CSV file.
        
        Args:
            file_path: Path to file
            file_type: 'xlsx', 'xls', or 'csv'
            
        Returns:
            {
                'full_text': str,
                'sheets': [{'name': str, 'data': list, 'text': str}],
                'metadata': dict,
                'stats': dict
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Parsing {file_type.upper()}: {path.name}")
        
        try:
            if file_type == "csv":
                return self._extract_csv(file_path)
            else:
                return self._extract_excel(file_path)
        except Exception as e:
            logger.error(f"{file_type.upper()} extraction failed: {e}")
            raise ExtractionError(file_type.upper(), str(e))
    
    def _extract_excel(self, file_path: str) -> Dict:
        """Extract from XLSX/XLS file (multiple sheets)"""
        # Read all sheets
        all_sheets = pd.read_excel(
            file_path,
            sheet_name=None,  # Get all sheets
            engine='openpyxl' if file_path.endswith('.xlsx') else 'xlrd'
        )
        
        sheets_data = []
        full_text_parts = []
        total_rows = 0
        total_cols = 0
        
        for sheet_name, df in all_sheets.items():
            if df.empty:
                continue
            
            # Clean dataframe
            df = df.fillna('')  # Replace NaN with empty string
            df = df.astype(str)  # Convert all to string
            
            # Get dimensions
            rows, cols = df.shape
            total_rows += rows
            total_cols = max(total_cols, cols)
            
            # Convert to text representation
            sheet_text = self._dataframe_to_text(df, sheet_name)
            
            sheets_data.append({
                'name': sheet_name,
                'rows': rows,
                'columns': cols,
                'column_names': df.columns.tolist(),
                'text': sheet_text,
                'preview': df.head(5).to_dict(orient='records')
            })
            
            full_text_parts.append(f"\n=== Sheet: {sheet_name} ===\n{sheet_text}")
        
        full_text = "\n\n".join(full_text_parts)
        
        result = {
            'full_text': full_text,
            'sheets': sheets_data,
            'metadata': {
                'file_format': 'excel',
                'sheets_count': len(sheets_data)
            },
            'stats': {
                'sheets_count': len(sheets_data),
                'total_rows': total_rows,
                'max_columns': total_cols,
                'total_characters': len(full_text),
                'word_count': len(full_text.split())
            }
        }
        
        logger.info(
            f"Excel extracted: {len(sheets_data)} sheets, "
            f"{total_rows} total rows, {total_cols} max columns"
        )
        
        return result
    
    def _extract_csv(self, file_path: str) -> Dict:
        """Extract from CSV file"""
        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')
                used_encoding = encoding
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        
        if df is None:
            raise ExtractionError("CSV", "Could not read with any encoding")
        
        # Clean
        df = df.fillna('')
        df = df.astype(str)
        
        rows, cols = df.shape
        
        # Convert to text
        sheet_text = self._dataframe_to_text(df, "CSV Data")
        
        result = {
            'full_text': sheet_text,
            'sheets': [{
                'name': 'CSV',
                'rows': rows,
                'columns': cols,
                'column_names': df.columns.tolist(),
                'text': sheet_text,
                'preview': df.head(5).to_dict(orient='records')
            }],
            'metadata': {
                'file_format': 'csv',
                'encoding': used_encoding
            },
            'stats': {
                'sheets_count': 1,
                'total_rows': rows,
                'max_columns': cols,
                'total_characters': len(sheet_text),
                'word_count': len(sheet_text.split())
            }
        }
        
        logger.info(f"CSV extracted: {rows} rows, {cols} columns ({used_encoding})")
        
        return result
    
    def _dataframe_to_text(self, df: pd.DataFrame, name: str = "") -> str:
        """Convert DataFrame to readable text"""
        if df.empty:
            return ""
        
        lines = []
        
        # Header row
        headers = df.columns.tolist()
        lines.append(" | ".join(str(h) for h in headers))
        lines.append("-" * 80)
        
        # Data rows (limit very large sheets)
        max_rows = 1000  # Limit to avoid huge text
        if len(df) > max_rows:
            logger.warning(f"Sheet has {len(df)} rows, limiting to {max_rows}")
            df = df.head(max_rows)
        
        for _, row in df.iterrows():
            line = " | ".join(str(val) for val in row)
            lines.append(line)
        
        return "\n".join(lines)


# Global instance
excel_parser = ExcelParser()
