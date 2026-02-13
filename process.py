import os
import sys
from hashlib import sha256
from datetime import datetime

import pandas as pd
from tqdm import tqdm

# Enable tqdm with pandas
tqdm.pandas()

filename: str = "exam_room.csv"
with open(filename, "rb") as f:
    filehash: str = sha256(f.read()).hexdigest()
print(f"HASH: {filehash}")
if os.path.exists(filename + ".hash"):
    with open(filename + ".hash", "r") as f:
        old_hash: str = f.read()
    if filehash == old_hash:
        print("NOT MODIFIED.")
        sys.exit(0)

df = pd.read_csv(filename)
df.drop(columns=["Sl No"], inplace=True)

try:
    df["rollnolist"] = df["rollnolist"].str.strip(",")
except KeyError:
    try:
        df["rollnolist"] = df["roll no"].str.strip(",")
    except KeyError:

        def collect_rolls(row: pd.DataFrame):
            return ",".join(
                value
                for key, value in row.items()
                if isinstance(value, str)
                and (
                    key == "Roll No of alloted Students"
                    or str(key).startswith("Unnamed: ")
                )
            )

        df["rollnolist"] = df.apply(collect_rolls, axis=1)
if "Course No" in df.columns and "coursecode" not in df.columns:
    df["coursecode"] = df["Course No"]
    df = df.drop(columns=["Course No"])
if "Date" in df.columns and "date" not in df.columns:
    df["date"] = df["Date"]
    df = df.drop(columns=["Date"])
if "SESSION" in df.columns and "shift" not in df.columns:
    df["shift"] = df["SESSION"]
    df = df.drop(columns=["SESSION"])
if "Room No" in df.columns and "roomno" not in df.columns:
    df["roomno"] = df["Room No"]
    df = df.drop(columns=["Room No"])
if "No of Students" in df.columns:
    df = df.drop(columns=["No of Students"])
if "Roll No of alloted Students" in df.columns:
    df = df.drop(columns=["Roll No of alloted Students"])

current_year = str(datetime.now().year)
def fix_year(x: str | float) -> str | float:
    if not isinstance(x, str):
        return x
    parts = x.replace("/", "-").split("-")
    if len(parts[-1]) == 3:  # year has 3 digits
        parts[-1] = current_year
    return "-".join(parts)


df["date"] = df["date"].map(fix_year)

if "day" not in df.columns:
    df["day"] = pd.to_datetime(
        df["date"],
        dayfirst=True,  # , format="mixed", errors="coerce"
    ).dt.day_name()
df = df.drop(
    columns=[column for column in df.columns if column.startswith("Unnamed: ")]
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
    codes = item["Course Code"].split("/")
    name = item["Course Name"]
    for code in codes:
        df3 = pd.concat(
            [pd.DataFrame([{"Course Code": code, "Course Name": name}]), df3]
        )

df3 = df3.drop_duplicates()
df3 = df3.set_index("Course Code")


# Faster + tqdm progress with map
def tmp(x):
    try:
        return df3.loc[x]["Course Name"]
    except Exception:
        return ""


df["coursename"] = df["coursecode"].progress_map(tmp)

df.to_csv("clean_data.csv")

with open(filename + ".hash", "w") as f:
    f.write(filehash)
