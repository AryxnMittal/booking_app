import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import plotly.express as px

def create_connection():
    return mysql.connector.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        database=st.secrets["DB_NAME"],
        port=int(st.secrets.get("DB_PORT", 3306)),
        autocommit=False
    )


def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
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
    conn.commit()
    cursor.close()
    conn.close()

def populate_data():
    conn = create_connection()
    cursor = conn.cursor()

    theatres = [
        "PVR Select City Walk, Saket",
        "PVR Vegas Luxe, Dwarka",
        "PVR Pacific, Subhash Nagar",
        "PVR Priya, Vasant Vihar",
        "PVR Naraina",
        "INOX Nehru Place",
        "INOX District Centre, Janakpuri",
        "INOX Vishal Cinema, Raja Garden",
        "Cinepolis V3S Mall, Laxmi Nagar",
        "Cinepolis DLF Avenue, Saket",
        "Miraj Cinemas Vikas Mall, Shahdara",
        "Wave Cinemas Raja Garden"
    ]
    cursor.execute("SELECT COUNT(*) FROM theatres")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO theatres (name) VALUES (%s)", [(t,) for t in theatres])

    movies = [
        "The Conjuring: Last Rites",
        "Baaghi 4",
        "Param Sundari",
        "Mahavatar Narsimha",
        "The Bengal Files",
        "Vash Level 2",
        "The Fantastic Four: First Steps"
    ]

    cursor.execute("SELECT id FROM theatres")
    theatre_ids = [t[0] for t in cursor.fetchall()]
    for tid in theatre_ids:
        for m in movies:
            cursor.execute("SELECT COUNT(*) FROM movies WHERE name=%s AND theatre_id=%s", (m, tid))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO movies (name, theatre_id) VALUES (%s,%s)", (m, tid))

    showtimes = ["10:00:00","13:00:00","16:00:00","19:00:00","22:00:00"]
    cursor.execute("SELECT id FROM movies")
    movie_ids = [m[0] for m in cursor.fetchall()]
    for mid in movie_ids:
        for stime in showtimes:
            cursor.execute("SELECT COUNT(*) FROM showtimes WHERE movie_id=%s AND showtime=%s", (mid, stime))
            if cursor.fetchone()[0]==0:
                cursor.execute("INSERT INTO showtimes (movie_id, showtime) VALUES (%s,%s)", (mid, stime))

    cursor.execute("SELECT id FROM showtimes")
    showtime_ids = [s[0] for s in cursor.fetchall()]
    seat_types = ["Standard"]*20 + ["Premium"]*10 + ["VIP"]*5

    for stid in showtime_ids:
        cursor.execute("SELECT COUNT(*) FROM seats WHERE showtime_id=%s",(stid,))
        if cursor.fetchone()[0]==0:
            for i, stype in enumerate(seat_types, start=1):
                seat_num = f"{stype[0]}{i}"  # e.g., S1, P1, V1
                cursor.execute("INSERT INTO seats (showtime_id, seat_number, seat_type) VALUES (%s,%s,%s)",
                               (stid, seat_num, stype))
    conn.commit()
    cursor.close()
    conn.close()

create_tables()
populate_data()

st.set_page_config(page_title="🎬 Movie Booking", layout="wide")
st.title("🎬 ARYAN AND DAKSH MOVIE BOOKING APP")

menu = ["Home","Book Ticket","Statistics","Admin Panel"]
choice = st.sidebar.selectbox("Menu", menu)

price_map = {"Standard":150,"Premium":250,"VIP":400}

if choice=="Home":
    st.subheader("Welcome to the Booking App!")
    st.write("Book tickets, manage shows, view analytics, and download receipts seamlessly.")

