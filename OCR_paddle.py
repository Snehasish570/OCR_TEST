import json
from paddleocr import PaddleOCR

# Initialize OCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Image path
img_path = "images/Aadhar10.jpg"

# Run OCR
results = ocr.ocr(img_path)

# Extract only the recognized texts
texts =results[0]["rec_texts"]

# Save to JSON file
with open("ocr_output.json", "w", encoding="utf-8") as f:
    json.dump(texts, f, ensure_ascii=False, indent=4)

print("✅ OCR results saved to ocr_output.json")
