# import libraries
from multiprocessing import current_process
import os
import re
import math
import shutil
import itertools
from pathlib import Path
from typing import Dict, Literal, List, Union

import numpy as np
import pandas as pd

import json
import pyperclip as pc


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
        sku['replacements'] = []

    return skus


def cast_as_int_if_possible(value):
    try:
        parsed = int(value)
        return parsed
    except ValueError:
        if value == np.NaN:
            return ''
        if (type(value) == str):
            return value.strip()
        return value.astype(str).replace('nan', '').replace('NaN', '')


def fill_sku_data_from_original(filename: str, skus: List[SKU]) -> List[SKU]:
    search_col = "Variant SKU"                              # O,
    source_cols = [
        "Handle",                                           # A,
        "Title",                                            # B,
        "Body (HTML)",                                      # C,
        "Vendor",                                           # D,
        "Standardized Product Type",                        # E,
        "Custom Product Type",                              # F,
        "Tags",                                             # G,
        "Published",                                        # H,
        "Variant Grams",                                    # P?,
        "Variant Inventory Tracker",                        # Q?,
        "Variant Inventory Policy",                         # S?,
        "Variant Fulfillment Service",                      # T?,
        "Variant Requires Shipping",                        # W?,
        "Variant Taxable",                                  # X?,
        "Variant Barcode",                                  # Y?,
        # "Image Alt Text",                                   # AB?,
        "Gift Card",                                        # AC?,
        "SEO Title",                                        # AD?,
        "SEO Description",                                  # AE?,
        "Google Shopping / Google Product Category",        # AF?,
        "Google Shopping / Gender",                         # AG?,
        "Google Shopping / Age Group",                      # AH?,
        "Google Shopping / MPN",                            # AI?,
        "Google Shopping / AdWords Grouping",               # AJ?,
        "Google Shopping / AdWords Labels",                 # AK?,
        "Google Shopping / Condition",                      # AL?,
        "Google Shopping / Custom Product",                 # AM?,
        "Google Shopping / Custom Label 0",                 # AN?,
        "Google Shopping / Custom Label 1",                 # AO?,
        "Google Shopping / Custom Label 2",                 # AP?,
        "Google Shopping / Custom Label 3",                 # AQ?,
        "Google Shopping / Custom Label 4",                 # AR?,
        "Variant Image",                                    # AS?,
        "Variant Weight Unit",                              # AT?,
        "Variant Tax Code",                                 # AU?,
        "Cost per item",                                    # AV?,
        "Status",                                           # AW?,
    ]

    df = pd.read_csv(f'input/{filename}.csv', encoding='utf-8', sep=',')

    for sku in skus:
        search_condition = (df[search_col] == f'{sku["code"]}-01')
        original_raw = df[search_condition].iloc[0]

        sku['basic_rate'] = int(original_raw['Variant Price'])
        sku['compare_rate'] = int(original_raw['Variant Compare At Price'])

        for source_col in source_cols:

            formatted_value = cast_as_int_if_possible(original_raw[source_col])

            sku["replacements"].append({
                "column": source_col,
                "value": formatted_value
            })

    return skus


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

    return (cols, option_cols)


def format_options_to_dict(option):
    value_dict = {idx: value for (idx, value) in enumerate(option["values"])}
    return {
        option["name"]: value_dict
    }


def build_output(columns: List[str], skus: List[SKU], option_columns: List[str]):
    separator = '|||'

    rows = []
    for sku in skus:
        print(f'Processing {sku["code"]}:')

        merged = [[f'{option["name"]}{separator}{value["value"]}'
                   for value in option["values"]]
                  for option in sku['options']
                  ]

        combinations = list(map(list, itertools.product(*merged)))

        col_map = {option["name"]: option["alias"]
                   for option in sku['options']}
        rate_map = {option["name"]: {value["value"]: value["additional_rate"]
                                     for value in option["values"]}
                    for option in sku['options']}

        combination_size = len(combinations)
        ratio = math.floor(1000 / combination_size)
        reminder = 1000 - (ratio * len(combinations))

        should_log = 0
        for (index, combiation) in enumerate(combinations):
            combination_number = f'{index +1}'.rjust(2, '0')

            current_progress = (index + 1) / combination_size
            if (should_log < current_progress):
                print(
                    f'  - {(index + 1)}/{combination_size} ({current_progress *100}%)')
                should_log += 0.25

            row_payload = {}
            row_payload["Variant SKU"] = f'{sku["code"]}-{combination_number}'

            extra_rate = 0
            for item in combiation:
                opt_key, opt_val = item.split(separator)
                col_name = col_map[opt_key]
                col_value = col_map[opt_key].replace('Name', 'Value')
                row_payload[col_name] = opt_key
                row_payload[col_value] = opt_val
                extra_rate += rate_map[opt_key][opt_val]

            for option_column in option_columns:
                if option_column not in row_payload:
                    row_payload[option_column] = ''

            row_payload['Variant Inventory Qty'] = ratio
            if (index < reminder):
                row_payload['Variant Inventory Qty'] += 1

            row_payload['Variant Price'] = sku['basic_rate'] + extra_rate
            row_payload['Variant Compare At Price'] = sku['compare_rate'] + extra_rate

            for replacement in sku["replacements"]:
                row_payload[replacement["column"]] = replacement["value"]

            for missing_column in columns:
                if missing_column not in row_payload:
                    row_payload[missing_column] = ''

            rows.append(row_payload)

        print(f'  - {combination_size}/{combination_size} (100%)')
    output_df = pd.DataFrame.from_dict(rows)
    output_df = output_df.reindex(columns=columns)
    return output_df


def main():
    output = folder_setup()

    filename = 'bedroom_sets_20220531_Wendy'

    codes = get_codes_from_original(filename=filename)
    skus = get_options_catalog(codes=codes)
    skus = fill_sku_data_from_original(filename=filename, skus=skus)
    output_columns, option_columns = get_output_columns(filename=filename,
                                                        skus=skus)

    output_df = build_output(columns=output_columns,
                             skus=skus,
                             option_columns=option_columns)

    print("Writing CSV...")
    output_df.to_csv(f'{output}/{filename}_from_catalog.csv',
                     index=False, sep=",", encoding='utf-8')

    pc.copy(json.dumps({"data": skus}))
    print("CSV Generated!")

    return 0


if __name__ == '__main__':
    main()
