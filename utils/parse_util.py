from abc import ABC, abstractmethod
import logging
import re

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
import lxml
from lxml.html.clean import Cleaner
from pandas.io.json import json_normalize


logger = logging.getLogger(__name__)


def _extract_single_node_from_list(node_list):
    """Check node list contains only one node and extract single node"""
    if len(node_list) != 1:
        raise ValueError('node_list of size {}, expected size 1'.format(len(node_list)))

    return node_list[0]


def _soup_find_single_child_check(node,
                                  tag,
                                  kwargs,
                                  allow_none=True):
    """run find on bs soup node, and ensure only single child exists"""
    child_nodes = node.find_all(tag, kwargs)

    if not len(child_nodes):
        if allow_none:
            return None
        else:
            raise ValueError('Expected child node to be not None')

    return _extract_single_node_from_list(child_nodes)


class HTMLFileReader:

    def __init__(self, file_path):
        """Class to read and preprocess html"""
        self.file_path = file_path
        self.raw_html_text = None

    def load(self):
        with open(self.file_path, 'r') as f:
            self.raw_html_text = f.read()

    def get_raw_html_text(self):
        return self.raw_html_text

    def get_clean_html_text(self, remove_whitespace=True):
        """Remove unnecessary tags, attributes from the html tree"""
        etree = lxml.html.document_fromstring(self.raw_html_text)

        cleaner_args = {
            'javascript': True,
            'style': True,
            'inline_style': True,
            'comments': True,
            'meta': True,
            'page_structure': False,
            'links': False,
            'safe_attrs_only': False,

            # This is a common tag I observed that I think is unnecessary so far
            'kill_tags': ['noscript'],
        }

        cleaner = Cleaner(**cleaner_args)
        etree_clean = cleaner.clean_html(etree)
        html_text_clean = lxml.html.tostring(etree_clean).decode('utf-8')

        # if True, remove consecutive whitespaces right before and after the tag
        if remove_whitespace:
            html_text_clean = re.sub(r'>\s+', '>', html_text_clean)
            html_text_clean = re.sub(r'\s+<', '<', html_text_clean)

        return html_text_clean

    def pretty_print_html_text(self, html_text):
        soup = BeautifulSoup(html_text)
        print(soup.prettify())


class HTMLParser(ABC):

    @abstractmethod
    def parse(self):
        pass

    @abstractmethod
    def get_formatted_content(self):
        pass


class LinkedInProfileParser(HTMLParser):

    def __init__(self, root_html):
        self.root = BeautifulSoup(root_html, 'lxml')

        self.header_section = HeaderSectionParser(
            self._extract_header_section_node())
        self.overview_section = OverviewSectionParser(
            self._extract_overview_section_node())
        self.summary_section = SummarySectionParser(
            self._extract_summary_section_node())
        self.specialty_section = SpecialtySectionParser(
            self._extract_specialty_section_node())
        self.experience_section = ExperienceSectionParser(
            self._extract_experience_section_node())
        self.education_section = EducationSectionParser(
            self._extract_education_section_node())

    def _extract_header_section_node(self):
        header_node = _soup_find_single_child_check(self.root,
                                                    'div',
                                                    {'class': 'profile-header'},
                                                    allow_none=False)
        return header_node

    def _extract_overview_section_node(self):
        overview_node = _soup_find_single_child_check(self.root,
                                                      'dl',
                                                      {'id': 'overview'},
                                                      allow_none=False)
        return overview_node

    def _extract_experience_section_node(self):
        experience_node = _soup_find_single_child_check(self.root,
                                                        'div',
                                                        {'id': 'profile-experience'},
                                                        allow_none=True)
        return experience_node

    def _extract_summary_section_node(self):
        summary_node = _soup_find_single_child_check(self.root,
                                                     'p',
                                                     {'class': 'description summary'},
                                                     allow_none=True)
        return summary_node

    def _extract_specialty_section_node(self):
        specialty_node = _soup_find_single_child_check(self.root,
                                                       'div',
                                                       {'id': 'profile-specialties'},
                                                       allow_none=True)
        if specialty_node is None:
            return None

        # skipping header in html
        specialty_node = specialty_node.contents[1]
        return specialty_node

    def _extract_education_section_node(self):
        education_node = _soup_find_single_child_check(self.root,
                                                       'div',
                                                       {'id': 'profile-education'},
                                                       allow_none=True)
        if education_node is None:
            return None

        return education_node

    def _get_children(self):
        return [
            self.header_section,
            self.overview_section,
            self.summary_section,
            self.specialty_section,
            self.experience_section,
            self.education_section,
        ]

    def parse(self):
        for child in self._get_children():
            child.parse()

    def get_formatted_content(self):
        content = {
            'header': self.header_section.get_formatted_content(),
            'overview': self.overview_section.get_formatted_content(),
            'summary': self.summary_section.get_formatted_content(),
            'specialty': self.specialty_section.get_formatted_content(),
            'experience': self.experience_section.get_formatted_content(),
            'education': self.education_section.get_formatted_content(),
        }
        return content


