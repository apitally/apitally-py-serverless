from pytest_mock import MockerFixture


def test_exception_truncation(mocker: MockerFixture):
    from apitally_serverless.common.exceptions import (
        get_exception_type,
        get_truncated_exception_msg,
        get_truncated_exception_traceback,
    )

    mocker.patch("apitally_serverless.common.exceptions.MAX_EXCEPTION_MSG_LENGTH", 32)
    mocker.patch("apitally_serverless.common.exceptions.MAX_EXCEPTION_TRACEBACK_LENGTH", 128)

    try:
        raise ValueError("a" * 88)
    except ValueError as e:
        type_ = get_exception_type(e)
        msg = get_truncated_exception_msg(e)
        tb = get_truncated_exception_traceback(e)

    assert type_ == "builtins.ValueError"
    assert len(msg) == 32
    assert msg.endswith("... (truncated)")
    assert len(tb) <= 128
    assert tb.startswith("... (truncated) ...\n")
