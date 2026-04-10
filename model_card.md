# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0** -- A content-based music recommender that scores songs against a user's taste profile using weighted feature matching.

---

## 2. Intended Use

This recommender suggests 3 to 5 songs from a small catalog of 18 tracks based on a user's preferred genre, mood, energy level, acousticness, danceability, and instrumental preferences. It is designed for classroom exploration and learning about how recommendation systems work. It is not intended for real users or production deployment. The system assumes each user has a single, static taste profile and does not learn or adapt over time.

---

## 3. How the Model Works

The recommender works like a judge at a talent show who scores each song on six criteria, then picks the top scorers.

For every song in the catalog, the system asks six questions and awards points:

1. **Does the genre match?** (up to 2 points) If the user loves pop and the song is pop, it gets full credit. If the song is in a related genre the user also likes (like indie pop), it gets partial credit. If the genre is completely unrelated, zero points.

2. **Does the mood match?** (up to 1 point) Same idea, but with emotions. If the user wants "happy" and the song is "happy," full credit. If the song is "uplifting" (which feels similar to happy), partial credit. If the song is "dark," nothing.

3. **How close is the energy level?** (up to 1.5 points) The system measures how far apart the song's energy and the user's target are. A song at 0.82 energy for a user wanting 0.85 loses almost nothing. A song at 0.28 energy loses a lot. The formula punishes bigger gaps more harshly than small ones (it squares the difference).

4. **Does the acoustic texture fit?** (up to 0.75 points) Same proximity logic as energy, comparing how acoustic the song sounds versus what the user wants.

5. **Is it danceable enough?** (up to 0.5 points) If the user set a danceability target, songs close to that target score higher.

6. **Vocal vs. instrumental preference?** (up to 0.25 points) A small bonus if the song matches whether the user wants vocals or pure instruments.

All six scores are added up. Maximum possible: 6.0 points. The songs are then sorted from highest to lowest score, and the top 5 are returned with a list of reasons explaining each point award.

---

## 4. Data

The catalog contains **18 songs** stored in `data/songs.csv` with 12 columns per song (id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness, instrumentalness, speechiness).

- **15 genres** are represented, but the distribution is uneven: lofi has 3 songs, pop has 2, and the remaining 13 genres have just 1 song each
- **14 moods** are represented: chill has 3 songs, happy and intense each have 2, and the other 11 moods have 1 each
- **Energy distribution** splits roughly into low-energy (7 songs below 0.5) and high-energy (8 songs at 0.75+), with only 3 songs in the middle range (0.50--0.74)
- The original starter had 10 songs; 8 were added to cover missing genres (hip hop, r&b, classical, electronic, folk, latin, funk, metal) and moods (romantic, aggressive, nostalgic, energetic, dreamy, uplifting, melancholy, dark)
- The dataset reflects a curated selection meant to demonstrate variety, not real listening data. It likely over-represents genres familiar to the author and under-represents regional or non-English music traditions

---

## 5. Strengths

- **Exact matches feel right.** When a user asks for pop/happy and the catalog has a pop/happy song (Sunrise City), it ranks #1 at 5.98/6.0. The results match musical intuition for well-defined tastes.
- **Cross-genre discovery works.** The genre affinity map lets a lofi listener find jazz and ambient tracks they would likely enjoy. Coffee Shop Stories (jazz/relaxed) surfaces at #5 for the Chill Lofi profile despite being a completely different genre.
- **Transparent reasoning.** Every recommendation comes with an itemized list of reasons and point values. A non-technical user can read "genre match (pop) +2.00, mood match (happy) +1.00" and understand exactly why a song was chosen. No black box.
- **Graceful degradation.** When tested with a genre that does not exist in the catalog (reggae), the system returned lower-confidence results (3.29--3.97 range) instead of high-scoring false positives. The scores honestly reflect the limitation.
- **Edge cases produce defensible results.** The Acoustic Electronic contradiction (electronic genre + high acousticness) was resolved by surfacing an ambient track that balanced both preferences, rather than blindly following genre alone.

---

## 6. Limitations and Bias

**The system over-prioritizes genre because genre match alone is worth 2.0 out of 6.0 points (33%).** During the weight shift experiment, we halved genre to 1.0 and doubled energy to 3.0. The most dramatic change was in the Middleground profile: with original weights, Sunrise City (pop) won at 4.48 because genre=pop carried it; with shifted weights, Midnight Coding (lofi/chill) won at 5.19 because its energy (0.42) was closer to the target (0.50). The genre weight acts as a gatekeeper -- a song from the wrong genre can almost never outscore one from the right genre, even if every other feature is a better match.

**The energy gap formula creates a "middle-energy blind spot."** Only 3 of 18 songs fall in the 0.50--0.74 energy range. A user who wants moderate energy (0.60) will see either low-energy songs or high-energy songs at the top, because the squared proximity formula penalizes both directions equally. The catalog itself is bimodal (clustered at low and high energy), so mid-energy users are structurally underserved regardless of weights.

**Lofi and pop listeners get more variety than everyone else.** Lofi has 3 songs and pop has 2, so those profiles always have multiple strong candidates scoring above 5.0. A classical listener has exactly 1 song (Winter Sonata). If that song does not match their energy or acousticness preferences, the system has nothing else to offer from that genre. This is a dataset size problem, not a scoring problem, but the effect is that some users get rich recommendations while others get a single match followed by a sharp quality drop.

