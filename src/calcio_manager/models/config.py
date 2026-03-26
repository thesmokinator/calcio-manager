"""Game configuration models parametrized by CSI rules."""

from pydantic import BaseModel

from calcio_manager.models.enums import AgeCategory, GameFormat


class CompetitionRules(BaseModel):
    """Rules for a CSI competition, parametrized by category and format."""

    format: GameFormat = GameFormat.C7
    category: AgeCategory = AgeCategory.OPEN

    # Match duration
    half_duration_minutes: int = 25
    num_periods: int = 2  # 2 for most, 4 for Under 12

    # Players
    players_on_pitch: int = 7
    min_players_to_play: int = 4
    max_squad_size: int = 14

    # Points system (CSI: penalties after every draw)
    points_win: int = 3
    points_win_penalties: int = 2
    points_loss_penalties: int = 1
    points_loss: int = 0
    penalties_after_draw: bool = True

    # Substitutions
    unlimited_subs: bool = True
    rolling_subs: bool = False  # True for C5, False for C7

    # Rules
    offside: bool = False
    timeout_per_half: int = 1  # C7 has 1 timeout per half
    timeout_duration_minutes: int = 2

    # Penalty after red card
    numerical_inferiority_minutes: int = 0  # 0 for C7, 2 for C5

    @classmethod
    def for_category(
        cls,
        category: AgeCategory,
        fmt: GameFormat = GameFormat.C7,
    ) -> "CompetitionRules":
        """Create rules appropriate for a given CSI age category and format."""
        base = cls(format=fmt, category=category)

        # C7-specific overrides by category
        if fmt == GameFormat.C7:
            if category in (AgeCategory.OPEN, AgeCategory.MASTER_30):
                base.half_duration_minutes = 25
            elif category in (
                AgeCategory.MASTER_40,
                AgeCategory.JUNIORES,
                AgeCategory.ALLIEVI,
            ):
                base.half_duration_minutes = 20
            elif category == AgeCategory.UNDER_14:
                base.half_duration_minutes = 15
            elif category == AgeCategory.UNDER_12:
                base.half_duration_minutes = 8
                base.num_periods = 4

        # C5-specific overrides
        elif fmt == GameFormat.C5:
            base.players_on_pitch = 5
            base.min_players_to_play = 3
            base.half_duration_minutes = 20
            base.rolling_subs = True
            base.timeout_per_half = 0
            base.numerical_inferiority_minutes = 2

        return base


class GameConfig(BaseModel):
    """Top-level configuration for a new game."""

    format: GameFormat = GameFormat.C7
    category: AgeCategory = AgeCategory.OPEN
    province: str = "Varese"
    region: str = "Lombardia"
    num_groups: int = 1
    teams_per_group: int = 8
    season_year: str = "2025-2026"
    rules: CompetitionRules = CompetitionRules()

    def model_post_init(self, __context: object) -> None:
        """Set rules based on category and format if not explicitly provided."""
        self.rules = CompetitionRules.for_category(self.category, self.format)
