import os
import sys
import argparse
import urllib.parse as urlparse
from urllib.parse import urlencode, urlunparse
import subprocess
import json
from collections import OrderedDict

import numpy as np
import requests


def simple_mean(values):
    """Simple mean, to be computed from iterator"""
    n = 0
    sum_ = 0.0
    for v in values:
        sum_ += v
        n += 1
    return sum_ / n


def build_query_url(url, params):
    """Use urllib to create the right url"""
    params = urlencode(params)

    url_parts = list(urlparse.urlparse(url))
    url_parts[4] = params

    return urlunparse(url_parts)


def fetch_by(key, id_):
    """Function used to call the filter endpoint"""
    url = 'https://api.opentargets.io/v3/platform/public/association/filter'
    params = {key: id_}

    res = requests.get(build_query_url(url, params))

    data = json.loads(res.text)['data']

    compute = OrderedDict()
    compute['maximum'] = max
    compute['minimum'] =  min
    compute['average'] = simple_mean
    compute['standard deviation'] = np.std

    output = []
    for k, v in compute.items():
        iter_ = iter(d['association_score']['overall'] for d in data)
        try:
            output.append('{}: {}'.format(k, v(iter_)))
        except AttributeError:
            output.append('{}: {}'.format(k, v(list(iter_))))

    sys.stdout.write('\n'.join(output) + '\n')


def run_tests():
    """
    Basic test
    :return:
    """
    test_string = b'maximum: 1.0\nminimum: 1.0\naverage: 1.0\nstandard deviation: 0.0\n'

    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'my_code_test.py')
    command = 'python {} -t ENSG00000157764'.format(dir_path).split(' ')
    test = subprocess.run(command, stdout=subprocess.PIPE)

    assert test_string == test.stdout


def main(args):
    """Module entrypoint"""
    # this can be done with introspection, but we go the easy way with a mapping
    # can be done also with a custom `ArgParseAction`
    FUNC = {
        "target": fetch_by,
        "disease": fetch_by
    }
    if args.test is not None:
        return run_tests()

    # find the right method in a fancy way (:
    key, value = tuple(filter(lambda i: i[1] if i[0] is not None else None, args.__dict__.items()))[0]
    op = FUNC[key](key, value)
    return op


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", help="Target ID")
    parser.add_argument("-d", "--disease", help="Disease ID")
    parser.add_argument("--test", nargs='*', help="Run tests")
    args = parser.parse_args()

    # check if the right number of arguments is passed
    if sum(a is None for a in args.__dict__.values()) in [0, 1, 3]:
        raise ValueError('One option between -t, -d or --test is required')

    main(args)



