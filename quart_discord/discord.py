import time
import functools

from quart import request, session, redirect, url_for, current_app
from requests_oauthlib import OAuth2Session
from .exceptions import AccessDenied, HTTPException, NotSignedIn
from .objects import Guild, User, Member


class Cache:
    def __init__(self, cache_time: int):
        self.storage = {}
        self._cache_time = cache_time

    def _check_clean(self):
        for g in list(self.storage):
            if self.storage[g]["expire"] < time.time():
                del self.storage[g]

    def get(self, key: str):
        self._check_clean()

        if key not in self.storage:
            return None
        return self.storage[key]["data"]

    def insert(self, key: str, value: dict):
        self._check_clean()

        self.storage[key] = {
            "expire": time.time() + self._cache_time,
            "data": value
        }
        return value


class DiscordOAuth:
    def __init__(self, app, client_id: int, client_secret: str, redirect_uri: str, debug: bool = False):
        self.app = app
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self.debug = debug
        self._cache = Cache(cache_time=15)

        self.api_base_url = "https://discordapp.com/api/v9"

    def print_debug(self, message: str) -> None:
        """ The debug method, idk """
        if self.debug:
            print(message)

    def query(self, path: str, method: str = "get") -> dict:
        """ Make a query to the Discord API """
        oauth2_token = session.get("oauth2_token", None)
        if not oauth2_token:
            raise NotSignedIn()

        discord = self.make_session(token=oauth2_token)
        discord_query = getattr(discord, method)
        r = discord_query(f"{self.api_base_url}{path}")

        if r.status_code == 429:
            raise HTTPException(r.status_code, r.json(), path)
        return r.json()

    def guilds(self, guild_id: int = None) -> list[Guild] or Guild:
        """ Fetch the guilds of @me user """
        user_id = session.get("user_id", None)
        if not user_id:
            user_id = self.user().id

        data = self._cache.get(f"GUILDS:{user_id}")

        if not data:
            discord_data = self.query("/users/@me/guilds")
            data = self._cache.insert(f"GUILDS:{user_id}", {
                "guilds": discord_data
            })

        all_guilds = [Guild(guild) for guild in data["guilds"]]
        if not guild_id:
            return all_guilds
        return next((g for g in all_guilds if g.id == guild_id), None)

    def member(self, guild_id: int) -> Member:
        """ Fetch @me member info from a guild """
        guild = self.guilds(guild_id)
        if not guild:
            return None
        data = self.query(f"/users/@me/guilds/{guild_id}/member")
        return Member(data, guild.__dict__)

    def user(self) -> User:
        """ Return User object or fetch if cache is old or not set """
        user_id = session.get("user_id", None)
        data = self._cache.get(f"USER:{user_id}")

        if not data:
            discord_data = self.query("/users/@me")
            session["user_id"] = discord_data['id']

            data = self._cache.insert(f"USER:{discord_data['id']}", {
                "id": discord_data["id"],
                "username": discord_data["username"],
                "banner": discord_data["banner"],
                "avatar": discord_data["avatar"],
                "discriminator": discord_data["discriminator"]
            })

            self.print_debug("DiscordOAuth.user: request")

        user_object = User(data)
        self.print_debug(f"DiscordOAuth.user: {user_object}")
        return user_object

    def token_update(self, token) -> str:
        """ Update the oauth token in the session """
        session["oauth2_token"] = token
        return token

    def require_discord_oauth(self, func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not session.get("oauth2_state", None):
                session["redirect_url"] = request.url
                return redirect(url_for(".login"))
            return await current_app.ensure_async(func)(*args, **kwargs)
        return wrapper

    def prepare_login(self, *scopes) -> str:
        """ Prepare the login url """
        scope = request.args.get("scope", " ".join(scopes))
        discord = self.make_session(scope=scope.split(" "))
        authorization_url, state = discord.authorization_url(
            f"{self.api_base_url}/oauth2/authorize"
        )
        session["oauth2_state"] = state
        return redirect(authorization_url)

    def clear_session(self) -> None:
        """ Clear the session """
        return session.clear()

    def make_session(self, token=None, state=None, scope=None) -> OAuth2Session:
        """ Make a new OAuth2 session """
        return OAuth2Session(
            client_id=self.client_id,
            token=token, state=state, scope=scope,
            redirect_uri=self.redirect_uri,
            auto_refresh_kwargs={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            auto_refresh_url=f"{self.api_base_url}/oauth2/token",
            token_updater=self.token_update,
        )

    def callback(self, redirect_url_for: str = None) -> str:
        """ Callback from Discord """
        error = request.args.get("error")
        if error:
            if error == "access_denied":
                raise AccessDenied("Access denied")
            raise HTTPException(f"Unknown error: {error}")
        discord = self.make_session(state=session["oauth2_state"])
        token = discord.fetch_token(
            f"{self.api_base_url}/oauth2/token", client_secret=self.client_secret,
            authorization_response=request.url
        )
        self.token_update(token)

        if redirect_url_for:
            return redirect(url_for(redirect_url_for))
        return token
