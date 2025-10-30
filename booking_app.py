import streamlit as st
import pymysql
from datetime import datetime
from fpdf import FPDF


def get_connection():
    return pymysql.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        #database=st.secrets["DB_NAME"],
        port=int(st.secrets.get("DB_PORT")),
        ssl={"ssl": {}},
        autocommit=False
    )

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS booking_app")
        cursor.execute("USE booking_app")
        cursor.execute("""CREATE TABLE IF NOT EXISTS theatres (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            theatre_id INT,
            FOREIGN KEY (theatre_id) REFERENCES theatres(id)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS showtimes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT,
            showtime TIME,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS seats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            showtime_id INT,
            seat_number VARCHAR(10),
            seat_type VARCHAR(10),
            booked BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS bookings (
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
        cursor.execute("""CREATE TABLE IF NOT EXISTS reviews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT,
            user_name VARCHAR(100),
            rating INT,
            comment TEXT,
            review_time DATETIME,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )""")
        conn.commit()

def preload_data():
    if "theatres_data" not in st.session_state:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM theatres")
            st.session_state.theatres_data = cursor.fetchall()

st.set_page_config(page_title="🎬 Movie Booking", layout="centered")
st.title("🎬 ARYAN & DAKSH MOVIE BOOKING APP")
menu = ["Home", "Book Ticket", "Reviews", "Admin Panel"]
choice = st.sidebar.radio("Navigate", menu)
price_map = {"Standard": 150, "Premium": 250, "VIP": 400}

if "db_initialized" not in st.session_state:
    try:
        init_db()
        preload_data()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Database setup failed: {e}")

if choice == "Home":
    st.markdown("""
    ### 👋 Welcome!
    Book tickets for your favorite movies and share your experience with others.
    Use the sidebar to navigate between booking, reviews, and admin options.
    """)

elif choice == "Book Ticket":
    try:
        preload_data()
        theatre_dict = {t[1]: t[0] for t in st.session_state.theatres_data}
        theatre_choice = st.selectbox("🏛 Select Theatre", list(theatre_dict.keys()))
        theatre_id = theatre_dict[theatre_choice]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM movies WHERE theatre_id=%s", (theatre_id,))
            movies = cursor.fetchall()
        if not movies:
            st.info("No movies available for this theatre.")
            st.stop()

        movie_dict = {m[1]: m[0] for m in movies}
        movie_choice = st.selectbox("🎞 Select Movie", list(movie_dict.keys()))
        movie_id = movie_dict[movie_choice]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE movie_id=%s", (movie_id,))
            avg_rating, count = cursor.fetchone()
            avg_rating = round(avg_rating, 1) if avg_rating else None
            st.markdown(f"⭐ **Rating:** {avg_rating if avg_rating else 'No ratings yet'} ({count} reviews)")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, showtime FROM showtimes WHERE movie_id=%s", (movie_id,))
            showtimes = cursor.fetchall()
        if not showtimes:
            st.info("No showtimes available.")
            st.stop()

        showtime_dict = {str(s[1]): s[0] for s in showtimes}
        showtime_choice = st.selectbox("🕒 Select Showtime", list(showtime_dict.keys()))
        showtime_id = showtime_dict[showtime_choice]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seat_number, seat_type, booked FROM seats WHERE showtime_id=%s", (showtime_id,))
            seats_data = cursor.fetchall()

        st.divider()
        st.markdown("### 🎟 Select Your Seats")

        if "selected_seats" not in st.session_state:
            st.session_state.selected_seats = []

        def toggle_seat(seat_num):
            if seat_num in st.session_state.selected_seats:
                st.session_state.selected_seats.remove(seat_num)
            elif len(st.session_state.selected_seats) < 10:
                st.session_state.selected_seats.append(seat_num)

        seat_colors = {
            "Standard": "lightblue",
            "Premium": "lightgreen",
            "VIP": "gold"
        }

        for seat_type in ["Standard", "Premium", "VIP"]:
            st.markdown(f"#### {seat_type} (₹{price_map[seat_type]})")
            seats_of_type = [s for s in seats_data if s[1] == seat_type]
            rows = [seats_of_type[i:i+8] for i in range(0, len(seats_of_type), 8)]

            for row in rows:
                cols = st.columns(8)
                for i, (seat_num, s_type, booked) in enumerate(row):
                    color = seat_colors[s_type]
                    if booked:
                        label = f"❌"
                        bg = "lightgray"
                    elif seat_num in st.session_state.selected_seats:
                        label = "🟡"
                        bg = "khaki"
                    else:
                        label = "✅"
                        bg = color

                    with cols[i]:
                        st.markdown(
                            f"""
                            <button style='background-color:{bg}; border:none; padding:10px; width:100%;
                            border-radius:5px; font-size:14px;' onClick="window.location.reload()">
                            {label}<br>{seat_num}
                            </button>
                            """,
                            unsafe_allow_html=True
                        )
                        if not booked and st.button(f"Select {seat_num}", key=f"btn_{seat_num}"):
                            toggle_seat(seat_num)

        st.markdown(f"**Selected Seats:** {', '.join(st.session_state.selected_seats) if st.session_state.selected_seats else 'None'}")
        total_price = sum([price_map[s[1]] for s in seats_data if s[0] in st.session_state.selected_seats])
        st.markdown(f"**Total Price:** ₹{total_price}")

        st.divider()
        name = st.text_input("👤 Name")
        email = st.text_input("📧 Email")
        phone = st.text_input("📞 Phone")

        if st.button("✅ Confirm Booking"):
            if not st.session_state.selected_seats:
                st.error("Please select at least one seat.")
            elif not (name.strip() and email.strip() and phone.strip()):
                st.error("Please fill in all details.")
            else:
                try:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        booked_success = []
                        for s in st.session_state.selected_seats:
                            cursor.execute(
                                "UPDATE seats SET booked=TRUE WHERE showtime_id=%s AND seat_number=%s AND booked=FALSE",
                                (showtime_id, s),
                            )
                            if cursor.rowcount == 1:
                                booked_success.append(s)
                        if not booked_success:
                            st.error("Some seats already booked.")
                        else:
                            cursor.execute(
                                """INSERT INTO bookings
                                (user_name,email,phone,theatre_id,movie_id,showtime_id,seats_selected,total_price,booking_time)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                (name,email,phone,theatre_id,movie_id,showtime_id,str(booked_success),total_price,datetime.now()),
                            )
                            conn.commit()
                            st.success(f"🎉 Booking confirmed for {movie_choice} ({len(booked_success)} seats)")

                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", "B", 16)
                            pdf.cell(0, 10, "Movie Ticket Receipt", ln=True, align="C")
                            pdf.set_font("Arial", "", 12)
                            for line in [
                                f"Name: {name}",
                                f"Theatre: {theatre_choice}",
                                f"Movie: {movie_choice}",
                                f"Showtime: {showtime_choice}",
                                f"Seats: {', '.join(booked_success)}",
                                f"Total Price: ₹{total_price}",
                            ]:
                                pdf.cell(0, 10, line, ln=True)
                            pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
                            st.download_button("📥 Download Ticket", pdf_bytes, file_name=f"ticket_{name}.pdf")
                            st.session_state.selected_seats = []
                except Exception as e:
                    st.error(f"Booking failed: {e}")

    except Exception as e:
        st.error(f"Database Error: {e}")

