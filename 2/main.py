"""
Parses the input file into dataframe, searching for substrings of type
([\d]+[.]*[,]*[ ]*[\d]*\/*[\d]*.*?({'|'.join(UNITS_TO_LOOK_FOR)})) in the "rawDim" column,
 where UNITS_TO_LOOK_FOR are defined in settigs.py.
Extracts numbers and the unit type from found substrings, and converts the values
to PREFFERED_LENGHT_UNIT using pint library
"""

import pandas as pd
import re
from settings import *
from pint import UnitRegistry, UndefinedUnitError
from fractions import Fraction
import numpy as np
import logging


def convert_fraction_string_to_decimal_string(v):
    # https://stackoverflow.com/a/1806309/4258005
    # This doesnt work properly with negative values, but i guess we shouldnt really come across any
    return str(float(sum(Fraction(s) for s in v.split())))


def check_if_unit_exists_in_pint(unit):
    try:
        ureg(unit)
        return True
    except UndefinedUnitError:
        return False


def get_desired_dimension_set(dimension_variants):
    """
    Given the list of possible dimension variants, chooses the one with measurement unit defined
    in PREFFERED_LENGHT_UNIT in settings.py.
    If there are multiple possible options, or none matching the PREFFERED_LENGHT_UNIT
    chooses the last one in the list with unit existing in pint, since there is no clear definition in the task.
    Might be an overkill since we can get any dimension variant and convert to the required unit, but it seems like
    in the raw stings different dimensions dont always match, either due to rounding or something else.
    For example line 4: 168.9 x 274.3 x 3.8 cm (66 1/2 x 108 x 1 1/2 in.). But 66.5 * 2.54 = 168.91<
    So this way we can control more over what data we get
    :param dimension_variants: list of pairs, containing the raw dimensions string and the measurement unit
    [(1x1cm, cm),...]
    :return: pair with raw string and measurement unit, (1x1cm, cm) or None
    """
    desired_dimensions = None
    last_set_with_existing_unit = None
    for variant in dimension_variants:
        if not check_if_unit_exists_in_pint(variant[-1]):
            continue
        last_set_with_existing_unit = variant
        if variant[-1] == PREFFERED_LENGHT_UNIT:
            desired_dimensions = variant
    if not desired_dimensions:
        desired_dimensions = last_set_with_existing_unit
    return desired_dimensions


if __name__ == '__main__':
    ureg = UnitRegistry()
    dim_df = pd.read_csv("../candidateEvalData/dim_df_correct.csv")
    # lowercase the raw string so that pint can recognize upper case units. Maybe its assumed
    # that data is already prepared, but just in case
    dim_df['rawDim'] = dim_df['rawDim'].str.lower()
    # Find all the substrings containing units and the numbers before them
    # Could probably be improved by listing all the possible units from pint in the capture group,
    # but need to be careful about cases like 150 mm, we could match meters instead
    re_dimensions_string = re.compile(rf"([\d]+[.]*[,]*[ ]*[\d]*\/*[\d]*.*?({'|'.join(UNITS_TO_LOOK_FOR)}))")
    # Find all the number formats that could represent a dimension
    re_single_dimension = re.compile(r"[\d]+[.]*[,]*[ ]*[\d]*\/*[\d]*")
    # dataframe to compare against the correct one in the end to check the correctness.
    result_df = pd.DataFrame(columns=["rawDim", "height", "width", "depth"])

    for i, raw_string in enumerate(dim_df['rawDim']):
        h_w_d = [np.nan] * 3
        dimension_variants = re_dimensions_string.findall(raw_string)
        if not dimension_variants:
            logging.warning(f'Could not find dimensions in dim_df_correct.csv, row-{i}')
            continue

        # get the dimensions in the form of (1x1cm, cm)
        desired_dimensions = get_desired_dimension_set(dimension_variants)
        if not desired_dimensions:
            logging.warning(f'Could not find dimensions in dim_df_correct.csv, row-{i}')
            continue
        desired_dimensions_measurement_unit = desired_dimensions[-1]
        desired_dimensions_string = desired_dimensions[0]

        # parse every single dimension in the dimensions string
        for j, value in enumerate(re_single_dimension.findall(desired_dimensions_string)):
            # check if the value came in the form of a fraction
            if '/' in value:
                try:
                    value = convert_fraction_string_to_decimal_string(value)
                except ValueError:
                    logging.error(f'Could not convert fraction string in dim_df_correct.csv, row-{i}')
                    h_w_d[j] = np.nan
                    continue
            #convert from the current unit to the desired one
            try:
                value = ureg(f"{value}{desired_dimensions_measurement_unit}".replace(',', '.')).to(
                    PREFFERED_LENGHT_UNIT)
            except UndefinedUnitError:
                logging.error(f'Could not convert units in dim_df_correct.csv, row-{i}. Skipping the dimension')
                h_w_d[j] = np.nan
                continue
            h_w_d[j] = float(value.magnitude)

        result_df.loc[len(result_df)] = [raw_string, *h_w_d]

    print(result_df)
    print(dim_df)
    print(result_df == dim_df)
    print(dim_df.equals(result_df))
