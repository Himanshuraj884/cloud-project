"""Sharding rule shared by the worker and the verification script."""


def select_shard(lines, shard_index, shard_count):
    """Yield (line_number, line) whose 0-based line number % shard_count == shard_index."""
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("need 0 <= SHARD_INDEX < SHARD_COUNT")
    for n, line in enumerate(lines):
        if n % shard_count == shard_index:
            yield n, line
