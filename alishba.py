import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Page config
st.set_page_config(page_title="School Management System", page_icon="🏫", layout="wide")

# Beautiful Custom CSS
st.markdown("""
<style>
    .main {background-color: #f0f8ff;}
    h1, h2, h3 {color: #008080; text-align: center;}
    .stButton>button {border-radius: 10px; font-weight: bold;}
    .add-btn button {background-color: #4CAF50 !important; color: white;}
    .edit-btn button {background-color: #FF9800 !important; color: white;}
    .delete-btn button {background-color: #f44336 !important; color: white;}
    .stSuccess {background-color: #d4edda; border-color: #c3e6cb;}
    .stDataFrame {border: 1px solid #008080;}
</style>
""", unsafe_allow_html=True)

# Database connection
conn = sqlite3.connect('school.db', check_same_thread=False)
c = conn.cursor()

# Create tables
tables = {
    "students": "(id INTEGER PRIMARY KEY, name TEXT, class TEXT, age INTEGER)",
    "teachers": "(id INTEGER PRIMARY KEY, name TEXT, subject TEXT)",
    "attendance": "(id INTEGER PRIMARY KEY, student_id INTEGER, date TEXT, status TEXT)",
    "fees": "(id INTEGER PRIMARY KEY, student_id INTEGER, amount REAL, paid INTEGER)",
    "exams": "(id INTEGER PRIMARY KEY, student_id INTEGER, subject TEXT, marks INTEGER)",
    "library": "(id INTEGER PRIMARY KEY, book TEXT, student_id INTEGER, issue_date TEXT)",
    "timetable": "(id INTEGER PRIMARY KEY, class TEXT, day TEXT, subject TEXT, teacher TEXT)"
}
for table, schema in tables.items():
    c.execute(f"CREATE TABLE IF NOT EXISTS {table} {schema}")
conn.commit()

# Helper functions
def get_df(table):
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)

def add_record(table, columns, values):
    placeholders = ','.join(['?' for _ in values])
    cols = ','.join(columns)
    c.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
    conn.commit()

def delete_record(table, id_val):
    c.execute(f"DELETE FROM {table} WHERE id=?", (id_val,))
    conn.commit()

# Sidebar with icons
st.sidebar.title("🏫 School Management")
module = st.sidebar.selectbox("Select Module", [
    "🏠 Dashboard", "👨‍🎓 Students", "👩‍🏫 Teachers", "📅 Attendance",
    "💰 Fees", "📝 Exams", "📚 Library", "🗓️ Timetable"
])

# Generic CRUD template function
def crud_module(title, table, fields, field_labels, add_cols):
    st.header(title)
    
    # Add new record
    with st.expander("➕ Add New Record", expanded=False):
        inputs = [st.text_input(label) if typ == "text" else st.number_input(label, min_value=0) 
                  for label, typ in zip(field_labels, ["text"] * len(fields))]
        if st.button("Add Record", type="primary", key=f"add_{table}"):
            add_record(table, add_cols, inputs)
            st.success("Record Added Successfully!")

    # View & Search
    df = get_df(table)
    search = st.text_input("🔍 Search", key=f"search_{table}")
    if search:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
    
    st.dataframe(df, use_container_width=True)

    # Edit & Delete
    with st.expander("✏️ Edit / 🗑️ Delete Record"):
        record_id = st.number_input("Enter ID", min_value=1, key=f"id_{table}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Record", key=f"del_{table}"):
                if st.checkbox("Confirm Delete? This cannot be undone!"):
                    delete_record(table, record_id)
                    st.error("Record Deleted!")
                    st.rerun()
        
        with col2:
            st.write("Update Fields:")
            updates = [st.text_input(f"New {label}", key=f"upd_{table}_{f}") for f, label in zip(fields, field_labels)]
            if st.button("Update Record", key=f"upd_{table}"):
                for field, value in zip(fields, updates):
                    if value:
                        c.execute(f"UPDATE {table} SET {field}=? WHERE id=?", (value, record_id))
                conn.commit()
                st.success("Record Updated!")

# Dashboard
if module == "🏠 Dashboard":
    st.title("🏫 School Management Dashboard")
    cols = st.columns(4)
    metrics = [
        ("Total Students", len(get_df('students'))),
        ("Total Teachers", len(get_df('teachers'))),
        ("Books Issued", len(get_df('library'))),
        ("Total Fees Paid", get_df('fees')['paid'].sum() if not get_df('fees').empty else 0)
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)

# Modules
elif module == "👨‍🎓 Students":
    crud_module("👨‍🎓 Students Management", "students", ["name", "class", "age"],
                ["Name", "Class", "Age"], ["name", "class", "age"])

elif module == "👩‍🏫 Teachers":
    crud_module("👩‍🏫 Teachers Management", "teachers", ["name", "subject"],
                ["Name", "Subject"], ["name", "subject"])

elif module == "📅 Attendance":
    st.header("📅 Attendance Management")
    with st.expander("Mark Attendance"):
        student_id = st.number_input("Student ID", min_value=1)
        status = st.selectbox("Status", ["Present", "Absent"])
        if st.button("Mark Attendance"):
            add_record("attendance", ["student_id", "date", "status"], [student_id, str(date.today()), status])
            st.success("Attendance Marked!")
    crud_module("View Attendance Records", "attendance", ["student_id", "date", "status"],
                ["Student ID", "Date", "Status"], ["student_id", "date", "status"])

elif module == "💰 Fees":
    crud_module("💰 Fees Management", "fees", ["student_id", "amount", "paid"],
                ["Student ID", "Amount", "Paid (1=Yes, 0=No)"], ["student_id", "amount", "paid"])

elif module == "📝 Exams":
    crud_module("📝 Exams & Marks", "exams", ["student_id", "subject", "marks"],
                ["Student ID", "Subject", "Marks"], ["student_id", "subject", "marks"])

elif module == "📚 Library":
    crud_module("📚 Library Management", "library", ["book", "student_id", "issue_date"],
                ["Book Title", "Student ID", "Issue Date (YYYY-MM-DD)"], ["book", "student_id", "issue_date"])

elif module == "🗓️ Timetable":
    crud_module("🗓️ Timetable Management", "timetable", ["class", "day", "subject", "teacher"],
                ["Class", "Day", "Subject", "Teacher"], ["class", "day", "subject", "teacher"])

st.caption("Beautiful & Complete School Management System in Streamlit 🏫 | Deploy on GitHub + Streamlit Cloud for free!")
