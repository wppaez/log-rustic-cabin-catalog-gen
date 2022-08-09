#import libraries
import pandas as pd
from pathlib import Path
import shutil

def folder_setup() -> str:
    cwd= Path.cwd()
    output_folder = (cwd/'./output').resolve()
    shutil.rmtree(output_folder)
    Path(output_folder).mkdir(exist_ok=True)
    return str(output_folder)

def process_csv(path:str, output:str):
    df = pd.read_csv(f'input/{path}', encoding='utf-8', sep=';') 
    df['Variant Inventory Qty'] = 1000
    test= df.groupby('Variant SKU').cumcount()+1
    df['Variant SKU']= df['Variant SKU'].str[:-2] + test.astype('string').str.pad(width=2,fillchar='0')
    df.to_csv(f'{output}/{path}', index= False, encoding='utf_8_sig', sep=";")
    print('DONE')

def main():
    output = folder_setup()
    process_csv(path ='bedroom_sets_20220531_Wendy.csv',output=output) 
     
if __name__ == '__main__':
    main()
