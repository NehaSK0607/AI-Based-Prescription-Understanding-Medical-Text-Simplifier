from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os

from PIL import Image
import pytesseract

app = FastAPI()

# 1. this is to allow frontend to access backend without CORS issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

# If a folder named uploads does NOT exist then Python creates it
# If it already exists then nothing happens (no error)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload")  # this line is building REST API endpoint
async def upload_file(file: UploadFile = File(...)):

    file_location = f"{UPLOAD_FOLDER}/{file.filename}"

    # saving the uploaded file in uploads folder
    with open(file_location, "wb+") as f:
        f.write(await file.read())

    # -------- OCR PART STARTS HERE --------

    # opening the uploaded image and converting it to grayscale to reduce complexity
    img = Image.open(file_location).convert("L")

    # we are adding threshold to remove noise and shadows (v.imp)
    img = img.point(lambda x: 0 if x < 140 else 255, '1')

    # we are enlarging the image to improve accuracy because tesseract works better with larger images
    img = img.resize((img.width * 2, img.height * 2))

    # oem 3 means we are using LSTM OCR Engine
    # psm 6 means we are treating the image as a single uniform block of text (good for paragraph/quotes)
    custom_config = r'--oem 3 --psm 6'

    text = pytesseract.image_to_string(img, config=custom_config)
    # basic cleaning of OCR text
    cleaned_text = text.lower()
    cleaned_text = cleaned_text.replace("s00", "500")
    cleaned_text = cleaned_text.replace("coid", "cold")
    cleaned_text = cleaned_text.replace("avold", "avoid")
    cleaned_text = " ".join(cleaned_text.split())
    # -------- SIMPLE MEDICAL UNDERSTANDING (RULE-BASED AI) --------

    medicines = {
        "pcm": "Paracetamol",
        "paracetamol": "Paracetamol",
        "cetzine": "Cetirizine",
        "cetirizine": "Cetirizine"
    }

    timings = {
        "bd": "twice a day (morning and evening)",
        "od": "once a day",
        "hs": "at night (before sleep)"
    }

    instructions = []

    found_medicines = []
    found_timings = []

    for key in medicines:
        if key in cleaned_text:
            found_medicines.append(medicines[key])

    for key in timings:
        if key in cleaned_text:
            found_timings.append(timings[key])

    if "avoid" in cleaned_text:
        instructions.append("Avoid cold drinks")
    if "after food" in cleaned_text:
        instructions.append("Take medicines after food")
    if "before food" in cleaned_text:
        instructions.append("Take medicines before food")



    # -------- OCR PART ENDS HERE --------

    return {
    "filename": file.filename,
    "message": "File uploaded successfully",
    "extracted_text": text,
    "cleaned_text": cleaned_text,
    "found_medicines": found_medicines,
    "found_timings": found_timings,
    "instructions": instructions
}


