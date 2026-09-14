import os
import sys
import json
import sqlite3
import random
import datetime
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 3000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "updf_recruitment.db")

SESSIONS = {}

DISTRICTS = [
    "Abim","Adjumani","Agago","Alebtong","Amolatar","Amudat","Amuria","Amuru","Apac","Arua",
    "Budaka","Bududa","Bugiri","Bugweri","Buhweju","Buikwe","Bukedea","Bukomansimbi","Bukwo",
    "Bulambuli","Buliisa","Bundibugyo","Bunyangabu","Bushenyi","Busia","Busiki","Butaleja",
    "Butambala","Butebo","Buvuma","Buyende","Dokolo","Gomba","Gulu","Hoima","Ibanda","Iganga",
    "Isingiro","Jinja","Kaabong","Kabale","Kabarole","Kaberamaido","Kagadi","Kakumiro","Kalaki",
    "Kalangala","Kaliro","Kalungu","Kampala","Kamuli","Kamwenge","Kanungu","Kapchorwa",
    "Kapelebyong","Karenga","Kasese","Katakwi","Kayunga","Kazo","Kibaale","Kiboga","Kibuku",
    "Kikuube","Kiruhura","Kiryandongo","Kisoro","Kitagwenda","Kitgum","Koboko","Kole","Kotido",
    "Kumi","Kwania","Kween","Kyankwanzi","Kyegegwa","Kyenjojo","Kyotera","Lamwo","Lira","Luuka",
    "Luwero","Lwengo","Lyantonde","Madi-Okollo","Manafwa","Maracha","Masaka","Masindi","Mayuge",
    "Mbale","Mbarara","Mitooma","Mityana","Moroto","Moyo","Mpigi","Mubende","Mukono",
    "Nabilatuk","Nakapiripirit","Nakaseke","Nakasongola","Namayingo","Namisindwa","Namutumba",
    "Napak","Nebbi","Ngora","Ntoroko","Ntungamo","Nwoya","Obongi","Omoro","Otuke","Oyam",
    "Pader","Pakwach","Pallisa","Rakai","Rubanda","Rubirizi","Rukiga","Rukungiri","Rwampara",
    "Sembabule","Serere","Sheema","Sironko","Soroti","Tororo","Wakiso","Yumbe","Zombo"
]

