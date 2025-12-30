# app/utils/constants.py

"""
Project‑wide constants
----------------------

A safe place to store:
- Collection names
- Fixed labels
- Scoring constants
- Region lists (if static)
"""

# Collections in Directus
COL_MEETINGS = "Meetings"
COL_LEADERBOARD = "Leaderboard"
COL_LEADERBOARD_ALL = "Leaderboard_all"
COL_LEADERBOARD_PREDICT = "Leaderboard_predict"
COL_REPORT = "report"
COL_REGIONS = "regions"

# Score multipliers (example values — adjust as needed)
MEETING_SCORE_WEIGHT = 0.4
PARTICIPANTS_SCORE_WEIGHT = 0.3
TOPIC_SCORE_WEIGHT = 0.3

# Report constants
REPORT_LANGUAGE_EN = "EN"
REPORT_LANGUAGE_AR = "AR"

# PDF folder name in Directus (optional)
DEFAULT_PDF_FOLDER = None

# Minimum rows needed to train LSTM
MIN_LSTM_ROWS = 3
