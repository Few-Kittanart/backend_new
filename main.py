from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List
from database import Base
from models import Building, PredictionTable, Unit, NumberOfUsers, ExamStatus, SemesterStatus, Member , GroupBuilding , Holiday 
from schemas import BuildingCreate, LoginData, UnitCreate, NumberOfUsersCreate, ExamStatusCreate, SemesterStatusCreate, MemberCreate, PredictionRequest, PredictionResponse , HolidayCreate  
from predict import predict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
import base64
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import NewsBase
from models import News  # Ensure this model exists
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse


DATABASE_URL = "mysql+pymysql://root:@localhost/efsdata"

IMAGES_DIRECTORY = "images" 

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
origins = [
    "http://localhost:3000",  # React frontend ที่รันอยู่บน localhost:3000
    "http://127.0.0.1:3000",   # หรือใช้ localhost ที่มี IP 127.0.0.1
]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Add this line
)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return f"{base64.urlsafe_b64encode(salt).decode('utf-8')}:{key.decode('utf-8')}"


def verify_password(stored_password, provided_password):
    salt, key = stored_password.split(":")
    salt = base64.urlsafe_b64decode(salt)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return key == base64.urlsafe_b64encode(kdf.derive(provided_password.encode('utf-8'))).decode('utf-8')



Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/holidays/", response_model=HolidayCreate)
def create_holiday(holiday: HolidayCreate, db: Session = Depends(get_db)):
    db_holiday = Holiday(
        years=holiday.years,
        month=holiday.month,
        Holiday=holiday.Holiday,  # ใช้ holiday.Holiday ตามที่ frontend ส่งมา
    )
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday

@app.get("/holidays/")
def get_holidays(
    year: int = Query(None),
    month: int = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Holiday)
    if year:
        query = query.filter(Holiday.years == year)
    if month:
        query = query.filter(Holiday.month == month)
    return query.all()

@app.put("/holidays/{holiday_id}", response_model=HolidayCreate)
def update_holiday(
    holiday_id: int, 
    holiday: HolidayCreate, 
    db: Session = Depends(get_db)
):
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not db_holiday:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลวันหยุด")
    # อัปเดตข้อมูล
    db_holiday.years = holiday.years
    db_holiday.month = holiday.month
    db_holiday.Holiday = holiday.Holiday  # ใช้ holiday.Holiday ตามที่ frontend ส่งมา
    db.commit()
    db.refresh(db_holiday)
    return db_holiday

# DELETE (Delete)
@app.delete("/holidays/{holiday_id}")
def delete_holiday(
    holiday_id: int, 
    db: Session = Depends(get_db)
):
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not db_holiday:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลวันหยุด")
    db.delete(db_holiday)
    db.commit()
    return {"detail": "ลบข้อมูลสำเร็จ"}

@app.get("/images/{filename}")
async def get_image(filename: str):
    print(f"Requested image: {filename}")
    image_path = os.path.join(IMAGES_DIRECTORY, filename)
    print(f"Full path: {image_path}")
    print(f"File exists: {os.path.exists(image_path)}")
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path)

@app.get("/news", response_model=List[NewsBase])
def get_news(db: Session = Depends(get_db)):
    news = db.query(News).order_by(News.created_at.desc()).all()
    return news

@app.get("/news", response_model=List[NewsBase])
def get_news(db: Session = Depends(get_db)):
    news = db.query(News).order_by(News.created_at.desc()).all()
    return news

