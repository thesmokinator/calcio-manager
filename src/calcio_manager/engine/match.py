"""Match simulation engine for CSI Calcio a 7."""

from __future__ import annotations

import random
from collections.abc import Callable
from uuid import UUID

from calcio_manager.models.config import CompetitionRules
from calcio_manager.models.enums import (
    MatchEventType,
    MatchResult,
    PlayerRole,
    TacticStyle,
)
from calcio_manager.models.match import Match, MatchEvent, MatchScore, PenaltyShootout
from calcio_manager.models.player import Player
from calcio_manager.models.team import Team


class MatchState:
    """Tracks the evolving state of a match during simulation."""

    def __init__(self, home: Team, away: Team, rules: CompetitionRules) -> None:
        self.home = home
        self.away = away
        self.rules = rules
        self.home_goals = 0
        self.away_goals = 0
        self.minute = 0
        self.half = 1
        self.home_possession = 50.0
        self.away_possession = 50.0
        self.home_momentum = 0.0
        self.away_momentum = 0.0
        self.home_fouls = 0
        self.away_fouls = 0
        self.home_shots = 0
        self.away_shots = 0
        self.home_shots_on_target = 0
        self.away_shots_on_target = 0
        self.home_corners = 0
        self.away_corners = 0
        self.events: list[MatchEvent] = []

        # Fatigue tracking (0.0 = fresh, 1.0 = exhausted)
        self.home_fatigue = 0.0
        self.away_fatigue = 0.0

        # Timeouts remaining
        self.home_timeouts = rules.timeout_per_half
        self.away_timeouts = rules.timeout_per_half


def _team_attack_strength(team: Team, fatigue: float) -> float:
    """Calculate a team's attacking strength based on player attributes and fatigue."""
    players = team.available_players
    if not players:
        return 1.0

    attackers = [p for p in players if p.role == PlayerRole.FWD]
    midfielders = [p for p in players if p.role == PlayerRole.MID]

    atk_score = 0.0
    count = 0

    for p in attackers:
        atk_score += (
            p.attributes.technical.finishing * 2
            + p.attributes.technical.dribbling
            + p.attributes.physical.pace
        ) / 4
        count += 1

    for p in midfielders:
        atk_score += (
            p.attributes.technical.passing * 2
            + p.attributes.mental.decisions
            + p.attributes.technical.first_touch
        ) / 4
        count += 1

    if count == 0:
        return 5.0

    base = atk_score / count
    fatigue_penalty = fatigue * 3.0  # Fatigue reduces strength up to 3 points
    return max(1.0, base - fatigue_penalty)


def _team_defense_strength(team: Team, fatigue: float) -> float:
    """Calculate a team's defensive strength based on player attributes and fatigue."""
    players = team.available_players
    if not players:
        return 1.0

    defenders = [p for p in players if p.role == PlayerRole.DEF]
    goalkeeper = next((p for p in players if p.role == PlayerRole.GK), None)

    def_score = 0.0
    count = 0

    for p in defenders:
        def_score += (
            p.attributes.mental.positioning * 2
            + p.attributes.physical.strength
            + p.attributes.mental.teamwork
        ) / 4
        count += 1

    if goalkeeper:
        def_score += (
            goalkeeper.attributes.goalkeeping.reflexes * 2
            + goalkeeper.attributes.goalkeeping.handling
        ) / 3
        count += 1

    if count == 0:
        return 5.0

    base = def_score / count
    fatigue_penalty = fatigue * 2.5
    return max(1.0, base - fatigue_penalty)


def _team_midfield_strength(team: Team, fatigue: float) -> float:
    """Calculate a team's midfield strength for possession battles."""
    players = team.available_players
    midfielders = [p for p in players if p.role == PlayerRole.MID]

    if not midfielders:
        return 5.0

    mid_score = sum(
        (
            p.attributes.technical.passing * 2
            + p.attributes.mental.teamwork
            + p.attributes.physical.stamina
            + p.attributes.mental.decisions
        )
        / 5
        for p in midfielders
    )
    base = mid_score / len(midfielders)
    fatigue_penalty = fatigue * 2.0
    return max(1.0, base - fatigue_penalty)


def _tactic_modifier(tactic: TacticStyle) -> dict[str, float]:
    """Return attack/defense modifiers based on tactic style."""
    modifiers = {
        TacticStyle.DEFENSIVE: {"attack": 0.8, "defense": 1.2, "possession": 0.9},
        TacticStyle.BALANCED: {"attack": 1.0, "defense": 1.0, "possession": 1.0},
        TacticStyle.ATTACKING: {"attack": 1.2, "defense": 0.8, "possession": 1.1},
        TacticStyle.COUNTER_ATTACK: {"attack": 1.1, "defense": 1.0, "possession": 0.85},
    }
    return modifiers[tactic]


