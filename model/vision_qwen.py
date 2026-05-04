import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image

from model.prompts import build_messages


class VisionModel:
    """
    Qwen2-VL wrapper using inference-time instruction tuning.

    See `model/prompts.py` for the system prompt, output schema, and
    few-shot example that "tune" this base model into a safety analyst
    without any gradient updates.
    """

    def __init__(self):
        self.model_id = "Qwen/Qwen2-VL-2B-Instruct"

        print("Loading Qwen Vision Model...")

        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_id,
            device_map="auto",
        )

        self.processor = AutoProcessor.from_pretrained(self.model_id)

        print("Vision model ready")

    def analyze_image(self, image_path: str) -> str:
        image = Image.open(image_path).convert("RGB")

        # Instruction-tuned messages: system role + few-shot + image
        messages = build_messages()

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt",
        ).to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=300,
                do_sample=False,
            )

        # Strip the prompt tokens so we only decode the assistant's reply
        input_len = inputs["input_ids"].shape[1]
        new_tokens = output_ids[:, input_len:]

        result = self.processor.batch_decode(
            new_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )[0]

        return result.strip()
