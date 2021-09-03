# test_yahoo.py

import pytest
import random

from sportscraper.yahoo import Scraper
from sportscraper import testconf


@pytest.yield_fixture(scope='session')
def scraper():
    scraper = Scraper(authfn=testconf.YAHOO_AUTH_FN,
                      sport=testconf.YAHOO_SPORT,
                      game_key=testconf.YAHOO_GAME_KEY,
                      yahoo_season=testconf.YAHOO_SEASON)
    yield scraper


def test_game(scraper):
    '''

    '''
    scraper.response_format = {'format': 'xml'}
    for game_subresource in ['metadata', 'stat_categories']:
        content = scraper.game(subresource=game_subresource)
        print(game_subresource)
        assert isinstance(content, str)


def test_games(scraper):
    '''

    '''
    scraper.response_format = {'format': 'xml'}
    for game_subresource in ['metadata', 'stat_categories']:
        content = scraper.games(subresource=game_subresource)
        print(game_subresource)
        assert isinstance(content, str)


def test_league(scraper):
    '''

    '''
    scraper.response_format = {'format': 'xml'}
    content = scraper.league(league_id=49127)
    assert isinstance(content, str)


def test_league_free_agents(scraper):
    '''

    '''
    scraper.response_format = {'format': 'xml'}
    content = scraper.league_free_agents(league_id=testconf.YAHOO_LEAGUE_ID)
    assert isinstance(content, str)


def test_leagues(scraper):
    '''

    '''
    scraper.response_format = {'format': 'xml'}
    league_key = scraper._league_key(testconf.YAHOO_LEAGUE_ID)
    content = scraper.leagues(league_keys=[league_key])
    assert isinstance(content, str)



def test_player(scraper):
    '''

    '''
    scraper.response_format = {'format': 'xml'}
    player_key = random.choice(testconf.YAHOO_PLAYER_KEYS)
    content = scraper.player(player_key=player_key)
    assert isinstance(content, str)
    assert 'player' in content


def test_players(scraper):
    '''

    '''
    scraper.response_format = {'format': 'xml'}
    player_keys = random.sample(testconf.YAHOO_PLAYER_KEYS, 3)
    content = scraper.players(player_keys=player_keys)
    assert isinstance(content, str)
    assert 'player' in content


def test_roster(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    team_key = random.choice(testconf.YAHOO_TEAM_KEYS)
    content = scraper.roster(team_key=team_key)
    assert isinstance(content, str)
    assert 'team' in content


def test_team(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    team_key = random.choice(testconf.YAHOO_TEAM_KEYS)
    content = scraper.team(team_key=team_key)
    assert isinstance(content, str)
    assert 'team' in content


def test_teams(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    team_keys = random.sample(testconf.YAHOO_TEAM_KEYS, 2)
    content = scraper.teams(team_keys=team_keys)
    assert isinstance(content, str)
    assert 'team' in content


def test_transactions(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    content = scraper.transactions(league_id=testconf.YAHOO_LEAGUE_ID)
    assert isinstance(content, str)
    assert 'transaction' in content


def test_user(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    content = scraper.user()
    assert isinstance(content, str)
    assert 'user' in content


def test_users(scraper):
    '''

    Args:
        scraper:

    Returns:

    '''
    content = scraper.users()
    assert isinstance(content, str)
    assert 'user' in content


