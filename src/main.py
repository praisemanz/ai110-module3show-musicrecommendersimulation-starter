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
# Standard profiles — clear, coherent preferences
# ---------------------------------------------------------------------------

STANDARD_PROFILES = {
    "High-Energy Pop": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.85,
        "likes_acoustic": False,
        "genre_preferences": {"pop": 1.0, "indie pop": 0.7, "electronic": 0.3},
        "target_acousticness": 0.15,
        "target_danceability": 0.85,
        "prefers_instrumental": False,
    },
    "Chill Lofi": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.38,
        "likes_acoustic": True,
        "genre_preferences": {"lofi": 1.0, "jazz": 0.7, "ambient": 0.6},
        "target_acousticness": 0.80,
        "target_danceability": 0.55,
        "prefers_instrumental": True,
    },
    "Deep Intense Rock": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.92,
        "likes_acoustic": False,
        "genre_preferences": {"rock": 1.0, "metal": 0.8, "synthwave": 0.3},
        "target_acousticness": 0.10,
        "target_danceability": 0.65,
        "prefers_instrumental": False,
    },
}

# ---------------------------------------------------------------------------
# Adversarial / edge-case profiles — designed to stress-test the scoring
# ---------------------------------------------------------------------------

EDGE_CASE_PROFILES = {
    "EDGE: High-Energy Sad": {
        # Conflict: energy 0.95 wants intense bangers, but melancholy mood
        # wants slow, sad songs. No song in the catalog is both.
        "genre": "classical",
        "mood": "melancholy",
        "energy": 0.95,
        "likes_acoustic": True,
        "genre_preferences": {"classical": 1.0, "ambient": 0.5},
        "target_acousticness": 0.90,
        "target_danceability": 0.25,
        "prefers_instrumental": True,
    },
    "EDGE: Ghost Genre": {
        # The genre "reggae" does not exist in the catalog at all.
        # No song will earn genre points. Tests graceful degradation.
        "genre": "reggae",
        "mood": "happy",
        "energy": 0.70,
        "likes_acoustic": False,
        "genre_preferences": {"reggae": 1.0},
        "target_acousticness": 0.30,
        "target_danceability": 0.80,
        "prefers_instrumental": False,
    },
    "EDGE: Acoustic Electronic": {
        # Contradiction: wants electronic genre but high acousticness.
        # Electronic songs have near-zero acousticness in the dataset.
        "genre": "electronic",
        "mood": "dreamy",
        "energy": 0.50,
        "likes_acoustic": True,
        "genre_preferences": {"electronic": 1.0, "ambient": 0.6},
        "target_acousticness": 0.90,
        "target_danceability": 0.40,
        "prefers_instrumental": True,
    },
    "EDGE: The Middleground": {
        # All numeric targets at 0.5, no genre preferences dict.
        # Tests what happens when the user has zero strong opinions.
        "genre": "pop",
        "mood": "chill",
        "energy": 0.50,
        "likes_acoustic": False,
        "target_acousticness": 0.50,
        "target_danceability": 0.50,
        "prefers_instrumental": None,
    },
}

USER_PROFILES = {**STANDARD_PROFILES, **EDGE_CASE_PROFILES}


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

def run_profiles(label: str, profiles: dict, songs: list) -> None:
    """Run a group of profiles and print results."""
    print()
    print(f"{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    for profile_name, user_prefs in profiles.items():
        print()
        print_profile(profile_name, user_prefs)
        print()

        recommendations = recommend_songs(user_prefs, songs, k=5)

        for rank, (song, score, reasons) in enumerate(recommendations, 1):
            print_recommendation(rank, song, score, reasons)


def main() -> None:
    songs = load_songs(os.path.join(_PROJECT_ROOT, "data", "songs.csv"))

    run_profiles("STANDARD PROFILES", STANDARD_PROFILES, songs)
    run_profiles("ADVERSARIAL / EDGE-CASE PROFILES", EDGE_CASE_PROFILES, songs)


if __name__ == "__main__":
    main()
