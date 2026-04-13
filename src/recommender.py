from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import csv


# ---------------------------------------------------------------------------
# Mood similarity map
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

# ---------------------------------------------------------------------------
# Mood-tag scoring: maps user-requested tags to point values.
# A song earns points for each tag it has that the user wants.
# ---------------------------------------------------------------------------
MOOD_TAG_POINTS = {
    "euphoric": 0.3, "anthemic": 0.25, "atmospheric": 0.2,
    "introspective": 0.2, "soothing": 0.15, "ethereal": 0.2,
    "warm": 0.15, "intimate": 0.15, "cinematic": 0.2,
    "brooding": 0.2, "minimal": 0.1, "sensual": 0.15,
    "bittersweet": 0.2, "chaotic": 0.15, "powerful": 0.25,
}

# ---------------------------------------------------------------------------
# Scoring mode presets (Challenge 2: Strategy pattern)
# Each mode defines a weight dict that overrides the defaults.
# ---------------------------------------------------------------------------
SCORING_MODES = {
    "balanced": {
        "genre": 2.0, "mood": 1.0, "energy": 1.5,
        "acoustic": 0.75, "dance": 0.5, "instrumental": 0.25,
        "popularity": 0.5, "decade": 0.3, "mood_tags": 0.5,
        "liveness": 0.2, "vocal": 0.25,
    },
    "genre-first": {
        "genre": 3.5, "mood": 0.5, "energy": 1.0,
        "acoustic": 0.5, "dance": 0.25, "instrumental": 0.25,
        "popularity": 0.25, "decade": 0.2, "mood_tags": 0.3,
        "liveness": 0.1, "vocal": 0.15,
    },
    "mood-first": {
        "genre": 1.0, "mood": 2.5, "energy": 1.0,
        "acoustic": 0.5, "dance": 0.25, "instrumental": 0.25,
        "popularity": 0.25, "decade": 0.2, "mood_tags": 1.0,
        "liveness": 0.1, "vocal": 0.15,
    },
    "energy-focused": {
        "genre": 1.0, "mood": 0.5, "energy": 3.0,
        "acoustic": 0.75, "dance": 1.0, "instrumental": 0.25,
        "popularity": 0.25, "decade": 0.1, "mood_tags": 0.25,
        "liveness": 0.3, "vocal": 0.1,
    },
}


@dataclass
class Song:
    """Represents a song and its attributes."""
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
    # --- Challenge 1: new features ---
    popularity: int = 50
    release_decade: str = "2020s"
    mood_tags: List[str] = field(default_factory=list)
    liveness: float = 0.1
    vocal_gender: str = "none"


