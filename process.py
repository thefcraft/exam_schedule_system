import pandas as pd
from tqdm import tqdm

# Enable tqdm with pandas
tqdm.pandas()

df = pd.read_csv("exam_room.csv")
df.drop(columns=["Sl No"], axis=1, inplace=True)

try:
    df['rollnolist'] = df['rollnolist'].str.strip(',')
except KeyError:
    df['rollnolist'] = df['roll no'].str.strip(',')

df['rollno'] = df['rollnolist'].str.split(',')
df = df.explode('rollno')
df = df.drop(['rollnolist'], axis=1)

df.to_csv("exam.csv", index=False)
df = pd.read_csv('exam.csv')

# Build course code/name map
df_map = pd.read_csv('code_name_map.csv')
df3 = pd.DataFrame(columns=['Course Code', 'Course Name'])

for i in tqdm(range(len(df_map)), desc="Building course map"):
    item = df_map.iloc[i]
    codes = item['Course Code'].split('/')
    name = item['Course Name']
    for code in codes:
        df3 = pd.concat([pd.DataFrame([{
            'Course Code': code,
            'Course Name': name
        }]), df3])

df3 = df3.drop_duplicates()
df3 = df3.set_index('Course Code')

# Faster + tqdm progress with map
def tmp(x):
    try:
        return df3.loc[x]['Course Name']
    except Exception:
        return ''

df['coursename'] = df['coursecode'].progress_map(tmp) 

df.to_csv('clean_data.csv')