**The mood similarity map is hand-authored and incomplete.** If a mood is not in the map, it gets zero partial credit. A user who wants "bittersweet" (not in the map) would get no mood points for any song, even though "nostalgic" or "melancholy" are clearly related. Real recommender systems learn these relationships from data rather than hardcoding them.

**The system cannot explain why it did NOT recommend a song.** It shows reasons for the top 5, but a user who expected a specific song has no way to see what disqualified it. This makes it harder to build trust with users whose expectations differ from the scoring logic.

---

## 7. Evaluation

### Profiles Tested

We tested 7 profiles across two categories:

**Standard profiles (3):** High-Energy Pop, Chill Lofi, Deep Intense Rock. These have coherent, non-contradictory preferences and test whether the system can match obvious intent.

**Adversarial edge cases (4):**
- **High-Energy Sad** (energy=0.95, mood=melancholy) -- tests contradictory preferences. Winter Sonata still won because genre+mood outweighed the energy penalty, which is arguably correct: a classical/melancholy listener wants the right vibe at the wrong tempo more than the wrong vibe at the right tempo.
- **Ghost Genre** (genre=reggae) -- tests a genre with zero catalog matches. The system degraded gracefully, returning low-confidence results driven by mood rather than fabricating false genre matches.
- **Acoustic Electronic** (electronic genre, acousticness=0.90) -- tests contradictory feature requirements. The system found a compromise (ambient music) rather than blindly following genre.
- **The Middleground** (all numeric features at 0.5) -- tests neutral preferences. Genre dominated the results, confirming the weight hierarchy.

### Weight Shift Experiment

We doubled energy weight (1.5 to 3.0) and halved genre weight (2.0 to 1.0) to test sensitivity:

| Profile | Original #1 | Experimental #1 | Changed? |
|---|---|---|---|
| High-Energy Pop | Sunrise City | Sunrise City | No |
| Chill Lofi | Library Rain | Library Rain | No |
| Deep Intense Rock | Storm Runner | Storm Runner | No |
| EDGE: The Middleground | Sunrise City (pop) | Midnight Coding (lofi) | **Yes** |
| EDGE: Acoustic Electronic | Spacewalk Thoughts | Spacewalk Thoughts | No |

The standard profiles were stable -- the #1 song did not change because the best match wins on all features simultaneously. The Middleground profile was the most sensitive because its neutral numeric preferences made genre the tiebreaker. When genre weight dropped, energy proximity took over, and a lofi song with energy closer to 0.50 displaced the pop song. This confirms the original genre=2.0 weight is appropriate for users with real preferences, but may over-determine results for users with weak preferences.

### What Surprised Us

- **Gym Hero keeps appearing for happy-pop users** even though its mood is "intense," not "happy." At #3 with 4.97 points, it outscores non-pop songs that have the right mood. In plain language: the system thinks being pop is more important than being happy. For a user who specifically wants cheerful music, this could feel wrong. Gym Hero is there because its genre match (+2.00) plus high energy proximity (+1.47) outweighs the missing mood point.
- **The Ghost Genre profile produced the most interesting results.** Without genre anchoring the scores, mood became the primary signal, and the system surfaced a diverse mix of songs: indie pop, pop, funk, latin, electronic. This is actually closer to how a real discovery playlist should work.
- **The 2.05pt gap** in the High-Energy Sad profile (5.35 for #1 vs. 3.30 for #2) was the largest drop between ranks across all profiles. It means the system is one song deletion away from having no good answer for that user.

---

## 8. Future Work

- **Weighted mood similarity from data.** Replace the hand-authored mood map with co-occurrence analysis -- if users who like "melancholy" also frequently listen to "nostalgic" songs, learn that relationship automatically.
- **Diversity constraint in ranking.** After scoring, ensure the top 5 do not all come from the same genre. A simple approach: after picking #1, apply a small penalty to songs sharing its genre before picking #2.
- **Negative preferences.** Let users specify genres or moods to avoid ("anything except metal"). Currently there is no way to penalize unwanted features.
- **Dynamic profiles.** Let the profile shift based on time of day or listening context. A user might want chill lofi in the morning and intense rock in the evening.
- **Larger catalog with real audio features.** 18 songs is enough to demonstrate the concept but too small to avoid the single-match problem for niche genres.

---

## 9. Personal Reflection

Building this recommender changed how I think about the music apps I use every day. The biggest lesson was that **weights are opinions disguised as math.** Setting genre to 2.0 and mood to 1.0 is not an objective fact -- it is a design decision that says "where a song comes from matters more than how it makes you feel." Different weight choices produce different realities for the user, and the user never sees those weights. They just see the playlist and assume it is objective.

The weight shift experiment made this concrete. When I doubled energy and halved genre, the Middleground profile suddenly got lofi recommendations instead of pop. Neither result is "wrong" -- they reflect different philosophies about what matters in music. Real platforms like Spotify make these tradeoffs thousands of times, and the user experience is shaped entirely by choices that look like engineering but are really editorial.

The most unexpected discovery was how the Ghost Genre profile (reggae) produced the most diverse, discovery-oriented results precisely because it could not rely on genre matching. When the system's strongest signal was removed, it had to use mood, energy, and texture to find songs -- and the results felt more like a curated "explore" playlist than a genre silo. This suggests that the genre weight, while useful for accuracy, might actually work against serendipity. A real recommender might benefit from occasionally turning down genre weight on purpose to help users escape their filter bubble.
