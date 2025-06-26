import streamlit as st
import os
import json
from datetime import datetime
from gemini_handler import extract_receipt_data
from db_handler import (
    init_db, insert_expense, fetch_expenses, fetch_expenses_by_month, update_expense, delete_expense,
    init_inventory_db, add_or_update_inventory_item, get_inventory, decrease_inventory_item, get_item_quantity, get_item_by_barcode
)
import pandas as pd
import sqlite3
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import uuid

def migrate_inventory_add_barcode():
    with sqlite3.connect("expenses.db") as conn:
        try:
            conn.execute("ALTER TABLE inventory ADD COLUMN barcode TEXT;")
        except sqlite3.OperationalError:
            # Column already exists
            pass

migrate_inventory_add_barcode()

st.set_page_config(page_title="Smart Receipt Reader & Expense Tracker", layout="wide")

st.title("🧾 Smart Receipt Reader & Expense Tracker")

# Create temp directory if not exists
if not os.path.exists("temp"):
    os.makedirs("temp")

# Initialize DBs
init_db()
init_inventory_db()

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
                        st.rerun()
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
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Invalid items JSON: {e}")
        else:
            st.info(f"No bills found for {selected_month}.")

# --- Store Name Setting (Admin Only) ---
if 'store_name' not in st.session_state:
    st.session_state['store_name'] = ''

st.sidebar.header("Store Settings")
if st.sidebar.checkbox("Edit Store Name (Admin Only)"):
    new_store = st.sidebar.text_input("Store Name", value=st.session_state['store_name'])
    if st.sidebar.button("Save Store Name"):
        st.session_state['store_name'] = new_store
        st.sidebar.success("Store Name updated!")

# --- GST Number Setting (Admin Only) ---
if 'gst_number' not in st.session_state:
    st.session_state['gst_number'] = ''

st.sidebar.header("GST Settings")
if st.sidebar.checkbox("Edit GST Number (Admin Only)"):
    new_gst = st.sidebar.text_input("GST Number", value=st.session_state['gst_number'])
    if st.sidebar.button("Save GST Number"):
        st.session_state['gst_number'] = new_gst
        st.sidebar.success("GST Number updated!")

# --- Main Interface Tabs ---
tabs = st.tabs(["Generate Bill", "Manage Inventory", "Manage All Bills"])

