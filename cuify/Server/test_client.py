import socket
import time
import struct
from pydub import AudioSegment

# Adjust to your backend settings
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9999

# Dummy configuration matching the backend's expected setup string
# STT, LLM, TTS, API keys, store/nostore, voice, preprompt
config = "OpenAI_whisper,OpenAI_gpt4o,OpenAI_tts,dummy_openai,dummy_aws,dummy_secret,dummy_google,store,alloy,Test prompt"
config_bytes = config.encode('utf-8')
length = len(config_bytes)



# Convert MP3 to WAV
mp3_audio = AudioSegment.from_mp3("sample.mp3")
mp3_audio.export("sample.wav", format="wav")

# Load a valid short WAV file
with open("sample.mp3", "rb") as f:  # 🔁 Make sure you include a sample .wav file in your directory!
    audio_data = f.read()
try:
    print(f"🔌 Connecting to {SERVER_IP}:{SERVER_PORT}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))

    # Step 1: Send config
    sock.send(struct.pack('<I', length))
    sock.send(config_bytes)
    print("✅ Sent config.")

    # Step 2: Wait for confirmation
    result = sock.recv(4)
    print(f"🧠 Backend reply: {result.decode()}")

    # Step 3: Send audio
    audio_length = len(audio_data)
    sock.send(struct.pack('<I', audio_length))      # Length
    sock.send(struct.pack('B', 1))                  # Final flag
    sock.send(audio_data)                           # Audio

    print("📤 Sent audio data to server.")

    # Step 4: Receive audio response
    response_len_bytes = sock.recv(4)
    response_len = struct.unpack('<I', response_len_bytes)[0]
    print(f"🎧 Expecting audio response length: {response_len} bytes")

    response_audio = b""
    while len(response_audio) < response_len:
        response_audio += sock.recv(min(4096, response_len - len(response_audio)))

    print(f"🎉 Received {len(response_audio)} bytes of response audio.")

    # Save to verify
    with open("test_response.wav", "wb") as out:
        out.write(response_audio)
    print("💾 Saved test_response.wav")

    # Step 5: Receive optional text (if your backend sends it)
    try:
        sock.settimeout(1)
        text = sock.recv(4096).decode('utf-8').strip()
        print(f"📝 LLM response text: {text}")
    except:
        print("🟡 No LLM text received.")

    sock.close()

except Exception as e:
    print(f"❌ Error: {e}")
