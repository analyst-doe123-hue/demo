from flask import Flask, render_template, request, redirect, url_for
import csv
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/gallery_uploads'

# Make sure the folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load student data once at startup
students_data = {}

def load_students():
    try:
        with open('edited_students.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                adm_no = row['Admission Number'].strip().upper()
                students_data[adm_no] = row
    except FileNotFoundError:
        print("⚠️ 'edited_students.csv' not found.")

def get_student_results(adm_no):
    results = []
    if os.path.exists('results.csv'):
        with open('results.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Admission Number'].strip().upper() == adm_no:
                    results.append({
                        'subject': row['Subject'],
                        'score': row['Score']
                    })
    return results

# === ROUTES ===

@app.route('/')
def home():
    return render_template('search.html')

@app.route('/search', methods=['POST'])
def search():
    adm_no = request.form.get('adm_no', '').strip().upper()
    if adm_no in students_data:
        return redirect(url_for('profile', adm_no=adm_no))
    return render_template('search.html', error="Student not found!")

@app.route('/profile/<adm_no>')
def profile(adm_no):
    adm_no = adm_no.strip().upper()
    student = students_data.get(adm_no)
    if student:
        return render_template('profile.html', student=student)
    return render_template('search.html', error="Student profile not found!")

@app.route('/profile', methods=['POST'])
def profile_redirect():
    adm_no = request.form.get('adm_no', '').strip().upper()
    return redirect(url_for('profile', adm_no=adm_no))

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        adm_no = request.form.get('adm_no', '').strip().upper()
        student = students_data.get(adm_no)
        if not student:
            return render_template('results.html', error="Student not found!")
        results = get_student_results(adm_no)
        return render_template('results.html', student=student, results=results)
    return render_template('results.html')

# ⬇️ UPDATED GALLERY ROUTE WITH UPLOAD SUPPORT
gallery_uploads = []

@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    global gallery_uploads
    if request.method == 'POST':
        file = request.files.get('photo')
        note = request.form.get('note', '')

        if file and file.filename:
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            # Store file info in memory
            gallery_uploads.append({'filename': filename, 'note': note})

        return redirect(url_for('gallery'))

    return render_template('gallery.html', uploads=gallery_uploads)

# Load student data on app start
load_students()

if __name__ == '__main__':
    app.run(debug=True)
