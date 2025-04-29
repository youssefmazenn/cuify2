import socket, threading
from ClientListener import client_listener
from argparse import ArgumentParser
import yaml
import os
from dotenv import dotenv_values
from SpeechToText import getSpeechToText
from TextToSpeech import getTextToSpeech
from LargeLanguageModels import getLargeLanguageModel
from OutputCapture import Capturing
from copy import deepcopy

class Config:
    def __init__(self, config_dict):
        self.config_dict = config_dict

    def __getattr__(self, name):
        if name in self.config_dict:
            return self.config_dict[name]
        else:
            return None
        
    def __deepcopy__(self, memo):
        return Config(self.config_dict)

def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="Configs/default.yaml", help="Path to the YAML configuration file")
    parser.add_argument("-cache_only", action="store_true", help="Only cache the models and exit")
    args = parser.parse_args()
    return args

def load_config(config_file):
    with open(config_file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            return config
        except yaml.YAMLError as exc:
            print(exc)
            return None
        
def LoadEnv(config):
    if config.api_key_path is not None:
        env_vars = dotenv_values(config.api_key_path)
        config.openai_api_key = env_vars.get("OPENAI_API_KEY", None)
        config.amazon_access_key_id = env_vars.get("Amazon_Access_Key_ID", None)
        config.amazon_secret_key = env_vars.get("Amazon_Secret_Access_Key", None)
        config.google_api_key = env_vars.get("Google_API_Key", None)

def Server(config):
    if config.api_key_path is not None:
        env_vars = dotenv_values(config.api_key_path)
        config.openai_api_key = env_vars.get("OPENAI_API_KEY", None)
        config.amazon_access_key_id = env_vars.get("Amazon_Access_Key_ID", None)
        config.amazon_secret_key = env_vars.get("Amazon_Secret_Access_Key", None)
        config.google_api_key = env_vars.get("Google_API_Key", None)

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((config.host, config.port))
    serversocket.listen(5)

    print(f"Server is listening on {config.host}:{config.port}")

    return serversocket, config

def ServerListener(server, config):
    while True:
        clientsocket, address = server.accept()
        print(f"Received connection from {address}")
        threading.Thread(target=client_listener, args=(clientsocket, address, deepcopy(config))).start()

def cacheModels(config):
    with Capturing() as output:
        STT = getSpeechToText(config.STT_model, config.openai_api_key, config.amazon_access_key_id, config.amazon_secret_key)
        LLM = getLargeLanguageModel(config.LLM_model, config.openai_api_key, config.google_api_key, config.stream)
        TTS = getTextToSpeech(config.TTS_model, config.openai_api_key, config.amazon_access_key_id, config.amazon_secret_key)

if __name__ == "__main__":
    args = parse_arguments()
    config = Config(load_config(args.config))
    os.makedirs("tmp", exist_ok=True)
    LoadEnv(config)
    if args.cache_only:
        cacheModels(config)
        exit()
    server, config = Server(config)
    ServerListener(server, config)
    