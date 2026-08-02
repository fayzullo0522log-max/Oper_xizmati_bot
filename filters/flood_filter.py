import time
from collections import defaultdict, deque
from config import FLOOD_MESSAGE_LIMIT, FLOOD_TIME_WINDOW

_message_times: dict[tuple[int, int], deque] = defaultdict(deque)


def is_flooding(chat_id: int, user_id: int) -> bool:
    key = (chat_id, user_id)
    now = time.time()
    dq = _message_times[key]
    dq.append(now)

    while dq and now - dq[0] > FLOOD_TIME_WINDOW:
        dq.popleft()

    return len(dq) > FLOOD_MESSAGE_LIMIT


def reset_user(chat_id: int, user_id: int):
    _message_times.pop((chat_id, user_id), None)
