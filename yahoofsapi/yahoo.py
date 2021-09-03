'''
# yahoo.py
# scraper / parser /agent
# for Yahoo fantasy sports API
'''

import base64
import json
import logging
import re
import webbrowser
import xml.etree.ElementTree as ET


from scraper import RequestScraper


class Scraper(RequestScraper):
    '''
    Access YAHOO! fantasy sports API

    '''

    def __init__(
            self, authfn, sport,
            yahoo_season, game_key=None,
            response_format="xml",
            cache_name="yahoo-scraper",
            **kwargs,
    ):
        """
        Initialize scraper object

        Args:
            authfn (str): path of auth.json file
            sport (str):
            yahoo_season (int): '2017-18' season is 2017
            game_key (str):
            response_format(str): 'json' or 'xml'
            cache_name (str):

        Returns:
            YahooFantasyScraper

        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        RequestScraper.__init__(self, cache_name=cache_name, **kwargs)

        self.auth = None
        self.authfn = authfn
        self.auth_uri = "https://api.login.yahoo.com/oauth2/request_auth"
        self.fantasy_uri = "https://fantasysports.yahooapis.com/fantasy/v2"
        self.response_format = {"format": response_format}
        self.sport = sport
        self.yahoo_season = yahoo_season
        self.token_uri = "https://api.login.yahoo.com/oauth2/get_token"

        if game_key:
            self.game_key = game_key
        else:
            self.game_key = self._game_key()
        self._load_credentials()

    def _filtstr(self, filters):
        """
        Creates filter string for collection URL

        Args:
            filters (dict): dict of filters

        Returns:
            str

        """
        vals = ["{}={}".format(k, filters[k]) for
                  k in sorted(filters.keys())]
        return ",".join(vals)

    def _game_key(self):
        """
        Game key for queries

        Args:
            None

        Returns:
            int

        """
        game_key_d = {"nba": {2017: 375, 2018: 385}, "nfl": {2018: 380}}
        return game_key_d.get(self.sport).get(self.yahoo_season)

    def _keystr(self, keys):
        """
        Creates string for keys

        Args:
            keys (list):

        Returns:
            str

        """
        return ",".join([str(k) for k in keys])

    def _league_key(self, league_id):
        """
        League key given league_id

        Args:
            league_id (int):

        Returns:
            str
        """
        return f"{self.game_key}.l.{league_id}"

    def _load_credentials(self):
        """
        Loads credentials from file or obtains new token from yahoo!

        Args:
            None

        Returns:
            None

        """
        # load credentials
        with open(self.authfn) as infile:
            self.auth = json.load(infile)

        # check file for refresh token
        if self.auth.get("refresh_token"):
            self._refresh_credentials()

        # if don't have a refresh token, then request auth
        else:
            params = {
                "client_id": self.auth["client_id"],
                "redirect_uri": "oob",
                "response_type": "code",
                "language": "en-us",
            }
            response = self.get(self.auth["auth_uri"], params=params)

            # response url will allow you to plug in code
            i = 1
            while i:
                # you may need to add export BROWSER=google-chrome to .bashrc
                webbrowser.open(url=response.url)
                code = input("Enter code from url: ")
                i = 0

            # now get authorization token
            hdr = self.auth_header
            body = {
                "grant_type": "authorization_code",
                "redirect_uri": "oob",
                "code": code,
            }
            headers = {
                "Authorization": hdr,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            response = self.post(self.token_uri, data=body, headers=headers)

            # add the token to auth
            context = self.auth.copy()
            context.update(response.json())
            self.auth = context

            # now write back to file
            with open(self.authfn, "w") as outfile:
                json.dump(self.auth, outfile)

    def _refresh_credentials(self):
        """
        Refreshes yahoo token

        Returns:
            None

        """
        body = {
            "grant_type": "refresh_token",
            "redirect_uri": "oob",
            "refresh_token": self.auth["refresh_token"],
        }
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        r = self.post(self.token_uri, data=body, headers=headers)

        # add the token to auth and write back to file
        context = self.auth.copy()
        context.update(r.json())
        self.auth = context
        with open(self.authfn, "w") as outfile:
            json.dump(self.auth, outfile)

    @property
    def auth_header(self):
        """
        Basic authorization header

        Args:
            None

        Returns:
            str

        """
        string = "%s:%s" % (self.auth["client_id"], self.auth["client_secret"])
        base64string = base64.standard_b64encode(string.encode("utf-8"))
        return "Basic %s" % base64string.decode("utf-8")

    @property
    def game_subresources(self):
        """
        Valid game subresources

        Args:
            None

        Returns:
            list

        """
        return [
            "metadata",
            "leagues",
            "players",
            "game_weeks",
            "stat_categories",
            "position_types",
            "roster_positions",
        ]

    @property
    def games_subresources(self):
        """
        Valid games subresources

        Args:
            None

        Returns:
            list

        """
        return [
            "metadata",
            "leagues",
            "players",
            "game_weeks",
            "stat_categories",
            "position_types",
            "roster_positions",
            "teams",
        ]

    @property
    def games_filters(self):
        """
        Valid games filters

        Args:
            None

        Returns:
            list

        """
        return ["is_available", "game_types", "game_codes", "seasons"]

    @property
    def league_subresources(self):
        """
        Valid league subresources

        Args:
            None

        Returns:
            list

        """
        return [
            "metadata",
            "settings",
            "standings",
            "scoreboard",
            "teams",
            "players",
            "draftresults",
            "transactions",
        ]

    @property
    def leagues_subresources(self):
        """
        Valid leagues subresources

        Args:
            None

        Returns:
            list

        """
        return self.league_subresources

    @property
    def player_subresources(self):
        """
        Valid player subresources

        Args:
            None

        Returns:
            list

        """
        return ["metadata", "stats", "ownership", "percent_owned", "draft_analysis"]

    @property
    def players_filters(self):
        """
        Valid players filters

        Args:
            None

        Returns:
            list

        """
        # for football, replace sort_date with sort_week
        return [
            "position",
            "status",
            "search",
            "sort",
            "sort_type",
            "sort_season",
            "sort_date",
            "start",
            "count",
        ]

    @property
    def players_subresources(self):
        """
        Valid player subresources

        Args:
            None

        Returns:
            list

        """
        return self.player_subresources

    @property
    def roster_subresources(self):
        """
        Valid roster subresources

        Args:
            None

        Returns:
            list

        """
        return ["players"]

    @property
    def team_subresources(self):
        """
        Valid team subresources

        Args:
            None

        Returns:
            list

        """
        return ["metadata", "stats", "standings", "roster", "draftresults", "matchups"]

    @property
    def teams_subresources(self):
        """
        Valid team subresources

        Args:
            None

        Returns:
            list

        """
        return self.team_subresources

    @property
    def transaction_filters(self):
        """
        Valid transaction filters

        Args:
            None

        Returns:
            list

        """
        return ["type", "types", "team_key", "count"]

    @property
    def transactions_filters(self):
        """
        Valid transaction filters

        Args:
            None

        Returns:
            list

        """
        return self.transaction_filters

    @property
    def transaction_subresources(self):
        """
        Valid transaction subresources

        Args:
            None

        Returns:
            list

        """
        return ["metadata", "players"]

    @property
    def transactions_subresources(self):
        """
        Valid transactions subresources

        Args:
            None

        Returns:
            list

        """
        return self.transaction_subresources

    @property
    def user_subresources(self):
        """
        Valid team subresources

        Args:
            None

        Returns:
            list

        """
        return [None, "leagues", "teams"]

    @property
    def users_subresources(self):
        """
        Valid users subresources

        Args:
            None

        Returns:
            list

        """
        return self.user_subresources

    # methods
    def _url(self, resource):
        """
        Base URLS for resources

        Args:
            resource(str):

        Returns:
            str

        """
        return f"{self.fantasy_uri}/{resource}"

    def game(self, subresource="metadata", keys=None):
        """
        Gets game resource
        https://developer.yahoo.com/fantasysports/guide/game-resource.html

        Args:
            subresource (str): default 'metadata'
            filters (dict):
            keys (list):

        Returns:
            str: XML

        """
        if subresource not in self.game_subresources:
            raise ValueError("invalid game subresource")
        if subresource in ["leagues", "players"]:
            if not keys:
                raise ValueError(
                    "cannot get subresource %s without keys" % subresource
                )
            if subresource == "leagues":
                url = f"{self._url('game')}/{self.game_key}/leagues;league_keys={','.join(keys)}"
            elif subresource == "players":
                url = f"{self._url('game')}/{self.game_key}/players;player_keys={','.join(keys)}"
        else:
            url = f"{self._url('game')}/{self.game_key}/{subresource}"
        return self.query(url)

    def games(self, subresource="metadata", filters=None, keys=None):
        """
        Gets games collection
        https://developer.yahoo.com/fantasysports/guide/games-collection.html

        Args:
            subresource (str): default 'metadata'
            filters (dict):
            keys (list):

        Returns:
            str: XML

        """
        # games adds an additional subresource for teams
        if subresource not in self.games_subresources:
            raise ValueError("invalid game subresource")
        if filters:
            if set(filters.keys()) <= set(self.games_filters):
                filter_str = self._filtstr(filters)
                url = f"{self._url('games')};{filter_str}"
            else:
                raise ValueError("games invalid filters: {}".format(filters))
        elif subresource == "leagues":
            key_str = ",".join(keys)
            url = f"{self._url('games')};game_keys={self.game_key}/leagues;league_keys={key_str}"
        elif subresource == "players":
            key_str = ",".join(keys)
            url = f"{self._url('games')};game_keys={self.game_key}/players;player_keys={key_str}"
        else:
            url = f"{self._url('games')};game_keys={self.game_key}/{subresource}"
        return self.query(url)

    def league(self, league_id, subresource="metadata"):
        """
        Gets league resource
        https://developer.yahoo.com/fantasysports/guide/league-resource.html

        Args:
            league_id (int): id for your league
            subresource (str): metadata, settings, standings, scoreboard, etc.

        Returns:
            str: XML

        """
        if subresource not in self.league_subresources:
            raise ValueError("invalid subresource")
        league_key = self._league_key(league_id)
        url = f"{self._url('league')}/{league_key}/{subresource}"
        return self.query(url)

    def league_free_agents(
        self,
        league_id,
        start=0,
        subresource="players",
        status="A",
        sort="AR",
        sort_type="lastmonth",
    ):
        """
        Gets league free agents

        Args:
            league_id (int): id for your league
            start(int): offset (returns 25 at a time)
            subresource (str): metadata, settings, standings, scoreboard, etc.
            status(str): 'A', 'FA', 'T', etc.
            sort(str): 'OR', 'AR', stat_code, etc.
            sort_type(str): 'lastmonth', etc.

        Returns:
            str: XML

        """
        league_key = self._league_key(league_id)
        url = (
            f"{self._url('league')}/{league_key}/{subresource};"
            f"status={status};sort={sort};sort_type={sort_type};start={start}"
        )
        return self.query(url)

    def leagues(self, league_keys, subresource="metadata"):
        """
        Gets leagues collection
        https://developer.yahoo.com/fantasysports/guide/leagues-collection.html

        Args:
            league_keys (list): of str (e.g. '375.l.10000')
            subresource (str): default 'metadata'

        Returns:
            str: XML

        """
        # games adds an additional subresource for teams
        if subresource not in self.league_subresources:
            raise ValueError("invalid league subresource")
        url = f"{self._url('leagues')};league_keys={','.join(league_keys)}/{subresource}"
        return self.query(url)

    def player(self, player_key, subresource="metadata"):
        """
        Gets player resource
        https://developer.yahoo.com/fantasysports/guide/player-resource.html

        Args:
            player_key (str): {game_key}.p.{player_id}

        Returns:
            str: XML

        """
        if subresource not in self.player_subresources:
            raise ValueError("invalid player subresource")
        url = f"{self._url('player')}/{player_key}/{subresource}"
        return self.query(url)

    def player_stats(self, league_id, player_keys):
        """

        Args:
            league_id:
            player_keys:

        Returns:
            str: XML

        TODO: flexible way to specify filters

        """
        league_key = self._league_key(league_id)
        playerstr = ",".join(player_keys)
        url = (
            f'{self._url("league")}/{league_key}/players;player_keys={playerstr}/stats'
        )
        return self.query(url)

    def players(
        self,
        league_id=None,
        league_ids=None,
        team_key=None,
        team_keys=None,
        player_keys=None,
        subresource="metadata",
        filters=None,
    ):
        """
        Gets players collection

        Args:
            league_id (int): id for your league, default None
            league_ids (list): ids for your league, default None
            team_key (str): default None
            team_keys (list): default None
            player_keys (list): default None
            subresource (str): 'metadata', etc.
            filters (dict): default None

        Returns:
            str: XML

       """

        filt_str = ''
        if filters:
            if set(filters.keys()) <= set(self.players_filters):
                filt_str = self._filtstr(filters)
        if league_id:
            league_key = self._league_key(league_id)
            url = (f"{self._url('league')}/{league_key}/players;"
                   f"{filt_str}/{subresource}")
        elif league_ids:
            league_keys = [self._league_key(lid) for lid in league_ids]
            lk_str = ",".join(league_keys)
            url = (f"{self._url('leagues')};league_keys={lk_str}/"
                   f"players;{filt_str}/{subresource}")
        elif team_key:
            url = (f"{self._url('team')}/{team_key}/players;"
                   f"{filt_str}/{subresource}")
        elif team_keys:
            key_str = ",".join(team_keys)
            url = (f"{self._url('teams')};{key_str}/players;"
                   f"{filt_str}/{subresource}")
        elif player_keys:
            key_str = ",".join(player_keys)
            url = (f"{self._url('players')};player_keys={key_str}"
                   f";{filt_str}/{subresource}")
        return self.query(url)

    def query(self, url):
        """
        Query yahoo API

        """
        params = self.response_format
        hdr = {"Authorization": "Bearer %s" % self.auth["access_token"]}
        if self.response_format == "json":
            content = self.get_json(url, params=params, headers=hdr)
            if "error" in content:
                # if get error for valid credentials, refresh and try again
                desc = content["error"]["description"]
                if "Please provide valid credentials" in desc:
                    self._refresh_credentials()
                    return self.get_json(url, params=params, headers=hdr)
        else:
            return self.get(url, params=params, headers=hdr)

    def roster(self, team_key, subresource="players", roster_date=None):
        """
        Gets team resource

        Args:
            team_key (str): id for team
            subresource (str): default 'players'
            roster_date (str): in YYYY-mm-dd format

        Returns:
            str: XML

        """
        if subresource not in self.roster_subresources:
            raise ValueError("invalid roster subresource")
        url = f"{self._url('team')}/{team_key}/roster/{subresource}"
        if roster_date:
            url += ";date={roster_date}"
        return self.query(url)

    def team(self, team_key, subresource="metadata"):
        """
        Gets team resource

        Args:
            team_key (str): id for team
            subresource (str):

        Returns:
            str: XML

        """
        if subresource not in self.team_subresources:
            raise ValueError("invalid team subresource")
        url = f"{self._url('team')}/{team_key}/{subresource}"
        return self.query(url)

    def teams(
        self, league_id=None, team_keys=None, my_team=False, subresource="metadata"
    ):
        """
        Gets teams collection

        Args:
            league_id (int): id for your league
            team_keys (list): of team keys
            subresource (str): default 'metadata'

        Returns:
            str: XML

        """
        if subresource not in self.teams_subresources:
            raise ValueError("invalid teams subresource")
        if league_id:
            league_key = self._league_key(league_id)
            url = f"{self._url('league')}/{league_key}/teams/{subresource}"
        elif team_keys:
            key_str = ",".join(team_keys)
            url = f"{self._url('teams')};team_keys={key_str}/{subresource}"
        elif my_team:
            url = f"{self._url('users')};use_login=1/teams/{subresource}"
        else:
            raise ValueError("need to specify league_id or team_keys or my_team")
        return self.query(url)

    def transaction(self, transaction_key, subresource="metadata"):
        """
        Gets transaction resource

        Args:
            transaction_key (str): id for transaction
            subresource (str):

        Returns:
            str: XML

        """
        if subresource not in self.transaction_subresources:
            raise ValueError("invalid transaction subresource")
        url = f"{self._url('transaction')}/{transaction_key}/{subresource}"
        return self.query(url)

    def transactions(self, league_id, subresource="metadata", filters=None):
        """
        Gets transactions resource

        Args:
            league_id (int): id for league
            subresource (str):
            filters (dict):

        Returns:
            str: XML

        """
        league_key = self._league_key(league_id)
        if subresource not in self.transactions_subresources:
            raise ValueError("invalid transactions subresource")
        if filters:
            if set(filters.keys()) <= set(self.transactions_filters):
                filt_str = self._filtstr(filters)
                url = (f"{self._url('league')}/{league_key}/transactions;"
                       f"{filt_str}/{subresource}")
            else:
                raise ValueError("games invalid filters: %s" % filters)
        else:
            url = f"{self._url('league')}/{league_key}/transactions/{subresource}"
        return self.query(url)

    def user(self, subresource=''):
        """
        Gets user resource. Yahoo recommends using users collection instead

        Args:
            subresource (str): default None

        Returns:
            dict:

        """
        url = (f'https://fantasysports.yahooapis.com/fantasy/v2/users;'
               f'use_login=1/games;game_keys={self.game_key}/{subresource}')
        return self.query(url)

    def users(self, subresource=''):
        """
        Gets users collection

        Args:
            subresource (str): default None

        Returns:
            dict

        """
        url = f"{self._url('users')};use_login=1/{subresource}"
        return self.query(url)


class Parser:
    """
    Parse yahoo fantasy sports API results

    """

    def __init__(self):
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        self._stat_ids = {
            0: "games_played",
            5: "fgp",
            7: "ftm",
            10: "tpm",
            12: "pts",
            15: "reb",
            16: "ast",
            17: "stl",
            18: "blk",
            19: "tov",
        }
        self.data = {}

    @staticmethod
    def _strip_ns(content):
        """
        Strips namespace from xml

        Args:
            content(str):

        Returns:
            str

        """
        return re.sub(r'\sxmlns="[^"]+"', "", str(content), count=1)

    def _game_stat_categories(self, content):
        """
        Parses stat_categories from game resource

        Args:
            content (str):

        Returns:
            list: of dict
        """

    def _stat_name(self, stat_id):
        """
        Yahoo standings use stat id rather than name

        """
        return self._stat_ids.get(stat_id)

    def game(self, content):
        """
        Parses game resource

        Args:
            content (str):

        Returns:
            list: of dict

        """
        root = ET.fromstring(Parser._strip_ns(content))
        vals = [{child.tag: child.text for child in game}
                  for game in root.iter("game")]
        self.data['game'] = vals
        return vals

    def league_free_agents(self, content):
        """
        Parses league with players subresource

        Args:
            content(str): XML string

        Returns:
            list: of dict (player_key, player_name, eligible_postiions, team)

        """
        vals = []
        root = ET.fromstring(Parser._strip_ns(content))
        for player in root.findall(".//player"):
            player_d = {
                "player_key": player.find("player_key").text,
                "player_name": player.find("name").find("full").text,
            }
            positions = [
                elpos for elpos in player.find("eligible_positions").findall("position")
            ]
            player_d["eligible_positions"] = ", ".join([pos.text for pos in positions])
            player_d["team"] = player.find("editorial_team_abbr").text.upper()
            vals.append(player_d)
        self.data['league_free_agents'] = vals
        return vals

    def league_standings(self, content):
        """
        Parses league with standings subresource

        Args:
            content(str): XML string

        Returns:
            list: of dict

        """
        vals = []
        root = ET.fromstring(Parser._strip_ns(content))
        for team in root.findall(".//standings/teams/team"):
            team_d = {
                "team_key": team.find("team_key").text,
                "team_name": team.find("name").text,
            }
            team_standings = team.find("team_standings")
            team_d["rank"] = team_standings.find("rank").text
            team_d["points_for"] = team_standings.find("points_for").text
            for stat in team.find(".//team_stats/stats"):
                stat_id = int(stat.find("stat_id").text)
                stat_name = self._stat_name(stat_id)
                if stat_name:
                    val = stat.find("value").text
                    team_d[stat_name] = val
            for stat in team.find(".//team_points/stats"):
                stat_id = int(stat.find("stat_id").text)
                stat_name = self._stat_name(stat_id)
                if stat_name:
                    val = stat.find("value").text
                    team_d[f"{stat_name}_pts"] = val
            vals.append(team_d)
        self.data['league_standings'] = vals
        return vals

    def leagues(self, content):
        """
        Parses leagues collection

        Args:
            content (str): XML

        Returns:
            list: of dict

        """
        root = ET.fromstring(Parser._strip_ns(content))
        vals = [
            {child.tag: child.text for child in league}
            for league in root.iter("league")
        ]
        self.data['leagues'] = vals
        return vals

    def player_stats(self, content):
        """
        Parses players with stats subresource

        Args:
            content(str): XML string

        Returns:
            list: of dict

        """
        vals = []
        root = ET.fromstring(Parser._strip_ns(content))
        for player in root.findall(".//player"):
            player_d = {
                "player_key": player.find("player_key").text,
                "player_name": player.find("name").find("full").text,
            }
            positions = [
                elpos for elpos in player.find("eligible_positions").findall("position")
            ]
            player_d["eligible_positions"] = ", ".join([pos.text for pos in positions])
            player_d["team"] = player.find("editorial_team_abbr").text.upper()
            for stat in player.find(".//player_stats/stats"):
                stat_id = int(stat.find("stat_id").text)
                stat_name = self._stat_name(stat_id)
                if stat_name:
                    val = stat.find("value").text
                    player_d[stat_name] = val
            vals.append(player_d)
        self.data['player_stats'] = vals
        return vals

    def user_leagues(self, content, game_key):
        """
        Parses user collection with leagues subresource

        Args:
            content(str): XML
            game_key(int): e.g. 385

        Returns:
            list: of dict

        """
        root = ET.fromstring(Parser._strip_ns(content))
        vals = []
        for node in root.findall(".//game"):
            if node.find("game_key").text == str(game_key):
                for league in node.findall(".//league"):
                    vals.append({child.tag: child.text for child in league})
        self.data['user_leagues'] = vals
        return vals


if __name__ == "__main__":
    pass
