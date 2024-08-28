from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit
import os
import subprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def transcode_video(filepath, output_folder):
    resolutions = ['720p', '1080p', '1440p', '2160p']  # 720p, 1080p, 2K, 4K
    output_files = []

    for resolution in resolutions:
        output_file = os.path.join(output_folder, f"{resolution}_{os.path.basename(filepath)}")
        ffmpeg_command = [
            'ffmpeg', '-i', filepath, '-vf', f'scale=-2:{resolution[:-1]}',
            '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast', '-c:a', 'aac',
            '-strict', 'experimental', output_file
        ]
        subprocess.run(ffmpeg_command)
        output_files.append(output_file)

    return output_files

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            transcode_video(filepath, app.config['UPLOAD_FOLDER'])
            return redirect(url_for('watch', filename=file.filename))
    return render_template('index.html')

@app.route('/watch/<filename>')
def watch(filename):
    return render_template('watch.html', filename=filename)

@app.route('/uploads/<resolution>_<filename>')
def uploads(resolution, filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], f"{resolution}_{filename}")

@socketio.on('sync')
def sync(data):
    emit('sync', data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, debug=True)
