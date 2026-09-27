
from .normalizer import normalize_name


def prepare(con):
    con.execute("""
        CREATE OR REPLACE TABLE normalized_name_index AS
        SELECT
            entity_id,
            business_name
        FROM businesses
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_normalized_entity
        ON normalized_name_index(entity_id)
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS normalized_candidates(
            source1_entity_id VARCHAR,
            candidate_entity_id VARCHAR
        )
    """)


def run_batch(con, start_row, end_row):
    """
    Normalized-name blocking.

    Uses DuckDB normalization-compatible SQL for the common
    normalization path. Python-level normalization is also
    exposed through normalizer.py for feature generation.
    """

    con.execute("""
        INSERT INTO normalized_candidates

        SELECT DISTINCT
            s.entity_id,
            n.entity_id

        FROM s1_work s

        JOIN normalized_name_index n
          ON regexp_replace(
                 lower(coalesce(s.business_name, '')),
                 '[^a-z0-9]',
                 '',
                 'g'
             )
             =
             regexp_replace(
                 lower(coalesce(n.business_name, '')),
                 '[^a-z0-9]',
                 '',
                 'g'
             )

        WHERE s.row_id > ?
          AND s.row_id <= ?

          AND length(
              regexp_replace(
                  lower(coalesce(s.business_name, '')),
                  '[^a-z0-9]',
                  '',
                  'g'
              )
          ) >= 3
    """, [start_row, end_row])
