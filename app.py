import re
from collections import defaultdict
import pdfplumber
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Shipping Label Aggregator", page_icon="📦")

st.title("📦 Shipping Label Inventory Aggregator")
st.write("Upload your TikTok / J&T Express PDF shipping labels to group and sum up quantities.")

uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])

if uploaded_file is not None:
    totals = defaultdict(int)

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            table_extracted = False
            
            # 1. Attempt extracting via table bounding boxes
            for table in tables:
                for row in table:
                    clean_row = [str(cell).strip() if cell else "" for cell in row]
                    if len(clean_row) >= 4:
                        v_name = clean_row[1]
                        sku = clean_row[2]
                        qty_str = clean_row[3]
                        
                        if qty_str.isdigit() and v_name and sku:
                            totals[(v_name, sku)] += int(qty_str)
                            table_extracted = True

            # 2. Line-by-line fallback parsing
            if not table_extracted:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        match = re.match(r"^\d+\s+(.+?)\s+([a-zA-Z0-9_\-\s]+?)\s+(\d+)$", line.strip())
                        if match:
                            v_name, sku, qty = match.groups()
                            totals[(v_name.strip(), sku.strip())] += int(qty)

    if totals:
        data = [
            {"V.name": v_name, "SKU": sku, "total Qty": qty}
            for (v_name, sku), qty in totals.items()
        ]
        df = pd.DataFrame(data)

        st.subheader("Aggregated Results")
        st.dataframe(df, use_container_width=True)

        total_items = df["total Qty"].sum()
        st.metric(label="Grand Total Items", value=total_items)

        # CSV Download button
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Summary (CSV)",
            data=csv_data,
            file_name="aggregated_summary.csv",
            mime="text/csv",
        )
    else:
        st.error("No valid table data found in the uploaded PDF. Please ensure the PDF is text-readable.")
