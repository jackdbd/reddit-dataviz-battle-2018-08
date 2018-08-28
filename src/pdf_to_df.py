"""Convert PDF tables into a Pandas DataFrame.

TSA claims data from 2016 and 2017 is available as PDF.
We can use tabula-py to read PDF files and extract tabular data,
but we have to handle a few different cases.

-- PDF from 2016 --

A) These 2 rows were not read correctly. They belong to the same row in the PDF.
ROW 0 [nan nan nan nan 'Lehigh Valley International' nan nan nan nan nan nan]
ROW 1 ['2016022629173' '5-Feb-16' '1/2/2016 16:00' 'ABE' 'Airport, Allentown'
 'American Airlines' 'Passenger Property Loss' 'Checked Baggage'
 'Currency' '$0.00' 'Deny']

B) This row was read correctly. Nothing to do here.
ROW 71 ['2016080832975' '1-Jul-16' '6/25/2016 0:00' 'ACK' 
 'Nantucket Memorial Airport' 'American Airlines' 'Property Damage'
 'Checked Baggage' 'Jewelry & Watches' '-' 'In Review']

-- PDF from 2017 --

A) These 3 rows were not read correctly. They belong to the same row in the PDF.
ROW 0 [nan nan nan nan 'Lehigh Valley International Airport,' nan nan nan nan
 nan nan]
ROW 1 ['2017042438845' nan nan nan nan nan nan nan nan nan nan]
ROW 2 [nan '16-Feb-17' '1/20/2017 0:00' 'ABE' 'Allentown' '-' 'Property Damage'
 'Checked Baggage' 'Cosmetics & Grooming' '-' 'In Review']

B) These 2 rows were not read correctly. They belong to the same row in the PDF.
ROW 91 [nan nan nan 'Albuquerque International Sunport' nan nan nan nan nan nan
 nan]
ROW 92 ['29-Sep-17' '9/17/2017 0:00' 'ABQ' 'Airport' 'Southwest Airlines'
 'Passenger Property Loss' 'Checked Baggage' 'Jewelry & Watches' '-'
 'In Review' nan]

C) This row was read correctly. Nothing to do here.
ROW 96 ['2017091443121' '3-Aug-17' '6/12/2017 8:54' 'ACT' 'Waco Regional Airport'
 'American Airlines' 'Passenger Property Loss' 'Checked Baggage'
 'Automobile Parts & Accessories; Cosmetics & Grooming' '-' 'In Review']

See Also:
    https://github.com/chezou/tabula-py/blob/master/tabula/wrapper.py
"""
import os
import time
import logging
import argparse
import tabula
import numpy as np
import pandas as pd
import sqlalchemy as sa
from PyPDF2 import PdfFileReader
from argparse import RawDescriptionHelpFormatter
from utils import harmonize_columns, sanitize_dates, assign_nan, produce_output

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(formatter_str)
ch = logging.StreamHandler()

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.abspath(os.path.join(HERE, '..', 'data'))

PDF_FILES = [
    'tsa claims data for 2016_0.pdf',
    '18_0314_OPA_2017_All_Airports_Data.pdf',
]

PAGE_ARGUMENT = {
    'shorthand': 'p',
    'name': 'page_step',
    'default': 5,
    'type': int,
    'help': 'Num. of pages to parse from PDF files at a time (default: 5)',
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=RawDescriptionHelpFormatter
    )
    parser.add_argument(
        f"-{PAGE_ARGUMENT['shorthand']}",
        f"--{PAGE_ARGUMENT['name']}",
        default=PAGE_ARGUMENT['default'],
        type=PAGE_ARGUMENT['type'],
        help=PAGE_ARGUMENT['help'],
    )
    parser.add_argument(
        '-o', '--output', action='store_true',
        help='If set, generate CSV file'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='If set, increase output verbosity'
    )
    return parser.parse_args()


def format_close_amount(series):
    if not isinstance(series['Close Amount'], float):
        orig = series['Close Amount']
        string = orig.replace('$', '').replace('-', '')
        if string:
            series['Close Amount'] = np.float(string)
        else:
            series['Close Amount'] = np.nan
    return series


def is_only(series, field, criteria):
    are_missing_fields = all([pd.isnull(series.loc[col]) for col in criteria])
    is_the_only_field = pd.notnull(series.loc[field]) and are_missing_fields
    return is_the_only_field


def is_parsed_incorrectly(series):
    """Flag whether a row was parsed correctly or not.

    Unfortunately it seems that rows with a very long 'Airport Name' are not
    parsed correctly by tabula-py because they have a slightly different layout.
    (e.g. Albuquerque International Sunport Airport)
    """
    boolean = len(series.loc['Airport Code']) > 3
    return boolean


