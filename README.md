# Medicine Tracker - Prabhas

A simple web app to track daily medicines (tablets and syrups) with prescription uploads.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

3. Open browser:
```
http://127.0.0.1:8000
```

## Features

✓ Add/Edit/Delete medicines  
✓ Track tablet and syrup dosages  
✓ Organize by time of day (morning, afternoon, evening)  
✓ Upload prescription images  
✓ View prescriptions  
✓ Dark/Light mode  
✓ All data persists in database  

## Database

Medicines are stored in `medicine_db.sqlite` - automatically created on first run.

## Prescriptions

Uploaded images are stored in the `prescriptions/` folder and linked to medicines.

---

Made by Prabhas
