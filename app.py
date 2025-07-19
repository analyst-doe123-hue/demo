from flask import Flask, render_template, request, redirect, url_for
import csv
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/gallery_uploads'
app.config['RESULTS_UPLOAD_FOLDER'] = 'static/results_uploads'
app.config['ALLOWED_RESULT_EXTENSIONS'] = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_UPLOAD_FOLDER'], exist_ok=True)

students_data = {}
uploads = []

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

def allowed_result_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_RESULT_EXTENSIONS']

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
    else:
        adm_no = request.args.get('adm_no', '').strip().upper()

    if not adm_no:
        return render_template('results.html')

    student = students_data.get(adm_no)
    if not student:
        return render_template('results.html', error="Student not found!")

    results = get_student_results(adm_no)

    # PDF and note
    pdf_filename = f"{adm_no}_result.pdf"
    note_filename = f"{adm_no}_note.txt"
    pdf_path = os.path.join(app.config['RESULTS_UPLOAD_FOLDER'], pdf_filename)
    note_path = os.path.join(app.config['RESULTS_UPLOAD_FOLDER'], note_filename)

    result_pdf_url = url_for('static', filename=f"results_uploads/{pdf_filename}") if os.path.exists(pdf_path) else None
    result_note = ""
    if os.path.exists(note_path):
        with open(note_path, 'r', encoding='utf-8') as f:
            result_note = f.read()

    return render_template('results.html', student=student, results=results, result_pdf=result_pdf_url, result_note=result_note)

@app.route('/upload_result_file', methods=['POST'])
def upload_result_file():
    adm_no = request.form.get('adm_no', '').strip().upper()
    note = request.form.get('note', '')
    file = request.files.get('result_pdf')

    if adm_no not in students_data:
        return render_template('results.html', error="Student not found!")

    if file and allowed_result_file(file.filename):
        filename = secure_filename(f"{adm_no}_result.pdf")
        filepath = os.path.join(app.config['RESULTS_UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Save note
        note_path = os.path.join(app.config['RESULTS_UPLOAD_FOLDER'], f"{adm_no}_note.txt")
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(note)

        return redirect(url_for('results', adm_no=adm_no))
    else:
        return render_template('results.html', error="Invalid file type. Please upload a PDF.")

@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    if request.method == 'POST':
        photo = request.files.get('photo')
        note = request.form.get('note', '')

        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(filepath)
            uploads.append({'filename': filename, 'note': note})
        return redirect(url_for('gallery'))

    return render_template('gallery.html', uploads=uploads)

# Load students at startup
load_students()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # ensure it's deployable
