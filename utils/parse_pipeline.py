from glob import glob
import json
import multiprocessing
import os
import time

from config import LOG_DIR, PARSED_CONTENT_DIR, SOURCE_DATA_DIR
from utils.parse_util import (
    HTMLFileReader, LinkedInProfileParser
)


_LOG_TOTAL_TIME_KEY = 'total_time'
_LOG_PARSE_ERROR_KEY = 'parse_error'
_LOG_FILECOUNT_KEY = 'num_files'
_LOG_EMPTY_FILE_KEY = 'empty_html_list'
_MIN_SUMMARY_PROFILE_LEN = 100


def _is_dir(filename):
    """Heuristic"""
    return filename.endswith('/')


def _get_dir_from_zip_filename(filename):
    return filename.split('/')[0]


def get_zipfile_directories(zf, sort=False):
    directories = []

    for filename in zf.namelist():
        if _is_dir(filename):
            directory = _get_dir_from_zip_filename(filename)
            directories.append(directory)

    if sort:
        # assume directory is an int
        directories = sorted(directories, key=lambda x: int(x))

    return directories


def get_file_content_generator_from_zip_directory(zf, usr_directory):
    for filename in zf.namelist():
        if not _is_dir(filename):
            directory = _get_dir_from_zip_filename(filename)
            if directory == usr_directory:
                with zf.open(filename) as f:
                    content = f.read()
                    yield filename, content


def get_file_content_generator_from_directory(directory):
    file_paths = glob(os.path.join(directory, '*.html'))
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            raw_html_text = f.read()
        yield file_path, raw_html_text


def parse_profile(profile_raw_html, from_zip=False):
    if from_zip:
        html_reader = HTMLFileReader.load_from_zipfile_html_text(profile_raw_html)
    else:
        html_reader = HTMLFileReader.load_from_html_text(profile_raw_html)

    clean_html = html_reader.get_clean_html_text()

    li_profile = LinkedInProfileParser(clean_html)
    li_profile.parse()
    li_profile_dict = li_profile.get_formatted_content()
    return li_profile_dict


def _is_profile_to_save(parsed_profile):
    summary_content = parsed_profile['summary']

    if (summary_content is not None) and (len(summary_content) > _MIN_SUMMARY_PROFILE_LEN):
        return True
    else:
        return False


def parse_profiles_for_directory(profile_dir, from_zip=False, zf=None):
    """zf: zipfile object"""
    my_logger = MyLogger()
    my_writer = FileWriter()

    tic = time.time()

    lowest_dir = profile_dir.split('/')[-1]

    if from_zip:
        raw_profile_contents = get_file_content_generator_from_zip_directory(zf, profile_dir)
    else:
        raw_profile_contents = get_file_content_generator_from_directory(profile_dir)

    n_files = 0
    for file_path, raw_html in raw_profile_contents:

        try:
            parsed = parse_profile(raw_html)

            # write parsed if it meets condition - summary > 100 chars
            if _is_profile_to_save(parsed):
                input_file_name = os.path.basename(file_path).split('.')[0]
                subdir = os.path.basename(profile_dir)
                my_writer.write_as_json(parsed,
                                        subdir=subdir,
                                        file_prefix=input_file_name)
        except Exception as e:

            error_message = str(e)
            if 'Document is empty' in error_message:
                # empty html file
                my_logger.records_item_append(_LOG_EMPTY_FILE_KEY, file_path)
            else:
                my_logger.record_item_update_dict(_LOG_PARSE_ERROR_KEY,
                                                  (file_path, error_message))

        n_files += 1
    toc = time.time()

    my_logger.record_item(_LOG_TOTAL_TIME_KEY, (toc - tic) / 60)
    my_logger.record_item(_LOG_FILECOUNT_KEY, n_files)
    my_logger.write_as_json(file_prefix=lowest_dir)
    print('Finished run for {}'.format(profile_dir))
    return


def run_parse_pipeline(root_dir=SOURCE_DATA_DIR,
                       sub_dirs_to_run=None,
                       n_process=5):
    # if sub_dirs_to_run is specified, run those sub_dirs only
    # otherwise run all dirs under root_dir
    if sub_dirs_to_run is None:
        sub_dirs_to_run = os.listdir(root_dir)

    dirs_to_run = [os.path.join(root_dir, s) for s in sub_dirs_to_run]

    print('Running parsing for {} directories'.format(len(dirs_to_run)))

    p = multiprocessing.Pool(n_process)
    p.map(parse_profiles_for_directory, dirs_to_run)
    p.close()
    return


class MyLogger:

    def __init__(self, log_dir=LOG_DIR):
        self.log_dir = log_dir
        self.log_record = self._init_log_record()
        self.log_file_format = '{}_log.json'

    def _init_log_record(self):
        log_record = dict()
        log_record[_LOG_EMPTY_FILE_KEY] = []
        log_record[_LOG_PARSE_ERROR_KEY] = dict()
        return log_record

    def record_item(self, log_item_key, log_content):
        self.log_record[log_item_key] = log_content

    def records_item_append(self, log_item_key, log_content):
        self.log_record[log_item_key].append(log_content)

    def record_item_update_dict(self, log_item_key, log_content_kv):
        log_content_key, log_content_value = log_content_kv

        self.log_record[log_item_key][log_content_key] = log_content_value

    def write_as_json(self, file_prefix=None):
        file_path = os.path.join(self.log_dir, self.log_file_format.format(file_prefix))

        with open(file_path, 'w') as f:
            json.dump(self.log_record, f, indent=4)


class FileWriter:

    def __init__(self, root_dir=PARSED_CONTENT_DIR):
        self.root_dir = root_dir
        self.json_file_format = '{}.json'

    def write_as_json(self, content, subdir=None, file_prefix=None):
        subdir_path = os.path.join(self.root_dir, subdir)

        if not os.path.exists(subdir_path):
            os.mkdir(subdir_path)

        file_path = os.path.join(subdir_path, self.json_file_format.format(file_prefix))
        with open(file_path, 'w') as f:
            json.dump(content, f, indent=4)
