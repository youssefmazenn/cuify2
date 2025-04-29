import time
import os
from SpeechToText import getSpeechToText
from TextToSpeech import getTextToSpeech
from LargeLanguageModels import getLargeLanguageModel
from OutputCapture import Capturing

import sys
sys.stdout.reconfigure(encoding='utf-8')

# YOUSSEF
# Global shared memory (used by ALL NPCs and user)
shared_memory = {
    "user": [],
    "Joe": [],
    "Megan": [],
    "Alex": [],
    "Christian": []
}

# 26/04
# Adding a global list to make the conversation more real and in the correct order
chat_turns = []  # Global ordered memory

def client_listener(connection, address, args):
    print(f"Connection from {address} has been established")
    client_log_folder = f"logs/{address[0]}_{address[1]}_{time.time()}"
    os.makedirs(client_log_folder, exist_ok=True)
    with open(f"{client_log_folder}/log.txt", "w") as f:
        f.write(f"Connection from {address} has been established at {time.time()}\n")
    
    client_config_lengths = int.from_bytes(connection.recv(4), byteorder='little')
    received = 0
    buf = b""
    while received < client_config_lengths:
        data = connection.recv(client_config_lengths-received)
        received += len(data)
        buf += data

    received_config = buf.decode("utf-8")
    model_names = buf.decode("utf-8").split(",")[0:3]
    api_keys = buf.decode("utf-8").split(",")[3:7]
    storeHistory = buf.decode("utf-8").split(",")[7]
    OpenAIVoice = buf.decode("utf-8").split(",")[8]
    npc_name = buf.decode("utf-8").split(",")[-1].strip()
    if OpenAIVoice not in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
        OpenAIVoice = "alloy"
    # preprompt = buf.decode("utf-8").split(",")[9:]
    # preprompt = " ".join(preprompt)
    # YOUSSEF 26/04
    # stripping the NPC name from the pre prompt tsince it's causing a problem
    preprompt_parts = buf.decode("utf-8").split(",")[9:-1]  # ✅ Skip the last 'npc_name'
    preprompt = " ".join(preprompt_parts).strip()
    print(f"Received config: {received_config}\nReceived model names: {model_names}\nReceived API keys: {api_keys}")
    print(f"Received NPC names: {npc_name}")



    if api_keys[0] != "":
        args.openai_api_key = api_keys[0]
    if api_keys[1] != "":
        args.amazon_access_key_id = api_keys[1]
    if api_keys[2] != "":
        args.amazon_secret_key = api_keys[2]
    if api_keys[3] != "":
        args.google_api_key = api_keys[3]
    
    print("**"*50)
    
    try:
        with Capturing() as output:
            STT = getSpeechToText(model_names[0], args.openai_api_key, args.amazon_access_key_id, args.amazon_secret_key)
            if "_stream" in model_names[1]:
                args.stream = True
                model_names[1] = model_names[1].replace("_stream", "")
            LLM = getLargeLanguageModel(model_names[1], args.openai_api_key, args.google_api_key, args.stream)
            TTS = getTextToSpeech(model_names[2], args.openai_api_key, args.amazon_access_key_id, args.amazon_secret_key, OpenAIVoice)
        connection.send("!OKK".encode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")
        connection.send("!ERR".encode("utf-8"))
        connection.close()
        return

    chat_history = []
    #all_history = [] # to store all the things being said by all the different models    Youssef



    lastPartFlag = 0
    while True:
        if lastPartFlag == 2:
            break
        lastPartFlag = 0
        receivedPart = 0
        received_text = ""
        while lastPartFlag == 0 and receivedPart < 100:
            try:
                messsage_length = int.from_bytes(connection.recv(4), byteorder='little')
                lastPartFlag = int.from_bytes(connection.recv(1), byteorder='little')
                received = 0
                receivedPart += 1
                buf = b""
                while received < messsage_length:
                    data = connection.recv(messsage_length-received)
                    received += len(data)
                    buf += data
                if buf is None or len(buf) == 0:
                    connection.close()
                    return
                with open(f"tmp/TTS_ex_server_input_{receivedPart}.wav", "wb") as f:
                    f.write(buf)
                start = time.time()
                with Capturing() as output:
                    received_text_part = STT.forward(buf).strip()
                received_text += received_text_part
                #all_history.append(received_text) #Youssef
                speech2text_time = time.time() - start
            except ConnectionResetError:
                print("Connection closed by client")
                connection.close()
                break

        # YOUSSEF
        shared_memory["user"].append(received_text)

        # 26/04
        chat_turns.append(("user", received_text))
        #shared_memory[npc_name].append(f"user asked: {received_text}")

        # Combine memory for full shared context
        memory_context = ""
        for speaker, lines in shared_memory.items():
            for line in lines:
                memory_context += f"{speaker}: {line}\n"

        memory_context_combined = ""
        for speaker, message in chat_turns:
            memory_context_combined += f"{speaker}: {message}\n"

        # Add user input to the end of the memory context
        # final_prompt = f"{memory_context}\n{npc_name}, respond to this: {received_text}"
        # print(f"Final prompt for {npc_name}:\n{final_prompt}")

        # YOUSSEF 24/04
        if "HuggingFace" in model_names[1]:
            final_prompt = (
                f"{preprompt.strip()}\n\n"  # ← two new lines (important)
                f"past conversation:\n{memory_context_combined}end of past conversation\n\n"
                #f"Answer the last question asked by the user.\nOnly reply as {npc_name}. Do not continue as the user\n\n"
                f"Continue the conversation naturally based on the last User message.\n"
                f"Only reply as {npc_name}.\n"
                f"Do not simulate the User.\n"
                f"Do not repeat your previous answers.\n"
                f"Focus on moving the conversation forward.\n"
                # f"User: {received_text.strip()}\n"
                f"{npc_name}:"
            )

            print(f"Final prompt for {npc_name}:\n{final_prompt}")
        else:
            # Use memory_context + LLM style prompt for other models
            final_prompt = f"{memory_context_combined}\n{npc_name}, respond to this: {received_text}"
            print(f"Final prompt for {npc_name}:\n{final_prompt}")

        # 👇 Pass the full prompt instead of just received_text

        # Large language model
        start = time.time()
        response_audio_path = "tmp/TTS_ex_server_output.wav"
        with Capturing() as output:
            #response_text_buffer = LLM.forward(received_text, chat_history, preprompt)
            if model_names[1].lower() == "google_gemini":
                response_text_buffer = LLM.forward(final_prompt, preprompt=preprompt)
            elif "HuggingFace" in model_names[1]:
                response_text_buffer = LLM.forward(final_prompt, chat_history, preprompt, npc_name=npc_name)
            else:
                response_text_buffer = LLM.forward(final_prompt, chat_history, preprompt)

        response_text = "" if args.stream else response_text_buffer
        gpt_time = time.time() - start
        if args.stream:
            buffer = []
            for chunk in response_text_buffer:
                content = chunk.choices[0].delta.content
                if content is not None and len(content) > 0:
                    buffer.append(content)
                    if buffer[-1] in [".", "!", "?"]:
                        response_text_part = "".join(buffer)
                        start = time.time()
                        with Capturing() as output:
                            TTS.forward_to_file(response_text_part, response_audio_path)
                        response_text += response_text_part
                        # YOUSSEF
                        #shared_memory[npc_name].append(response_text)

                        response_audio = open(response_audio_path, "rb").read()
                        text2speech_time = time.time() - start
                        lastPartFlag = 0
                        response_audio = len(response_audio).to_bytes(4, byteorder='little') + lastPartFlag.to_bytes(1, byteorder='little') + response_audio
                        connection.send(response_audio)
                        connection.send(response_text.encode("utf-8"))  # added by youssef
                        #all_history.append(response_text)  # Youssef


                        buffer = []
            if len(buffer) > 0:
                response_text_part = "".join(buffer)
                start = time.time()
                with Capturing() as output:
                    TTS.forward_to_file(response_text_part, response_audio_path)
                response_text += response_text_part
                # YOUSSEF
                #shared_memory[npc_name].append(response_text)

                response_audio = open(response_audio_path, "rb").read()
                text2speech_time = time.time() - start
                lastPartFlag = 1
                response_audio = len(response_audio).to_bytes(4, byteorder='little') + lastPartFlag.to_bytes(1, byteorder='little') + response_audio
                connection.send(response_audio)
                connection.send(response_text.encode("utf-8"))  # added by youssef

            else:
                lastPartFlag = 1
                response_audio = []
                response_audio = len(response_audio).to_bytes(4, byteorder='little') + lastPartFlag.to_bytes(1, byteorder='little')
                connection.send(response_audio)
                connection.send(response_text.encode("utf-8"))  # added by youssef


            print(shared_memory)
            # 26/04
            print(chat_turns)
            # YOUSSEF 24/04
            print(f"[AUDIO] Generated WAV size: {os.path.getsize(response_audio_path)} bytes")
            print(f"[SEND] Sending {len(response_audio)} bytes to Unity")
        else:
            # Text to speech
            start = time.time()
            with Capturing() as output:
                TTS.forward_to_file(response_text, response_audio_path)
            response_audio = open(response_audio_path, "rb").read()
            # response_audio = TTS.forward(response_text)
            text2speech_time = time.time() - start
            response_audio = len(response_audio).to_bytes(4, byteorder='little') + response_audio
            #connection.send(response_audio)
            # Send plain response text right after audio
            #connection.send(response_text.encode("utf-8"))

            # try:
            #     connection.send(response_text.encode("utf-8"))  # ✅ NEW LINE
            # except Exception as e:
            #     print(f"[ERROR] Failed to send response text: {e}")
            try:
                connection.send(response_audio)
                time.sleep(0.05)  # ⏱ short delay to avoid packet mixing
                connection.send(response_text.encode("utf-8"))  # text second
            except OSError as e:
                print(f"[ERROR] Failed to send audio: {e}")

            # YOUSSEF 24/04
            ##################################################################
            print(f"[AUDIO] Generated WAV size: {os.path.getsize(response_audio_path)} bytes")
            print(f"[SEND] Sending {len(response_audio)} bytes to Unity")

            # Optional: Save a debug copy to check manually
            with open("debug_output.wav", "wb") as f:
                f.write(response_audio[4:])

            #########################################################
        # YOUSSEF
        # add the response text of the certain NPC that is talking
        shared_memory[npc_name].append(response_text)
        #26/04
        chat_turns.append((npc_name, response_text))

        if not (storeHistory == "nostore"):
            chat_history.append({"user": received_text, "assistant": response_text})

        # append the logs
        with open(f"{client_log_folder}/log.txt", "a") as f:
            f.write("-" * 50 + "\n")
            f.write(f"Received config: {received_config}\n")
            f.write(f"Received audio length: {len(response_audio)}\n")
            f.write(f"Speech2Text time: {speech2text_time} seconds\n")
            f.write(f"Received text: {received_text}\n")
            f.write(f"GPT time: {gpt_time} seconds\n")
            f.write(f"Response text: {response_text}\n")
            f.write(f"Text2Speech time: {text2speech_time} seconds\n")
            f.write(f"dictionary of each person with everything they said: {shared_memory}\n")
            f.write(f"whole conversation with the correct order: {chat_turns}\n")
            # YOUSSEF
            f.write("-" * 50 + "\n")

        # if args.verbose:
        #     print("-" * 50)
        #     print(f"Received text: {received_text}")
        #     if args.stream:
        #         print(f"Received text parts: {response_text_part}")
        #     else:
        #         print(f"Response text: {response_text}")
        #     print(response_text)
        #     print(f"Speech2Text time: {speech2text_time} seconds, GPT time: {gpt_time} seconds, Text2Speech time: {text2speech_time} seconds")
        #     print("-" * 50)
        print("-" * 50)
        print(f"Received text: {received_text}")
        print(f"Response text: {response_text}")
        print(
            f"Speech2Text time: {speech2text_time} seconds, GPT time: {gpt_time} seconds, Text2Speech time: {text2speech_time} seconds")
        print(shared_memory)
        print(chat_turns)
        print("-" * 50)


        # send audio data to client
        time.sleep(0.01)