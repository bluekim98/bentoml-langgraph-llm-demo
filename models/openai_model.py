import os
import logging
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from app.schemas import ReviewAnalysisOutput, ReviewInputs

load_dotenv()
logger = logging.getLogger(__name__)

# PydanticOutputParser를 ReviewAnalysisOutput 스키마로 초기화
output_parser = PydanticOutputParser(pydantic_object=ReviewAnalysisOutput)

def invoke_openai_with_structured_output(
    prompt_file_path: str,
    params: ReviewInputs,
    model_name: str,
    temperature: float,
) -> ReviewAnalysisOutput:
    if not model_name or temperature is None:
        error_msg = "ValueError: model_name and temperature must be provided."
        logger.error(error_msg)
        raise ValueError(error_msg)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "ValueError: OPENAI_API_KEY environment variable not set."
        logger.error(error_msg)
        raise ValueError(error_msg)

    param_field_keys = list(ReviewInputs.model_fields.keys()) if params else None
    logger.info(f"OpenAI call started: model='{model_name}', temperature={temperature}, prompt_file='{prompt_file_path}', input_param_fields={param_field_keys}")

    try:
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_template_str = f.read()
            logger.info(f"Prompt template loaded successfully: {prompt_file_path}")

        except FileNotFoundError:
            logger.error(f"FileNotFoundError: Prompt file not found: {prompt_file_path}")
            raise
        
        prompt_template = ChatPromptTemplate.from_template(prompt_template_str)

        llm = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            temperature=temperature,
        )
        logger.info(f"ChatOpenAI initialized: model='{model_name}', temperature={temperature}")

        structured_llm = llm.with_structured_output(ReviewAnalysisOutput)
        chain = prompt_template | structured_llm
        
        logger.info(f"Sending request to OpenAI LLM ({model_name})...")
        
        invoke_args = params.model_dump()
        
        # PydanticOutputParser를 사용하여 format_instructions 생성 및 주입
        format_instructions_str = output_parser.get_format_instructions()
        invoke_args["format_instructions"] = format_instructions_str 
        logger.debug(f"Generated format_instructions for OpenAI prompt (length: {len(format_instructions_str)})")
            
        response_pydantic = chain.invoke(invoke_args)
        logger.info(f"Response received from OpenAI LLM ({model_name}).")
        
        if isinstance(response_pydantic, ReviewAnalysisOutput):
             logger.info(f"LLM response successfully parsed to ReviewAnalysisOutput (model: {model_name}). Summary: {response_pydantic.summary}")
        else:
             logger.warning(f"LLM response is not of the expected ReviewAnalysisOutput type (model: {model_name}). Type: {type(response_pydantic)}")
        return response_pydantic

    except FileNotFoundError:
        raise
    except OutputParserException as e:
        error_msg = f"OpenAI response parsing failed (model: {model_name}): {e}. Input params: {params.model_dump_json(indent=2, ensure_ascii=False)}"
        logger.error(error_msg)
        raise
    except ValueError as e:
        logger.error(f"ValueError during OpenAI processing (model: {model_name}): {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during OpenAI model ({model_name}) call: {e}")
        raise 