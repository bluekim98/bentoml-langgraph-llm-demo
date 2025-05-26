import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from app.schemas import ReviewAnalysisOutput
import logging
import os

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize PydanticOutputParser at the module level
output_parser = PydanticOutputParser(pydantic_object=ReviewAnalysisOutput)

def invoke_gemini_with_structured_output(
    prompt_file_path: str,
    params: dict,
    model_name: str,
    temperature: float
) -> ReviewAnalysisOutput:
    """
    지정된 프롬프트 파일, 파라미터, 모델명, 온도를 사용하여 Gemini 모델을 동적으로 생성 및 호출하고,
    응답을 Pydantic 모델 객체로 구조화하여 반환합니다.

    Args:
        prompt_file_path: 사용할 메타 프롬프트 파일의 경로.
        params: 프롬프트 포맷팅에 사용될 딕셔너리 형태의 파라미터.
        model_name: 사용할 Gemini 모델의 이름 (예: "gemini-1.5-flash-latest"). 필수 입력.
        temperature: 모델의 생성 온도. 필수 입력.

    Returns:
        ReviewAnalysisOutput: Gemini 모델의 응답을 파싱한 Pydantic 객체.

    Raises:
        ValueError: model_name 또는 temperature 파라미터가 누락된 경우.
        FileNotFoundError: 프롬프트 파일이 존재하지 않을 경우.
        OutputParserException: LLM의 응답을 Pydantic 모델로 파싱하지 못할 경우.
        Exception: Gemini API 호출 중 오류 발생 시 또는 기타 예외.
    """
    if not model_name or temperature is None: # temperature가 0.0일 수 있으므로 None 체크
        logging.error("ValueError: model_name and temperature must be provided.")
        raise ValueError("model_name and temperature must be provided.")

    logging.info(f"Invoking Gemini with prompt file: {prompt_file_path}, param keys: {list(params.keys()) if params else None}, model: {model_name}, temperature: {temperature}")
    
    try:
        # Dynamically create ChatGoogleGenerativeAI instance
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature
            # GOOGLE_API_KEY is typically loaded from environment variables by the library itself
        )
        logging.info(f"Dynamically initialized ChatGoogleGenerativeAI with model: {model_name}, temperature: {temperature}")

        # 1. Load prompt template from file
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template_str = f.read()
        logging.info(f"Successfully loaded prompt template from {prompt_file_path}")

        # 2. Get format instructions from the parser
        format_instructions = output_parser.get_format_instructions()
        # logging.info(f"Format instructions for PydanticOutputParser: {format_instructions}") # 로그가 너무 길어질 수 있어 주석 처리

        # 3. Format the prompt template
        full_prompt = prompt_template_str.format(**params, format_instructions=format_instructions)
        # logging.info(f"Formatted prompt: {full_prompt}") # 프롬프트 내용이 민감하거나 길 수 있어 주석 처리
        logging.info("Prompt formatted successfully.")

        # 4. Create HumanMessage
        message = HumanMessage(content=full_prompt)

        # 5. Invoke LLM
        logging.info(f"Sending request to Gemini LLM (model: {model_name})...")
        response = llm.invoke([message]) # Use the dynamically created llm instance
        logging.info(f"Received response from Gemini LLM (model: {model_name}). Content length: {len(response.content)}")

        # 6. Parse the LLM response content
        parsed_output = output_parser.parse(response.content)
        logging.info(f"Successfully parsed LLM response into Pydantic object for model: {model_name}")
        return parsed_output

    except FileNotFoundError:
        logging.error(f"Prompt file not found: {prompt_file_path}")
        raise
    except OutputParserException as e:
        # 여기서 response.content를 로깅할 때도 매우 길거나 민감할 수 있으므로 주의가 필요합니다.
        # 필요한 경우 일부만 로깅하거나 길이를 제한하는 것이 좋습니다.
        original_content_snippet = response.content[:500] if 'response' in locals() and response and hasattr(response, 'content') and isinstance(response.content, str) else 'Response not available or not string type'
        logging.error(f"Failed to parse LLM response for model {model_name}: {e}. Original content snippet: {original_content_snippet}")
        raise
    except ValueError as e: # Catch the ValueError raisedChecks for missing parameters
        logging.error(f"ValueError in invoke_gemini_with_structured_output: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred with model {model_name}: {e}")
        raise