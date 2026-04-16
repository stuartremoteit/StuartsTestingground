#!/usr/bin/env python3
"""
San Francisco Giants 2026 Season Stat Tracker
Day-by-day results from Opening Day.

Data source: MLB Stats API (https://statsapi.mlb.com/api/v1)
Falls back to bundled sample_data.json when the API is unreachable.
Run with --live to force live API (requires network access to MLB servers).
"""

import sys
import os
import json
import datetime
import argparse
import textwrap

BASE_URL = "https://statsapi.mlb.com/api/v1"
GIANTS_ID = 137
SEASON = 2026
OPENING_DAY = datetime.date(2026, 3, 27)

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "sample_data.json")


# ── colour helpers ──────────────────────────────────────────────────────────

def _clr(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"

def green(t):  return _clr("32;1", t)
def red(t):    return _clr("31;1", t)
def yellow(t): return _clr("33;1", t)
def cyan(t):   return _clr("36;1", t)
def bold(t):   return _clr("1", t)


# ── simple table printer (no external deps) ─────────────────────────────────

def table(rows: list, headers: list, *, align: dict = None) -> str:
    align = align or {}
    cols = len(headers)
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_row(row, is_header=False):
        parts = []
        for i, cell in enumerate(row):
            s = str(cell)
            a = align.get(i, "left")
            if a == "right":
                s = s.rjust(widths[i])
            else:
                s = s.ljust(widths[i])
            parts.append(s)
        sep = "  "
        return sep.join(parts)

    sep_line = "  ".join("─" * w for w in widths)
    lines = [fmt_row(headers, is_header=True), sep_line]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


# ── MLB Stats API ────────────────────────────────────────────────────────────

def _api_get(endpoint: str, params: dict = None) -> dict:
    try:
        import requests
        resp = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise RuntimeError(f"MLB API error: {exc}") from exc


def _live_schedule(start: datetime.date, end: datetime.date) -> list:
    data = _api_get("/schedule", params={
        "sportId": 1,
        "teamId": GIANTS_ID,
        "season": SEASON,
        "startDate": start.strftime("%Y-%m-%d"),
        "endDate": end.strftime("%Y-%m-%d"),
        "hydrate": "decisions,linescore,team",
        "gameType": "R",
    })
    games = []
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            games.append(_parse_live_game(g))
    return games


def _parse_live_game(game: dict) -> dict:
    gm = {
        "game_pk": game.get("gamePk"),
        "date": game.get("officialDate", ""),
        "status": game.get("status", {}).get("abstractGameState", ""),
    }
    teams = game.get("teams", {})
    away, home = teams.get("away", {}), teams.get("home", {})
    away_name = away.get("team", {}).get("name", "")
    home_name = home.get("team", {}).get("name", "")

    if home_name == "San Francisco Giants":
        gm["opponent"] = away_name
        gm["home_away"] = "HOME"
        gm["giants_score"] = home.get("score")
        gm["opp_score"] = away.get("score")
        gm["giants_record"] = home.get("leagueRecord", {})
    else:
        gm["opponent"] = home_name
        gm["home_away"] = "AWAY"
        gm["giants_score"] = away.get("score")
        gm["opp_score"] = home.get("score")
        gm["giants_record"] = away.get("leagueRecord", {})

    if gm["status"] == "Final":
        gs, os_ = gm["giants_score"], gm["opp_score"]
        gm["result"] = "W" if (gs is not None and os_ is not None and gs > os_) else "L"
    elif gm["status"] == "Live":
        gm["result"] = "LIVE"
    else:
        gm["result"] = "-"

    decisions = game.get("decisions") or {}
    gm["winning_pitcher"] = decisions.get("winner", {}).get("fullName", "")
    gm["losing_pitcher"]  = decisions.get("loser", {}).get("fullName", "")
    gm["save"]            = decisions.get("save", {}).get("fullName", "")

    rec = gm["giants_record"]
    gm["record"] = f"{rec.get('wins',0)}-{rec.get('losses',0)}" if rec else ""
    return gm


def _live_roster_stats(group: str) -> list:
    data = _api_get("/stats", params={
        "stats": "season",
        "group": group,
        "teamId": GIANTS_ID,
        "season": SEASON,
        "sportId": 1,
        "limit": 40,
    })
    return data.get("stats", [{}])[0].get("splits", [])


# ── sample data loader ───────────────────────────────────────────────────────

def _load_sample() -> dict:
    if not os.path.exists(SAMPLE_FILE):
        sys.exit(f"Error: {SAMPLE_FILE} not found. Cannot run without data.")
    with open(SAMPLE_FILE) as f:
        return json.load(f)


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_schedule(args):
    today = datetime.date.today()
    end = min(today, datetime.date(2026, 10, 5))

    print()
    print(bold("=" * 72))
    print(bold("  SAN FRANCISCO GIANTS  ⚾  2026 SEASON"))
    print(bold(f"  Opening Day: {OPENING_DAY}  |  Data through: {end}"))
    print(bold("=" * 72))

    if args.live:
        print("  Fetching live schedule from MLB Stats API...\n")
        try:
            games = _live_schedule(OPENING_DAY, end)
            source = "MLB Stats API (live)"
        except RuntimeError as e:
            print(f"  {yellow('WARNING:')} {e}")
            print("  Falling back to sample data.\n")
            games = _load_sample()["games"]
            source = "sample_data.json"
    else:
        games = _load_sample()["games"]
        source = "sample_data.json (use --live for real data)"

    rows = []
    for g in games:
        res = g.get("result", "-")
        score = ""
        if res in ("W", "L") and g.get("giants_score") is not None:
            score = f"{g['giants_score']}-{g['opp_score']}"
        elif res == "LIVE":
            score = f"{g.get('giants_score', '?')}-{g.get('opp_score', '?')} ●"

        if res == "W":
            res_display = green("W")
        elif res == "L":
            res_display = red("L")
        elif res == "LIVE":
            res_display = yellow("LIVE")
        else:
            res_display = res

        loc = "vs" if g["home_away"] == "HOME" else " @"
        note = g.get("note", "")
        opp_col = f"{loc} {g['opponent']}"
        if note:
            opp_col += f"  [{note}]"

        dec = g.get("winning_pitcher", "") if res == "W" else g.get("losing_pitcher", "")
        sv  = g.get("save", "")
        dec_col = f"W: {g.get('winning_pitcher','')}  L: {g.get('losing_pitcher','')}"
        if sv:
            dec_col += f"  SV: {sv}"

        rows.append([
            g["date"],
            opp_col,
            res_display,
            score,
            g.get("record", ""),
            dec_col,
        ])

    headers = ["Date", "Opponent", "R", "Score", "Rec", "Decision"]
    print(table(rows, headers))

    completed = [g for g in games if g.get("result") in ("W", "L")]
    wins = sum(1 for g in completed if g["result"] == "W")
    losses = len(completed) - wins
    pct = wins / len(completed) if completed else 0
    print()
    print(bold(f"  Thru {today}:  {wins}-{losses}  ({pct:.3f})  |  {len(completed)} games played"))
    print(f"  Source: {source}")
    print()


def cmd_today(args):
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")

    if args.live:
        try:
            games = _live_schedule(today, today)
            source = "live"
        except RuntimeError as e:
            print(f"\n  {yellow('WARNING:')} {e} — checking sample data.")
            games = [g for g in _load_sample()["games"] if g["date"] == today_str]
            source = "sample"
    else:
        games = [g for g in _load_sample()["games"] if g["date"] == today_str]
        source = "sample"

    print()
    print(bold(f"  SF Giants  —  {today_str}"))
    print(bold("  " + "─" * 60))

    if not games:
        print("  No Giants game today (off day or date not in data).")
        print()
        return

    for g in games:
        res = g.get("result", "-")
        loc = "vs" if g["home_away"] == "HOME" else "@"
        print(f"  {g['date']}  {bold('Giants')} {loc} {g['opponent']}")
        if res in ("W", "L"):
            colour = green if res == "W" else red
            print(f"  Final: Giants {g['giants_score']}, {g['opponent']} {g['opp_score']}  "
                  f"→  {colour(res)}  {g.get('record', '')}")
            wp = g.get("winning_pitcher", "")
            lp = g.get("losing_pitcher", "")
            sv = g.get("save", "")
            line = f"  W: {wp}  |  L: {lp}"
            if sv:
                line += f"  |  SV: {sv}"
            print(line)
        elif res == "LIVE":
            print(f"  In progress: Giants {g.get('giants_score','?')}, "
                  f"{g['opponent']} {g.get('opp_score','?')}")
        else:
            print(f"  Status: {res}")

    print(f"\n  [{source} data]")
    print()


def cmd_hitting(args):
    print()
    print(bold("=" * 72))
    print(bold("  SAN FRANCISCO GIANTS  ⚾  2026 SEASON BATTING"))
    print(bold("=" * 72))

    if args.live:
        print("  Fetching live hitting stats...\n")
        try:
            splits = _live_roster_stats("hitting")
            rows = []
            for s in splits:
                p = s.get("player", {})
                st = s.get("stat", {})
                rows.append([
                    p.get("fullName", ""),
                    s.get("position", {}).get("abbreviation", ""),
                    st.get("gamesPlayed", 0),
                    st.get("atBats", 0),
                    st.get("hits", 0),
                    st.get("doubles", 0),
                    st.get("homeRuns", 0),
                    st.get("rbi", 0),
                    st.get("runs", 0),
                    st.get("baseOnBalls", 0),
                    st.get("strikeOuts", 0),
                    st.get("stolenBases", 0),
                    st.get("avg", ".000"),
                    st.get("obp", ".000"),
                    st.get("slg", ".000"),
                    st.get("ops", ".000"),
                ])
            rows.sort(key=lambda r: int(r[3]) if str(r[3]).isdigit() else 0, reverse=True)
            source = "MLB Stats API (live)"
        except RuntimeError as e:
            print(f"  {yellow('WARNING:')} {e} — falling back to sample data.\n")
            rows = _hitting_rows_from_sample()
            source = "sample_data.json"
    else:
        rows = _hitting_rows_from_sample()
        source = "sample_data.json (use --live for real data)"

    headers = ["Player", "Pos", "G", "AB", "H", "2B", "HR", "RBI", "R", "BB", "K", "SB",
               "AVG", "OBP", "SLG", "OPS"]
    right_cols = {i: "right" for i in range(2, 16)}
    print(table(rows, headers, align=right_cols))
    print(f"\n  Source: {source}")
    print()


def _hitting_rows_from_sample() -> list:
    data = _load_sample()
    rows = []
    for p in data["hitting_stats"]:
        rows.append([
            p["name"], p["pos"], p["g"], p["ab"], p["h"],
            p["2b"], p["hr"], p["rbi"], p["r"], p["bb"],
            p["k"], p["sb"], p["avg"], p["obp"], p["slg"], p["ops"],
        ])
    rows.sort(key=lambda r: int(r[3]) if str(r[3]).isdigit() else 0, reverse=True)
    return rows


def cmd_pitching(args):
    print()
    print(bold("=" * 72))
    print(bold("  SAN FRANCISCO GIANTS  ⚾  2026 SEASON PITCHING"))
    print(bold("=" * 72))

    if args.live:
        print("  Fetching live pitching stats...\n")
        try:
            splits = _live_roster_stats("pitching")
            rows = []
            for s in splits:
                p = s.get("player", {})
                st = s.get("stat", {})
                rows.append([
                    p.get("fullName", ""),
                    st.get("gamesPlayed", 0),
                    st.get("gamesStarted", 0),
                    st.get("wins", 0),
                    st.get("losses", 0),
                    st.get("saves", 0),
                    st.get("inningsPitched", "0.0"),
                    st.get("hits", 0),
                    st.get("earnedRuns", 0),
                    st.get("baseOnBalls", 0),
                    st.get("strikeOuts", 0),
                    st.get("era", "-.--"),
                    st.get("whip", "-.--"),
                ])
            rows.sort(key=lambda r: float(r[6]) if str(r[6]).replace(".", "").isdigit() else 0,
                      reverse=True)
            source = "MLB Stats API (live)"
        except RuntimeError as e:
            print(f"  {yellow('WARNING:')} {e} — falling back to sample data.\n")
            rows = _pitching_rows_from_sample()
            source = "sample_data.json"
    else:
        rows = _pitching_rows_from_sample()
        source = "sample_data.json (use --live for real data)"

    headers = ["Player", "G", "GS", "W", "L", "SV", "IP", "H", "ER", "BB", "K", "ERA", "WHIP"]
    right_cols = {i: "right" for i in range(1, 13)}
    print(table(rows, headers, align=right_cols))
    print(f"\n  Source: {source}")
    print()


def _pitching_rows_from_sample() -> list:
    data = _load_sample()
    rows = []
    for p in data["pitching_stats"]:
        rows.append([
            p["name"], p["g"], p["gs"], p["w"], p["l"], p["sv"],
            p["ip"], p["h"], p["er"], p["bb"], p["k"], p["era"], p["whip"],
        ])
    rows.sort(key=lambda r: float(r[6]) if str(r[6]).replace(".", "").isdigit() else 0,
              reverse=True)
    return rows


def cmd_summary(args):
    """Print a full-season summary: record + key stat leaders."""
    data = _load_sample()
    games = data["games"]
    completed = [g for g in games if g.get("result") in ("W", "L")]
    wins = sum(1 for g in completed if g["result"] == "W")
    losses = len(completed) - wins
    today = datetime.date.today()

    print()
    print(bold("╔" + "═" * 70 + "╗"))
    print(bold("║") + cyan("  SAN FRANCISCO GIANTS — 2026 SEASON SUMMARY".center(70)) + bold("║"))
    print(bold("╠" + "═" * 70 + "╣"))

    def row(label, val):
        print(bold("║") + f"  {label:<28}{str(val):<40}" + bold("║"))

    row("Through:", str(today))
    row("Record:", f"{wins}-{losses}  ({wins/len(completed):.3f})" if completed else "0-0")
    row("Home:", _split(completed, "HOME"))
    row("Away:", _split(completed, "AWAY"))

    print(bold("╠" + "═" * 70 + "╣"))
    print(bold("║") + cyan("  BATTING LEADERS".center(70)) + bold("║"))

    batting = data["hitting_stats"]
    hr_leader = max(batting, key=lambda p: p["hr"])
    rbi_leader = max(batting, key=lambda p: p["rbi"])
    avg_leader = max((p for p in batting if p["ab"] >= 30), key=lambda p: float(p["avg"]))
    ops_leader = max((p for p in batting if p["ab"] >= 30), key=lambda p: float(p["ops"]))
    sb_leader  = max(batting, key=lambda p: p["sb"])

    row("Home Runs:", f"{hr_leader['name']} ({hr_leader['hr']})")
    row("RBI:", f"{rbi_leader['name']} ({rbi_leader['rbi']})")
    row("Batting Avg:", f"{avg_leader['name']} ({avg_leader['avg']})")
    row("OPS:", f"{ops_leader['name']} ({ops_leader['ops']})")
    row("Stolen Bases:", f"{sb_leader['name']} ({sb_leader['sb']})")

    print(bold("╠" + "═" * 70 + "╣"))
    print(bold("║") + cyan("  PITCHING LEADERS".center(70)) + bold("║"))

    pitching = data["pitching_stats"]
    sp = [p for p in pitching if p["gs"] >= 3]
    era_leader  = min(sp, key=lambda p: float(p["era"]))
    win_leader  = max(sp, key=lambda p: p["w"])
    k_leader    = max(pitching, key=lambda p: p["k"])
    save_leader = max(pitching, key=lambda p: p["sv"])
    whip_leader = min(sp, key=lambda p: float(p["whip"]))

    row("ERA (SP, min 3 GS):", f"{era_leader['name']} ({era_leader['era']})")
    row("Wins:", f"{win_leader['name']} ({win_leader['w']})")
    row("Strikeouts:", f"{k_leader['name']} ({k_leader['k']})")
    row("Saves:", f"{save_leader['name']} ({save_leader['sv']})")
    row("WHIP:", f"{whip_leader['name']} ({whip_leader['whip']})")

    print(bold("╚" + "═" * 70 + "╝"))
    print()


def cmd_update(args):
    """Fetch new game results + fresh player stats and save to sample_data.json."""
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")

    print()
    print(bold("=" * 72))
    print(bold("  SF GIANTS TRACKER — UPDATE"))
    print(bold("=" * 72))

    data = _load_sample()
    existing_pks = {g["game_pk"] for g in data["games"]}

    # Find the day after the last stored completed game
    completed_dates = [
        g["date"] for g in data["games"] if g.get("result") in ("W", "L")
    ]
    if completed_dates:
        last_stored = datetime.date.fromisoformat(max(completed_dates))
        fetch_from = last_stored  # re-fetch last day in case it was mid-game
    else:
        fetch_from = OPENING_DAY

    print(f"  Fetching games from {fetch_from} through {today}...")

    try:
        new_games = _live_schedule(fetch_from, today)
    except RuntimeError as e:
        print(f"\n  {red('ERROR:')} {e}")
        print("  Could not connect to MLB Stats API. Try again with internet access.")
        print()
        return

    added = 0
    skipped = 0
    for g in new_games:
        if g["game_pk"] in existing_pks:
            skipped += 1
            continue
        if g.get("result") not in ("W", "L"):
            # Skip games not yet final
            continue
        # Strip internal-only key before storing
        g.pop("status", None)
        g.pop("giants_record", None)
        data["games"].append(g)
        existing_pks.add(g["game_pk"])
        added += 1
        res_col = green("W") if g["result"] == "W" else red("L")
        loc = "vs" if g["home_away"] == "HOME" else " @"
        print(f"  + {g['date']}  {loc} {g['opponent']}  "
              f"{g['giants_score']}-{g['opp_score']}  {res_col}  ({g.get('record','')})")

    if added == 0:
        print("  No new completed games to add.")

    # Sort games by date
    data["games"].sort(key=lambda g: g["date"])

    # Refresh player hitting stats
    print(f"\n  Refreshing hitting stats...")
    try:
        hitting_splits = _live_roster_stats("hitting")
        data["hitting_stats"] = []
        for s in hitting_splits:
            p  = s.get("player", {})
            st = s.get("stat", {})
            ab = st.get("atBats", 0)
            if ab == 0:
                continue
            data["hitting_stats"].append({
                "name": p.get("fullName", ""),
                "pos":  s.get("position", {}).get("abbreviation", ""),
                "g":    st.get("gamesPlayed", 0),
                "ab":   ab,
                "h":    st.get("hits", 0),
                "2b":   st.get("doubles", 0),
                "3b":   st.get("triples", 0),
                "hr":   st.get("homeRuns", 0),
                "rbi":  st.get("rbi", 0),
                "r":    st.get("runs", 0),
                "bb":   st.get("baseOnBalls", 0),
                "k":    st.get("strikeOuts", 0),
                "sb":   st.get("stolenBases", 0),
                "avg":  st.get("avg", ".000"),
                "obp":  st.get("obp", ".000"),
                "slg":  st.get("slg", ".000"),
                "ops":  st.get("ops", ".000"),
            })
        print(f"  Updated {len(data['hitting_stats'])} hitters.")
    except RuntimeError as e:
        print(f"  {yellow('WARNING:')} Could not refresh hitting stats: {e}")

    # Refresh player pitching stats
    print(f"  Refreshing pitching stats...")
    try:
        pitching_splits = _live_roster_stats("pitching")
        data["pitching_stats"] = []
        for s in pitching_splits:
            p  = s.get("player", {})
            st = s.get("stat", {})
            ip = st.get("inningsPitched", "0.0")
            if ip == "0.0" or ip == 0:
                continue
            data["pitching_stats"].append({
                "name": p.get("fullName", ""),
                "g":    st.get("gamesPlayed", 0),
                "gs":   st.get("gamesStarted", 0),
                "w":    st.get("wins", 0),
                "l":    st.get("losses", 0),
                "sv":   st.get("saves", 0),
                "ip":   ip,
                "h":    st.get("hits", 0),
                "er":   st.get("earnedRuns", 0),
                "bb":   st.get("baseOnBalls", 0),
                "k":    st.get("strikeOuts", 0),
                "era":  st.get("era", "-.--"),
                "whip": st.get("whip", "-.--"),
            })
        print(f"  Updated {len(data['pitching_stats'])} pitchers.")
    except RuntimeError as e:
        print(f"  {yellow('WARNING:')} Could not refresh pitching stats: {e}")

    # Save
    with open(SAMPLE_FILE, "w") as f:
        json.dump(data, f, indent=2)

    completed = [g for g in data["games"] if g.get("result") in ("W", "L")]
    wins   = sum(1 for g in completed if g["result"] == "W")
    losses = len(completed) - wins
    print()
    print(bold(f"  Saved.  Record: {wins}-{losses}  |  {len(data['games'])} games stored."))
    print(bold(f"  sample_data.json updated — run any command without --live to view."))
    print()


def _split(games, loc):
    sub = [g for g in games if g.get("home_away") == loc]
    w = sum(1 for g in sub if g["result"] == "W")
    return f"{w}-{len(sub)-w}"


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="giants_tracker.py",
        description="SF Giants 2026 Day-by-Day Stat Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
          commands:
            schedule    Full season schedule with W/L results  (default)
            today       Today's game result/status
            hitting     Season batting stats for all players
            pitching    Season pitching stats for all players
            summary     Season-at-a-glance with stat leaders
            update      Pull new games + fresh stats from MLB API → saves to sample_data.json

          flags:
            --live      Fetch from MLB Stats API instead of sample data
                        (requires network access to statsapi.mlb.com)

          examples:
            python giants_tracker.py
            python giants_tracker.py schedule
            python giants_tracker.py today
            python giants_tracker.py hitting
            python giants_tracker.py pitching
            python giants_tracker.py summary
            python giants_tracker.py update        ← run this daily to stay current
            python giants_tracker.py schedule --live
        """),
    )
    parser.add_argument("--live", action="store_true",
                        help="Fetch live data from MLB Stats API")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("schedule")
    sub.add_parser("today")
    sub.add_parser("hitting")
    sub.add_parser("pitching")
    sub.add_parser("summary")
    sub.add_parser("update")

    args = parser.parse_args()
    cmd = args.command or "schedule"

    dispatch = {
        "schedule": cmd_schedule,
        "today":    cmd_today,
        "hitting":  cmd_hitting,
        "pitching": cmd_pitching,
        "summary":  cmd_summary,
        "update":   cmd_update,
    }

    fn = dispatch.get(cmd)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
