import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

df = pd.read_excel('Croma_LED_TVs_Complete.xlsx')
df.columns = df.columns.str.lower()
NEON_URL = os.getenv("NEON_URL")
engine = create_engine(NEON_URL)
df.to_sql('led_tv', engine, if_exists='append', index=False)

print("All data is now live on Neon.")