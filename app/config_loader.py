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
    (내부 사용) 지정된 경로의 YAML 파일을 로드하여 전체 모델 설정 딕셔너리를 반환하고 캐시에 저장합니다.
    이 함수는 모듈 외부로 직접 노출되지 않고, `get_model_config` 함수를 통해 간접적으로 사용됩니다.

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

def get_model_config(config_key: str | None = None, config_path: str = "config/model_configurations.yaml") -> dict | None:
    """
    특정 `config_key`에 해당하는 모델 설정을 반환합니다.
    `config_key`가 제공되지 않으면 기본 설정을 반환합니다.
    설정은 내부 캐시를 활용하여 로드됩니다.

    Args:
        config_key: 가져올 모델 설정의 키 (예: "gemini_flash_zero_temp"). 
                      `None`일 경우 기본 설정을 의미합니다. 기본값은 `None`입니다.
        config_path: 로드할 설정 파일의 경로. 
                      `_MODEL_CONFIGS_CACHE`에 해당 경로의 설정이 없을 때 사용됩니다. 
                      기본값은 "config/model_configurations.yaml"입니다.

    Returns:
        dict | None: 특정 또는 기본 모델 설정 딕셔너리. 
                     키가 없거나 유효하지 않거나, 설정 로드에 실패하면 `None`.
    """
    try:
        configurations = load_model_configurations(config_path)
    except Exception as e:
        # load_model_configurations에서 예외 발생 시, 여기서는 추가 로깅 없이 None 반환 또는 예외 전파
        # 현재 프롬프트에서는 예외 전파 가능성도 언급하지만, 기존 코드 흐름상 None 반환이 자연스러울 수 있음
        # 여기서는 예외가 이미 로깅되었으므로 None을 반환하여 호출자에게 실패를 알림.
        logger.debug(f"Failed to load configurations from {config_path} in get_model_config due to: {e}")
        return None
    
    if not configurations: # load_model_configurations가 정상적으로 dict를 반환했는지 한번 더 확인 (이론상 위 try-except에서 걸릴 것)
        logger.warning("Configurations could not be loaded or are empty.")
        return None

    actual_config_key = config_key
    if actual_config_key is None: # 기본 설정 요청
        logger.info(f"No specific config_key provided, attempting to use default key from {config_path}.")
        default_key_from_yaml = configurations.get("default_model_config_key")
        if default_key_from_yaml is None:
            logger.warning(f"'default_model_config_key' not found in configurations loaded from {config_path}.")
            return None
        if not isinstance(default_key_from_yaml, str):
            logger.warning(f"'default_model_config_key' in {config_path} is not a string: {default_key_from_yaml}")
            return None
        actual_config_key = default_key_from_yaml
        logger.info(f"Using default model config key: {actual_config_key}")

    model_specific_configs = configurations.get("model_configurations")
    if not isinstance(model_specific_configs, dict):
        logger.warning(f"'model_configurations' key not found or is not a dictionary in the loaded config from {config_path}.")
        return None

    final_config = model_specific_configs.get(actual_config_key)
    if final_config is None:
        logger.warning(f"Model configuration key '{actual_config_key}' not found in model_configurations from {config_path}.")
        return None
    
    if not isinstance(final_config, dict):
        logger.warning(f"Configuration for key '{actual_config_key}' in {config_path} is not a dictionary.")
        return None
        
    logger.info(f"Retrieved configuration for model key: {actual_config_key} from {config_path}")
    return final_config

# Example of how to set up logging in the main application to see logs from this module
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     
#     # Test loading
#     print("--- Testing default model config ---")
#     default_config = get_model_config()
#     if default_config:
#         print("Default config:", default_config)
#     else:
#         print("Failed to get default config.")
#     
#     print("\n--- Testing specific model config (gemini_flash_zero_temp) ---")
#     specific_config = get_model_config("gemini_flash_zero_temp")
#     if specific_config:
#         print("Specific config for gemini_flash_zero_temp:", specific_config)
#     else:
#         print("Failed to get specific config for gemini_flash_zero_temp.")
# 
#     print("\n--- Testing non-existent model config ---")
#     non_existent_config = get_model_config("non_existent_key_123")
#     if non_existent_config:
#         print("Config for non_existent_key_123:", non_existent_config)
#     else:
#         print("Correctly failed to get config for non_existent_key_123 (should be None).")

#     print("\n--- Testing with non-existent file ---")
#     non_existent_file_config = get_model_config(config_path="config/non_existent.yaml")
#     if non_existent_file_config:
#         print("Config from non_existent.yaml:", non_existent_file_config) # Should not happen
#     else:
#         print("Correctly failed to get config from non_existent.yaml (should be None).")

#     print("\n--- Testing with a custom config file (create a dummy one for testing) ---")
#     custom_config_content = {
#         "default_model_config_key": "my_default",
#         "model_configurations": {
#             "my_default": {"desc": "My custom default model"},
#             "my_other": {"desc": "My other custom model"}
#         }
#     }
#     custom_path = "temp_custom_config.yaml"
#     with open(custom_path, 'w') as f:
#         yaml.dump(custom_config_content, f)
#     
#     custom_default = get_model_config(config_path=custom_path)
#     if custom_default:
#         print(f"Default from {custom_path}:", custom_default)
#     else:
#         print(f"Failed to get default from {custom_path}.")
#     
#     custom_specific = get_model_config("my_other", config_path=custom_path)
#     if custom_specific:
#         print(f"Specific 'my_other' from {custom_path}:", custom_specific)
#     else:
#         print(f"Failed to get specific 'my_other' from {custom_path}.")
#     os.remove(custom_path) # Clean up dummy file 