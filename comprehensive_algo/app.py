from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Load the JSON data
try:
    with open('data.json', 'r') as f:
        videos = json.load(f)
except FileNotFoundError:
    # Fallback dummy data if file is not found
    videos = {
        "video_0": {
            "category_combined": {
                "Education & Knowledge": ["science", "psychology", "finance"]
            },
            "interactions": {},
            "score": 0
        },
        "video_1": {
            "category_combined": {
                "Trends & Modern Culture": ["gadgets"],
                "Inspiration & Personal Growth": ["productivity"]
            },
            "interactions": {},
            "score": 0
        }
    }

print(videos)

@app.route("/")
def index():
    # Pass the entire videos dictionary to the template
    return render_template("index.html",
                         videos=videos,
                         total_videos=len(videos))

@app.route("/interact/<video_id>/<interaction>", methods=["POST"])
def interact(video_id, interaction):
    print(f"Video: {video_id}, Interaction: {interaction}")
    
    # Process the interaction. You can add your logic here,
    # for example, updating the score or saving the interaction to a database.
    # We will simply print to the console for this example.

    # Return a JSON response instead of a redirect
    return jsonify({'status': 'success', 'message': f'Interaction {interaction} for video {video_id} recorded.'})

@app.route("/record_duration/<video_id>", methods=["POST"])
def record_duration(video_id):
    try:
        data = request.get_json()
        duration_ms = data.get('duration')
        
        duration_seconds = duration_ms / 1000
        
        print(f"Video {video_id} was on screen for {duration_seconds:.2f} seconds ({duration_ms:.2f} milliseconds).")

        # You can add logic here to save the duration to a database,
        # update the video object in your dictionary, etc.
        # For example: videos[video_id]['interactions']['time_on_screen'] = duration_ms

        return jsonify({'status': 'success', 'message': f'Duration for video {video_id} recorded.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)