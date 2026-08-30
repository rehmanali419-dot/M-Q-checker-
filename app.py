import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Page Configuration
st.set_page_config(page_title="M&Q Document Checker", layout="wide")

st.title("📋 M&Q Engineering Document Checker")
st.write("Upload your Engineering Drawings and Inspection Sheets (Images: JPG/PNG, or PDF) for automatic cross-verification.")

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

# System Prompt with User's Exact Verification Rules
SYSTEM_PROMPT = """
Aap ek expert Manufacturing & Quality (M&Q) Engineering Document Checker hain. Aap ko 1 ya 1 se zayada pages/pictures wale document diye gaye hain (Images JPG/PNG ya PDF).
Document mein:
1. Drawing Sketch (Page 1 ya View 1)
2. Inspection Sheet / Sizes Table (Page 2 ya View 2)
Ya dono ek hi picture/page par ho sakte hain.

Aap ka kaam drawing sketches par maujood sizes ko inspection sheet / sizes tables ke saath cross-check karna hai aur kisi bhi typing error ya discrepancy ko point out karna hai.

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

OUTPUT FORMAT:
- Inspection sheet par jaise sizes diye gaye hain waise hi tamam sizes ki tabular report provide karein.
- Tabular format: | S.No | Parameter / Label | Drawing Size | Inspection Sheet Size | Match Status |
- Agar 1 se zayada pages/pictures hain to page number / image wise alag alag report dein.
- Tabular report ke neeche "Discrepancies & Observations" ki heading ke tehat sirf wo errors highlight karein jo sahi mein typing mismatch hon.
"""

if st.button("Run Verification Check"):
    if not api_key:
        st.error("API Key missing! Please input API key first in the sidebar.")
    elif not uploaded_files:
        st.error("Please upload at least one image or document file.")
    else:
        with st.spinner("Processing pictures & analyzing engineering drawing dimensions..."):
            try:
                # Updated active model: gemini-3.6-flash
                # (gemini-2.5-flash was retired by Google; gemini-3.6-flash is the
                # current stable replacement as of August 2026)
                model = genai.GenerativeModel('gemini-3.6-flash')
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
                
                response = model.generate_content(content_inputs)
                st.markdown("---")
                st.success("Verification Completed Successfully!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
