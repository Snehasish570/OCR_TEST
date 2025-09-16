import pytesseract
from PIL import Image


# Load image
img = Image.open("images/Aadhar1.jpg")

# Extract text
text = pytesseract.image_to_string(img)

with open("TEXT_FILES/Aadhar1_pytessseract.txt", "w") as f:
    f.write(text)

