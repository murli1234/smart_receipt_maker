import google.generativeai as genai
import os
from PIL import Image

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDk67KuFfhXTqlYFvxvwDfPq47K3a-IDjE")
genai.configure(api_key=GEMINI_API_KEY)

def extract_receipt_data(image_path):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = (
        """
        You are an expense extraction assistant. Given a photo of a receipt, extract the following fields in JSON:\n        {\n          \"store\": string,\n          \"date\": string (YYYY-MM-DD),\n          \"items\": [ {\"name\": string, \"price\": float} ],\n          \"amount\": float,\n          \"category\": string\n        }\n        Only output valid JSON. Do not include any explanation or text before or after the JSON. If you cannot extract, return: {\"store\": null, \"date\": null, \"items\": null, \"amount\": null, \"category\": null}
        """
    )
    img = Image.open(image_path)
    response = model.generate_content([prompt, img])
    try:
        return response.text
    except Exception as e:
        return None 