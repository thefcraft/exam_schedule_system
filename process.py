import os
import sys
import argparse
from hashlib import sha256
from datetime import datetime

import pandas as pd
from tqdm import tqdm

# Enable tqdm with pandas
tqdm.pandas()

# Argument parser
parser = argparse.ArgumentParser(description="Process exam room CSV.")
parser.add_argument(
    "--force", action="store_true", help="Force run even if file not modified"
)
args = parser.parse_args()

filename: str = "exam_room.csv"
with open(filename, "rb") as f:
    filehash: str = sha256(f.read()).hexdigest()
print(f"HASH: {filehash}")
if not args.force and os.path.exists(filename + ".hash"):
    with open(filename + ".hash", "r") as f:
        old_hash: str = f.read()
    if filehash == old_hash:
        print("NOT MODIFIED.")
        sys.exit(0)

df = pd.read_csv(filename)
try:
    df.drop(columns=["Sl No"], inplace=True)
except KeyError:
    try:
        df.drop(columns=["Sl.No"], inplace=True)
    except:
        pass

try:
    df["rollnolist"] = df["rollnolist"].str.strip(",")
except KeyError:
    try:
        df["rollnolist"] = df["roll no"].str.strip(",")
    except KeyError:
        try:
            roll_cols = set(
                df.columns[list(df.columns).index("Roll No of alloted Students") :]
            )
        except ValueError:
            roll_cols = set(df.columns[list(df.columns).index("Rolls") :])

        def collect_rolls(row: pd.DataFrame):
            return ",".join(
                value
                for key, value in row.items()
                if isinstance(value, str) and key in roll_cols and value.strip()
            )

        df["rollnolist"] = df.apply(collect_rolls, axis=1)
if "Course No" in df.columns and "coursecode" not in df.columns:
    df["coursecode"] = df["Course No"]
    df = df.drop(columns=["Course No"])
elif "Courses" in df.columns and "coursecode" not in df.columns:
    df["coursecode"] = df["Courses"]
    df = df.drop(columns=["Courses"])
if "Slot" in df.columns and "shift" not in df.columns:
    df["shift"] = df["Slot"]
    df = df.drop(columns=["Slot"])
if "Date" in df.columns and "date" not in df.columns:
    df["date"] = df["Date"]
    df = df.drop(columns=["Date"])
if "SESSION" in df.columns and "shift" not in df.columns:
    df["shift"] = df["SESSION"]
    df = df.drop(columns=["SESSION"])
if "Room No" in df.columns and "roomno" not in df.columns:
    df["roomno"] = df["Room No"]
    df = df.drop(columns=["Room No"])
elif "Room" in df.columns and "roomno" not in df.columns:
    df["roomno"] = df["Room"]
    df = df.drop(columns=["Room"])
if "No of Students" in df.columns:
    df = df.drop(columns=["No of Students"])
if "Roll No of alloted Students" in df.columns:
    df = df.drop(columns=["Roll No of alloted Students"])

current_year = str(datetime.now().year)


def fix_year(x: str | float) -> str | float:
    if not isinstance(x, str):
        return x
    parts = x.replace("/", "-").split("-")
    if len(parts) != 3:
        return "1-1-2011"
    day, month, year = parts
    if len(year) == 3:  # year has 3 digits
        year = current_year
    if day == current_year:
        day, year = year, day
    return f"{day}-{month}-{year}"


df["date"] = df["date"].map(fix_year)

if "day" not in df.columns:
    df["day"] = pd.to_datetime(
        df["date"],
        dayfirst=True,  # , format="mixed", errors="coerce"
    ).dt.day_name()
df = df.drop(
    columns=[column for column in df.columns if column.startswith("Unnamed: ")]
)
df = df.drop(
    columns=[
        column
        for column in df.columns
        if column not in ["rollnolist", "coursecode", "date", "shift", "roomno", "day"]
    ]
)

df["rollno"] = df["rollnolist"].str.split(",")
df = df.explode("rollno")
df = df.drop(["rollnolist"], axis=1)

df.to_csv("exam.csv", index=False)
df = pd.read_csv("exam.csv")

# Build course code/name map
df_map = pd.read_csv("code_name_map.csv")
df3 = pd.DataFrame(columns=["Course Code", "Course Name"])

for i in tqdm(range(len(df_map)), desc="Building course map"):
    item = df_map.iloc[i]
    codes = item["Course Code"].replace(" OR ", "/").split("/")
    name = item["Course Name"]
    for code in codes:
        df3 = pd.concat(
            [pd.DataFrame([{"Course Code": code, "Course Name": name}]), df3]
        )

df3 = df3.drop_duplicates()
df3 = df3.set_index("Course Code")


# Faster + tqdm progress with map
def map_course_name(data: str):
    courses = [
        result
        for course in data.split(",")
        if (course_str := course.strip().split(" ")[0])
        for result in course_str.split("/")
    ]
    for course in courses:
        try:
            return df3.loc[course]["Course Name"]
        except KeyError:
            pass
    return ""


df["coursename"] = df["coursecode"].progress_map(map_course_name)
assert(
    set(df.columns)
    == {"coursecode", "date", "shift", "roomno", "day", "rollno", "coursename"}
)
df.to_csv("clean_data.csv")

with open(filename + ".hash", "w") as f:
    f.write(filehash)
