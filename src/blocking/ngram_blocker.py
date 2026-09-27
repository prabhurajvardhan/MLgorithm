def prepare(con, n=3):
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS name_char_index AS
        SELECT DISTINCT
            entity_id,
            substr(
                regexp_replace(
                    lower(coalesce(business_name, '')),
                    '[^a-z0-9]',
                    '',
                    'g'
                ),
                pos,
                {n}
            ) AS gram
        FROM businesses,
        LATERAL range(
            1,
            greatest(
                length(
                    regexp_replace(
                        lower(coalesce(business_name, '')),
                        '[^a-z0-9]',
                        '',
                        'g'
                    )
                ) - {n} + 2,
                1
            )
        ) r(pos)
        WHERE length(
            regexp_replace(
                lower(coalesce(business_name, '')),
                '[^a-z0-9]',
                '',
                'g'
            )
        ) >= {n}
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS char_df AS
        SELECT gram, COUNT(DISTINCT entity_id) AS df
        FROM name_char_index
        GROUP BY gram
    """)

    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_char_index
        ON name_char_index(gram)
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS ngram_candidates(
            source1_entity_id VARCHAR,
            candidate_entity_id VARCHAR
        )
    """)


def run_batch(con, start_row, end_row):
    con.execute("""
        CREATE OR REPLACE TEMP TABLE s1_grams AS
        SELECT DISTINCT
            s.entity_id AS source1_entity_id,
            substr(
                regexp_replace(
                    lower(coalesce(s.business_name, '')),
                    '[^a-z0-9]',
                    '',
                    'g'
                ),
                r.pos,
                3
            ) AS gram
        FROM s1_work s,
        LATERAL range(
            1,
            greatest(
                length(
                    regexp_replace(
                        lower(coalesce(s.business_name, '')),
                        '[^a-z0-9]',
                        '',
                        'g'
                    )
                ) - 3 + 2,
                1
            )
        ) r(pos)
        WHERE s.row_id > ? AND s.row_id <= ?
    """, [start_row, end_row])

    con.execute("""
        INSERT INTO ngram_candidates
        SELECT
            g.source1_entity_id,
            n.entity_id
        FROM s1_grams g
        JOIN char_df d
          ON d.gram = g.gram
         AND d.df <= 50000
        JOIN name_char_index n
          ON n.gram = g.gram
        GROUP BY
            g.source1_entity_id,
            n.entity_id
        HAVING COUNT(DISTINCT g.gram) >= 2
    """)
