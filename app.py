import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import re

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

        "possible_diseases": [
            "Type 2 Diabetes",
            "Obesity",
            "Fatty Liver Disease",
            "Tooth Decay"
        ],

        "avoid_groups": [
            "People with diabetes",
            "People trying to lose weight",
            "People with insulin resistance",
            "Children consuming excessive sugar"
        ]
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

        "possible_diseases": [
            "High Blood Pressure",
            "Sleep Disorders",
            "Heart Palpitations",
            "Anxiety Problems"
        ],

        "avoid_groups": [
            "People with heart disease",
            "People with anxiety disorders",
            "Pregnant women",
            "Children sensitive to caffeine"
        ]
    },

    "Taurine": {
        "aliases": [
            "taurine"
        ],

        "risk": "LOW",

        "effects": [
            "Usually safe in moderation",
            "Combined with caffeine may intensify stimulant effects"
        ],

        "possible_diseases": [
            "Possible heart stress when mixed with high caffeine"
        ],

        "avoid_groups": [
            "People with heart conditions",
            "People sensitive to stimulants"
        ]
    },

    "Artificial Flavoring": {
        "aliases": [
            "artificial flavor",
            "artificial flavours",
            "artificial flavouring",
            "artificial flavoring"
        ],

        "risk": "LOW",

        "effects": [
            "May contain synthetic compounds",
            "Some people report sensitivities"
        ],

        "possible_diseases": [
            "Possible allergic reactions",
            "Food sensitivities"
        ],

        "avoid_groups": [
            "People with food sensitivities",
            "People allergic to additives"
        ]
    }
}

# =========================================================
# CLEAN OCR TEXT
# =========================================================
def normalize_text(text):

    text = text.lower()

    text = re.sub(r'[^a-z0-9,\-\s]', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()

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

        if found:

            detected.append({
                "ingredient": ingredient,
                "risk": data["risk"],
                "effects": data["effects"],
                "possible_diseases": data["possible_diseases"],
                "avoid_groups": data["avoid_groups"]
            })

    return detected

# =========================================================
# EXTRACT SUGAR
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
Upload an energy drink label to:
- Detect unhealthy ingredients
- Learn possible health risks
- See what diseases excessive intake may contribute to
- Find out who should avoid the drink
""")

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png"]
)

# =========================================================
# PROCESS IMAGE
# =========================================================
if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(image, caption="Uploaded Label", use_container_width=True)

    img_array = np.array(image)

    # OCR
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
    sugar = extract_sugar(normalized_text)

    if sugar is not None:

        st.subheader("🍬 Sugar Analysis")

        if sugar >= 25:

            st.error(
                f"High sugar detected: {sugar}g"
            )

        elif sugar >= 10:

            st.warning(
                f"Moderate sugar detected: {sugar}g"
            )

        else:

            st.success(
                f"Low sugar detected: {sugar}g"
            )

    # =====================================================
    # INGREDIENT WARNINGS
    # =====================================================
    st.subheader("⚠️ Ingredient Health Warnings")

    detected = detect_ingredients(normalized_text)

    if detected:

        for item in detected:

            # Risk colors
            if item["risk"] == "HIGH":
                st.error(f"🚨 {item['ingredient']}")

            elif item["risk"] == "MEDIUM":
                st.warning(f"⚠️ {item['ingredient']}")

            else:
                st.info(f"ℹ️ {item['ingredient']}")

            # Effects
            st.write("### Possible Effects")

            for effect in item["effects"]:
                st.write(f"- {effect}")

            # Diseases
            st.write("### Diseases Excessive Intake May Contribute To")

            for disease in item["possible_diseases"]:
                st.write(f"- {disease}")

            # Who should avoid
            st.write("### People Who Should Limit or Avoid This")

            for group in item["avoid_groups"]:
                st.write(f"- {group}")

            st.divider()

    else:

        st.success("No concerning ingredients detected.")

    # =====================================================
    # OVERALL HEALTH SUMMARY
    # =====================================================
    st.subheader("🩺 Overall Health Summary")

    if sugar and sugar >= 25:

        st.error("""
This drink contains high sugar and stimulants.

Frequent consumption may increase risk of:
- Type 2 Diabetes
- Obesity
- High Blood Pressure
- Sleep Problems
- Heart Issues
""")

    st.warning("""
People who should be careful with energy drinks:
- People with diabetes
- People with heart disease
- Pregnant women
- Children and teenagers
- People with anxiety disorders
- People sensitive to caffeine
""")

    st.info("""
Occasional consumption is usually acceptable for
healthy adults, but frequent intake may increase
long-term health risks.
""")

    # =====================================================
    # DEBUG TEXT
    # =====================================================
    with st.expander("Normalized OCR Text"):
        st.write(normalized_text)
