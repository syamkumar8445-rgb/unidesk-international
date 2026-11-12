from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = 'unidesk_secret_key_advanced_crm'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "student": {
        "password": "123", 
        "role": "student", 
        "name": "Rahul Menon", 
        "address": "Kollam, Kerala, India", 
        "dob": "15-06-2002", 
        "education": "BSc Computer Science", 
        "study_history": "2020 - 2023 at University College", 
        "target_country": "United Kingdom (UK)", 
        "target_course": "MSc Artificial Intelligence", 
        "status": "Pending Admin Approval",
        "progress_status": "Document Verification Pending",
        "contact_count": 0,
        "certificates": []
    }
}
TEMP_OTP_STORAGE = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def student_login():
    action = request.args.get('action', 'login')
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'login':
            username = request.form['username']
            password = request.form['password']
            if username in USERS and USERS[username]['password'] == password and USERS[username]['role'] == 'student':
                session['user'] = username
                session['role'] = 'student'
                return redirect(url_for('student_dashboard'))
            else:
                return render_template('login.html', error="Invalid Username or Password", action='login')
        elif form_type == 'register':
            email = request.form['email']
            otp = str(random.randint(100000, 999999))
            TEMP_OTP_STORAGE[email] = otp
            print(f"DEBUG OTP for {email}: {otp}")
            return render_template('login.html', action='verify_otp', email=email)
        elif form_type == 'verify':
            email = request.form['email']
            user_otp = request.form['otp']
            if email in TEMP_OTP_STORAGE and TEMP_OTP_STORAGE[email] == user_otp:
                USERS[email] = {
                    "password": request.form['new_password'], 
                    "role": "student", 
                    "name": "New Student", 
                    "address": "Not Provided", 
                    "dob": "Not Provided", 
                    "education": "Not Provided", 
                    "study_history": "Not Provided", 
                    "target_country": "Not Selected", 
                    "target_course": "Not Selected", 
                    "status": "Pending Admin Approval",
                    "progress_status": "Profile Created",
                    "contact_count": 0,
                    "certificates": []
                }
                return render_template('login.html', error="Account created successfully! Please login.", action='login')
            else:
                return render_template('login.html', error="Invalid OTP, try again.", action='verify_otp', email=email)
    return render_template('login.html', action=action)

@app.route('/student-dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if 'user' in session and session['role'] == 'student':
        username = session['user']
        user_data = USERS[username]
            
        if request.method == 'POST':
            if 'update_profile' in request.form:
                user_data['name'] = request.form.get('name')
                user_data['address'] = request.form.get('address')
                user_data['dob'] = request.form.get('dob')
                user_data['education'] = request.form.get('education')
                user_data['study_history'] = request.form.get('study_history')
                user_data['target_country'] = request.form.get('target_country')
                user_data['target_course'] = request.form.get('target_course')
            elif 'upload_cert' in request.form:
                doc_type = request.form.get('doc_type')
                file = request.files.get('certificate_file')
                if file and file.filename != '':
                    filename = file.filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    user_data['certificates'].append({"type": doc_type, "filename": filename, "status": "Under Review"})
                
        return render_template('student_dashboard.html', username=username, user=user_data)
    return redirect(url_for('student_login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username]['password'] == password and USERS[username]['role'] == 'admin':
            session['user'] = username
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid Admin Credentials")
    return render_template('admin_login.html')

@app.route('/admin-dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user' in session and session['role'] == 'admin':
        if request.method == 'POST':
            student_email = request.form.get('student_email')
            action_type = request.form.get('action_type')
            
            if student_email in USERS:
                if action_type == 'approve':
                    USERS[student_email]['status'] = 'Active & Approved'
                elif action_type == 'reject':
                    USERS[student_email]['status'] = 'Rejected'
                elif action_type == 'update_crm':
                    USERS[student_email]['progress_status'] = request.form.get('progress_status')
                    if 'add_contact' in request.form:
                        USERS[student_email]['contact_count'] += 1
                        
        search_query = request.args.get('search', '').lower()
        students_list = {}
        for k, v in USERS.items():
            if v['role'] == 'student':
                if search_query in k.lower() or search_query in v['name'].lower() or search_query in v['target_country'].lower():
                    students_list[k] = v
                    
        pending_count = sum(1 for v in USERS.values() if v.get('role') == 'student' and v.get('status') == 'Pending Admin Approval')
        return render_template('admin_dashboard.html', students=students_list, pending_count=pending_count, search_query=search_query, user={'name': session['user']})
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)