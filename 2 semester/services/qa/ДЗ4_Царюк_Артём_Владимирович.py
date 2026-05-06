import datetime
import functools
import inspect
import logging
from typing import Any, Callable


def configure_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def logging_middleware(service_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    logger = configure_logger(service_name)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound_args = signature.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            payload = bound_args.arguments

            tracked_fields = {
                "event_id": payload.get("event_id"),
                "user_id": payload.get("user_id"),
                "booking_id": payload.get("booking_id"),
                "task_id": payload.get("task_id"),
            }

            logger.info("call %s args=%s", func.__name__, tracked_fields)

            try:
                result = func(*args, **kwargs)
                logger.info("success %s", func.__name__)
                return result
            except (ValueError, KeyError) as err:
                logger.error("error %s: %s", func.__name__, err)
                raise

        return wrapper

    return decorator


# ===== Booking service =====
EVENTS_DB = {
    1: {"title": "Football Match", "available_seats": 10, "date": datetime.date(2025, 7, 1)},
    2: {"title": "Basketball Playoffs", "available_seats": 5, "date": datetime.date(2025, 7, 2)},
    3: {"title": "Tennis Open", "available_seats": 3, "date": datetime.date(2025, 7, 3)},
}
BOOKINGS_DB = {}


@logging_middleware("Booking")
def create_booking(event_id: int, user_id: int) -> dict:
    if event_id not in EVENTS_DB:
        raise ValueError(f"Event with id={event_id} does not exist.")

    event_info = EVENTS_DB[event_id]
    if event_info["available_seats"] <= 0:
        raise ValueError("No available seats.")

    event_info["available_seats"] -= 1
    booking_id = f"{int(datetime.datetime.now().timestamp())}_{user_id}"

    booking_data = {
        "booking_id": booking_id,
        "event_id": event_id,
        "user_id": user_id,
        "title": event_info["title"],
        "date": event_info["date"],
        "created_at": datetime.datetime.now(),
    }
    BOOKINGS_DB[booking_id] = booking_data
    return booking_data


@logging_middleware("Booking")
def get_booking(booking_id: str) -> dict:
    return BOOKINGS_DB[booking_id]


# ===== TaskManager service =====
TASKS_DB = {}


@logging_middleware("TaskManager")
def create_task(title: str, user_id: int, due_date: datetime.date) -> dict:
    if not title:
        raise ValueError("Task title cannot be empty.")
    if due_date < datetime.date.today():
        raise ValueError("Due date cannot be in the past.")

    task_id = len(TASKS_DB) + 1
    task_data = {
        "task_id": task_id,
        "title": title,
        "user_id": user_id,
        "due_date": due_date,
        "created_at": datetime.datetime.now(),
        "completed": False,
    }
    TASKS_DB[task_id] = task_data
    return task_data


@logging_middleware("TaskManager")
def complete_task(task_id: int) -> dict:
    if task_id not in TASKS_DB:
        raise KeyError(f"Task with id={task_id} not found.")

    task_data = TASKS_DB[task_id]
    task_data["completed"] = True
    return task_data


if __name__ == "__main__":
    created_booking = create_booking(event_id=1, user_id=101)
    print("Created booking:", created_booking)
    loaded_booking = get_booking(created_booking["booking_id"])
    print("Retrieved booking:", loaded_booking)

    created_task = create_task(
        title="Finish project",
        user_id=101,
        due_date=datetime.date.today() + datetime.timedelta(days=1),
    )
    print("Created task:", created_task)
    done_task = complete_task(created_task["task_id"])
    print("Updated task:", done_task)
