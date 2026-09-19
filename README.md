# Aerostudy

A shared study room with an airplane-cabin theme. You and a friend connect, pick a flight (= study session length), and when it lands, the session ends.

## 4. Launch the app
OPEN https://aerostudy.onrender.com

- If you want to study with friends, copy the code and send it to them!

## How to use it

1. You create the room by choosing a flight (the duration = study time)
2. The app gives you a 4-letter code (e.g. `KBTQ`)
3. Send the link to your friend: ex. "KLPS"
4. Your friend enters their name and joins
5. You both appear in the cabin in your seats
6. The timer counts down — when it hits 0, you've landed
7. You can pause/resume with the "Studying" button
8. Cabin chat is available to coordinate with each other

## Available routes

| Route | Duration |
|---|---|
| Madrid → Paris | 1h 15m |
| Madrid → Rome | 1h 30m |
| Barcelona → London | 2h |
| Madrid → New York | 7h |
| Madrid → Tokyo | 12h |
| Madrid → Dubai | 6h |
| Madrid → Sydney | 19h |
| Custom | whatever you want |

## Project structure

```
study-flight/
├── server.py          # FastAPI + WebSockets server
├── requirements.txt   # dependencies
├── README.md
└── static/
    ├── index.html     # home page (create/join)
    └── cabin.html      # the real-time cabin
```
