from datetime import datetime  # ใช้ datetime จาก Python เองสำหรับเวลาปัจจุบัน
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime  # นำเข้า Boolean และ DateTime จาก SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

Base = declarative_base()

class News(Base):
    __tablename__ = 'news'  # Ensure this matches your actual table name
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    cover_image = Column(String(500))  # Matches your screenshot
    attachment = Column(String(500))  # Increased length to handle long filenames
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Building(Base):
    __tablename__ = 'building'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50))
    name = Column(String(100))
    area = Column(String, index=True)
    idGroup = Column(Integer, index=True)

class Unit(Base):
    __tablename__ = 'unit'
    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    amount = Column(Integer)
    idBuilding = Column(Integer, ForeignKey('building.id'))

class NumberOfUsers(Base):
    __tablename__ = 'numberOfUsers'
    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    amount = Column(Integer)

class ExamStatus(Base):
    __tablename__ = 'examStatus'
    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    status = Column(Boolean)

class SemesterStatus(Base):
    __tablename__ = 'semesterStatus'
    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    status = Column(Boolean)

class Member(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    fname = Column(String)
    lname = Column(String)
    email = Column(String)
    phone = Column(String)
    status = Column(Integer)

class PredictionTable(Base):
    __tablename__ = "predictiontable"

    id = Column(Integer, primary_key=True, index=True)
    building = Column(String, index=True)
    area = Column(Float)
    prediction = Column(Float)
    unit = Column(Float)
    modelName = Column(String)
    month_current = Column(Integer)
    year_current = Column(Integer)
    month_predict = Column(Integer)
    year_predict = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class GroupBuilding(Base):
    __tablename__ = 'groupbuilding'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    about = Column(Text)

class Holiday(Base):
    __tablename__ = "holiday"
    id = Column(Integer, primary_key=True, index=True)
    years = Column(Integer)
    month = Column(Integer)
    Holiday = Column(Integer)  # or whatever data type is appropriate