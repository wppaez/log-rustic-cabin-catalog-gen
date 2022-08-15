#import libraries
from enum import unique
import shutil
from pathlib import Path

import pandas as pd
import numpy as np

def folder_setup() -> str:
    cwd= Path.cwd()
    output_folder = (cwd/'./output').resolve()
    shutil.rmtree(output_folder)
    Path(output_folder).mkdir(exist_ok=True)
    return str(output_folder)

def process_csv(filename:str, output:str):
    search_column = 'Variant SKU'
    swapable_columns = [
        'Option1 Value',            # j
        'Option2 Value',            # l
        'Option3 Value',            # n
        'Variant Price',            # u
        'Variant Compare At Price', # v
        'Image Src',                # z
        'Image Position',           # aa
        'Image Alt Text',           # ab
    ]
    numeric_columns = [
        'Variant Price',            # u
        'Variant Compare At Price', # v
        'Image Position',           # aa
    ]

    db = pd.read_csv(f'static/db.csv', encoding='utf-8', sep=',') 
    df = pd.read_csv(f'input/{filename}.csv', encoding='utf-8', sep=',') 
    
    for group_key in df[search_column].unique():
        mask = df[search_column] == group_key
        df.loc[mask,'Variant Inventory Qty'] = 1000/int(df[mask].count()[search_column])
        df.loc[mask, 'Variant Inventory Qty'] = df.loc[mask, 'Variant Inventory Qty'].astype(np.int64)
        print(1000/int(df[mask].count()[search_column]))

    test= df.groupby(search_column).cumcount()+1
    df[search_column]= df[search_column].str[:-2] + test.astype('string').str.pad(width=2,fillchar='0')

    print('Generating ids')
    df.to_csv(f'{output}/{filename}_sku_ready.csv', index= False, encoding='utf-8', sep=",")
    sku_codes = list(df[search_column].unique())

    print('Replacing from original')
    for sku_code in sku_codes:
        print(f'    Browsing {sku_code}')
        raw_row = db.loc[db[search_column] == sku_code, swapable_columns].round(decimals=0)

        for numeric_column in numeric_columns:
            mask = pd.to_numeric(raw_row[numeric_column]).notnull()
            raw_row.loc[mask, numeric_column] = raw_row.loc[mask, numeric_column].astype(np.int64)

        raw_row['Image Position'] = raw_row['Image Position'].fillna('').astype(str).str.replace(".0","",regex=False)

        df.loc[df[search_column] == sku_code, swapable_columns] = raw_row.values.tolist()
    
    df.to_csv(f'{output}/{filename}_replaced_from_original.csv', index= False, encoding='utf-8', sep=",")
    print('Replaced')


def main():
    output = folder_setup()
    process_csv(filename ='bedroom_sets_20220531_Wendy',output=output) 
     
if __name__ == '__main__':
    main()
