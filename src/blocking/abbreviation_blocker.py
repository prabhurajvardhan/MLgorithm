
from .normalizer import normalized_initials


def prepare(con):
    con.execute("""
        CREATE OR REPLACE TABLE abbreviation_index AS
        SELECT
            entity_id,
            business_name
        FROM businesses
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_abbrev_entity
        ON abbreviation_index(entity_id)
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS abbreviation_candidates(
            source1_entity_id VARCHAR,
            candidate_entity_id VARCHAR
        )
    """)


def run_batch(con, start_row, end_row):
    """
    Abbreviation/initial blocking.

    The SQL path uses meaningful-token initials while ignoring
    common legal suffixes.
    """

    con.execute("""
        INSERT INTO abbreviation_candidates

        SELECT DISTINCT
            s.entity_id,
            a.entity_id

        FROM s1_work s

        JOIN abbreviation_index a

          ON array_to_string(
                list_transform(
                    list_filter(
                        regexp_extract_all(
                            lower(coalesce(s.business_name, '')),
                            '[a-z0-9]+'
                        ),
                        x -> x NOT IN (
                            'the','and','of','for',
                            'inc','llc','ltd','limited',
                            'company','co','corp',
                            'corporation','plc','pvt',
                            'private','com','net','org'
                        )
                    ),
                    x -> substr(x, 1, 1)
                ),
                ''
             )

             =

             array_to_string(
                list_transform(
                    list_filter(
                        regexp_extract_all(
                            lower(coalesce(a.business_name, '')),
                            '[a-z0-9]+'
                        ),
                        x -> x NOT IN (
                            'the','and','of','for',
                            'inc','llc','ltd','limited',
                            'company','co','corp',
                            'corporation','plc','pvt',
                            'private','com','net','org'
                        )
                    ),
                    x -> substr(x, 1, 1)
                ),
                ''
             )

        WHERE s.row_id > ?
          AND s.row_id <= ?

          AND length(
              array_to_string(
                  list_transform(
                      list_filter(
                          regexp_extract_all(
                              lower(coalesce(s.business_name, '')),
                              '[a-z0-9]+'
                          ),
                          x -> x NOT IN (
                              'the','and','of','for',
                              'inc','llc','ltd','limited',
                              'company','co','corp',
                              'corporation','plc','pvt',
                              'private','com','net','org'
                          )
                      ),
                      x -> substr(x, 1, 1)
                  ),
                  ''
              )
          ) >= 3
    """, [start_row, end_row])
