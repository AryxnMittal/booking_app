#physics wallah site phsyicswallahalakhpandey.com   https://web.archive.org/web/20210411035426/http://physicswallahalakhpandey.com/
import streamlit as st
import pymysql
from datetime import datetime
from fpdf import FPDF
import pandas as pd
import plotly.express as px

# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return pymysql.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        database=st.secrets["DB_NAME"],
        port=int(st.secrets.get("DB_PORT", 3306)),
        autocommit=False
    )

# ---------------- INITIALIZE DB ----------------
def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theatres (
                id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100)
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), theatre_id INT,
                FOREIGN KEY (theatre_id) REFERENCES theatres(id)
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS showtimes (
                id INT AUTO_INCREMENT PRIMARY KEY, movie_id INT, showtime TIME,
                FOREIGN KEY (movie_id) REFERENCES movies(id)
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seats (
                id INT AUTO_INCREMENT PRIMARY KEY, showtime_id INT, seat_number VARCHAR(10),
                seat_type VARCHAR(10), booked BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (showtime_id) REFERENCES showtimes(id)
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_name VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(15),
                theatre_id INT,
                movie_id INT,
                showtime_id INT,
                seats_selected TEXT,
                total_price FLOAT,
                booking_time DATETIME
            )""")
        conn.commit()

# ---------------- PRELOAD DATA INTO SESSION_STATE ----------------
def preload_data():
    if "theatres_data" not in st.session_state:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id,name FROM theatres")
            st.session_state.theatres_data = cursor.fetchall()

# ---------------- INITIALIZATION ----------------
if "db_initialized" not in st.session_state:
    try:
        init_db()
        preload_data()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"DB Initialization Failed: {e}")

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="🎬 Movie Booking", layout="wide")
st.title("🎬 ARYAN & DAKSH MOVIE BOOKING APP")
menu = ["Home","Book Ticket","Statistics","Admin Panel"]
choice = st.sidebar.selectbox("Menu", menu)
price_map = {"Standard":150,"Premium":250,"VIP":400}

# ---------------- HOME ----------------
if choice=="Home":
    st.subheader("Welcome to the Booking App!")
    st.write("Book tickets, manage shows, view analytics, and download receipts seamlessly.")

# ---------------- BOOK TICKET ----------------
elif choice=="Book Ticket":
    try:
        preload_data()
        theatre_dict = {t[1]: t[0] for t in st.session_state.theatres_data}
        theatre_choice = st.selectbox("Select Theatre", list(theatre_dict.keys()))
        theatre_id = theatre_dict[theatre_choice]

        # Load movies for selected theatre
        if "movies_data" not in st.session_state or st.session_state.get("theatre_id") != theatre_id:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id,name FROM movies WHERE theatre_id=%s", (theatre_id,))
                st.session_state.movies_data = cursor.fetchall()
                st.session_state.theatre_id = theatre_id

        movie_dict = {m[1]: m[0] for m in st.session_state.movies_data}
        movie_choice = st.selectbox("Select Movie", list(movie_dict.keys()))
        movie_id = movie_dict[movie_choice]

        # Load showtimes for selected movie
        if "showtimes_data" not in st.session_state or st.session_state.get("movie_id") != movie_id:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id,showtime FROM showtimes WHERE movie_id=%s", (movie_id,))
                st.session_state.showtimes_data = cursor.fetchall()
                st.session_state.movie_id = movie_id

        showtime_dict = {str(s[1]): s[0] for s in st.session_state.showtimes_data}
        showtime_choice = st.selectbox("Select Showtime", list(showtime_dict.keys()))
        showtime_id = showtime_dict[showtime_choice]

        # Load seats once
        if "seats_data" not in st.session_state or st.session_state.get("showtime_id") != showtime_id:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT seat_number,seat_type,booked FROM seats WHERE showtime_id=%s ORDER BY seat_type,seat_number",
                    (showtime_id,)
                )
                st.session_state.seats_data = cursor.fetchall()
                st.session_state.selected_seats = []
                st.session_state.showtime_id = showtime_id

        # ---------------- SEAT SELECTION UI ----------------
        st.markdown("### Select Seats (Max 10)")
        for stype in ["Standard","Premium","VIP"]:
            st.markdown(f"#### {stype} (Rs.{price_map[stype]})")
            type_seats = [s for s in st.session_state.seats_data if s[1]==stype]
            cols_per_row = 7
            for i in range(0, len(type_seats), cols_per_row):
                cols = st.columns(cols_per_row)
                for idx, (seat_num, _, booked) in enumerate(type_seats[i:i+cols_per_row]):
                    col = cols[idx]
                    key = f"{stype}_{seat_num}"
                    if booked:
                        col.button(f"❌{seat_num}", key=key, disabled=True)
                    else:
                        selected = seat_num in st.session_state.selected_seats
                        label = f"🟢{seat_num}" if selected else seat_num
                        if col.button(label, key=key):
                            if selected:
                                st.session_state.selected_seats.remove(seat_num)
                            elif len(st.session_state.selected_seats) < 10:
                                st.session_state.selected_seats.append(seat_num)
                            else:
                                st.warning("⚠️ Max 10 seats allowed!")

            st.markdown(f"**Selected Seats:** {', '.join(st.session_state.selected_seats) if st.session_state.selected_seats else 'None'}")
            total_price = sum([price_map[s[1]] for s in st.session_state.seats_data if s[0] in st.session_state.selected_seats])
            st.markdown(f"**Total Price:** Rs.{total_price}")

        # ---------------- USER INFO & BOOKING ----------------
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")

        if st.button("Confirm Booking"):
            if not st.session_state.selected_seats:
                st.error("Select at least 1 seat!")
            elif not (name.strip() and email.strip() and phone.strip()):
                st.error("Fill all fields!")
            else:
                try:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        booked_success = []
                        for s in st.session_state.selected_seats:
                            cursor.execute(
                                "UPDATE seats SET booked=TRUE WHERE showtime_id=%s AND seat_number=%s AND booked=FALSE",
                                (showtime_id,s)
                            )
                            if cursor.rowcount == 1:
                                booked_success.append(s)
                        if not booked_success:
                            st.error("Selected seats already booked.")
                        else:
                            cursor.execute(
                                """INSERT INTO bookings
                                (user_name,email,phone,theatre_id,movie_id,showtime_id,seats_selected,total_price,booking_time)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                (name,email,phone,theatre_id,movie_id,showtime_id,str(booked_success),total_price,datetime.now())
                            )
                            conn.commit()
                            st.success(f"🎉 Booking Confirmed! Seats: {', '.join(booked_success)}")

                            # PDF receipt
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial","B",16)
                            pdf.cell(0,10,"Movie Ticket Receipt",ln=True,align="C")
                            pdf.ln(10)
                            pdf.set_font("Arial","",12)
                            pdf.cell(0,10,f"Name: {name}",ln=True)
                            pdf.cell(0,10,f"Email: {email}",ln=True)
                            pdf.cell(0,10,f"Phone: {phone}",ln=True)
                            pdf.cell(0,10,f"Theatre: {theatre_choice}",ln=True)
                            pdf.cell(0,10,f"Movie: {movie_choice}",ln=True)
                            pdf.cell(0,10,f"Showtime: {showtime_choice}",ln=True)
                            pdf.cell(0,10,"Seats:",ln=True)
                            for s in booked_success:
                                pdf.cell(0,8,f" - {s}",ln=True)
                            pdf.cell(0,10,f"Total Price: Rs.{total_price}",ln=True)
                            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
                            st.download_button(
                                "📥 Download Receipt",
                                data=pdf_bytes,
                                file_name=f"receipt_{name.replace(' ','')}.pdf",
                                mime="application/pdf"
                            )
                            st.session_state.selected_seats = []
                except Exception as e:
                    st.error(f"Booking Failed: {e}")

    except Exception as e:
        st.error(f"DB Connection Error: {e}")