@app.get("/news/{news_id}", response_model=NewsBase)
def get_news_by_id(news_id: int, db: Session = Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

# CRUD for Building
@app.post("/buildings/", response_model=BuildingCreate)
def create_building(building: BuildingCreate, db: Session = Depends(get_db)):
    db_building = Building(
        code=building.code, 
        name=building.name, 
        area=building.area,
        idGroup=building.idGroup
    )
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building

@app.get("/buildings/{building_id}", response_model=BuildingCreate)
def read_building(building_id: int, db: Session = Depends(get_db)):
    db_building = db.query(Building).filter(Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return db_building

@app.get("/buildings/", response_model=List[BuildingCreate])
def read_buildings(db: Session = Depends(get_db)):
    buildings = db.query(Building).all()
    return buildings

@app.get("/groupbuildings")
def get_group_buildings(db: Session = Depends(get_db)):
    buildings = db.query(Building).all()
    # ปรับแต่งรูปแบบการตอบกลับให้มีเฉพาะข้อมูลที่ต้องการ
    return [{"id": building.id, "name": building.name,} for building in buildings]

@app.get("/groupofbuildings")
def get_group_buildings(db: Session = Depends(get_db)):
    buildings = db.query(GroupBuilding).all()
    # ปรับแต่งรูปแบบการตอบกลับให้มีเฉพาะข้อมูลที่ต้องการ
    return [{"id": building.id, "name": building.name,} for building in buildings]

@app.put("/buildings/{building_id}", response_model=BuildingCreate)
def update_building(building_id: int, building: BuildingCreate, db: Session = Depends(get_db)):
    db_building = db.query(Building).filter(Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    db_building.code = building.code
    db_building.name = building.name
    db_building.area = building.area
    db.commit()
    db.refresh(db_building)
    return db_building

@app.delete("/buildings/{building_id}")
def delete_building(building_id: int, db: Session = Depends(get_db)):
    db_building = db.query(Building).filter(Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    db.delete(db_building)
    db.commit()
    return {"detail": "Building deleted"}

# CRUD for Unit
@app.post("/units/", response_model=UnitCreate)
def create_unit(unit: UnitCreate, db: Session = Depends(get_db)):
    db_unit = Unit(years=unit.years, month=unit.month, amount=unit.amount, idBuilding=unit.idBuilding)
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@app.get("/units/{unit_id}", response_model=UnitCreate)
def read_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    return db_unit

@app.get("/units/", response_model=UnitCreate)
def read_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(Unit)
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    return db_unit



@app.get("/unit/")
def read_unit(
    year: int = Query(None),
    month: int = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Unit).filter(Unit.id != 0)
    if year is not None:
        query = query.filter(Unit.years == year)
    if month is not None:
        query = query.filter(Unit.month == month)
    
    units = query.all()
    return units

@app.get("/units")
def get_units_by_year_month(
    year: int = Query(None), 
    month: int = Query(None), 
    db: Session = Depends(get_db)
):
    query = db.query(Unit)
    if year is not None:
        query = query.filter(Unit.years == year)
    if month is not None:
        query = query.filter(Unit.month == month)
    
    units = query.all()
    return units

@app.put("/units/{unit_id}", response_model=UnitCreate)
def update_unit(unit_id: int, unit: UnitCreate, db: Session = Depends(get_db)):
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    db_unit.years = unit.years
    db_unit.month = unit.month
    db_unit.amount = unit.amount
    db_unit.idBuilding = unit.idBuilding
    db.commit()
    db.refresh(db_unit)
    return db_unit

@app.delete("/units/{unit_id}")
def delete_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(db_unit)
    db.commit()
    return {"detail": "Unit deleted"}

# CRUD for NumberOfUsers
@app.post("/numberOfUsers/", response_model=NumberOfUsersCreate)
def create_number_of_users(number_of_users: NumberOfUsersCreate, db: Session = Depends(get_db)):
    db_number_of_users = NumberOfUsers(years=number_of_users.years, month=number_of_users.month, amount=number_of_users.amount)
    db.add(db_number_of_users)
    db.commit()
    db.refresh(db_number_of_users)
    return db_number_of_users

@app.post("/add-numberofusers/")
def add_number_of_users(data: dict, db: Session = Depends(get_db)):
    # Create entries for all 12 months with the same user amount
    added_entries = []
    year = data.get("years")
    amount = data.get("amount")
    
    for month in range(1, 13):
        # Check if entry already exists for this year and month
        existing = db.query(NumberOfUsers).filter(
            NumberOfUsers.years == year, 
            NumberOfUsers.month == month
        ).first()
        
        if existing:
            # Update existing entry
            existing.amount = amount
            db.commit()
            db.refresh(existing)
            added_entries.append(existing)
        else:
            # Create new entry
            new_entry = NumberOfUsers(years=year, month=month, amount=amount)
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            added_entries.append(new_entry)
    
    return {"message": "Data added successfully", "entries": len(added_entries)}

@app.get("/numberOfUsers/{number_of_users_id}", response_model=NumberOfUsersCreate)
def read_number_of_users(number_of_users_id: int, db: Session = Depends(get_db)):
    db_number_of_users = db.query(NumberOfUsers).filter(NumberOfUsers.id == number_of_users_id).first()
    if db_number_of_users is None:
        raise HTTPException(status_code=404, detail="Number of users not found")
    return db_number_of_users

@app.get("/numberOfUsers", response_model=List[NumberOfUsersCreate])
def read_all_number_of_users(db: Session = Depends(get_db)):
    db_number_of_users = db.query(NumberOfUsers).all()
    if not db_number_of_users:
        return []
    return db_number_of_users

@app.put("/numberOfUsers/{number_of_users_id}", response_model=NumberOfUsersCreate)
def update_number_of_users(number_of_users_id: int, number_of_users: NumberOfUsersCreate, db: Session = Depends(get_db)):
    db_number_of_users = db.query(NumberOfUsers).filter(NumberOfUsers.id == number_of_users_id).first()
    if db_number_of_users is None:
        raise HTTPException(status_code=404, detail="Number of users not found")
    db_number_of_users.years = number_of_users.years
    db_number_of_users.month = number_of_users.month
    db_number_of_users.amount = number_of_users.amount
    db.commit()
    db.refresh(db_number_of_users)
    return db_number_of_users

@app.put("/update-numberofusers/{year}")
def update_number_of_users_by_year(year: int, data: dict, db: Session = Depends(get_db)):
    # Find all entries for the specified year
    entries = db.query(NumberOfUsers).filter(NumberOfUsers.years == year).all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="No data found for this year")
    
    new_year = data.get("years")
    new_amount = data.get("amount")
    
    # Check if the year already exists and it's not the same as the current year
    if new_year != year:
        existing = db.query(NumberOfUsers).filter(NumberOfUsers.years == new_year).first()
        if existing:
            raise HTTPException(status_code=400, detail="Year already exists, cannot update")
    
    # Update all entries for the year
    count = 0
    for entry in entries:
        entry.years = new_year
        entry.amount = new_amount
        count += 1
    
    db.commit()
    return {"message": "Data updated successfully", "updated_count": count}

@app.delete("/numberOfUsers/{number_of_users_id}")
def delete_number_of_users(number_of_users_id: int, db: Session = Depends(get_db)):
    db_number_of_users = db.query(NumberOfUsers).filter(NumberOfUsers.id == number_of_users_id).first()
    if db_number_of_users is None:
        raise HTTPException(status_code=404, detail="Number of users not found")
    db.delete(db_number_of_users)
    db.commit()
    return {"detail": "Number of users deleted"}

@app.delete("/delete-numberofusers/{year}")
def delete_number_of_users_by_year(year: int, db: Session = Depends(get_db)):
    # Find all entries for the specified year
    entries = db.query(NumberOfUsers).filter(NumberOfUsers.years == year).all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="No data found for this year")
    
    # Delete all entries for the year
    count = 0
    for entry in entries:
        db.delete(entry)
        count += 1
    
    db.commit()
    return {"message": "Data deleted successfully", "deleted_count": count}

# CRUD for ExamStatus
@app.post("/examStatus/", response_model=ExamStatusCreate)
def create_exam_status(exam_status: ExamStatusCreate, db: Session = Depends(get_db)):
    db_exam_status = ExamStatus(years=exam_status.years, month=exam_status.month, status=exam_status.status)
    db.add(db_exam_status)
    db.commit()
    db.refresh(db_exam_status)
    return db_exam_status

@app.get("/examStatus/{exam_status_id}", response_model=ExamStatusCreate)
def read_exam_status(exam_status_id: int, db: Session = Depends(get_db)):
    db_exam_status = db.query(ExamStatus).filter(ExamStatus.id == exam_status_id).first()
    if db_exam_status is None:
        raise HTTPException(status_code=404, detail="Exam status not found")
    return db_exam_status

@app.get("/examStatus/", response_model=List[ExamStatusCreate])
def read_all_exam_status(db: Session = Depends(get_db)):
    db_exam_status = db.query(ExamStatus).all()
    if not db_exam_status:
        return []
    return db_exam_status

@app.delete("/examStatus/{exam_status_id}")
def delete_exam_status(exam_status_id: int, db: Session = Depends(get_db)):
    db_exam_status = db.query(ExamStatus).filter(ExamStatus.id == exam_status_id).first()
    if db_exam_status is None:
        raise HTTPException(status_code=404, detail="Exam status not found")
    db.delete(db_exam_status)
    db.commit()
    return {"detail": "Exam status deleted"}

# CRUD for SemesterStatus
@app.post("/semesterStatus/", response_model=SemesterStatusCreate)
def create_semester_status(semester_status: SemesterStatusCreate, db: Session = Depends(get_db)):
    db_semester_status = SemesterStatus(years=semester_status.years, month=semester_status.month, status=semester_status.status)
    db.add(db_semester_status)
    db.commit()
    db.refresh(db_semester_status)
    return db_semester_status

@app.get("/semesterStatus/{semester_status_id}", response_model=SemesterStatusCreate)
def read_semester_status(semester_status_id: int, db: Session = Depends(get_db)):
    db_semester_status = db.query(SemesterStatus).filter(SemesterStatus.id == semester_status_id).first()
    if db_semester_status is None:
        raise HTTPException(status_code=404, detail="Semester status not found")
    return db_semester_status

@app.get("/semesterStatus/", response_model=List[SemesterStatusCreate])
def read_all_semester_status(db: Session = Depends(get_db)):
    db_semester_status = db.query(SemesterStatus).all()
    if not db_semester_status:
        return []
    return db_semester_status

@app.get("/semesterstatus", response_model=List[SemesterStatusCreate])
def read_all_semester_status_lowercase(db: Session = Depends(get_db)):
    return read_all_semester_status(db)

@app.put("/semesterStatus/{semester_status_id}", response_model=SemesterStatusCreate)
def update_semester_status(semester_status_id: int, semester_status: SemesterStatusCreate, db: Session = Depends(get_db)):
    db_semester_status = db.query(SemesterStatus).filter(SemesterStatus.id == semester_status_id).first()
    if db_semester_status is None:
        raise HTTPException(status_code=404, detail="Semester status not found")
    db_semester_status.years = semester_status.years
    db_semester_status.month = semester_status.month
    db_semester_status.status = semester_status.status
    db.commit()
    db.refresh(db_semester_status)
    return db_semester_status

@app.delete("/semesterStatus/{semester_status_id}")
def delete_semester_status(semester_status_id: int, db: Session = Depends(get_db)):
    db_semester_status = db.query(SemesterStatus).filter(SemesterStatus.id == semester_status_id).first()
    if db_semester_status is None:
        raise HTTPException(status_code=404, detail="Semester status not found")
    db.delete(db_semester_status)
    db.commit()
    return {"detail": "Semester status deleted"}

# CRUD for Member
@app.post("/members/", response_model=MemberCreate)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    db_user = db.query(Member).filter(Member.username == member.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = hash_password(member.password)

    db_member = Member(
        username=member.username,
        password=hashed_password,
        fname=member.fname,
        lname=member.lname,
        email=member.email,
        phone=member.phone,
        status=member.status
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@app.get("/members/{member_id}", response_model=MemberCreate)
def read_member(member_id: int, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return db_member

@app.get("/members/", response_model=List[MemberCreate])
def read_all_members(db: Session = Depends(get_db)):
    db_members = db.query(Member).all()
    if not db_members:
        return []
    return db_members

@app.put("/members/{member_id}", response_model=MemberCreate)
def update_member(member_id: int, member: MemberCreate, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    db_member.username = member.username
    db_member.password = member.password
    db_member.fname = member.fname
    db_member.lname = member.lname
    db_member.email = member.email
    db_member.phone = member.phone
    db_member.status = member.status
    db.commit()
    db.refresh(db_member)
    return db_member

@app.delete("/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(db_member)
    db.commit()
    return {"detail": "Member deleted"}

@app.post("/login/")
def login(data: LoginData, db: Session = Depends(get_db)):
    db_user = db.query(Member).filter(Member.username == data.username).first()
    if not db_user or not verify_password(db_user.password, data.password):
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "status": db_user.status,
        "name": f"{db_user.fname} {db_user.lname}"
    }


def check_existing_prediction(db: Session, year: int, month: int) -> List[PredictionResponse]:
    # ดึงข้อมูลจากฐานข้อมูล
    existing_records = db.query(PredictionTable).filter(
        PredictionTable.year_current == year,
        PredictionTable.month_current == month
    ).all()
    
    if not existing_records:
        return []
    
    predictions = []
    for record in existing_records:
        # สร้าง response object โดยไม่มี holiday
        prediction = PredictionResponse(
            building=str(record.building),
            area=record.area,
            prediction=record.prediction,
            unit=record.unit,
            # ไม่รวม holiday
            modelName=record.modelName,
            month_current=record.month_current,
            year_current=record.year_current,
            month_predict=record.month_predict,
            year_predict=record.year_predict
        )
        predictions.append(prediction)
    
    return predictions


def save_prediction_to_db(db: Session, predictions):
    for pred in predictions:
        # สร้าง object โดยไม่รวมฟิลด์ holiday
        prediction_db = PredictionTable(
            building=pred["building"],
            area=pred["area"],
            prediction=pred["prediction"],
            unit=pred["unit"],
            # ไม่รวม holiday
            modelName=pred["modelName"],
            month_current=pred["month_current"],
            year_current=pred["year_current"],
            month_predict=pred["month_predict"],
            year_predict=pred["year_predict"]
        )
        db.add(prediction_db)
    db.commit()


@app.post("/predict-or-fetch", response_model=List[PredictionResponse])  # กำหนด response model ให้เป็น List[PredictionResponse]
def predict_or_fetch(request: PredictionRequest, db: Session = Depends(get_db)) -> List[PredictionResponse]:
    # ตรวจสอบว่ามีข้อมูลในฐานข้อมูลหรือไม่
    existing_predictions = check_existing_prediction(db, request.year, request.month)

    if existing_predictions:
        # ถ้ามีข้อมูลแล้วให้ดึงข้อมูลมาแสดง
        return existing_predictions
    else:
        # ถ้าไม่มีข้อมูล ให้ทำการพยากรณ์
        predictions = predict(request, db)
        # บันทึกผลลัพธ์ลงในฐานข้อมูล
        save_prediction_to_db(db, predictions)
        return predictions

def get_latest_year_month(db: Session):
    try:
        latest_entry = db.query(PredictionTable).order_by(
            PredictionTable.year_current.desc(),
            PredictionTable.month_current.desc()
        ).first()
        return (latest_entry.year_current, latest_entry.month_current) if latest_entry else (None, None)
    except Exception as e:
        print(f"Error getting latest year/month: {str(e)}")
        return None, None
    
@app.get("/current-month")
def get_current_month(db: Session = Depends(get_db)):
    latest_record = db.query(Unit).order_by(Unit.years.desc(), Unit.month.desc()).first()
    if not latest_record:
        raise HTTPException(status_code=404, detail="No data found")
    return {"year": latest_record.years, "month": latest_record.month}

@app.get("/check-predictions")
def check_predictions(year: int = Query(...), month: int = Query(...), db: Session = Depends(get_db)):
    predictions = db.query(PredictionTable).filter_by(year_current=year, month_current=month).all()
    
    if not predictions:
        return []
    
    return predictions

@app.get("/prediction_sum_by_month")
def get_prediction_sum_by_month(db: Session = Depends(get_db)):
    try:
        latest_year, latest_month = get_latest_year_month(db)
        
        if not latest_year or not latest_month:
            return JSONResponse(
                status_code=404,
                content={"detail": "No prediction data found"}
            )

        predictions = db.query(PredictionTable).filter(
            PredictionTable.year_current == latest_year,
            PredictionTable.month_current == latest_month
        ).all()

        thai_months = {
            1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 
            5: 'พ.ค.', 6: 'มิ.ย.', 7: 'ก.ค.', 8: 'ส.ค.', 
            9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'
        }

        monthly_predictions = {}
        for pred in predictions:
            # Validate month_predict range
            if not (1 <= pred.month_predict <= 12):
                continue

            key = (pred.year_predict, pred.month_predict)
            if key not in monthly_predictions:
                monthly_predictions[key] = {
                    'year_predict': pred.year_predict,
                    'month_predict': pred.month_predict,
                    'month_thai': thai_months.get(pred.month_predict, 'N/A'),
                    'prediction': 0
                }
            monthly_predictions[key]['prediction'] += pred.prediction

        result = list(monthly_predictions.values())
        result.sort(key=lambda x: (x['year_predict'], x['month_predict']))

        formatted_result = []
        for item in result:
            formatted_result.append({
                'year_predict': int(item['year_predict']) + 543,
                'month_predict': item['month_thai'],
                'prediction': round(float(item['prediction']))
            })

        return formatted_result[:12]

    except Exception as e:
        print(f"Error in prediction_sum_by_month: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
@app.get("/yearly-comparison")
def get_yearly_comparison(db: Session = Depends(get_db)):
    # Get the most recent year and month used for prediction
    latest_year, latest_month = get_latest_year_month(db)
    
    if not latest_year or not latest_month:
        raise HTTPException(status_code=404, detail="No prediction data found")
    
    # Get predictions for the current month
    predictions = db.query(PredictionTable).filter(
        PredictionTable.year_current == latest_year,
        PredictionTable.month_current == latest_month
    ).all()
    
    # Get actual unit data for comparison
    # We'll get the latest 12 months of actual data
    current_month = latest_month
    current_year = latest_year
    
    # Calculate the start month/year (12 months prior)
    start_month = current_month + 1 if current_month < 12 else 1
    start_year = current_year - 1 if current_month >= 12 else current_year - 1
    
    # Get actual unit data for the past 12 months
    actual_data = []
    temp_month = start_month
    temp_year = start_year
    
    # Collect 12 months of actual data
    for _ in range(12):
        # Query the unit data for this month/year
        unit_data = db.query(Unit).filter(
            Unit.years == temp_year,
            Unit.month == temp_month
        ).all()
        
        # Group by building and sum the units
        month_total = sum(unit.amount for unit in unit_data) if unit_data else 0
        
        actual_data.append({
            "month": f"{temp_month}-{temp_year}",
            "actual": month_total
        })
        
        # Move to next month
        temp_month += 1
        if temp_month > 12:
            temp_month = 1
            temp_year += 1
    
    # Format prediction data
    # We'll use the next 12 months from current
    forecast_data = []
    temp_month = latest_month + 1 if latest_month < 12 else 1
    temp_year = latest_year if latest_month < 12 else latest_year + 1
    
    # Group predictions by month
    pred_by_month = {}
    for pred in predictions:
        key = (pred.year_predict, pred.month_predict)
        if key not in pred_by_month:
            pred_by_month[key] = 0
        pred_by_month[key] += pred.prediction
    
    # Collect 12 months of forecast data
    for _ in range(12):
        key = (temp_year, temp_month)
        forecast_value = pred_by_month.get(key, 0)
        
        forecast_data.append({
            "month": f"{temp_month}-{temp_year}",
            "forecast": round(forecast_value)
        })
        
        # Move to next month
        temp_month += 1
        if temp_month > 12:
            temp_month = 1
            temp_year += 1
    
    # Combine the data
    result = []
    for i in range(12):
        result.append({
            "month": actual_data[i]["month"],
            "actual": actual_data[i]["actual"],
            "forecast": forecast_data[i]["forecast"],
            "actual_year_month": actual_data[i]["month"]
        })
    
    # Convert month numbers to Thai month abbreviations
    thai_months = {
        1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.',
        7: 'ก.ค.', 8: 'ส.ค.', 9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'
    }
    
    for item in result:
        month_num = int(item["month"].split("-")[0])
        year = int(item["month"].split("-")[1]) + 543
        item["month"] = f"{thai_months[month_num]} {year}"
        
        actual_month_num = int(item["actual_year_month"].split("-")[0])
        actual_year = int(item["actual_year_month"].split("-")[1]) + 543
        item["actual_year_month"] = f"{thai_months[actual_month_num]} {actual_year}"
    
    return result

@app.get("/group-prediction-sum", response_model=List[dict])
def get_prediction_sum_by_group(db: Session = Depends(get_db)):
    # ดึงข้อมูลกลุ่มอาคารทั้งหมด
    groups = db.query(GroupBuilding).all()
    group_map = {group.id: group.name for group in groups}  # แมป id กลุ่มกับชื่อ
    
    # ดึงข้อมูลการพยากรณ์ล่าสุด
    latest_year, latest_month = get_latest_year_month(db)
    predictions = db.query(PredictionTable).filter(
        PredictionTable.year_current == latest_year,
        PredictionTable.month_current == latest_month
    ).all()
    
    buildings = db.query(Building).all()
    groups = db.query(GroupBuilding).all()
    
    # Create mappings
    building_info = {b.id: {"name": b.name, "group_id": b.idGroup} for b in buildings}
    group_info = {g.id: g.name for g in groups}
    
    # Process data
    grouped_data = {}
    for pred in predictions:
        building_id = next((b_id for b_id, info in building_info.items() if info["name"] == pred.building), None)
        
        if not building_id or building_id not in building_info:
            continue
            
        group_id = building_info[building_id]["group_id"]
        group_name = group_info.get(group_id, "อื่นๆ")
        
        if group_name not in grouped_data:
            grouped_data[group_name] = {
                "group_name": group_name,
                "prediction_sum": 0,
                "buildings": []
            }
        
        grouped_data[group_name]["prediction_sum"] += pred.prediction
        
        # Update building list
        building_entry = next((b for b in grouped_data[group_name]["buildings"] if b["name"] == pred.building), None)
        if building_entry:
            building_entry["prediction"] += pred.prediction
        else:
            grouped_data[group_name]["buildings"].append({
                "name": pred.building,
                "prediction": pred.prediction
            })
    
    # Format response
    result = list(grouped_data.values())
    for group in result:
        group["prediction_sum"] = round(group["prediction_sum"])
        for building in group["buildings"]:
            building["prediction"] = round(building["prediction"])
    
    return result

@app.get("/building_predictions/{year}/{month}")
def get_building_predictions(year: int, month: int, db: Session = Depends(get_db)):
    # Get predictions for specific year and month
    predictions = db.query(PredictionTable).filter(
        PredictionTable.year_predict == year,
        PredictionTable.month_predict == month
    ).all()
    
    if not predictions:
        raise HTTPException(status_code=404, detail="No predictions found for this year and month")
    
    # Format response to match what the DrillDownChart expects
    result = []
    for pred in predictions:
        result.append({
            "building": pred.building,
            "prediction": pred.prediction
        })
    
    return result   