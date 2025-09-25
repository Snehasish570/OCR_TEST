from flask import Flask, request, render_template
from PIL import Image
from paddleocr import PaddleOCR
import io
import numpy as np
import cv2

app = Flask(__name__)


@app.route("/",method=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    
    file = request.files["image"]

    ocr = PaddleOCR(use_angle_cls=True, lang='en')

    # Read image with PIL
    img = Image.open(io.BytesIO(file.read())).convert("RGB")

    # Convert PIL -> numpy array (OpenCV format BGR)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Run OCR
    results = ocr.ocr(img_cv)

    
    if results and results[0]["rec_texts"]:
        texts = results[0]["rec_texts"]
    else:
        texts.append("⚠️ No text detected")

    return render_template("result.html", extracted_text=texts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


