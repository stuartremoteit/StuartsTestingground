"""
Data models for the SF Giants stat tracker.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BattingLine:
    player: str
    position: str
    pa: int = 0      # plate appearances
    ab: int = 0      # at bats
    r: int = 0       # runs
    h: int = 0       # hits
    doubles: int = 0
    triples: int = 0
    hr: int = 0      # home runs
    rbi: int = 0     # runs batted in
    bb: int = 0      # walks
    k: int = 0       # strikeouts
    hbp: int = 0     # hit by pitch
    sb: int = 0      # stolen bases


@dataclass
class PitchingLine:
    player: str
    ip: float = 0.0  # innings pitched
    h: int = 0       # hits allowed
    r: int = 0       # runs allowed
    er: int = 0      # earned runs
    bb: int = 0      # walks
    k: int = 0       # strikeouts
    hr: int = 0      # home runs allowed
    decision: Optional[str] = None   # W, L, S, H, BS, or None
    blown_save: bool = False


@dataclass
class Game:
    date: str                         # YYYY-MM-DD
    opponent: str
    location: str                     # "home" or "away"
    venue: str
    result: str                       # "W" or "L"
    giants_score: int = 0
    opponent_score: int = 0
    batting: list = field(default_factory=list)
    pitching: list = field(default_factory=list)
    notes: str = ""

    @property
    def is_win(self) -> bool:
        return self.result == "W"


@dataclass
class PlayerBattingStats:
    name: str
    position: str
    games: int = 0
    pa: int = 0
    ab: int = 0
    r: int = 0
    h: int = 0
    doubles: int = 0
    triples: int = 0
    hr: int = 0
    rbi: int = 0
    bb: int = 0
    k: int = 0
    hbp: int = 0
    sb: int = 0

    @property
    def avg(self) -> float:
        return self.h / self.ab if self.ab > 0 else 0.0

    @property
    def obp(self) -> float:
        denom = self.ab + self.bb + self.hbp
        return (self.h + self.bb + self.hbp) / denom if denom > 0 else 0.0

    @property
    def slg(self) -> float:
        tb = self.h + self.doubles + (2 * self.triples) + (3 * self.hr)
        return tb / self.ab if self.ab > 0 else 0.0

    @property
    def ops(self) -> float:
        return self.obp + self.slg


@dataclass
class PlayerPitchingStats:
    name: str
    games: int = 0
    wins: int = 0
    losses: int = 0
    saves: int = 0
    holds: int = 0
    blown_saves: int = 0
    ip: float = 0.0
    h: int = 0
    r: int = 0
    er: int = 0
    bb: int = 0
    k: int = 0
    hr: int = 0

    @property
    def era(self) -> float:
        return (self.er * 9) / self.ip if self.ip > 0 else 0.0

    @property
    def whip(self) -> float:
        return (self.bb + self.h) / self.ip if self.ip > 0 else 0.0

    @property
    def k9(self) -> float:
        return (self.k * 9) / self.ip if self.ip > 0 else 0.0