with tabs[0]:
    st.title("🧾 Bill Entry")
    bill_tabs = st.tabs(["Manual Bill Entry", "Upload Bill"])
    # --- Manual Bill Entry ---
    with bill_tabs[0]:
        st.header("Manual Bill Entry")
        if 'manual_items' not in st.session_state:
            st.session_state['manual_items'] = [{"id": str(uuid.uuid4()), "name": "", "price": 0.0, "quantity": 1}]
        manual_items = st.session_state['manual_items']
        st.markdown("**Add Items** (Name, Price, Quantity)")
        remove_indices = []
        for i, item in enumerate(manual_items):
            cols = st.columns([3,2,2,1])
            name_key = f"item_name_{item['id']}"
            price_key = f"item_price_{item['id']}"
            qty_key = f"item_qty_{item['id']}"
            # Initialize session_state for each item only if not present
            if name_key not in st.session_state:
                st.session_state[name_key] = item["name"]
            if price_key not in st.session_state:
                st.session_state[price_key] = item["price"]
            if qty_key not in st.session_state:
                st.session_state[qty_key] = item["quantity"]
            cols[0].text_input(f"Item Name", key=name_key)
            cols[1].number_input(f"Price", min_value=0.0, key=price_key)
            cols[2].number_input(f"Quantity", min_value=1, key=qty_key)
            if len(manual_items) > 1:
                if cols[3].button("Remove", key=f"remove_item_{item['id']}"):
                    remove_indices.append(i)
        if st.button("Add Item", key="add_item_btn"):
            new_item = {"id": str(uuid.uuid4()), "name": "", "price": 0.0, "quantity": 1}
            st.session_state['manual_items'] = manual_items + [new_item]
            st.session_state[f"item_name_{new_item['id']}"] = ""
            st.session_state[f"item_price_{new_item['id']}"] = 0.0
            st.session_state[f"item_qty_{new_item['id']}"] = 1
            st.rerun()
        for idx in sorted(remove_indices, reverse=True):
            # Remove session_state keys for this item
            item = manual_items[idx]
            for k in [f"item_name_{item['id']}", f"item_price_{item['id']}", f"item_qty_{item['id']}"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state['manual_items'] = [it for i, it in enumerate(manual_items) if i != idx]
            st.rerun()
        # --- Bill Form ---
        with st.form("generate_bill_form"):
            store = st.text_input("Store Name", value=st.session_state['store_name'], disabled=True)
            date = st.date_input("Date", value=datetime.now().date())
            category = st.text_input("Category", value="General")
            gst_number = st.text_input("GST Number", value=st.session_state['gst_number'], disabled=True)
            # Build items from session_state
            bill_items = []
            for item in st.session_state['manual_items']:
                name = st.session_state[f"item_name_{item['id']}"]
                price = st.session_state[f"item_price_{item['id']}"]
                quantity = st.session_state[f"item_qty_{item['id']}"]
                bill_items.append({"id": item['id'], "name": name, "price": price, "quantity": quantity})
            total_amount = sum(item["price"] * item["quantity"] for item in bill_items)
            bill_error = False
            bill_error_msg = ""
            for item in bill_items:
                current_qty = get_item_quantity(item["name"])
                if current_qty is not None and item["quantity"] > current_qty:
                    bill_error = True
                    bill_error_msg += f"Not enough stock for {item['name']} (Available: {current_qty})\n"
            submitted = st.form_submit_button("Generate Bill")
        if submitted:
            if bill_error:
                st.error(bill_error_msg)
            else:
                # Decrease inventory
                for item in bill_items:
                    if get_item_quantity(item['name']) is not None:
                        decrease_inventory_item(item['name'], item['quantity'])
                # Save bill to DB
                insert_expense(
                    str(date),
                    store,
                    json.dumps(bill_items),
                    float(total_amount),
                    category
                )
                st.success("Bill generated and saved!")
                # Show printable bill
                st.markdown("---")
                st.markdown(f"### Printable Bill")
                st.markdown(f"**Store:** {store}")
                st.markdown(f"**Date:** {date}")
                st.markdown(f"**GST Number:** {gst_number}")
                st.markdown(f"**Category:** {category}")
                bill_table = [[item['name'], item['price'], item['quantity'], item['price']*item['quantity']] for item in bill_items]
                bill_df = pd.DataFrame(bill_table, columns=["Item Name", "Price", "Quantity", "Total"])
                st.table(bill_df)
                st.markdown(f"**Total Amount:** ₹{total_amount:.2f}")
                # PDF download
                if st.button("Download PDF Bill"):
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=letter)
                    width, height = letter
                    y = height - 40
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(50, y, f"Bill")
                    y -= 30
                    c.setFont("Helvetica", 12)
                    c.drawString(50, y, f"Store: {store}")
                    y -= 18
                    c.drawString(50, y, f"Date: {date}")
                    y -= 18
                    c.drawString(50, y, f"GST Number: {gst_number}")
                    y -= 18
                    c.drawString(50, y, f"Category: {category}")
                    y -= 30
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y, "Item Name")
                    c.drawString(200, y, "Price")
                    c.drawString(300, y, "Quantity")
                    c.drawString(400, y, "Total")
                    c.setFont("Helvetica", 12)
                    y -= 18
                    for item in bill_table:
                        c.drawString(50, y, str(item[0]))
                        c.drawString(200, y, f"{item[1]}")
                        c.drawString(300, y, f"{item[2]}")
                        c.drawString(400, y, f"{item[3]}")
                        y -= 18
                        if y < 60:
                            c.showPage()
                            y = height - 40
                    y -= 10
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y, f"Total Amount: ₹{total_amount:.2f}")
                    c.save()
                    buffer.seek(0)
                    st.download_button(
                        label="Download PDF",
                        data=buffer,
                        file_name=f"bill_{date}.pdf",
                        mime="application/pdf"
                    )
                # Reset manual_items and item field session_state after bill generation
                st.session_state['manual_items'] = [{"id": str(uuid.uuid4()), "name": "", "price": 0.0, "quantity": 1}]
                for k in list(st.session_state.keys()):
                    if k.startswith("item_name_") or k.startswith("item_price_") or k.startswith("item_qty_"):
                        del st.session_state[k]
    # --- Upload Bill ---
    with bill_tabs[1]:
        st.header("Upload Bill (PDF/JPG/PNG)")
        uploaded_file = st.file_uploader("Upload a bill image or PDF", type=["jpg", "jpeg", "png", "pdf"])
        if uploaded_file:
            temp_path = os.path.join("temp", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            if uploaded_file.type == "application/pdf":
                st.info("PDF upload is supported, but extraction works best with images.")
            st.image(uploaded_file, caption="Uploaded Bill", use_container_width=True)
            with st.spinner("Extracting bill details..."):
                result = extract_receipt_data(temp_path)
            if result:
                st.write("Raw Gemini output:", result)
                # Remove Markdown code block markers if present
                if result.strip().startswith("```"):
                    result = result.strip().split('\n', 1)[1].rsplit('```', 1)[0].strip()
                try:
                    data = json.loads(result)
                    st.success("Extraction successful!")
                    st.markdown(f"**Store:** {data.get('store', 'Unknown')}")
                    st.markdown(f"**Date:** {data.get('date', str(datetime.now().date()))}")
                    st.markdown(f"**Total Amount:** ₹{data.get('amount', 0):.2f}")
                    st.markdown(f"**Category:** {data.get('category', 'Uncategorized')}")
                    items = data.get('items', [])
                    if items:
                        items_df = pd.DataFrame(items)
                        st.markdown("**Items:**")
                        st.dataframe(items_df, use_container_width=True)
                    else:
                        st.info("No items found on the bill.")
                    # Insert into DB
                    insert_expense(
                        data.get("date", str(datetime.now().date())),
                        data.get("store", "Unknown"),
                        json.dumps(data.get("items", [])),
                        float(data.get("amount", 0)),
                        data.get("category", "Uncategorized")
                    )
                    st.info("Bill saved.")
                    # PDF download for extracted bill
                    if st.button("Download PDF Bill (Extracted)"):
                        buffer = io.BytesIO()
                        c = canvas.Canvas(buffer, pagesize=letter)
                        width, height = letter
                        y = height - 40
                        c.setFont("Helvetica-Bold", 16)
                        c.drawString(50, y, f"Bill")
                        y -= 30
                        c.setFont("Helvetica", 12)
                        c.drawString(50, y, f"Store: {data.get('store', 'Unknown')}")
                        y -= 18
                        c.drawString(50, y, f"Date: {data.get('date', str(datetime.now().date()))}")
                        y -= 18
                        c.drawString(50, y, f"Category: {data.get('category', 'Uncategorized')}")
                        y -= 30
                        c.setFont("Helvetica-Bold", 12)
                        c.drawString(50, y, "Item Name")
                        c.drawString(200, y, "Price")
                        c.drawString(300, y, "Quantity")
                        c.drawString(400, y, "Total")
                        c.setFont("Helvetica", 12)
                        y -= 18
                        for item in items:
                            c.drawString(50, y, str(item.get('name', '')))
                            c.drawString(200, y, f"{item.get('price', 0)}")
                            c.drawString(300, y, f"{item.get('quantity', 1)}")
                            c.drawString(400, y, f"{item.get('price', 0) * item.get('quantity', 1)}")
                            y -= 18
                            if y < 60:
                                c.showPage()
                                y = height - 40
                        y -= 10
                        c.setFont("Helvetica-Bold", 12)
                        c.drawString(50, y, f"Total Amount: ₹{data.get('amount', 0):.2f}")
                        c.save()
                        buffer.seek(0)
                        st.download_button(
                            label="Download PDF (Extracted)",
                            data=buffer,
                            file_name=f"bill_{data.get('date', str(datetime.now().date()))}.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"Failed to parse extracted data: {e}")
            else:
                st.error("Failed to extract data from the bill.")
            # Delete temp image
            try:
                os.remove(temp_path)
            except Exception as e:
                st.warning(f"Could not delete temp file: {e}")

with tabs[1]:
    st.title("📦 Inventory Management")
    inv_item = st.text_input("Item Name (Add/Update)", key="inv_item_tab")
    inv_qty = st.number_input("Quantity", min_value=0, value=0, key="inv_qty_tab")
    if st.button("Add/Update Item", key="add_update_inv_tab"):
        add_or_update_inventory_item(inv_item, int(inv_qty))
        st.success(f"Inventory updated for {inv_item}")
    st.markdown("---")
    st.markdown("**Current Inventory:**")
    inventory = get_inventory()
    if inventory:
        inv_df = pd.DataFrame(inventory, columns=["Item Name", "Quantity"])
        def highlight_low_col(col):
            return ['background-color: #ffcccc' if v <= 5 else '' for v in col]
        st.dataframe(inv_df.style.apply(highlight_low_col, subset=['Quantity']))
        low_stock = inv_df[inv_df["Quantity"] <= 5]
        if not low_stock.empty:
            st.warning("Low stock items: " + ", ".join(low_stock["Item Name"].tolist()))
    else:
        st.info("No inventory items yet.")

with tabs[2]:
    st.title("🗂️ Manage All Bills")
    if 'deleted_bills' not in st.session_state:
        st.session_state['deleted_bills'] = set()
    if 'updated_bills' not in st.session_state:
        st.session_state['updated_bills'] = dict()
    # Delete All Bills button with confirmation
    if 'delete_all_bills_clicked' not in st.session_state:
        st.session_state['delete_all_bills_clicked'] = False
    if st.button("Delete All Bills", key="delete_all_bills_btn"):
        st.session_state['delete_all_bills_clicked'] = True
    if st.session_state['delete_all_bills_clicked']:
        st.warning("Are you sure you want to delete ALL bills? This action cannot be undone.")
        if st.button("Confirm Delete All Bills", key="confirm_delete_all_bills_btn"):
            # Delete all rows from expenses and reset sequence
            with sqlite3.connect("expenses.db") as conn:
                conn.execute("DELETE FROM expenses;")
                conn.execute("DELETE FROM sqlite_sequence WHERE name='expenses';")
            st.session_state['deleted_bills'] = set()
            st.session_state['updated_bills'] = dict()
            st.session_state['delete_all_bills_clicked'] = False
            st.success("All bills deleted.")
        if st.button("Cancel", key="cancel_delete_all_bills_btn"):
            st.session_state['delete_all_bills_clicked'] = False
    all_rows = fetch_expenses()
    # Remove deleted bills from display
    all_rows = [row for row in all_rows if row[0] not in st.session_state['deleted_bills']]
    # Apply updates in session state
    all_rows = [st.session_state['updated_bills'].get(row[0], row) for row in all_rows]
    if all_rows:
        all_df = pd.DataFrame(all_rows, columns=["ID", "Date", "Store", "Items", "Amount", "Category"])
        st.dataframe(all_df.drop(columns=["ID", "Items"]), use_container_width=True)
        for idx, row in all_df.iterrows():
            with st.expander(f"Bill ID: {row['ID']} | {row['Store']} | {row['Date']}"):
                st.write(f"**Store:** {row['Store']}")
                st.write(f"**Date:** {row['Date']}")
                st.write(f"**Amount:** ₹{row['Amount']:.2f}")
                st.write(f"**Category:** {row['Category']}")
                items = json.loads(row['Items']) if row['Items'] else []
                if items:
                    items_df = pd.DataFrame(items)
                    st.write("**Items:**")
                    st.dataframe(items_df, use_container_width=True)
                else:
                    st.info("No items found on the receipt.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Delete", key=f"delete_all_{row['ID']}"):
                        delete_expense(row['ID'])
                        st.session_state['deleted_bills'].add(row['ID'])
                        st.success("Bill deleted.")
                with col2:
                    if st.button(f"Edit", key=f"edit_all_{row['ID']}"):
                        with st.form(f"edit_form_all_{row['ID']}"):
                            new_store = st.text_input("Store", value=row['Store'], key=f"store_all_{row['ID']}")
                            new_date = st.text_input("Date", value=row['Date'], key=f"date_all_{row['ID']}")
                            new_amount = st.number_input("Amount", value=float(row['Amount']), key=f"amount_all_{row['ID']}")
                            new_category = st.text_input("Category", value=row['Category'], key=f"cat_all_{row['ID']}")
                            new_items_str = st.text_area("Items (JSON Array)", value=row['Items'], key=f"items_all_{row['ID']}")
                            submitted = st.form_submit_button("Update Bill")
                            if submitted:
                                try:
                                    json.loads(new_items_str)
                                    update_expense(row['ID'], new_date, new_store, new_items_str, new_amount, new_category)
                                    # Update in session state for immediate UI feedback
                                    st.session_state['updated_bills'][row['ID']] = (
                                        row['ID'], new_date, new_store, new_items_str, new_amount, new_category
                                    )
                                    st.success("Bill updated.")
                                except Exception as e:
                                    st.error(f"Invalid items JSON: {e}")
    else:
        st.info("No bills found.")

# Fetch and display all expenses
rows = fetch_expenses()
if rows:
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
    else:
        st.subheader("All Expenses (Item-wise)")
        st.info("No items found in any receipts.")
else:
    st.subheader("All Expenses (Item-wise)")
    st.info("No expenses recorded yet.") 