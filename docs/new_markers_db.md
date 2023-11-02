Given the updated requirements, an efficient way to store and query this data in Redis would be to utilize both **Hashes** and **Sorted Sets**. 

### 1. Storing Data using Hashes:

For every phrase (which we'll call a "marker" in this context), you should maintain a hash to store its associated values:

- Key: The marker (phrase)
- Fields: true_positives, false_positives, true_negatives, false_negatives

```shell
HSET "marker:example phrase" true_positives 10 false_positives 5 true_negatives 80 false_negatives 5
```

### 2. Maintaining Ratios using Sorted Sets:

You will need two sorted sets to maintain the markers ranked by their respective ratios:

- One sorted set for `true_positives / positives` (where `positives = true_positives + false_negatives`)
- Another sorted set for `false_positives / negatives` (where `negatives = false_positives + true_negatives`)

Whenever you update the values for a marker in its hash, you should also update its score in the sorted sets. 

For example, after updating the hash for "marker:example phrase", calculate its ratios and update the sorted sets:

```python
true_positives = HGET "marker:example phrase" true_positives
false_negatives = HGET "marker:example phrase" false_negatives
positives = true_positives + false_negatives

ratio1 = true_positives / positives
ZADD tp_ratio_sortedset ratio1 "example phrase"
```

Similarly, do this for the second ratio.

### 3. Querying:

To get the marker with the maximum ratio for `true_positives / positives`:

```shell
ZREVRANGE tp_ratio_sortedset 0 0
```

For `false_positives / negatives`:

```shell
ZREVRANGE fp_ratio_sortedset 0 0
```

### Important Considerations:

1. **Atomicity**: Ensure the operations are atomic. Redis provides the `MULTI` and `EXEC` commands which allow you to execute a series of commands atomically. This can ensure that the sorted set and the hash are always in sync.

2. **Memory Overhead**: Storing data in both a hash and a sorted set will increase memory usage. Ensure you monitor Redis memory consumption, especially if you have a large number of markers.

3. **Updating Ratios**: Every time you update the metrics for a marker, remember to recalculate the ratios and update the sorted sets. This can be done efficiently in a single batch of commands or in a script using Lua with Redis's `EVAL` command.

This combination of Redis data structures allows you to efficiently store the data and perform the specific queries you're interested in.