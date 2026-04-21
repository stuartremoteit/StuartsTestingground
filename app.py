#!/usr/bin/env python3
"""
SF Giants 2026 Stat Tracker — Flask Web Interface
Run: python app.py
Then open: http://localhost:5000
"""

import json
import os
from flask import Flask, render_template, abort

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "sample_data.json")


def load_data() -> dict:
    with open(DATA_FILE) as f:
        return json.load(f)


@app.route("/")
def schedule():
    data = load_data()
    games = data["games"]
    completed = [g for g in games if g.get("result") in ("W", "L")]
    wins = sum(1 for g in completed if g["result"] == "W")
    losses = len(completed) - wins
    return render_template("schedule.html",
                           games=games,
                           wins=wins,
                           losses=losses,
                           games_played=len(completed))


@app.route("/hitting")
def hitting():
    data = load_data()
    players = sorted(data["hitting_stats"], key=lambda p: int(p["ab"]), reverse=True)
    return render_template("hitting.html", players=players)


@app.route("/pitching")
def pitching():
    data = load_data()
    starters  = sorted([p for p in data["pitching_stats"] if p["gs"] >= 1],
                       key=lambda p: float(p["ip"]), reverse=True)
    relievers = sorted([p for p in data["pitching_stats"] if p["gs"] == 0],
                       key=lambda p: float(p["ip"]), reverse=True)
    return render_template("pitching.html", starters=starters, relievers=relievers)


@app.route("/game/<int:pk>")
def game(pk):
    data = load_data()
    box = data.get("boxscores", {}).get(str(pk))
    if not box:
        abort(404)
    return render_template("game.html", box=box)


@app.route("/summary")
def summary():
    data = load_data()
    games = data["games"]
    completed = [g for g in games if g.get("result") in ("W", "L")]
    wins   = sum(1 for g in completed if g["result"] == "W")
    losses = len(completed) - wins

    home_games = [g for g in completed if g["home_away"] == "HOME"]
    away_games = [g for g in completed if g["home_away"] == "AWAY"]
    home_w = sum(1 for g in home_games if g["result"] == "W")
    away_w = sum(1 for g in away_games if g["result"] == "W")

    batting = data["hitting_stats"]
    qual_bat = [p for p in batting if p["ab"] >= 30]

    pitching = data["pitching_stats"]
    qual_sp  = [p for p in pitching if p["gs"] >= 3]

    leaders = {
        "hr":   max(batting,   key=lambda p: p["hr"]),
        "rbi":  max(batting,   key=lambda p: p["rbi"]),
        "avg":  max(qual_bat,  key=lambda p: float(p["avg"])),
        "ops":  max(qual_bat,  key=lambda p: float(p["ops"])),
        "sb":   max(batting,   key=lambda p: p["sb"]),
        "era":  min(qual_sp,   key=lambda p: float(p["era"])),
        "wins": max(qual_sp,   key=lambda p: p["w"]),
        "k":    max(pitching,  key=lambda p: p["k"]),
        "sv":   max(pitching,  key=lambda p: p["sv"]),
        "whip": min(qual_sp,   key=lambda p: float(p["whip"])),
    }

    return render_template("summary.html",
                           wins=wins, losses=losses,
                           games_played=len(completed),
                           home_w=home_w, home_l=len(home_games)-home_w,
                           away_w=away_w, away_l=len(away_games)-away_w,
                           leaders=leaders)


if __name__ == "__main__":
    app.run(debug=True)
