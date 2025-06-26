# Smart Receipt Reader & Expense Tracker

A web application to automatically extract data from receipt images, track expenses, and manage bills with an easy-to-use admin panel.

## Features
- **Manual Bill Entry:** Add bills manually with dynamic item addition/removal (name, price, quantity)
- **Upload Receipt Images/PDFs:** Extract details using AI (Google Gemini API)
- **Inventory Management:** Add/update items and quantities, low-stock warnings, and automatic inventory update when bills are generated
- **PDF Bill Download:** Download a printable PDF after bill generation or extraction
- **Admin Panel:** View, edit, and delete any bill; delete all bills with sequence reset
- **GST Number & Store Name Settings:** Editable in sidebar (admin only)
- **Item-wise Expense Breakdown:** Price, quantity, and category for each item
- **Robust Session State:** No data loss on Streamlit rerun during manual entry
- **No Barcode/QR Dependency:** Barcode/QR features have been removed for simplicity
- **User-friendly Interface:** Built with Streamlit

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd smart_receipt_reader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Gemini API key**
   - Set the `GEMINI_API_KEY` environment variable with your Google Gemini API key.
   - Example (Windows):
     ```cmd
     set GEMINI_API_KEY=your_api_key_here
     ```
   - Example (Linux/macOS):
     ```bash
     export GEMINI_API_KEY=your_api_key_here
     ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```
   The app will be available at [http://localhost:8501](http://localhost:8501)

## Usage
- **Manual Bill Entry:** Use the "Manual Bill Entry" tab to add bills with any number of items. Add or remove items dynamically. Data is never lost on rerun.
- **Upload a Receipt:** Use the "Upload Bill" tab to upload a receipt image or PDF. The app will extract and display the details, and save them to the database.
- **Download PDF:** After generating or extracting a bill, download a printable PDF version.
- **Inventory Management:** Use the "Manage Inventory" tab to add or update items and their quantities. Low-stock items are highlighted.
- **View All Bills:** The "Manage All Bills" tab lets you view, edit, or delete any bill. You can also delete all bills and reset the sequence.
- **GST/Store Settings:** In the sidebar, admins can set the GST number and store name.

## File Structure
- `app.py` — Main Streamlit app (UI, logic, admin panel, inventory, PDF)
- `db_handler.py` — Database functions (SQLite)
- `gemini_handler.py` — Handles AI extraction from images
- `report_generator.py` — PDF and chart report generation
- `requirements.txt` — Python dependencies
- `expenses.db` — Local SQLite database (ignored by git)
- `temp/` — Temporary storage for uploaded images (ignored by git)
- `.gitignore` — Files and folders to exclude from git

## License
This project is for educational and personal use. 