# ---------------- STATISTICS ----------------
elif choice=="Statistics":
    st.subheader("📊 Booking Statistics")
    try:
        with get_connection() as conn:
            df_total = pd.read_sql("SELECT COUNT(*) as total, COALESCE(SUM(total_price),0) as total_spent FROM bookings",conn)
            total_bookings = df_total['total'][0]
            total_spent = df_total['total_spent'][0]
            col1, col2 = st.columns(2)
            col1.metric("🎟️ Total Bookings", total_bookings)
            col2.metric("💰 Total Spent (Rs.)", int(total_spent))

            df_recent = pd.read_sql("SELECT user_name,theatre_id,movie_id,showtime_id,seats_selected,total_price,booking_time FROM bookings ORDER BY booking_time DESC LIMIT 10",conn)
            st.dataframe(df_recent, use_container_width=True)

            df_chart = pd.read_sql("""
                SELECT DATE(booking_time) as date, COUNT(*) as bookings_count
                FROM bookings
                GROUP BY DATE(booking_time)
                ORDER BY date DESC
                LIMIT 10
            """, conn)
            if not df_chart.empty:
                fig = px.bar(df_chart, x="date", y="bookings_count", title="📊 Bookings Trend (Last 10 Days)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No bookings yet to plot.")
    except Exception as e:
        st.error(f"DB Error: {e}")

