from worker.shard import select_shard


def test_shards_cover_every_line_exactly_once():
    lines = [f"line{i}" for i in range(101)]
    got = []
    for idx in range(3):
        got += [n for n, _ in select_shard(lines, idx, 3)]
    assert sorted(got) == list(range(101))
    assert len(got) == len(set(got))


def test_shard_rule_is_line_number_modulo_count():
    lines = list("abcdefghij")
    assert [n for n, _ in select_shard(lines, 1, 4)] == [1, 5, 9]


def test_bad_index_rejected():
    import pytest

    with pytest.raises(ValueError):
        list(select_shard(["x"], 2, 2))
