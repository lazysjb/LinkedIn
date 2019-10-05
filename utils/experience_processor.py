from datetime import datetime

import numpy as np
import pandas as pd


_MONTH_MAP = {
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12,
}

_MIN_WORK_YEAR = 1940
_MAX_WORK_YEAR = 2014
_PRESENT_Y_M = '2013-11'


def _validate_month(month_string):
    if month_string not in _MONTH_MAP:
        raise ValueError('month string {} is  not a valid month!'.format(month_string))


def _validate_year(year_string):
    if not year_string.isnumeric():
        raise ValueError('expected year string {} to be of numbers'.format(year_string))

    year_num = int(year_string)
    if (year_num > _MAX_WORK_YEAR) or (year_num < _MIN_WORK_YEAR):
        raise ValueError('year is {} which is outside the allowable range'.format(year_num))


def parse_work_date(date_string, date_type='start_date'):
    if pd.isnull(date_string):
        return np.nan

    if date_string == 'Present':
        if date_type == 'start_date':
            raise ValueError('We expect start_date cannot be "Present"')
        else:
            return datetime.strptime(_PRESENT_Y_M, '%Y-%m')

    splits = date_string.split()

    try:
        if len(splits) == 1:
            year = splits[0]
            # assume January start, December end if only yr provided
            if date_type == 'start_date':
                month_number = 2
            elif date_type == 'end_date':
                month_number = 1
            else:
                raise ValueError('invalid date_type arg {}'.format(date_type))
        elif len(splits) == 2:
            month, year = splits
            _validate_month(month)
            month_number = _MONTH_MAP[month]
        else:
            raise ValueError('Unexpected date string format with split length {}'.format(len(splits)))

        _validate_year(year)

        y_m_string = '{}-{}'.format(year, month_number)
        y_m = datetime.strptime(y_m_string, '%Y-%m')

        return y_m

    except Exception:
        # print('Skipping unparseable date string {}'.format(date_string))
        return np.nan


def parse_work_duration(duration_string):
    if duration_string == 'less than a year':
        return 12

    splits = duration_string.split()
    len_splits = len(splits)

    if len_splits not in [2, 4]:
        print('Unexpected duration string format of length {}, {}'.format(len_splits, duration_string))
        return np.nan

    num_months = 0

    for i in range(1, len_splits, 2):
        if splits[i] in ['year', 'years']:
            num_months += int(splits[i - 1]) * 12
        elif splits[i] in ['month', 'months']:
            num_months += int(splits[i - 1])
        else:
            # raise ValueError('Unexpected duration string format showing {}'.format(splits[i]))
            print('Unexpected duration string format showing {}'.format(splits[i]))
            return np.nan

    return num_months


def diff_month(date_end, date_start, zero_floor=True):
    n_months = (date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1
    if zero_floor:
        n_months = max(n_months, 0)

    return n_months


def get_person_stay_term(g_df):
    if (g_df['date_end'] == 'Present').any():
        return np.nan

    start_date_valid = g_df['date_start_parsed'].notnull()
    end_date_valid = g_df['date_end_parsed'].notnull()
    mask = start_date_valid & end_date_valid
    filtered_df = g_df[mask]

    if len(filtered_df) == 0:
        return np.nan

    # simplest case
    elif len(filtered_df) == 1:
        return filtered_df.iloc[0]['duration_parsed']

    else:
        return calc_non_overlapping_duration(g_df)


def is_current_job(person_id, org_person_df):
    date_end_values = org_person_df.loc[
        org_person_df['person_id'] == person_id, 'date_end']
    is_current = (date_end_values == 'Present').any()
    return is_current


def calc_non_overlapping_duration(df):
    starts = df['date_start_parsed'].tolist()
    ends = df['date_end_parsed'].tolist()
    start_end_pairs = list(zip(starts, ends))
    start_end_pairs = sorted(start_end_pairs, key=lambda x: x[0])

    i = 0
    total_n_months = 0

    while i < len(start_end_pairs):
        start_date = start_end_pairs[i][0]
        end_date = start_end_pairs[i][1]

        r = i + 1
        while r < len(start_end_pairs) and start_end_pairs[r][0] < end_date:
            end_date = max(end_date, start_end_pairs[r][1])
            r += 1
        total_n_months += diff_month(end_date, start_date)

        i = r
    return total_n_months
