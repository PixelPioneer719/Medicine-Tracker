from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Field, Session, create_engine, select
import os
import shutil
from fastapi.responses import FileResponse

class MedicineBase(SQLModel):
    name: str
    dose: str
    time_of_day: str  # morning / afternoon / evening
    notes: Optional[str] = None  # Tablet or Syrup
    active: bool = True
    prescription_url: Optional[str] = None  # path to image file

class Medicine(MedicineBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class MedicineCreate(MedicineBase):
    pass

class MedicineRead(MedicineBase):
    id: int

class MedicineUpdate(SQLModel):
    name: Optional[str] = None
    dose: Optional[str] = None
    time_of_day: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None
    prescription_url: Optional[str] = None

# Use absolute path for database to persist across restarts
import pathlib
db_dir = pathlib.Path(__file__).parent
DATABASE_URL = f"sqlite:///{db_dir}/medicine_db.sqlite"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI(title="Prabhas Medicine Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/prescriptions", StaticFiles(directory=UPLOAD_DIR), name="prescriptions")

# Mount static files AFTER CORS
static_dir = db_dir
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def serve_app():
    """Serve the HTML app"""
    return FileResponse("index.html", media_type="text/html")

@app.get("/prescriptions/{filename}")
def get_prescription(filename: str):
    """Serve prescription images"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "Prescription not found")
    return FileResponse(file_path)

@app.post("/medicines", response_model=MedicineRead)
def create_medicine(medicine: MedicineCreate, session: Session = Depends(get_session)):
    db_medicine = Medicine.from_orm(medicine)
    session.add(db_medicine)
    session.commit()
    session.refresh(db_medicine)
    return db_medicine

@app.get("/medicines", response_model=List[MedicineRead])
def list_medicines(time_of_day: Optional[str] = None, session: Session = Depends(get_session)):
    statement = select(Medicine)
    if time_of_day:
        statement = statement.where(Medicine.time_of_day == time_of_day)
    results = session.exec(statement).all()
    return results

@app.get("/medicines/{medicine_id}", response_model=MedicineRead)
def get_medicine(medicine_id: int, session: Session = Depends(get_session)):
    med = session.get(Medicine, medicine_id)
    if not med:
        raise HTTPException(404, "Medicine not found")
    return med

@app.put("/medicines/{medicine_id}", response_model=MedicineRead)
def update_medicine(
    medicine_id: int,
    medicine_update: MedicineUpdate,
    session: Session = Depends(get_session)
):
    med = session.get(Medicine, medicine_id)
    if not med:
        raise HTTPException(404, "Medicine not found")

    update_data = medicine_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(med, key, value)

    session.add(med)
    session.commit()
    session.refresh(med)
    return med

@app.delete("/medicines/{medicine_id}")
def delete_medicine(medicine_id: int, session: Session = Depends(get_session)):
    med = session.get(Medicine, medicine_id)
    if not med:
        raise HTTPException(404, "Medicine not found")

    session.delete(med)
    session.commit()
    return {"status": "deleted"}


@app.post("/upload-prescription/{medicine_id}")
def upload_prescription(
    medicine_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    med = session.get(Medicine, medicine_id)
    if not med:
        raise HTTPException(404, "Medicine not found")

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Create unique filename
    filename = f"{medicine_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        # Write file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update medicine with prescription URL
        med.prescription_url = f"prescriptions/{filename}"
        session.add(med)
        session.commit()
        session.refresh(med)
        
        return {"status": "uploaded", "file": med.prescription_url}
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")