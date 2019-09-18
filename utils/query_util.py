from utils.db_util import make_query


def query_all_parent_folders(conn):
    q = """
        SELECT DISTINCT parent_folder
        FROM
            linkedin.person_meta
    """

    df = make_query(q, conn)
    return df


def query_person_summary_in_parent_folder(conn,
                                          parent_folder):
    q = """
        SELECT meta.person_id, meta.parent_folder, person_summary.person_summary
        FROM
            (SELECT *
             FROM
                linkedin.person_meta
             WHERE
                parent_folder = '{parent_folder}') meta
        JOIN
            linkedin.person_summary
            ON
                person_summary.person_id = meta.person_id
    """.format(parent_folder=parent_folder)

    df = make_query(q, conn)
    return df


def query_person_in_org(conn,
                        org_profile_links):

    formatted_org_profile_links = '(' + ','.join(["'{}'".format(t) for t in org_profile_links]) + ')'

    q = """
        SELECT *
        FROM
            linkedin.person_experience
        WHERE
            org_profile_link IN {profile_links}
        """.format(profile_links=formatted_org_profile_links)

    df = make_query(q, conn)
    return df


def query_organization_stats(conn,
                             org_profile_links=None,
                             min_word_length=None,
                             min_person_count_per_org=1000):

    if org_profile_links is None:
        where_in_selected_org_links_clause = ''
    else:
        formatted_org_profile_links = '(' + ','.join(["'{}'".format(
            t) for t in org_profile_links]) + ')'
        where_in_selected_org_links_clause = """
            WHERE
                org_profile_link IN {}
        """.format(formatted_org_profile_links)

    if min_word_length is None:
        where_min_word_length_clause = ''
    else:
        where_min_word_length_clause = """
            WHERE
                word_length >= {}
        """.format(min_word_length)

    q = """
        SELECT
            org_profile_link,
            COUNT(org_profile_link) AS count_person,
            AVG(word_length) AS avg_word_length,
            percentile_disc(0.5) within GROUP (ORDER BY word_length) as median_word_length
        FROM

            (SELECT org_profile_link, person_id
            FROM
                linkedin.person_experience
            
            {where_in_selected_org_links_clause}
            
            GROUP BY
                org_profile_link, person_id) filtered_experience

        JOIN
            (SELECT meta.person_id, word_length, char_length
            FROM
                linkedin.person_meta meta
            JOIN (
                SELECT *
                FROM linkedin.location_country
                WHERE country IN ('US', 'Canada')
            ) q
                ON meta.header_location = q.header_location
            JOIN linkedin.person_summary_length
                ON person_summary_length.person_id = meta.person_id
                ) us_canada_person_with_summary

            ON
                us_canada_person_with_summary.person_id = filtered_experience.person_id
            {where_min_word_length_clause}

        GROUP BY
            org_profile_link
            
        HAVING
            COUNT(org_profile_link) >= {min_person_count_per_org}
            
        ORDER BY
            count_person DESC

        """.format(where_in_selected_org_links_clause=where_in_selected_org_links_clause,
                   where_min_word_length_clause=where_min_word_length_clause,
                   min_person_count_per_org=min_person_count_per_org)

    df = make_query(q, conn)
    return df

#
# """
# SELECT *
# FROM
# 	(WITH count_distinct as
# 		(SELECT org_profile_link
# 		 FROM
# 		 	(SELECT person_experience.person_id, org_profile_link
# 			FROM linkedin.person_experience
# 			JOIN
# 				(SELECT person_id
# 				FROM linkedin.person_meta meta
# 				JOIN (
# 					SELECT *
# 					FROM linkedin.location_country
# 					WHERE country IN ('US', 'Canada')
# 				) q
# 				ON
# 					meta.header_location = q.header_location) us_canada_person
#
# 				ON us_canada_person.person_id = person_experience.person_id) qq
#
# 		 GROUP BY org_profile_link, person_id)
# 	SELECT org_profile_link, count(org_profile_link) AS count_person
# 	FROM count_distinct
# 	GROUP BY org_profile_link) q
# WHERE count_person >= 1000
# ORDER BY count_person DESC
# """
