# Design Prompt: `app/config_loader.py`

## 1. 개요
이 문서는 `app/config_loader.py` 모듈의 설계 및 구현 가이드라인을 정의합니다. 이 모듈은 `config/model_configurations.yaml` 파일에서 모델 설정 정보를 로드하고, 애플리케이션의 다른 부분에서 쉽게 사용할 수 있도록 제공하는 역할을 담당합니다.

## 2. 모듈 위치
`app/config_loader.py`

## 3. 주요 기능
-   지정된 경로의 YAML 설정 파일 (기본값: `config/model_configurations.yaml`)을 로드합니다.
-   로드된 전체 설정을 반환하거나, 특정 모델 설정 키에 해당하는 설정을 반환하는 함수를 제공합니다.
-   기본 모델 설정 키를 반환하는 함수를 제공합니다.
-   파일 I/O 오류, YAML 파싱 오류, 키 누락 등의 예외를 적절히 처리하고 로깅합니다.
-   로드된 설정은 한 번 로드된 후 캐싱되어 반복적인 파일 I/O를 방지할 수 있습니다 (선택적 최적화).

## 4. 핵심 함수 정의

### 4.1. `_MODEL_CONFIGS_CACHE = {}` (모듈 수준 비공개 변수)
-   로드된 설정을 캐싱하기 위한 딕셔너리 (선택 사항).

### 4.2. `load_model_configurations(config_path: str = "config/model_configurations.yaml") -> dict`
-   **목적**: 지정된 경로의 YAML 파일을 로드하여 전체 모델 설정 딕셔너리를 반환합니다. 캐싱 로직을 포함할 수 있습니다.
-   **입력**:
    -   `config_path: str`: 로드할 YAML 설정 파일의 경로. 기본값은 "config/model_configurations.yaml"입니다. (프로젝트 루트 기준 상대 경로)
-   **처리 과정**:
    1.  (선택 사항) `_MODEL_CONFIGS_CACHE`에 `config_path`에 해당하는 설정이 이미 캐시되어 있는지 확인하고, 있다면 캐시된 값을 반환합니다.
    2.  `PyYAML` 라이브러리를 사용하여 YAML 파일을 엽니다 (`read` 모드, `utf-8` 인코딩).
    3.  `yaml.safe_load()`를 사용하여 파일 내용을 파싱합니다.
    4.  파싱된 딕셔너리를 (선택 사항) `_MODEL_CONFIGS_CACHE`에 저장합니다.
    5.  파싱된 딕셔너리를 반환합니다.
    6.  `FileNotFoundError` 발생 시: 로깅 후 예외를 다시 발생시키거나, 빈 딕셔너리 또는 `None`을 반환하고 오류를 로깅할 수 있습니다 (여기서는 예외 재발생 권장).
    7.  `yaml.YAMLError` (파싱 오류) 발생 시: 로깅 후 예외를 다시 발생시킵니다.
-   **반환**: `dict`: 로드된 전체 설정 딕셔너리. 오류 발생 시 예외.

### 4.3. `get_model_config(config_key: str, configurations: dict | None = None) -> dict | None`
-   **목적**: 로드된 전체 설정 딕셔너리에서 특정 `config_key`에 해당하는 모델 설정을 반환합니다.
-   **입력**:
    -   `config_key: str`: 가져올 모델 설정의 키 (예: "gemini_flash_zero_temp").
    -   `configurations: dict | None`: `load_model_configurations()`로부터 반환된 전체 설정 딕셔너리. `None`일 경우 내부적으로 `load_model_configurations()`를 호출하여 로드합니다.
-   **처리 과정**:
    1.  `configurations`가 `None`이면 `load_model_configurations()`를 호출하여 설정을 로드합니다.
    2.  로드된 설정에서 `model_configurations` 키 아래의 딕셔너리를 가져옵니다. 해당 키가 없으면 `KeyError`를 발생시키거나 `None`을 반환하고 경고를 로깅합니다.
    3.  가져온 딕셔너리에서 `config_key`에 해당하는 설정을 조회합니다.
    4.  키가 존재하면 해당 설정 딕셔너리를 반환합니다.
    5.  키가 존재하지 않으면 `None`을 반환하고 경고를 로깅합니다 (또는 `KeyError` 발생).
-   **반환**: `dict | None`: 특정 모델 설정 딕셔너리 또는 키가 없을 경우 `None`.

### 4.4. `get_default_model_config_key(configurations: dict | None = None) -> str | None`
-   **목적**: 로드된 전체 설정 딕셔너리에서 `default_model_config_key` 값을 반환합니다.
-   **입력**:
    -   `configurations: dict | None`: `load_model_configurations()`로부터 반환된 전체 설정 딕셔너리. `None`일 경우 내부적으로 `load_model_configurations()`를 호출하여 로드합니다.
-   **처리 과정**:
    1.  `configurations`가 `None`이면 `load_model_configurations()`를 호출하여 설정을 로드합니다.
    2.  로드된 설정에서 `default_model_config_key` 값을 조회합니다.
    3.  키가 존재하면 해당 문자열 값을 반환합니다.
    4.  키가 존재하지 않으면 `None`을 반환하고 경고를 로깅합니다 (또는 `KeyError` 발생).
-   **반환**: `str | None`: 기본 모델 설정 키 문자열 또는 키가 없을 경우 `None`.

## 5. 로깅
-   표준 `logging` 모듈을 사용합니다.
-   설정 파일 로드 시도, 성공, 실패(파일 없음, 파싱 오류 등)를 로깅합니다.
-   특정 설정 키 조회 시 성공 또는 실패(키 없음)를 로깅합니다.

## 6. 의존성
-   `PyYAML` (YAML 파싱을 위해 `requirements.txt`에 추가 필요)
-   `logging`
-   `os` (파일 경로 처리를 위해)

## 7. 사용 예시 (다른 모듈에서)
'''python
# from app.config_loader import load_model_configurations, get_model_config, get_default_model_config_key
#
# all_configs = load_model_configurations()
# default_key = get_default_model_config_key(all_configs)
# if default_key:
#     default_model_settings = get_model_config(default_key, all_configs)
#     if default_model_settings:
#         # ... 설정 사용 ...
#         pass
#
# specific_settings = get_model_config("gemini_flash_zero_temp") # 내부적으로 로드
# if specific_settings:
#     # ... 설정 사용 ...
#     pass
''' 