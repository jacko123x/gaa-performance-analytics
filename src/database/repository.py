import pandas as pd
from sqlalchemy import select

from src.database.db import SessionLocal
from src.database.models import (
    KickoutStat,
    Match,
    Player,
    PlayerMatchStat,
    ScoringSource,
    ShootingDetail,
    TeamMatchStat,
    TurnoverStat,
)


def load_matches_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = (
            session.execute(
                select(Match).order_by(Match.date, Match.id)
            )
            .scalars()
            .all()
        )

        matches = pd.DataFrame(
            [
                {
                    "MatchID": row.match_code,
                    "Date": row.date,
                    "Competition": row.competition,
                    "Round": row.round,
                    "Venue": row.venue,
                    "HomeTeam": row.home_team,
                    "AwayTeam": row.away_team,
                    "HomeScore": row.home_score,
                    "AwayScore": row.away_score,
                    "Result": row.result,
                }
                for row in rows
            ]
        )

        matches["Date"] = pd.to_datetime(
            matches["Date"],
            errors="coerce",
        )
        for column in ["HomeScore", "AwayScore"]:
            matches[column] = pd.to_numeric(
                matches[column],
                errors="coerce",
            )

        return matches


def load_team_stats_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(TeamMatchStat, Match)
            .join(Match, TeamMatchStat.match_id == Match.id)
            .order_by(Match.id, TeamMatchStat.id)
        ).all()

        return pd.DataFrame(
            [
                {
                    "MatchID": match.match_code,
                    "Team": stat.team,
                    "Opponent": stat.opponent,
                    "Goals": stat.goals,
                    "Points": stat.points,
                    "TwoPointers": stat.two_pointers,
                    "Wides": stat.wides,
                    "Shorts": stat.shorts,
                    "KickoutsWon": stat.kickouts_won,
                    "KickoutsLost": stat.kickouts_lost,
                    "ForcedTurnovers": stat.forced_turnovers,
                    "UnforcedTurnovers": stat.unforced_turnovers,
                    "FreesConceded": stat.frees_conceded,
                    "BreakingBallWon": stat.breaking_ball_won,
                    "Attacks": stat.attacks,
                    "TotalShots": stat.total_shots,
                    "TotalScores": stat.total_scores,
                    "ShotsPlay": stat.shots_play,
                    "ScoresPlay": stat.scores_play,
                    "ShotsPlaced": stat.shots_placed,
                    "ScoresPlaced": stat.scores_placed,
                }
                for stat, match in rows
            ]
        )


def load_shooting_detail_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(ShootingDetail, Match)
            .join(Match, ShootingDetail.match_id == Match.id)
            .order_by(Match.id, ShootingDetail.id)
        ).all()

        return pd.DataFrame(
            [
                {
                    "MatchID": match.match_code,
                    "Team": stat.team,
                    "Period": stat.period,
                    "ShotType": stat.shot_type,
                    "ShotsTaken": stat.shots_taken,
                    "ShotsScored": stat.shots_scored,
                    "Wides": stat.wides,
                    "Shorts": stat.shorts,
                    "Blocked": stat.blocked,
                    "Post": stat.post,
                    "Saved": stat.saved,
                }
                for stat, match in rows
            ]
        )


def load_scoring_sources_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(ScoringSource, Match)
            .join(Match, ScoringSource.match_id == Match.id)
            .order_by(Match.id, ScoringSource.id)
        ).all()

        return pd.DataFrame(
            [
                {
                    "MatchID": match.match_code,
                    "Team": stat.team,
                    "Source": stat.source,
                    "Scores": stat.scores,
                }
                for stat, match in rows
            ]
        )


