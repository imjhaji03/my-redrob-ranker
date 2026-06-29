
import argparse
import csv
import io
import sys
import time
from pathlib import Path

import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.features import extract_all_features, generate_reasoning
from src.honeypot_detector import compute_honeypot_score
from src.utils import load_candidates, print_section


def validate_candidate_count(candidates, top_n, sample_mode=False):
    """Validate dataset size expectations before ranking."""
    total = len(candidates)
    if total == 0:
        raise ValueError("No candidates were loaded from the input file.")
    if not sample_mode and total < top_n:
        raise ValueError(
            f"Full ranking mode requires at least {top_n} candidates; loaded {total}. "
            "Use --sample for small datasets."
        )


def score_candidate(candidate):

    # Extract features
    features = extract_all_features(candidate)

    # Detect honeypots
    honeypot_result = compute_honeypot_score(candidate)

    # Compute final score
    base_score = features["base_score"]
    engagement_mult = features["engagement_multiplier"]
    honeypot_penalty = honeypot_result["honeypot_score"]

    # Final scoring formula
    final_score = base_score * engagement_mult * (1 - honeypot_penalty)

    # Normalize to 0-1 range (base_score max is 100, engagement max is 1.2)
    # Max possible = 100 * 1.2 * 1.0 = 120
    normalized_score = round(min(final_score / 120, 1.0), 4)

    # Generate reasoning
    reasoning = generate_reasoning(candidate, features, honeypot_result)

    return {
        "candidate_id": candidate["candidate_id"],
        "final_score": normalized_score,
        "raw_score": round(final_score, 2),
        "base_score": base_score,
        "features": features,
        "honeypot_result": honeypot_result,
        "reasoning": reasoning,
    }


def rank_candidates(candidates, top_n=100, verbose=False):
    
    total = len(candidates)
    if verbose:
        print(f"\n  Scoring {total} candidates...")

    results = []
    start_time = time.time()

    for i, candidate in enumerate(candidates):
        result = score_candidate(candidate)
        results.append(result)

        if verbose and (i + 1) % 10000 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate
            print(f"    [{i+1:>7d}/{total}] {rate:.0f} candidates/sec | ETA: {eta:.0f}s")

    elapsed = time.time() - start_time
    if verbose:
        print(f"  Scoring complete: {total} candidates in {elapsed:.1f}s ({total/elapsed:.0f}/sec)")

    # Sort by final_score descending, tie-break by candidate_id ascending
    results.sort(key=lambda x: (-x["final_score"], x["candidate_id"]))

    # Take top N
    top_results = results[:top_n]

    # Assign ranks
    for i, result in enumerate(top_results):
        result["rank"] = i + 1

    return top_results


def build_submission_rows(results):
    
    return [
        {
            "candidate_id": result["candidate_id"],
            "rank": result["rank"],
            "score": round(result["final_score"], 4),
            "reasoning": result["reasoning"],
        }
        for result in results
    ]


def write_submission_csv(results, output_path):
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_submission_rows(results)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(submission_columns())

        for row in rows:
            writer.writerow([
                row["candidate_id"],
                row["rank"],
                f"{row['score']:.4f}",
                row["reasoning"],
            ])

    return str(output_path)


def write_submission_xlsx(results, output_path):
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    submission_to_dataframe(results).to_excel(output_path, index=False)
    return str(output_path)


def write_submission(results, output_path):
    
    output_path = Path(output_path)
    suffix = output_path.suffix.lower()

    if suffix == ".csv":
        return write_submission_csv(results, output_path)
    if suffix == ".xlsx":
        return write_submission_xlsx(results, output_path)

    raise ValueError("Output file must end with .csv or .xlsx")


def submission_to_dataframe(results):
    
    rows = build_submission_rows(results)
    return pd.DataFrame(rows, columns=submission_columns())


def submission_columns():
    
    return ["candidate_id", "rank", "score", "reasoning"]


def submission_xlsx_bytes(results):
    
    buffer = io.BytesIO()
    submission_to_dataframe(results).to_excel(buffer, index=False)
    return buffer.getvalue()


def submission_csv_text(results):
    
    rows = build_submission_rows(results)

    text_buffer = io.StringIO()
    writer = csv.writer(text_buffer)
    writer.writerow(submission_columns())
    for row in rows:
        writer.writerow([
            row["candidate_id"],
            row["rank"],
            f"{row['score']:.4f}",
            row["reasoning"],
        ])
    return text_buffer.getvalue()



