"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import os

from recommender import load_songs, recommend_songs, Recommender

# Resolve paths relative to the project root (one level above src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAX_SCORE = Recommender.MAX_SCORE


# ---------------------------------------------------------------------------
# User taste profiles
# ---------------------------------------------------------------------------

USER_PROFILES = {
    "Pop Enthusiast": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.80,
        "likes_acoustic": False,
        "genre_preferences": {"pop": 1.0, "indie pop": 0.7, "electronic": 0.3},
        "target_acousticness": 0.20,
        "target_danceability": 0.82,
        "prefers_instrumental": False,
    },
    "Chill Lofi Coder": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.38,
        "likes_acoustic": True,
        "genre_preferences": {"lofi": 1.0, "jazz": 0.7, "ambient": 0.6},
        "target_acousticness": 0.80,
        "target_danceability": 0.55,
        "prefers_instrumental": True,
    },
    "Workout Warrior": {
        "genre": "electronic",
        "mood": "energetic",
        "energy": 0.90,
        "likes_acoustic": False,
        "genre_preferences": {"electronic": 1.0, "pop": 0.6, "metal": 0.5},
        "target_acousticness": 0.08,
        "target_danceability": 0.90,
        "prefers_instrumental": False,
    },
    "Acoustic Campfire": {
        "genre": "folk",
        "mood": "nostalgic",
        "energy": 0.45,
        "likes_acoustic": True,
        "genre_preferences": {"folk": 1.0, "jazz": 0.6, "classical": 0.5, "indie pop": 0.4},
        "target_acousticness": 0.90,
        "target_danceability": 0.45,
        "prefers_instrumental": False,
    },
    "Late-Night Hip Hop": {
        "genre": "hip hop",
        "mood": "dark",
        "energy": 0.68,
        "likes_acoustic": False,
        "genre_preferences": {"hip hop": 1.0, "r&b": 0.7, "synthwave": 0.4},
        "target_acousticness": 0.15,
        "target_danceability": 0.75,
        "prefers_instrumental": False,
    },
}


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_profile(name: str, prefs: dict) -> None:
    """Print a boxed profile header."""
    w = 60
    border = "+" + "-" * (w - 2) + "+"
    print(border)
    print(f"|  {name:^{w - 4}}  |")
    print(border)

    genre = prefs["genre"]
    mood = prefs["mood"]
    energy = prefs["energy"]
    print(f"|  Genre: {genre:<12} Mood: {mood:<12} Energy: {energy:<6}  |")

    if prefs.get("genre_preferences"):
        affinities = ", ".join(f"{g} ({v})" for g, v in
                               prefs["genre_preferences"].items())
        line = f"  Affinities: {affinities}"
        print(f"|{line:<{w - 2}}|")

    extras = []
    if prefs.get("target_acousticness") is not None:
        extras.append(f"acoustic={prefs['target_acousticness']}")
    if prefs.get("target_danceability") is not None:
        extras.append(f"dance={prefs['target_danceability']}")
    if prefs.get("prefers_instrumental") is not None:
        extras.append(f"instrumental={prefs['prefers_instrumental']}")
    if extras:
        line = f"  {', '.join(extras)}"
        print(f"|{line:<{w - 2}}|")

    print(border)


def print_recommendation(rank: int, song: dict, score: float,
                         reasons: list) -> None:
    """Print a single ranked recommendation with score bar and reasons."""
    title = song["title"]
    artist = song["artist"]
    genre = song["genre"]
    mood = song["mood"]

    print(f"  #{rank}  {title} -- {artist}")
    print(f"       {genre} / {mood}")
    print(f"       {score:.2f} / {MAX_SCORE:.1f} pts")
    print(f"       Reasons:")
    for reason in reasons:
        print(f"         + {reason}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs(os.path.join(_PROJECT_ROOT, "data", "songs.csv"))

    for profile_name, user_prefs in USER_PROFILES.items():
        print()
        print_profile(profile_name, user_prefs)
        print()

        recommendations = recommend_songs(user_prefs, songs, k=5)

        for rank, (song, score, reasons) in enumerate(recommendations, 1):
            print_recommendation(rank, song, score, reasons)

        print()


if __name__ == "__main__":
    main()
