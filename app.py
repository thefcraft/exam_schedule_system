import pandas as pd
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import List, Callable, TypeVar, ParamSpec, Any
from functools import wraps
import os

# Define generic type variables
P = ParamSpec("P")  # Represents parameters of the function
R = TypeVar("R")    # Represents return type of the function

def handle_exceptions(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to handle unexpected exceptions in FastAPI route functions.
    Returns a 500 HTTP error for unhandled exceptions.
    """
    @wraps(func)  # Preserves metadata of the original function
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            # Call the original function
            return func(*args, **kwargs)
        except HTTPException:
            # Let FastAPI's HTTP exceptions pass through
            raise
        except Exception as e:
            # Catch all other exceptions and return HTTP 500 response
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal Server Error: {e}"
            )
    return wrapper  # Return the wrapped function

excel_file_url = "https://cciitpatna-my.sharepoint.com/:x:/g/personal/pic_cetc_iitp_ac_in/Ead7bbOsScZJnX1Bb17LuvEBJcCwJGgAgoItalETUVONbw?e=5l8S2D"

basedir = os.path.dirname(__file__)
csv_path = os.path.join(basedir, "clean_data.csv")
template_path = os.path.join(basedir, "templates")

class StudentResponse(BaseModel):
    date: str # "2025-02-27",
    day: str # "Thursday"
    shift: str # "Evening"
    coursecode: str # "MA2204"
    roomno: str # "408"
    rollno: str # "2302MC05"
    coursename: str # Engineering Mechanics

class FacultyResponse(BaseModel):
    date: str # "2025-02-22",
    shift: str # "Evening",
    coursecode: str # "CS2207",
    day: str # "Saturday",
    roomno: List[str] # ["LT102", "LT103"]
    coursename: str # Engineering Mechanics

templates = Jinja2Templates(directory=template_path)

def get_dataframe(request: Request) -> pd.DataFrame:
    if not hasattr(request.app.state, "df"):
        try:
            df = pd.read_csv(csv_path)
            if 'roomno' in df.columns:
                df['roomno'] = df['roomno'].fillna('')
            if 'coursename' in df.columns:
                df['coursename'] = df['coursename'].fillna('')
            request.app.state.df = df
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load data: {e}")
    return request.app.state.df

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     app.state.df = pd.read_csv(csv_path)
#     yield

app = FastAPI() # lifespan=lifespan

def find_by_rollno(df: pd.DataFrame, rollno: str) -> pd.DataFrame:
    result = df[df['rollno'] == rollno.upper()].copy()
    return result.sort_values(by='date')

def find_by_coursecode(df: pd.DataFrame, course_code: str) -> pd.DataFrame:
    filtered = df[df['coursecode'].str.upper() == course_code.upper()]
    grouped = filtered.groupby(['date', 'shift']).agg({
        'coursecode': 'first',
        'day': 'first',
        'coursename': 'first',
        'roomno': lambda x: list(set(x))
    }).reset_index()
    return grouped


@app.get("/student/{rollno}", response_model=List[StudentResponse])
@handle_exceptions
def get_student_by_rollno(
    rollno: str,
    df: pd.DataFrame = Depends(get_dataframe)
):
    rollno = rollno.replace(" ","").strip()
    result = find_by_rollno(df, rollno)
    if result.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return result.to_dict(orient="records")
 
@app.get("/faculty/{course_code}", response_model=FacultyResponse)
@handle_exceptions
def get_faculty_by_coursecode(
    course_code: str,
    df: pd.DataFrame = Depends(get_dataframe)
):
    course_code = course_code.replace(" ","").strip()
    result = find_by_coursecode(df, course_code)
    if result.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if len(result) != 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exam should be scheduled on the same day and shift, result: {result.to_dict(orient='records')}"
        )
    return result.to_dict(orient="records")[0]

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "excel_file_url": excel_file_url,
    })

if __name__ == "__main__":
    import uvicorn
    app.mount('/static', StaticFiles(directory=os.path.join(basedir, 'static')), name="static")
    uvicorn.run(app, host='0.0.0.0', port=8000)