def _simulate_tick(state: MatchState) -> list[MatchEvent]:
    """Simulate one tick (~1-2 minutes) of the match."""
    events: list[MatchEvent] = []

    # Determine possession
    home_mid = _team_midfield_strength(state.home, state.home_fatigue)
    away_mid = _team_midfield_strength(state.away, state.away_fatigue)
    home_tactic = _tactic_modifier(state.home.tactic)
    away_tactic = _tactic_modifier(state.away.tactic)

    home_poss_weight = home_mid * home_tactic["possession"] + state.home_momentum
    away_poss_weight = away_mid * away_tactic["possession"] + state.away_momentum
    total = home_poss_weight + away_poss_weight
    if total > 0:
        state.home_possession = (home_poss_weight / total) * 100
        state.away_possession = 100 - state.home_possession

    # Determine which team attacks this tick
    attacking_home = random.random() < (state.home_possession / 100)

    # Emit a possession event every tick so the UI always has something to show.
    # The UI uses this to display time passing and update the minute clock.
    poss_team_id = state.home.id if attacking_home else state.away.id
    events.append(MatchEvent(
        minute=state.minute,
        event_type=MatchEventType.POSSESSION,
        team_id=poss_team_id,
    ))

    if attacking_home:
        atk_team, def_team = state.home, state.away
        atk_fatigue, def_fatigue = state.home_fatigue, state.away_fatigue
        atk_tactic, def_tactic = home_tactic, away_tactic
        atk_id, def_id = state.home.id, state.away.id
    else:
        atk_team, def_team = state.away, state.home
        atk_fatigue, def_fatigue = state.away_fatigue, state.home_fatigue
        atk_tactic, def_tactic = away_tactic, home_tactic
        atk_id, def_id = state.away.id, state.home.id

    atk_strength = _team_attack_strength(atk_team, atk_fatigue) * atk_tactic["attack"]
    def_strength = _team_defense_strength(def_team, def_fatigue) * def_tactic["defense"]

    # Action chain: build-up -> chance creation -> shot -> goal
    # Step 1: Build-up (does the attack create a chance?)
    chance_threshold = 30 + (atk_strength - def_strength) * 3
    chance_threshold = max(10, min(60, chance_threshold))

    roll = random.randint(1, 100)

    if roll <= chance_threshold:
        # Chance created
        shot_roll = random.randint(1, 100)

        # Select scorer and assister
        attackers = [
            p for p in atk_team.available_players
            if p.role in (PlayerRole.FWD, PlayerRole.MID)
        ]
        scorer = (
            random.choice(attackers)
            if attackers
            else random.choice(atk_team.available_players)
        )

        if shot_roll <= 20:
            # Corner kick
            if attacking_home:
                state.home_corners += 1
            else:
                state.away_corners += 1
            events.append(MatchEvent(
                minute=state.minute,
                event_type=MatchEventType.CORNER,
                team_id=atk_id,
                player_id=scorer.id,
            ))
        elif shot_roll <= 45:
            # Shot on target but saved
            if attacking_home:
                state.home_shots += 1
                state.home_shots_on_target += 1
            else:
                state.away_shots += 1
                state.away_shots_on_target += 1
            events.append(MatchEvent(
                minute=state.minute,
                event_type=MatchEventType.SHOT_SAVED,
                team_id=atk_id,
                player_id=scorer.id,
            ))
        elif shot_roll <= 60:
            # Shot wide
            if attacking_home:
                state.home_shots += 1
            else:
                state.away_shots += 1
            events.append(MatchEvent(
                minute=state.minute,
                event_type=MatchEventType.SHOT_WIDE,
                team_id=atk_id,
                player_id=scorer.id,
            ))
        elif shot_roll <= 70:
            # Hit the post
            if attacking_home:
                state.home_shots += 1
                state.home_shots_on_target += 1
            else:
                state.away_shots += 1
                state.away_shots_on_target += 1
            events.append(MatchEvent(
                minute=state.minute,
                event_type=MatchEventType.SHOT_POST,
                team_id=atk_id,
                player_id=scorer.id,
            ))
        else:
            # GOAL!
            goal_chance = 50 + (atk_strength - def_strength) * 4
            goal_chance = max(20, min(80, goal_chance))

            if random.randint(1, 100) <= goal_chance:
                if attacking_home:
                    state.home_goals += 1
                    state.home_shots += 1
                    state.home_shots_on_target += 1
                else:
                    state.away_goals += 1
                    state.away_shots += 1
                    state.away_shots_on_target += 1

                # Pick assister
                assist_candidates = [
                    p for p in atk_team.available_players
                    if p.id != scorer.id and p.role != PlayerRole.GK
                ]
                assister = random.choice(assist_candidates) if assist_candidates else None

                events.append(MatchEvent(
                    minute=state.minute,
                    event_type=MatchEventType.GOAL,
                    team_id=atk_id,
                    player_id=scorer.id,
                    assist_player_id=assister.id if assister else None,
                ))

                # Momentum shift after goal
                if attacking_home:
                    state.home_momentum = min(5.0, state.home_momentum + 2.0)
                    state.away_momentum = max(-3.0, state.away_momentum - 1.0)
                else:
                    state.away_momentum = min(5.0, state.away_momentum + 2.0)
                    state.home_momentum = max(-3.0, state.home_momentum - 1.0)
            else:
                # Great save
                if attacking_home:
                    state.home_shots += 1
                    state.home_shots_on_target += 1
                else:
                    state.away_shots += 1
                    state.away_shots_on_target += 1
                events.append(MatchEvent(
                    minute=state.minute,
                    event_type=MatchEventType.SHOT_SAVED,
                    team_id=atk_id,
                    player_id=scorer.id,
                ))

    # Check for fouls
    foul_chance = 15 + random.randint(-5, 5)
    if random.randint(1, 100) <= foul_chance:
        fouling_players = [
            p for p in def_team.available_players
            if p.role != PlayerRole.GK
        ]
        fouler = (
            random.choice(fouling_players)
            if fouling_players
            else random.choice(def_team.available_players)
        )

        if attacking_home:
            state.away_fouls += 1
        else:
            state.home_fouls += 1

        events.append(MatchEvent(
            minute=state.minute,
            event_type=MatchEventType.FOUL,
            team_id=def_id,
            player_id=fouler.id,
        ))

        # Check for card
        card_roll = random.randint(1, 100)
        if card_roll <= 5:
            # Red card (direct)
            events.append(MatchEvent(
                minute=state.minute,
                event_type=MatchEventType.RED_CARD,
                team_id=def_id,
                player_id=fouler.id,
            ))
        elif card_roll <= 20:
            # Yellow card
            events.append(MatchEvent(
                minute=state.minute,
                event_type=MatchEventType.YELLOW_CARD,
                team_id=def_id,
                player_id=fouler.id,
            ))

    # Update fatigue (amateur players tire faster)
    fatigue_rate = 0.02 if state.minute < state.rules.half_duration_minutes else 0.035
    state.home_fatigue = min(1.0, state.home_fatigue + fatigue_rate)
    state.away_fatigue = min(1.0, state.away_fatigue + fatigue_rate)

    # Momentum decay
    state.home_momentum *= 0.9
    state.away_momentum *= 0.9

    return events


