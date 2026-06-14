from sermoncut_core.timecode import to_seconds, hms


def test_to_seconds_hms():
    assert to_seconds("01:15:07") == 4507.0
    assert to_seconds("25:36") == 1536.0
    assert to_seconds("09") == 9.0


def test_hms_roundtrip():
    assert hms(4507) == "01:15:07"
    assert hms(1536) == "00:25:36"


def test_roundtrip_stable():
    for s in (0, 59, 60, 3599, 3600, 4507):
        assert to_seconds(hms(s)) == float(s)
