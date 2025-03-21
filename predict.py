from sqlalchemy.orm import Session
from typing import List
import pandas as pd
# import pickle
from models import Building, ExamStatus, NumberOfUsers, SemesterStatus, Unit , Holiday
from schemas import PredictionRequest, PredictionResponse
import logging
from fastapi import HTTPException
import os
from datetime import datetime
from fastapi import Query
import joblib


# --------- ส่วนของการเก็บ log ---------------
# สร้างโฟลเดอร์ 'log' หากยังไม่มี
if not os.path.exists('log'):
    os.makedirs('log')

# สร้างชื่อไฟล์ที่มีวันที่และเวลาปัจจุบัน
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f'log/log-{current_time}.txt'

# กำหนดค่าให้กับ logging
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

# --------- ส่วนของการเก็บ log ---------------

def load_model(model_name: str):
    model_path = f"models/{model_name}.pkl"
    if not os.path.exists(model_path):
        logging.error(f"Model file does not exist: {model_path}")
        raise HTTPException(status_code=404, detail="Model file not found")
    
    model = joblib.load(model_path)

    # Validate the model type before returning
    if not hasattr(model, "predict"):
        logging.error(f"Loaded object is not a valid model: {type(model)}")
        raise HTTPException(status_code=500, detail=f"Invalid model format: {model_name}")

    return model

def predict(request: PredictionRequest, db: Session) -> List[PredictionResponse]:
    model_name = request.modelName
    
    if not model_name:
        logging.error("Model name is missing or empty")
        raise HTTPException(status_code=400, detail="Model name is required")
    
    model_names = [f"model_T+{i}" for i in range(1, 13)] if model_name == "All" else model_name.split(",")
    model = load_model("model_T+1")
    logging.info(f"Model names to be used: {model_names}")
    
    year = request.year
    month = request.month

    units = db.query(Unit.idBuilding).filter_by(years=year, month=month).distinct().all()
    if not units:
        logging.warning(f"No buildings found in Unit table for year: {year}, month: {month}")
        raise HTTPException(status_code=404, detail="No buildings found for the specified year and month")

    building_ids = [unit.idBuilding for unit in units]
    predictions = []

    for building_id in building_ids:
        building = db.query(Building).filter_by(id=building_id).first()
        if not building:
            logging.warning(f"Building not found for id: {building_id}")
            continue

        building_code = building.code
        building_area = building.area

        current_unit = db.query(Unit).filter_by(years=year, month=month, idBuilding=building_id).first()
        unit_amount = current_unit.amount if current_unit else 0

        current_number_of_users = db.query(NumberOfUsers).filter_by(years=year, month=month).first()
        current_exam_status = db.query(ExamStatus).filter_by(years=year, month=month).first()
        current_semester_status = db.query(SemesterStatus).filter_by(years=year, month=month).first()
        
        # ดึงข้อมูลวันหยุด
        current_holiday = db.query(Holiday).filter_by(years=year, month=month).first()
        holiday_count = current_holiday.Holiday if current_holiday else 0

        data = {
            "month": month,
            "building": str(building_id),
            "Area": building_area,
            "Eusers": current_number_of_users.amount if current_number_of_users else 0,
            "exam": current_exam_status.status if current_exam_status else 0,
            "semester": current_semester_status.status if current_semester_status else 0,
            "Holiday": holiday_count,
            "Unit": unit_amount
        }

        # ข้อมูลย้อนหลัง 11 เดือน
        for i in range(1, 12):
            prev_month = (month - i - 1) % 12 + 1
            prev_year = year - (1 if month - i <= 0 else 0)
            
            number_of_users = db.query(NumberOfUsers).filter_by(years=prev_year, month=prev_month).first()
            exam_status = db.query(ExamStatus).filter_by(years=prev_year, month=prev_month).first()
            semester_status = db.query(SemesterStatus).filter_by(years=prev_year, month=prev_month).first()
            unit = db.query(Unit).filter_by(years=prev_year, month=prev_month, idBuilding=building_id).first()
            holiday = db.query(Holiday).filter_by(years=prev_year, month=prev_month).first()

            data[f"Eusers-{i}"] = number_of_users.amount if number_of_users else 0
            data[f"exam-{i}"] = exam_status.status if exam_status else 0
            data[f"semester-{i}"] = semester_status.status if semester_status else 0
            data[f"Holiday-{i}"] = holiday.Holiday if holiday else 0
            data[f"Unit-{i}"] = unit.amount if unit else 0

        # เพิ่ม Holiday ใน columns
        columns = ['month', 'building', 'Area', 'Eusers'] + \
                  [f'Eusers-{i}' for i in range(1, 12)] + \
                  ['exam'] + [f'exam-{i}' for i in range(1, 12)] + \
                  ['semester'] + [f'semester-{i}' for i in range(1, 12)] + \
                  ['Holiday'] + [f'Holiday-{i}' for i in range(1, 12)] + \
                  ['Unit'] + [f'Unit-{i}' for i in range(1, 12)] 
                  
        df = pd.DataFrame([data])
        X = df[columns]

        for i, model_name in enumerate(model_names):
            try:
                model = load_model(model_name)
                
                # ดึงตัวเลขหลัง T+ จากชื่อโมเดล
                forecast_months = int(model_name.split("+")[1])
                
                # คำนวณเดือนและปีที่ถูกต้อง
                month_predict = (month + forecast_months - 1) % 12 + 1
                year_predict = year + (month + forecast_months - 1) // 12
                
                prediction = model.predict(X)[0]

                predictions.append({
                    "building": str(building_id),
                    "area": building_area,
                    "prediction": prediction,
                    "unit": unit_amount,
                    "modelName": model_name,
                    "month_current": month,
                    "year_current": year,
                    "month_predict": month_predict,
                    "year_predict": year_predict
                })
                
                logging.info(f"Model: {model_name}, Building: {building_id}, Prediction: {prediction}")
            except Exception as model_error:
                logging.error(f"Prediction error for building {building_id} with model {model_name}: {str(model_error)}")
                raise HTTPException(status_code=500, detail="Model prediction error")
            
    return predictions