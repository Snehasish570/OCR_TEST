# Install:
# pip install easyocr

import easyocr

reader = easyocr.Reader(['en'])
results = reader.readtext("images/Aadhar1.jpg")
text2 = "\n".join([res[1] for res in results])

with open("TEXT_FILES/Aadhar1_easyocr.txt", "w") as f:
    f.write(text2)