class UPDFHandler(SimpleHTTPRequestHandler):
    def get_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def send_json(self, data, code=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Route matching
        if path == "/":
            return self.serve_file(os.path.join(BASE_DIR, "public", "index.html"), "text/html")
        elif path == "/application-form":
            return self.serve_file(os.path.join(BASE_DIR, "public", "apply.html"), "text/html")
        elif path == "/check-status":
            return self.serve_file(os.path.join(BASE_DIR, "public", "status.html"), "text/html")
        elif path == "/requirements":
            return self.serve_file(os.path.join(BASE_DIR, "public", "requirements.html"), "text/html")
        elif path == "/guidelines":
            return self.serve_file(os.path.join(BASE_DIR, "public", "guidelines.html"), "text/html")
        elif path == "/admin/login" or path == "/admin":
            return self.serve_file(os.path.join(BASE_DIR, "views", "admin", "login.html"), "text/html")
        elif path == "/admin/dashboard":
            return self.serve_file(os.path.join(BASE_DIR, "views", "admin", "dashboard.html"), "text/html")
        elif path == "/admin/applications":
            return self.serve_file(os.path.join(BASE_DIR, "views", "admin", "applications.html"), "text/html")
        elif path == "/admin/users":
            return self.serve_file(os.path.join(BASE_DIR, "views", "admin", "users.html"), "text/html")

        # API Endpoints
        elif path == "/api/districts":
            return self.send_json({"success": True, "data": DISTRICTS})
        elif path == "/api/cycle":
            conn = self.get_db()
            row = conn.execute("SELECT * FROM recruitment_cycles WHERE is_active = 1 LIMIT 1").fetchone()
            conn.close()
            return self.send_json({"success": True, "data": dict(row) if row else None})
        elif path.startswith("/api/check-nin/"):
            nin = urllib.parse.unquote(path.split("/api/check-nin/")[1])
            conn = self.get_db()
            row = conn.execute("SELECT id FROM applicants WHERE national_id = ?", (nin,)).fetchone()
            conn.close()
            return self.send_json({"exists": bool(row)})
        elif path.startswith("/apply/status/"):
            app_num = urllib.parse.unquote(path.split("/apply/status/")[1]).upper()
            conn = self.get_db()
            row = conn.execute("""
                SELECT application_number, surname, given_names, gender, district_of_origin,
                       recruitment_category, professional_category, status, shortlist_center,
                       interview_date, submitted_at
                FROM applicants WHERE application_number = ?
            """, (app_num,)).fetchone()
            conn.close()
            if row:
                return self.send_json({"success": True, "data": dict(row)})
            else:
                return self.send_json({"success": False, "message": "Application not found."}, 404)
        elif path == "/auth/me":
            return self.send_json({"success": True, "admin": {"username": "superadmin", "role": "Superadmin", "email": "admin@updf.go.ug"}})
        elif path == "/admin/api/stats":
            conn = self.get_db()
            stats = {
                "total": conn.execute("SELECT COUNT(*) as c FROM applicants").fetchone()["c"],
                "submitted": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE status='Submitted'").fetchone()["c"],
                "under_review": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE status='Under Review'").fetchone()["c"],
                "shortlisted": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE status='Shortlisted'").fetchone()["c"],
                "accepted": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE status='Accepted'").fetchone()["c"],
                "rejected": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE status='Rejected'").fetchone()["c"],
                "general": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE recruitment_category='General Recruit'").fetchone()["c"],
                "professional": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE recruitment_category='Professional'").fetchone()["c"],
                "male": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE gender='Male'").fetchone()["c"],
                "female": conn.execute("SELECT COUNT(*) as c FROM applicants WHERE gender='Female'").fetchone()["c"],
                "by_district": [dict(r) for r in conn.execute("SELECT district_of_origin as district, COUNT(*) as count FROM applicants GROUP BY district_of_origin ORDER BY count DESC LIMIT 15").fetchall()],
                "by_category": [dict(r) for r in conn.execute("SELECT professional_category as category, COUNT(*) as count FROM applicants WHERE recruitment_category='Professional' AND professional_category IS NOT NULL GROUP BY professional_category ORDER BY count DESC").fetchall()],
                "recent": [dict(r) for r in conn.execute("SELECT application_number, surname, given_names, district_of_origin, recruitment_category, status, submitted_at FROM applicants ORDER BY id DESC LIMIT 10").fetchall()]
            }
            conn.close()
            return self.send_json({"success": True, "data": stats})
        elif path == "/admin/api/applications":
            query = urllib.parse.parse_qs(parsed.query)
            status = query.get("status", [None])[0]
            district = query.get("district", [None])[0]
            category = query.get("category", [None])[0]
            search = query.get("search", [None])[0]
            page = int(query.get("page", [1])[0])
            limit = int(query.get("limit", [25])[0])
            offset = (page - 1) * limit

            where = ["1=1"]
            params = []
            if status: where.append("status = ?"); params.append(status)
            if district: where.append("district_of_origin = ?"); params.append(district)
            if category: where.append("recruitment_category = ?"); params.append(category)
            if search:
                where.append("(application_number LIKE ? OR national_id LIKE ? OR surname LIKE ? OR given_names LIKE ?)")
                s = f"%{search}%"
                params.extend([s, s, s, s])

            w_clause = " AND ".join(where)
            conn = self.get_db()
            total = conn.execute(f"SELECT COUNT(*) as c FROM applicants WHERE {w_clause}", params).fetchone()["c"]
            rows = conn.execute(f"SELECT * FROM applicants WHERE {w_clause} ORDER BY id DESC LIMIT ? OFFSET ?", params + [limit, offset]).fetchall()
            conn.close()

            return self.send_json({"success": True, "data": [dict(r) for r in rows], "total": total, "page": page, "limit": limit})
        elif path.startswith("/admin/api/applications/"):
            app_id = path.split("/")[-1]
            conn = self.get_db()
            row = conn.execute("SELECT * FROM applicants WHERE id = ?", (app_id,)).fetchone()
            conn.close()
            if row:
                return self.send_json({"success": True, "data": dict(row)})
            return self.send_json({"error": "Not found"}, 404)
        elif path == "/admin/api/users":
            conn = self.get_db()
            rows = conn.execute("SELECT id, username, email, role, is_active, last_login, created_at FROM admins").fetchall()
            conn.close()
            return self.send_json({"success": True, "data": [dict(r) for r in rows]})
        elif path == "/admin/api/export/csv":
            conn = self.get_db()
            rows = conn.execute("SELECT application_number, surname, given_names, gender, age, date_of_birth, national_id, phone, email, district_of_origin, district_of_residence, recruitment_category, professional_category, status, submitted_at FROM applicants").fetchall()
            conn.close()

            lines = ["Application Number,Surname,Given Names,Gender,Age,DOB,National ID,Phone,Email,District Origin,District Residence,Category,Professional Category,Status,Submitted At"]
            for r in rows:
                d = dict(r)
                lines.append(f'"{d["application_number"]}","{d["surname"]}","{d["given_names"]}","{d["gender"]}",{d["age"] or ""},"{d["date_of_birth"]}","{d["national_id"]}","{d["phone"]}","{d["email"] or ""}","{d["district_of_origin"]}","{d["district_of_residence"]}","{d["recruitment_category"]}","{d["professional_category"] or ""}","{d["status"]}","{d["submitted_at"]}"')

            csv_data = "\n".join(lines).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", 'attachment; filename="updf_applications.csv"')
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)
            return

        # Serve static files from public
        filepath = os.path.join(BASE_DIR, "public", path.lstrip("/"))
        if os.path.isfile(filepath):
            ext = os.path.splitext(filepath)[1]
            mime = {".css": "text/css", ".js": "application/javascript", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}.get(ext, "text/plain")
            return self.serve_file(filepath, mime)

        self.send_error(404, "Page not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        if path == "/auth/login":
            data = json.loads(body.decode('utf-8'))
            email = data.get("email")
            password = data.get("password")
            if email == "admin@updf.go.ug" and (password == "Admin@1234" or password == "admin"):
                return self.send_json({"success": True, "role": "Superadmin"})
            return self.send_json({"error": "Invalid email or password"}, 401)

        elif path == "/auth/logout":
            return self.send_json({"success": True})

        elif path == "/apply/submit":
            ctype = self.headers.get('Content-Type', '')
            data = {}
            if 'multipart/form-data' in ctype:
                boundary = ctype.split('boundary=')[1].encode()
                parts = body.split(b'--' + boundary)
                for part in parts:
                    if b'Content-Disposition' in part:
                        headers_body = part.split(b'\r\n\r\n', 1)
                        if len(headers_body) == 2:
                            h, val = headers_body
                            val = val.rstrip(b'\r\n')
                            name_part = [x for x in h.decode('utf-8', 'ignore').split(';') if 'name=' in x]
                            if name_part and 'filename=' not in h.decode('utf-8', 'ignore'):
                                name = name_part[0].split('=')[1].strip('"\'')
                                data[name] = val.decode('utf-8', 'ignore')
            else:
                data = json.loads(body.decode('utf-8'))

            app_num = f"UPDF-{datetime.date.today().year}-{random.randint(100000, 999999)}"
            conn = self.get_db()
            cursor = conn.cursor()
            
            nin = data.get("national_id", "").strip().upper()
            if not nin:
                return self.send_json({"success": False, "message": "National ID required."}, 400)

            dup = cursor.execute("SELECT id FROM applicants WHERE national_id = ?", (nin,)).fetchone()
            if dup:
                conn.close()
                return self.send_json({"success": False, "message": "An application with this National ID already exists."}, 409)

            dob = data.get("date_of_birth", "2000-01-01")
            age = datetime.date.today().year - int(dob.split("-")[0])

            cursor.execute("""
                INSERT INTO applicants (
                    application_number, surname, given_names, date_of_birth, age, gender, marital_status, religion,
                    national_id, phone, alternate_phone, email, district_of_origin, district_of_residence,
                    sub_county, parish, village, height_cm, weight_kg, blood_group,
                    recruitment_category, professional_category, uce_index, uce_year, uce_aggregate, uce_grade,
                    uace_index, uace_year, uace_points, uace_grade, higher_edu_institution, higher_edu_qualification,
                    higher_edu_field, nok_name, nok_relationship, nok_phone, nok_address,
                    lc1_name, lc2_name, lc3_name, giso_diso_name, rdc_name,
                    has_disability, has_medical_condition, has_criminal_record, previously_dismissed, declaration_accepted
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
            """, (
                app_num, data.get("surname","").upper(), data.get("given_names","").upper(), dob, age,
                data.get("gender","Male"), data.get("marital_status","Single"), data.get("religion"),
                nin, data.get("phone",""), data.get("alternate_phone"), data.get("email"),
                data.get("district_of_origin","Kampala"), data.get("district_of_residence","Kampala"),
                data.get("sub_county",""), data.get("parish",""), data.get("village",""),
                int(data.get("height_cm", 170)), int(data.get("weight_kg", 65)), data.get("blood_group"),
                data.get("recruitment_category","General Recruit"), data.get("professional_category"),
                data.get("uce_index"), data.get("uce_year"), data.get("uce_aggregate"), data.get("uce_grade"),
                data.get("uace_index"), data.get("uace_year"), data.get("uace_points"), data.get("uace_grade"),
                data.get("higher_edu_institution"), data.get("higher_edu_qualification"), data.get("higher_edu_field"),
                data.get("nok_name",""), data.get("nok_relationship",""), data.get("nok_phone",""), data.get("nok_address",""),
                data.get("lc1_name"), data.get("lc2_name"), data.get("lc3_name"), data.get("giso_diso_name"), data.get("rdc_name"),
                data.get("has_disability","No"), data.get("has_medical_condition","No"), data.get("has_criminal_record","No"),
                data.get("previously_dismissed","No")
            ))
            conn.commit()
            conn.close()

            return self.send_json({
                "success": True,
                "message": "Application submitted successfully!",
                "application_number": app_num,
                "applicant_name": f"{data.get('surname','')} {data.get('given_names','')}"
            })

        elif path == "/admin/api/applications/bulk-status":
            data = json.loads(body.decode('utf-8'))
            ids = data.get("ids", [])
            status = data.get("status")
            if ids and status:
                conn = self.get_db()
                placeholders = ",".join(["?"] * len(ids))
                conn.execute(f"UPDATE applicants SET status = ? WHERE id IN ({placeholders})", [status] + ids)
                conn.commit()
                conn.close()
                return self.send_json({"success": True, "message": f"{len(ids)} application(s) updated to {status}."})
            return self.send_json({"error": "Invalid data"}, 400)

        elif path == "/admin/api/users":
            data = json.loads(body.decode('utf-8'))
            conn = self.get_db()
            try:
                conn.execute("INSERT INTO admins (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                             (data.get("username"), data.get("email"), data.get("password"), data.get("role")))
                conn.commit()
                conn.close()
                return self.send_json({"success": True, "message": "User created."})
            except Exception as e:
                conn.close()
                return self.send_json({"error": "Username/Email already exists."}, 409)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length).decode('utf-8'))

        if path.startswith("/admin/api/applications/") and path.endswith("/status"):
            app_id = path.split("/")[4]
            status = body.get("status")
            notes = body.get("admin_notes")
            center = body.get("shortlist_center")
            idate = body.get("interview_date")
            reason = body.get("rejection_reason")

            conn = self.get_db()
            conn.execute("UPDATE applicants SET status=?, admin_notes=?, shortlist_center=?, interview_date=?, rejection_reason=? WHERE id=?",
                         (status, notes, center, idate, reason, app_id))
            conn.commit()
            conn.close()
            return self.send_json({"success": True, "message": "Status updated successfully."})

        elif path.startswith("/admin/api/users/"):
            uid = path.split("/")[-1]
            active = body.get("is_active", 1)
            conn = self.get_db()
            conn.execute("UPDATE admins SET is_active=? WHERE id=?", (active, uid))
            conn.commit()
            conn.close()
            return self.send_json({"success": True, "message": "User updated."})

    def serve_file(self, filepath, content_type):
        if not os.path.exists(filepath):
            return self.send_error(404, "File not found")
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__ == "__main__":
    print(f"UPDF Recruitment Portal running on http://localhost:{PORT}")
    print(f"Admin Dashboard: http://localhost:{PORT}/admin")
    print(f"Application Form: http://localhost:{PORT}/application-form")
    server = HTTPServer(("0.0.0.0", PORT), UPDFHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