def simulate_penalty_shootout(
    home: Team,
    away: Team,
    listeners: list[Callable[[MatchEvent], None]] | None = None,
) -> PenaltyShootout:
    """Simulate a penalty shootout (CSI rules: 5 penalties then sudden death)."""
    shootout = PenaltyShootout()

    # Select penalty takers (outfield players sorted by finishing)
    home_takers = sorted(
        [p for p in home.available_players if p.role != PlayerRole.GK],
        key=lambda p: p.attributes.technical.finishing,
        reverse=True,
    )
    away_takers = sorted(
        [p for p in away.available_players if p.role != PlayerRole.GK],
        key=lambda p: p.attributes.technical.finishing,
        reverse=True,
    )

    home_gk = next((p for p in home.available_players if p.role == PlayerRole.GK), None)
    away_gk = next((p for p in away.available_players if p.role == PlayerRole.GK), None)

    if not home_takers or not away_takers:
        return shootout

    def _emit(event: MatchEvent) -> None:
        if listeners:
            for listener in listeners:
                listener(event)

    def _take_penalty(taker: Player, gk: Player | None, team_id: UUID) -> bool:
        """Simulate a single penalty. Returns True if scored."""
        finishing = taker.attributes.technical.finishing
        gk_skill = 10.0
        if gk:
            gk_skill = (gk.attributes.goalkeeping.reflexes + gk.attributes.goalkeeping.handling) / 2

        # Base chance: 75% + (finishing - gk_skill) * 2%
        score_chance = 75 + (finishing - gk_skill) * 2
        score_chance = max(40, min(95, score_chance))

        scored = random.randint(1, 100) <= score_chance

        if scored:
            _emit(MatchEvent(
                minute=90, event_type=MatchEventType.PENALTY_SCORED,
                team_id=team_id, player_id=taker.id,
            ))
        else:
            event_type = (
                MatchEventType.PENALTY_SAVED
                if random.random() < 0.6
                else MatchEventType.PENALTY_MISSED
            )
            _emit(MatchEvent(
                minute=90, event_type=event_type,
                team_id=team_id, player_id=taker.id,
            ))

        return scored

    _emit(MatchEvent(
        minute=90, event_type=MatchEventType.PENALTY_SHOOTOUT_START,
        team_id=home.id,
    ))

    # First 5 rounds
    for i in range(5):
        home_taker = home_takers[i % len(home_takers)]
        scored = _take_penalty(home_taker, away_gk, home.id)
        shootout.home_scores.append(scored)

        away_taker = away_takers[i % len(away_takers)]
        scored = _take_penalty(away_taker, home_gk, away.id)
        shootout.away_scores.append(scored)

        # Check if shootout is decided early
        remaining = 4 - i
        if shootout.home_goals - shootout.away_goals > remaining:
            break
        if shootout.away_goals - shootout.home_goals > remaining:
            break

    # Sudden death if tied
    round_idx = 5
    while shootout.home_goals == shootout.away_goals:
        home_taker = home_takers[round_idx % len(home_takers)]
        scored = _take_penalty(home_taker, away_gk, home.id)
        shootout.home_scores.append(scored)

        away_taker = away_takers[round_idx % len(away_takers)]
        scored = _take_penalty(away_taker, home_gk, away.id)
        shootout.away_scores.append(scored)

        round_idx += 1

        # Safety valve to prevent infinite loop
        if round_idx > 20:
            break

    return shootout


