"""Util to handle processing of LIWC files"""

from glob import glob
import os
import re

import numpy as np
from tqdm import tqdm

from config import (
    LIWC_VECTOR_ROOT_DIR, LIWC_VECTOR_SAVE_SUBDIR, LIWC_VECTOR_FILE_FORMAT,
    LIWC_DISTANCE_FILE_FORMAT
)
from liwc_utils.constants import LIWC_FIELD_NAMES
from liwc_utils.distances import Cosine, Euclidean, JSDivergence, Mahalanobis

COMPANY_COLUMN_NAME = 'company'
PERSON_ID_COLUMN_NAME = 'Filename.x'


def process_liwc_source_df(liwc_df, liwc_cols=LIWC_FIELD_NAMES, verbose=False):
    """Save consolidate liwc df into npz chunks by company

    Args:
        liwc_df: DataFrame - for each row the dataframe consists of:
            person ids,
            liwc_vector (with a .x postfix) to indicate liwc vector at person level
            liwc vector (with a .y postfix) to indicate liwc vector at company level

    Returns:
        None - save data to .npz files at company level
    """
    REG_BEGIN_MATCH = re.compile('^.*__')
    REG_END_MATHCH = re.compile('\.txt$')

    def _transform_text(text):
        sub = re.sub(REG_BEGIN_MATCH, '', text)
        sub = re.sub(REG_END_MATHCH, '', sub)

        return sub

    for company_name, sub_liwc_df in tqdm(liwc_df.groupby(COMPANY_COLUMN_NAME)):
        person_ids = sub_liwc_df[PERSON_ID_COLUMN_NAME].apply(_transform_text).values
        company_person_ids = company_name + '__' + person_ids

        x_col_names = [c + '.x' for c in liwc_cols]
        y_col_names = [c + '.y' for c in liwc_cols]

        person_vectors = sub_liwc_df[x_col_names].values
        company_vector = sub_liwc_df[y_col_names].iloc[0].values

        save_filepath = os.path.join(LIWC_VECTOR_ROOT_DIR,
                                     LIWC_VECTOR_SAVE_SUBDIR,
                                     LIWC_VECTOR_FILE_FORMAT).format(company_name=company_name)

        np.savez(save_filepath,
                 company_person_ids=company_person_ids,
                 person_vectors=person_vectors,
                 company_vector=company_vector)

        if verbose:
            print('Saving raw liwc vector to npz file {}'.format(save_filepath))

    return None


def process_liwc_distances(source_dir, dest_dir):

    distance_name_map = {
        'cosine': [Cosine, [True, False]],
        'euclidean': [Euclidean, [True, False]],
        'mahalonobis': [Mahalanobis, [True, False]],   # mahalonobis is already standardized
        'js_divergence': [JSDivergence, [True, False]],
    }

    liwc_vector_filepaths = glob(os.path.join(source_dir, '*.npz'))
    for filepath in tqdm(liwc_vector_filepaths):
        company_name = os.path.basename(filepath).replace('_raw_liwc.npz', '')
        raw_liwc_data = np.load(filepath, allow_pickle=True)
        X = raw_liwc_data['person_vectors']
        y = raw_liwc_data['company_vector']

        to_save = {'company_person_ids': raw_liwc_data['company_person_ids']}

        for k, v in distance_name_map.items():
            distance_metric, standardize_args = v
            for standardize_arg in standardize_args:
                if standardize_arg:
                    distance_name = k + '_standardized'
                else:
                    distance_name = k
                distances = distance_metric(X, y, standardize=standardize_arg).calc_distance()
                to_save[distance_name] = distances

        save_filepath = os.path.join(dest_dir,
                                     LIWC_DISTANCE_FILE_FORMAT.format(company_name=company_name))
        np.savez(save_filepath, **to_save)
