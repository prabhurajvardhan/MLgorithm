def prepare(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS abbreviation_index AS
        SELECT DISTINCT
            entity_id,

            regexp_replace(
                lower(coalesce(business_name, '')),
                '[^a-z0-9]',
                '',
                'g'
            ) AS compact_name,

            array_to_string(
                list_transform(
                    list_filter(
                        regexp_extract_all(
                            lower(coalesce(business_name, '')),
                            '[a-z0-9]+'
                        ),
                        x -> x NOT IN (
                            'the','and','of','for','inc','llc',
                            'ltd','limited','company','co','corp',
                            'corporation','com','net','org'
                        )
                    ),
                    x -> substr(x, 1, 1)
                ),
                ''
            ) AS initials
        FROM businesses
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_abbrev_initials
        ON abbreviation_index(initials)
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_abbrev_compact
        ON abbreviation_index(compact_name)
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS abbreviation_candidates(
            source1_entity_id VARCHAR,
            candidate_entity_id VARCHAR
        )
    """)


def run_batch(con, start_row, end_row):
    con.execute("""
        INSERT INTO abbreviation_candidates
        SELECT DISTINCT
            s.entity_id,
            a.entity_id
        FROM s1_work s
        JOIN abbreviation_index a
          ON a.initials =
             array_to_string(
                 list_transform(
                     list_filter(
                         regexp_extract_all(
                             lower(coalesce(s.business_name, '')),
                             '[a-z0-9]+'
                         ),
                         x -> x NOT IN (
                             'the','and','of','for','inc','llc',
                             'ltd','limited','company','co','corp',
                             'corporation','com','net','org'
                         )
                     ),
                     x -> substr(x, 1, 1)
                 ),
                 ''
             )
        WHERE s.row_id > ? AND s.row_id <= ?
          AND length(a.initials) >= 3
    """, [start_row, end_row])
