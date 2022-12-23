import time

import pytest

import requests

from request_rate_limiter import rate_limiter


@pytest.fixture
def server_url(httpserver):
    httpserver.expect_request("/").respond_with_data("Foobar!")
    return httpserver.url_for("/")


def test_rate_limit_violating_request_discarded(server_url):
    RPS = 1 # requests per second
    limiter = rate_limiter(RPS)

    @limiter
    def make_request():
        return requests.get(server_url)

    res = make_request()
    assert isinstance(res, requests.Response)

    res = make_request()
    assert res is None


def test_rate_limit_complying_requests_executed(server_url):
    RPS = 20 # requests per second
    limiter = rate_limiter(RPS)

    @limiter
    def make_request():
        return requests.get(server_url)

    for _ in range(10):
        res = make_request()
        assert isinstance(res, requests.Response)
        time.sleep(1/RPS)


def test_separate_rate_limiters_do_not_interfere(server_url):
    RPS_20 = 20
    RPS_10 = 10

    @rate_limiter(RPS_20)
    def make_request_20():
        return requests.get(server_url)

    @rate_limiter(RPS_10)
    def make_request_10():
        return requests.get(server_url)

    res_10 = make_request_10()
    res_20 = make_request_20()

    assert isinstance(res_10, requests.Response)
    assert isinstance(res_20, requests.Response)


def test_one_rate_limiter_multiple_functions(server_url):
    RPS_20 = 20

    limiter = rate_limiter(RPS_20)

    @limiter
    def make_request_1():
        return requests.get(server_url)

    @limiter
    def make_request_2():
        return requests.get(server_url)

    # test rate violated
    res = make_request_1()
    assert isinstance(res, requests.Response)

    res = make_request_2()
    assert res is None

    # test rate respected
    time.sleep(1/RPS_20)

    res = make_request_1()
    assert isinstance(res, requests.Response)

    time.sleep(1/RPS_20)
    assert isinstance(res, requests.Response)
