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
