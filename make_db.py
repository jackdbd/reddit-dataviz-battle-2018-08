"""Gather data from all sources and store it in a SQLite database."""
import os
import time
import datetime
import numpy as np
import pandas as pd
import sqlalchemy as sa


EXCEL_FILES = [
    # 'claims-2002-2006_0.xls',
    # 'claims-2007-2009_0.xls',
    # 'claims-2010-2013_0.xls',
    'claims-2014.xls',
    'claims-data-2015-as-of-feb-9-2016.xlsx'
]

def harmonize_df(df):
    columns = {
        'Item Category': 'item',
        'Item': 'item',
        'Incident D': 'incident_date',
        'Incident Date': 'incident_date',
        'Close Amount': 'close_amount',
        'Date Received': 'date_received', 
        'Airport Code': 'airport_code', 
        'Airport Name': 'airport_name',
        'Airline Name': 'airline_name',
        'Claim Type': 'claim_type',
        'Claim Site': 'claim_site',
        'Disposition': 'disposition'
    }
    df.rename(columns=columns, inplace=True)
    columns_to_drop = ['Claim Number', 'Claim Amount', 'Status']
    columns_available_to_drop = list(set(df.columns.values).intersection(set(columns_to_drop)))
    df.drop(columns=columns_available_to_drop, inplace=True)
    return df


def clean_df(df):
    # drop problematic records (e.g. dates with incorrect datatype)
    ii = set(range(df.shape[0]))
    ii_invalid = set([i for i, x in enumerate(df['incident_date']) if isinstance(x, str) or pd.isnull(x)])
    ii_valid = list(ii.difference(ii_invalid))
    ddf = df.iloc[ii_valid].reset_index()
    ddf.set_index('index', inplace=True)
    ddf['incident_date'].astype('str')
    ddf['incident_date'].apply(lambda x: datetime.datetime(year=x.year, month=x.month, day=x.day))
    
    # assign NaN where no data is available
    ddf.replace(to_replace='-', value=np.nan, inplace=True)    
    return ddf


def make_df_from_excel(file_name, nrows=5000):
    """Read from an Excel file in chunks and make a single DataFrame."""
    file_path = os.path.abspath(os.path.join('data', file_name))
    xl = pd.ExcelFile(file_path)
    sheetname = xl.sheet_names[0]
    df_header = pd.read_excel(file_path, sheetname=sheetname, nrows=1)
    print(f"Excel file: {file_name} (worksheet: {sheetname})")
    
    chunks = []    
    i_chunk = 0
    skiprows = 1
    while True:
        df_chunk = pd.read_excel(file_path, sheetname=sheetname, nrows=nrows, skiprows=skiprows, header=None)
        skiprows += nrows
        if not df_chunk.shape[0]:
            break
        else:
            print(f"  - chunk {i_chunk} ({df_chunk.shape[0]} rows)")
            chunks.append(df_chunk)
        i_chunk += 1
    
    df_chunks = pd.concat(chunks)
    # We need to rename the columns to concatenate the chunks with the header.
    columns = {i: col for i, col in enumerate(df_header.columns.tolist())}    
    df_chunks.rename(columns=columns, inplace=True)
    df_raw = pd.concat([df_header, df_chunks])
    df = harmonize_df(df_raw)
    return df


def main():
    t0 = time.time()
    dataframes = [make_df_from_excel(file_name) for file_name in EXCEL_FILES]
    print(f"Concatenate {len(dataframes)} dataframes into 1 and clean it")
    df = clean_df(pd.concat(dataframes)).reset_index().drop(columns=['index'])
    engine = sa.create_engine('sqlite:///tsa.db')
    df.to_sql('tsa_claims', con=engine, if_exists='append', index=False, chunksize=10000)
    t1 = time.time()
    print(f"Done in: {(t1 - t0):.2f} seconds")

if __name__ == '__main__':
    main()
