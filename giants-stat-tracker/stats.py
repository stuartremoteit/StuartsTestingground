"""
Stats aggregation and display for the SF Giants stat tracker.
"""

import json
import os
from models import PlayerBattingStats, PlayerPitchingStats

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "games.json")


def load_games(filepath=DATA_FILE):
    with open(filepath) as f:
        return json.load(f)


def save_games(games, filepath=DATA_FILE):
    with open(filepath, "w") as f:
        json.dump(games, f, indent=2)


# ── Aggregation ────────────────────────────────────────────────────────────────

def aggregate_batting(games):
    """Return dict of player_name -> PlayerBattingStats accumulated across games."""
    players = {}
    for game in games:
        for line in game.get("batting", []):
            name = line["player"]
            if name not in players:
                players[name] = PlayerBattingStats(name=name, position=line["position"])
            p = players[name]
            p.games   += 1
            p.pa      += line.get("pa", 0)
            p.ab      += line.get("ab", 0)
            p.r       += line.get("r", 0)
            p.h       += line.get("h", 0)
            p.doubles += line.get("doubles", 0)
            p.triples += line.get("triples", 0)
            p.hr      += line.get("hr", 0)
            p.rbi     += line.get("rbi", 0)
            p.bb      += line.get("bb", 0)
            p.k       += line.get("k", 0)
            p.hbp     += line.get("hbp", 0)
            p.sb      += line.get("sb", 0)
    return players


def aggregate_pitching(games):
    """Return dict of player_name -> PlayerPitchingStats accumulated across games."""
    players = {}
    for game in games:
        for line in game.get("pitching", []):
            name = line["player"]
            if name not in players:
                players[name] = PlayerPitchingStats(name=name)
            p = players[name]
            p.games += 1
            p.ip    += line.get("ip", 0)
            p.h     += line.get("h", 0)
            p.r     += line.get("r", 0)
            p.er    += line.get("er", 0)
            p.bb    += line.get("bb", 0)
            p.k     += line.get("k", 0)
            p.hr    += line.get("hr", 0)
            decision = line.get("decision")
            if decision == "W":
                p.wins += 1
            elif decision == "L":
                p.losses += 1
            elif decision == "S":
                p.saves += 1
            elif decision == "H":
                p.holds += 1
            if line.get("blown_save"):
                p.blown_saves += 1
    return players


def season_record(games):
    wins   = sum(1 for g in games if g["result"] == "W")
    losses = sum(1 for g in games if g["result"] == "L")
    return wins, losses


# ── Display helpers ────────────────────────────────────────────────────────────

def _pct(val):
    """Format a batting average / OBP / SLG."""
    return f"{val:.3f}".lstrip("0") if val < 1 else f"{val:.3f}"


def _ip(val):
    """Format innings pitched with fractional outs (e.g. 6.2 not 6.67)."""
    whole = int(val)
    frac  = round((val - whole) * 3)   # 0.333… -> 1 out, 0.667… -> 2 outs
    return f"{whole}.{frac}" if frac else f"{whole}.0"


DIVIDER = "─" * 90


def print_banner():
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║   SAN FRANCISCO GIANTS  ·  2026 SEASON TRACKER  ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()


def print_record(games):
    w, l = season_record(games)
    total = w + l
    pct   = w / total if total else 0
    gb_label = f"  {w}–{l}  ({pct:.3f})"
    print(f"  Season Record: {gb_label}")
    print()


def print_game_log(games):
    print(DIVIDER)
    print(f"  {'GAME LOG':^88}")
    print(DIVIDER)
    header = f"  {'#':>3}  {'DATE':<12} {'OPP':<22} {'LOC':<5} {'SCORE':>7}  {'W/L'}"
    print(header)
    print(DIVIDER)
    for i, g in enumerate(games, 1):
        loc_str = "Home" if g["location"] == "home" else "Away"
        score   = f"{g['giants_score']}-{g['opponent_score']}"
        print(f"  {i:>3}  {g['date']:<12} {g['opponent']:<22} {loc_str:<5} {score:>7}   {g['result']}")
    print(DIVIDER)
    print()