def print_top_results(results, n=10):
    
    print_section(f"TOP {n} CANDIDATES")

    for result in results[:n]:
        features = result["features"]
        hp = result["honeypot_result"]

        print(f"\n  Rank {result['rank']:>3d} | {result['candidate_id']} | Score: {result['final_score']:.4f}")
        print(f"  {'-'*80}")
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Scores: exp={features['experience_score']:.1f}/30 | "
              f"skill={features['skill_match_score']:.1f}/40 | "
              f"company={features['company_tier_score']:.1f}/20 | "
              f"career={features['career_fit_score']:.1f}/10 | "
              f"base={features['base_score']:.1f}/100")
        print(f"  Multipliers: engagement={features['engagement_multiplier']:.3f} | "
              f"honeypot_penalty={hp['honeypot_score']:.3f} | "
              f"is_honeypot={hp['is_honeypot']}")

        if hp["flags"]:
            print(f"  Flags: {'; '.join(hp['flags'][:2])}")



def print_score_distribution(results):
    
    scores = [r["final_score"] for r in results]

    print(f"\n  Score Distribution (top {len(results)}):")
    print(f"    Max:    {max(scores):.4f}")
    print(f"    Min:    {min(scores):.4f}")
    print(f"    Mean:   {sum(scores)/len(scores):.4f}")
    print(f"    Median: {sorted(scores)[len(scores)//2]:.4f}")

    # Count honeypots in results
    hp_count = sum(1 for r in results if r["honeypot_result"]["is_honeypot"])
    print(f"\n  Honeypots in top {len(results)}: {hp_count} ({hp_count/len(results)*100:.1f}%)")

    # Verify scores are non-increasing
    is_sorted = all(results[i]["final_score"] >= results[i+1]["final_score"]
                     for i in range(len(results)-1))
    print(f"  Scores non-increasing: {'YES' if is_sorted else 'NO -- ERROR!'}")



def main():
    parser = argparse.ArgumentParser(
        description="Redrob Intelligent Candidate Ranker"
    )
    parser.add_argument(
        "--candidates", required=True,
        help="Path to candidates file (JSONL or JSON)"
    )
    parser.add_argument(
        "--out", required=True,
        help="Path for output submission file (.csv or .xlsx)"
    )
    parser.add_argument(
        "--top", type=int, default=100,
        help="Number of top candidates to output (default: 100)"
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="Indicate sample mode (smaller dataset, more verbose output)"
    )

    args = parser.parse_args()

    print_section("REDROB INTELLIGENT CANDIDATE RANKER")
    print(f"\n  Loading candidates from: {args.candidates}")
    candidates = load_candidates(args.candidates)
    print(f"  Loaded {len(candidates)} candidates")
    validate_candidate_count(candidates, args.top, sample_mode=args.sample)

    run_mode = "sample" if args.sample else "full"
    print(f"  Run mode: {run_mode}")
    print(f"  Target output rows: {min(args.top, len(candidates))}")

    run_start = time.time()
    results = rank_candidates(candidates, top_n=args.top, verbose=True)
    total_runtime = time.time() - run_start

    print_top_results(results, n=min(10, len(results)))
    print_score_distribution(results)

    output_path = write_submission(results, args.out)
    print(f"\n  Submission written to: {output_path}")
    print(f"  Total rows: {len(results)} (+ 1 header)")

    print(f"\n  Quick Validation:")
    expected_rows = min(args.top, len(candidates))
    print(f"    Rows: {len(results)} {'(OK)' if len(results) == expected_rows else '(ISSUE)'}")

    ranks = [r["rank"] for r in results]
    print(f"    Ranks unique: {'YES' if len(set(ranks)) == len(ranks) else 'NO'}")
    print(f"    Rank range: {min(ranks)}-{max(ranks)}")

    scores = [r["final_score"] for r in results]
    non_increasing = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    print(f"    Scores non-increasing: {'YES' if non_increasing else 'NO'}")

    hp_in_top = sum(1 for r in results if r["honeypot_result"]["is_honeypot"])
    print(f"    Honeypots in top {len(results)}: {hp_in_top} ({hp_in_top/len(results)*100:.1f}%)")
    print(f"    Total runtime: {total_runtime:.2f}s")
    if total_runtime > 0:
        print(f"    Throughput: {len(candidates)/total_runtime:.0f} candidates/sec")

    if not args.sample and len(results) != args.top:
        raise ValueError(
            f"Full ranking mode must emit exactly {args.top} rows; got {len(results)}."
        )

    print(f"\n  Ranking complete.\n")

    return results


if __name__ == "__main__":
    main()
