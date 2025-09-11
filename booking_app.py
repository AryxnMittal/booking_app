import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd

# ----------------- Database Connection -----------------
def create_connection():
    return mysql.connector.connect(
        host="localhost",  # your MySQL host
        user="root",       # your MySQL username
        password="root",       # your MySQL password
        database="booking_app"
    )

# ----------------- CRUD FUNCTIONS -----------------

# Create Booking
def add_booking(name, email, phone, date, time, service):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO bookings (name, email, phone, date, time, service) VALUES (%s,%s,%s,%s,%s,%s)",
                       (name, email, phone, date, time, service))
        conn.commit()
        st.success("Booking added successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Read Bookings
def view_bookings():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings")
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Phone', 'Date', 'Time', 'Service'])
        return df
    except Error as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Update Booking
def update_booking(id, name, email, phone, date, time, service):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""UPDATE bookings SET name=%s, email=%s, phone=%s, date=%s, time=%s, service=%s 
                          WHERE id=%s""", (name, email, phone, date, time, service, id))
        conn.commit()
        st.success("Booking updated successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Delete Booking
def delete_booking(id):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE id=%s", (id,))
        conn.commit()
        st.success("Booking deleted successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ----------------- STREAMLIT FRONTEND -----------------
st.title("Booking App")

menu = ["Add Booking", "View Bookings", "Update Booking", "Delete Booking"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------- Add Booking ----------
if choice == "Add Booking":
    st.subheader("Add New Booking")
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    date = st.date_input("Date")
    time = st.time_input("Time")
    service = st.text_input("Service")
    
    if st.button("Add Booking"):
        add_booking(name, email, phone, date, time, service)

# ---------- View Bookings ----------
elif choice == "View Bookings":
    st.subheader("All Bookings")
    df = view_bookings()
    st.dataframe(df)
    st.download_button("Download as CSV", df.to_csv(index=False), file_name="bookings.csv")

# ---------- Update Booking ----------
elif choice == "Update Booking":
    st.subheader("Update Booking")
    df = view_bookings()
    st.dataframe(df)
    id = st.number_input("Enter Booking ID to Update", min_value=1)
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    date = st.date_input("Date")
    time = st.time_input("Time")
    service = st.text_input("Service")
    
    if st.button("Update Booking"):
        update_booking(id, name, email, phone, date, time, service)

# ---------- Delete Booking ----------
elif choice == "Delete Booking":
    st.subheader("Delete Booking")
    df = view_bookings()
    st.dataframe(df)
    id = st.number_input("Enter Booking ID to Delete", min_value=1)
    
    if st.button("Delete Booking"):
        delete_booking(id)
