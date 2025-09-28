import mysql.connector

try:
    conn = mysql.connector.connect(
        host="sql12.freesqldatabase.com",
        port=3306,
        user="sql12800450",
        password="wqhsWEXUN2",
        database="sql12800450"
    )
    print("✅ DB Connected")
except Exception as e:
    print(f"❌ DB Connection Failed: {e}")

