from flask import Flask, request, jsonify
from PIL import Image
from paddleocr import PaddleOCR
import io
import numpy as np
import base64
import uuid
import re

app = Flask(__name__)


@app.route("/", methods=["POST"])
def upload():
    response = {
        "input_image": "",
        "ocr_result": "",
        "txn_id": "",
        "msg": "",
        "remark": "",
        "doc_type": "",
    }

    data = request.get_json()

    if not data or "input_image" not in data:
        response["msg"] = "No base64 image found in request!"
        response["remark"] = "failed"
        return jsonify(response)

    
    txn_id = data.get("txn_id", "txn")
    response["txn_id"] = f"{txn_id}_{str(uuid.uuid4())[:4]}"

    # Decode base64 string
    img_data = base64.b64decode(data["input_image"])
    img = Image.open(io.BytesIO(img_data)).convert("RGB")

    # Save back the same base64 for output
    response["input_image"] = data["input_image"]

    # Convert to NumPy for OCR
    img_np = np.array(img)

    # Run OCR
    ocr = PaddleOCR(use_angle_cls=True, lang="en")
    results = ocr.ocr(img_np)

    texts = []
    if results and results[0]["rec_texts"]:
        texts = results[0]["rec_texts"]

    def detect_document_type(extracted_text: str) -> str:

        if re.search(r"\b\d{12}\b", extracted_text) or re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", extracted_text):
            return "Aadhaar Card"

        if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", extracted_text):
            return "PAN Card"

        if re.search(r"\b[A-Z][0-9]{7}\b", extracted_text):
            return "Passport"

        if re.search(r"\b[A-Z]{2}[- ]?\d{2}[- ]?\d{4,10}\b", extracted_text):
            return "Driving License"

        if re.search(r"\b[A-Z]{3}[0-9]{7}\b", extracted_text):
            return "Voter ID"

        if re.search(r"\b\d{9,18}\b", extracted_text) and re.search(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", extracted_text):
            return "Bank Cheque / Account Document"
        
        if re.search(r"\b(?:\d{4}[- ]?){3}\d{4}\b", extracted_text):
            return "Credit/Debit Card"
        
        if re.search(r"\b\d{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b", extracted_text):
            return "GSTIN"

        return "Unknown Document"

    if texts:
        response["ocr_result"] = "  ".join(texts)
        response["msg"] = "Text detected"
        response["remark"] = "success"
        response["doc_type"] = detect_document_type(response["ocr_result"])
    else:
        response["msg"] = "⚠️ No text detected"
        response["remark"] = "failed"
        response["doc_type"] = "Unknown Document"

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
