import redis


def check(values):
    # anagram detection. ignore palindromes (numbers that are the reverse of themselves) unless they're unique repeated
    # items within values (e.g., in the case of the list [b'1331', b'1331', b'34']).
    if type(values) is list:
        if any(i1 != i2 and values[i1][::-1] == values[i2] for i1 in range(len(values)) for i2 in range(len(values))):
            return 0
    else:
        if any(v1 != v2 and v1[::-1] == v2 for v1 in values for v2 in values):
            return 0

    # x / y = 177 detection
    nums = [int(v) for v in values]
    if any(v1 / v2 == 177 for v1 in nums for v2 in nums):
        return 0

    # return max - min
    return max(nums) - min(nums)


def test_check():
    '''
    Test cases for the rules listed (items in the set can be divided to yield 177, no anagrams).

    :return: True if check() returns expected values. Throws AssertionError otherwise.
    '''
    test_lists = [
        (3, [b'1', "2", b'3', "4"]),  # test check works with list
        (0, ["10", b'531', b'3']),  # test x / y = 177 condition returns 0
        (0, ["123", "321", "11"])  # test for anagrams
    ]
    test_values = test_lists + [(r, set(v)) for (r, v) in test_lists]
    for (resp, inp) in test_values:
        if check(inp) != resp:
            raise AssertionError(
                "\nFailed test: " + str(inp) +
                "\nexpected response: " + str(resp) +
                "\ngot: " + str(check(inp))
            )
    return True


def get_values(redis_and_key):
    '''
    Given a key, check if it corresponds to a list or a set. Either way, get all values from the redis DB.

    Assumes that we can ask the DB for all of the values for these keys without clogging anything up.

    :param r: active redis client.
    :param key: key to check the type of and return the values of.
    :return: values (set or list) associated with given key.
    '''
    r, key = redis_and_key
    t = r.type(key)
    if t == b'list':
        return r.lrange(key, 0, -1)
    elif t == b'set':
        return r.smembers(key)


def test_input(r):
    '''
    data expectations:
    - every value is a set or a list.
    - every item in each value is a string of a natural number.

    :return: True if expectations are met. Throws AssertionError otherwise.
    '''
    keys = r.keys("*")
    if any(r.type(k) not in [b'set', b'list'] for k in keys):
        raise AssertionError(
            "\nUnexpected datatypes in input: " + str(set(r.type(k) for k in r.keys("*"))) +
            "\nOnly expected datatypes are set and list."
        )
    for k in keys:
        values = get_values((r, k))
        assert type(values) is list or type(values) is set #redundant but comforting check.
        try:
            if any(int(v) for v in values) < 1:
                raise AssertionError("Negative or zero integer found out of range in input.\nOffending values: " +
                                     str([v for v in get_values((r, k))]))
        except TypeError:
            raise AssertionError("Value which could not be coerced into integer type included in input."
                                 "\nOffending values: " + str([v for v in get_values((r, k))]))


if __name__ == "__main__":
    import sys

    r = redis.StrictRedis(host='redis', port=6379, db=0)

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_input(r)
        test_check()

    # assumes that we can ask the redis server for all the keys at once without clogging anything up.
    # Get the keys, get the values for those keys, and then check the values. Sum output from the values checks.
    checksum = sum(map(check, map(get_values, ((r, key) for key in r.keys("*")))))

    print(checksum)
