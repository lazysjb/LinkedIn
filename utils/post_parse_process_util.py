from glob import glob
import json
import os
import time

import pandas as pd
from tqdm import tqdm

from config import PARSED_CONTENT_ROOT_DIR
from db_config import (
    PERSON_META_TABLE, PERSON_EXPERIENCE_TABLE,
    PERSON_SPECIALTY_TABLE, PERSON_SUMMARY_TABLE
)
from utils.db_util import write_to_db


def _read_json(fpath):
    with open(fpath, 'r') as f:
        content = json.load(f)
    return content


def get_person_id_infos(fpath):
    components = fpath.split('/')
    file_name = components[-1].split('.')[0]
    parent_folder = components[-2]
    batch_folder = components[-3]
    person_id = '_'.join([file_name, parent_folder, batch_folder])

    return person_id, parent_folder, batch_folder


def _extract_keys_from_dict(dict_struct, keys):
    """Get values from a dict of dicts"""
    result = dict_struct.copy()

    for key in keys:
        result = result[key]

    return result


def extract_person_meta(file_path, parsed_content):
    person_id, parent_folder, batch_folder = get_person_id_infos(file_path)

    given_name = _extract_keys_from_dict(parsed_content, ['header', 'name', 'given_name'])
    family_name = _extract_keys_from_dict(parsed_content, ['header', 'name', 'family_name'])
    header_title = _extract_keys_from_dict(parsed_content, ['header', 'title'])
    header_location = _extract_keys_from_dict(parsed_content, ['header', 'location'])
    header_industry = _extract_keys_from_dict(parsed_content, ['header', 'industry'])

    result = {
        'person_id': person_id,
        'parent_folder': parent_folder,
        'batch_folder': batch_folder,
        'given_name': given_name,
        'family_name': family_name,
        'header_title': header_title,
        'header_location': header_location,
        'header_industry': header_industry,
    }

    return result


def extract_person_summary(file_path, parsed_content):
    person_id, parent_folder, batch_folder = get_person_id_infos(file_path)
    person_summary = parsed_content['summary']

    return {
        'person_id': person_id,
        'person_summary': person_summary,
    }


def extract_person_specialty(file_path, parsed_content):
    person_id, parent_folder, batch_folder = get_person_id_infos(file_path)
    person_specialty = parsed_content['specialty']

    return {
        'person_id': person_id,
        'person_specialty': person_specialty,
    }


def _is_current_experience(experience_item):
    date_end = _extract_keys_from_dict(experience_item, ['period', 'date_end'])
    return date_end == 'Present'


def extract_person_experience(file_path, parsed_content):
    person_id, parent_folder, batch_folder = get_person_id_infos(file_path)

    experience_list = parsed_content['experience']

    result = []

    for idx, experience_item in enumerate(experience_list):
        org_name = experience_item['org_summary']
        org_profile_link = experience_item['company_profile']
        org_detail = experience_item['org_detail']

        experience_title = experience_item['title']
        experience_location = experience_item['location']
        experience_description = experience_item['description']
        date_start = _extract_keys_from_dict(experience_item, ['period', 'date_start'])
        date_end = _extract_keys_from_dict(experience_item, ['period', 'date_end'])
        duration = _extract_keys_from_dict(experience_item, ['period', 'duration'])

        # delete parenthesis from duration
        if isinstance(duration, str):
            if duration.startswith('('):
                duration = duration[1:]

            if duration.endswith(')'):
                duration = duration[:-1]

        is_current = _is_current_experience(experience_item)

        result.append({
            'person_id': person_id,
            'experience_id': idx,
            'org_name': org_name,
            'org_profile_link': org_profile_link,
            'org_detail': org_detail,
            'experience_title': experience_title,
            'experience_location': experience_location,
            'experience_description': experience_description,
            'date_start': date_start,
            'date_end': date_end,
            'duration': duration,
            'is_current': is_current,
        })

    return result


def run_parsed_to_db(batch_dir,
                     db_conn,
                     sub_dir_list=None,
                     root_dir=PARSED_CONTENT_ROOT_DIR):
    tic = time.time()

    if sub_dir_list is None:
        sub_dir_list = os.listdir(os.path.join(root_dir, batch_dir))

    for sub_dir in tqdm(sub_dir_list):
        parsed_paths = glob(os.path.join(root_dir, batch_dir, sub_dir, '*.json'))

        person_meta_contents = []
        person_summary_contents = []
        person_specialty_contents = []
        person_experience_contents = []

        for fpath in parsed_paths:
            parsed_content = _read_json(fpath)

            person_meta_contents.append(extract_person_meta(fpath, parsed_content))
            person_summary_contents.append(extract_person_summary(fpath, parsed_content))
            person_specialty_contents.append(extract_person_specialty(fpath, parsed_content))
            person_experience_contents.extend(extract_person_experience(fpath, parsed_content))

        person_meta_contents = pd.DataFrame(person_meta_contents)
        person_summary_contents = pd.DataFrame(person_summary_contents)
        person_specialty_contents = pd.DataFrame(person_specialty_contents)
        person_experience_contents = pd.DataFrame(person_experience_contents)

        write_to_db(person_meta_contents,
                    db_conn,
                    PERSON_META_TABLE, schema='linkedin', if_exists='append')

        write_to_db(person_experience_contents,
                    db_conn,
                    PERSON_EXPERIENCE_TABLE, schema='linkedin', if_exists='append')

        write_to_db(person_summary_contents,
                    db_conn,
                    PERSON_SUMMARY_TABLE, schema='linkedin', if_exists='append')

        write_to_db(person_specialty_contents,
                    db_conn,
                    PERSON_SPECIALTY_TABLE, schema='linkedin', if_exists='append')

    toc = time.time()
    total_time = (toc - tic) / 60
    print('process finished took {} mins'.format(total_time))
