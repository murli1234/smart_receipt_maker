import streamlit as st
import os
import json
from datetime import datetime
from gemini_handler import extract_receipt_data
from db_handler import init_db, insert_expense, fetch_expenses, fetch_expenses_by_month, update_expense, delete_expense

st.set_page_config(page_title="Smart Receipt Reader & Expense Tracker", layout="wide")

st.title("🧾 Smart Receipt Reader & Expense Tracker")

# Create temp directory if not exists
if not os.path.exists("temp"):
    os.makedirs("temp")

# Initialize DB
init_db()

# Sidebar (for future filters)
st.sidebar.header("Filters")
# (Filters will be added later)

# Admin Panel in Sidebar
st.sidebar.header("Admin Panel")
with st.sidebar.expander("View Monthly Report", expanded=False):
    selected_month = st.text_input("Enter month (YYYY-MM)", value=datetime.now().strftime("%Y-%m"), key="admin_month")
    show_report = st.button("Show Monthly Report", key="show_report_btn")
    if show_report:
        monthly_rows = fetch_expenses_by_month(selected_month)
        if monthly_rows:
            import pandas as pd
            monthly_df = pd.DataFrame(monthly_rows, columns=["ID", "Date", "Store", "Items", "Amount", "Category"])
            st.subheader(f"All Bills for {selected_month}")
            total_amount = monthly_df["Amount"].sum()
            st.success(f"Total Money Spent in {selected_month}: ${total_amount:.2f}")
            for idx, row in monthly_df.iterrows():
                st.write(":heavy_minus_sign:"*40)
                st.write(f"**Store:** {row['Store']} | **Date:** {row['Date']} | **Amount:** ${row['Amount']:.2f} | **Category:** {row['Category']}")
                items = json.loads(row['Items']) if row['Items'] else []
                if items:
                    items_df = pd.DataFrame(items)
                    st.write("**Items:**")
                    st.dataframe(items_df, use_container_width=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Delete", key=f"delete_{row['ID']}"):
                        delete_expense(row['ID'])
                        st.success("Bill deleted.")
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Edit", key=f"edit_{row['ID']}"):
                        with st.form(f"edit_form_{row['ID']}"):
                            new_store = st.text_input("Store", value=row['Store'], key=f"store_{row['ID']}")
                            new_date = st.text_input("Date", value=row['Date'], key=f"date_{row['ID']}")
                            new_amount = st.number_input("Amount", value=float(row['Amount']), key=f"amount_{row['ID']}")
                            new_category = st.text_input("Category", value=row['Category'], key=f"cat_{row['ID']}")
                            new_items_str = st.text_area("Items (JSON Array)", value=row['Items'], key=f"items_{row['ID']}")
                            submitted = st.form_submit_button("Update Bill")
                            if submitted:
                                try:
                                    json.loads(new_items_str)
                                    update_expense(row['ID'], new_date, new_store, new_items_str, new_amount, new_category)
                                    st.success("Bill updated.")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Invalid items JSON: {e}")
        else:
            st.info(f"No bills found for {selected_month}.")

# File uploader
uploaded_file = st.file_uploader("Upload a receipt image (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    temp_path = os.path.join("temp", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)
    with st.spinner("Extracting receipt details..."):
        result = extract_receipt_data(temp_path)
    if result:
        st.write("Raw Gemini output:", result)
        # Remove Markdown code block markers if present
        if result.strip().startswith("```"):
            result = result.strip().split('\n', 1)[1].rsplit('```', 1)[0].strip()
        try:
            data = json.loads(result)
            st.success("Extraction successful!")
            # User-friendly display of extracted data
            st.markdown(f"**Store:** {data.get('store', 'Unknown')}")
            st.markdown(f"**Date:** {data.get('date', str(datetime.now().date()))}")
            st.markdown(f"**Total Amount:** ${data.get('amount', 0):.2f}")
            st.markdown(f"**Category:** {data.get('category', 'Uncategorized')}")
            items = data.get('items', [])
            if items:
                import pandas as pd
                items_df = pd.DataFrame(items)
                st.markdown("**Items:**")
                st.dataframe(items_df, use_container_width=True)
            else:
                st.info("No items found on the receipt.")
            # Insert into DB
            insert_expense(
                data.get("date", str(datetime.now().date())),
                data.get("store", "Unknown"),
                json.dumps(data.get("items", [])),
                float(data.get("amount", 0)),
                data.get("category", "Uncategorized")
            )
            st.info("Expense saved.")
        except Exception as e:
            st.error(f"Failed to parse extracted data: {e}")
    else:
        st.error("Failed to extract data from the receipt.")
    # Delete temp image
    try:
        os.remove(temp_path)
    except Exception as e:
        st.warning(f"Could not delete temp file: {e}")

# Fetch and display all expenses
rows = fetch_expenses()
if rows:
    import pandas as pd
    import matplotlib.pyplot as plt
    # Flatten all items from all receipts
    item_rows = []
    for row in rows:
        bill_id, date, store, items_json, amount, category = row
        items = json.loads(items_json) if items_json else []
        for item in items:
            item_name = item.get('name', 'Unknown')
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            item_rows.append({
                'Date': date,
                'Item Name': item_name,
                'Price': price,
                'Quantity': quantity,
                'Amount': price * quantity,
                'Category': category
            })
    if item_rows:
        item_df = pd.DataFrame(item_rows)
        st.subheader("All Expenses (Item-wise)")
        st.dataframe(item_df, use_container_width=True)
        # Visualization: Expenses by Category
        st.markdown("### Expenses by Category")
        cat_sum = item_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        if not cat_sum.empty:
            fig1, ax1 = plt.subplots()
            cat_sum.plot(kind="bar", ax=ax1)
            ax1.set_ylabel("Total Amount")
            ax1.set_xlabel("Category")
            st.pyplot(fig1)
        else:
            st.info("No data to display for category chart.")
        # Visualization: Expenses Over Time
        st.markdown("### Expenses Over Time")
        item_df["Date"] = pd.to_datetime(item_df["Date"], errors="coerce")
        date_sum = item_df.groupby("Date")["Amount"].sum().sort_index()
        if not date_sum.empty:
            fig2, ax2 = plt.subplots()
            date_sum.plot(kind="bar", ax=ax2)
            ax2.set_ylabel("Total Amount")
            ax2.set_xlabel("Date")
            st.pyplot(fig2)
        else:
            st.info("No data to display for date chart.")
    else:
        st.subheader("All Expenses (Item-wise)")
        st.info("No items found in any receipts.")
else:
    st.subheader("All Expenses (Item-wise)")
    st.info("No expenses recorded yet.") 