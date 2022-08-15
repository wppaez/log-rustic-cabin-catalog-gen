#import libraries
from pyexpat.errors import codes
import shutil
from pathlib import Path
from typing import List

import pandas as pd
import numpy as np

def folder_setup() -> str:
    cwd= Path.cwd()
    output_folder = (cwd/'./output').resolve()
    shutil.rmtree(output_folder)
    Path(output_folder).mkdir(exist_ok=True)
    return str(output_folder)

def verbose(filename:str):
    df = pd.read_csv(f'input/{filename}.csv', encoding='utf-8', sep=',')
    print(df.columns)

def get_options_catalog(codes: List[str]):
    search_column = 'code (Variant SKU)'
    target_column = 'options'
    catalog = pd.read_csv(f'static/catalog.csv', encoding='utf-8', sep=',') 
    raw_rows: List[str] = list(catalog.loc[catalog[search_column].isin(codes), target_column])
    option_lines: List[List[str]] = [list(filter(None, raw_row.splitlines())) for raw_row in raw_rows]

    remove_quote = lambda x: x.replace('"', '')
    options_raw = [[list(map(remove_quote, value.split('" "'))) for value in line] for line in option_lines]
    options_as_dict = [[{"name": values[0], "values": values[1:]} for values in lines] for lines in options_raw]
    
    skus = []
    for index, option_dict in enumerate(options_as_dict):
        skus.append({
            "code": codes[index],
            "options": option_dict
        })
    
    for sku in skus:
        print('-----------------')
        print(f'    {sku["code"]}')
        for option in sku['options']:
            print(option)

def get_codes_from_original(filename:str) -> List[str]:
    code_column = 'Variant SKU'
    df = pd.read_csv(f'input/{filename}.csv', encoding='utf-8', sep=',')
    codes = df[code_column].str[:-3].unique()
    return codes

def main():
    output = folder_setup()
    debug = False
    filename = 'bedroom_sets_20220531_Wendy'
    if(debug):
        verbose(filename=filename)
    codes = get_codes_from_original(filename=filename)
    get_options_catalog(codes=codes)
    pass
     
if __name__ == '__main__':
    main()
