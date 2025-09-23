import cv2
import numpy as np
from paddleocr import PaddleOCR
import json
from PIL import Image, ImageDraw, ImageFont


def enhance_for_ocr(image_path, output_path="enhanced.png"):
    img = cv2.imread(image_path)
    blur = cv2.GaussianBlur(img, (5,5), 2)
    sharp = cv2.addWeighted(img, 1.5, blur, -0.5, 0)
    denoised = cv2.fastNlMeansDenoisingColored(sharp, None, 6, 10, 9, 21)
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    bg = cv2.medianBlur(gray, 31)
    norm = cv2.divide(gray, bg, scale=255)

   
    # Save processed image
    cv2.imwrite(output_path,norm )

    return norm


# Example usage:
enhanced_img = enhance_for_ocr("images/Aadhar10.jpg", "enhanced.png")

image_path = "enhanced.png"
def run_ocr(image_path, output_json="ocr_output.json"):
    # Initialize PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en')

    # Run OCR
    results = ocr.ocr(image_path)

    # Extract recognized texts (handling PaddleOCR’s result structure)
    texts = results[0]["rec_texts"]

    # Save to JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=4)

    print(f"✅ OCR results saved to {output_json}")
    return texts




if __name__ == "__main__":
    texts = run_ocr(image_path, "ocr_output.json")
    print("Recognized Texts:", texts)
    