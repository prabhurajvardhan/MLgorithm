def prepare(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS normalized_name_index AS
        SELECT
            entity_id,
            regexp_replace(
                lower(coalesce(business_name, '')),
                '[^a-z0-9]',
                '',
                'g'
            ) AS normalized_name
        FROM businesses
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_normalized_name
        ON normalized_name_index(normalized_name)
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS normalized_candidates(
            source1_entity_id VARCHAR,
            candidate_entity_id VARCHAR
        )
    """)


def run_batch(con, start_row, end_row):
    con.execute("""
        INSERT INTO normalized_candidates
        SELECT DISTINCT
            s.entity_id,
            n.entity_id
        FROM s1_work s
        JOIN normalized_name_index n
          ON n.normalized_name =
             regexp_replace(
                 lower(coalesce(s.business_name, '')),
                 '[^a-z0-9]',
                 '',
                 'g'
             )
        WHERE s.row_id > ? AND s.row_id <= ?
          AND length(n.normalized_name) >= 3
    """, [start_row, end_row])