class HeaderSectionParser(HTMLParser):

    def __init__(self, root):
        self.root = root
        self.name = None
        self.title = None
        self.location = None
        self.industry = None

    def parse_name_info(self):
        given_name = _soup_find_single_child_check(self.root,
                                                   'span',
                                                   {'class': 'given-name'},
                                                   allow_none=False).get_text()
        family_name = _soup_find_single_child_check(self.root,
                                                    'span',
                                                    {'class': 'family-name'},
                                                    allow_none=False).get_text()
        self.name = {
            'given_name': given_name,
            'family_name': family_name,
        }

    def parse_title_info(self):
        title_node = _soup_find_single_child_check(self.root,
                                                   'p',
                                                   {'class': 'headline-title title'},
                                                   allow_none=True)
        if title_node is not None:
            self.title = title_node.get_text()
        return

    def parse_location_info(self):
        location = _soup_find_single_child_check(self.root,
                                                 'span',
                                                 {'class': 'locality'},
                                                 allow_none=False).get_text()
        self.location = location

    def parse_industry_info(self):
        industry = _soup_find_single_child_check(self.root,
                                                 'dd',
                                                 {'class': 'industry'},
                                                 allow_none=False).get_text()
        self.industry = industry

    def parse(self):
        self.parse_name_info()
        self.parse_title_info()
        self.parse_location_info()
        self.parse_industry_info()

    def get_formatted_content(self):
        content = {
            'name': self.name,
            'title': self.title,
            'location': self.location,
            'industry': self.industry,
        }
        return content

    def get_formatted_content_as_df(self):
        content_dict = self.get_formatted_content()
        df = json_normalize(content_dict)
        return df


class OverviewSectionParser(HTMLParser):

    def __init__(self, root):
        self.root = root
        self.current = None
        self.past = None
        self.education = None
        self.connections = None
        self.recommendations = None
        self.websites = None

    def parse_current_info(self):
        """get list of dicts with keys 'role', 'at' """
        curr_exp_node = _soup_find_single_child_check(self.root,
                                                      'dd',
                                                      {'class': 'summary-current'},
                                                      allow_none=True)
        if curr_exp_node is None:
            return

        curr_exp_nodes = curr_exp_node.find_all('li')
        curr_experiences = [self._parse_experience_triplet_node(n) for n in curr_exp_nodes]
        self.current = curr_experiences
        return

    def parse_past_info(self):
        """get list of dicts with keys 'role', 'at' """
        past_exp_node = _soup_find_single_child_check(self.root,
                                                      'dd',
                                                      {'class': 'summary-past'},
                                                      allow_none=True)
        if past_exp_node is None:
            return

        past_exp_nodes = past_exp_node.find_all('li')
        past_experiences = [self._parse_experience_triplet_node(n) for n in past_exp_nodes]
        self.past = past_experiences
        return

    def parse_education_info(self):
        """get list of educations summary"""
        edu_node = _soup_find_single_child_check(self.root,
                                                 'dd',
                                                 {'class': 'summary-education'},
                                                 allow_none=True)
        if edu_node is None:
            return None

        edu_nodes = edu_node.find_all('li')
        education_infos = [n.get_text() for n in edu_nodes]
        self.education = education_infos
        return

    def parse_connections_info(self):
        """get number of connections summary (int)"""
        conn_node = _soup_find_single_child_check(self.root,
                                                  'dd',
                                                  {'class': 'overview-connections'},
                                                  allow_none=False)
        num_connections = conn_node.find('strong').get_text()
        # num_connections is a string since there are cases
        # such as "500+" connections
        # num_connections = int(num_connections)
        self.connections = num_connections

    def parse_recommendations_info(self):
        recommendation_title_node = self.root.find(
            text=re.compile('Recommendations'))

        if recommendation_title_node is None:
            return None

        num_recommendations = recommendation_title_node.find_next().find('strong').get_text()
        num_recommendations = int(num_recommendations)
        self.recommendations = num_recommendations
        return

    def parse_websites_info(self):
        website_node = _soup_find_single_child_check(self.root,
                                                     'dd',
                                                     {'class': 'websites'},
                                                     allow_none=True)
        if website_node is None:
            return None

        website_nodes = website_node.find_all('li')
        website_infos = [n.get_text() for n in website_nodes]
        self.websites = website_infos
        return

    def _parse_experience_triplet_node(self, experience_triplet_node):
        """In the form of xxx role at yyy"""
        experience_children = list(experience_triplet_node.children)

        if len(experience_children) != 3:
            raise ValueError('Length of experience_children is {}, expected 3'.format(
                len(experience_children)))

        role = experience_children[0]
        if not isinstance(role, NavigableString):
            raise TypeError('Type of role is unexpected')
        role = role.string

        assert experience_children[1].get_text() == 'at'

        at = experience_children[2]
        if isinstance(at, Tag):
            at = at.get_text()
        elif isinstance(at, NavigableString):
            at = at.string
        else:
            raise TypeError('Type of at is unexpected')

        return {'role': role, 'at': at}

    def parse(self):
        self.parse_current_info()
        self.parse_past_info()
        self.parse_education_info()
        self.parse_connections_info()
        self.parse_recommendations_info()
        self.parse_websites_info()

    def get_formatted_content(self):
        content = {
            'current': self.current,
            'past': self.past,
            'education': self.education,
            'connections': self.connections,
            'recommendations': self.recommendations,
            'websites': self.websites,
        }
        return content