class MatchEngine:
    """Simulates a complete match between two teams."""

    def __init__(self) -> None:
        self._listeners: list[Callable[[MatchEvent], None]] = []

    def add_listener(self, callback: Callable[[MatchEvent], None]) -> None:
        """Register a listener for match events."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[MatchEvent], None]) -> None:
        """Remove a registered listener."""
        self._listeners.remove(callback)

    def _emit(self, event: MatchEvent) -> None:
        """Emit an event to all registered listeners."""
        for listener in self._listeners:
            listener(event)

    def simulate(
        self, home: Team, away: Team, rules: CompetitionRules
    ) -> Match:
        """Simulate a complete match and return the result."""
        state = MatchState(home, away, rules)
        match = Match(
            home_team_id=home.id,
            away_team_id=away.id,
            competition_id=home.id,  # Placeholder, set by caller
        )

        # Check for forfeit
        if not home.can_play:
            match.played = True
            match.score = MatchScore(home_goals=0, away_goals=3)
            match.result = MatchResult.FORFEIT_HOME
            return match
        if not away.can_play:
            match.played = True
            match.score = MatchScore(home_goals=3, away_goals=0)
            match.result = MatchResult.FORFEIT_AWAY
            return match

        # Kick off
        self._emit(MatchEvent(
            minute=0, event_type=MatchEventType.KICK_OFF, team_id=home.id,
        ))

        # First half
        half_duration = rules.half_duration_minutes
        for minute in range(1, half_duration + 1):
            state.minute = minute
            tick_events = _simulate_tick(state)
            for event in tick_events:
                state.events.append(event)
                self._emit(event)

        # Half time
        self._emit(MatchEvent(
            minute=half_duration, event_type=MatchEventType.HALF_TIME,
        ))

        # Reset fatigue partially at half time (amateur players recover some)
        state.home_fatigue *= 0.5
        state.away_fatigue *= 0.5
        state.home_timeouts = rules.timeout_per_half
        state.away_timeouts = rules.timeout_per_half

        # Second half
        for minute in range(half_duration + 1, half_duration * 2 + 1):
            state.minute = minute
            tick_events = _simulate_tick(state)
            for event in tick_events:
                state.events.append(event)
                self._emit(event)

        # Full time
        self._emit(MatchEvent(
            minute=half_duration * 2, event_type=MatchEventType.FULL_TIME,
        ))

        # Build match result
        match.played = True
        match.events = state.events
        match.home_possession = round(state.home_possession, 1)
        match.away_possession = round(state.away_possession, 1)
        match.home_shots = state.home_shots
        match.away_shots = state.away_shots
        match.home_shots_on_target = state.home_shots_on_target
        match.away_shots_on_target = state.away_shots_on_target
        match.home_fouls = state.home_fouls
        match.away_fouls = state.away_fouls
        match.home_corners = state.home_corners
        match.away_corners = state.away_corners

        score = MatchScore(home_goals=state.home_goals, away_goals=state.away_goals)

        if state.home_goals > state.away_goals:
            match.result = MatchResult.HOME_WIN
        elif state.away_goals > state.home_goals:
            match.result = MatchResult.AWAY_WIN
        elif rules.penalties_after_draw:
            # CSI rule: penalties after every draw
            shootout = simulate_penalty_shootout(home, away, self._listeners)
            score.penalty_shootout = shootout
            if shootout.home_goals > shootout.away_goals:
                match.result = MatchResult.HOME_WIN_PENALTIES
            else:
                match.result = MatchResult.AWAY_WIN_PENALTIES

        match.score = score
        return match
