# agent.py
"""
LangChain-based thumbnail prompt generator (Hugging Face text LLM)
and Qwen-Image caller (Hugging Face Inference API).

Install requirements:
pip install langchain huggingface-hub requests python-dotenv pillow

Environment variables required:
- HUGGINGFACEHUB_API_TOKEN  (for LangChain HuggingFaceHub LLM)
- HF_INFERENCE_TOKEN        (for calling the Hugging Face inference API for Qwen-Image)
"""

import os
import json
import time
import base64
from io import BytesIO
from typing import List, Dict, Tuple
from PIL import Image
import requests
from dotenv import load_dotenv

# LangChain imports
try:
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_huggingface import HuggingFaceEndpoint
except ImportError as e:
    raise ImportError(
        "LangChain components could not be imported. "
        "Please install the required packages:\n"
        "pip install langchain langchain-core langchain-huggingface huggingface-hub requests python-dotenv pillow\n"
        f"Original error: {e}"
    )

load_dotenv()

# --- Config: change these if you want other models ---
# Text LLM on Hugging Face (use a chat model that works with serverless inference)
HF_TEXT_MODEL = os.getenv("HF_TEXT_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
# Image model id (Qwen image)
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "Qwen/Qwen-Image")  # used only in the inference API URL

# Tokens
# The HuggingFaceEndpoint uses the same token for both the LLM and the image generation API.
# It typically reads from the HF_TOKEN or HUGGINGFACEHUB_API_TOKEN environment variables.
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN") or os.getenv("HF_INFERENCE_TOKEN")
if not HF_TOKEN:
    raise EnvironmentError("Set HUGGINGFACEHUB_API_TOKEN or HF_TOKEN in environment for Hugging Face APIs.")

# Instantiate a ChatHuggingFace LLM for chat-based inference
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

# First create the endpoint
llm_endpoint = HuggingFaceEndpoint(
    repo_id=HF_TEXT_MODEL,
    huggingfacehub_api_token=HF_TOKEN,
    temperature=0.7,
    max_new_tokens=512,
    task="text-generation",
)

# Wrap it with ChatHuggingFace for chat-based completions
llm = ChatHuggingFace(llm=llm_endpoint)

# Create output parser for the chain
output_parser = StrOutputParser()

# Prompt template: produce JSON output with main prompt + variations
# Focused on BACKGROUND and COMPOSITION only - text will be added as overlay
THUMBNAIL_PROMPT_TEMPLATE = """You are an expert YouTube thumbnail designer and prompt engineer.
Given the video title, keywords, audience and style, produce a vivid text-to-image prompt for a BACKGROUND IMAGE only.

CRITICAL RULES:
- Focus ONLY on background, composition, colors, lighting, and visual elements
- DO NOT include any text, words, letters, typography, or captions in the prompt
- Create eye-catching visuals that would work well behind overlay text
- Suggest dramatic lighting, bold colors, and engaging compositions

Output must be valid JSON exactly in the format:
{{
  "main_prompt": "<background image prompt here - NO TEXT>",
  "variations": ["variation 1", "variation 2", "variation 3"]
}}

DO NOT output anything else.
Title: {title}
Keywords: {keywords}
Audience: {audience}
Style / mood: {style}
"""

prompt_template = PromptTemplate(
    input_variables=["title", "keywords", "audience", "style"],
    template=THUMBNAIL_PROMPT_TEMPLATE
)

# Modern LCEL chain (replaces deprecated LLMChain)
chain = prompt_template | llm | output_parser


def generate_prompt_spec(title: str, keywords: str, audience: str, style: str) -> Dict:
    """
    Run the LangChain LLM to create a JSON spec containing main_prompt + variations.
    Returns dict with keys "main_prompt" and "variations".
    """
    raw = chain.invoke({
        "title": title,
        "keywords": keywords,
        "audience": audience,
        "style": style
    })

    # Attempt to parse JSON from the LLM output robustly
    try:
        parsed = json.loads(raw)
        # Ensure keys exist
        if "main_prompt" in parsed and "variations" in parsed:
            return parsed
    except Exception:
        # best-effort extraction of JSON substring
        try:
            jtext = raw[raw.index("{"): raw.rindex("}")+1]
            parsed = json.loads(jtext)
            return parsed
        except Exception:
            # fallback: return minimal spec
            return {"main_prompt": raw.strip(), "variations": []}
    return parsed