class SummarySectionParser(HTMLParser):
    def __init__(self, root):
        self.root = root
        self.text = None

    def parse(self):
        if self.root is None:
            return
        self.text = self.root.get_text()

    def get_formatted_content(self):
        return self.text


class SpecialtySectionParser(HTMLParser):
    def __init__(self, root):
        self.root = root
        self.text = None

    def parse(self):
        if self.root is None:
            return
        self.text = self.root.get_text()

    def get_formatted_content(self):
        return self.text


class ExperienceSectionParser(HTMLParser):
    def __init__(self, root):
        self.root = root
        self.experience_items = [ExperienceItemParser(
            n) for n in self._extract_experience_item_nodes()]

    def _extract_experience_item_nodes(self):
        if self.root is None:
            return []

        experience_item_nodes = self.root.find_all(
            'div', {'class': re.compile('vevent vcard summary')})
        return experience_item_nodes

    def parse(self):
        for item in self.experience_items:
            item.parse()

    def get_formatted_content(self):
        return [i.get_formatted_content() for i in self.experience_items]

    def get_formatted_content_as_df(self):
        content_list = self.get_formatted_content()
        df = json_normalize(content_list)
        return df


class ExperienceItemParser(HTMLParser):
    def __init__(self, root):
        self.root = root
        self.title = None
        self.org_summary = None
        self.org_detail = None
        self.period = None
        self.location = None
        self.description = None

    def parse_title_info(self):
        title_node = _soup_find_single_child_check(self.root,
                                                   'span',
                                                   {'class': 'title'},
                                                   allow_none=False)
        self.title = title_node.get_text()

    def parse_org_summary_info(self):
        org_summary_node = _soup_find_single_child_check(self.root,
                                                         'span',
                                                         {'class': 'org summary'},
                                                         allow_none=False)
        self.org_summary = org_summary_node.get_text()

    def parse_org_detail_info(self):
        org_detail_node = _soup_find_single_child_check(self.root,
                                                        'p',
                                                        {'class':
                                                            re.compile('organization-details')},
                                                        allow_none=True)
        if org_detail_node is None:
            return

        self.org_detail = org_detail_node.get_text()

    def parse_period_info(self):
        # TODO (SJ): Can potentially get more 'accurate' 'YYYY-MM-DD' dates
        #   is it worth it? leave for now
        period_node = _soup_find_single_child_check(self.root,
                                                    'p',
                                                    {'class': 'period'},
                                                    allow_none=True)

        date_nodes = period_node.find_all('abbr')

        if len(date_nodes):
            # sanity check
            date_nodes[0].get_attribute_list('class')[0] == 'dtstart'
            date_nodes[1].get_attribute_list('class')[0] == 'dtend'

            date_start, date_end = [x.get_text() for x in date_nodes]
            duration = period_node.find('span', {'class': 'duration'}).get_text()
            period = {
                'date_start': date_start,
                'date_end': date_end,
                'duration': duration,
                'text': None,
            }
        # below is to handle period such as "Currently holds this position"
        else:

            period = {
                'date_start': None,
                'date_end': None,
                'duration': None,
                'text': period_node.get_text(),
            }

        self.period = period

    def parse_location_info(self):
        loc_node = _soup_find_single_child_check(self.root,
                                                 'span',
                                                 {'class': 'location'},
                                                 allow_none=True)
        if loc_node is None:
            return
        self.location = loc_node.get_text()

    def parse_description_info(self):
        # TODO (SJ): perhaps remove non-ascii symbols from this string
        description_node = _soup_find_single_child_check(self.root,
                                                         'p',
                                                         {'class': re.compile('description')},
                                                         allow_none=True)
        if description_node is None:
            return
        self.description = description_node.get_text('\n')

    def parse(self):
        self.parse_title_info()
        self.parse_org_summary_info()
        self.parse_org_detail_info()
        self.parse_period_info()
        self.parse_location_info()
        self.parse_description_info()

    def get_formatted_content(self):
        content = {
            'title': self.title,
            'org_summary': self.org_summary,
            'org_detail': self.org_detail,
            'period': self.period,
            'location': self.location,
            'description': self.description,
        }
        return content


