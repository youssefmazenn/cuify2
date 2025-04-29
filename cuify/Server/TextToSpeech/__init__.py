from .Amazon import Polly
from .OpenAI import OpenAI_tts
from .TransformersTTS import TransformersTTS

def getTextToSpeech(model_name, openai_api_key=None, amazon_access_key_id=None, amazon_secret_key=None, OpenAIVoice="alloy"):
    if model_name == "Amazon_polly":
        if amazon_access_key_id is None or amazon_secret_key is None:
            raise ValueError("Amazon access key id and secret key must be provided")
        return Polly(amazon_access_key_id, amazon_secret_key)
    elif model_name == "OpenAI_tts":
        if openai_api_key is None:
            raise ValueError("OpenAI api key must be provided")
        return OpenAI_tts(openai_api_key, voice=OpenAIVoice)
    elif model_name == "Local_TTS":
        return TransformersTTS()
    else:
        raise ValueError(f"Model name {model_name} is not supported")