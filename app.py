import streamlit as st
from PIL import Image
import io
import os

from agent import generate_prompt_spec, call_qwen_image, save_images, add_text_overlay

st.set_page_config(page_title="YouTube Thumbnail Generator", layout="centered")

st.title("🎨 YouTube Thumbnail Generator")
st.write("Generate stunning thumbnails with AI backgrounds and crisp text overlays!")

# Main form
with st.form("input_form"):
    st.subheader("📹 Video Details")
    title = st.text_input("Video title", value="How I Edited My iPhone Photos to Go Viral (Fast!)")
    keywords = st.text_input("Keywords (comma separated)", value="phone photography, editing, before after")
    audience = st.text_input("Target audience", value="beginner photographers, 18-35")
    style = st.text_input("Style / mood", value="bold, high-contrast, cinematic, dramatic lighting")
    
    st.subheader("✏️ Text Overlay")
    overlay_text = st.text_area(
        "Text to overlay (use Enter for new lines)", 
        value="GO VIRAL\nFAST!",
        height=100
    )
    col1, col2 = st.columns(2)
    with col1:
        font_size = st.slider("Font size", min_value=30, max_value=150, value=80, step=5)
    with col2:
        font_color = st.color_picker("Text color", value="#FFFFFF")
        stroke_color = st.color_picker("Outline color", value="#000000")
    stroke_width = st.slider("Outline thickness", min_value=0, max_value=10, value=4, step=1)

    # Fixed text position selectbox (center, top, bottom)
    text_position = st.selectbox("Text position", ["center", "top", "bottom"], index=0)

    # Live preview using add_text_overlay (centered preview)
    preview_width, preview_height = 640, 360
    preview_img = Image.new("RGBA", (preview_width, preview_height), (30, 30, 30, 255))
    preview_img_with_text = add_text_overlay(
        preview_img.copy(),
        overlay_text,
        position=text_position,
        font_size=font_size,
        font_color=font_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    )
    st.image(preview_img_with_text, caption="Live Font/Text Preview", use_column_width=False)

    st.subheader("🖼️ Image Settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        width = st.selectbox("Width", options=[1280, 1920, 1024, 640], index=0)
    with col2:
        height = st.selectbox("Height", options=[720, 1080, 576, 360], index=0)
    with col3:
        num_images = st.selectbox("Number of images", options=[1, 2, 3, 4], index=0)
    
    submitted = st.form_submit_button("🚀 Generate Thumbnails", use_container_width=True)

if submitted:
    # Step 1: Generate prompt (hidden from user)
    with st.spinner("🤖 AI is designing the perfect background..."):
        try:
            spec = generate_prompt_spec(title, keywords, audience, style)
            main_prompt = spec.get("main_prompt", "")
            if not main_prompt:
                st.error("Failed to generate thumbnail prompt. Please try again.")
                st.stop()
        except Exception as e:
            st.error(f"Error generating prompt: {e}")
            st.stop()
    
    # Step 2: Generate background images
    with st.spinner("🎨 Generating background images... This may take a moment."):
        try:
            images = call_qwen_image(main_prompt, width=width, height=height, num_images=num_images)
        except Exception as e:
            st.error(f"Image generation error: {e}")
            st.stop()
    
    # Step 3: Apply text overlay if text is provided
    if overlay_text.strip():
        with st.spinner("✏️ Adding text overlay..."):
            images_with_text = []
            for img in images:
                img_with_text = add_text_overlay(
                    img,
                    overlay_text,
                    position=text_position,
                    font_size=font_size,
                    font_color=font_color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width
                )
                images_with_text.append(img_with_text)
            images = images_with_text
    
    # Step 4: Save and display
    filepaths = save_images(images, prefix="yt_thumbnail")
    
    st.success(f"✅ Generated {len(images)} thumbnail(s)!")
    
    for i, (img, img_path) in enumerate(zip(images, filepaths)):
        st.image(img, caption=f"Thumbnail {i+1}", use_container_width=True)
        
        # Download button
        with open(img_path, "rb") as f:
            st.download_button(
                label=f"⬇️ Download Thumbnail {i+1}",
                data=f,
                file_name=os.path.basename(img_path),
                mime="image/png",
                key=f"download_{i}"
            )

st.markdown("---")
st.markdown("""
💡 **Tips:**
- Use short, punchy text for best results (2-4 words per line)
- Yellow (#FFFF00) and white (#FFFFFF) text work great for thumbnails
- Increase outline thickness for better readability on busy backgrounds
""")