# -------------- Image Generation (HuggingFace Inference API) --------------
from huggingface_hub import InferenceClient

# Use FLUX.1-dev which is available on HuggingFace's free serverless inference API
HF_IMAGE_MODEL_ACTUAL = "black-forest-labs/FLUX.1-dev"

# Create inference client
inference_client = InferenceClient(token=HF_TOKEN)


def call_qwen_image(prompt: str, width: int = 1280, height: int = 720, num_images: int = 1, timeout: int = 120) -> List[Image.Image]:
    """
    Generate images using HuggingFace Inference API with FLUX model.
    Returns a list of PIL.Image objects.
    """
    images = []
    
    for i in range(num_images):
        try:
            # Generate image using the inference client
            image = inference_client.text_to_image(
                prompt=prompt,
                model=HF_IMAGE_MODEL_ACTUAL,
                width=width,
                height=height,
            )
            # Convert to RGBA for consistency
            images.append(image.convert("RGBA"))
        except Exception as e:
            raise RuntimeError(f"Image generation failed: {e}")
    
    if len(images) == 0:
        raise RuntimeError("No images were generated")
    
    return images


def add_text_overlay(
    image: Image.Image,
    text: str,
    position: str = "center",  # "top", "center", "bottom"
    font_size: int = 60,
    font_color: str = "#FFFFFF",
    stroke_color: str = "#000000",
    stroke_width: int = 3,
) -> Image.Image:
    """
    Add clean, crisp text overlay on an image.
    
    Args:
        image: PIL Image to add text to
        text: Text to overlay
        position: Where to place text - "top", "center", or "bottom"
        font_size: Size of the font
        font_color: Hex color for the text (e.g., "#FFFFFF" for white)
        stroke_color: Hex color for the text outline/stroke
        stroke_width: Width of the stroke (0 for no stroke)
    
    Returns:
        PIL Image with text overlay
    """
    from PIL import ImageDraw, ImageFont
    
    # Create a copy to avoid modifying original
    img = image.copy()
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default
    try:
        # Try common system fonts
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",  # Windows Impact (great for thumbnails)
            "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
            "C:/Windows/Fonts/arial.ttf",   # Windows Arial
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
        ]
        font = None
        for fp in font_paths:
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Get image dimensions
    img_width, img_height = img.size
    
    # Split text into lines if it contains newlines
    lines = text.split('\n')
    
    # Calculate total text height
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])
    
    total_height = sum(line_heights) + (len(lines) - 1) * 10  # 10px line spacing
    max_width = max(line_widths) if line_widths else 0
    
    # Calculate starting Y position based on position parameter
    if position == "top":
        y = 30
    elif position == "bottom":
        y = img_height - total_height - 30
    else:  # center
        y = (img_height - total_height) // 2
    
    # Draw each line
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        
        # Center horizontally
        x = (img_width - line_width) // 2
        
        # Draw stroke/outline if specified
        if stroke_width > 0:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font, fill=stroke_color)
        
        # Draw main text
        draw.text((x, y), line, font=font, fill=font_color)
        
        y += line_height + 10  # Move to next line
    
    return img


def save_images(images: List[Image.Image], prefix: str = "yt_thumb") -> List[str]:
    """Save images to current folder and return file paths."""
    out_files = []
    ts = int(time.time())
    for i, img in enumerate(images):
        fname = f"{prefix}_{ts}_{i+1}.png"
        img.save(fname, format="PNG")
        out_files.append(fname)
    return out_files


# If module is run directly, demonstrate a small example (won't run in Streamlit import)
if __name__ == "__main__":
    # quick test (replace with your inputs)
    title = "How I Edited My iPhone Photos to Go Viral (Fast!)"
    keywords = "phone photography, night shots, before after, editing tricks"
    audience = "beginner photographers, YouTube viewers 18-35"
    style = "bold, high-contrast, cinematic, close-up face with big reaction"

    spec = generate_prompt_spec(title, keywords, audience, style)
    print("Spec:", spec)
