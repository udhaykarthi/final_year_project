"""
Instruction-tuned prompts for the Qwen2-VL vision-language model.

What is "instruction tuning" here?
----------------------------------
True instruction fine-tuning (gradient updates on the model weights with
domain-specific input/output pairs) is impractical for a 2B-parameter VLM in
this project. Instead we apply *inference-time* instruction tuning, which is
a well-established technique:

  1. A carefully written **system message** that pins the model into a
     specific role and behaviour (a safety analyst).
  2. **Output schema constraints** so every reply is parseable and useful for
     the downstream rule engines.
  3. **Few-shot examples** that demonstrate the exact format we expect.

This is how production LLM apps "tune" a base model for a task without any
training. The prompts live here so they can be iterated on independently of
the model wrapper.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. System role
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are Rov-E, a safety-focused vision analyst embedded in a "
    "surveillance rover. For every image you receive, produce a precise, "
    "factual report. Never invent objects you cannot see. Be concise but "
    "specific. Pay special attention to safety hazards: weapons (knife, "
    "gun, blade), fire and smoke, falls or people lying on the floor, "
    "crowds (3+ people), unattended bags, and obvious medical "
    "emergencies."
)

# ---------------------------------------------------------------------------
# 2. Output schema (we ask for plain text with fixed sections)
# ---------------------------------------------------------------------------
USER_INSTRUCTION = (
    "Analyze this image and reply using EXACTLY the following sections, "
    "in this order, with these headers:\n"
    "Scene: <one sentence describing the overall environment>\n"
    "People: <count and brief description, or 'none'>\n"
    "Objects: <comma-separated list of clearly visible objects>\n"
    "Hazards: <comma-separated list of safety hazards, or 'none'>\n"
    "Risk: <low | medium | high>\n"
    "Notes: <one sentence with anything else worth flagging, or 'none'>"
)

# ---------------------------------------------------------------------------
# 3. Few-shot exemplar (text only — used to anchor the format)
# ---------------------------------------------------------------------------
FEW_SHOT_EXAMPLE_USER = (
    "Example image (described): An office hallway with two people walking "
    "and a backpack on the floor."
)

FEW_SHOT_EXAMPLE_ASSISTANT = (
    "Scene: An indoor office hallway with fluorescent lighting.\n"
    "People: 2 adults walking away from the camera.\n"
    "Objects: backpack, doors, ceiling lights, floor tiles\n"
    "Hazards: unattended_bag\n"
    "Risk: medium\n"
    "Notes: The backpack is several meters from both people."
)


def build_messages():
    """
    Build the chat-template messages that go to Qwen2-VL.

    The current image is attached to the FINAL user turn so the model
    grounds its answer on it (the few-shot example is text-only).
    """
    return [
        {
            "role": "system",
            "content": [{"type": "text", "text": SYSTEM_PROMPT}],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": FEW_SHOT_EXAMPLE_USER}],
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": FEW_SHOT_EXAMPLE_ASSISTANT}],
        },
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": USER_INSTRUCTION},
            ],
        },
    ]

