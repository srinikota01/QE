import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, Response, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import desc, asc, and_, text, func
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse, RedirectResponse

from database.database import SessionLocal, engine
from sqlalchemy.orm import Session
from database import models
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

origins = [
    "*"
]

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "dbf05aaa94b7a95681ebb1f0fc95de2218be91a76204107b66d24db4cf522529"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
models.Base.metadata.create_all(bind=engine)


# Dependency
def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# Basic output for most of the routes
class OutPut(BaseModel):
    msg: str
    data: list
    result: str

    def toJsonStr(self):
        return {
            'msg': self.msg,
            'data': self.data,
            'result': self.result
        }


commonResponses = {
    400: OutPut(msg='error msg', data=[], result='failed').toJsonStr(),
    200: OutPut(msg='info msg', data=['might have some data'], result='success').toJsonStr(),
    201: OutPut(msg='info msg', data=['might have some data'], result='success').toJsonStr(),
    422: OutPut(msg='error msg', data=[], result='failed').toJsonStr()
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    password: str


def get_user(db, username: str):
    return db.query(models.User).filter(models.User.userName == username).first()


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(getDb)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/api/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDb)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OutPut(msg='Incorrect username or password', data=[], result='failed').toJsonStr(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.userName}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


class Result(BaseModel):
    category: str = Field(
        None, min_length=1, max_length=150
    )
    testcases: int
    passed: int
    failed: int
    skipped: int
    passpercentage: int
    environment: str = Field(
        None, min_length=1, max_length=150
    )
    datetime: datetime
    comments: str = Field(
        None, min_length=1, max_length=200
    )


@app.post("/api/submit_results", response_model=OutPut)
def submit_results(result: Result, db: Session = Depends(getDb), current_user: User = Depends(get_current_active_user)):
    mResult = models.Results(**result.dict())
    db.add(mResult)
    db.commit()
    db.refresh(mResult)
    return OutPut(msg="result entered successfully", data=[], result="success")


@app.get("/api/results/", response_model=OutPut)
def get_results(category: str, from_date: datetime, to_date: datetime, environment: str,
                db: Session = Depends(getDb)):
    mSqlData = db.query(models.Results) \
        .where(and_(models.Results.category == category, models.Results.environment == environment)) \
        .filter(models.Results.datetime.between(from_date, to_date)) \
        .order_by(asc(models.Results.resultId)).all()
    mOutPutData = []
    for mRow in mSqlData:
        mOutPutData.append({
            "resultId": mRow.resultId,
            "category": mRow.category,
            "testcases": mRow.testcases,
            "passed": mRow.passed,
            "failed": mRow.failed,
            "skipped": mRow.skipped,
            "passpercentage": mRow.passpercentage,
            "environment": mRow.environment,
            "datetime": mRow.datetime,
            "comments": mRow.comments
        })
    return OutPut(msg="report data retrieved successfully", data=mOutPutData, result="success")

@app.get("/")
def index_login():
    return FileResponse('templates/index.html')

@app.get("/login.html")
def index_login():
    return FileResponse('templates/index.html')

@app.get("/utils.js")
def get_utlis_js():
    return FileResponse('templates/utils.js')

@app.get("/home.html")
def home():
    return FileResponse('templates/home.html')

@app.get("/results_entry.html")
def results_entry():
    return FileResponse('templates/results_entry.html')

@app.get("/reports.html")
def results_entry():
    return FileResponse('templates/reports.html')