from flask import Flask, request, jsonify
from PIL import Image
from paddleocr import PaddleOCR
import io
import numpy as np
import base64
import uuid   

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    response = {
        "input_image": "",
        "ocr_result": "",
        "txn_id": "",
        "msg": "",
        "remark": ""
    }

    data = request.get_json()

    if not data or "input_image" not in data:
        response["msg"] = "No base64 image found in request!"
        response["remark"] = "failed"
        return jsonify(response)

    
    # ✅ Generate UUID as txn_id
    response["txn_id"] = str(uuid.uuid4())

    # Decode base64 string
    img_data = base64.b64decode(data["input_image"])
    img = Image.open(io.BytesIO(img_data)).convert("RGB")

    # Save back the same base64 for output
    response["input_image"] = data["input_image"]

    # Convert to NumPy for OCR
    img_np = np.array(img)

    # Run OCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    results = ocr.ocr(img_np)

    texts = []
    if results and results[0]["rec_texts"]:
        texts = results[0]["rec_texts"]

    if texts:
        response["ocr_result"] = "  ".join(texts)
        response["msg"] = " Text detected"
        response["remark"] = "success"
    else:
        response["msg"] = "⚠️ No text detected"
        response["remark"] = "failed"

    

    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



