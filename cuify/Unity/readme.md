## Client Unity Application

This Unity application facilitates communication with a Python server for various natural language processing (NLP) tasks, including speech-to-text (STT), text-to-speech (TTS), and interaction with large language models (LLM).

### Prerequisites

- Unity Engine

### Installation

1. Clone this repository to your local machine.

2. Open the Unity project in the Unity Editor. Install the CUIfy unity package, or download scripts from CUIfy folder.

3. Ensure that the Python server is running and properly configured.

### Configuration

The client application can be configured directly within the Unity Inspector. Key configurations include:

- **Text-to-Speech Models**: Choose from available models such as Coqui, Vits, Amazon Polly, or OpenAI TTS.
- **Large Language Models (LLM)**: Select the desired LLM model, including options like OpenAI GPT-3.5 Turbo, Google Gemini, or custom HuggingFace models.
- **Speech-to-Text Models**: Choose from available STT models such as Transformers, OpenAI Whisper, or Amazon Transcribe.
- **Preprompt**: Optionally provide a pre-prompt message.
- **Server IP and Port**: Specify the IP address and port of the Python server.
- **API Keys**: If required by the models used, provide API keys for OpenAI and Amazon services.
- **Record Time**: Set the duration for recording audio (in seconds).
- **Store History**: Enable or disable the history of LLM.

### Usage

1. Launch the Unity application.

2. Interact with the application using the Unity Editor's Play mode or by building and running the standalone application.

3. Press the designated key (e.g., Space) to start and stop recording audio. The recorded audio will be sent to the Python server for processing.

### Functionality

- **Socket Communication**: Establishes a TCP socket connection with the Python server for data exchange.
- **Recording**: Allows users to record audio input.
- **Model Interaction**: Communicates with the Python server to utilize various NLP models for processing audio data.

### Notes

- Ensure that the Python server is properly configured and running before using the client application.
- Debug logs within the Unity Editor provide information about the communication with the Python server and the processing of audio data.