elif choice == "Reviews":
    st.subheader("⭐ Movie Reviews")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.name, r.user_name, r.rating, r.comment, r.review_time
            FROM reviews r
            JOIN movies m ON r.movie_id = m.id
            ORDER BY r.review_time DESC
        """)
        reviews = cursor.fetchall()
    if not reviews:
        st.info("No reviews yet.")
    else:
        for movie, user, rating, comment, time in reviews:
            st.markdown(f"### 🎞 {movie}")
            st.markdown(f"⭐ {rating}/5 by **{user}** on {time.strftime('%d %b %Y')}")
            st.write(comment)
            st.divider()

elif choice == "Admin Panel":
    st.subheader("🔧 Admin Panel")
    admin_passwords = ["AryanM", "DakshM"]
    pwd = st.text_input("Enter Admin Password", type="password")
    if pwd in admin_passwords:
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                st.markdown("### ➕ Add Theatre")
                theatre_name = st.text_input("Theatre Name")
                if st.button("Add Theatre"):
                    if theatre_name.strip():
                        cursor.execute("INSERT INTO theatres (name) VALUES (%s)", (theatre_name,))
                        conn.commit()
                        st.success("✅ Theatre Added")

                st.markdown("### ➕ Add Movie")
                cursor.execute("SELECT id,name FROM theatres ORDER BY name")
                theatres = cursor.fetchall()
                if theatres:
                    theatre_dict = {t[1]: t[0] for t in theatres}
                    sel_theatre = st.selectbox("Select Theatre", list(theatre_dict.keys()))
                    movie_name = st.text_input("Movie Name")
                    if st.button("Add Movie"):
                        if movie_name.strip():
                            cursor.execute(
                                "INSERT INTO movies (name,theatre_id) VALUES (%s,%s)",
                                (movie_name, theatre_dict[sel_theatre]),
                            )
                            conn.commit()
                            st.success("✅ Movie Added")

                st.markdown("### ➕ Add Showtime")
                cursor.execute("SELECT id,name FROM movies ORDER BY name")
                movies = cursor.fetchall()
                if movies:
                    movie_dict = {m[1]: m[0] for m in movies}
                    sel_movie = st.selectbox("Select Movie", list(movie_dict.keys()))
                    showtime = st.text_input("Showtime (HH:MM:SS)", "16:00:00")
                    if st.button("Add Showtime"):
                        cursor.execute("INSERT INTO showtimes (movie_id,showtime) VALUES (%s,%s)", (movie_dict[sel_movie], showtime))
                        conn.commit()
                        st.success("✅ Showtime Added")
        except Exception as e:
            st.error(f"DB Error: {e}")
    else:
        st.info("Enter correct admin password.")

