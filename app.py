import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Page Configuration
st.set_page_config(page_title="M&Q Document Checker (100% Precision Engine)", layout="wide")

st.title("📋 M&Q Engineering Document Checker")
st.write("Upload Engineering Drawings and Inspection Sheets (Images: JPG/PNG, or PDF) for automatic 100% high-precision cross-verification.")

# API Key Input
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("Please enter your Gemini API Key in the sidebar to proceed.")

# File Uploader
uploaded_files = st.file_uploader(
    "Choose Drawing & Inspection Sheet Pictures/Files", 
    type=["jpg", "jpeg", "png", "pdf"], 
    accept_multiple_files=True
)

# System Prompt with All User Requirements Fully Integrated
SYSTEM_PROMPT = """
Aap ek expert Manufacturing & Quality (M&Q) Engineering Document Checker hain. Aap ko 1 ya 1 se zayada pages/pictures wale document diye gaye hain (Images JPG/PNG ya PDF).
Document mein:
1. Drawing Sketch (Page 1 ya View 1)
2. Inspection Sheet / Sizes Table (Page 2 ya View 2)
Ya dono ek hi picture/page par ho sakte hain.

Aap ka kaam drawing sketches par maujood sizes aur text notes ko inspection sheet / sizes tables ke saath cross-check karna hai aur kisi bhi typing error, tolerance class mismatch, text difference, ya discrepancy ko point out karna hai.

RULES & VERIFICATION LOGIC FOR 100% HIGH PRECISION:

1. LABELED VS UNLABELED SIZES:
   - Drawing Sketch par kisi bhi size ka Name/Label/Annotation (e.g., D1, D4, D5, L1, TL, RA, DG1, KW1, etc.) hai to wo Inspection Sheet par lazmi match hona chahiye.
   - Unlabeled sizes ko ignore kar dein.

2. TOLERANCE CLASS VERIFICATION (EXACT CLASS & CASE-SENSITIVE):
   - Jab bhi kisi dimension ke saath Tolerance Class (e.g., e9, h8, H7, p9, P9, j6, k6, etc.) likhi ho, us Tolerance Class ko Drawing aur Inspection Sheet ke darmiyan STRICTLY compare karein.
   - Letter Case (Small vs Capital, e.g., 'e9' vs 'E9', 'p9' vs 'P9') aur Class Number (e.g., 9, 8, 7) 100% exact match hone chahiye.
   - Agar numerical tolerance limit values match kar rahi hon LEKIN Tolerance Class letter/case mein fark ho (e.g., Drawing par 'e9' aur Inspection Sheet par 'E9'), to is ko STRICT MISMATCH / Discrepancy ke taur par report karein.

3. TOTAL LENGTH (TL) & OVERALL DIMENSION CHECK:
   - Drawing par di gayi Total Length (e.g., TL=3670 ya TL_3670) ko Inspection Sheet ki TL entry (e.g., TL=3670(Face "B")) se exact compare karein.
   - Numerical value (3670) match ho rahi hai ya nahi, aur Face annotation (Face "A" / Face "B") added hai ya missing hai, is ko report mein clearly mention karein.

4. FIT SPECIFICATIONS & TEXT ANNOTATIONS (e.g., D5, D4, D6):
   - Dimensions ke saath likhe gaye tambahan text/notes ko lafz-ba-lafz compare karein (e.g., Drawing par "D5=Ø 460 SHRINK FIT" vs Inspection Sheet par "D5=Ø 460(Shrink Fit As Per Shell Bore)"). Wording variations aur extra text ko strictly highlight karein.

5. HOLE CALLOUTS & PCD CHECK:
   - Agar drawing par hole callouts aur PCD alag lines par hon (e.g., H=Ø26.99 24-Holes thru aur P.C.D Ø1543.05), to inspection sheet par combined text ko verify karein ke numerical value aur hole counts 100% accurate hain.

6. HANDWRITING & PEN CORRECTIONS DETECTION:
   - Document par (Sketch ya Inspection Sheet par) pen se likhi hui handwriting, dates (e.g., 01/09/26), signatures, ya manual Urdu/English notes (jaise DETAIL G ke paas hand-written notes) ko scan karein aur report ke neeche "Handwritten Notes & Annotations" ki heading mein highlight karein.

7. CONFIDENCE & ACCURACY PERCENTAGE EVALUATION:
   - Har parameter ka confidence percentage score dein (% accuracy).
   - Agar blurry image, bad handwriting, ya resolution issue ki waja se kisi parameter mein 1% bhi doubt ho, to us ko status mein "⚠️ DOUBTFUL (X% Confidence)" report karein aur doubt ki clear reason batayein.

OUTPUT FORMAT:
- Top Header: **Overall Verification Confidence Score: X%**
- Complete tabular report: | S.No | Parameter / Label | Drawing Size & Specs | Inspection Sheet Size & Specs | Match Status (Confidence %) |
- Heading: **"Discrepancies & Observations"** (for typing mismatches, tolerance class errors, missing face callouts, and text differences).
- Heading: **"Uncertain / Doubtful Inspections"** (listing items where AI has doubt or image resolution is low, along with reasons).
- Heading: **"Handwritten Notes & Manual Corrections"** (listing all pen handwritten text, notes, and dates).
"""

# Dynamic Candidate Models for Auto-Fallback
CANDIDATE_MODELS = [
    "gemini-flash-latest",   # Google-managed alias
    "gemini-3.6-flash",      # Dated fallback #1
    "gemini-3.5-flash",      # Dated fallback #2
    "gemini-2.5-flash",      # Dated fallback #3
]


def get_working_model(content_inputs):
    """
    Try each candidate model in order until one succeeds.
    Returns (response, model_name_used).
    """
    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(content_inputs)
            return response, model_name
        except Exception as e:
            last_error = e
            continue
    raise last_error


if st.button("Run Verification Check"):
    if not api_key:
        st.error("API Key missing! Please input API key first in the sidebar.")
    elif not uploaded_files:
        st.error("Please upload at least one image or document file.")
    else:
        with st.spinner("Processing pictures & performing 100% High-Precision Audit..."):
            try:
                content_inputs = [SYSTEM_PROMPT]
                
                st.subheader("Uploaded Pictures / Documents Preview:")
                cols = st.columns(min(len(uploaded_files), 4))
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    file_bytes = uploaded_file.read()
                    
                    if uploaded_file.type.startswith('image/'):
                        image = Image.open(io.BytesIO(file_bytes))
                        content_inputs.append(image)
                        with cols[idx % 4]:
                            st.image(image, caption=f"Image {idx+1}: {uploaded_file.name}", use_container_width=True)
                    elif uploaded_file.type == 'application/pdf':
                        content_inputs.append({
                            "mime_type": "application/pdf",
                            "data": file_bytes
                        })
                        with cols[idx % 4]:
                            st.info(f"📄 PDF Document {idx+1}: {uploaded_file.name}")
                
                response, model_used = get_working_model(content_inputs)
                st.markdown("---")
                st.success(f"Verification Completed Successfully! (model used: {model_used})")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
