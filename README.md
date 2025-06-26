# Smart Receipt Reader & Expense Tracker

A web application to automatically extract data from receipt images, track expenses, and manage bills with an easy-to-use admin panel.

## Features
- Upload receipt images (JPG/PNG) and extract details using AI (Google Gemini API)
- Store and view all expenses in a local SQLite database
- Item-wise expense breakdown with price and quantity
- Visualizations: expenses by category and over time
- Admin panel to view, edit, and delete bills for any month
- User-friendly interface built with Streamlit

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
- **Upload a receipt:** Use the main page to upload a receipt image. The app will extract and display the details, and save them to the database.
- **View all expenses:** The "All Expenses" section shows every item from all receipts, with price, quantity, and category. Visual charts help you understand your spending.
- **Admin panel:** In the sidebar, use the Admin Panel to view, edit, or delete bills for any month. You can update bill details or remove bills as needed.

## File Structure
- `app.py` — Main Streamlit app
- `db_handler.py` — Database functions (SQLite)
- `gemini_handler.py` — Handles AI extraction from images
- `report_generator.py` — (Optional) PDF and chart report generation
- `requirements.txt` — Python dependencies
- `expenses.db` — Local SQLite database
- `temp/` — Temporary storage for uploaded images

## License
This project is for educational and personal use. 