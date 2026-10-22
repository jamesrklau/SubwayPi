import time

from settings import (
    WALKING_TIME_MINUTES,
    SAFETY_BUFFER_MINUTES
)


def get_departure_options(arrivals):

    options = []

    for train in arrivals:

        minutes_away = (
            train["arrival_time"] - time.time()
        ) / 60

        leave_in = (
            minutes_away
            - WALKING_TIME_MINUTES
            - SAFETY_BUFFER_MINUTES
        )

        # Skip trains we cannot realistically catch
        if leave_in < 0:
            continue

        train_option = train.copy()

        train_option["minutes_away"] = round(minutes_away)
        train_option["leave_in"] = round(leave_in)

        options.append(train_option)

    return options
