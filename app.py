import streamlit as st
import easyocr
from PIL import Image
import numpy as np

# Initialize OCR reader (English + optionally add more languages)
reader = easyocr.Reader(['en'])

# List of additives to flag
UNHEALTHY_ADDITIVES = {
    "E621": "Monosodium Glutamate (MSG)",
    "E211": "Sodium Benzoate",
    "E250": "Sodium Nitrite",
    "E951": "Aspartame",
    "E102": "Tartrazine"
}

st.title("🧾 Food Label Scanner")
st.write("Upload an image of ingredients to detect potentially harmful additives.")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    st.write("🔍 Extracting text...")

    # Convert image to numpy array
    img_array = np.array(image)

    # OCR processing
    results = reader.readtext(img_array, detail=0)
    extracted_text = " ".join(results)

    st.subheader("📄 Extracted Text")
    st.write(extracted_text)

    # Check for additives
    found_additives = []

    for code, name in UNHEALTHY_ADDITIVES.items():
        if code.lower() in extracted_text.lower():
            found_additives.append(f"{code} - {name}")

    st.subheader("⚠️ Detected Additives")

    if found_additives:
        for additive in found_additives:
            st.warning(additive)
    else:
        st.success("No flagged additives detected.")
