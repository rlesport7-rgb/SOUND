import os
import json
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template_string

app = Flask(__name__)

LIBRARY_FOLDER = 'library'
os.makedirs(LIBRARY_FOLDER, exist_ok=True)
JSON_PATH = os.path.join(LIBRARY_FOLDER, 'sounds.json')
ADMIN_PASSWORD = 'RASHID707'   # You can also use an env variable

# ---------- Helpers ----------
def load_sounds():
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, 'r') as f:
        return json.load(f)

def save_sounds(sounds):
    with open(JSON_PATH, 'w') as f:
        json.dump(sounds, f, indent=2)

# ---------- Public API ----------
@app.route('/api/sounds')
def api_sounds():
    return jsonify(load_sounds())

@app.route('/api/play/<filename>')
def serve_audio(filename):
    return send_from_directory(LIBRARY_FOLDER, filename)

# ---------- Admin API (password‑protected) ----------
def check_password():
    return request.form.get('password') == ADMIN_PASSWORD or request.args.get('password') == ADMIN_PASSWORD

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    if not check_password():
        return jsonify({'error': 'Unauthorized'}), 403
    file = request.files.get('file')
    name = request.form.get('name', 'Unnamed')
    if not file:
        return jsonify({'error': 'No file'}), 400
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file.save(os.path.join(LIBRARY_FOLDER, filename))
    sounds = load_sounds()
    sounds.append({"name": name, "file": filename})
    save_sounds(sounds)
    return jsonify({'success': True, 'file': filename})

@app.route('/admin/delete/<filename>', methods=['DELETE'])
def admin_delete(filename):
    if not check_password():
        return jsonify({'error': 'Unauthorized'}), 403
    filepath = os.path.join(LIBRARY_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    sounds = load_sounds()
    sounds = [s for s in sounds if s['file'] != filename]
    save_sounds(sounds)
    return jsonify({'success': True})

@app.route('/admin/rename', methods=['POST'])
def admin_rename():
    if not check_password():
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or request.form
    old_filename = data.get('file')
    new_name = data.get('name')
    if not old_filename or not new_name:
        return jsonify({'error': 'Missing parameters'}), 400
    sounds = load_sounds()
    for s in sounds:
        if s['file'] == old_filename:
            s['name'] = new_name
            break
    save_sounds(sounds)
    return jsonify({'success': True})

# ---------- Serve frontend ----------
@app.route('/')
def index():
    with open('templates/index.html', 'r') as f:
        return render_template_string(f.read())

if __name__ == '__main__':
    app.run(debug=True)