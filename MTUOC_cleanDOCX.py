import argparse
import os
import shutil
import zipfile
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_COLOR_INDEX
from docx.shared import RGBColor

def get_style_chain(style):
    """Yield styles in inheritance order (closest to furthest)."""
    while style is not None:
        yield style
        style = style.base_style

def get_effective_run_format(run, paragraph):
    """Returns a dictionary of all effective formatting properties."""
    def resolve(prop):
        # Check in priority order: run -> run style -> paragraph -> style chain
        sources = [
            run.font,
            run.style.font if run.style else None,
            paragraph,
            *(get_style_chain(paragraph.style) if paragraph.style else [])
        ]
        for source in filter(None, sources):
            val = getattr(source, prop, None)
            if val is not None:
                return val
        return None

    highlight = resolve('highlight_color')
    color = resolve('color')
    
    return {
        'bold': bool(resolve('bold')),
        'italic': bool(resolve('italic')),
        'underline': bool(resolve('underline')),
        'strike': bool(resolve('strike')),
        'double_strike': bool(resolve('double_strike')),
        'all_caps': bool(resolve('all_caps')),
        'small_caps': bool(resolve('small_caps')),
        'shadow': bool(resolve('shadow')),
        'outline': bool(resolve('outline')),
        'emboss': bool(resolve('emboss')),
        'imprint': bool(resolve('imprint')),
        'size': resolve('size'),
        'highlight_color': None if highlight == WD_COLOR_INDEX.WHITE else highlight,
        'color_rgb': getattr(color, 'rgb', None),
        'name': resolve('name'),
        'subscript': bool(resolve('subscript')),
        'superscript': bool(resolve('superscript'))
    }

def merge_runs(paragraph):
    """Merges adjacent runs with identical formatting."""
    if len(paragraph.runs) < 2:
        return

    # Initialize with first run
    current_fmt = get_effective_run_format(paragraph.runs[0], paragraph)
    current_text = paragraph.runs[0].text
    merged_runs = []

    # Process subsequent runs
    for run in paragraph.runs[1:]:
        run_fmt = get_effective_run_format(run, paragraph)
        if run_fmt == current_fmt:
            current_text += run.text
        else:
            merged_runs.append((current_text, current_fmt))
            current_text = run.text
            current_fmt = run_fmt
    merged_runs.append((current_text, current_fmt))

    # Replace original runs
    p_element = paragraph._element
    for r in paragraph.runs:
        p_element.remove(r._element)

    # Add merged runs with formatting
    for text, fmt in merged_runs:
        new_run = paragraph.add_run(text)
        font = new_run.font
        
        # Set all compatible properties
        for prop, value in fmt.items():
            if value is None:
                continue
                
            if prop == 'color_rgb':
                if hasattr(font, 'color'):
                    font.color.rgb = value
            elif prop == 'highlight_color':
                font.highlight_color = value
            elif hasattr(font, prop):
                setattr(font, prop, value)

def iter_paragraphs_in_element(element):
    """Yields all paragraphs in an element (including nested tables)."""
    for child in element._element.iter():
        if isinstance(child, CT_P):
            yield Paragraph(child, element)
        elif isinstance(child, CT_Tbl):
            table = Table(child, element)
            for row in table.rows:
                for cell in row.cells:
                    yield from iter_paragraphs_in_element(cell)

def clean_document(input_path, output_path):
    """Processes all paragraphs in a document."""
    doc = Document(input_path)

    # Process main document body
    for para in iter_paragraphs_in_element(doc):
        merge_runs(para)

    # Process headers and footers
    for section in doc.sections:
        for header_footer in (section.header, section.footer):
            for para in iter_paragraphs_in_element(header_footer):
                merge_runs(para)

    doc.save(output_path)

def main():
    parser = argparse.ArgumentParser(
        description="Merge adjacent runs with identical formatting in DOCX files."
    )
    parser.add_argument("input", help="Input DOCX file path")
    parser.add_argument("output", help="Output DOCX file path")
    parser.add_argument(
        "--unzip", 
        action="store_true",
        help="Unzip the output for inspection"
    )
    args = parser.parse_args()

    clean_document(args.input, args.output)
    print(f"Cleaned document saved to: {args.output}")

    if args.unzip:
        unzip_dir = os.path.splitext(args.output)[0]
        if os.path.exists(unzip_dir):
            shutil.rmtree(unzip_dir)
        os.makedirs(unzip_dir)
        with zipfile.ZipFile(args.output, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)
        print(f"Unzipped output to: {unzip_dir}")

if __name__ == "__main__":
    main()