class EducationSectionParser(HTMLParser):
    def __init__(self, root):
        self.root = root
        self.education_items = [EducationItemParser(
            n) for n in self._extract_education_item_nodes()]

    def _extract_education_item_nodes(self):
        if self.root is None:
            return []

        education_item_nodes = self.root.find_all(
            'div', {'class': re.compile('vevent vcard')})
        return education_item_nodes

    def parse(self):
        for item in self.education_items:
            item.parse()

    def get_formatted_content(self):
        return [i.get_formatted_content() for i in self.education_items]

    def get_formatted_content_as_df(self):
        content_list = self.get_formatted_content()
        df = json_normalize(content_list)
        return df


class EducationItemParser(HTMLParser):
    def __init__(self, root):
        self.root = root
        self.org_name = None
        self.degree = None
        self.major = None
        self.period = None
        self.education_detail = None

    def parse_org_name_info(self):
        org_name_node = _soup_find_single_child_check(self.root,
                                                      None,
                                                      {'class': 'summary fn org'},
                                                      allow_none=False)
        self.org_name = org_name_node.get_text()

    def parse_degree_info(self):
        degree_node = _soup_find_single_child_check(self.root,
                                                    'span',
                                                    {'class': 'degree'},
                                                    allow_none=True)
        if degree_node is None:
            return
        self.degree = degree_node.get_text()

    def parse_major_info(self):
        major_node = _soup_find_single_child_check(self.root,
                                                   'span',
                                                   {'class': 'major'},
                                                   allow_none=True)
        if major_node is None:
            return
        self.major = major_node.get_text()

    def parse_period_info(self):
        # TODO (SJ): Can potentially get more 'accurate' 'YYYY-MM-DD' dates
        #   is it worth it? leave for now
        period_node = _soup_find_single_child_check(self.root,
                                                    'p',
                                                    {'class': 'period'},
                                                    allow_none=True)
        if period_node is None:
            self.period = {
                'date_start': None,
                'date_end': None,
            }
            return

        date_nodes = period_node.find_all('abbr')
        date_node_attrs = [n.get_attribute_list('class')[0] for n in date_nodes]

        if 'dtstart' not in date_node_attrs:
            date_start = None
        else:
            date_start = date_nodes[date_node_attrs.index('dtstart')].get_text()

        if 'dtend' not in date_node_attrs:
            date_end = None
        else:
            date_end = date_nodes[date_node_attrs.index('dtend')].get_text()

        period = {
            'date_start': date_start,
            'date_end': date_end,
        }
        self.period = period

    def parse_education_detail_info(self):
        # TODO(SJ): Add detail activity attribute to accomodate 15.html
        education_detail_node = _soup_find_single_child_check(self.root,
                                                              'p',
                                                              {'class': 'desc details-education',
                                                               'name': None},
                                                              allow_none=False)
        self.education_detail = education_detail_node.get_text('\n')

    def parse(self):
        self.parse_org_name_info()
        self.parse_degree_info()
        self.parse_major_info()
        self.parse_period_info()
        self.parse_education_detail_info()

    def get_formatted_content(self):
        content = {
            'org_name': self.org_name,
            'degree': self.degree,
            'major': self.major,
            'period': self.period,
            'education_detail': self.education_detail
        }
        return content
