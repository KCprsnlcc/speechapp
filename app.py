from flask import Flask, request, jsonify, render_template_string, send_file
import speech_recognition as sr
import sqlite3
from flask_cors import CORS
import io
import datetime
from googletrans import Translator, LANGUAGES

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

DATABASE = 'database.db'

# Initialize the database and create tables if they don't exist
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transcription TEXT NOT NULL,
            translated_text TEXT,
            translation_direction TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Route: Home Page
@app.route('/')
def index():
    return render_template_string(html_template)

# Route: Transcribe Audio
@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio_data' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio_data']

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        transcription = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        transcription = "Sorry, could not understand the audio."
    except sr.RequestError:
        transcription = "Could not request results from the speech recognition service."

    # Save transcription to database without translation initially
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO transcriptions (transcription) VALUES (?)', (transcription,))
    conn.commit()
    conn.close()

    return jsonify({'transcription': transcription}), 200

# Route: Translate Transcription
@app.route('/translate/<int:transcription_id>', methods=['POST'])
def translate_transcription(transcription_id):
    data = request.get_json()
    direction = data.get('direction')  # 'en_to_tl' or 'tl_to_en'

    if direction not in ['en_to_tl', 'tl_to_en']:
        return jsonify({'error': 'Invalid translation direction.'}), 400

    # Fetch the transcription from the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT transcription FROM transcriptions WHERE id = ?', (transcription_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Transcription not found.'}), 404

    original_text = row[0]

    translator = Translator()
    try:
        if direction == 'en_to_tl':
            translated = translator.translate(original_text, src='en', dest='tl')
        else:
            translated = translator.translate(original_text, src='tl', dest='en')
        translated_text = translated.text
    except Exception as e:
        return jsonify({'error': 'Translation failed.', 'details': str(e)}), 500

    # Update the transcription with translated text and direction
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transcriptions 
        SET translated_text = ?, translation_direction = ?
        WHERE id = ?
    ''', (translated_text, direction, transcription_id))
    conn.commit()
    conn.close()

    return jsonify({'translated_text': translated_text, 'direction': direction}), 200

# Route: Get All Transcriptions
@app.route('/get_transcriptions', methods=['GET'])
def get_transcriptions():
    search_query = request.args.get('search', '')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    if search_query:
        cursor.execute('''
            SELECT id, transcription, translated_text, translation_direction, timestamp FROM transcriptions 
            WHERE transcription LIKE ? 
            ORDER BY timestamp DESC
        ''', ('%'+search_query+'%',))
    else:
        cursor.execute('SELECT id, transcription, translated_text, translation_direction, timestamp FROM transcriptions ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()

    transcriptions = [
        {
            'id': row[0],
            'transcription': row[1],
            'translated_text': row[2],
            'translation_direction': row[3],
            'timestamp': row[4]
        }
        for row in rows
    ]

    return jsonify({'transcriptions': transcriptions}), 200

# Route: Delete Transcription
@app.route('/delete_transcription/<int:transcription_id>', methods=['DELETE'])
def delete_transcription(transcription_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transcriptions WHERE id = ?', (transcription_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200

# Route: Edit Transcription
@app.route('/edit_transcription/<int:transcription_id>', methods=['PUT'])
def edit_transcription(transcription_id):
    data = request.get_json()
    new_text = data.get('transcription', '')

    if not new_text:
        return jsonify({'error': 'No transcription provided'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transcriptions 
        SET transcription = ?, translated_text = NULL, translation_direction = NULL, timestamp = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (new_text, transcription_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'transcription': new_text}), 200

# Route: Download Transcriptions
@app.route('/download_transcriptions', methods=['GET'])
def download_transcriptions():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT transcription, translated_text, translation_direction, timestamp FROM transcriptions ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    for row in rows:
        transcription = row[0]
        translated_text = row[1] if row[1] else ""
        direction = row[2] if row[2] else ""
        timestamp = row[3]
        if translated_text and direction:
            if direction == 'en_to_tl':
                direction_text = "English to Tagalog"
            else:
                direction_text = "Tagalog to English"
            output.write(f"{timestamp} - {transcription} | {direction_text} | {translated_text}\n")
        else:
            output.write(f"{timestamp} - {transcription}\n")
    output.seek(0)

    return send_file(
        io.BytesIO(output.read().encode()),
        mimetype='text/plain',
        as_attachment=True,
        attachment_filename='transcriptions.txt'
    )

# HTML Template with Embedded CSS and JavaScript
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Advanced Speech Recognition App</title>
    <style>
        /* CSS Styling */

        :root {
            /* Default Color Palette */
            --bg-color: #0e2326;
            --accent-color: #689e4b;
            --text-color: #FFFFFF;
            --button-hover: #557c3b;
            --button-active: #b22222;
        }

        /* Color Blind Mode Palette */
        .color-blind-mode {
            --bg-color: #1a1a1a;
            --accent-color: #f1c40f; /* Yellow for better visibility */
            --text-color: #FFFFFF;
            --button-hover: #d4ac0d;
            --button-active: #e74c3c;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            transition: background-color 0.3s, color 0.3s;
        }

        .container {
            max-width: 900px;
            margin: 30px auto;
            padding: 20px;
            background-color: var(--bg-color);
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
            transition: background-color 0.3s;
        }

        h1, h2 {
            text-align: center;
            color: var(--accent-color);
            transition: color 0.3s;
        }

        button {
            display: inline-block;
            margin: 10px 5px;
            padding: 12px 25px;
            font-size: 16px;
            color: var(--text-color);
            background-color: var(--accent-color);
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button:hover {
            background-color: var(--button-hover);
        }

        button.recording {
            background-color: var(--button-active);
        }

        #status {
            text-align: center;
            margin-top: 10px;
            font-size: 18px;
        }

        #searchBar {
            width: 100%;
            padding: 10px;
            margin: 20px 0;
            border: 2px solid var(--accent-color);
            border-radius: 5px;
            font-size: 16px;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: border-color 0.3s, background-color 0.3s, color 0.3s;
        }

        #transcriptionContainer {
            margin-top: 30px;
        }

        #transcriptionList {
            list-style-type: none;
            padding: 0;
        }

        .transcription-item {
            background-color: var(--accent-color);
            margin-bottom: 10px;
            padding: 15px;
            border-radius: 4px;
            color: var(--text-color);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: background-color 0.3s;
        }

        .transcription-text {
            margin-bottom: 10px;
        }

        .transcription-actions {
            display: flex;
            flex-wrap: wrap;
        }

        .transcription-actions button {
            margin-right: 5px;
            margin-bottom: 5px;
            padding: 8px 12px;
            font-size: 14px;
        }

        /* Color Blind Mode Specific Styles */
        .color-blind-mode .transcription-item {
            background-color: #f1c40f; /* Yellow for better visibility */
        }

        .color-blind-mode button {
            background-color: #f1c40f;
            color: #000000;
        }

        .color-blind-mode button:hover {
            background-color: #d4ac0d;
        }

        .color-blind-mode #searchBar {
            border-color: #f1c40f;
        }

        /* Responsive Design */
        @media (max-width: 600px) {
            .transcription-item {
                flex-direction: column;
                align-items: flex-start;
            }

            .transcription-actions {
                margin-top: 10px;
            }
        }

        /* Modal Styling */
        .modal {
            display: none; 
            position: fixed; 
            z-index: 2; 
            padding-top: 100px; 
            left: 0;
            top: 0;
            width: 100%; 
            height: 100%; 
            overflow: auto; 
            background-color: rgba(0,0,0,0.4); 
        }

        .modal-content {
            background-color: var(--bg-color);
            margin: auto;
            padding: 20px;
            border: 1px solid var(--accent-color);
            width: 80%;
            border-radius: 8px;
            transition: background-color 0.3s, border-color 0.3s;
        }

        .color-blind-mode .modal-content {
            border-color: #f1c40f;
        }

        .close {
            color: var(--text-color);
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.3s;
        }

        .color-blind-mode .close:hover,
        .color-blind-mode .close:focus {
            color: #f1c40f;
        }

        /* Toggle Switch Styling */
        .toggle-switch {
            position: fixed;
            top: 20px;
            right: 20px;
            display: flex;
            align-items: center;
            font-size: 14px;
        }

        .toggle-switch input {
            display: none;
        }

        .toggle-switch label {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
            margin-right: 10px;
        }

        .toggle-switch label::before {
            content: "";
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background-color: #ffffff;
            border-radius: 50%;
            transition: transform 0.3s;
        }

        .toggle-switch input:checked + label::before {
            transform: translateX(26px);
        }

        .toggle-switch span {
            color: var(--text-color);
        }

        .color-blind-mode .toggle-switch span {
            color: #f1c40f;
        }

        /* Translation Direction Selection */
        .translation-options {
            margin-top: 10px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }

        .translation-options label {
            margin-right: 10px;
        }

        .translation-options select {
            padding: 8px;
            border: 2px solid var(--accent-color);
            border-radius: 5px;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: border-color 0.3s, background-color 0.3s, color 0.3s;
        }

    </style>
</head>
<body>
    <!-- Toggle Switch for Color Blind Mode -->
    <div class="toggle-switch">
        <input type="checkbox" id="colorBlindToggle">
        <label for="colorBlindToggle"></label>
        <span>Color Blind Mode</span>
    </div>

    <div class="container">
        <h1>Speech Recognition App</h1>
        <button id="recordButton" aria-label="Start recording">Record</button>
        <button id="downloadButton">Download Transcriptions</button>
        <p id="status" aria-live="polite">Press the button to start recording.</p>

        <input type="text" id="searchBar" placeholder="Search transcriptions...">

        <div id="transcriptionContainer">
            <h2>Transcriptions</h2>
            <ul id="transcriptionList">
                <!-- Transcriptions will be populated here -->
            </ul>
        </div>
    </div>

    <!-- Edit Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close" id="closeModal">&times;</span>
            <h2>Edit Transcription</h2>
            <textarea id="editText" rows="4" style="width: 100%; padding: 10px; border: 2px solid var(--accent-color); border-radius: 5px; background-color: var(--bg-color); color: var(--text-color);"></textarea>
            <button id="saveEditButton">Save</button>
        </div>
    </div>

    <!-- Translation Modal -->
    <div id="translateModal" class="modal">
        <div class="modal-content">
            <span class="close" id="closeTranslateModal">&times;</span>
            <h2>Translate Transcription</h2>
            <div class="translation-options">
                <label for="translationDirection">Direction:</label>
                <select id="translationDirection">
                    <option value="en_to_tl">English to Tagalog</option>
                    <option value="tl_to_en">Tagalog to English</option>
                </select>
            </div>
            <button id="translateButton">Translate</button>
            <div id="translationResult" style="margin-top: 20px; white-space: pre-wrap;"></div>
        </div>
    </div>

    <script>
        // JavaScript Functionality

        const recordButton = document.getElementById('recordButton');
        const status = document.getElementById('status');
        const transcriptionList = document.getElementById('transcriptionList');
        const searchBar = document.getElementById('searchBar');
        const downloadButton = document.getElementById('downloadButton');

        const editModal = document.getElementById('editModal');
        const closeModal = document.getElementById('closeModal');
        const editText = document.getElementById('editText');
        const saveEditButton = document.getElementById('saveEditButton');

        const translateModal = document.getElementById('translateModal');
        const closeTranslateModal = document.getElementById('closeTranslateModal');
        const translationDirection = document.getElementById('translationDirection');
        const translateButton = document.getElementById('translateButton');
        const translationResult = document.getElementById('translationResult');

        const colorBlindToggle = document.getElementById('colorBlindToggle');
        const body = document.body;

        let mediaRecorder;
        let audioChunks = [];
        let currentEditId = null;
        let currentTranslateId = null;

        // Initialize Color Blind Mode based on saved preference
        if (localStorage.getItem('colorBlindMode') === 'enabled') {
            colorBlindToggle.checked = true;
            body.classList.add('color-blind-mode');
        }

        // Check for browser support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('Your browser does not support audio recording.');
        }

        // Event Listeners
        recordButton.addEventListener('click', () => {
            if (recordButton.textContent === 'Record') {
                startRecording();
            } else {
                stopRecording();
            }
        });

        searchBar.addEventListener('input', fetchTranscriptions);
        downloadButton.addEventListener('click', downloadTranscriptions);

        // Edit Modal Event Listeners
        closeModal.addEventListener('click', () => {
            editModal.style.display = 'none';
        });

        saveEditButton.addEventListener('click', saveEdit);

        // Translate Modal Event Listeners
        closeTranslateModal.addEventListener('click', () => {
            translateModal.style.display = 'none';
            translationResult.textContent = '';
        });

        translateButton.addEventListener('click', translateTranscription);

        // Color Blind Mode Toggle Listener
        colorBlindToggle.addEventListener('change', () => {
            if (colorBlindToggle.checked) {
                body.classList.add('color-blind-mode');
                localStorage.setItem('colorBlindMode', 'enabled');
            } else {
                body.classList.remove('color-blind-mode');
                localStorage.setItem('colorBlindMode', 'disabled');
            }
        });

        // Keyboard accessibility for Record Button
        recordButton.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                recordButton.click();
            }
        });

        // Functions
        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    status.textContent = 'Recording...';
                    recordButton.textContent = 'Stop';
                    recordButton.classList.add('recording');

                    mediaRecorder.addEventListener("dataavailable", event => {
                        audioChunks.push(event.data);
                    });

                    mediaRecorder.addEventListener("stop", () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        uploadAudio(audioBlob);
                        audioChunks = [];
                        recordButton.classList.remove('recording');
                    });
                })
                .catch(error => {
                    console.error('Error accessing microphone:', error);
                    status.textContent = 'Microphone access denied.';
                });
        }

        function stopRecording() {
            mediaRecorder.stop();
            status.textContent = 'Processing...';
            recordButton.textContent = 'Record';
        }

        function uploadAudio(blob) {
            const formData = new FormData();
            formData.append('audio_data', blob, 'recording.wav');

            fetch('/transcribe', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.transcription) {
                    status.textContent = 'Transcription Complete.';
                    addTranscriptionToList(data.transcription);
                } else if (data.error) {
                    status.textContent = data.error;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                status.textContent = 'An error occurred during transcription.';
            });
        }

        function addTranscriptionToList(transcription) {
            fetchTranscriptions();
        }

        // Fetch Transcriptions with Optional Search
        function fetchTranscriptions() {
            const query = searchBar.value;
            let url = '/get_transcriptions';
            if (query) {
                url += '?search=' + encodeURIComponent(query);
            }

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    transcriptionList.innerHTML = '';
                    if (data.transcriptions) {
                        data.transcriptions.forEach(item => {
                            const li = document.createElement('li');
                            li.className = 'transcription-item';

                            const textDiv = document.createElement('div');
                            textDiv.className = 'transcription-text';
                            textDiv.innerHTML = `<strong>Original:</strong> ${item.transcription}`;

                            if (item.translated_text && item.translation_direction) {
                                let directionText = "";
                                if (item.translation_direction === 'en_to_tl') {
                                    directionText = "English to Tagalog";
                                } else if (item.translation_direction === 'tl_to_en') {
                                    directionText = "Tagalog to English";
                                }
                                textDiv.innerHTML += `<br><strong>Translated (${directionText}):</strong> ${item.translated_text}`;
                            }

                            const actionsDiv = document.createElement('div');
                            actionsDiv.className = 'transcription-actions';

                            // Text-to-Speech Button
                            const speakButton = document.createElement('button');
                            speakButton.textContent = 'Speak';
                            speakButton.style.marginRight = '5px';
                            speakButton.addEventListener('click', () => {
                                speakText(item.transcription);
                            });

                            // Translate Button
                            const translateButton = document.createElement('button');
                            translateButton.textContent = 'Translate';
                            translateButton.style.marginRight = '5px';
                            translateButton.addEventListener('click', () => {
                                openTranslateModal(item.id);
                            });

                            const editButton = document.createElement('button');
                            editButton.textContent = 'Edit';
                            editButton.addEventListener('click', () => {
                                openEditModal(item.id, item.transcription);
                            });

                            const deleteButton = document.createElement('button');
                            deleteButton.textContent = 'Delete';
                            deleteButton.addEventListener('click', () => {
                                deleteTranscription(item.id);
                            });

                            actionsDiv.appendChild(speakButton);
                            actionsDiv.appendChild(translateButton);
                            actionsDiv.appendChild(editButton);
                            actionsDiv.appendChild(deleteButton);

                            li.appendChild(textDiv);
                            li.appendChild(actionsDiv);
                            transcriptionList.appendChild(li);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching transcriptions:', error);
                });
        }

        // Delete Transcription
        function deleteTranscription(id) {
            if (!confirm('Are you sure you want to delete this transcription?')) return;

            fetch('/delete_transcription/' + id, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fetchTranscriptions();
                }
            })
            .catch(error => {
                console.error('Error deleting transcription:', error);
            });
        }

        // Open Edit Modal
        function openEditModal(id, currentText) {
            currentEditId = id;
            editText.value = currentText;
            editModal.style.display = 'block';
        }

        // Save Edited Transcription
        function saveEdit() {
            const newText = editText.value.trim();
            if (!newText) {
                alert('Transcription cannot be empty.');
                return;
            }

            fetch('/edit_transcription/' + currentEditId, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ transcription: newText })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    editModal.style.display = 'none';
                    fetchTranscriptions();
                } else if (data.error) {
                    alert(data.error);
                }
            })
            .catch(error => {
                console.error('Error editing transcription:', error);
            });
        }

        // Open Translate Modal
        function openTranslateModal(id) {
            currentTranslateId = id;
            translateModal.style.display = 'block';
            translationResult.textContent = '';
        }

        // Translate Transcription
        function translateTranscription() {
            const direction = translationDirection.value;

            fetch('/translate/' + currentTranslateId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ direction: direction })
            })
            .then(response => response.json())
            .then(data => {
                if (data.translated_text) {
                    const directionText = direction === 'en_to_tl' ? 'English to Tagalog' : 'Tagalog to English';
                    translationResult.innerHTML = `<strong>Translated (${directionText}):</strong> ${data.translated_text}`;
                    fetchTranscriptions();
                } else if (data.error) {
                    translationResult.textContent = data.error;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                translationResult.textContent = 'An error occurred during translation.';
            });
        }

        // Text-to-Speech Function
        function speakText(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                window.speechSynthesis.speak(utterance);
            } else {
                alert('Sorry, your browser does not support text-to-speech.');
            }
        }

        // Download Transcriptions
        function downloadTranscriptions() {
            window.location.href = '/download_transcriptions';
        }

        // Close Modal when clicking outside of it
        window.onclick = function(event) {
            if (event.target == editModal) {
                editModal.style.display = "none";
            }
            if (event.target == translateModal) {
                translateModal.style.display = "none";
                translationResult.textContent = '';
            }
        }

        // Fetch existing transcriptions on page load
        window.onload = fetchTranscriptions;
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