def print_batting(games):
    players = aggregate_batting(games)
    rows    = sorted(players.values(), key=lambda p: p.ab, reverse=True)

    print(DIVIDER)
    print(f"  {'BATTING STATS':^88}")
    print(DIVIDER)
    hdr = (f"  {'PLAYER':<22} {'POS':<4} {'G':>3} {'AB':>4} {'R':>4} {'H':>4}"
           f" {'2B':>3} {'3B':>3} {'HR':>3} {'RBI':>4} {'BB':>3} {'K':>4}"
           f" {'SB':>3} {'AVG':>6} {'OBP':>6} {'SLG':>6} {'OPS':>6}")
    print(hdr)
    print(DIVIDER)
    for p in rows:
        print(f"  {p.name:<22} {p.position:<4} {p.games:>3} {p.ab:>4} {p.r:>4} {p.h:>4}"
              f" {p.doubles:>3} {p.triples:>3} {p.hr:>3} {p.rbi:>4} {p.bb:>3} {p.k:>4}"
              f" {p.sb:>3} {_pct(p.avg):>6} {_pct(p.obp):>6} {_pct(p.slg):>6} {_pct(p.ops):>6}")
    print(DIVIDER)
    print()


def print_pitching(games):
    players = aggregate_pitching(games)
    rows    = sorted(players.values(), key=lambda p: p.ip, reverse=True)

    print(DIVIDER)
    print(f"  {'PITCHING STATS':^88}")
    print(DIVIDER)
    hdr = (f"  {'PLAYER':<22} {'G':>3} {'W':>3} {'L':>3} {'SV':>3} {'IP':>6}"
           f" {'H':>4} {'R':>4} {'ER':>4} {'BB':>4} {'K':>4} {'HR':>3}"
           f" {'ERA':>6} {'WHIP':>6} {'K/9':>5}")
    print(hdr)
    print(DIVIDER)
    for p in rows:
        era  = f"{p.era:.2f}"  if p.ip > 0 else "---"
        whip = f"{p.whip:.2f}" if p.ip > 0 else "---"
        k9   = f"{p.k9:.1f}"   if p.ip > 0 else "---"
        print(f"  {p.name:<22} {p.games:>3} {p.wins:>3} {p.losses:>3} {p.saves:>3} {_ip(p.ip):>6}"
              f" {p.h:>4} {p.r:>4} {p.er:>4} {p.bb:>4} {p.k:>4} {p.hr:>3}"
              f" {era:>6} {whip:>6} {k9:>5}")
    print(DIVIDER)
    print()


def print_game_detail(game):
    result_str = "WIN" if game["result"] == "W" else "LOSS"
    score      = f"{game['giants_score']}-{game['opponent_score']}"
    print()
    print(DIVIDER)
    venue_str  = f"{game['venue']}  ({'Home' if game['location'] == 'home' else 'Away'})"
    print(f"  {game['date']}  vs  {game['opponent']}  |  {result_str} {score}  |  {venue_str}")
    if game.get("notes"):
        print(f"  {game['notes']}")
    print(DIVIDER)

    # Batting box
    print(f"  {'BATTING':<22} {'POS':<4} {'AB':>3} {'R':>3} {'H':>3} {'2B':>3}"
          f" {'HR':>3} {'RBI':>4} {'BB':>3} {'K':>3} {'SB':>3}")
    print("  " + "·" * 70)
    for b in game["batting"]:
        print(f"  {b['player']:<22} {b['position']:<4} {b['ab']:>3} {b['r']:>3} {b['h']:>3}"
              f" {b['doubles']:>3} {b['hr']:>3} {b['rbi']:>4} {b['bb']:>3} {b['k']:>3} {b['sb']:>3}")
    print()

    # Pitching box
    print(f"  {'PITCHING':<22} {'IP':>6} {'H':>3} {'R':>3} {'ER':>3} {'BB':>3} {'K':>3} {'DEC':>4}")
    print("  " + "·" * 60)
    for p in game["pitching"]:
        dec = p.get("decision") or "-"
        print(f"  {p['player']:<22} {_ip(p['ip']):>6} {p['h']:>3} {p['r']:>3}"
              f" {p['er']:>3} {p['bb']:>3} {p['k']:>3} {dec:>4}")
    print(DIVIDER)
    print()
