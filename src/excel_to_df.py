"""Convert Excel worksheets into a Pandas DataFrame.

TSA claims data from 2002 to 2015 is available as Excel files (.xls and .xlsx).
These files are sometimes quite big, so we read them in chunks.

Usage:
    $ python excel_to_df.py
    # Read each Excel file in chunks of 20k rows, output as CSV file
    $ python excel_to_df.py -x 20000 -o

See Also:
    https://pandas.pydata.org/pandas-docs/version/0.20/generated/pandas.to_datetime.html
"""
import os
import time
import logging
import argparse
import pandas as pd
from argparse import RawDescriptionHelpFormatter
from utils import harmonize_columns, sanitize_dates, assign_nan, produce_output


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(formatter_str)
ch = logging.StreamHandler()

logger_utils = logging.getLogger('utils')
logger_utils.setLevel(logging.DEBUG)
logger_utils.addHandler(ch)

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.abspath(os.path.join(HERE, '..', 'data'))


EXCEL_FILES = [
    'claims-2002-2006_0.xls',
    'claims-2007-2009_0.xls',
    'claims-2010-2013_0.xls',
    'claims-2014.xls',
    'claims-data-2015-as-of-feb-9-2016.xlsx'
]

XLS_ARGUMENT = {
    'shorthand': 'x',
    'name': 'xls_chunksize',
    'default': 10000,
    'type': int,
    'help': 'Num. of rows to read from Excel files at a time (default: 10000)',
}

def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=RawDescriptionHelpFormatter
    )
    parser.add_argument(
        f"-{XLS_ARGUMENT['shorthand']}",
        f"--{XLS_ARGUMENT['name']}",
        default=XLS_ARGUMENT['default'],
        type=XLS_ARGUMENT['type'],
        help=XLS_ARGUMENT['help'],
    )
    parser.add_argument(
        '-o', '--output', action='store_true', help='If set, generate CSV file'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='If set, increase output verbosity'
    )
    return parser.parse_args()


def date_parser(x):
    dt = pd.to_datetime(x, coerce=True)
    print(dt)
    return dt


def make_df_from_excel(file_name, nrows):
    """Read from an Excel file in chunks and make a single DataFrame."""
    file_path = os.path.abspath(os.path.join(DATA_DIR, file_name))
    xl = pd.ExcelFile(file_path)
    sheetname = xl.sheet_names[0]

    df_header = pd.read_excel(file_path, sheetname=sheetname, nrows=1)
    logger.info(f"Excel file: {file_name} (worksheet: {sheetname})")
    
    chunks = []    
    i_chunk = 0
    skiprows = 1
    while True:
        df_chunk = pd.read_excel(
            file_path, sheetname=sheetname,
            nrows=nrows, skiprows=skiprows, header=None)
        skiprows += nrows
        if not df_chunk.shape[0]:
            break
        else:
            logger.debug(f"  - chunk {i_chunk} ({df_chunk.shape[0]} rows)")
            chunks.append(df_chunk)
        i_chunk += 1
    
    df_chunks = pd.concat(chunks)
    # We need to rename the columns to concatenate the chunks with the header.
    columns = {i: col for i, col in enumerate(df_header.columns.tolist())}    
    df_chunks.rename(columns=columns, inplace=True)
    df_raw = pd.concat([df_header, df_chunks])
    df0 = harmonize_columns(df_raw)
    df1 = sanitize_dates(df0)
    df = assign_nan(df1)
    return df


def main():
    args = parse_args()
    nrows = [x[1] for x in args._get_kwargs() if x[0] == XLS_ARGUMENT['name']][0]
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    t0 = time.time()

    dataframes = [
        make_df_from_excel(file_name, nrows=nrows) 
        for file_name in EXCEL_FILES]

    for i, df in enumerate(dataframes):
        logger.debug(f"{i} df: {df.shape}")
        
    logger.debug(f"Concatenate {len(dataframes)} dataframe/s into 1")
    df = pd.concat(dataframes).reset_index().drop(columns=['index'])
    logger.info(f"DataFrame {i} shape: {df.shape}")

    if args.output:
        produce_output(dataframes, EXCEL_FILES)

    t1 = time.time()
    logger.info(f"Done in: {(t1 - t0):.2f} seconds")

if __name__ == '__main__':
    main()
