import json
import io
import pandas as pd
from PIL import Image
import google.generativeai as genai
import streamlit as st

st.set_page_config(page_title="M&Q Multi-Page PDF Audit AI", layout="centered")

st.title("🛡️ M&Q PDF & Drawing Audit System")
st.caption("Manufacturing & Quality Plan Inspector (Multi-Page PDF Support)")

# User API Key Input
api_key = st.text_input("🔑 Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    st.subheader("📄 Upload Audit Documents")
    uploaded_pdf = st.file_uploader(
        "Upload M&Q PDF Document (Contains Sketch, Operations Table, etc.)",
        type=["pdf"],
        key="mq_pdf",
    )
    master_drawing = st.file_uploader(
        "Optional: Master Engineering Drawing (Image/PDF)",
        type=["jpg", "png", "jpeg", "pdf"],
        key="master_doc",
    )

    if st.button("🔍 Run Full M&Q Audit", type="primary"):
        if uploaded_pdf:
            with st.spinner("AI is reading all pages of the PDF, checking typos, dimensions, and tolerances..."):
                pdf_bytes = uploaded_pdf.read()

                contents = [
                    {
                        "mime_type": "application/pdf",
                        "data": pdf_bytes,
                    },
                    """
                    You are an Expert Mechanical Quality & Process Auditor. 
                    Perform a comprehensive multi-page audit on the uploaded M&Q document.
                    
                    Tasks:
                    1. Check the M&Q sketch pages against the M&Q operations table / requirement size pages inside the PDF.
                    2. Identify any typing errors (typos), dimensional mismatches, or tolerance discrepancies between the sketch annotations and the required size tables.
                    3. If a Master Drawing is provided, cross-verify the sizes and tolerances against it as well.
                    4. Account for multi-page documents seamlessly.

                    Output ONLY a raw JSON array of objects with the exact keys:
                    [
                      {
                        "feature": "L4 (Step Length / Tolerance)",
                        "drawing_val": "772 ±0.1 mm",
                        "sketch_val": "772 mm",
                        "ops_table_val": "722 mm",
                        "status": "FAIL",
                        "remarks": "Typo in Operations table (722 mm instead of 772 mm). Tolerance missing."
                      }
                    ]
                    Do NOT wrap in markdown codeblocks. Output raw JSON only.
                    """,
                ]

                if master_drawing:
                    master_bytes = master_drawing.read()
                    if master_drawing.type == "application/pdf":
                        contents.append({"mime_type": "application/pdf", "data": master_bytes})
                    else:
                        img = Image.open(master_drawing)
                        contents.append(img)

                try:
                    response = model.generate_content(contents)
                    clean_res = response.text.replace("```json", "").replace("```", "").strip()
                    audit_data = json.loads(clean_res)

                    st.subheader("📊 M&Q Audit Results")
                    for item in audit_data:
                        if item["status"] == "FAIL":
                            st.error(
                                f"❌ **{item['feature']} — ERROR DETECTED!**\n\nDrawing: **{item.get('drawing_val', 'N/A')}** | Sketch: **{item.get('sketch_val', 'N/A')}** | Operations Table: **{item.get('ops_table_val', 'N/A')}**\n\n*Remarks:* {item.get('remarks', '')}"
                            )
                        else:
                            st.success(
                                f"✅ **{item['feature']}**: {item.get('sketch_val', '')} (Passed / Matched)"
                            )

                    # Download Excel Report
                    df = pd.DataFrame(audit_data)
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False, sheet_name="MQ_PDF_Audit")

                    st.download_button(
                        label="📥 Download M&Q Audit Excel Report",
                        data=buffer.getvalue(),
                        file_name="MNQ_PDF_Audit_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                except Exception as e:
                    st.error(f"Audit Execution Error: {e}. Please ensure the PDF is clear and readable.")
        else:
            st.warning("Please upload the M&Q PDF document to start the audit.")
else:
    st.info("Please enter your Gemini API Key above to unlock.")
