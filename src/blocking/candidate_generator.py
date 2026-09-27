import argparse
import os
import tempfile
from pathlib import Path

import duckdb

from . import token_blocker
from . import normalized_blocker
from . import abbreviation_blocker
from . import ngram_blocker


def _load(con, path, table):
    con.execute(f"DROP TABLE IF EXISTS {table}")

    con.execute(f"""
        CREATE TABLE {table} AS
        SELECT
            entity_id,
            business_name,
            business_address,
            country
        FROM read_csv(
            ?,
            delim='\\t',
            header=true,
            nullstr=''
        )
    """, [str(Path(path).resolve())])


def _build_indexes(con):
    con.execute("""
        CREATE OR REPLACE TABLE businesses AS
        SELECT entity_id, business_name FROM source2
        UNION ALL
        SELECT entity_id, business_name FROM source3
    """)

    con.execute("""
        CREATE OR REPLACE TABLE name_tokens AS
        SELECT DISTINCT
            entity_id,
            unnest(
                regexp_extract_all(
                    lower(coalesce(business_name, '')),
                    '[a-z0-9]+'
                )
            ) AS token
        FROM businesses
    """)

    token_blocker.prepare(con)
    normalized_blocker.prepare(con)
    abbreviation_blocker.prepare(con)
    ngram_blocker.prepare(con)


def _prepare_s1(con):
    con.execute("DROP TABLE IF EXISTS s1_work")

    con.execute("""
        CREATE TABLE s1_work AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY entity_id) AS row_id,
            *
        FROM source1
    """)


def _run_batches(con, batch_size):
    total = con.execute(
        "SELECT COUNT(*) FROM s1_work"
    ).fetchone()[0]

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)

        token_blocker.run_batch(con, start, end)
        normalized_blocker.run_batch(con, start, end)
        abbreviation_blocker.run_batch(con, start, end)
        ngram_blocker.run_batch(con, start, end)

        print(f"Processed {end:,}/{total:,} S1 records")


def _write_output(con, output):
    con.execute("""
        CREATE OR REPLACE TABLE candidate_pairs AS
        SELECT DISTINCT
            source1_entity_id,
            candidate_entity_id
        FROM (
            SELECT * FROM token_candidates
            UNION ALL
            SELECT * FROM normalized_candidates
            UNION ALL
            SELECT * FROM abbreviation_candidates
            UNION ALL
            SELECT * FROM ngram_candidates
        )
        WHERE candidate_entity_id LIKE 'S2-%'
           OR candidate_entity_id LIKE 'S3-%'
    """)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    con.execute("""
        COPY candidate_pairs
        TO ?
        WITH (HEADER, DELIMITER '\\t')
    """, [str(Path(output).resolve())])

    count = con.execute(
        "SELECT COUNT(*) FROM candidate_pairs"
    ).fetchone()[0]

    print(f"Candidate pairs: {count:,}")
    print(f"Output: {output}")


def generate_candidates(
    source1,
    source2,
    source3,
    output,
    batch_size=5000,
    work_dir=None
):
    if work_dir is None:
        work_dir = tempfile.mkdtemp(
            prefix="business_entity_blocking_"
        )

    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = work_dir / "duckdb_tmp"
    tmp_dir.mkdir(exist_ok=True)

    con = duckdb.connect(
        str(work_dir / "blocking.duckdb")
    )

    try:
        con.execute("SET memory_limit='3GB'")
        con.execute("SET threads=2")
        con.execute(
            f"SET temp_directory='{tmp_dir.resolve()}'"
        )
        con.execute(
            "SET preserve_insertion_order=false"
        )

        print("Loading normalized datasets...")
        _load(con, source1, "source1")
        _load(con, source2, "source2")
        _load(con, source3, "source3")

        print("Building indexes...")
        _build_indexes(con)

        _prepare_s1(con)

        _run_batches(con, batch_size)

        _write_output(con, output)

    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--source1", required=True)
    parser.add_argument("--source2", required=True)
    parser.add_argument("--source3", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--work-dir", default=None)

    args = parser.parse_args()

    generate_candidates(
        args.source1,
        args.source2,
        args.source3,
        args.output,
        args.batch_size,
        args.work_dir
    )


if __name__ == "__main__":
    main()
