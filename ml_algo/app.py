from flask import Flask, render_template, request, jsonify
import json
import pandas as pd
import faiss
import random
import numpy as np

app = Flask(__name__)


interactions = {
    "view_time": {
        "skip": 0.01,
        "short": 0.25,
        "long": +1.5,
    },  # where skip = <2 seconds, short = 7 seconds or less, long is for more than 7 seconds
    "like": +2,
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
all_videos = {}
feed = []
faiss_index = None
user_embedding = None

# Batch updates every N interactions
interaction_counter = 0


def get_all_videos():
    # say all videos is the database
    # in real world, this can be sql / postgres
    global all_videos, feed
    # Load the JSON data
    try:
        with open("ml_algo/data2.json", "r") as f:
            all_videos = json.load(f)
    except FileNotFoundError:
        # all_videos dummy data if file is not found
        all_videos = {
            "video_0": {
                "description": "This video is about xyz.",
                "categories": [],
                "sub_categories": [],
                "embeddings": [],
            },
            "video_1": {
                "description": "This video is about pqr",
                "categories": [],
                "sub_categories": [],
                "embeddings": [],
            },
        }


def get_faiss_index():
    global faiss_index
    faiss_index = faiss.read_index("ml_algo/index.faiss")


def initialize():
    get_faiss_index()
    get_all_videos()


def initialize_v2():
    get_faiss_index_v2()
    get_all_videos()


def init_feed():
    # cold start
    # picking first 10 random vidoes if feed is empty, we are assuming user is new
    if feed.__len__() == 0:
        for i in range(10):
            rand_vid_id = list(all_videos.keys())[
                random.randint(
                    0, all_videos.__len__() - 1
                )  # FIXED: was causing IndexError
            ]
            feed_data = [rand_vid_id]
            for i in list(all_videos[rand_vid_id].values()):
                feed_data.append(i)
            feed.append(feed_data)


@app.route("/")
def index():
    # initialize()
    initialize_v2()
    init_feed()
    # Pass the entire videos dictionary and the user's history to the template
    return render_template(
        "index.html", videos=feed, total_videos=len(feed), history=history
    )


# app.py


@app.route("/interact/<video_id>/<interaction>/<state>", methods=["POST"])
def interact(video_id, interaction, state):
    print(f"Video: {video_id}, Interaction: {interaction}, State: {state}")

    # # Ensure the video and interaction are in the history dictionary
    if video_id not in history.keys():
        history.setdefault(
            video_id,
            {
                "embeddings": all_videos[video_id]["embeddings"],
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
                    "embeddings": all_videos[video_id]["embeddings"],
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
        global interaction_counter

        interaction_counter += 1
        if interaction_counter % 5 == 0:  # Update every 5 videos
            update_user_embedding_simple_v2()
        print("Duration recorded")
        return jsonify(
            {"status": "success", "message": f"Duration for video {video_id} recorded."}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# this version stops recommending videos after 20-21 videos, it just makes the search returns 0 videos after that.
# lets try make this version better, check update_user_embedding_simple_v2
def update_user_embedding_simple():
    # i am pretty sure this feels illegal, this all can be done in better way if used database.
    global user_embedding

    if len(history) == 0:
        return

    history_df = pd.DataFrame(history).T
    embedding_matrix = []
    weights = []
    for row in history_df.itertuples():
        embedding_matrix.append(row.embeddings)
        weights.append(int(row.score) + 1)

    print(weights)

    # weighted mean of weights:
    weights = np.array(weights) / np.sum(weights)

    # FIXED: reshape for FAISS (needs 2D array)
    user_embedding_1d = np.average(np.array(embedding_matrix), axis=0, weights=weights)
    user_embedding = user_embedding_1d.reshape(1, -1).astype("float32")
    print("user_embedding updated")


# in this we are gonna introduce a filter to only use videos where score is > 2:
# say user watched the video once = 1 point, (refer dictionary on top) => the user also watched entire video: +1.5 points
def update_user_embedding_simple_v2():
    global user_embedding

    if len(history) == 0:
        return

    history_df = pd.DataFrame(history).T
    embedding_matrix = []
    weights = []
    # after adding the repalce already shown video with random video logic,
    # keep only the last 5 videos with score >= 2
    # ie implementing sliding window: only keep the last N videos (N=5 here)
    filtered_df = history_df[history_df["score"] >= 2].tail(5)

    for row in filtered_df.itertuples():
        embedding_matrix.append(row.embeddings)
        weights.append(int(row.score) + 1)

    print(weights)

    # weighted mean of weights:
    weights = np.array(weights) / np.sum(weights)

    #  reshape for FAISS (needs 2D array)
    user_embedding_1d = np.average(np.array(embedding_matrix), axis=0, weights=weights)
    user_embedding = user_embedding_1d.reshape(1, -1).astype("float32")
    print("user_embedding updated")

# using the new index:
def get_faiss_index_v2():
    global faiss_index
    faiss_index = faiss.read_index("ml_algo/index_v2.faiss")


# @app.route("/fetch_more", methods=["GET"])
def fetch_more_videos():
    try:
        global all_videos, feed
        new_videos = []

        # FIXED: Changed condition from == len(feed)/2 to >= 3
        if len(history.keys()) >= 3 and user_embedding is not None:
            dist, similar_item_index = faiss_index.search(user_embedding, 10)
            video_keys = list(all_videos.keys())

            for i in similar_item_index[0]:
                # FIXED: Check if index is valid
                if i >= len(video_keys):
                    continue

                rand_vid_id = video_keys[i]

                # Skip if video already in feed
                if any(rand_vid_id == video[0] for video in feed):
                    continue

                feed_data = [rand_vid_id]

                for val in list(all_videos[rand_vid_id].values()):
                    feed_data.append(val)

                feed.append(feed_data)
                new_videos.append(
                    {
                        "video_id": feed_data[0],
                        "description": feed_data[3] if len(feed_data) > 3 else "",
                    }
                )

        else:
            # Cold start: return random videos if not enough history
            print("Not enough history yet, returning random videos")
            video_keys = list(all_videos.keys())
            for _ in range(min(5, len(video_keys))):
                rand_vid_id = video_keys[random.randint(0, len(video_keys) - 1)]

                # Skip if already in feed
                if any(rand_vid_id == video[0] for video in feed):
                    continue

                feed_data = [rand_vid_id]
                for val in list(all_videos[rand_vid_id].values()):
                    feed_data.append(val)

                feed.append(feed_data)
                new_videos.append(
                    {
                        "video_id": feed_data[0],
                        "description": feed_data[3] if len(feed_data) > 3 else "",
                    }
                )

        print(f"Returning {len(new_videos)} new videos")
        # Always return a list, not a dict
        return jsonify(new_videos)

    except Exception as e:
        print("Error in /fetch_more:", e)
        import traceback

        traceback.print_exc()
        return jsonify([]), 500  # return an empty list instead of an object


@app.route("/fetch_more", methods=["GET"])
def fetch_more_videos_v2():
    try:
        global all_videos, feed
        new_videos = []

        # FIXED: Changed condition from == len(feed)/2 to >= 3
        if user_embedding is not None:
            faiss_index.nprobe = 5
            # dist, similar_item_index = faiss_index.search(user_embedding, 10)

            # after implementing sliding window, while browsing i noticed if all the similar items were not shown before
            # all 10 videos seem to be consecutive of same topic, which can bore the user.
            # so i am thinking of adding a bit of variation even when all similar items are new to user
            # so 70% will be new videos and 30% will be the random ones.

            # we are gonne find 7 videos compared to 10 in dist, similar_item_index = faiss_index.search(user_embedding, 10)
            dist, similar_item_index = faiss_index.search(user_embedding, 7)

            print(
                f"Distances = {dist}\nIndices of Them in Index/DB = {similar_item_index}"
            )
            video_keys = list(all_videos.keys())

            # if similar_item_index.__len__() == 0 :
            #     print(f"Returning random videos cos similar_item_index = 0")
            #     new_videos = get_random_videos()

            for i in similar_item_index[0]:
                # FIXED: Check if index is valid
                if i >= len(video_keys):
                    continue

                rand_vid_id = video_keys[i]

                # Skip if video already in feed
                if any(rand_vid_id == video[0] for video in feed):
                    print(f"{rand_vid_id} already shown, showing random video instead")
                    # continue
                    # pick any random video
                    rand_vid_id = video_keys[random.randint(0, len(video_keys) - 1)]
                # ABOUT THE FEED STOPPING AFTER 20ish videos, is because of this.
                # at first i thought maybe its because we not finding similar videos. we are, but they were already shown
                # to the user. hence it returns 0 videos
                # so if all the found videos are already in feed, we need to show random video
                # this is done in : if new_videos.__len__() == 0: block of this code
                # one other thing i would like to do is, instead of skipping the video which is already shown, i want to
                # instead show a random video, this will serve 2 purposes:
                # 1. if there are many similar videos lined up, it may get repetetive for user, so we can break the repetion
                # 2. this will allow us to serve 10 videos, fulfilling the batch size condition.
                # this made the feed much better
                # now to mimic time decay, that is priorotise recent preferences, i am also gonna add sliding window to history
                # the better way to do this is to input time decay / stamp as weight but since we are not recording timestamps
                # slidng window is the easier solution for this.

                feed_data = [rand_vid_id]

                for val in list(all_videos[rand_vid_id].values()):
                    feed_data.append(val)

                feed.append(feed_data)
                new_videos.append(
                    {
                        "video_id": feed_data[0],
                        "description": feed_data[3] if len(feed_data) > 3 else "",
                    }
                )
            print(f"Returning {len(new_videos)} new similar videos")

            # and for remaining 3 videos we are gonna pick random 3
            for i in range(3):

                vid_for_variation_id = video_keys[random.randint(0, len(video_keys) - 1)]
                temp = [
                    vid_for_variation_id,
                ]
                for val in list(all_videos[vid_for_variation_id].values()):
                    temp.append(val)

                feed.append(temp)
                new_videos.append(
                    {
                        "video_id": temp[0],
                        "description": temp[3] if len(temp) > 3 else "",
                    }
                )
                print(f"Returning {len(new_videos)} new random video for variation")

        else:
            # Cold start: return random videos if not enough history
            print("Not enough history yet, returning random videos")
            new_videos = get_random_videos()

            print(f"Returning {len(new_videos)} new videos")

        if new_videos.__len__() == 0:
            new_videos = get_random_videos()
            print("All similar videos shown, returning random videos")

        # now that we have add variation, 70 similar - 30 random, we need to shuffle the list to make it seem more random ordered
        random.shuffle(new_videos)
        return jsonify(new_videos)

    except Exception as e:
        print("Error in /fetch_more:", e)
        import traceback

        traceback.print_exc()
        return jsonify([]), 500  # return an empty list instead of an object


def get_random_videos():
    video_keys = list(all_videos.keys())
    rand_vid = []
    for _ in range(min(5, len(video_keys))):
        rand_vid_id = video_keys[random.randint(0, len(video_keys) - 1)]

        # Skip if already in feed
        if any(rand_vid_id == video[0] for video in feed):
            continue

        feed_data = [rand_vid_id]
        for val in list(all_videos[rand_vid_id].values()):
            feed_data.append(val)

        feed.append(feed_data)
        rand_vid.append(
            {
                "video_id": feed_data[0],
                "description": feed_data[3] if len(feed_data) > 3 else "",
            }
        )

    print(f"Returning {len(rand_vid)} new videos")
    return rand_vid
    # Always return a list, not a dict


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