def load_kickout_stats_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(KickoutStat, Match)
            .join(Match, KickoutStat.match_id == Match.id)
            .order_by(Match.id, KickoutStat.id)
        ).all()

        return pd.DataFrame(
            [
                {
                    "MatchID": match.match_code,
                    "Team": stat.team,
                    "Period": stat.period,
                    "KickoutType": stat.kickout_type,
                    "Taken": stat.taken,
                    "Won": stat.won,
                    "Lost": stat.lost,
                    "CleanWins": stat.clean_wins,
                    "BreakWins": stat.break_wins,
                    "FreeWins": stat.free_wins,
                    "SidelineWins": stat.sideline_wins,
                }
                for stat, match in rows
            ]
        )


def load_turnover_stats_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(TurnoverStat, Match)
            .join(Match, TurnoverStat.match_id == Match.id)
            .order_by(Match.id, TurnoverStat.id)
        ).all()

        return pd.DataFrame(
            [
                {
                    "MatchID": match.match_code,
                    "Team": stat.team,
                    "Period": stat.period,
                    "TurnoversWonForced": stat.turnovers_won_forced,
                    "TurnoversWonUnforced": stat.turnovers_won_unforced,
                    "TurnoversLostForced": stat.turnovers_lost_forced,
                    "TurnoversLostUnforced": stat.turnovers_lost_unforced,
                }
                for stat, match in rows
            ]
        )


def load_player_match_data_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(PlayerMatchStat, Player, Match)
            .join(Player, PlayerMatchStat.player_id == Player.id)
            .join(Match, PlayerMatchStat.match_id == Match.id)
            .order_by(Match.id, PlayerMatchStat.id)
        ).all()

        return pd.DataFrame(
            [
                {
                    "MatchID": match.match_code,
                    "Date": stat.date,
                    "Opponent": stat.opponent,
                    "HomeAway": stat.home_away,
                    "Result": stat.result,
                    "DataType": stat.data_type,
                    "SquadNumber": stat.squad_number,
                    "PlayerName": player.player_name,
                    "Position": stat.position,
                    "Captain": stat.captain,
                    "Started": stat.started,
                    "MinutesPlayed": stat.minutes_played,
                    "Possessions": stat.possessions,
                    "HandpassesTotal": stat.handpasses_total,
                    "Handpasses1H": stat.handpasses_1h,
                    "Handpasses2H": stat.handpasses_2h,
                    "HandpassesCompleted": stat.handpasses_completed,
                    "FootpassesTotal": stat.footpasses_total,
                    "Footpasses1H": stat.footpasses_1h,
                    "Footpasses2H": stat.footpasses_2h,
                    "FootpassesCompleted": stat.footpasses_completed,
                    "IncompletePasses": stat.incomplete_passes,
                    "KickoutsWon": stat.kickouts_won,
                    "BreakingBallsWon": stat.breaking_balls_won,
                    "TurnoversWon": stat.turnovers_won,
                    "TurnoversLost": stat.turnovers_lost,
                    "FreesWon": stat.frees_won,
                    "FreesConceded": stat.frees_conceded,
                    "Assists": stat.assists,
                    "Points": stat.points,
                    "PointsPlay": stat.points_play,
                    "PointsFree": stat.points_free,
                    "Points45": stat.points_45,
                    "Goals": stat.goals,
                    "TwoPointers": stat.two_pointers,
                    "ShotAttempts": stat.shot_attempts,
                    "Scores": stat.scores,
                    "ShotConversionPct": stat.shot_conversion_pct,
                    "YellowCards": stat.yellow_cards,
                    "BlackCards": stat.black_cards,
                    "RedCards": stat.red_cards,
                    "Notes": stat.notes,
                }
                for stat, player, match in rows
            ]
        )


def load_squad_numbers_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(Player)
            .where(Player.active.is_(True))
            .order_by(
                Player.squad_number,
                Player.player_name,
            )
        ).scalars().all()

        return pd.DataFrame(
            [
                {
                    "SquadNumber": player.squad_number,
                    "PlayerName": player.player_name,
                }
                for player in rows
            ],
            columns=[
                "SquadNumber",
                "PlayerName",
            ],
        )
