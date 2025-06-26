import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as RLImage
import os

def generate_monthly_report(expenses, month, output_path):
    # expenses: list of dicts with keys: date, store, items, amount, category
    # month: 'YYYY-MM'
    # output_path: PDF file path
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Expense Report for {month}")
    c.setFont("Helvetica", 12)
    y = height - 80
    total = 0
    category_totals = {}
    for exp in expenses:
        c.drawString(50, y, f"{exp['date']} | {exp['store']} | {exp['category']} | ${exp['amount']:.2f}")
        y -= 18
        total += exp['amount']
        category_totals[exp['category']] = category_totals.get(exp['category'], 0) + exp['amount']
        if y < 100:
            c.showPage()
            y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y-20, f"Total: ${total:.2f}")
    # Pie chart
    if category_totals:
        plt.figure(figsize=(4,4))
        plt.pie(category_totals.values(), labels=category_totals.keys(), autopct='%1.1f%%')
        plt.title('Expenses by Category')
        chart_path = "temp/category_pie.png"
        plt.savefig(chart_path)
        plt.close()
        c.drawImage(chart_path, 350, y-100, width=180, height=180)
        os.remove(chart_path)
    c.save() 