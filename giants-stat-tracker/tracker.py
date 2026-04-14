#!/usr/bin/env python3
"""
SF Giants Day-by-Day Stat Tracker  ·  2025 Season
Usage:
  python tracker.py              — full dashboard (record + log + batting + pitching)
  python tracker.py log          — season game log only
  python tracker.py batting      — season batting stats
  python tracker.py pitching     — season pitching stats
  python tracker.py game <N>     — detail view for game #N (1-indexed)
  python tracker.py add          — interactive wizard to add a new game
"""

import sys
import json
from stats import (
    load_games, save_games,
    print_banner, print_record, print_game_log,
    print_batting, print_pitching, print_game_detail,
)


# ── Add-game wizard ────────────────────────────────────────────────────────────

def _ask(prompt, cast=str, default=None):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"  {prompt}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        try:
            return cast(raw)
        except ValueError:
            print(f"    Invalid input, expected {cast.__name__}.")


def collect_batting_lines():
    lines = []
    print("\n  Enter batting lines (blank player name to finish):")
    while True:
        name = input("    Player name: ").strip()
        if not name:
            break
        pos    = input("    Position: ").strip().upper()
        pa     = _ask("    PA",       cast=int, default=0)
        ab     = _ask("    AB",       cast=int, default=pa)
        r      = _ask("    R",        cast=int, default=0)
        h      = _ask("    H",        cast=int, default=0)
        db     = _ask("    2B",       cast=int, default=0)
        tb     = _ask("    3B",       cast=int, default=0)
        hr     = _ask("    HR",       cast=int, default=0)
        rbi    = _ask("    RBI",      cast=int, default=0)
        bb     = _ask("    BB",       cast=int, default=0)
        k      = _ask("    K",        cast=int, default=0)
        hbp    = _ask("    HBP",      cast=int, default=0)
        sb     = _ask("    SB",       cast=int, default=0)
        lines.append({
            "player": name, "position": pos,
            "pa": pa, "ab": ab, "r": r, "h": h,
            "doubles": db, "triples": tb, "hr": hr,
            "rbi": rbi, "bb": bb, "k": k, "hbp": hbp, "sb": sb,
        })
    return lines


def collect_pitching_lines():
    lines = []
    print("\n  Enter pitching lines (blank player name to finish):")
    while True:
        name = input("    Player name: ").strip()
        if not name:
            break
        ip  = _ask("    IP (e.g. 6.2)", cast=float, default=0.0)
        h   = _ask("    H",             cast=int,   default=0)
        r   = _ask("    R",             cast=int,   default=0)
        er  = _ask("    ER",            cast=int,   default=r)
        bb  = _ask("    BB",            cast=int,   default=0)
        k   = _ask("    K",             cast=int,   default=0)
        hr  = _ask("    HR",            cast=int,   default=0)
        dec = input("    Decision (W/L/S/H or blank): ").strip().upper() or None
        bs  = input("    Blown save? (y/N): ").strip().lower() == "y"
        lines.append({
            "player": name, "ip": ip, "h": h, "r": r, "er": er,
            "bb": bb, "k": k, "hr": hr,
            "decision": dec, "blown_save": bs,
        })
    return lines


def add_game(games):
    print("\n  ── Add New Game ──────────────────────────────────────")
    date     = _ask("Date (YYYY-MM-DD)")
    opponent = _ask("Opponent")
    location = ""
    while location not in ("home", "away"):
        location = input("  Location (home/away): ").strip().lower()
    venue    = _ask("Venue")
    result   = ""
    while result not in ("W", "L"):
        result = input("  Result (W/L): ").strip().upper()
    gscore   = _ask("Giants score", cast=int)
    oscore   = _ask("Opponent score", cast=int)
    notes    = _ask("Notes (optional)", default="")
    batting  = collect_batting_lines()
    pitching = collect_pitching_lines()

    game = {
        "date": date, "opponent": opponent,
        "location": location, "venue": venue,
        "result": result,
        "giants_score": gscore, "opponent_score": oscore,
        "notes": notes,
        "batting": batting, "pitching": pitching,
    }
    games.append(game)
    games.sort(key=lambda g: g["date"])
    save_games(games)
    print(f"\n  Game saved. Giants now {sum(g['result']=='W' for g in games)}"
          f"–{sum(g['result']=='L' for g in games)}.\n")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    games = load_games()
    args  = sys.argv[1:]
    cmd   = args[0].lower() if args else "all"

    print_banner()

    if cmd == "all":
        print_record(games)
        print_game_log(games)
        print_batting(games)
        print_pitching(games)

    elif cmd == "log":
        print_record(games)
        print_game_log(games)

    elif cmd == "batting":
        print_record(games)
        print_batting(games)

    elif cmd == "pitching":
        print_record(games)
        print_pitching(games)

    elif cmd == "game":
        if len(args) < 2:
            print("  Usage: python tracker.py game <N>")
            sys.exit(1)
        idx = int(args[1]) - 1
        if idx < 0 or idx >= len(games):
            print(f"  Game #{idx+1} not found. There are {len(games)} games.")
            sys.exit(1)
        print_record(games)
        print_game_detail(games[idx])

    elif cmd == "add":
        add_game(games)

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
