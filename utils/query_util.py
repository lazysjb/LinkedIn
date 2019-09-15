
company_q = """
    SELECT * 
    FROM 
        (WITH count_distinct as 
            (SELECT org_profile_link 
             FROM linkedin.person_experience 
             GROUP BY org_profile_link, person_id)
        SELECT org_profile_link, count(org_profile_link) AS count_person 
        FROM count_distinct 
        GROUP BY org_profile_link) q
    WHERE count_person >= 1000
    ORDER BY count_person DESC
"""

