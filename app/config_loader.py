import yaml
import logging
import os

# Configure logging for this module
logger = logging.getLogger(__name__)
# To see these logs, the main application's logging configuration should be set up.
# For example, in your main script:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

_MODEL_CONFIGS_CACHE = {} # Module-level cache

def load_model_configurations(config_path: str = "config/model_configurations.yaml") -> dict:
    """
    지정된 경로의 YAML 파일을 로드하여 전체 모델 설정 딕셔너리를 반환합니다.
    로드된 설정은 메모리에 캐싱되어 반복적인 파일 I/O를 방지합니다.

    Args:
        config_path: 로드할 YAML 설정 파일의 경로 (프로젝트 루트 기준 상대 경로).

    Returns:
        dict: 로드된 전체 설정 딕셔너리.

    Raises:
        FileNotFoundError: 설정 파일이 존재하지 않을 경우.
        yaml.YAMLError: YAML 파싱 중 오류 발생 시.
        Exception: 기타 예외 발생 시.
    """
    # 절대 경로로 변환하여 캐시 키의 일관성 유지
    abs_config_path = os.path.abspath(config_path)

    if abs_config_path in _MODEL_CONFIGS_CACHE:
        logger.info(f"Returning cached model configurations from {abs_config_path}")
        return _MODEL_CONFIGS_CACHE[abs_config_path]

    logger.info(f"Loading model configurations from {abs_config_path}")
    try:
        with open(abs_config_path, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f)
        if not isinstance(configs, dict):
            logger.error(f"Configuration file {abs_config_path} did not load as a dictionary.")
            raise yaml.YAMLError(f"Configuration file {abs_config_path} must be a dictionary.")
        
        _MODEL_CONFIGS_CACHE[abs_config_path] = configs
        logger.info(f"Successfully loaded and cached model configurations from {abs_config_path}")
        return configs
    except FileNotFoundError:
        logger.error(f"Model configuration file not found: {abs_config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration file {abs_config_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading {abs_config_path}: {e}")
        raise

def get_model_config(config_key: str, configurations: dict | None = None, config_path: str = "config/model_configurations.yaml") -> dict | None:
    """
    로드된 전체 설정 딕셔너리에서 특정 config_key에 해당하는 모델 설정을 반환합니다.

    Args:
        config_key: 가져올 모델 설정의 키 (예: "gemini_flash_zero_temp").
        configurations: 선택 사항. 미리 로드된 전체 설정 딕셔너리.
                      None일 경우 config_path를 사용하여 내부적으로 로드합니다.
        config_path: configurations가 None일 때 로드할 설정 파일 경로.

    Returns:
        dict | None: 특정 모델 설정 딕셔너리. 키가 없거나 오류 발생 시 None을 반환할 수 있음 (또는 예외 발생).
                     현재 설계에서는 키 누락 시 None 반환 및 경고 로깅.
    """
    if configurations is None:
        try:
            configurations = load_model_configurations(config_path)
        except Exception:
            # load_model_configurations에서 이미 에러 로깅 및 예외 발생
            return None # 또는 예외를 그대로 전달할 수 있음
    
    if not configurations or not isinstance(configurations, dict):
        logger.warning("Invalid or empty configurations provided to get_model_config.")
        return None

    model_specific_configs = configurations.get("model_configurations")
    if not isinstance(model_specific_configs, dict):
        logger.warning(f"'model_configurations' key not found or is not a dictionary in the loaded config.")
        return None

    config = model_specific_configs.get(config_key)
    if config is None:
        logger.warning(f"Model configuration key '{config_key}' not found in model_configurations.")
        return None
    
    if not isinstance(config, dict):
        logger.warning(f"Configuration for key '{config_key}' is not a dictionary.")
        return None
        
    logger.info(f"Retrieved configuration for model key: {config_key}")
    return config

def get_default_model_config_key(configurations: dict | None = None, config_path: str = "config/model_configurations.yaml") -> str | None:
    """
    로드된 전체 설정 딕셔너리에서 default_model_config_key 값을 반환합니다.

    Args:
        configurations: 선택 사항. 미리 로드된 전체 설정 딕셔너리.
                      None일 경우 config_path를 사용하여 내부적으로 로드합니다.
        config_path: configurations가 None일 때 로드할 설정 파일 경로.

    Returns:
        str | None: 기본 모델 설정 키 문자열. 키가 없거나 오류 시 None 반환.
    """
    if configurations is None:
        try:
            configurations = load_model_configurations(config_path)
        except Exception:
            return None

    if not configurations or not isinstance(configurations, dict):
        logger.warning("Invalid or empty configurations provided to get_default_model_config_key.")
        return None

    default_key = configurations.get("default_model_config_key")
    if default_key is None:
        logger.warning("'default_model_config_key' not found in configurations.")
        return None
    if not isinstance(default_key, str):
        logger.warning(f"'default_model_config_key' is not a string: {default_key}")
        return None

    logger.info(f"Retrieved default model configuration key: {default_key}")
    return default_key

# Example of how to set up logging in the main application to see logs from this module
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     
#     # Test loading
#     try:
#         configs = load_model_configurations()
#         print("Loaded configs:", configs)
#         
#         default_key = get_default_model_config_key(configs)
#         print("Default key:", default_key)
#         
#         if default_key:
#             default_config = get_model_config(default_key, configs)
#             print("Default config:", default_config)
#             
#         specific_config = get_model_config("gemini_flash_zero_temp", configs)
#         print("Specific config for gemini_flash_zero_temp:", specific_config)

#         non_existent_config = get_model_config("non_existent_key", configs)
#         print("Config for non_existent_key:", non_existent_config) # Should be None

#         # Test with non-existent file
#         # load_model_configurations("config/non_existent.yaml")
#     except Exception as e:
#         print(f"An error occurred during testing: {e}") 