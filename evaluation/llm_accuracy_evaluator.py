import json
import math
from scipy.stats import binomtest
from typing import List, Dict, Any, Tuple
import os
from .reporter import generate_markdown_report

# 경계값 정의 (예시 2 기준)
NEGATIVE_THRESHOLD_UPPER = 1/3  # 0.0 <= score < 0.333...
NEUTRAL_THRESHOLD_UPPER = 2/3   # 0.333... <= score < 0.666...
# POSITIVE: 0.666... <= score <= 1.0

def get_sentiment_bin_label(score: float) -> str:
    """Helper function to determine the sentiment bin label for a given score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Score must be between 0.0 and 1.0")
    
    if score < NEGATIVE_THRESHOLD_UPPER:
        return "Negative"
    elif score < NEUTRAL_THRESHOLD_UPPER:
        return "Neutral"
    else:
        return "Positive"

def evaluate_llm_accuracy_by_sentiment_bin(
    json_file_path: str = "data/benchmark/sample.json",
    human_score_key: str = "pre_score",
    llm_score_key: str = "score",
    confidence_level: float = 0.95
) -> List[Dict[str, Any]]:
    """
    Evaluates LLM accuracy by comparing human scores and LLM scores binned into
    Negative, Neutral, and Positive sentiment categories, and calculates the Wilson 
    score confidence interval for the match rate within each human sentiment bin.

    Args:
        json_file_path: Path to the JSON file containing evaluation data.
        human_score_key: Key for the human-assigned score in the JSON data.
        llm_score_key: Key for the LLM-assigned score in the JSON data.
        confidence_level: Confidence level for the Wilson score interval.

    Returns:
        A list of dictionaries, where each dictionary represents a human_sentiment_bin and contains:
        - 'human_sentiment_bin_label': The label ("Negative", "Neutral", "Positive").
        - 'total_reviews_in_bin': Total number of reviews where human_score falls into this bin.
        - 'matched_reviews_in_bin': Number of reviews where LLM_score_bin matches human_score_bin.
        - 'match_rate': Proportion of matches in this bin.
        - 'wilson_lower_bound': Lower bound of the Wilson score confidence interval.
        - 'wilson_upper_bound': Upper bound of the Wilson score confidence interval.
        - 'llm_score_distribution': Distribution of LLM scores (binned) for this human score bin.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {json_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}")
        return []

    sentiment_bin_labels = ["Negative", "Neutral", "Positive"]
    human_sentiment_bins: Dict[str, Dict[str, Any]] = {}

    for label in sentiment_bin_labels:
        human_sentiment_bins[label] = {
            "total_reviews_in_bin": 0,
            "matched_reviews_in_bin": 0,
            "llm_score_distribution": {bin_l: 0 for bin_l in sentiment_bin_labels}
        }

    for item in data:
        try:
            human_score = float(item.get(human_score_key, -1))
            llm_score = float(item.get(llm_score_key, -1))

            if not (0.0 <= human_score <= 1.0 and 0.0 <= llm_score <= 1.0):
                # print(f"Skipping item with invalid score: {item}")
                continue

            human_bin_label = get_sentiment_bin_label(human_score)
            llm_bin_label = get_sentiment_bin_label(llm_score)
            
            # This check is for safety, human_bin_label should always be one of the defined sentiment_bin_labels
            if human_bin_label in human_sentiment_bins:
                 human_sentiment_bins[human_bin_label]["total_reviews_in_bin"] += 1
                 human_sentiment_bins[human_bin_label]["llm_score_distribution"][llm_bin_label] +=1
                 if human_bin_label == llm_bin_label:
                    human_sentiment_bins[human_bin_label]["matched_reviews_in_bin"] += 1
            else:
                # Should not happen with the current get_sentiment_bin_label logic
                print(f"Warning: Human score {human_score} (bin {human_bin_label}) did not fall into a predefined sentiment bin.")


        except (TypeError, ValueError) as e:
            print(f"Skipping item due to data error: {item} - {e}")
            continue

    results = []
    # Ensure a specific order for bins in the results
    ordered_bin_labels = ["Negative", "Neutral", "Positive"]

    for bin_label in ordered_bin_labels:
        bin_data = human_sentiment_bins[bin_label]
        total_reviews = bin_data["total_reviews_in_bin"]
        matched_reviews = bin_data["matched_reviews_in_bin"]

        if total_reviews == 0:
            match_rate = 0.0
            lower_bound = 0.0
            upper_bound = 0.0
        else:
            match_rate = matched_reviews / total_reviews
            ci_result = binomtest(k=matched_reviews, n=total_reviews) 
            interval = ci_result.proportion_ci(confidence_level=confidence_level, method='wilson')
            lower_bound = interval.low
            upper_bound = interval.high
            
            if math.isnan(lower_bound) or lower_bound < 0: lower_bound = 0.0
            if math.isnan(upper_bound) or upper_bound > 1: upper_bound = 1.0


        results.append({
            "human_sentiment_bin_label": bin_label,
            "total_reviews_in_bin": total_reviews,
            "matched_reviews_in_bin": matched_reviews,
            "match_rate": match_rate,
            "wilson_lower_bound": lower_bound,
            "wilson_upper_bound": upper_bound,
            "llm_score_distribution": bin_data["llm_score_distribution"]
        })
        
    return results
