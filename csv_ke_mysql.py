import pandas as pd
from sqlalchemy import create_engine

# Ganti path-nya sesuai lokasi file CSV kamu
csv_path = "DataClean7_greedy.csv"

# Koneksi database MySQL
user = "root"
password = ""  
host = "localhost"
database = "newest_db"  

# Buat engine SQLAlchemy
engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

# Baca data
df = pd.read_csv(csv_path)

# Impor si csvnya ke tabel 
df.to_sql(name="hasil_greedy", con=engine, if_exists="replace", index=False)

print("✅ Data berhasil diimpor ke MySQL")