elif choice=="Book Ticket":
    conn=create_connection()
    cursor=conn.cursor()

    cursor.execute("SELECT id,name FROM theatres")
    theatres=cursor.fetchall()
    theatre_dict={t[1]:t[0] for t in theatres}
    theatre_names=list(theatre_dict.keys())

    if not theatre_names:
        st.error("No theatres available. Add from Admin Panel.")
        cursor.close(); conn.close(); st.stop()

    if "ui_selected_theatre" not in st.session_state:
        st.session_state.ui_selected_theatre = theatre_names[0]

    theatre_choice = st.selectbox("Select Theatre", theatre_names,
                                  index=theatre_names.index(st.session_state.ui_selected_theatre))
    st.session_state.ui_selected_theatre = theatre_choice
    theatre_id = theatre_dict[theatre_choice]


    cursor.execute("SELECT id,name FROM movies WHERE theatre_id=%s",(theatre_id,))
    movies=cursor.fetchall()
    movie_dict={m[1]:m[0] for m in movies}
    movie_names=list(movie_dict.keys())

    if not movie_names:
        st.warning("No movies for this theatre yet."); cursor.close(); conn.close(); st.stop()

    if "ui_selected_movie" not in st.session_state or st.session_state.ui_selected_movie not in movie_names:
        st.session_state.ui_selected_movie=movie_names[0]

    movie_choice = st.selectbox("Select Movie", movie_names,
                                index=movie_names.index(st.session_state.ui_selected_movie))
    st.session_state.ui_selected_movie=movie_choice
    movie_id=movie_dict[movie_choice]


    cursor.execute("SELECT id,showtime FROM showtimes WHERE movie_id=%s",(movie_id,))
    showtimes=cursor.fetchall()
    showtime_dict={str(s[1]):s[0] for s in showtimes}
    showtime_names=list(showtime_dict.keys())

    if not showtime_names:
        st.warning("No showtimes yet."); cursor.close(); conn.close(); st.stop()

    if "ui_selected_showtime" not in st.session_state or st.session_state.ui_selected_showtime not in showtime_names:
        st.session_state.ui_selected_showtime=showtime_names[0]

    showtime_choice=st.selectbox("Select Showtime", showtime_names,
                                 index=showtime_names.index(st.session_state.ui_selected_showtime))
    st.session_state.ui_selected_showtime=showtime_choice
    showtime_id=showtime_dict[showtime_choice]


    cursor.execute("SELECT seat_number,seat_type,booked FROM seats WHERE showtime_id=%s ORDER BY seat_type,seat_number",(showtime_id,))
    seats=cursor.fetchall()

    st.markdown("### Select Seats (Min 1, Max 10)")
    if "selected_seats" not in st.session_state:
        st.session_state.selected_seats=[]
    selected_seats=st.session_state.selected_seats

    for stype in ["Standard","Premium","VIP"]:
        st.markdown(f"#### {stype} (Rs.{price_map[stype]})")
        type_seats=[s for s in seats if s[1]==stype]
        cols=st.columns(7)
        for idx,(seat_num,_,booked) in enumerate(type_seats):
            col=cols[idx%7]
            key=f"{stype}_{seat_num}"
            if booked:
                col.button(f"❌{seat_num}",key=key,disabled=True)
            else:
                btn_label=f"🟢{seat_num}" if seat_num in selected_seats else seat_num
                if col.button(btn_label,key=key):
                    if seat_num in selected_seats:
                        selected_seats.remove(seat_num)
                    else:
                        if len(selected_seats)<10: selected_seats.append(seat_num)
                        else: st.warning("⚠️ Max 10 seats allowed!")

    total_price=sum([price_map[s[1]] for s in seats if s[0] in selected_seats])
    st.markdown(f"**Selected Seats:** {', '.join(selected_seats) if selected_seats else 'None'}")
    st.markdown(f"**Total Price:** Rs.{total_price}")

    name=st.text_input("Name")
    email=st.text_input("Email")
    phone=st.text_input("Phone")

    if st.button("Confirm Booking"):
        if len(selected_seats)<1:
            st.error("Select at least 1 seat!")
        elif not name.strip() or not email.strip() or not phone.strip():
            st.error("Fill all fields!")
        else:
            try:
                seats_success=[]
                for s in selected_seats:
                    cursor.execute("UPDATE seats SET booked=TRUE WHERE showtime_id=%s AND seat_number=%s AND booked=FALSE",(showtime_id,s))
                    if cursor.rowcount==1:
                        seats_success.append(s)
                    else:
                        raise RuntimeError(f"Seat {s} already booked")

                cursor.execute(
                    """INSERT INTO bookings
                    (user_name,email,phone,theatre_id,movie_id,showtime_id,seats_selected,total_price,booking_time)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (name,email,phone,theatre_id,movie_id,showtime_id,str(seats_success),total_price,datetime.now())
                )
                conn.commit()

                st.success(f"🎉 Booking Confirmed! Total Price: Rs.{total_price}")


                pdf=FPDF()
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
                for s in seats_success:
                    pdf.cell(0,8,f" - {s}",ln=True)
                pdf.cell(0,10,f"Total Price: Rs.{total_price}",ln=True)

                pdf_bytes=pdf.output(dest='S').encode('latin-1', 'replace')
                st.download_button("📥 Download Receipt",data=pdf_bytes,file_name=f"receipt_{name.replace(' ','')}.pdf",mime="application/pdf")

                st.session_state.selected_seats=[]

            except Exception as e:
                conn.rollback()
                st.error(f"Booking failed: {e}")

    cursor.close()
    conn.close()

elif choice=="Statistics":
    st.subheader("📊 Booking Statistics")
    conn=create_connection()
    cursor=conn.cursor()

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM bookings")
    row=cursor.fetchone()
    total_bookings=row[0] if row and row[0] else 0
    total_spent=row[1] if row and row[1] else 0

    m1,m2=st.columns(2)
    m1.metric("🎟️ Total Bookings",total_bookings)
    m2.metric("💰 Total Spent (Rs.)",int(total_spent))

    df=pd.read_sql("SELECT user_name,theatre_id,movie_id,showtime_id,seats_selected,total_price,booking_time FROM bookings ORDER BY booking_time DESC LIMIT 10",conn)
    st.dataframe(df,use_container_width=True)

    df_chart=pd.read_sql("""
        SELECT DATE(booking_time) as date, COUNT(*) as bookings_count
        FROM bookings
        GROUP BY DATE(booking_time)
        ORDER BY date DESC
        LIMIT 10
    """,conn)

    if not df_chart.empty:
        fig=px.bar(df_chart,x="date",y="bookings_count",title="📊 Bookings Trend (Last 10 Days)")
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("No bookings yet to plot.")

    cursor.close()
    conn.close()

elif choice=="Admin Panel":
    st.subheader("🔧 Admin Panel (Password Protected)")
    admin_password1="AryanM"
    admin_password2="DakshM"
    pwd=st.text_input("Enter Admin Password",type="password")
    if pwd==admin_password1 or pwd==admin_password2:
        conn=create_connection()
        cursor=conn.cursor()

        st.markdown("### ➕ Add Theatre")
        theatre_name=st.text_input("Theatre Name", key="admin_add_theatre")
        if st.button("Add Theatre"):
            if theatre_name.strip():
                cursor.execute("INSERT INTO theatres (name) VALUES (%s)",(theatre_name.strip(),))
                conn.commit()
                st.success("✅ Theatre Added")

        st.markdown("### ➖ Delete Theatre")
        cursor.execute("SELECT id,name FROM theatres ORDER BY name")
        theatres=cursor.fetchall()
        theatre_dict={t[1]:t[0] for t in theatres}
        theatre_names=list(theatre_dict.keys())
        if theatre_names:
            del_theatre=st.selectbox("Select Theatre to Delete",theatre_names,key="del_theatre")
            if st.button("Delete Theatre"):
                cursor.execute("DELETE FROM theatres WHERE id=%s",(theatre_dict[del_theatre],))
                conn.commit()
                st.success("✅ Theatre Deleted")

        st.markdown("### ➕ Add Movie")
        if theatre_names:
            sel_theatre=st.selectbox("Select Theatre for Movie",theatre_names,key="admin_sel_theatre")
            movie_name=st.text_input("Movie Name",key="admin_add_movie")
            if st.button("Add Movie"):
                if movie_name.strip():
                    cursor.execute("INSERT INTO movies (name,theatre_id) VALUES (%s,%s)",(movie_name.strip(),theatre_dict[sel_theatre]))
                    conn.commit()
                    st.success("✅ Movie Added")

        st.markdown("### ➖ Delete Movie")
        cursor.execute("SELECT id,name FROM movies ORDER BY name")
        movies=cursor.fetchall()
        movie_dict={m[1]:m[0] for m in movies}
        movie_names=list(movie_dict.keys())
        if movie_names:
            del_movie=st.selectbox("Select Movie to Delete",movie_names,key="del_movie")
            if st.button("Delete Movie"):
                cursor.execute("DELETE FROM movies WHERE id=%s",(movie_dict[del_movie],))
                conn.commit()
                st.success("✅ Movie Deleted")

        st.markdown("### ➕ Add Showtime")
        if movie_names:
            sel_movie=st.selectbox("Select Movie for Showtime",movie_names,key="admin_sel_showtime_movie")
            showtime=st.text_input("Showtime (HH:MM:SS)", "16:00:00", key="admin_add_showtime")
            if st.button("Add Showtime"):
                if showtime.strip():
                    cursor.execute("INSERT INTO showtimes (movie_id,showtime) VALUES (%s,%s)",(movie_dict[sel_movie],showtime.strip()))
                    conn.commit()
                    st.success("✅ Showtime Added")

        st.markdown("### ➖ Delete Showtime")
        cursor.execute("SELECT id,movie_id,showtime FROM showtimes ORDER BY showtime")
        showtimes=cursor.fetchall()
        showtime_dict={f"{s[2]} ({[m[1] for m in movies if m[0]==s[1]][0]})":s[0] for s in showtimes}
        showtime_names=list(showtime_dict.keys())
        if showtime_names:
            del_showtime=st.selectbox("Select Showtime to Delete",showtime_names,key="del_showtime")
            if st.button("Delete Showtime"):
                cursor.execute("DELETE FROM showtimes WHERE id=%s",(showtime_dict[del_showtime],))
                conn.commit()
                st.success("✅ Showtime Deleted")

        cursor.close()
        conn.close()

    else:
        st.info("Enter correct admin password to access panel.")

