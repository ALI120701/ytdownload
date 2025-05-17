from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/api/video_info', methods=['POST'])
def video_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = [
        {
            'format_id': f['format_id'],
            'ext': f['ext'],
            'resolution': f.get('resolution'),
            'filesize': f.get('filesize'),
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
    url = data.get('url')
    format_id = data.get('format_id')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {
        'quiet': True,
        'format': format_id if format_id else 'best',
        'noplaylist': True,
        'skip_download': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    selected_format = None
    if format_id:
        for f in info['formats']:
            if f['format_id'] == format_id:
                selected_format = f
                break
    else:
        selected_format = info['formats'][-1]

    if not selected_format or 'url' not in selected_format:
        return jsonify({'error': 'Format URL not found'}), 404

    download_url = selected_format['url']

    return jsonify({'downloadUrl': download_url})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
