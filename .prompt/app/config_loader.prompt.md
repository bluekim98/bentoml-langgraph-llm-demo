# Design Prompt: `app/config_loader.py`

## 1. 개요
이 문서는 `app/config_loader.py` 모듈의 설계 및 구현 가이드라인을 정의합니다. 이 모듈은 `config/model_configurations.yaml` 파일에서 모델 설정 정보를 로드하고, 애플리케이션의 다른 부분에서 특정 모델 설정을 쉽게 사용할 수 있도록 제공하는 역할을 담당합니다.

## 2. 모듈 위치
`app/config_loader.py`

## 3. 주요 기능
-   지정된 경로의 YAML 설정 파일 (기본값: `config/model_configurations.yaml`)에서 모델 설정을 내부적으로 로드하고 캐싱합니다.
-   특정 모델 설정 키에 해당하는 설정을 반환하는 함수를 제공합니다. 이 함수는 키가 제공되지 않으면 기본 모델 설정을 반환합니다.
-   파일 I/O 오류, YAML 파싱 오류, 키 누락 등의 예외를 적절히 처리하고 로깅합니다.

## 4. 핵심 함수 정의

### 4.1. `_MODEL_CONFIGS_CACHE = {}` (모듈 수준 비공개 변수)
-   로드된 설정을 캐싱하기 위한 딕셔너리. 이 캐시는 `load_model_configurations` 함수에 의해서만 내부적으로 관리됩니다.

### 4.2. `load_model_configurations(config_path: str = "config/model_configurations.yaml") -> dict`
-   **목적**: (내부 사용) 지정된 경로의 YAML 파일을 로드하여 전체 모델 설정 딕셔너리를 반환하고 캐시에 저장합니다. 이 함수는 모듈 외부로 직접 노출되지 않고, `get_model_config` 함수를 통해 간접적으로 사용됩니다.
-   **입력**:
    -   `config_path: str`: 로드할 YAML 설정 파일의 경로. 기본값은 "config/model_configurations.yaml"입니다. (프로젝트 루트 기준 상대 경로)
-   **처리 과정**:
    1.  `_MODEL_CONFIGS_CACHE`에 `config_path`에 해당하는 설정이 이미 캐시되어 있는지 확인하고, 있다면 캐시된 값을 반환합니다.
    2.  `PyYAML` 라이브러리를 사용하여 YAML 파일을 엽니다 (`read` 모드, `utf-8` 인코딩).
    3.  `yaml.safe_load()`를 사용하여 파일 내용을 파싱합니다.
    4.  파싱된 결과가 딕셔너리 타입인지 검증하고, 아닐 경우 `yaml.YAMLError`를 발생시킵니다.
    5.  파싱된 딕셔너리를 `_MODEL_CONFIGS_CACHE`에 저장합니다.
    6.  파싱된 딕셔너리를 반환합니다.
    7.  `FileNotFoundError` 발생 시: 로깅 후 예외를 다시 발생시킵니다.
    8.  `yaml.YAMLError` (파싱 오류 또는 타입 불일치) 발생 시: 로깅 후 예외를 다시 발생시킵니다.
-   **반환**: `dict`: 로드된 전체 설정 딕셔너리. 오류 발생 시 예외.

### 4.3. `get_model_config(config_key: str | None = None, config_path: str = "config/model_configurations.yaml") -> dict | None`
-   **목적**: 특정 `config_key`에 해당하는 모델 설정을 반환합니다. `config_key`가 제공되지 않으면 기본 설정을 반환합니다. 설정은 내부 캐시를 활용하여 로드됩니다.
-   **입력**:
    -   `config_key: str | None`: 가져올 모델 설정의 키 (예: "gemini_flash_zero_temp"). `None`일 경우 기본 설정을 의미합니다. 기본값은 `None`입니다.
    -   `config_path: str`: 로드할 설정 파일의 경로. `_MODEL_CONFIGS_CACHE`에 해당 경로의 설정이 없을 때 사용됩니다. 기본값은 "config/model_configurations.yaml"입니다.
-   **처리 과정**:
    1.  `load_model_configurations(config_path)`를 호출하여 전체 설정을 로드하거나 캐시에서 가져옵니다. 로드 중 예외 발생 시(예: 파일 없음, YAML 형식 오류) 해당 예외가 전파되거나, 상황에 따라 로깅 후 `None`을 반환할 수 있습니다 (현재 코드에서는 `load_model_configurations`가 예외를 직접 발생시킴).
    2.  만약 `config_key`가 `None` (기본 설정 요청):
        a.  로드된 전체 설정에서 `default_model_config_key` 값을 조회합니다.
        b.  해당 키가 없거나 값이 문자열이 아니면 경고 로깅 후 `None`을 반환합니다.
        c.  조회된 기본 키를 `config_key`로 사용합니다.
    3.  로드된 전체 설정에서 `model_configurations` 키 아래의 딕셔너리를 가져옵니다. 해당 키가 없거나 값이 딕셔너리가 아니면 경고를 로깅하고 `None`을 반환합니다.
    4.  가져온 `model_configurations` 딕셔너리에서 현재 `config_key`에 해당하는 설정을 조회합니다.
    5.  조회된 설정이 딕셔너리가 아니면 경고 로깅 후 `None`을 반환합니다.
    6.  키가 존재하고 유효한 설정 딕셔너리이면 해당 설정을 반환합니다.
    7.  키가 존재하지 않으면 `None`을 반환하고 경고를 로깅합니다.
-   **반환**: `dict | None`: 특정 또는 기본 모델 설정 딕셔너리. 키가 없거나 유효하지 않거나, 설정 로드에 실패하면 `None`.

## 5. 로깅
-   표준 `logging` 모듈을 사용합니다.
-   설정 파일 로드 시도, 성공, 실패(파일 없음, 파싱 오류 등)를 로깅합니다.
-   특정 설정 키 (또는 기본 설정) 조회 시 성공 또는 실패(키 없음, 형식 오류 등)를 로깅합니다.

## 6. 의존성
-   `PyYAML` (YAML 파싱을 위해 `requirements.txt`에 추가 필요)
-   `logging`
-   `os` (파일 경로 처리를 위해)

## 7. 사용 예시 (다른 모듈에서)
'''python
# from app.config_loader import get_model_config
#
# # 기본 모델 설정 가져오기
# default_model_settings = get_model_config()
# if default_model_settings:
#     # ... 기본 설정 사용 ...
#     pass
#
# # 특정 모델 설정 가져오기
# specific_settings = get_model_config("gemini_flash_zero_temp")
# if specific_settings:
#     # ... 특정 설정 사용 ...
#     pass
#
# # 다른 경로의 설정 파일에서 가져오기 (필요시)
# custom_settings = get_model_config("my_custom_key", config_path="custom_config/models.yaml")
# if custom_settings:
#     # ... 사용자 정의 설정 사용 ...
#     pass 
''' 