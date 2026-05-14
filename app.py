import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import re
from rapidfuzz import fuzz

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Energy Drink Health Scanner",
    page_icon="🧾",
    layout="centered"
)

# =========================================================
# LOAD OCR MODEL
# =========================================================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])

reader = load_reader()

# =========================================================
# HEALTH DATABASE
# =========================================================
HEALTH_RULES = {

    "Sugar": {
        "aliases": [
            "sugar",
            "glucose",
            "fructose",
            "glucose-fructose",
            "sucrose",
            "corn syrup"
        ],

        "risk": "HIGH",

        "effects": [
            "Raises blood sugar rapidly",
            "Can contribute to obesity",
            "May worsen insulin resistance",
            "Can increase risk of tooth decay"
        ],

        "diseases": {
            "Diabetes": "May cause dangerous blood sugar spikes",
            "Obesity": "Adds excess calories",
            "Fatty Liver Disease": "High fructose intake may worsen liver fat"
        }
    },

    "Caffeine": {
        "aliases": [
            "caffeine"
        ],

        "risk": "MEDIUM",

        "effects": [
            "Can increase heart rate",
            "May cause anxiety",
            "Can disrupt sleep",
            "May increase blood pressure"
        ],

        "diseases": {
            "Hypertension": "May temporarily elevate blood pressure",
            "Anxiety Disorders": "Can worsen anxiety symptoms",
            "Heart Disease": "High intake may trigger palpitations"
        }
    },

    "Taurine": {
        "aliases": [
            "taurine"
        ],

        "risk": "LOW",

        "effects": [
            "Usually safe in moderation",
            "Often combined with stimulants"
        ],

        "diseases": {
            "Heart Conditions": "Large stimulant combinations should be monitored"
        }
    },

    "Artificial Flavoring": {
        "aliases": [
            "artificial flavor",
            "artificial flavours",
            "artificial flavoring",
            "artificial flavouring"
        ],

        "risk": "LOW",

        "effects": [
            "May contain synthetic compounds",
            "Some people report sensitivities"
        ],

        "diseases": {
            "Food Sensitivities": "May trigger reactions in sensitive individuals"
        }
    }
}

# =========================================================
# TEXT CLEANING
# =========================================================
def normalize_text(text):

    text = text.lower()

    text = re.sub(r'[^a-z0-9,\-\s]', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()

# =========================================================
# FUZZY OCR MATCH
# =========================================================
def fuzzy_contains(text, phrase, threshold=87):

    words = text.split()

    phrase_length = len(phrase.split())

    for i in range(len(words) - phrase_length + 1):

        chunk = " ".join(words[i:i + phrase_length])

        score = fuzz.ratio(chunk, phrase)

        if score >= threshold:
            return True

    return False

# =========================================================
# DETECT INGREDIENTS
# =========================================================
def detect_ingredients(text):

    detected = []

    for ingredient, data in HEALTH_RULES.items():

        found = False

        for alias in data["aliases"]:

            pattern = r'\b' + re.escape(alias) + r'\b'

            if re.search(pattern, text):
                found = True
                break

            if fuzzy_contains(text, alias):
                found = True
                break

        if found:

            detected.append({
                "ingredient": ingredient,
                "risk": data["risk"],
                "effects": data["effects"],
                "diseases": data["diseases"]
            })

    return detected

# =========================================================
# EXTRACT SUGAR AMOUNT
# =========================================================
def extract_sugar(text):

    patterns = [
        r'sugars?\s+(\d+)\s*g',
        r'sugar\s+(\d+)\s*g'
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:
            return int(match.group(1))

    return None

# =========================================================
# UI
# =========================================================
st.title("🧾 Energy Drink Health Scanner")

st.write("""
Upload a drink label image to analyze ingredients
and detect possible health concerns.
""")

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png"]
)

# =========================================================
# IMAGE PROCESSING
# =========================================================
if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(image, caption="Uploaded Label", use_container_width=True)

    img_array = np.array(image)

    with st.spinner("Scanning label with EasyOCR..."):

        results = reader.readtext(img_array, detail=0)

        extracted_text = " ".join(results)

        normalized_text = normalize_text(extracted_text)

    # =====================================================
    # OCR TEXT
    # =====================================================
    st.subheader("📄 Extracted Text")

    with st.expander("Show OCR Text"):
        st.write(extracted_text)

    # =====================================================
    # SUGAR ANALYSIS
    # =====================================================
    sugar = extract_sugar(normalized_text)

    if sugar is not None:

        st.subheader("🍬 Sugar Analysis")

        if sugar >= 25:

            st.error(f"High sugar detected: {sugar}g")

        elif sugar >= 10:

            st.warning(f"Moderate sugar detected: {sugar}g")

        else:

            st.success(f"Low sugar detected: {sugar}g")

    # =====================================================
    # INGREDIENT DETECTION
    # =====================================================
    st.subheader("⚠️ Ingredient Warnings")

    detected = detect_ingredients(normalized_text)

    if detected:

        for item in detected:

            if item["risk"] == "HIGH":
                st.error(f"🚨 {item['ingredient']}")

            elif item["risk"] == "MEDIUM":
                st.warning(f"⚠️ {item['ingredient']}")

            else:
                st.info(f"ℹ️ {item['ingredient']}")

            st.write("### Possible Effects")

            for effect in item["effects"]:
                st.write(f"- {effect}")

            st.write("### Disease Warnings")

            for disease, info in item["diseases"].items():
                st.write(f"- **{disease}** → {info}")

            st.divider()

    else:

        st.success("No concerning ingredients detected.")

    # =====================================================
    # OVERALL SUMMARY
    # =====================================================
    st.subheader("🩺 Overall Health Summary")

    if sugar and sugar >= 25:

        st.error("""
        This drink may be unhealthy for:
        - People with diabetes
        - People with obesity
        - People with insulin resistance
        """)

    st.info("""
    Occasional consumption is usually acceptable for
    healthy adults, but frequent intake of sugary
    energy drinks may increase health risks.
    """)