# ---------------- ADMIN PANEL ----------------
elif choice=="Admin Panel":
    st.subheader("🔧 Admin Panel (Password Protected)")
    admin_passwords = ["AryanM","DakshM"]
    pwd = st.text_input("Enter Admin Password", type="password")
    if pwd in admin_passwords:
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                st.markdown("### ➕ Add Theatre")
                theatre_name = st.text_input("Theatre Name", key="admin_add_theatre")
                if st.button("Add Theatre"):
                    if theatre_name.strip():
                        cursor.execute("INSERT INTO theatres (name) VALUES (%s)",(theatre_name.strip(),))
                        conn.commit()
                        st.success("✅ Theatre Added")
                        st.session_state.pop("theatres_data", None)

                st.markdown("### ➖ Delete Theatre")
                cursor.execute("SELECT id,name FROM theatres ORDER BY name")
                theatres = cursor.fetchall()
                theatre_dict = {t[1]:t[0] for t in theatres}
                if theatre_dict:
                    del_theatre = st.selectbox("Select Theatre to Delete", list(theatre_dict.keys()), key="del_theatre")
                    if st.button("Delete Theatre"):
                        cursor.execute("DELETE FROM theatres WHERE id=%s",(theatre_dict[del_theatre],))
                        conn.commit()
                        st.success("✅ Theatre Deleted")
                        st.session_state.pop("theatres_data", None)

                st.markdown("### ➕ Add Movie")
                if theatre_dict:
                    sel_theatre = st.selectbox("Select Theatre for Movie", list(theatre_dict.keys()), key="admin_sel_theatre")
                    movie_name = st.text_input("Movie Name", key="admin_add_movie")
                    if st.button("Add Movie"):
                        if movie_name.strip():
                            cursor.execute("INSERT INTO movies (name,theatre_id) VALUES (%s,%s)",(movie_name.strip(),theatre_dict[sel_theatre]))
                            conn.commit()
                            st.success("✅ Movie Added")
                            st.session_state.pop("movies_data", None)

                st.markdown("### ➖ Delete Movie")
                cursor.execute("SELECT id,name FROM movies ORDER BY name")
                movies = cursor.fetchall()
                movie_dict = {m[1]:m[0] for m in movies}
                if movie_dict:
                    del_movie = st.selectbox("Select Movie to Delete", list(movie_dict.keys()), key="del_movie")
                    if st.button("Delete Movie"):
                        cursor.execute("DELETE FROM movies WHERE id=%s",(movie_dict[del_movie],))
                        conn.commit()
                        st.success("✅ Movie Deleted")
                        st.session_state.pop("movies_data", None)

                st.markdown("### ➕ Add Showtime")
                if movie_dict:
                    sel_movie = st.selectbox("Select Movie for Showtime", list(movie_dict.keys()), key="admin_sel_showtime_movie")
                    showtime = st.text_input("Showtime (HH:MM:SS)", "16:00:00", key="admin_add_showtime")
                    if st.button("Add Showtime"):
                        if showtime.strip():
                            cursor.execute("INSERT INTO showtimes (movie_id,showtime) VALUES (%s,%s)",(movie_dict[sel_movie],showtime.strip()))
                            conn.commit()
                            st.success("✅ Showtime Added")
                            st.session_state.pop("showtimes_data", None)

                st.markdown("### ➖ Delete Showtime")
                cursor.execute("SELECT id,movie_id,showtime FROM showtimes ORDER BY showtime")
                showtimes = cursor.fetchall()
                showtime_dict = {f"{s[2]} ({[m[1] for m in movies if m[0]==s[1]][0]})":s[0] for s in showtimes}
                if showtime_dict:
                    del_showtime = st.selectbox("Select Showtime to Delete", list(showtime_dict.keys()), key="del_showtime")
                    if st.button("Delete Showtime"):
                        cursor.execute("DELETE FROM showtimes WHERE id=%s",(showtime_dict[del_showtime],))
                        conn.commit()
                        st.success("✅ Showtime Deleted")
                        st.session_state.pop("showtimes_data", None)

        except Exception as e:
            st.error(f"DB Error: {e}")
    else:
        st.info("Enter correct admin password to access panel.")

