import os
from utils.parse_util import HTMLFileReader, LinkedInProfileParser
import numpy as np
from liwc_utils.distances import Euclidean, Mahalanobis
# from pandas.io.json import json_normalize
# import json
# import pandas as pd
# import flatten_json

# Distance calculation testing

LIWC_NPZ_DIR = ('/home/sjb/Projects/Research/LinkedIn_OB/data/'
                'word_features/company_level_liwc/raw_vectors/')
SAMPLE_FILE = 'jpmorgan-chase_raw_liwc.npz'
raw_liwc_data = np.load(os.path.join(LIWC_NPZ_DIR, SAMPLE_FILE), allow_pickle=True)
person_vectors = raw_liwc_data['person_vectors']
company_vector = raw_liwc_data['company_vector']

euclidean = Euclidean(person_vectors, company_vector, standardize=False).calc_distance()
standardized_euclidean = Euclidean(person_vectors,
                                   company_vector, standardize=True).calc_distance()
mahalanobis = Mahalanobis(person_vectors, company_vector, standardize=False).calc_distance()
standardized_mahalanobis = Mahalanobis(person_vectors,
                                       company_vector, standardize=True).calc_distance()

# File parse testing

HTML_FILE_PATH = './data/sample_html_profiles/1.html'


html_reader = HTMLFileReader(HTML_FILE_PATH)
html_reader.load()
clean_html = html_reader.get_clean_html_text()

li_profile = LinkedInProfileParser(clean_html)

li_profile.parse()

li_profile_dict = li_profile.get_formatted_content()
