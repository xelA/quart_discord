import time
import functools

from quart import request, session, redirect, url_for, current_app
from requests_oauthlib import OAuth2Session
from .exceptions import AccessDenied, HTTPException, NotSignedIn


class DiscordOAuth:
    def __init__(self, app, client_id: int, client_secret: str, redirect_uri: str, debug: bool = False):
        self.app = app
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.debug = debug
        self.api_base_url = "https://discordapp.com/api"

    def print_debug(self, message: str):
        if self.debug:
            print(message)

    def fetch_user(self):
        if "oauth2_token" not in session:
            raise NotSignedIn()

        discord = self.make_session(token=session["oauth2_token"])
        user = discord.get(f"{self.api_base_url}/users/@me").json()
        if "id" not in user:
            return None

        print(user)
        img_format = "gif" if user["avatar"].startswith("a_") else "png"
        return {
            "expire": time.time() + 3600,
            "id": int(user["id"]),
            "user": f"{user['username']}#{user['discriminator']}",
            "username": user["username"],
            "avatar": f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.{img_format}?size=1024",
        }

    def user(self):
        cache = session.get("discord_user", None)
        if not cache:
            cache = self.fetch_user()
            session["discord_user"] = cache
            self.print_debug("DiscordOAuth.user: request")
        if cache["expire"] < time.time():
            cache = self.fetch_user()
            session["discord_user"] = cache
        self.print_debug(f"DiscordOAuth.user: {cache}")
        return cache

    def token_update(self, token):
        session["oauth2_token"] = token

    def require_discord_oauth(self, func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if "oauth2_state" not in session:
                return redirect(url_for(".login"))
            return await current_app.ensure_async(func)(
                *args, **kwargs
            )
        return wrapper

    def prepare_login(self, *scopes):
        scope = request.args.get(*scopes)
        discord = self.make_session(scope=scope.split(" "))

        authorization_url, state = discord.authorization_url(
            f"{self.api_base_url}/oauth2/authorize"
        )
        session["oauth2_state"] = state
        return redirect(authorization_url)

    def clear_session(self):
        return session.clear()

    def make_session(self, token=None, state=None, scope=None):
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

    def callback(self):
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
        return token
