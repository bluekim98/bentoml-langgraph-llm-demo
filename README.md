# LLM 기반 텍스트 분석 샘플 프로젝트 (with Cursor)

## 🌟 소개

- 이 프로젝트는 **Cursor** 와 함께 개발되었으며, AI 기반 개발 도구를 활용한 효율적인 코딩 과정을 탐색하는 것을 목표로 합니다.
- LLM을 활용한 심층 텍스트 분석, 특히 음식점 리뷰에 초점을 맞춘 실용적인 예제를 보여줍니다. 
- LangGraph를 사용하여 복잡한 LLM 체인을 구성 및 관리하고, BentoML을 활용하여 LangGraph 파이프라인을 패키징하고 API로 서빙합니다.


## ✨ 특징

*   **AI 기반 개발 (`Cursor Project Rules` 활용)**: **Cursor** 와 같은 AI 개발 도구를 적극적으로 활용하여 프로젝트를 진행하며, `Cursor Project Rules` 를 정의하고 활용하여 AI와의 협업을 최적화하고 효율적인 코딩 및 개발 과정을 탐색합니다.
*   **`LLM` 기반 심층 분석 예제**: 음식점 리뷰와 같은 텍스트 데이터에 대해 `LLM`을 활용하여 심층적인 분석을 수행하는 실용적인 예제를 제공합니다.
*   **`LangGraph` 워크플로우**: 복잡한 LLM 체인 및 상태 기반 에이전트 로직을 `LangGraph`를 통해 그래프 형태로 구성하고 관리하는 방법을 보여줍니다.
*   **`BentoML` API 서빙**: 개발된 `LangGraph` 기반 분석 파이프라인을 `BentoML`을 사용하여 패키징하고, 실제 API로 서빙하는 과정을 포함합니다.

## 🛠️ 기술 스택

*   `bentoml`: MLOps 플랫폼으로, 모델 배포 및 관리를 용이하게 합니다.
*   `langchain`: LLM 애플리케이션 개발을 위한 프레임워크입니다.
*   `langgraph`: `langchain`을 기반으로 복잡한 LLM 워크플로우를 그래프 형태로 구성합니다.
*   `pytest`: Python 코드 테스트를 위한 프레임워크입니다.

## 🚀 실행 및 빌드 (BentoML)

