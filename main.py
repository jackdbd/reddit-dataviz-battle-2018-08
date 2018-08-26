import os
import time
import numpy as np
import pandas as pd
import sqlalchemy as sa
import altair as alt


def clean_df(df):
    df.replace(to_replace='-', value=np.nan, inplace=True)
    return df


def main():
    engine = sa.create_engine('sqlite:///tsa.db')
    # file_path = os.path.abspath(os.path.join('data', 'claims-2002-2006_0.xls'))
    # file_path = os.path.abspath(os.path.join('data', 'claims-2007-2009_0.xls'))
    # file_path = os.path.abspath(os.path.join('data', 'claims-2010-2013_0.xls'))
    file_path = os.path.abspath(os.path.join('data', 'claims-2014.xls'))
    # file_path = os.path.abspath(os.path.join('data', 'claims-data-2015-as-of-feb-9-2016.xlsx'))
    xl = pd.ExcelFile(file_path)
    print(f'{file_path}')
    sheets = xl.sheet_names
    print('Excel worksheets', sheets)
    assert len(sheets) == 1
    t0 = time.time()
    # df = pd.read_excel(file_path, sheetname=sheets[0], nrows=100)
    df = pd.read_excel(file_path, sheetname=sheets[0])
    # df.to_sql('tsa_claims', engine, if_exists='append')
    # df = df.drop(df.columns[11], axis=1)
    # df = df.drop('Unnamed: 11', axis=1)
    df = clean_df(df)
    print(df.head())
    print(df.shape)
    for col in df.columns:
        nan_count = df[col].isnull().sum()
        print(f"\n{col}")
        print(f"NaN count {nan_count}")
        print(df[col].describe())

    
    alt.Chart(df).mark_bar().encode(
        x=alt.X("Close Amount:Q", bin=True),
        y='count()'
    )

    # for i in range(10):
    #     print(df.iloc[i].values)
    t1 = time.time()
    print(f"Done in: {(t1 - t0):.2f} seconds")

if __name__ == '__main__':
    main()

