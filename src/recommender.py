from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import csv


# ---------------------------------------------------------------------------
# Mood similarity map
# Each mood maps to related moods with a similarity weight (0.0–1.0).
# An exact match always scores 1.0; these handle partial credit.
# ---------------------------------------------------------------------------
MOOD_SIMILARITY: Dict[str, Dict[str, float]] = {
    "happy":      {"uplifting": 0.8, "energetic": 0.6, "romantic": 0.5, "relaxed": 0.3},
    "chill":      {"relaxed": 0.8, "dreamy": 0.7, "focused": 0.6, "nostalgic": 0.4, "moody": 0.3},
    "intense":    {"aggressive": 0.8, "energetic": 0.7, "dark": 0.4},
    "relaxed":    {"chill": 0.8, "dreamy": 0.6, "nostalgic": 0.5, "focused": 0.4},
    "moody":      {"dark": 0.7, "dreamy": 0.6, "melancholy": 0.6, "nostalgic": 0.5},
    "focused":    {"chill": 0.6, "relaxed": 0.4, "dreamy": 0.3},
    "romantic":   {"dreamy": 0.7, "happy": 0.5, "nostalgic": 0.4, "relaxed": 0.3},
    "aggressive": {"intense": 0.8, "dark": 0.6, "energetic": 0.5},
    "nostalgic":  {"melancholy": 0.7, "dreamy": 0.6, "moody": 0.5, "relaxed": 0.4},
    "energetic":  {"intense": 0.7, "happy": 0.6, "uplifting": 0.7, "aggressive": 0.4},
    "dreamy":     {"chill": 0.7, "romantic": 0.7, "relaxed": 0.6, "moody": 0.5},
    "uplifting":  {"happy": 0.8, "energetic": 0.7, "romantic": 0.4},
    "melancholy": {"nostalgic": 0.7, "moody": 0.6, "dark": 0.5, "dreamy": 0.4},
    "dark":       {"moody": 0.7, "melancholy": 0.6, "aggressive": 0.5, "intense": 0.3},
}


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    instrumentalness: float = 0.0
    speechiness: float = 0.0


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    Core fields (positional — backwards-compatible with existing tests):
        favorite_genre, favorite_mood, target_energy, likes_acoustic

    Extended fields (keyword-only, optional):
        genre_preferences  — dict mapping genres to 0.0–1.0 affinity weights
        target_acousticness — float target replacing the boolean when set
        target_danceability — float target for danceability proximity
        prefers_instrumental — boolean for vocal vs. instrumental preference
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    genre_preferences: Optional[Dict[str, float]] = None
    target_acousticness: Optional[float] = None
    target_danceability: Optional[float] = None
    prefers_instrumental: Optional[bool] = None


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py

    Point budget (additive scoring):
        Genre match        +2.00  (categorical — exact or preference-weighted)
        Mood match         +1.00  (categorical — exact or similarity-weighted)
        Energy proximity   +1.50  (continuous  — 1 - |diff|²)
        Acousticness fit   +0.75  (continuous  — proximity or directional)
        Danceability fit   +0.50  (continuous  — proximity, optional)
        Instrumentalness   +0.25  (directional — boolean, optional)
        ─────────────────────────
        Maximum possible    6.00
    """

    GENRE_POINTS = 2.0
    MOOD_POINTS = 1.0
    ENERGY_POINTS = 1.5
    ACOUSTIC_POINTS = 0.75
    DANCE_POINTS = 0.5
    INSTRUMENTAL_POINTS = 0.25
    MAX_SCORE = 6.0

    def __init__(self, songs: List[Song]):
        self.songs = songs

    # --- Per-feature scoring helpers ----------------------------------------
    # Each helper returns (points, reason_string).  When the feature does
    # not contribute, reason is "" so the caller can filter it out.

    def _score_genre(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Exact match = full points. Genre preferences dict = scaled points."""
        if user.genre_preferences:
            pts = user.genre_preferences.get(song.genre, 0.0) * self.GENRE_POINTS
        else:
            pts = self.GENRE_POINTS if song.genre == user.favorite_genre else 0.0

        if pts == self.GENRE_POINTS:
            reason = f"genre match ({song.genre}) +{pts:.2f}"
        elif pts > 0:
            reason = f"similar genre ({song.genre}) +{pts:.2f}"
        else:
            reason = ""
        return pts, reason

    def _score_mood(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Exact match = full points. Similar mood = partial credit from map."""
        if song.mood == user.favorite_mood:
            pts = self.MOOD_POINTS
        else:
            similarity = MOOD_SIMILARITY.get(user.favorite_mood, {})
            pts = similarity.get(song.mood, 0.0) * self.MOOD_POINTS

        if pts == self.MOOD_POINTS:
            reason = f"mood match ({song.mood}) +{pts:.2f}"
        elif pts > 0:
            reason = f"similar mood ({song.mood}) +{pts:.2f}"
        else:
            reason = ""
        return pts, reason

    def _score_energy(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Proximity: closer to the user's target = more points."""
        proximity = 1.0 - abs(song.energy - user.target_energy) ** 2
        pts = proximity * self.ENERGY_POINTS
        reason = f"energy proximity +{pts:.2f}"
        return pts, reason

    def _score_acousticness(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Float target = proximity. Boolean fallback = directional."""
        if user.target_acousticness is not None:
            proximity = 1.0 - abs(song.acousticness - user.target_acousticness) ** 2
            pts = proximity * self.ACOUSTIC_POINTS
        elif user.likes_acoustic:
            pts = song.acousticness * self.ACOUSTIC_POINTS
        else:
            pts = (1.0 - song.acousticness) * self.ACOUSTIC_POINTS
        reason = f"acousticness fit +{pts:.2f}"
        return pts, reason

    def _score_danceability(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Proximity scoring, only active when the user sets a target."""
        if user.target_danceability is None:
            return 0.0, ""
        proximity = 1.0 - abs(song.danceability - user.target_danceability) ** 2
        pts = proximity * self.DANCE_POINTS
        reason = f"danceability fit +{pts:.2f}"
        return pts, reason

    def _score_instrumentalness(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Directional scoring, only active when the user sets a preference."""
        if user.prefers_instrumental is None:
            return 0.0, ""
        if user.prefers_instrumental:
            pts = song.instrumentalness * self.INSTRUMENTAL_POINTS
        else:
            pts = (1.0 - song.instrumentalness) * self.INSTRUMENTAL_POINTS
        reason = f"instrumental fit +{pts:.2f}"
        return pts, reason

    # --- Composite scoring --------------------------------------------------

    def score_song(self, song: Song, user: UserProfile) -> Tuple[float, List[str]]:
        """Score a single song against the user profile.

        Returns:
            (total_score, reasons) where reasons is a list of human-readable
            strings like "genre match (pop) +2.00" for every feature that
            contributed points.
        """
        components = [
            self._score_genre(song, user),
            self._score_mood(song, user),
            self._score_energy(song, user),
            self._score_acousticness(song, user),
            self._score_danceability(song, user),
            self._score_instrumentalness(song, user),
        ]
        total = sum(pts for pts, _ in components)
        reasons = [reason for _, reason in components if reason]
        return total, reasons

    # --- Ranking ------------------------------------------------------------

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Score every song, sort descending, return top k."""
        scored = [(song, self.score_song(song, user)) for song in self.songs]
        scored.sort(key=lambda x: x[1][0], reverse=True)
        return [song for song, _ in scored[:k]]

    # --- Explanation --------------------------------------------------------

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable breakdown of why this song was recommended."""
        total, reasons = self.score_song(song, user)
        return f"Score {total:.2f}/{self.MAX_SCORE:.1f}: " + ", ".join(reasons)


# ---------------------------------------------------------------------------
# Functional API (used by main.py)
# ---------------------------------------------------------------------------

def _dict_to_song(d: Dict) -> Song:
    """Convert a CSV row dict into a Song object."""
    return Song(
        id=int(d["id"]),
        title=d["title"],
        artist=d["artist"],
        genre=d["genre"],
        mood=d["mood"],
        energy=float(d["energy"]),
        tempo_bpm=float(d["tempo_bpm"]),
        valence=float(d["valence"]),
        danceability=float(d["danceability"]),
        acousticness=float(d["acousticness"]),
        instrumentalness=float(d.get("instrumentalness", 0.0)),
        speechiness=float(d.get("speechiness", 0.0)),
    )


def _dict_to_user(d: Dict) -> UserProfile:
    """Convert a user preferences dict into a UserProfile object."""
    return UserProfile(
        favorite_genre=d.get("genre", ""),
        favorite_mood=d.get("mood", ""),
        target_energy=d.get("energy", 0.5),
        likes_acoustic=d.get("likes_acoustic", False),
        genre_preferences=d.get("genre_preferences"),
        target_acousticness=d.get("target_acousticness"),
        target_danceability=d.get("target_danceability"),
        prefers_instrumental=d.get("prefers_instrumental"),
    )


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            for key in ("energy", "tempo_bpm", "valence", "danceability",
                        "acousticness", "instrumentalness", "speechiness"):
                if key in row:
                    row[key] = float(row[key])
            songs.append(dict(row))
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song dict against a user preferences dict.

    This is the standalone functional entry point for scoring. It converts
    both dicts into typed objects, runs the six-component scoring formula,
    and returns the result in one pass.

    Args:
        user_prefs: Dict with keys genre, mood, energy, likes_acoustic,
                    and optional extended fields (genre_preferences, etc.)
        song:       Dict with keys matching the songs.csv columns.

    Returns:
        (total_score, reasons) where total_score is a float 0.0–6.0 and
        reasons is a list of human-readable strings explaining each
        component, e.g. ["genre match (pop) +2.00", "mood match (happy) +1.00", ...].
    """
    song_obj = _dict_to_song(song)
    user = _dict_to_user(user_prefs)
    rec = Recommender([])
    return rec.score_song(song_obj, user)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, List[str]]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Returns:
        List of (song_dict, total_score, reasons_list) tuples, sorted by
        score descending, limited to the top k results.
    """
    song_objects = [_dict_to_song(s) for s in songs]
    user = _dict_to_user(user_prefs)

    rec = Recommender(song_objects)
    scored = [(obj, rec.score_song(obj, user)) for obj in song_objects]
    scored.sort(key=lambda x: x[1][0], reverse=True)

    results = []
    for song_obj, (total, reasons) in scored[:k]:
        song_dict = next(s for s in songs if s["id"] == song_obj.id)
        results.append((song_dict, total, reasons))
    return results
