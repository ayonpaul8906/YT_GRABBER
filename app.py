import os
import yt_dlp
import re
import time
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

DOWNLOADS_DIR = "static/downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)  # Ensure the downloads folder exists

def sanitize_filename(title):
    """Remove invalid characters for safe filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", title)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    video_url = data.get("video_url")

    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    try:
        # Extract video metadata
        ydl_opts_info = {
            "quiet": True,
            "geo_bypass": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = sanitize_filename(info.get("title", "video"))

        # Prepare filenames
        video_filename = f"{video_title}.mp4"
        audio_filename = f"{video_title}.m4a"
        final_filename = f"{video_title}_final.mp4"

        video_path = os.path.join(DOWNLOADS_DIR, video_filename)
        audio_path = os.path.join(DOWNLOADS_DIR, audio_filename)
        final_path = os.path.join(DOWNLOADS_DIR, final_filename)

        # Download video
        video_opts = {
            "format": "bv*[ext=mp4]",
            "outtmpl": video_path,
            "quiet": True,
            "geo_bypass": True,
        }
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([video_url])

        # Download audio
        audio_opts = {
            "format": "ba[ext=m4a]",
            "outtmpl": audio_path,
            "quiet": True,
            "geo_bypass": True,
        }
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([video_url])

        # Merge video + audio using ffmpeg
        merge_command = f'ffmpeg -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{final_path}" -y -loglevel error'
        os.system(merge_command)

        print(f"[INFO] Video merged and saved as: {final_filename}")

        return jsonify({
            "download_url": f"/download_file/{final_filename}",
            "video_title": video_title
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/download_file/<filename>")
def download_file(filename):
    final_path = os.path.join(DOWNLOADS_DIR, filename)

    if not os.path.exists(final_path):
        return jsonify({"error": "File not found"}), 404

    # Derive the intermediate filenames
    video_filename = filename.replace("_final.mp4", ".mp4")
    audio_filename = filename.replace("_final.mp4", ".m4a")
    video_path = os.path.join(DOWNLOADS_DIR, video_filename)
    audio_path = os.path.join(DOWNLOADS_DIR, audio_filename)

    # Delete all related files after 10 seconds
    def delete_files():
        time.sleep(10)
        for file_path in [final_path, video_path, audio_path]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"[CLEANUP] Deleted: {file_path}")
            except Exception as e:
                print(f"[CLEANUP ERROR] Could not delete {file_path}: {e}")

    threading.Thread(target=delete_files, daemon=True).start()

    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
