# SubwayPi

SubwayPi is a Python application that uses MTA real-time subway data to show upcoming trains at a configured station and estimate when to leave home to catch one.

I built this project to make my daily commute easier while learning how to work with APIs, process real-time data, and build a web application.

## Features

- Retrieves real-time subway arrival information from MTA feeds.
- Displays upcoming trains in a web interface.
- Estimates when to leave based on walking time and a safety buffer.
- Provides a compact view for smaller screens.
- Exposes JSON endpoints for train arrival data.
- Refreshes train information automatically in the browser.

## How It Works

SubwayPi separates its main responsibilities into Python modules:

- `app.py` — Flask application and web/API routes.
- `mta.py` — Downloads and parses MTA real-time feeds.
- `arrivals.py` — Filters train arrivals for configured routes and stops.
- `departure.py` — Calculates which trains are still realistically catchable.
- `routes.py` — Defines the station, subway routes, feeds, and stop IDs.
- `settings.py` — Defines walking time and the safety buffer.
- `templates/` — Contains the web interfaces.

## Requirements

- Python 3
- An internet connection to retrieve MTA data
- The Python packages listed in `requirements.txt`

## Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/jamesrklau/SubwayPi.git
cd SubwayPi
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

The application listens on port `5000`. Its current station and route configuration are defined in `routes.py`.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Main train display |
| `/compact` | Compact train display |
| `/api/trains` | Upcoming trains as JSON |
| `/api/compact` | Compact train data as JSON |

## Configuration

Walking time and the safety buffer can be adjusted in `settings.py`. Station stop IDs, route mappings, and the station name can be adjusted in `routes.py`.

## Future Improvements

- Add automated tests for arrival filtering and departure calculations.
- Improve error handling when MTA feeds are unavailable.
- Add automated testing through GitHub Actions.
- Make station configuration easier to customize.
