from service.validate import parse_output


def test_valid_output_accepted():
    out = parse_output('{"intent": "alarm_set", "date": "tomorrow", "time": "seven am", "place": null}')
    assert out == {"intent": "alarm_set", "date": "tomorrow", "time": "seven am", "place": None}


def test_invalid_outputs_rejected():
    for bad in ["not json", "", '{"intent": "alarm_set"}',
                '{"intent": "x", "date": null, "time": null, "place": null}',
                '{"intent": "alarm_set", "date": 1, "time": null, "place": null}',
                '{"intent": "alarm_set", "date": null, "time": null, "place": null, "extra": 1}', "[]"]:
        assert parse_output(bad) is None
