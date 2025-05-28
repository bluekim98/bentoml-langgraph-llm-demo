import datetime
import os
from typing import List, Dict, Any

def generate_markdown_report(
    evaluation_results: List[Dict[str, Any]],
    dataset_filename: str,
    model_name: str = "LLM" # 모델 이름을 받을 수 있도록 추가
) -> str:
    """
    Generates a markdown report from LLM evaluation results.

    Args:
        evaluation_results: A list of dictionaries, where each dictionary 
                            represents a human_sentiment_bin and contains evaluation metrics.
        dataset_filename: The name of the dataset file used for evaluation (e.g., "reviews_test_set_v1.csv").
        model_name: The name of the LLM model evaluated.

    Returns:
        The filepath of the generated markdown report.
    """
    report_parts = []

    # 1. Report Header
    report_parts.append(f"# {model_name} Evaluation Report for {dataset_filename}")
    report_parts.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_parts.append("")
    report_parts.append("---")

    # 2. Summary Section
    report_parts.append("## 1. Evaluation Summary")
    report_parts.append("| Human Sentiment Bin | Total Reviews | Matched Reviews | Match Rate | Wilson CI (95%) | LLM Prediction Distribution (N, Neu, P) |")
    report_parts.append("|---|---|---|---|---|---|")

    for result in evaluation_results:
        dist = result['llm_score_distribution']
        llm_dist_str = f"N: {dist.get('Negative', 0)}, Neu: {dist.get('Neutral', 0)}, P: {dist.get('Positive', 0)}"
        summary_line = (
            f"| {result['human_sentiment_bin_label']} "
            f"| {result['total_reviews_in_bin']} "
            f"| {result['matched_reviews_in_bin']} "
            f"| {result['match_rate']:.2%} "
            f"| ({result['wilson_lower_bound']:.3f}, {result['wilson_upper_bound']:.3f}) "
            f"| {llm_dist_str} |"
        )
        report_parts.append(summary_line)
    report_parts.append("")

    # 3. Detailed Analysis Section
    report_parts.append("## 2. 상세 분석 (사람 평가 감성 범주별)")

    for result in evaluation_results:
        bin_label_korean = {"Negative": "부정", "Neutral": "중립", "Positive": "긍정"}.get(result['human_sentiment_bin_label'], result['human_sentiment_bin_label'])
        bin_label_english = result['human_sentiment_bin_label'] # LLM Dist 접근 시 필요

        total_reviews = result['total_reviews_in_bin']
        matched_reviews = result['matched_reviews_in_bin']
        match_rate = result['match_rate']
        lower_bound = result['wilson_lower_bound']
        upper_bound = result['wilson_upper_bound']
        llm_dist = result['llm_score_distribution']

        report_parts.append(f"### 2.{evaluation_results.index(result) + 1}. 사람이 '{bin_label_korean}'으로 평가한 리뷰 그룹")
        report_parts.append(f"- **총 리뷰 수**: {total_reviews}")
        if total_reviews > 0:
            report_parts.append(f"  - *해석*: 전체 평가 리뷰 중 {total_reviews}개가 사람에 의해 '{bin_label_korean}'(으)로 평가되었습니다.")
            report_parts.append(f"- **일치된 리뷰 수**: {matched_reviews}")
            report_parts.append(f"  - *해석*: 이 {total_reviews}개의 '{bin_label_korean}' 리뷰 중에서 {model_name} 또한 '{bin_label_korean}'(으)로 평가한 리뷰는 {matched_reviews}개입니다.")
            report_parts.append(f"- **일치율**: {match_rate:.2%}")
            report_parts.append(f"  - *해석*: '{bin_label_korean}'으로 평가된 리뷰에 대해 {model_name}이 동일하게 '{bin_label_korean}'(으)로 평가할 확률은 약 {match_rate:.2%}입니다.")
            report_parts.append(f"- **윌슨 신뢰 구간 (95%)**: ({lower_bound:.3f}, {upper_bound:.3f})")
            report_parts.append(f"  - *해석*: 95% 신뢰수준에서, 실제 '{bin_label_korean}' 리뷰에 대한 {model_name}의 일치율은 {lower_bound*100:.1f}%에서 {upper_bound*100:.1f}% 사이일 것으로 추정됩니다.")
            if lower_bound > 0.7:
                report_parts.append("    - *참고*: 신뢰구간의 하한값이 비교적 높아, 해당 범주에 대해 모델의 성능이 상당히 안정적이라고 볼 수 있습니다.")
            elif upper_bound < 0.5:
                report_parts.append("    - *참고*: 신뢰구간의 상한값이 비교적 낮아, 해당 범주에 대해 모델의 성능이 다소 불안정하거나 개선의 여지가 있음을 시사합니다.")
            else:
                 report_parts.append("    - *참고*: 신뢰구간은 모델의 실제 성능 범위를 나타냅니다. 구간이 넓을 경우, 샘플 크기나 결과의 변동성으로 인해 불확실성이 클 수 있습니다.")

            report_parts.append(f"- **사람이 '{bin_label_korean}'으로 평가한 리뷰에 대한 {model_name}의 예측 분포**:")
            report_parts.append(f"  - 부정(N)으로 예측: {llm_dist.get('Negative', 0)}")
            report_parts.append(f"  - 중립(Neu)으로 예측: {llm_dist.get('Neutral', 0)}")
            report_parts.append(f"  - 긍정(P)으로 예측: {llm_dist.get('Positive', 0)}")
            
            misclassified_as = []
            if bin_label_english == "Negative":
                if llm_dist.get('Neutral', 0) > 0: misclassified_as.append(f"{llm_dist.get('Neutral', 0)}개를 중립(실제보다 긍정적)으로")
                if llm_dist.get('Positive', 0) > 0: misclassified_as.append(f"{llm_dist.get('Positive', 0)}개를 긍정(실제보다 매우 긍정적)으로")
            elif bin_label_english == "Neutral":
                if llm_dist.get('Negative', 0) > 0: misclassified_as.append(f"{llm_dist.get('Negative', 0)}개를 부정(실제보다 부정적)으로")
                if llm_dist.get('Positive', 0) > 0: misclassified_as.append(f"{llm_dist.get('Positive', 0)}개를 긍정(실제보다 긍정적)으로")
            elif bin_label_english == "Positive":
                if llm_dist.get('Negative', 0) > 0: misclassified_as.append(f"{llm_dist.get('Negative', 0)}개를 부정(실제보다 매우 부정적)으로")
                if llm_dist.get('Neutral', 0) > 0: misclassified_as.append(f"{llm_dist.get('Neutral', 0)}개를 중립(실제보다 부정적)으로")

            if misclassified_as:
                report_parts.append(f"  - *오분류 분석*: 사람이 '{bin_label_korean}'(으)로 평가한 리뷰를 {model_name}이 잘못 분류한 경우, 주로 {'; '.join(misclassified_as)} 평가했습니다.")
            elif matched_reviews == total_reviews:
                report_parts.append(f"  - *오분류 분석*: {model_name}은(는) 사람이 '{bin_label_korean}'(으)로 평가한 모든 리뷰를 완벽하게 분류했습니다.")
            else: 
                 report_parts.append(f"  - *오분류 분석*: 해당 범주에서는 직접 일치 외 특별한 오분류 경향은 나타나지 않았습니다.")
        else: # total_reviews == 0
            report_parts.append(f"  - 이 데이터셋에서 사람이 '{bin_label_korean}'(으)로 평가한 리뷰는 없습니다.")
        report_parts.append("")

    # File saving logic
    output_dir = "data/benchmark/result"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sanitize dataset_filename to remove extension for the report filename
    dataset_filename_base = os.path.splitext(os.path.basename(dataset_filename))[0]
    
    # Sanitize model_name for filename
    safe_model_name = "".join(c if c.isalnum() else "_" for c in model_name)

    report_filename = f"{dataset_filename_base}_on_{safe_model_name}_eval_{timestamp}.md"
    report_filepath = os.path.join(output_dir, report_filename)

    try:
        with open(report_filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_parts))
        print(f"Markdown report generated: {report_filepath}")
        return report_filepath
    except IOError as e:
        print(f"Error writing markdown report to {report_filepath}: {e}")
        return ""

