import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Page Configuration
st.set_page_config(page_title="M&Q Document Checker", layout="wide")

st.title("📋 M&Q Engineering Document Checker")
st.write("Upload your Engineering Drawings and Inspection Sheets (PDF, Word, Excel, PNG, JPG) for automatic cross-verification.")

# API Key Input
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("Please enter your Gemini API Key in the sidebar to proceed.")

# Optional Feature Toggle in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Verification Options")
verify_original_drawing = st.sidebar.checkbox(
    "Verify M&Q Sketch against Original Master Drawing", 
    value=False,
    help="Check this if you are uploading the Original Master Drawing along with the M&Q Sketch & Inspection Sheet to compare sketches."
)

# File Uploader supporting multiple formats
uploaded_files = st.file_uploader(
    "Choose Drawing and Inspection Files", 
    type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx"], 
    accept_multiple_files=True
)

# System Prompt Construction
BASE_PROMPT = """
Aap ek expert Manufacturing & Quality (M&Q) Engineering Document Checker hain. Aap ko uploaded documents (Image, Word, Excel, ya PDF) diye gaye hain.

Aap ka kaam drawing sketches aur inspection sheets / sizes tables ke darmiyan cross-checking karna aur discrepancies point out karna hai.

RULES & VERIFICATION LOGIC:

1. LABELED VS UNLABELED SIZES:
   - Agar Drawing Sketch par kisi size ko koi Name/Label/Annotation diya gaya hai (e.g., P1=647.7, LE=63.5, CH4=1.6 x 45°, H=Ø26.99, etc.), to wo size Inspection Sheet / sizes tables par lazmi add hona chahiye.
   - Agar kisi Detail View / kisi bhi view (jaise Detail E, Section F-F) mein koi size likha hai lekin us ke saath koi Name/Label (jaise CH, LD, P, H) nahi diya gaya (unlabeled size), to wo Inspection Sheet / sizes tables par add nahi hoga. Us ko ignore kar dein aur omission/error na samjhein.

2. HOLE CALLOUTS & PCD CHECK:
   - Agar drawing par kisi hole ka main specification text alag jagah likha ho (e.g., H=Ø26.99 24-Holes thru) aur us ki PCD drawing par alag line se indicator ke saath di gayi ho (e.g., P.C.D Ø1543.05), to inspection sheet par un dono ko mila kar likhna ("H=Ø26.99 (24-Holes thru) @PCD 1543.05") 100% correct mana jayega. Lekin check karna hoga P.C.D size theek mila kar likha ho aur numerical value 100% match kare.

3. OVERWRITING & HANDWRITING CORRECTIONS:
   - Drawing par pen se ki gayi corrections (e.g., CH4 aur CH5 ke labels ko aapas mein swap/cut karna) ko inspection sheet par maujood handwriting corrections ke saath cross-verify karein aur ensure karein ke final label correct matching par ho.

4. NUMERICAL VALUE ACCURACY:
   - Fastener specs, angles (DG1, DG2), tolerances, diameters, aur lengths ke sabhi numbers ko digit-by-digit compare karein aur bataein ke koi typing mistake hai ya nahi.
"""

# Additional Prompt condition when Optional Checkbox is ON
if verify_original_drawing:
    OPTIONAL_PROMPT = """
5. MASTER DRAWING VS M&Q SKETCH VERIFICATION (OPTIONAL MODE ACTIVE):
   - Provided documents mein se Original Master Drawing ke views ko M&Q Sheet ke Sketches ke saath match karein.
   - Confirm karein ke M&Q Sheet par banaye gaye tamam views, details (Detail E, Section F-F, etc.), aur geometry Original Master Drawing ke mutabiq 100% accurate hain ya nahi.
   - Agar M&Q Sketch par koi View missing hai ya Master Drawing ke muqable mein koi structural mismatch / distortion hai, to usay specific heading "Master Drawing vs M&Q Sketch Discrepancies" ke tehat point out karein.
"""
else:
    OPTIONAL_PROMPT = ""

OUTPUT_FORMAT_PROMPT = """
OUTPUT FORMAT:
- Inspection sheet par jaise sizes diye gaye hain waise hi tamam sizes ki tabular report provide karein.
- Tabular format: | S.No | Parameter / Label | Drawing Size | Inspection Sheet Size | Match Status |
- Agar 1 se zayada pages hain to page number wise alag alag report dein.
- Tabular report ke neeche "Discrepancies & Observations" ki heading ke tehat sirf wo errors highlight karein jo sahi mein typing mismatch hon.
"""

FULL_SYSTEM_PROMPT = BASE_PROMPT + OPTIONAL_PROMPT + OUTPUT_FORMAT_PROMPT

if st.button("Run Verification Check"):
    if not api_key:
        st.error("API Key missing! Please input API key first in the sidebar.")
    elif not uploaded_files:
        st.error("Please upload at least one document or image.")
    else:
        with st.spinner("Analyzing documents and verifying tolerances/dimensions..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                content_inputs = [FULL_SYSTEM_PROMPT]
                
                for uploaded_file in uploaded_files:
                    file_bytes = uploaded_file.read()
                    if uploaded_file.type.startswith('image/'):
                        image = Image.open(io.BytesIO(file_bytes))
                        content_inputs.append(image)
                    else:
                        content_inputs.append({
                            "mime_type": uploaded_file.type,
                            "data": file_bytes
                        })
                
                response = model.generate_content(content_inputs)
                st.success("Verification Completed!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
