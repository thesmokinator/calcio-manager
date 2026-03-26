"""Enumerations for Calcio Manager."""

from enum import IntEnum, StrEnum


class GameFormat(StrEnum):
    """Supported game formats."""

    C7 = "c7"
    C5 = "c5"


class PlayerRole(StrEnum):
    """Player positions on the field."""

    GK = "POR"  # Portiere
    DEF = "DIF"  # Difensore
    MID = "CEN"  # Centrocampista
    FWD = "ATT"  # Attaccante


class AgeCategory(StrEnum):
    """CSI age categories with their specific rules."""

    OPEN = "open"
    MASTER_30 = "master_30"
    MASTER_40 = "master_40"
    JUNIORES = "juniores"
    ALLIEVI = "allievi"
    UNDER_14 = "under_14"
    UNDER_12 = "under_12"


class CompetitionType(StrEnum):
    """Types of CSI competitions."""

    LEAGUE = "campionato"
    CUP = "coppa"
    SUMMER_TOURNAMENT = "torneo_estivo"
    PLAYOFF = "playoff"
    PLAYOUT = "playout"


class CompetitionPhase(StrEnum):
    """Phase of a competition within the CSI hierarchy."""

    TERRITORIAL = "territoriale"  # Provincial
    REGIONAL = "regionale"
    NATIONAL = "nazionale"


class Division(StrEnum):
    """CSI league divisions."""

    ECCELLENZA = "eccellenza"
    SERIE_ORO = "serie_oro"
    SERIE_ARGENTO = "serie_argento"


class SeasonPhase(StrEnum):
    """Phases of a game season."""

    OFF_SEASON = "off_season"
    PRE_SEASON = "pre_season"
    IN_SEASON = "in_season"
    PLAYOFFS = "playoffs"
    SUMMER_TOURNAMENTS = "tornei_estivi"


class MatchEventType(StrEnum):
    """Types of events that can occur during a match."""

    KICK_OFF = "calcio_inizio"
    GOAL = "gol"
    CHANCE = "occasione"
    SHOT_SAVED = "parata"
    SHOT_WIDE = "tiro_fuori"
    SHOT_POST = "palo"
    FOUL = "fallo"
    YELLOW_CARD = "ammonizione"
    RED_CARD = "espulsione"
    SECOND_YELLOW = "doppia_ammonizione"
    SUBSTITUTION = "sostituzione"
    TIMEOUT = "time_out"
    HALF_TIME = "intervallo"
    FULL_TIME = "fine_partita"
    PENALTY_SHOOTOUT_START = "inizio_rigori"
    PENALTY_SCORED = "rigore_segnato"
    PENALTY_MISSED = "rigore_sbagliato"
    PENALTY_SAVED = "rigore_parato"
    CORNER = "calcio_angolo"
    FREE_KICK = "punizione"
    POSSESSION = "possesso"


class MatchResult(StrEnum):
    """Possible match outcomes."""

    HOME_WIN = "vittoria_casa"
    AWAY_WIN = "vittoria_trasferta"
    HOME_WIN_PENALTIES = "vittoria_casa_rigori"
    AWAY_WIN_PENALTIES = "vittoria_trasferta_rigori"
    FORFEIT_HOME = "rinuncia_casa"
    FORFEIT_AWAY = "rinuncia_trasferta"


class MoraleLevel(IntEnum):
    """Player morale levels."""

    TERRIBLE = 1
    LOW = 2
    NORMAL = 3
    GOOD = 4
    EXCELLENT = 5


class TacticStyle(StrEnum):
    """Team tactical approaches."""

    DEFENSIVE = "difensiva"
    BALANCED = "equilibrata"
    ATTACKING = "offensiva"
    COUNTER_ATTACK = "contropiede"
