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

# Initialize Gemini LLM (already provided by user)
gemini = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-1.0-pro"), # 환경 변수 또는 기본값 사용
    temperature=float(os.getenv("GEMINI_TEMPERATURE", 0.0)), # 환경 변수 또는 기본값 사용
    # google_api_key=os.getenv("GOOGLE_API_KEY") # API 키는 ChatGoogleGenerativeAI 내부적으로 환경 변수에서 로드함
)

# Initialize PydanticOutputParser at the module level
output_parser = PydanticOutputParser(pydantic_object=ReviewAnalysisOutput)

def invoke_gemini_with_structured_output(
    prompt_file_path: str,
    params: dict
) -> ReviewAnalysisOutput:
    """
    지정된 프롬프트 파일과 파라미터를 사용하여 Gemini 모델을 호출하고,
    응답을 Pydantic 모델 객체로 구조화하여 반환합니다.

    Args:
        prompt_file_path: 사용할 메타 프롬프트 파일의 경로.
        params: 프롬프트 포맷팅에 사용될 딕셔너리 형태의 파라미터.

    Returns:
        ReviewAnalysisOutput: Gemini 모델의 응답을 파싱한 Pydantic 객체.

    Raises:
        FileNotFoundError: 프롬프트 파일이 존재하지 않을 경우.
        OutputParserException: LLM의 응답을 Pydantic 모델로 파싱하지 못할 경우.
        Exception: Gemini API 호출 중 오류 발생 시 또는 기타 예외.
    """
    logging.info(f"Invoking Gemini with prompt file: {prompt_file_path} and params: {params}")
    try:
        # 1. Load prompt template from file
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template_str = f.read()
        logging.info(f"Successfully loaded prompt template from {prompt_file_path}")

        # 2. Get format instructions from the parser
        format_instructions = output_parser.get_format_instructions()
        logging.info(f"Format instructions for PydanticOutputParser: {format_instructions}")

        # 3. Format the prompt template with user params and format instructions
        # Ensure the prompt template has placeholders for all keys in params and for 'format_instructions'
        # Example prompt template:
        # """
        # Your original prompt with {param1}, {param2}...
        # {format_instructions}
        # """
        full_prompt = prompt_template_str.format(**params, format_instructions=format_instructions)
        logging.info(f"Formatted prompt: {full_prompt}")

        # 4. Create HumanMessage
        message = HumanMessage(content=full_prompt)

        # 5. Invoke LLM
        logging.info("Sending request to Gemini LLM...")
        response = gemini.invoke([message])
        logging.info(f"Received response from Gemini LLM: {response.content}")

        # 6. Parse the LLM response content
        parsed_output = output_parser.parse(response.content)
        logging.info(f"Successfully parsed LLM response into Pydantic object: {parsed_output}")
        return parsed_output

    except FileNotFoundError:
        logging.error(f"Prompt file not found: {prompt_file_path}")
        raise
    except OutputParserException as e:
        logging.error(f"Failed to parse LLM response: {e}")
        # 추가적으로 LLM의 원본 응답을 로깅하거나 포함하여 예외를 다시 발생시킬 수 있습니다.
        # raise OutputParserException(f"Original LLM output: {response.content} \\n Parsing error: {e}") from e
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise