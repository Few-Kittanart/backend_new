from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BuildingCreate(BaseModel):
    id : int
    code: str
    name: str
    area: str
    idGroup: Optional[int] = None
    
    class Config:
        orm_mode = True

class UnitCreate(BaseModel):
    years: int
    month: int
    amount: int
    idBuilding: int

class HolidayCreate(BaseModel):
    years: int
    month: int
    Holiday : int

class NumberOfUsersCreate(BaseModel):
    years: int
    month: int
    amount: int

class ExamStatusCreate(BaseModel):
    years: int
    month: int
    status: bool

class SemesterStatusCreate(BaseModel):
    years: int
    month: int
    status: bool

class MemberCreate(BaseModel):
    username: str
    password: str
    fname: str
    lname: str
    email: str
    phone: str
    status: int

class PredictionRequest(BaseModel):
    year: int
    month: int
    modelName: str

class PredictionResponse(BaseModel):
    building: str
    area: float
    prediction: float
    unit: float
    modelName: str
    month_current: int
    year_current: int
    month_predict: int
    year_predict: int
    
class LoginData(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    username: str
    status: int
    name: str

class NewsBase(BaseModel):
    id: Optional[int] = None
    title: str
    content: Optional[str] = None
    cover_image: Optional[str] = None
    attachment: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class ExamStatusBase(BaseModel):
    years: int
    month: int
    status: bool

class HolidayBase(BaseModel):
    years: int
    month: int
    Holiday: int

class ExamStatusCreate(ExamStatusBase):
    pass

class ExamStatusResponse(ExamStatusBase):
    id: int

    class Config:
        orm_mode = True  # สำหรับ pydantic V1
        # ใน pydantic V2 ใช้: from_attributes = True
