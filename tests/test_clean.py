import json

from worker.clean import check_record, clean, serialise, sha256_line


def rec(i, text, reply):
    return {"id": i, "text": text, "teacher_raw": reply if isinstance(reply, str) else json.dumps(reply)}


GOOD = {"intent": "weather_query", "date": None, "time": None, "place": "london"}


def test_each_rejection_reason():
    t = "what is the weather in london"
    assert check_record(rec("C1", t, "not json")) == "a"
    assert check_record(rec("C1", t, {"intent": "weather_query", "place": "london"})) == "b"
    assert check_record(rec("C1", t, [1, 2])) == "b"
    assert check_record(rec("C1", t, dict(GOOD, intent="play_music"))) == "c"
    assert check_record(rec("C1", t, dict(GOOD, place="paris"))) == "d"
    assert check_record(rec("C1", t, dict(GOOD, date=5))) == "d"
    assert check_record(rec("C1", t, GOOD)) is None


def test_counts_add_up_and_duplicates_keep_smallest_id():
    t = "what is the weather in london"
    records = [
        rec("C3", t, GOOD),
        rec("C1", t, GOOD),
        rec("C2", "hello", "oops"),
        rec("C4", "hello there", dict(GOOD, intent="nope")),
    ]
    kept, counts = clean(records)
    assert [r["id"] for r in kept] == ["C1"]
    assert counts["duplicates"] == 1 and counts["a_invalid_json"] == 1 and counts["c_bad_intent"] == 1
    assert counts["input"] == sum(v for k, v in counts.items() if k != "input")


def test_output_is_deterministic_and_in_id_order():
    a = [rec("C2", "b weather in london", GOOD), rec("C1", "weather in london", GOOD)]
    k1, _ = clean(a)
    k2, _ = clean(list(reversed(a)))
    assert serialise(k1) == serialise(k2)
    assert [r["id"] for r in k1] == ["C1", "C2"]
    assert sha256_line(serialise(k1)) == sha256_line(serialise(k2))
