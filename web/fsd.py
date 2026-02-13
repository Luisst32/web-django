import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-1RILENQ\\SQLEXPRESS;"
    "DATABASE=db_web;"
    "UID=luis;"
    "PWD=luis123;"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Conexión exitosa.")
    conn.close()
except Exception as e:
    print("❌ Error al conectar:", e)
