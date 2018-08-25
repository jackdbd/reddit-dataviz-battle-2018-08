import os
import time
import numpy as np
import pandas as pd


def main():
    # file_path = os.path.abspath(os.path.join('data', 'claims-2014.xls'))
    file_path = os.path.abspath(os.path.join('data', 'tsa_2016.xlsx'))
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    assert len(sheets) == 1
    t0 = time.time()
    # df = pd.read_excel(file_path, sheetname=sheets[0], nrows=100)
    df = pd.read_excel(file_path, sheetname=sheets[0])
    print('COLUMNS', df.columns)
    # ii0 = df[(df['Claim Number'].isnull()) & (df['Airport Name'].notnull())].index.values

    # ii = df[df['Claim Number'].notnull()].index.values
    rows = []
    for i, r in df.iterrows():
        r_pre = df.iloc[i-1]
        if pd.isnull(r_pre['Claim Number']):
            if pd.notnull(r_pre['Airport Name']):
                airport_name = f"{r_pre['Airport Name']} {r['Airport Name']}"
                # print(airport_name)
                r['Airport Name'] = airport_name
            else:
                continue
        rows.append(r)

    df = pd.DataFrame(rows, columns=df.columns)
    # df = df.drop(df.columns[11], axis=1)
    # df = df.drop('Unnamed: 11', axis=1)
    print(df.head())
    print(df.shape)
    print(df.columns)
    # print(df.iloc[:, 11])
    # for i,r in df.iterrows():
    #     print(r.values)
    # print('0', df.loc[0].values)
    # print('1', df.loc[1].values)
    # print('50', df.loc[50].values)
    # print('94', df.loc[94].values)
    print(df.describe())
    t1 = time.time()
    print(f"Done in: {(t1 - t0):.2f} seconds")

if __name__ == '__main__':
    main()

