# import libraries
import os
import re
import json
import shutil
import itertools
from pathlib import Path
from typing import Dict, Literal, List, Union

import pandas as pd
import numpy as np


def folder_setup() -> str:
    cwd = Path.cwd()
    output_folder = (cwd / './output').resolve()

    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    Path(output_folder).mkdir(exist_ok=True)
    return str(output_folder)


def get_codes_from_original(filename: str) -> List[str]:
    code_column = 'Variant SKU'
    df = pd.read_csv(f'input/{filename}.csv', encoding='utf-8', sep=',')
    codes = df[code_column].str[:-3].unique()
    return codes


def extract_number(value: str):
    matches = re.findall(r'\+\d+', value)

    if matches is None:
        return 0
    if len(matches) == 0:
        return 0

    return int(matches[0])


def format_option_value(value: str) -> Dict[str, Union[str, int]]:
    additional_rate = extract_number(value)
    formatted_value = value.replace(f'(+{additional_rate})', '').strip()

    return {
        "value": formatted_value,
        "additional_rate": additional_rate,
    }


SKU_OPTION_KEYS = Literal['alias', 'length', 'value', 'additional_rate']
SKU_OPTION_VALUE = Dict[SKU_OPTION_KEYS, Union[str, int]]
SKU_OPTION_KEY = Literal['name', 'alias', 'values']
SKU_OPTION = Dict[SKU_OPTION_KEY, Union[str, List[SKU_OPTION_VALUE]]]
SKU_KEY = Literal['code', 'options', 'basic_rate']
SKU_VALUE = Union[int, str, List[SKU_OPTION]]
SKU = Dict[SKU_KEY, SKU_VALUE]


def get_options_catalog(codes: List[str]) -> List[SKU]:
    search_column = 'code (Variant SKU)'
    target_column = 'options'
    catalog = pd.read_csv(f'static/catalog.csv', encoding='utf-8', sep=',')
    catalog_mask = catalog[search_column].isin(codes)
    match = catalog.loc[catalog_mask, [search_column, target_column]]
    searchable = match.set_index([search_column])

    raw_rows: List[str] = list(searchable.loc[codes][target_column])
    option_lines: List[List[str]] = [
        list(filter(None, raw_row.splitlines())) for raw_row in raw_rows]

    remove_quote = lambda x: x.replace('"', '')
    options_raw = [
        [list(map(remove_quote, re.split(r'"\s+"', value))) for value in line]
        for line in option_lines
    ]

    options_as_dict = [
        [{"name": values[0], "values": values[1:]} for values in lines]
        for lines in options_raw
    ]

    skus = []
    for index, option_dict in enumerate(options_as_dict):
        skus.append({
            "code": codes[index],
            "options": option_dict
        })

    for sku in skus:
        for (index, option) in enumerate(sku['options']):
            option['values'] = list(map(format_option_value, option['values']))
            option['length'] = len(option['values'])
            option['alias'] = f'Option{index + 1} Name'

            for value in option['values']:
                value['alias'] = f'Option{index + 1} Value'
        sku['option_length'] = len(sku['options'])

    return skus


def fill_basic_rate(filename: str, skus: List[SKU]) -> List[SKU]:
    df = pd.read_csv(f'input/{filename}.csv', encoding='utf-8', sep=',')
    pass


def get_output_columns(filename: str, skus: List[SKU]) -> List[str]:
    df = pd.read_csv(f'input/{filename}.csv', encoding='utf-8', sep=',')
    cols: List[str] = df.columns.to_list()

    option_lengths = list(map(lambda x: x['option_length'], skus))
    max_options = max(option_lengths)
    option_cols = []
    for i in range(max_options):
        option_cols.append(f'Option{i + 1} Name')
        option_cols.append(f'Option{i + 1} Value')

    old_index = [i for i, col in enumerate(cols) if col.startswith('Option')]

    cols[old_index[0]: old_index[-1]] = option_cols

    return cols


def build_output(columns: List[str], skus: List[SKU]):
    output_df = pd.DataFrame(columns=columns)

    # No se como generar bien las filas :C

    ram = {}
    for sku in skus:
        ram['Variant SKU'] = sku['code']
        merged = [[value["value"] for value in option["values"]]
                  for option in sku['options']]

        combinations = itertools.product(*merged)

        for combiation in combinations:
            pass

    # for option in sku['options']:

    #     ram[option['alias']] = sku['code']
    #     for value in option['values']:
    #         ram[value['alias']] = value['value']
    #         print(ram)


def main():
    output = folder_setup()

    filename = 'bedroom_sets_20220531_Wendy'

    codes = get_codes_from_original(filename=filename)
    skus = get_options_catalog(codes=codes)
    output_columns = get_output_columns(filename=filename, skus=skus)
    # print(output_columns)
    build_output(columns=output_columns, skus=skus)
    # print(json.dumps({"skus": skus}))
    # skus = fill_basic_rate(filename, options)
    pass


if __name__ == '__main__':
    main()
