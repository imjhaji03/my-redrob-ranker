# Redrob Intelligent Candidate Ranking System

## Overview
This project ranks 100,000 candidate profiles to identify the top 100 best-fit candidates for a Senior AI Engineer role in the India Runs Data & AI Challenge. The solution uses a deterministic, rule-based ranking pipeline that combines feature engineering, behavioral-signal weighting, and honeypot detection to produce a submission-ready XLSX file under the challenge runtime constraints.

The approach is designed for fast CPU-only execution, reproducible outputs, and strong resistance to keyword-stuffed or logically inconsistent candidate profiles.

## How It Works
1. Load candidates from JSONL or JSON.
2. Extract ranking features for each candidate:
   - experience fit
   - skill match to the JD
   - company/product-fit tier
   - career narrative fit
   - engagement multiplier from Redrob behavioral signals
3. Compute honeypot / trap risk using multiple rule-based detectors.
4. Apply the scoring formula:

```text
base_score = experience_score + skill_match_score + company_tier_score + career_fit_score
final_score = base_score * engagement_multiplier * (1 - honeypot_penalty)
```

5. Sort by final score descending, with `candidate_id` ascending as the tie-break.
6. Output the top 100 rows in valid submission XLSX format.

## Repository Structure
```text
my-redrob-ranker/
├── app.py
├── README.md
├── requirements.txt
├── submission_metadata.yaml
├── submission_metadata_template.yaml
├── validate_submission.py
├── data/
│   └── sample_candidates.json
├── output/
│   └── submission.xlsx
└── src/
    ├── __init__.py
    ├── features.py
    ├── honeypot_detector.py
    ├── ranker.py
    └── utils.py
```

## Core Modules
### `src/ranker.py`
Main entry point for loading candidates, scoring, ranking, and writing XLSX output.

### `src/features.py`
Implements:
- experience scoring
- JD skill matching
- company tier scoring
- career-fit scoring
- engagement multiplier
- submission reasoning generation

### `src/honeypot_detector.py`
Implements multi-layer trap detection for:
- logical impossibilities
- title/skill mismatch
- career narrative inconsistency
- engagement red flags
- services-only backgrounds
- research-only backgrounds
- keyword stuffing

### `validate_submission.py`
Validates submission format and ranking constraints required by the challenge.

## Quick Start
### Prerequisites
- Python 3.10+
- CPU-only environment
- No network access required during ranking

### Install
```bash
pip install -r requirements.txt
```

### Run on sample candidates
```bash
python src/ranker.py --candidates ./data/sample_candidates.json --out ./output/submission.xlsx --sample
```

### Run on full dataset
Place `candidates.jsonl` in the project root or update the path accordingly, then run:

```bash
python src/ranker.py --candidates ./candidates.jsonl --out ./output/submission.xlsx
```


### One-click Windows run
For a single-command Windows workflow, use:

```bat
run_project.bat
```

This BAT file:
- installs dependencies
- finds `candidates.jsonl`
- runs the full ranker
- validates the generated XLSX submission
- creates the final submission output as an XLSX file
- removes common cache/temp artifacts afterward

### Validate output
```bash
python validate_submission.py ./output/submission.xlsx
```


## Design Decisions
### Why rule-based instead of a trained model?
- deterministic and reproducible
- fast enough for 100K candidates on CPU
- transparent scoring and easier reasoning generation
- easier to harden against explicit challenge traps

### Why behavioral signals matter
A high-skill but inactive candidate is less valuable than a slightly weaker but highly engaged one. The engagement multiplier incorporates response rate, recency, open-to-work status, applications, interview completion, and related recruiter-facing signals.

### Why honeypot detection matters
The challenge explicitly penalizes rankings containing too many honeypot profiles. This implementation aggressively down-ranks candidates with inconsistent skill histories, title/skill mismatches, suspicious narrative gaps, and stuffed AI buzzwords without evidence.

## Performance
Measured local full-run performance:
- candidates processed: 100,000
- runtime: ~38 seconds
- throughput: ~2,600+ candidates/second
- top-100 honeypot rate: 0.0% in the current validated run

## Validation Status
Current pipeline status:
- full submission XLSX validates successfully
- 100 rows + header
- ranks 1-100 unique
- scores non-increasing
- tie-break compatible with validator

Note: the provided sample file contains 50 candidates, so it is useful for smoke testing but cannot satisfy the validator's exact 100-row requirement.

## Sandbox / Demo
A Streamlit demo app is included as `app.py`. It supports small JSON/JSONL uploads, previewing ranked candidates, and downloading the ranking as XLSX.

To run locally:
```bash
streamlit run app.py
```

## Limitations
- Purely heuristic scoring; no learned ranking model is used.
- Career narrative understanding relies on keyword and title matching.
- Full challenge score remains hidden until competition evaluation.
- Sample dataset is too small for validator-passing sample submissions.

## Reproducibility Command
```bash
python src/ranker.py --candidates ./candidates.jsonl --out ./output/submission.xlsx
```


## Submission Notes
Before final submission, confirm:
- `submission_metadata.yaml` is fully filled
- sandbox link is public
- repository paths and commands match this README exactly
- the final uploaded submission filename matches the portal requirement for your participant ID, preferably `.xlsx` if that is what the portal expects

## Deployment Notes
To finish the public deliverables:
1. push `my-redrob-ranker/` to a public GitHub repository
2. deploy `app.py` on Streamlit Cloud
3. update `submission_metadata.yaml` with the real GitHub URL, sandbox URL, and team details
4. upload the final validated XLSX using the participant-ID filename required by the organizers

## Alignment with Organizer Requirements
This implementation is aligned with the organizer bundle on the following points:
- ranks exactly the top 100 candidates from the full pool
- produces the required submission columns in XLSX format
- uses deterministic tie-break by `candidate_id` ascending
- runs on CPU with no network calls during ranking
- finishes well within the 5-minute ranking budget on the full 100K dataset
- includes a working sandbox app for small-sample reproducibility
- includes repository metadata and reproducibility instructions for Stage 3 review

Known caveat:
- `sample_candidates.json` contains only 50 rows, so it is suitable for smoke tests and sandbox demos but cannot pass the official 100-row validator by itself.

## Can this win?
It is structurally aligned with the challenge and avoids the most common failure modes: invalid format, excessive honeypots, non-reproducible code, and generic keyword-only ranking. The current system is strong on:
- JD-aware skill and retrieval/ranking fit
- product-vs-services discrimination
- behavioral signal weighting
- honeypot avoidance
- reproducibility and validation

However, whether it wins depends on hidden ground truth and how well the current heuristics capture subtle Tier-4/Tier-5 candidates. It is submission-ready and credible, but no one can honestly guarantee a win without the hidden labels.

Recommendation:
- keep this implementation as the baseline final submission
- do one last manual review of the top 20 candidates before uploading the XLSX
- ensure sandbox and metadata are fully completed before submission
- name the uploaded file exactly as required by the submission spec

Presentation work has been intentionally left out per your instruction.
# my-redrob-ranker
