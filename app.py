from flask import Flask, request, jsonify, send_from_directory, abort
import yt_dlp
import os
import threading
import time
import uuid
import logging
import subprocess

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

CLEANUP_DELAY = 600  # 10 minutes
downloaded_files = {}

def schedule_file_cleanup(filepath):
    def cleanup():
        time.sleep(CLEANUP_DELAY)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                app.logger.info(f"Deleted file: {filepath}")
        except Exception as e:
            app.logger.error(f"Error deleting file {filepath}: {e}")

    threading.Thread(target=cleanup, daemon=True).start()

@app.route('/api/video_info', methods=['POST'])
def video_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {'quiet': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        app.logger.error(f"Failed to extract info: {e}", exc_info=True)
        return jsonify({'error': f'Failed to extract info: {str(e)}'}), 500

    formats = [
        {
            'format_id': f['format_id'],
            'ext': f['ext'],
            'resolution': f.get('resolution'),
            'filesize': f.get('filesize'),
            'acodec': f.get('acodec'),
            'vcodec': f.get('vcodec')
        }
        for f in info['formats']
    ]

    return jsonify({
        'title': info.get('title'),
        'thumbnail': info.get('thumbnail'),
        'formats': formats
    })

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    url = data.get('url')
    format_id = data.get('format_id')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    unique_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}.%(ext)s')

    ydl_opts = {
        'format': format_id if format_id else 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        app.logger.error(f"Download failed: {e}", exc_info=True)
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

    ext = info.get('ext', 'mp4')
    filename = f"{unique_id}.{ext}"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        app.logger.error(f"Downloaded file not found: {filepath}")
        return jsonify({'error': 'Downloaded file not found'}), 500

    schedule_file_cleanup(filepath)
    downloaded_files[unique_id] = filepath

    download_url = f'/download/{filename}'

    return jsonify({'downloadUrl': download_url})

@app.route('/download/<path:filename>', methods=['GET'])
def serve_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(400)
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/ffmpeg_version')
def ffmpeg_version():
    try:
        version = subprocess.check_output(['ffmpeg', '-version']).decode('utf-8').split('\n')[0]
        return jsonify({'ffmpeg_version': version})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
