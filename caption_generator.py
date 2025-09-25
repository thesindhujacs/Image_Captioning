import base64
import os
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# -------------------- CONFIG --------------------
API_KEY = "KEY"  # replace with your OpenAI key
IMAGE_FOLDER = "images"   # folder containing input images
OUTPUT_FOLDER = "captioned_images"  # folder to save captioned images
FONT_PATH = "C:/Windows/Fonts/seguiemj.ttf"  # Windows emoji-capable font
FONT_SIZE = 40
LINE_SPACING = 10  # pixels between lines
MARGIN = 20       # side margin for text
# ------------------------------------------------

client = OpenAI(api_key=API_KEY)

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_caption(image_path):
    base64_image = encode_image(image_path)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "Generate a short fun caption for this image (emojis allowed)."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
    )
    return response.choices[0].message.content

def wrap_text(draw, text, font, max_width):
    """Wrap text so it fits within max_width in pixels"""
    words = text.split()
    lines = []
    for word in words:
        if not lines:
            lines.append(word)
        else:
            test_line = lines[-1] + " " + word
            bbox = draw.textbbox((0,0), test_line, font=font)
            if bbox[2] > max_width:
                lines.append(word)
            else:
                lines[-1] = test_line
    return lines

def add_caption_below(image_path, caption, output_path):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        font = ImageFont.load_default()
        print("⚠️ Warning: Could not load emoji font, emojis may not render.")

    # Wrap text dynamically
    max_text_width = img.width - 2*MARGIN
    lines = wrap_text(draw, caption, font, max_text_width)

    # Calculate total caption height
    bbox = draw.textbbox((0,0), "A", font=font)
    line_height = bbox[3] - bbox[1]
    total_text_height = line_height * len(lines) + LINE_SPACING * (len(lines)-1) + MARGIN

    # Create new image with extra padding for caption
    new_height = img.height + total_text_height
    new_img = Image.new("RGB", (img.width, new_height), "white")
    new_img.paste(img, (0,0))
    draw = ImageDraw.Draw(new_img)

    # Draw each line centered
    y_text = img.height + MARGIN // 2
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x_text = (img.width - text_width) / 2
        draw.text((x_text, y_text), line, font=font, fill="black")
        y_text += line_height + LINE_SPACING

    # Save image
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    new_img.save(output_path)
    print(f"✅ Caption added: {output_path}")

if __name__ == "__main__":
    supported_ext = (".jpg", ".jpeg", ".png")
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(supported_ext)]

    for img_file in image_files:
        img_path = os.path.join(IMAGE_FOLDER, img_file)
        print(f"🖼 Processing {img_file} ...")
        caption = generate_caption(img_path)
        print(f"Generated Caption: {caption}")

        output_file = os.path.join(OUTPUT_FOLDER, f"captioned_{img_file}")
        add_caption_below(img_path, caption, output_file)
