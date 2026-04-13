"""
Command line runner for the Music Recommender Simulation.
Demonstrates all four challenges: advanced features, scoring modes,
diversity penalty, and visual summary tables.
"""

import os

from recommender import load_songs, recommend_songs, Recommender, SCORING_MODES

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# User taste profiles (using all new features)
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
        "min_popularity": 60,
        "preferred_decade": "2020s",
        "preferred_mood_tags": ["euphoric", "anthemic"],
        "target_liveness": 0.15,
        "preferred_vocal": "mixed",
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
        "min_popularity": 30,
        "preferred_decade": "2020s",
        "preferred_mood_tags": ["atmospheric", "soothing", "minimal"],
        "target_liveness": 0.05,
        "preferred_vocal": "none",
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
        "min_popularity": 50,
        "preferred_decade": "2010s",
        "preferred_mood_tags": ["aggressive", "powerful"],
        "target_liveness": 0.35,
        "preferred_vocal": "male",
    },
}

EDGE_CASE_PROFILES = {
    "EDGE: High-Energy Sad": {
        "genre": "classical",
        "mood": "melancholy",
        "energy": 0.95,
        "likes_acoustic": True,
        "genre_preferences": {"classical": 1.0, "ambient": 0.5},
        "target_acousticness": 0.90,
        "target_danceability": 0.25,
        "prefers_instrumental": True,
        "min_popularity": 20,
        "preferred_decade": "1990s",
        "preferred_mood_tags": ["bittersweet", "ethereal"],
        "target_liveness": 0.05,
        "preferred_vocal": "none",
    },
    "EDGE: Ghost Genre": {
        "genre": "reggae",
        "mood": "happy",
        "energy": 0.70,
        "likes_acoustic": False,
        "genre_preferences": {"reggae": 1.0},
        "target_acousticness": 0.30,
        "target_danceability": 0.80,
        "prefers_instrumental": False,
        "min_popularity": 60,
        "preferred_decade": "2020s",
        "preferred_mood_tags": ["warm", "euphoric"],
        "target_liveness": 0.20,
        "preferred_vocal": "male",
    },
}

USER_PROFILES = {**STANDARD_PROFILES, **EDGE_CASE_PROFILES}


# ---------------------------------------------------------------------------
# Challenge 4: Visual summary table (ASCII, no external dependencies)
# ---------------------------------------------------------------------------

def format_table(headers: list, rows: list, col_widths: list) -> str:
    """Build an ASCII table string from headers and rows."""
    lines = []
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    lines.append(sep)

    header_line = "|"
    for h, w in zip(headers, col_widths):
        header_line += f" {h:<{w}} |"
    lines.append(header_line)
    lines.append(sep)

    for row in rows:
        line = "|"
        for val, w in zip(row, col_widths):
            line += f" {str(val):<{w}} |"
        lines.append(line)

    lines.append(sep)
    return "\n".join(lines)


def reasons_summary(reasons: list, max_reasons: int = 3) -> str:
    """Compact the top N reasons into a short string."""
    top = reasons[:max_reasons]
    return "; ".join(top)


def print_profile_header(name: str, prefs: dict, mode: str) -> None:
    """Print a compact profile header."""
    print(f"\n  Profile: {name}  [mode: {mode}]")
    parts = [f"genre={prefs['genre']}", f"mood={prefs['mood']}",
             f"energy={prefs['energy']}"]
    if prefs.get("preferred_decade"):
        parts.append(f"decade={prefs['preferred_decade']}")
    if prefs.get("min_popularity"):
        parts.append(f"min_pop={prefs['min_popularity']}")
    if prefs.get("preferred_mood_tags"):
        parts.append(f"tags={','.join(prefs['preferred_mood_tags'][:3])}")
    print(f"  {', '.join(parts)}")


def print_results_table(recommendations: list, max_score: float,
                        diversity: bool = False) -> None:
    """Print recommendations as a formatted ASCII table."""
    headers = ["#", "Title", "Artist", "Genre", "Score", "Top Reasons"]
    widths = [2, 22, 16, 11, 10, 48]
    rows = []
    for rank, (song, score, reasons) in enumerate(recommendations, 1):
        pct = f"{score:.2f}/{max_score:.1f}"
        short_reasons = reasons_summary(reasons)
        rows.append([
            rank,
            song["title"][:22],
            song["artist"][:16],
            song["genre"][:11],
            pct,
            short_reasons[:48],
        ])

    label = " (diversity ON)" if diversity else ""
    print(f"\n  Top {len(recommendations)} Recommendations{label}:\n")
    for line in format_table(headers, rows, widths).split("\n"):
        print(f"  {line}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_profile(name: str, prefs: dict, songs: list, mode: str = "balanced",
                diversity: bool = False) -> None:
    """Run a single profile and print the table."""
    prefs_with_mode = {**prefs, "mode": mode}
    max_score = sum(SCORING_MODES[mode].values())

    print_profile_header(name, prefs, mode)
    recommendations = recommend_songs(prefs_with_mode, songs, k=5,
                                      diversity=diversity)
    print_results_table(recommendations, max_score, diversity)


def main() -> None:
    songs = load_songs(os.path.join(_PROJECT_ROOT, "data", "songs.csv"))

    # --- Standard profiles in balanced mode ---
    print("=" * 70)
    print("  STANDARD PROFILES (balanced mode)")
    print("=" * 70)
    for name, prefs in STANDARD_PROFILES.items():
        run_profile(name, prefs, songs, mode="balanced")

    # --- Edge cases in balanced mode ---
    print("\n" + "=" * 70)
    print("  EDGE-CASE PROFILES (balanced mode)")
    print("=" * 70)
    for name, prefs in EDGE_CASE_PROFILES.items():
        run_profile(name, prefs, songs, mode="balanced")

    # --- Challenge 2: Scoring mode comparison ---
    print("\n" + "=" * 70)
    print("  SCORING MODE COMPARISON (High-Energy Pop across all modes)")
    print("=" * 70)
    pop_prefs = STANDARD_PROFILES["High-Energy Pop"]
    for mode in SCORING_MODES:
        run_profile("High-Energy Pop", pop_prefs, songs, mode=mode)

    # --- Challenge 3: Diversity penalty demo ---
    print("\n" + "=" * 70)
    print("  DIVERSITY PENALTY DEMO (Chill Lofi: OFF vs ON)")
    print("=" * 70)
    lofi_prefs = STANDARD_PROFILES["Chill Lofi"]
    run_profile("Chill Lofi", lofi_prefs, songs, mode="balanced",
                diversity=False)
    run_profile("Chill Lofi", lofi_prefs, songs, mode="balanced",
                diversity=True)


if __name__ == "__main__":
    main()
