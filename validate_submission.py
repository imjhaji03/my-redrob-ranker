#!/usr/bin/env python3

import csv
import re
import sys
from pathlib import Path

import pandas as pd

REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
CANDIDATE_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")
DATA_ROW_START = 2
EXPECTED_DATA_ROWS = 100


def load_submission_rows(path):
    suffix = path.suffix.lower()

    if suffix == ".csv":
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return None, None, ["Row 1 must be the header row; file is empty."]

            data_rows = [row for row in reader if any(cell.strip() for cell in row)]
            return header, data_rows, []

    if suffix == ".xlsx":
        df = pd.read_excel(path, dtype={"candidate_id": str})
        header = list(df.columns)
        df = df.where(pd.notnull(df), "")
        data_rows = [[str(row[col]).strip() for col in header] for _, row in df.iterrows()]
        data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
        return header, data_rows, []

    return None, None, ["Filename must use a .csv or .xlsx extension."]


def validate_submission(submission_path):
    errors = []
    path = Path(submission_path)

    if path.suffix.lower() not in {".csv", ".xlsx"}:
        errors.append("Filename must use a .csv or .xlsx extension.")
    elif not path.stem:
        errors.append("Filename must be your registered participant ID (e.g. team_xxx.csv or team_xxx.xlsx).")

    try:
        header, data_rows, load_errors = load_submission_rows(path)
        errors.extend(load_errors)
        if load_errors:
            return errors
    except UnicodeDecodeError:
        errors.append("CSV files must be UTF-8 encoded.")
        return errors
    except OSError as e:
        errors.append(f"Cannot read file: {e}")
        return errors
    except Exception as e:
        errors.append(f"Cannot parse submission file: {e}")
        return errors

    if header != REQUIRED_HEADER:
        errors.append(
            "Row 1 (header) must be exactly:\n"
            f"  {','.join(REQUIRED_HEADER)}\n"
            f"Found:\n"
            f"  {','.join(header)}"
        )

    n = len(data_rows)
    if n != EXPECTED_DATA_ROWS:
        errors.append(
            f"After the header (row 1), there must be exactly {EXPECTED_DATA_ROWS} "
            f"data rows (rows {DATA_ROW_START}–{DATA_ROW_START + EXPECTED_DATA_ROWS - 1}); "
            f"found {n}."
        )

    seen_ids = set()
    seen_ranks = set()
    by_rank = []

    for i, cells in enumerate(data_rows):
        row_num = DATA_ROW_START + i

        if len(cells) != len(REQUIRED_HEADER):
            errors.append(
                f"Row {row_num}: expected {len(REQUIRED_HEADER)} columns "
                f"({','.join(REQUIRED_HEADER)}), got {len(cells)}."
            )
            continue

        row = dict(zip(REQUIRED_HEADER, cells))
        cid = row["candidate_id"].strip()
        rank_s = row["rank"].strip()
        score_s = row["score"].strip()

        if not cid:
            errors.append(f"Row {row_num}: candidate_id is required.")
        elif not CANDIDATE_ID_PATTERN.match(cid):
            errors.append(
                f"Row {row_num}: candidate_id must be CAND_XXXXXXX (7 digits)."
            )
        elif cid in seen_ids:
            errors.append(f"Row {row_num}: duplicate candidate_id '{cid}'.")
        else:
            seen_ids.add(cid)

        try:
            rank = int(rank_s)
            if str(rank) != rank_s:
                raise ValueError
            if not 1 <= rank <= 100:
                errors.append(f"Row {row_num}: rank must be between 1 and 100.")
            elif rank in seen_ranks:
                errors.append(f"Row {row_num}: duplicate rank {rank}.")
            else:
                seen_ranks.add(rank)
        except ValueError:
            errors.append(f"Row {row_num}: rank must be an integer (1–100).")
            rank = None

        try:
            score = float(score_s)
        except ValueError:
            errors.append(f"Row {row_num}: score must be a float.")
            score = None

        if rank is not None and score is not None and cid:
            by_rank.append((rank, score, cid))

    missing = set(range(1, 101)) - seen_ranks
    if missing:
        errors.append(
            f"Each rank 1–100 must appear exactly once; missing: {sorted(missing)}"
        )

    by_rank.sort(key=lambda x: x[0])

    for i in range(len(by_rank) - 1):
        r1, s1, _ = by_rank[i]
        r2, s2, _ = by_rank[i + 1]
        if s1 < s2:
            errors.append(
                f"score must be non-increasing by rank: "
                f"rank {r1} ({s1}) < rank {r2} ({s2})."
            )

    for i in range(len(by_rank) - 1):
        r1, s1, c1 = by_rank[i]
        r2, s2, c2 = by_rank[i + 1]
        if s1 == s2 and c1 > c2:
            errors.append(
                f"Equal scores at ranks {r1} and {r2}: "
                f"tie-break requires candidate_id ascending "
                f"({c1!r} > {c2!r})."
            )

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_submission.py <participant_id>.csv|.xlsx")
        sys.exit(1)

    errors = validate_submission(sys.argv[1])
    if errors:
        print(f"Validation failed ({len(errors)} issue(s)):\n")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)

    print("Submission is valid.")


if __name__ == "__main__":
    main()