def pdf_to_rows_columns(file_path, pages_string):
    logger.info(f"PDF file {file_path}")
    logger.info(f"Pages {pages_string}: parse with tabula")
    df = tabula.read_pdf(file_path, pages=pages_string)
    previous_data = {}
    rows = []
    for i, r in df.iterrows():
        # skip the header after the first page
        if r['Claim Number'] == 'Claim Number':
            logger.debug(f"ROW {i}: header of new page. Will be skipped.")
            previous_data = {}
            continue

        if is_only(r, 'Claim Number', ['Airport Name', 'Airport Code']):
            previous_data['Claim Number'] = r.loc['Claim Number']
            continue
        elif is_only(r, 'Airport Name', ['Claim Number', 'Airport Code']):
            previous_data['Airport Name'] = r.loc['Airport Name']
            continue
        elif is_parsed_incorrectly(r):
            logger.debug(f"ROW {i}: parsed_incorrectly: {r.values}")
            previous_data = {}
            continue
        else:
            pre_airport_name = previous_data.get('Airport Name', '')
            if pre_airport_name:
                logger.debug(f"ROW {i}: 'Airport Name' is incomplete.")
                updated_airport_name = f"{pre_airport_name}{r['Airport Name']}"
                r['Airport Name'] = updated_airport_name
                logger.debug(f"ROW {i}: 'Airport Name' updated: {updated_airport_name}")

            # SOMETIMES 'Claim Number' is missing and MIGHT be retrieved from
            # 1-2 rows above. We KEEP records with missing 'Claim Number'.
            if pd.isnull(r['Claim Number']):
                logger.debug(f"ROW {i}: 'Claim Number' is missing.")
                updated_claim_number = previous_data.get('Claim Number')
                r['Claim Number'] = updated_claim_number
                logger.debug(f"ROW {i}: 'Claim Number' updated: {updated_claim_number}")

            r = format_close_amount(r)
            rows.append(r)
            previous_data = {}

    return rows, df.columns


def make_df_from_pdf(file_name, page_step, debug=False):
    """Read from a PDF file in chunks and make a single DataFrame.

    In PDF file containing all TSA data from 2017 the header appears only on the
    first page. If we read e.g. pages 2-3, tabula-py doesn't find the header and
    parses the page incorrectly, so pandas fails to tokenize the PDF.
    A workaround is to always read the first page, and to remove all duplicate
    records later.
    Unfortunately, sometimes pandas fails to tokenize the page for other issues.

    Parameters
    ----------
    file_name : str
    page_step : int
        Number of pages to read at a time. These PDF files are too big, so we
        can't read all pages in one go.
    debug : bool
        It's handy to parse only 2-3 pages when debugging
    """
    t0 = time.time()
    file_path = os.path.abspath(os.path.join(DATA_DIR, file_name))
    num_pages = None
    with open(file_path, 'rb') as stream:
        pdf = PdfFileReader(stream)
        num_pages = pdf.getNumPages()
    
    logger.info(f"{file_name} has {num_pages} pages")

    if debug:
        num_pages = 2

    rows_all = []
    for i in range(0, num_pages, page_step):
        p0 = i + 1 if i > 0 else 2
        p1 = min(num_pages, i + page_step)
        pages_string = f"1,{p0}-{p1}"
        try:
            rows, columns = pdf_to_rows_columns(file_path, pages_string)
        except Exception as e:
            logger.error(f"File {file_path} - Cannot parse pages [{p0}-{p1}]")
            logger.error(e)
        else:
            rows_all.extend(rows)

    df_all = pd.DataFrame(rows_all, columns=columns)
    logger.info(f"'Claim Number' WITH NaNs AND duplicates: shape {df_all.shape}")

    df_nans = df_all[df_all['Claim Number'].isnull()]
    logger.info(f"'Claim Number' WITH only NaNs: shape {df_nans.shape}")
    
    df_no_duplicates = df_all.drop_duplicates(subset=['Claim Number'], keep='first')
    df_raw = pd.merge(df_nans, df_no_duplicates, how='outer')
    logger.info(f"'Claim Number' WITH NaNs BUT NO duplicates: shape {df_raw.shape}")
    
    df0 = harmonize_columns(df_raw)
    df1 = sanitize_dates(df0)
    df = assign_nan(df1)
    t1 = time.time()
    logger.info(f"{file_name} processed in: {(t1 - t0):.2f} seconds")
    return df


def main():
    args = parse_args()
    page_step = [x[1] for x in args._get_kwargs() if x[0] == PAGE_ARGUMENT['name']][0]
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    t0 = time.time()

    dataframes = [
        make_df_from_pdf(file_name, page_step=page_step) 
        for file_name in PDF_FILES]
    
    for i, df in enumerate(dataframes):
        logger.debug(f"{i} df: {df.shape}")
        
    logger.debug(f"Concatenate {len(dataframes)} dataframe/s into 1")
    df = pd.concat(dataframes).reset_index().drop(columns=['index'])
    logger.info(f"DataFrame {i} shape: {df.shape}")

    if args.output:
        produce_output(dataframes, PDF_FILES)

    t1 = time.time()
    logger.info(f"Done in: {(t1 - t0):.2f} seconds")

if __name__ == '__main__':
    main()

