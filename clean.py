from collections import Counter

import redis
import requests

verbose = False


def c(binary):
    return Counter(str(int(binary)))


def check(values):
    '''
    Performs the following checks and returns either the difference between the max and the min values, or 0 if the
    values should be skipped:

    Scan the array for any numerical anagrams (123 is a numerical anagram of 321, as is 212 of 221). If it contains any
    numerical anagrams, skip this array and continue to the next. If any two numbers in the array can be divided
    together to equal 177, skip this array and continue to the next.

    :param values: either a list or set
    :return: 0 or the difference between the max and min values.
    '''

    # anagram detection. ignore identity cases unless they're unique repeated
    # items within a list (e.g., 1331 in [b'1331', b'1331', b'34']).
    if type(values) is list:
        if verbose: print("Values is a list.")
        if any(i1 != i2 and c(values[i1]) == c(values[i2]) for i1 in range(len(values)) for i2 in range(len(values))):
            if verbose: print("Anagram in list found!")
            return 0
    elif type(values) is set:
        if verbose: print("Values is a set.")
        if any(v1 != v2 and c(v1) == c(v2) for v1 in values for v2 in values):
            if verbose: print("Anagram in set found!")
            return 0
    else:
        raise AssertionError("Invalid type passed to check: " + str(type(values)) + "\nvalue: " + str(values))

    # x / y = 177 detection
    nums = sorted(int(v) for v in values)

    if verbose: print("Searching for values that when divided yield 177.")
    for i in range(len(nums)):
        options = [i + 1, len(nums) - 1]  # the range of values where a division by nums[i] may yield 177.
        while options[0] <= options[1]:
            if verbose: print("range of valid options: "+str(options))
            middle = int(sum(options) / 2)
            if verbose: print("Current dividend: "+str(nums[middle] / nums[i]))
            if nums[middle] / nums[i] == 177:
                if verbose: print("dividend of 177 found!")
                return 0
            elif nums[middle] / nums[i] < 177:
                options = [middle + 1, options[1]]
            elif nums[middle] / nums[i] > 177:
                options = [options[0], middle - 1]
        if verbose: print("\n\n\n")

    # return max - min
    return nums[-1] - nums[0]


def test_check():
    '''
    Test cases for the rules listed (items in the set can be divided to yield 177, no anagrams).

    :return: True if check() returns expected values. Throws AssertionError otherwise.
    '''
    test_lists = [
        (3, [b'1', "2", b'3', "4"]),  # test check works with list
        (0, ["10", b'531', b'3']),  # test x / y = 177 condition returns 0
        (0, ["123", b'321', "11"])  # test for anagrams
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


def test_data(r):
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
        assert type(values) is list or type(values) is set  # no None values please, redis!
        try:
            if any(int(v) for v in values) < 1:
                raise AssertionError("Negative or zero integer found out of range in input." +
                                     "\nOffending values: " + str([v for v in get_values((r, k))]))
        except TypeError:
            raise AssertionError("Value which could not be coerced into integer type included in input."
                                 "\nOffending values: " + str([v for v in get_values((r, k))]))


if __name__ == "__main__":
    import sys

    r = redis.StrictRedis(host='redis', port=6379, db=0)

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_data(r)
        test_check()

    # assumes that we can ask the redis server for all the keys at once without clogging anything up.
    # Get the keys, get the values for those keys, and then check the values. Sum output from the values checks.
    checksum = str(sum(map(check, map(get_values, ((r, key) for key in r.keys("*"))))))

    print("checksum found: " + checksum)

    print(requests.get("http://answer:3000/" + checksum))
