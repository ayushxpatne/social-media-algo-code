from flask import Flask, render_template, request, jsonify
import json
import pandas as pd

app = Flask(__name__)

# Load the JSON data
try:
    with open("comprehensive_algo/data.json", "r") as f:
        videos = json.load(f)
except FileNotFoundError:
    # Fallback dummy data if file is not found
    videos = {
        "video_0": {
            "category_combined": {
                "Education & Knowledge": ["science", "psychology", "finance"]
            },
            "interactions": {},
            "score": 0,
        },
        "video_1": {
            "category_combined": {
                "Trends & Modern Culture": ["gadgets"],
                "Inspiration & Personal Growth": ["productivity"],
            },
            "interactions": {},
            "score": 0,
        },
    }

interactions = {
    "view_time": {
        "skip": -1,
        "short": -0.5,
        "long": +1.5,
    },  # where skip = <2 seconds, short = 7 seconds or less, long is for more than 7 seconds
    "like": +1,
    "comment": +2,
    "share": +3,  # we can further classify it as{"private": +2, "public": +3} where private = posting to story, public = sharing it in the DMs, but for simplicity we are keeping one score.
    "save": +3,
    "rewatch_count": 0,
    # some other examples of interaction can be:
    # "follow": +5,
    # "dislike": -1,
    # "comment_like": +0.5,
    # "comment_reply": +1
    # "comment_sentiment"
}

history = {}


@app.route("/")
def index():
    # Pass the entire videos dictionary and the user's history to the template
    return render_template(
        "index.html", videos=videos, total_videos=len(videos), history=history
    )


# app.py


@app.route("/interact/<video_id>/<interaction>/<state>", methods=["POST"])
def interact(video_id, interaction, state):
    print(f"Video: {video_id}, Interaction: {interaction}, State: {state}")

    # Ensure the video and interaction are in the history dictionary
    if video_id not in history.keys():
        history.setdefault(
            video_id,
            {
                "category_combined": videos[video_id]["category_combined"],
                "interactions": {},
                "score": 0,
                "view_duration": 0,
            },
        )

    # Update the interactions based on the state
    if state == "true":
        if interaction == "like":
            history[video_id]["interactions"]["like"] = interactions["like"]
        elif interaction == "comment":
            history[video_id]["interactions"]["comment"] = interactions["comment"]
        elif interaction == "share":
            history[video_id]["interactions"]["share"] = interactions["share"]
        elif interaction == "save":
            history[video_id]["interactions"]["save"] = interactions["save"]
    elif state == "false":
        if interaction in history[video_id]["interactions"]:
            del history[video_id]["interactions"][interaction]

    # print("Updated History:", history)

    # Return a JSON response
    return jsonify(
        {
            "status": "success",
            "message": f"Interaction {interaction} for video {video_id} updated to {state}.",
        }
    )


@app.route("/record_duration/<video_id>", methods=["POST"])
def record_duration(video_id):
    try:
        data = request.get_json()
        duration_ms = data.get("duration")

        duration_seconds = duration_ms / 1000
        if video_id not in history.keys():
            history.setdefault(
                video_id,
                {
                    "category_combined": videos[video_id]["category_combined"],
                    "interactions": {},
                    "score": 0,
                    "view_duration": 0,
                },
            )

        history[video_id]["view_duration"] += duration_seconds
        history[video_id]["interactions"]["rewatch_count"] = get_rewatch_count(
            duration_seconds=duration_seconds
        )
        history[video_id]["interactions"]["view_time"] = get_view_time(
            duration_seconds=duration_seconds
        )

        calculate_score(video_id=video_id)

        # print(history)
        pd.DataFrame(history).to_json("history.json")
        return jsonify(
            {"status": "success", "message": f"Duration for video {video_id} recorded."}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def get_view_time(duration_seconds):

    if duration_seconds < 2:
        return interactions["view_time"]["skip"]
    if duration_seconds <= 7:
        return interactions["view_time"]["short"]
    elif duration_seconds > 7:
        return interactions["view_time"]["long"]


def get_rewatch_count(duration_seconds):
    max_video_len = 15  # seconds
    return round(duration_seconds / max_video_len)


def calculate_score(video_id):
    interactions_dict = history[video_id]["interactions"]
    print(interactions_dict.keys())
    score = 0
    for key, value in interactions_dict.items():
        # we are simply gonna add the scores based on interactions, we can make it this more complex but lets keep it simple
        score += value
    history[video_id]["score"] = score


if __name__ == "__main__":
    app.run(debug=True)
