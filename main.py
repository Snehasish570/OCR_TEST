import os
import json

import re
from flask import Flask, request, jsonify, render_template
from PIL import Image
from paddleocr import PaddleOCR
from statistics import median
import numpy as np
import base64
import uuid
import cv2
from PIL import Image, ImageDraw, ImageFont
from functools import wraps

app = Flask(__name__)
# ---------- AUTH SETUP ----------
VALID_USERNAME = "snehasish"
VALID_PASSWORD = "sneha123"

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == VALID_USERNAME and auth.password == VALID_PASSWORD):
            return jsonify({"msg": "Unauthorized: Invalid username or password"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/upload", methods=["POST"])
@require_auth
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

    # Create unique txn_id
    txn_id = data.get("txn_id")
    txn_folder = f"{txn_id}_{str(uuid.uuid4())[:4]}"
    response["txn_id"] = txn_folder

    # Define directory structure
    base_dir = os.path.join(os.getcwd(), txn_folder)
    dirs = {
        "assets": os.path.join(base_dir, "Assets"),
        "logs": os.path.join(base_dir, "Logs"),
        "input": os.path.join(base_dir, "Input"),
        "output": os.path.join(base_dir, "Output"),
    }
    subdirs = {
        "assets_input": os.path.join(dirs["assets"], "input_image"),
        
        
        "input_request": os.path.join(dirs["input"], "request"),
        "output_response": os.path.join(dirs["output"], "response"),
        "output_ocr_image": os.path.join(dirs["output"], "OCR_IMAGE"),
        "output_processed_image": os.path.join(dirs["output"], "PROCESSED_IMAGE"),
        "output_ocr_text": os.path.join(dirs["output"], "OCR_TEXT"),
        "output_sorted_text":os.path.join(dirs["output"],"sorted_text")
    }

    # Create folders if not exist
    for d in list(dirs.values()) + list(subdirs.values()):
        os.makedirs(d, exist_ok=True)

    # Save input image
    img_data = base64.b64decode(data["input_image"])
    input_img_path = os.path.join(subdirs["assets_input"], "input.png")
    with open(input_img_path, "wb") as f:
        f.write(img_data)

    

    # Save request JSON
    req_json_path = os.path.join(subdirs["input_request"], "input.json")
    with open(req_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

     


    # Enhance for OCR
    def compute_skew_projection(img_data, delta=0.5, limit=90):
    
        img = cv2.imread(img_data, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"Can't open image")

        # Binarize (text = black)
        _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if np.mean(thresh) > 127:
            thresh = 255 - thresh  # ensure text is black

        best_angle = 0
        max_var = -1

        angles = np.arange(-limit, limit + delta, delta)
        for angle in angles:
            # Rotate small angle
            M = cv2.getRotationMatrix2D((thresh.shape[1]//2, thresh.shape[0]//2), angle, 1)
            rotated = cv2.warpAffine(thresh, M, (thresh.shape[1], thresh.shape[0]),
                                    flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

            # Projection profile (sum of pixels per row)
            proj = np.sum(rotated, axis=1)
            var = np.var(proj)  # variance = sharpness of text lines

            if var > max_var:
                max_var = var
                best_angle = angle

        print(f"Detected skew angle: {best_angle:.2f}°")
        return best_angle


    def rotate_image_auto(img_data, angle):
        img = cv2.imread(img_data)
        if img is None:
            raise FileNotFoundError(f"Can't open image")

        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)

        if abs(angle) < 0.5:  # tolerance
            print("Image already straight.")
            print("final_angle :",-angle)
            return img_data
        if angle==-90:
            angle = -angle
        else:
            if angle<0:
                angle=angle
            else:
                angle=-angle
        

        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        out_path = f"{txn_folder}/Output/PROCESSED_IMAGE/straightened.png"
        cv2.imwrite(out_path, rotated)
        return out_path
    
    angle=compute_skew_projection(input_img_path)
    deskewed_path=rotate_image_auto(input_img_path,angle)

    response["input_image"] = data["input_image"]

    # Run OCR
    ocr = PaddleOCR(use_angle_cls=True, lang="en")
    results = ocr.ocr(deskewed_path)

    texts = []
    if results and results[0]:
        texts = results[0]["rec_texts"]

    if texts:
        response["ocr_result"] = "\n".join(texts)
        response["msg"] = "Text detected"
        response["remark"] = "success"
        
    else:
        response["msg"] = "⚠️ No text detected"
        response["remark"] = "failed"
        response["doc_type"] = "Unknown Document"

    
    
    image_results = results[0]  
    boxes = image_results["rec_polys"]  
    texts = image_results["rec_texts"]   


    #sorted text
        
    def words_maker(boxes, texts):
        words = []
        for bbox, text in zip(boxes, texts):
            xs = [x for x, y in bbox]
            ys = [y for x, y in bbox]
            x_min, x_max = min(xs), max(xs)
            y_center = (min(ys) + max(ys)) / 2
            height = max(ys) - min(ys)
            words.append({
                "text": text,
                "x_min": x_min,
                "y_center": y_center,
                "height": height if height > 0 else None
            })
        return words

    def cluster_lines(words, multiplier=0.7, min_threshold=10):
        if not words:
            return []

        heights = [w["height"] for w in words if w["height"]]
        med_h = median(heights) if heights else 5
        threshold = max(med_h * multiplier, min_threshold)

        # Sort by vertical position
        words_sorted = sorted(words, key=lambda w: w["y_center"])

        lines = []
        current_line = [words_sorted[0]]
        current_y = words_sorted[0]["y_center"]

        for w in words_sorted[1:]:
            if abs(w["y_center"] - current_y) <= threshold:
                current_line.append(w)
                current_y = (current_y * (len(current_line) - 1) + w["y_center"]) / len(current_line)
            else:
                lines.append(current_line)
                current_line = [w]
                current_y = w["y_center"]

        if current_line:
            lines.append(current_line)

        return lines

    def build_text(lines):
        out = []
        for line in lines:
            # Sort each line by x position
            line_sorted = sorted(line, key=lambda w: w["x_min"])
            text_line = " ".join([w["text"] for w in line_sorted])
            out.append(text_line)
        return "\n".join(out)

    def main(boxes, texts, output):
        words = words_maker(boxes, texts)
        lines = cluster_lines(words)
        sorted_text = build_text(lines)

        # Write to file
        with open(output, "w", encoding="utf-8") as f:
            f.write(sorted_text)
        
        
        return sorted_text

    # Run main and save output
    if boxes and texts:
        main(boxes, texts, f"{txn_folder}/Output/sorted_text/sorted_output.txt")
    else:
        print("No OCR results found.")


    # Open image
    image = Image.open(deskewed_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(r"c:\WINDOWS\Fonts\NIRMALA.TTC", 10)

    # Draw boxes and text
    for box, text in zip(boxes, texts):
        pts = [(int(float(p[0])), int(float(p[1]))) for p in box]
        draw.polygon(pts, outline="green", width=3)
        x, y = pts[0]
        draw.text((x, y - 15 ), text, fill="red", font=font)

    image.save(f"{txn_folder}/Output/OCR_IMAGE/boxed_img.png")

    # Save OCR text output
    ocr_text_path = os.path.join(subdirs["output_ocr_text"], "ocr_text.txt")
    with open(ocr_text_path, "w", encoding="utf-8") as f:
        f.write(response["ocr_result"])

    #for checking which type of document
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
        return "Unknown Document"
    doc_name=detect_document_type(response["ocr_result"])

    response["doc_type"]=doc_name
    
    response["ocr_result"]=response["ocr_result"].replace("\n"," ")

    # Save response JSON
    response_json_path = os.path.join(subdirs["output_response"], "output.json")
    with open(response_json_path, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4)
    

    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)