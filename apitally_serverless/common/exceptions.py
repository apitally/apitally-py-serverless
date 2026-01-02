import traceback


MAX_EXCEPTION_MSG_LENGTH = 2048
MAX_EXCEPTION_TRACEBACK_LENGTH = 65536


def get_exception_type(exception: BaseException) -> str:
    exception_type = type(exception)
    return f"{exception_type.__module__}.{exception_type.__qualname__}"


def get_truncated_exception_msg(exception: BaseException) -> str:
    msg = str(exception).strip()
    if len(msg) <= MAX_EXCEPTION_MSG_LENGTH:
        return msg
    suffix = "... (truncated)"
    cutoff = MAX_EXCEPTION_MSG_LENGTH - len(suffix)
    return msg[:cutoff] + suffix


def get_truncated_exception_traceback(exception: BaseException) -> str:
    prefix = "... (truncated) ...\n"
    cutoff = MAX_EXCEPTION_TRACEBACK_LENGTH - len(prefix)
    lines = []
    length = 0
    traceback_lines = traceback.format_exception(exception)
    for line in traceback_lines[::-1]:
        if length + len(line) > cutoff:
            lines.append(prefix)
            break
        lines.append(line)
        length += len(line)
    return "".join(lines[::-1]).strip()
