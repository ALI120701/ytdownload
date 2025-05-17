@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id')  # Optional: specify format

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {
        'quiet': True,
        'format': format_id if format_id else 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',  # Optional: local path
        'noplaylist': True,
        'skip_download': True  # Change to False if you want to download on server
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # Example: Return direct video URL for streaming or downloading
    # Usually, info['formats'] contains URLs for each format
    # Pick the requested format or best format URL

    selected_format = None
    if format_id:
        for f in info['formats']:
            if f['format_id'] == format_id:
                selected_format = f
                break
    else:
        selected_format = info['formats'][-1]  # last format as fallback

    if not selected_format or 'url' not in selected_format:
        return jsonify({'error': 'Format URL not found'}), 404

    download_url = selected_format['url']

    return jsonify({'downloadUrl': download_url})
