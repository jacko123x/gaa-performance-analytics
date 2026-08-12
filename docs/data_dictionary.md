# Austin Stacks Analytics Platform
## Data Dictionary

This document describes the datasets used by the Austin Stacks Analytics Platform.

---

# Dataset Relationships

```
Matches
   │
   ├───────────────┐
   │               │
   ▼               ▼
Team Stats      Player Stats
   │
   ├──────────────┐
   │              │
   ▼              ▼
Shooting      Kickouts
   │
   ▼
Turnovers
```

Each dataset is linked using **MatchID**.

---

# matches.csv

One record per match.

## Primary Key

MatchID

## Fields

| Column | Description |
|---------|-------------|
| MatchID | Unique match identifier |
| Date | Match date |
| Competition | League / Championship |
| Opponent | Opposition team |
| Venue | Home or Away |
| Result | Win / Loss / Draw |
| Season | Season identifier |

---

# team_match_stats.csv

One record per team per match.

## Primary Key

MatchID + Team

## Columns

| Column | Description |
|---------|-------------|
| MatchID | Match identifier |
| Team | Team name |
| Opponent | Opposition |
| Goals | Goals scored |
| Points | Points scored |
| TwoPointers | Two-point scores |
| Wides | Wide shots |
| Shorts | Short shots |
| KickoutsWon | Own kickouts retained |
| KickoutsLost | Own kickouts lost |
| ForcedTurnovers | Opposition possessions won through pressure |
| UnforcedTurnovers | Opposition unforced turnovers won |
| FreesConceded | Frees conceded |
| BreakingBallWon | Breaking balls won |
| Attacks | Total attacking possessions |
| TotalShots | Total shots |
| TotalScores | Total scoring shots |
| ShotsPlay | Shots from play |
| ScoresPlay | Scores from play |
| ShotsPlaced | Placed-ball shots |
| ScoresPlaced | Placed-ball scores |

---

## Derived Metrics

Calculated automatically.

- Shot Conversion %
- Play Conversion %
- Placed Ball Conversion %
- Kickout Win %
- Turnover Differential
- Scores Per Attack
- Attack → Shot %
- Attack → Score %

---

# player_match_data.csv

One record per player per match.

## Primary Key

MatchID + PlayerName

## Columns

### Match

- MatchID
- Date
- Opponent
- HomeAway
- Result
- DataType

### Player

- SquadNumber
- PlayerName
- Position
- Started
- MinutesPlayed

### Passing

- HandpassesTotal
- Handpasses1H
- Handpasses2H
- HandpassTarget

- FootpassesTotal
- Footpasses1H
- Footpasses2H
- FootpassTarget

- IncompletePasses

### Discipline

- FreesWon
- FreesConceded

### Attack

- Assists
- Points
- Goals
- TwoPointers
- ShotAttempts
- Scores
- ShotConversionPct

---

## Derived Player Metrics

Calculated automatically.

- Total Passes
- Completed Passes
- Pass Accuracy %
- Handpass %
- Footpass %
- Total Score Value
- Shot Conversion %
- Passes Per Minute
- Score Value Per 60
- Assists Per 60
- Frees Won Per 60
- Direct Score Contributions
- Free Differential

---

# shooting_detail.csv

Detailed shooting information.

One record per period and shot type.

## Primary Key

MatchID + Team + Period + ShotType

## Columns

| Column | Description |
|---------|-------------|
| MatchID | Match identifier |
| Team | Team |
| Period | 1H / 2H / FT |
| ShotType | Overall / Play / Free / Mark / 45 / Penalty |
| ShotsTaken | Total shots |
| ShotsScored | Total scores |
| Wides | Wides |
| Shorts | Shorts |
| Blocked | Blocked shots |
| Saved | Saved shots |
| Post | Hit post |

---

## Dashboard Uses

- Shot conversion
- Shot type comparison
- Half comparison
- Miss analysis

---

# kickout_stats.csv

Detailed kickout analysis.

One record per period and kickout type.

## Primary Key

MatchID + Team + Period + KickoutType

## Columns

| Column | Description |
|---------|-------------|
| MatchID | Match identifier |
| Team | Team |
| Period | 1H / 2H / FT |
| KickoutType | Own / Opponent |
| Taken | Total kickouts |
| Won | Successful possessions |
| Lost | Lost possessions |
| CleanWins | Clean catches |
| BreakWins | Breaking ball wins |
| FreeWins | Won from free |
| SidelineWins | Won from sideline |

---

## Dashboard Uses

- Own kickout retention
- Opposition kickout press
- Clean win %
- Break win %
- Half comparison

---

# turnover_stats.csv

Detailed turnover analysis.

One record per period.

## Primary Key

MatchID + Team + Period

## Columns

| Column | Description |
|---------|-------------|
| MatchID | Match identifier |
| Team | Team |
| Period | 1H / 2H / FT |
| TurnoversWonForced | Forced turnovers won |
| TurnoversWonUnforced | Unforced turnovers won |
| TurnoversLostForced | Forced turnovers lost |
| TurnoversLostUnforced | Unforced turnovers lost |

---

## Dashboard Uses

- Turnover differential
- Forced turnover rate
- Unforced error rate
- Half comparison

---

# Data Validation Rules

## Team Stats

- Goals >= 0
- Points >= 0
- TwoPointers >= 0
- TotalShots >= TotalScores
- ShotsPlay + ShotsPlaced = TotalShots
- ScoresPlay + ScoresPlaced = TotalScores
- KickoutsWon + KickoutsLost > 0
- Attacks >= TotalShots

---

## Player Stats

- MinutesPlayed <= 70
- Handpasses1H + Handpasses2H = HandpassesTotal
- Footpasses1H + Footpasses2H = FootpassesTotal
- Scores <= ShotAttempts
- No duplicate MatchID + PlayerName combinations

---

## Shooting

ShotsTaken =

ShotsScored +
Wides +
Shorts +
Blocked +
Saved +
Post

---

## Kickouts

Won + Lost = Taken

CleanWins +
BreakWins +
FreeWins +
SidelineWins = Won

---

## Turnovers

Forced +
Unforced =
Total Turnovers

---

# Future Expansion

Planned datasets.

- shot_events.csv
- kickout_events.csv
- gps_data.csv
- wellness_data.csv
- training_load.csv
- opposition_scouting.csv
- player_ratings.csv

These datasets will integrate with the current platform without changing the existing schema.