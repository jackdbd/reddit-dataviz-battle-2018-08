"""Gather data from all sources and store it in a SQLite database.

Usage:
    Run command with sane defaults
    $ python make_db.py

    Run command with different arguments
      - read 3000 rows at a time from any excel file,
      - read 20 pages at a time from any PDF file,
      - drop db first,
      - verbose output
    $ python make_db.py -x 3000 -p 20 -d -v
"""
import os
import time
import datetime
import logging
import argparse
import numpy as np
import pandas as pd
import sqlalchemy as sa
from argparse import RawDescriptionHelpFormatter
from excel_to_df import make_df_from_excel, EXCEL_FILES, XLS_ARGUMENT
from pdf_to_df import make_df_from_pdf, PDF_FILES, PAGE_ARGUMENT

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(formatter_str)
ch = logging.StreamHandler()

logger_xls = logging.getLogger('excel_to_df')
logger_xls.setLevel(logging.DEBUG)
logger_xls.addHandler(ch)

logger_pdf = logging.getLogger('pdf_to_df')
logger_pdf.setLevel(logging.DEBUG)
logger_pdf.addHandler(ch)


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
DB_NAME = 'TSA.db'
DB_PATH = os.path.abspath(os.path.join(ROOT, DB_NAME))
TABLE_NAME = 'claims'


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
        f"-{PAGE_ARGUMENT['shorthand']}",
        f"--{PAGE_ARGUMENT['name']}",
        default=PAGE_ARGUMENT['default'],
        type=PAGE_ARGUMENT['type'],
        help=PAGE_ARGUMENT['help'],
    )
    parser.add_argument(
        "-d", "--drop_db",
        action="store_true",
        help="If set, drop the database"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="If set, increase output verbosity"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if args.drop_db:
        try:
            os.unlink(DB_PATH)
        except FileNotFoundError:
            pass

    t0 = time.time()

    dataframes_excel = [
        make_df_from_excel(file_name, nrows=args.xls_chunksize) 
        for file_name in EXCEL_FILES]
    
    dataframes_pdf = [
        make_df_from_pdf(file_name, page_step=args.page_step) 
        for file_name in PDF_FILES]

    dataframes = []
    dataframes.extend(dataframes_excel)
    dataframes.extend(dataframes_pdf)

    for i, df in enumerate(dataframes):
        logger.debug(f"{i} DataFrame: {df.shape}")
        logger.debug(df.columns)

    logger.debug(f"Concatenate {len(dataframes)} dataframes into 1")
    df = pd.concat(dataframes).reset_index().drop(columns=['index'])
    logger.debug(df.shape)

    # TODO: cast dates before writing to the DB?
    # df['incident_date'] = df['incident_date'].astype('str')
    # df['date_received'] = df['date_received'].astype('str')
    
    engine = sa.create_engine(f"sqlite:///{DB_PATH}")
    df.to_sql(TABLE_NAME, con=engine, if_exists='append', index=False, chunksize=10000)

    t1 = time.time()
    logger.info(f"Done in: {(t1 - t0):.2f} seconds")

if __name__ == '__main__':
    main()
