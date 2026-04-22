import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import re

# Initialize OCR reader
reader = easyocr.Reader(['en'])

# Focused "flag for review" list (energy drink related)
FLAGGED_INGREDIENTS = {
    "aspartame": "Artificial sweetener (controversial in high intake)",
    "e951": "Aspartame (artificial sweetener)",

    "acesulfame k": "Artificial sweetener (Ace-K)",
    "e950": "Acesulfame K (artificial sweetener)",

    "sucralose": "Artificial sweetener",
    "e955": "Sucralose (artificial sweetener)",

    "sodium benzoate": "Preservative (can form benzene in rare conditions)",
    "e211": "Sodium Benzoate",

    "potassium sorbate": "Preservative",
    "e202": "Potassium Sorbate",

    "artificial flavor": "May include synthetic compounds",
    "artificial flavours": "May include synthetic compounds",

    "color": "Artificial coloring",
    "colour": "Artificial coloring",
    "e102": "Tartrazine (artificial dye)",
    "e110": "Sunset Yellow (artificial dye)",
    "e129": "Allura Red (artificial dye)"
}

def normalize_text(text):
    return text.lower()

def find_ingredients(text):
    found = []

    for key, description in FLAGGED_INGREDIENTS.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, text):
            found.append(f"{key.upper()} → {description}")

    return list(set(found))


# UI
st.title("🧾 Energy Drink Ingredient Scanner")
st.write("Detects controversial additives like artificial sweeteners and preservatives.")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    st.write("🔍 Extracting text...")
    img_array = np.array(image)

    results = reader.readtext(img_array, detail=0)
    extracted_text = " ".join(results)
    normalized_text = normalize_text(extracted_text)

    st.subheader("📄 Extracted Text")
    st.write(extracted_text)

    st.subheader("⚠️ Flagged Ingredients")

    found_items = find_ingredients(normalized_text)

    if found_items:
        for item in found_items:
            st.warning(item)
    else:
        st.success("No flagged ingredients detected.")
