# YouTube Thumbnail Generator

Generate stunning YouTube thumbnails with AI-powered backgrounds and customizable text overlays using Streamlit and Hugging Face models.

## Features

- Generate thumbnail prompts using LangChain and Hugging Face LLMs
- Create backgrounds with Qwen-Image (Hugging Face Inference API)
- Add crisp, styled text overlays (font size, color, outline, position)
- Preview thumbnails before downloading
- Download generated thumbnails as PNG files

## Setup

1. **Clone this repository**  
   ```
   git clone <your-repo-url>
   cd thumbnail_generator
   ```

2. **Create and activate a virtual environment**  
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```
   pip install -r requirements.txt
   ```
   Or manually:
   ```
   pip install streamlit pillow requests python-dotenv langchain huggingface-hub
   ```

4. **Set environment variables**  
   Create a `.env` file in the project folder with:
   ```
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
   HF_INFERENCE_TOKEN=your_huggingface_token
   ```
   Replace `your_huggingface_token` with your Hugging Face API token.

## Usage

1. **Start the app**
   ```
   streamlit run app.py
   ```

2. **Fill in video details and text overlay options**
3. **Generate thumbnails and download your favorites**

## Troubleshooting

- **Missing API tokens:**  
  Ensure your `.env` file is present and contains valid Hugging Face tokens.

- **Font errors:**  
  Make sure the fonts listed in the app are available on your system or adjust the font list.

- **Image generation errors:**  
  Check your Hugging Face API quota and model availability.

## Customization

- To add more fonts, update the `FONT_OPTIONS` and `FONT_LABELS` in `app.py`.
- To change the AI model, update the model IDs in `agent.py`.

## License

MIT License

## Credits

- [Streamlit](https://streamlit.io/)
- [LangChain](https://langchain.com/)
- [Hugging Face](https://huggingface.co/)