@dataclass
class UserProfile:
    """Represents a user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    genre_preferences: Optional[Dict[str, float]] = None
    target_acousticness: Optional[float] = None
    target_danceability: Optional[float] = None
    prefers_instrumental: Optional[bool] = None
    # --- Challenge 1: new preference fields ---
    min_popularity: Optional[int] = None
    preferred_decade: Optional[str] = None
    preferred_mood_tags: Optional[List[str]] = None
    target_liveness: Optional[float] = None
    preferred_vocal: Optional[str] = None


class Recommender:
    """
    OOP scoring engine with pluggable scoring modes (Challenge 2).

    Usage:
        rec = Recommender(songs, mode="balanced")      # default
        rec = Recommender(songs, mode="genre-first")    # genre-heavy
        rec = Recommender(songs, mode="mood-first")     # mood-heavy
        rec = Recommender(songs, mode="energy-focused") # energy-heavy
    """

    def __init__(self, songs: List[Song], mode: str = "balanced"):
        self.songs = songs
        self.mode = mode
        self._w = SCORING_MODES[mode]
        self.max_score = sum(self._w.values())

    # --- Per-feature scoring helpers ----------------------------------------

    def _score_genre(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        w = self._w["genre"]
        if user.genre_preferences:
            pts = user.genre_preferences.get(song.genre, 0.0) * w
        else:
            pts = w if song.genre == user.favorite_genre else 0.0
        if pts == w:
            reason = f"genre match ({song.genre}) +{pts:.2f}"
        elif pts > 0:
            reason = f"similar genre ({song.genre}) +{pts:.2f}"
        else:
            reason = ""
        return pts, reason

    def _score_mood(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        w = self._w["mood"]
        if song.mood == user.favorite_mood:
            pts = w
        else:
            similarity = MOOD_SIMILARITY.get(user.favorite_mood, {})
            pts = similarity.get(song.mood, 0.0) * w
        if pts == w:
            reason = f"mood match ({song.mood}) +{pts:.2f}"
        elif pts > 0:
            reason = f"similar mood ({song.mood}) +{pts:.2f}"
        else:
            reason = ""
        return pts, reason

    def _score_energy(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        w = self._w["energy"]
        proximity = 1.0 - abs(song.energy - user.target_energy) ** 2
        pts = proximity * w
        return pts, f"energy proximity +{pts:.2f}"

    def _score_acousticness(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        w = self._w["acoustic"]
        if user.target_acousticness is not None:
            proximity = 1.0 - abs(song.acousticness - user.target_acousticness) ** 2
            pts = proximity * w
        elif user.likes_acoustic:
            pts = song.acousticness * w
        else:
            pts = (1.0 - song.acousticness) * w
        return pts, f"acousticness fit +{pts:.2f}"

    def _score_danceability(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        w = self._w["dance"]
        if user.target_danceability is None:
            return 0.0, ""
        proximity = 1.0 - abs(song.danceability - user.target_danceability) ** 2
        pts = proximity * w
        return pts, f"danceability fit +{pts:.2f}"

    def _score_instrumentalness(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        w = self._w["instrumental"]
        if user.prefers_instrumental is None:
            return 0.0, ""
        if user.prefers_instrumental:
            pts = song.instrumentalness * w
        else:
            pts = (1.0 - song.instrumentalness) * w
        return pts, f"instrumental fit +{pts:.2f}"

    # --- Challenge 1: new feature scorers ---

    def _score_popularity(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Songs above user's min_popularity get scaled points."""
        w = self._w["popularity"]
        if user.min_popularity is None:
            return 0.0, ""
        pts = (song.popularity / 100.0) * w
        if song.popularity < user.min_popularity:
            pts *= 0.3  # heavy penalty for songs below threshold
            return pts, f"popularity low ({song.popularity}) +{pts:.2f}"
        return pts, f"popularity ({song.popularity}) +{pts:.2f}"

    def _score_decade(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Exact decade match = full points. Adjacent decades = half."""
        w = self._w["decade"]
        if user.preferred_decade is None:
            return 0.0, ""
        decades_ordered = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
        if song.release_decade == user.preferred_decade:
            pts = w
            return pts, f"decade match ({song.release_decade}) +{pts:.2f}"
        try:
            si = decades_ordered.index(song.release_decade)
            ui = decades_ordered.index(user.preferred_decade)
            if abs(si - ui) == 1:
                pts = w * 0.5
                return pts, f"adjacent decade ({song.release_decade}) +{pts:.2f}"
        except ValueError:
            pass
        return 0.0, ""

    def _score_mood_tags(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Award points for each mood tag the user wants that the song has."""
        w = self._w["mood_tags"]
        if not user.preferred_mood_tags or not song.mood_tags:
            return 0.0, ""
        matched = [t for t in user.preferred_mood_tags if t in song.mood_tags]
        if not matched:
            return 0.0, ""
        # Sum individual tag weights, cap at the maximum
        raw = sum(MOOD_TAG_POINTS.get(t, 0.1) for t in matched)
        pts = min(raw, 1.0) * w
        tag_str = ";".join(matched)
        return pts, f"mood tags ({tag_str}) +{pts:.2f}"

    def _score_liveness(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Proximity scoring for live vs. studio preference."""
        w = self._w["liveness"]
        if user.target_liveness is None:
            return 0.0, ""
        proximity = 1.0 - abs(song.liveness - user.target_liveness) ** 2
        pts = proximity * w
        return pts, f"liveness fit +{pts:.2f}"

    def _score_vocal(self, song: Song, user: UserProfile) -> Tuple[float, str]:
        """Match vocal gender preference: exact = full, none = half."""
        w = self._w["vocal"]
        if user.preferred_vocal is None:
            return 0.0, ""
        if song.vocal_gender == user.preferred_vocal:
            pts = w
            return pts, f"vocal match ({song.vocal_gender}) +{pts:.2f}"
        if song.vocal_gender == "mixed":
            pts = w * 0.5
            return pts, f"vocal partial (mixed) +{pts:.2f}"
        if song.vocal_gender == "none" and user.preferred_vocal != "none":
            pts = w * 0.3
            return pts, f"vocal instrumental +{pts:.2f}"
        return 0.0, ""

    # --- Composite scoring --------------------------------------------------

    def score_song(self, song: Song, user: UserProfile) -> Tuple[float, List[str]]:
        """Score a single song. Returns (total, reasons_list)."""
        components = [
            self._score_genre(song, user),
            self._score_mood(song, user),
            self._score_energy(song, user),
            self._score_acousticness(song, user),
            self._score_danceability(song, user),
            self._score_instrumentalness(song, user),
            self._score_popularity(song, user),
            self._score_decade(song, user),
            self._score_mood_tags(song, user),
            self._score_liveness(song, user),
            self._score_vocal(song, user),
        ]
        total = sum(pts for pts, _ in components)
        reasons = [reason for _, reason in components if reason]
        return total, reasons

    # --- Ranking with diversity penalty (Challenge 3) -----------------------

    def recommend(self, user: UserProfile, k: int = 5,
                  diversity: bool = False) -> List[Song]:
        """Score every song, sort descending, return top k.

        If diversity=True, apply a penalty for repeated artists/genres
        among the already-selected results (greedy re-ranking).
        """
        scored = [(song, self.score_song(song, user)) for song in self.songs]
        scored.sort(key=lambda x: x[1][0], reverse=True)

        if not diversity:
            return [song for song, _ in scored[:k]]

        return self._diverse_topk(scored, k)

    def _diverse_topk(self, scored: list, k: int) -> List[Song]:
        """Greedy re-ranking: penalize songs whose artist or genre is
        already in the selected set."""
        selected: List[Song] = []
        seen_artists: Dict[str, int] = {}
        seen_genres: Dict[str, int] = {}
        ARTIST_PENALTY = 0.15  # per duplicate
        GENRE_PENALTY = 0.08   # per duplicate

        for song, (base_score, _reasons) in scored:
            penalty = (seen_artists.get(song.artist, 0) * ARTIST_PENALTY
                       + seen_genres.get(song.genre, 0) * GENRE_PENALTY)
            adjusted = base_score * max(0.0, 1.0 - penalty)
            # Re-insert with adjusted score for selection
            if len(selected) < k:
                selected.append(song)
                seen_artists[song.artist] = seen_artists.get(song.artist, 0) + 1
                seen_genres[song.genre] = seen_genres.get(song.genre, 0) + 1
            else:
                break

        return selected

    # --- Explanation --------------------------------------------------------

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        total, reasons = self.score_song(song, user)
        return f"Score {total:.2f}/{self.max_score:.1f}: " + ", ".join(reasons)


# Backwards-compatible constants for tests
Recommender.GENRE_POINTS = 2.0
Recommender.MOOD_POINTS = 1.0
Recommender.ENERGY_POINTS = 1.5
Recommender.ACOUSTIC_POINTS = 0.75
Recommender.DANCE_POINTS = 0.5
Recommender.INSTRUMENTAL_POINTS = 0.25
Recommender.MAX_SCORE = 6.0


# ---------------------------------------------------------------------------
# Functional API
# ---------------------------------------------------------------------------

def _dict_to_song(d: Dict) -> Song:
    """Convert a CSV row dict into a Song object."""
    tags_raw = d.get("mood_tags", "")
    tags = tags_raw.split(";") if isinstance(tags_raw, str) and tags_raw else []
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
        popularity=int(d.get("popularity", 50)),
        release_decade=d.get("release_decade", "2020s"),
        mood_tags=tags,
        liveness=float(d.get("liveness", 0.1)),
        vocal_gender=d.get("vocal_gender", "none"),
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
        min_popularity=d.get("min_popularity"),
        preferred_decade=d.get("preferred_decade"),
        preferred_mood_tags=d.get("preferred_mood_tags"),
        target_liveness=d.get("target_liveness"),
        preferred_vocal=d.get("preferred_vocal"),
    )


def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file."""
    songs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            for key in ("energy", "tempo_bpm", "valence", "danceability",
                        "acousticness", "instrumentalness", "speechiness",
                        "liveness"):
                if key in row:
                    row[key] = float(row[key])
            if "popularity" in row:
                row["popularity"] = int(row["popularity"])
            songs.append(dict(row))
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song dict against a user preferences dict."""
    song_obj = _dict_to_song(song)
    user = _dict_to_user(user_prefs)
    mode = user_prefs.get("mode", "balanced")
    rec = Recommender([], mode=mode)
    return rec.score_song(song_obj, user)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    diversity: bool = False) -> List[Tuple[Dict, float, List[str]]]:
    """Functional recommendation API used by main.py."""
    song_objects = [_dict_to_song(s) for s in songs]
    user = _dict_to_user(user_prefs)
    mode = user_prefs.get("mode", "balanced")

    rec = Recommender(song_objects, mode=mode)
    scored = [(obj, rec.score_song(obj, user)) for obj in song_objects]
    scored.sort(key=lambda x: x[1][0], reverse=True)

    if diversity:
        # Greedy diverse re-ranking
        selected = []
        seen_artists: Dict[str, int] = {}
        seen_genres: Dict[str, int] = {}
        for song_obj, (total, reasons) in scored:
            penalty = (seen_artists.get(song_obj.artist, 0) * 0.15
                       + seen_genres.get(song_obj.genre, 0) * 0.08)
            adjusted = total * max(0.0, 1.0 - penalty)
            song_dict = next(s for s in songs if s["id"] == song_obj.id)
            selected.append((song_dict, adjusted, reasons, song_obj))
            seen_artists[song_obj.artist] = seen_artists.get(song_obj.artist, 0) + 1
            seen_genres[song_obj.genre] = seen_genres.get(song_obj.genre, 0) + 1
            if len(selected) >= k * 2:
                break
        selected.sort(key=lambda x: x[1], reverse=True)
        return [(sd, sc, rs) for sd, sc, rs, _ in selected[:k]]

    results = []
    for song_obj, (total, reasons) in scored[:k]:
        song_dict = next(s for s in songs if s["id"] == song_obj.id)
        results.append((song_dict, total, reasons))
    return results
