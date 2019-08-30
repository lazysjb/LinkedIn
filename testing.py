from utils.parse_util import HTMLFileReader, LinkedInProfileParser
# from pandas.io.json import json_normalize
# import json
# import pandas as pd
# import flatten_json

HTML_FILE_PATH = './data/sample_html_profiles/16.html'


html_reader = HTMLFileReader(HTML_FILE_PATH)
html_reader.load()
clean_html = html_reader.get_clean_html_text()

li_profile = LinkedInProfileParser(clean_html)

li_profile.parse()

li_profile_dict = li_profile.get_formatted_content()
