"""Convert PDF tables into a Pandas DataFrame.

Data from 2016 and 2017 is available in the PDF format. We can use tabula-py to
read it, but we have to handle a few different cases.

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
import tabula
import pandas as pd

def pdf_to_rows_columns(file_path):
    df = tabula.read_pdf(file_path, pages='1-3')
    # df = tabula.read_pdf(file_path, pages='all')
    rows = []
    for i, r in df.iterrows():
        print(f"ROW {i}", r.values)
        if pd.notnull(r['Claim Number']) and pd.notnull(r['Airport Name']) and i > 0:
            r_pre = df.iloc[i-1]
            if pd.isnull(r_pre['Claim Number']):
                if pd.notnull(r_pre['Airport Name']):
                    airport_name = f"{r_pre['Airport Name']} {r['Airport Name']}"
                    # print(f"{r['Airport Name']} --> {airport_name}")
                    r['Airport Name'] = airport_name
                    rows.append(r)
            else:
                rows.append(r)
    return rows, df.columns


def main():
    file_path = os.path.abspath(os.path.join('data', 'tsa claims data for 2016_0.pdf'))
    # file_path = os.path.abspath(os.path.join('data', '18_0314_OPA_2017_All_Airports_Data.pdf'))
    t0 = time.time()
    rows, columns = pdf_to_rows_columns(file_path)        
    df = pd.DataFrame(rows, columns=columns)
    # print(df.shape)
    for i in range(10):
        print(df.iloc[i].values)
        # assert isinstance(df['Claim Number'].iloc[i], int)

    print(df.head())
    print(df.describe())
    
    t1 = time.time()
    print(f"Done in: {(t1 - t0):.2f} seconds")

if __name__ == '__main__':
    main()

