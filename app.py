import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import re
from rapidfuzz import fuzz

# =========================================================
# OCR MODEL
# =========================================================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])

reader = load_reader()

# =========================================================
# INGREDIENT / NUTRITION DATABASE
# =========================================================
# Focused on energy drinks like Red Bull

HEALTH_RULES = {

    "sugar": {
        "aliases": [
            "sugar",
            "glucose",
            "fructose",
            "glucose-fructose",
            "sucrose",
            "corn syrup"
        ],

        "risk_level": "HIGH",

        "harm": [
            "Raises blood sugar rapidly",
            "Can worsen insulin resistance",
            "Contributes to weight gain",
            "Increases risk of tooth decay"
        ],

        "conditions": {
            "Diabetes": "Can cause dangerous blood sugar spikes",
            "Obesity": "Adds excess calories with low satiety",
            "Fatty Liver Disease": "High fructose intake may worsen liver fat accumulation"
        }
    },

    "caffeine": {
        "aliases": [
            "caffeine"
        ],

        "risk_level": "MEDIUM",

        "harm": [
            "Can increase heart rate",
            "May cause anxiety or jitters",
            "Can disrupt sleep",
            "May increase blood pressure temporarily"
        ],

        "conditions": {
            "High Blood Pressure": "May temporarily elevate blood pressure",
            "Anxiety Disorders": "Can worsen nervousness and panic symptoms",
            "Heart Conditions": "High stimulant intake may trigger palpitations"
        }
    },

    "taurine": {
        "aliases": [
            "taurine"
        ],

        "risk_level": "LOW",

        "harm": [
            "Usually safe in moderation",
            "Combined with caffeine may intensify stimulant effects"
        ],

        "conditions": {
            "Heart Conditions": "Large stimulant combinations should be monitored"
        }
    },

    "artificial flavoring": {
        "aliases": [
            "artificial flavor",
            "artificial flavours",
            "artificial flavoring",
            "artificial flavouring"
        ],

        "risk_level": "LOW",

        "harm": [
            "May contain synthetic compounds",
            "Some individuals report sensitivities"
        ],

        "conditions": {
            "Food Sensitivities": "May trigger reactions in sensitive individuals"
        }
    },

    "sodium benzoate": {
        "aliases": [
            "sodium benzoate",
            "e211"
        ],

        "risk_level": "MEDIUM",

        "harm": [
            "Preservative used in acidic drinks",
            "Can form benzene in rare conditions with vitamin C"
        ],

        "conditions": {
            "Asthma": "Some sensitive individuals report reactions"
        }
    }
}

# =========================================================
# TEXT CLEANING
# =========================================================
def normalize_text(text):

    text = text.lower()

    # Remove weird OCR symbols
    text = re.sub(r'[^a-z0-9,\-\s]', ' ', text)

    # Remove duplicate spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

# =========================================================
# FUZZY OCR MATCH
# =========================================================
def fuzzy_contains(text, phrase, threshold=87):

    words = text.split()

    phrase_len = len(phrase.split())

    for i in range(len(words) - phrase_len + 1):

        chunk = " ".join(words[i:i + phrase_len])

        score = fuzz.ratio(chunk, phrase)

        if score >= threshold:
            return True

    return False

# =========================================================
# EXTRACT SUGAR GRAMS
# =========================================================
def extract_sugar_amount(text):

    # Example:
    # sugars 27 g
    # sugar 39g

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
# DETECT INGREDIENTS
# =========================================================
def detect_ingredients(text):

    detected = []

    for ingredient, data in HEALTH_RULES.items():

        found = False

        for alias in data["aliases"]:

            pattern = r'\b' + re.escape(alias) + r'\b'

            # Exact match
            if re.search(pattern, text):
                found = True
                break

            # OCR fuzzy match
            if fuzzy_contains(text, alias):
                found = True
                break

        if found:
            detected.append({
                "ingredient": ingredient,
                "risk": data["risk_level"],
                "harm": data["harm"],
                "conditions": data["conditions"]
            })

    return detected

# =========================================================
# STREAMLIT UI
# =========================================================
st.set_page_config(page_title="Energy Drink Health Scanner")

st.title("🧾 Energy Drink Health Scanner")

st.write("""
Upload an ingredient label.

The app will:
- Extract text using OCR
- Detect potentially unhealthy ingredients
- Explain health risks
- Warn for specific diseases like diabetes or hypertension
""")

uploaded_file = st.file_uploader(
    "Upload label image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(image, caption="Uploaded Label", use_container_width=True)

    img_array = np.array(image)

    with st.spinner("🔍 Scanning label..."):

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
    sugar_amount = extract_sugar_amount(normalized_text)

    if sugar_amount is not None:

        st.subheader("🍬 Sugar Analysis")

        if sugar_amount >= 25:

            st.error(
                f"""
                High sugar detected: {sugar_amount}g
                
                This is considered high for a single serving.
                """
            )

        elif sugar_amount >= 10:

            st.warning(
                f"Moderate sugar detected: {sugar_amount}g"
            )

        else:

            st.success(
                f"Low sugar detected: {sugar_amount}g"
            )

    # =====================================================
    # INGREDIENT DETECTION
    # =====================================================
    st.subheader("⚠️ Health Warnings")

    detected = detect_ingredients(normalized_text)

    if detected:

        for item in detected:

            risk = item["risk"]

            if risk == "HIGH":
                st.error(f"🚨 {item['ingredient'].upper()}")

            elif risk == "MEDIUM":
                st.warning(f"⚠️ {item['ingredient'].upper()}")

            else:
                st.info(f"ℹ️ {item['ingredient'].upper()}")

            st.write(f"### Risk Level: {risk}")

            st.write("### Possible Effects")

            for effect in item["harm"]:
                st.write(f"- {effect}")

            st.write("### Disease Warnings")

            for disease, warning in item["conditions"].items():
                st.write(f"- **{disease}** → {warning}")

            st.divider()

    else:
        st.success("No concerning ingredients detected.")

    # =====================================================
    # OVERALL HEALTH SUMMARY
    # =====================================================
    st.subheader("🩺 Overall Health Summary")

    if sugar_amount and sugar_amount >= 25:

        st.error("""
        This drink may be unhealthy for:
        - People with diabetes
        - People trying to lose weight
        - People with insulin resistance
        - Children consuming multiple energy drinks
        """)

    st.info("""
    Occasional consumption is usually acceptable for healthy adults,
    but frequent intake of sugary energy drinks may increase long-term
    health risks.
    """)

    # =====================================================
    # DEBUG
    # =====================================================
    with st.expander("Normalized OCR Text"):
        st.write(normalized_text)
