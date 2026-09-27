def prepare(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS token_df AS
        SELECT token, COUNT(DISTINCT entity_id) AS df
        FROM name_tokens
        GROUP BY token
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_token_df
        ON token_df(token)
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_name_tokens
        ON name_tokens(token)
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS token_candidates(
            source1_entity_id VARCHAR,
            candidate_entity_id VARCHAR
        )
    """)


def run_batch(con, start_row, end_row):
    con.execute("""
        INSERT INTO token_candidates
        SELECT DISTINCT
            q.source1_entity_id,
            n.entity_id
        FROM (
            SELECT
                s.entity_id AS source1_entity_id,
                t.token
            FROM s1_work s
            CROSS JOIN LATERAL unnest(
                regexp_extract_all(
                    lower(coalesce(s.business_name, '')),
                    '[a-z0-9]+'
                )
            ) AS t(token)
            JOIN token_df d ON d.token = t.token
            WHERE s.row_id > ? AND s.row_id <= ?
              AND length(t.token) >= 2
              AND t.token NOT IN (
                  'the','and','of','for','inc','llc','ltd',
                  'limited','company','co','corp','corporation',
                  'com','net','org'
              )
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY s.entity_id
                ORDER BY d.df ASC
            ) <= 3
        ) q
        JOIN name_tokens n
          ON n.token = q.token
    """, [start_row, end_row])
