
import json
import time
import os
from datetime import datetime, date
from pathlib import Path


def load_candidates_jsonl(filepath, max_count=None):

    candidates = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                candidates.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  Warning: Skipping malformed line {line_num}: {e}")

            if max_count and len(candidates) >= max_count:
                break
    return candidates


def load_candidates_json(filepath):
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_candidates(filepath, max_count=None):
    
    filepath = str(filepath)
    if filepath.endswith(".jsonl"):
        return load_candidates_jsonl(filepath, max_count=max_count)
    elif filepath.endswith(".json"):
        data = load_candidates_json(filepath)
        if max_count:
            return data[:max_count]
        return data
    else:
        try:
            return load_candidates_jsonl(filepath, max_count=max_count)
        except Exception:
            return load_candidates_json(filepath)



class Timer:

    def __init__(self, label=""):
        self.label = label
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed = time.time() - self.start_time
        if self.label:
            print(f"  [{self.label}] {self.elapsed:.2f}s")



def format_score(score, decimals=4):
    
    return f"{score:.{decimals}f}"


def truncate_string(s, max_len=200):
    
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


def print_section(title):
    
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")
