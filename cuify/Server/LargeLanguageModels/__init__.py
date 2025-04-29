from .Base import LLM
from .OpenAI import OpenAI_gpt
from .Google import Google
from .HuggingFace import HuggingFace

def getLargeLanguageModel(model_name, openai_api_key, google_api_key, stream=False):
    if model_name == "Local_base":
        return LLM()
    elif model_name == "OpenAI_gpt3_5_turbo":
        if openai_api_key is None:
            raise ValueError("OpenAI api key must be provided")
        return OpenAI_gpt(openai_api_key, stream=stream)
    elif model_name == "OpenAI_gpt4_turbo":
        if openai_api_key is None:
            raise ValueError("OpenAI api key must be provided")
        return OpenAI_gpt(openai_api_key, model="gpt-4-turbo", stream=stream)
    elif model_name == "OpenAI_gpt4o":
        if openai_api_key is None:
            raise ValueError("OpenAI api key must be provided")
        return OpenAI_gpt(openai_api_key, model="gpt-4o", stream=stream)
    elif model_name == "OpenAI_gpt4o_mini":
        if openai_api_key is None:
            raise ValueError("OpenAI api key must be provided")
        return OpenAI_gpt(openai_api_key, model="gpt-4o-mini", stream=stream)
    elif model_name == "Google_gemini":
        if google_api_key is None:
            raise ValueError("Google api key must be provided")
        return Google(google_api_key, stream=stream)
    elif "HuggingFace" in model_name:
        model_name = model_name.replace("HuggingFace_", "")
        return HuggingFace(model_name, stream=stream)
    else:
        raise ValueError(f"Model name {model_name} is not supported")