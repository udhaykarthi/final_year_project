import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image

class VisionModel:

    def __init__(self):
        self.model_id = "Qwen/Qwen2-VL-2B-Instruct"

        print("Loading Qwen Vision Model...")

        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_id,
            device_map="auto"
        )

        self.processor = AutoProcessor.from_pretrained(self.model_id)

        print("Vision model ready")

    def analyze_image(self, image_path):

        image = Image.open(image_path)

        messages = [{
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "Describe the scene and list objects."}
            ]
        }]

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt"
        ).to(self.model.device)

        output = self.model.generate(
            **inputs,
            max_new_tokens=120
        )

        result = self.processor.batch_decode(
            output,
            skip_special_tokens=True
        )[0]

        return result