if __name__ == '__main__':
    # Dummy data for testing the reporter
    # This structure matches what evaluate_llm_accuracy_by_sentiment_bin would return
    sample_evaluation_results = [
        {
            "human_sentiment_bin_label": "Negative",
            "total_reviews_in_bin": 76,
            "matched_reviews_in_bin": 59,
            "match_rate": 0.7763157894736842,
            "wilson_lower_bound": 0.671,
            "wilson_upper_bound": 0.855,
            "llm_score_distribution": {"Negative": 59, "Neutral": 15, "Positive": 2}
        },
        {
            "human_sentiment_bin_label": "Neutral",
            "total_reviews_in_bin": 50,
            "matched_reviews_in_bin": 30,
            "match_rate": 0.60,
            "wilson_lower_bound": 0.457,
            "wilson_upper_bound": 0.729,
            "llm_score_distribution": {"Negative": 10, "Neutral": 30, "Positive": 10}
        },
        {
            "human_sentiment_bin_label": "Positive",
            "total_reviews_in_bin": 74,
            "matched_reviews_in_bin": 65,
            "match_rate": 0.8783783783783784,
            "wilson_lower_bound": 0.782,
            "wilson_upper_bound": 0.937,
            "llm_score_distribution": {"Negative": 1, "Neutral": 8, "Positive": 65}
        }
    ]
    
    sample_dataset_filename = "sample_reviews_test.csv"
    sample_model_name = "AwesomeLLM v1.2"

    # Generate the report
    generated_file = generate_markdown_report(sample_evaluation_results, sample_dataset_filename, sample_model_name)
    
    if generated_file:
        print(f"Test report generated successfully: {generated_file}")
        # You can open and verify the generated file.
        # For example, to print its content:
        # with open(generated_file, 'r') as f_read:
        #     print("\\n--- Report Content ---")
        #     print(f_read.read())
    else:
        print("Test report generation failed.")

    # Test case with no reviews in a bin
    sample_empty_bin_results = [
        {
            "human_sentiment_bin_label": "Negative",
            "total_reviews_in_bin": 0,
            "matched_reviews_in_bin": 0,
            "match_rate": 0.0,
            "wilson_lower_bound": 0.0,
            "wilson_upper_bound": 0.0,
            "llm_score_distribution": {"Negative": 0, "Neutral": 0, "Positive": 0}
        },
         {
            "human_sentiment_bin_label": "Neutral",
            "total_reviews_in_bin": 10,
            "matched_reviews_in_bin": 5,
            "match_rate": 0.5,
            "wilson_lower_bound": 0.22,
            "wilson_upper_bound": 0.78,
            "llm_score_distribution": {"Negative": 2, "Neutral": 5, "Positive": 3}
        },
    ]
    generated_empty_bin_file = generate_markdown_report(sample_empty_bin_results, "empty_bin_test.json", "TestModel")
    if generated_empty_bin_file:
        print(f"Test report with empty bin generated successfully: {generated_empty_bin_file}")
    else:
        print("Test report generation with empty bin failed.") 