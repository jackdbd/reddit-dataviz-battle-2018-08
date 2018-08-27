import os
import datetime
import logging
import numpy as np
import pandas as pd


# TODO: fix logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(formatter_str)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)


def harmonize_columns(df_in, drop_columns=False):
    columns = {
        'Airline Name': 'airline_name',
        'Airport Code': 'airport_code', 
        'Airport Name': 'airport_name',
        'Claim Amount': 'claim_amount',
        'Claim Number': 'claim_number',
        'Claim Type': 'claim_type',
        'Claim Site': 'claim_site',
        'Close Amount': 'close_amount',
        'Date Received': 'date_received',         
        'Disposition': 'disposition',
        'Incident D': 'incident_date',
        'Incident Date': 'incident_date',
        'Item': 'item',
        'Item Category': 'item',
        'Status': 'status',
    }
    df_out = df_in.rename(columns=columns)

    if drop_columns:
        cols_available = set(df_out.columns.values)
        cols_to_drop = set(['claim_number', 'claim_amount', 'status'])    
        cols_available_to_drop = list(cols_available.intersection(cols_to_drop))
        df_out.drop(columns=cols_available_to_drop, inplace=True)

    return df_out


def convert_ts(ts):
        ts_out = datetime.datetime(year=ts.year, month=ts.month, day=ts.day)
        # print(f"{ts} --> {ts_out}")
        return ts_out

def sanitize_dates(df_in):
    df_out = df_in
    # df_out['date_received'] = pd.to_datetime(df_in['date_received'], format='%Y-%m-%d', errors='coerce')
    # df_out['incident_date'] = pd.to_datetime(df_in['incident_date'], format='%Y-%m-%d', errors='coerce')

    df_out['date_received'] = pd.to_datetime(df_in['date_received'], errors='coerce')
    df_out['incident_date'] = pd.to_datetime(df_in['incident_date'], errors='coerce')
    return df_out


def produce_output(dataframes, files):
    for i, df in enumerate(dataframes):
        file_path = os.path.abspath(os.path.join('data', files[i]))
        file_name, file_extension = os.path.splitext(file_path) 
        csv_file = f"{file_name}.csv"
        df.to_csv(csv_file, sep=',', encoding='utf-8', index=False)


def assign_nan(df_in):
    df_out = df_in.replace(to_replace='-', value=np.nan)
    return df_out
