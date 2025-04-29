# Python Server for Speech and Language Processing

This Python server integrates multiple speech and language processing models including speech-to-text (STT), large language models (LLM), and text-to-speech (TTS). It is designed to handle requests over a network and utilize environment-specific API keys for various services.

## Features

- **Speech-to-Text Conversion:** Utilizes speech recognition models to convert audio input to text.
- **Text-to-Speech Synthesis:** Implements text-to-speech models to convert text input to audio.
- **Large Language Model Integration:** Supports models like OpenAI's GPT-3.5 Turbo for processing natural language.
- **Dynamic Configuration:** Configurable through a YAML file for easy adaptation to different environments and use cases.

## Getting Started

### Prerequisites

- Python 3.x
- Required packages (install using `pip install -r requirements.txt`)
- API keys for the services you want to use (e.g., OpenAI, Google, etc.)
- HuggingFace Access Token (if using private Hugging Face repositories)

### Installation

1. Clone the repository:
   ```bash
   git clone git@gitlab.lrz.de:hctl/cuify.git
    ```
2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3. Setup FFmpeg:

    •	If conda is installed, run the following command:
      ```bash
      conda install ffmpeg
      ```

    •	Otherwise, follow these steps:
      ```bash
      - Download the latest version of ffmpeg from https://ffmpeg.org/download.html.
      - Extract the downloaded file and add the `bin` folder to the system path.
    ```  
     
    •	Verify the installation by running `ffmpeg -version` in the terminal.
    
4. Create a `.env` file in this folder and add your API keys:
    ```bash
    OPENAI_API_KEY=your_OpenAI_API_key
    Amazon_Access_Key_ID=your_Amazon_Access_Key_ID
    Amazon_Secret_Access_Key=your_Amazon_Secret_Access_Key
    Google_API_Key=your_Google_API_Key
    ```
    
5.	(Optional) Configure Hugging Face Access Token: If using Hugging Face private repositories, set the HF_TOKEN environment variable with your Hugging Face user access token.

	•	Windows:
      ```bash
      setx HF_TOKEN "your_HuggingFace_Access_Token"
      ```
	•	macOS and Linux:
      ```bash
      export HF_TOKEN="your_HuggingFace_Access_Token"
      ```
      
6. Run the server:
    ```bash
    python server.py
    ```

## Docker Support

You can also run the server using Docker. First create a `.env` file in the Server folder:

```bash
OPENAI_API_KEY=your_OpenAI_API_key
Amazon_Access_Key_ID=your_Amazon_Access_Key_ID
Amazon_Secret_Access_Key=your_Amazon_Secret_Access_Key
Google_API_Key=your_Google_API_Key
```

Then to build the Docker image, run following command on the parent directory (If CUDA is available on the system, use the DockerFileWithCUDA instead):

```bash
docker build -f DockerFile -t speech-and-language-server .
```

To run the Docker container, use:

```bash
docker run -it -p 9999:9999 speech-and-language-server
```
