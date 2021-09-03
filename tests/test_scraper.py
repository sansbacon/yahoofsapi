# test_scraper.py

import os
import pytest

from sportscraper.scraper import RequestScraper, BrowserScraper


@pytest.yield_fixture(scope='session')
def scraper():
    scraper = RequestScraper(cache_name='test_rs')
    yield scraper


@pytest.yield_fixture(scope='session')
def bscraper():
    bscraper = BrowserScraper(profile=os.getenv('FIREFOX_PROFILE'))
    yield bscraper
    bscraper.__del__()


@pytest.fixture
def mock_response(monkeypatch):
    """

    Args:
        monkeypatch:

    Returns:

    """
    def mock_get(*args, **kwargs):
        return '<html>Google</html>'

    def mock_get_json(*args, **kwargs):
        return {'username': 'User'}

    monkeypatch.setattr(RequestScraper, "get", mock_get)
    monkeypatch.setattr(RequestScraper, "get_json", mock_get_json)


def test_rget_mock(mock_response):
    '''

    '''
    url = 'https://www.google.com'
    scraper = RequestScraper()
    content = scraper.get(url)
    assert isinstance(content, str)
    assert 'Google' in content


def test_rget_json_mock(mock_response):
    '''

    '''
    url = 'https://api.bitbucket.org/2.0/users/karllhughes'
    scraper = RequestScraper()
    content = scraper.get_json(url)
    assert isinstance(content, dict)
    assert content.get('username') is not None


def test_rget(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    url = 'https://www.google.com'
    content = scraper.get(url)
    assert isinstance(content, str)
    assert 'Google' in content


def test_rget_json(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    url = 'https://api.bitbucket.org/2.0/users/karllhughes'
    content = scraper.get_json(url)
    assert isinstance(content, dict)
    assert content.get('username') is not None


def test_bget(bscraper):
    '''

    Args:
        bscraper:

    Returns:

    '''
    url = 'https://www.google.com'
    content = bscraper.get(url)
    assert isinstance(content, str)
    assert 'Google' in content


def test_bget_json(bscraper):
    '''

    Args:
        bscraper:

    Returns:

    '''
    url = 'https://api.bitbucket.org/2.0/users/karllhughes'
    content = bscraper.get_json(url)
    assert isinstance(content, dict)
    assert content.get('username') is not None
