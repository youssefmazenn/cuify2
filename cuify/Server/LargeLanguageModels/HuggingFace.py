
import transformers
import torch
from threading import Thread
from .Base import LLM
from huggingface_hub import login
import os

class HuggingFace(LLM):
    def __init__(self, model_id = "meta-llama/Llama-3.2-1B", device_map='auto', stream=False):
        """
        Initializes the HuggingFace model with given configurations.

        Args:
            model_id (str): The ID of the model to use.
            quantization_config (transformers.BitsAndBytesConfig): Configuration for model quantization.
            device_map (str or dict): Device placement strategy for the model.

        Returns:
            None
        """

        login(os.environ["HF_TOKEN"])
        print("Logged in")
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
        # quantization_config = transformers.BitsAndBytesConfig(
        #     load_in_4bit=True,
        #     bnb_4bit_use_double_quant=True,
        #     bnb_4bit_quant_type="nf4",
        #     bnb_4bit_compute_dtype=torch.bfloat16
        # )
        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            # quantization_config=quantization_config,
            device_map=device_map
        )
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        #self.model.to(self.device)
        if device_map != "auto":
            self.model.to(self.device)
        self.stream = stream

    def streamer(self, streamer):
        print("streaming")
        model_output = ""
        for new_text in streamer:
            model_output += new_text
            yield model_output


    # def forward(self, text, history=[], preprompt="You are a helpful assistant.", npc_name="Assistant"):
    #     # Build manual prompt
    #     prompt = preprompt.strip() + "\n"
    #     for h in history:
    #         prompt += f"User: {h['user']}\n{npc_name}: {h['assistant']}\n"
    #     prompt += f"User: {text}\n{npc_name}:"
    #
    #     print(f"[HF] Final prompt sent to model:\n{prompt}")
    #
    #     # Tokenize
    #     encoded_inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
    #
    #     # Streaming or non-streaming
    #     if self.stream:
    #         streamer = transformers.TextIteratorStreamer(self.tokenizer, skip_special_tokens=True)
    #         generate_kwargs = dict(
    #             input_ids=encoded_inputs["input_ids"],
    #             streamer=streamer,
    #             max_new_tokens=512,
    #             do_sample=True,
    #             temperature=0.7,
    #             pad_token_id=self.tokenizer.eos_token_id
    #         )
    #         t = Thread(target=self.model.generate, kwargs=generate_kwargs)
    #         t.start()
    #         return self.streamer(streamer)
    #     else:
    #         output = self.model.generate(
    #             **encoded_inputs,
    #             max_new_tokens=512,
    #             do_sample=True,
    #             temperature=0.7,
    #             pad_token_id=self.tokenizer.eos_token_id
    #         )
    #         full_output = self.tokenizer.decode(output[0], skip_special_tokens=True)
    #         response = full_output.replace(prompt, "").strip()
    #         return response

    # Works with Meta Llama 3.2 but is slow
    """"
    This
    will
    work
    with all your HuggingFace models now — including:

    Llama
    3.2
    1
    B

    DeepSeek

    Mistral

    Any
    instruction - tuned
    model
    """

    def forward(self, text, history=[], preprompt="You are a helpful assistant.", npc_name="Assistant"):
        prompt = text  # Directly use the final_prompt sent from ClientListener

        print(f"[HF] Final prompt sent to model:\n{prompt}")

        encoded_inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output_ids = self.model.generate(
            **encoded_inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
            pad_token_id=self.tokenizer.eos_token_id
        )

        output_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

        response = output_text.replace(prompt, "").strip()

        # Step 1: Cut if model hallucinated [INST] User:
        if "[INST] User:" in response:
            response = response.split("[INST] User:")[0].strip()

        # Step 2: Cut if model hallucinated User:
        if "User:" in response:
            response = response.split("User:")[0].strip()

        # Step 3: Cut if model repeated multiple 'Joe:'
        joe_speaker = f"{npc_name}:"
        if response.count(joe_speaker) > 1:
            first_joe_index = response.find(joe_speaker)
            second_joe_index = response.find(joe_speaker, first_joe_index + len(joe_speaker))
            response = response[:second_joe_index].strip()

        # Step 4: Clean leftover [/INST] or junk
        response = response.replace('[/INST]', '').strip()

        return response

    # forward function for gemma3-1B
    # def forward(self, text, history=[], preprompt="You are a helpful assistant.", npc_name="Assistant"):
    #     # Format the prompt for instruction/chat-tuned models
    #     prompt = f"[INST] {preprompt.strip()} [/INST]\n"
    #     for h in history:
    #         prompt += f"[INST] User: {h['user']} [/INST] {npc_name}: {h['assistant']}\n"
    #     prompt += f"[INST] User: {text} [/INST] {npc_name}:"
    #
    #     print(f"[HF] Final prompt:\n{prompt}")
    #
    #     encoded_inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
    #
    #     model_output = self.model.generate(
    #         **encoded_inputs,
    #         max_new_tokens=512,
    #         do_sample=True,
    #         temperature=0.7,
    #         pad_token_id=self.tokenizer.eos_token_id
    #     )
    #
    #     response = self.tokenizer.decode(model_output[0], skip_special_tokens=True)
    #
    #     # Strip the prompt from the output
    #     if prompt in response:
    #         response = response.replace(prompt, "").strip()
    #
    #     # Cut off if model continues conversation by hallucinating [INST] User:
    #     if "[INST] User:" in response:
    #         response = response.split("[INST] User:")[0].strip()
    #     response = response.replace('[/INST]', '').strip()
    #
    #     return response
    #
