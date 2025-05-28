# evaluation/run_evaluation.py 의 내용입니다.

import argparse
import os
import json # 더미 데이터 생성 로직이 필요하다면 사용

# 같은 evaluation 패키지 내의 모듈을 상대 경로로 임포트합니다.
from .llm_accuracy_evaluator import evaluate_llm_accuracy_by_sentiment_bin
from .reporter import generate_markdown_report

def main():
    parser = argparse.ArgumentParser(description="LLM Accuracy Evaluator and Reporter")
    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="Path to the JSON file containing evaluation data (e.g., data/benchmark/sample.json)"
    )

    args = parser.parse_args()

    # 고정값 설정
    human_score_key = "pre_score"
    llm_score_key = "score"

    if not os.path.exists(args.data_path):
        print(f"Error: Data file not found at {args.data_path}")
        return

    print(f"Starting evaluation for data: {args.data_path}")
    evaluation_results = evaluate_llm_accuracy_by_sentiment_bin(
        json_file_path=args.data_path,
        human_score_key=human_score_key,
        llm_score_key=llm_score_key,
    )

    if evaluation_results:
        print("\nEvaluation Results by Sentiment Bin (Summary):")
        for result in evaluation_results:
            print(
                f"  Human Sentiment Bin: {result['human_sentiment_bin_label']:<10} | "
                f"Match Rate: {result['match_rate']:.2%} | "
                f"LLM Dist: N:{result['llm_score_distribution']['Negative']}, Neu:{result['llm_score_distribution']['Neutral']}, P:{result['llm_score_distribution']['Positive']}"
            )
        
        # 모델 이름 파생
        model_name_from_file = os.path.splitext(os.path.basename(args.data_path))[0]
        report_model_name = model_name_from_file if model_name_from_file.lower() not in ["sample", "dummy"] else "LLM_Output"
        
        report_file_path = generate_markdown_report(
            evaluation_results, 
            args.data_path, 
            report_model_name
        )
        if report_file_path:
            print(f"\nMarkdown report successfully generated at: {report_file_path}")
        else:
            print("\nFailed to generate markdown report.")
    else:
        print("No evaluation results were generated. Please check the input file and keys.")

if __name__ == '__main__':
    main() 