이 프로젝트는 [BentoML](https://www.bentoml.com/)을 사용하여 빌드되고 서빙될 수 있습니다.

### 개발 모드에서 서비스 실행

개발 환경에서 서비스를 실행하려면 다음 명령어를 사용하세요. 서비스는 기본적으로 `http://localhost:3000`에서 실행됩니다.

```bash
bentoml serve service:svc --reload
```

*   `service:svc`: `service.py` 파일의 `svc`라는 이름의 BentoML 서비스를 의미합니다.
*   `--reload`: 코드 변경 시 자동으로 서비스를 재시작합니다.

### Bento 빌드

배포 가능한 Bento를 빌드하려면 다음 명령어를 사용합니다. 이 명령어는 프로젝트의 모든 종속성과 코드를 포함하는 이미지(Bento)를 생성합니다.

```bash
bentoml build
```

빌드가 완료되면 Bento 태그가 출력됩니다 (예: `service:xxxxxxxxxxxxxxx`). 이 태그를 사용하여 Bento를 컨테이너화하거나 클라우드에 배포할 수 있습니다.

### 빌드된 Bento 실행 (예시)

빌드된 Bento를 로컬에서 실행하려면 (주로 테스트 목적):

```bash
# 먼저 Bento를 컨테이너 이미지로 빌드합니다 (태그는 bentoml build 결과로 나온 것을 사용).
# bentoml containerize service:xxxxxxxxxxxxxxx 
# (위 명령은 이미지를 생성하고, Docker Hub 등에 푸시하지는 않습니다.)

# Docker를 사용하여 로컬에서 실행
# docker run -p 3000:3000 your_bentoml_image_name_and_tag
# 예: docker run -p 3000:3000 bentoml-langgraph-llm-demo-service:latest 
# (이미지 이름과 태그는 containerize 또는 bentoml build 시 지정/확인된 값으로 변경)
```
(위 `service:xxxxxxxxxxxxxxx`는 `bentoml build` 후 출력된 실제 태그로 변경해야 합니다. `bentoml containerize` 명령으로 생성된 이미지 이름과 태그를 확인하여 `docker run` 명령에 사용하세요.)

더 자세한 정보는 [BentoML 공식 문서](https://docs.bentoml.com/en/latest/index.html)를 참고하세요.

### LLM 기반 분석 API 실행

LLM(음식점 리뷰) 분석 기능은 BentoML 서비스를 통해 API로 제공됩니다. 먼저 아래 명령어를 사용하여 BentoML 개발 서버를 실행합니다.

```bash
# 프로젝트 루트 디렉토리에서 실행
bentoml serve bentos.service:ReviewAnalysisService --reload
```

서버가 실행되면 (기본적으로 `http://localhost:3000`), 다음 `curl` 명령어를 사용하여 `/analyze_review` 엔드포인트로 리뷰 분석을 요청할 수 있습니다. 
이 예시는 API가 받을 수 있는 모든 파라미터를 포함합니다.

```bash
curl -X POST -H "Content-Type: application/json" --data '{ \
  "review_text": "음식이 정말 맛있어요! 특히 파스타는 인생 최고였습니다. 다만, 대기 시간이 조금 길었어요.", \
  "rating": 4.5, \
  "ordered_items": ["크림 파스타", "마르게리따 피자", "레드 와인"] \
}' http://localhost:3000/analyze_review
```

**요청 파라미터 설명:**

*   `review_text` (string, 필수): 분석할 음식점 리뷰 텍스트입니다.
*   `rating` (float, 필수): 고객이 부여한 평점입니다.
*   `ordered_items` (array of strings, 필수): 고객이 주문한 메뉴 목록입니다.

(참고: 현재 API 정의상 `model_config_key`나 `prompt_version`과 같은 파라미터는 API를 통해 직접 전달받지 않고, 서비스 내부에서 기본값이 사용됩니다. 이러한 값을 동적으로 변경하려면 서비스 코드 수정이 필요합니다.)


## LLM 성능 평가

프로젝트에는 LLM의 감성 분석 성능을 평가하고 결과를 리포트로 생성하는 기능이 포함되어 있습니다.

### 평가 실행 방법

1.  **평가 데이터 준비**: LLM의 예측 결과와 실제 사람의 평가 점수가 포함된 JSON 파일을 준비합니다. 각 항목에는 사람 평가 점수 키(기본값: `pre_score`)와 LLM 예측 점수 키(기본값: `score`)가 있어야 합니다. 점수는 0.0에서 1.0 사이의 값이어야 합니다.
    예시 데이터 파일: `data/benchmark/sample.json` (프로젝트에 포함된 샘플)

2.  **평가 스크립트 실행**: 프로젝트 루트 디렉토리에서 다음 명령어를 실행합니다.

    ```bash
    python -m evaluation.run_evaluation --data-path path/to/your/evaluation_data.json
    ```

    예를 들어, 프로젝트에 포함된 샘플 데이터를 사용하여 평가하려면 다음을 실행합니다.
    ```bash
    python -m evaluation.run_evaluation --data-path data/benchmark/sample.json
    ```

3.  **결과 확인**: 
    -   스크립트 실행 후 터미널에 간략한 평가 요약이 출력됩니다.
    -   상세 분석 내용이 포함된 Markdown 리포트가 `data/benchmark/result/` 디렉토리에 생성됩니다. 
        (예: `sample_on_LLM_Output_eval_YYYYMMDD_HHMMSS.md`)

이 리포트에는 각 감성 범주별(부정, 중립, 긍정) LLM의 일치율, 윌슨 신뢰 구간, 예측 분포 및 상세한 한국어 분석이 포함됩니다.

## Cursor 활용 팁
