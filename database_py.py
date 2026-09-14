import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "updf_recruitment.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applicants (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      application_number TEXT UNIQUE NOT NULL,
      surname TEXT NOT NULL,
      given_names TEXT NOT NULL,
      date_of_birth TEXT NOT NULL,
      age INTEGER,
      gender TEXT NOT NULL,
      marital_status TEXT NOT NULL,
      religion TEXT,
      national_id TEXT UNIQUE NOT NULL,
      phone TEXT NOT NULL,
      alternate_phone TEXT,
      email TEXT,
      district_of_origin TEXT NOT NULL,
      district_of_residence TEXT NOT NULL,
      sub_county TEXT NOT NULL,
      parish TEXT NOT NULL,
      village TEXT NOT NULL,
      height_cm INTEGER NOT NULL,
      weight_kg INTEGER NOT NULL,
      chest_cm INTEGER,
      blood_group TEXT,
      eye_color TEXT,
      hair_color TEXT,
      distinguishing_marks TEXT,
      has_disability TEXT DEFAULT 'No',
      disability_details TEXT,
      recruitment_category TEXT NOT NULL,
      professional_category TEXT,
      uce_index TEXT, uce_year INTEGER, uce_aggregate INTEGER, uce_school TEXT, uce_grade TEXT,
      uace_index TEXT, uace_year INTEGER, uace_points INTEGER, uace_school TEXT, uace_grade TEXT,
      higher_edu_institution TEXT, higher_edu_qualification TEXT, higher_edu_field TEXT, higher_edu_year INTEGER,
      current_employer TEXT, current_position TEXT, years_experience INTEGER,
      nok_name TEXT NOT NULL, nok_relationship TEXT NOT NULL, nok_phone TEXT NOT NULL, nok_address TEXT NOT NULL,
      lc1_name TEXT, lc2_name TEXT, lc3_name TEXT, giso_diso_name TEXT, rdc_name TEXT,
      has_criminal_record TEXT DEFAULT 'No', criminal_details TEXT,
      has_medical_condition TEXT DEFAULT 'No', medical_details TEXT,
      previously_dismissed TEXT DEFAULT 'No',
      passport_photo_path TEXT, national_id_path TEXT, uce_certificate_path TEXT,
      uace_certificate_path TEXT, degree_certificate_path TEXT, other_docs_path TEXT,
      status TEXT DEFAULT 'Submitted',
      shortlist_center TEXT, interview_date TEXT, admin_notes TEXT, rejection_reason TEXT,
      declaration_accepted INTEGER DEFAULT 1,
      submitted_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT DEFAULT 'Superadmin',
      is_active INTEGER DEFAULT 1,
      last_login TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    cursor.execute("SELECT id FROM admins WHERE email = ?", ("admin@updf.go.ug",))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admins (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                       ("superadmin", "admin@updf.go.ug", "Admin@1234", "Superadmin"))
        print("Default admin created: admin@updf.go.ug / Admin@1234")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recruitment_cycles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      cycle_name TEXT NOT NULL,
      intake_year INTEGER NOT NULL,
      applications_open TEXT NOT NULL,
      applications_close TEXT NOT NULL,
      is_active INTEGER DEFAULT 1,
      description TEXT
    )
    """)
    cursor.execute("SELECT id FROM recruitment_cycles LIMIT 1")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO recruitment_cycles (cycle_name, intake_year, applications_open, applications_close, is_active, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """, ("UPDF General & Professional Recruitment 2026", 2026, "2026-09-01", "2026-12-31", 1, "Annual Recruitment Exercise"))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
