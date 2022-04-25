import json
import os

from quart import Quart, redirect, url_for, render_template_string
from quart_discord import DiscordOAuth, NotSignedIn

with open("./config.json", "r") as f:
    config = json.load(f)

app = Quart(__name__)
app.config["SECRET_KEY"] = config["client_secret"]
if "http://" in config["redirect_uri"]:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"

discord = DiscordOAuth(
    app, config["client_id"], config["client_secret"],
    config["redirect_uri"], debug=config["debug"]
)


@app.route("/")
async def index():
    return await render_template_string("\n".join([
        "<h1>Welcome to the Discord OAuth example</h1>",
        "<a href='{{ url_for('.login') }}'>Login</a>",
    ]))


@app.route("/login")
async def login():
    return discord.prepare_login(
        "identify", "guilds", "guilds.members.read"
    )


@app.route("/logout")
async def logout():
    discord.clear_session()
    return redirect(url_for(".index"))


@app.route("/callback")
async def callback():
    return discord.callback(".me")


@app.errorhandler(NotSignedIn)
async def redirect_unauthorized(e):
    return redirect(url_for("login"))


@app.route("/me")
@discord.require_discord_oauth
async def me():
    user = discord.user()
    guilds = discord.guilds()
    return await render_template_string("\n".join([
        f"<h1>Hello {user}</h1>",
        f"<h4>Created: {user.created_at}</h4>",

        f"Logout: <a href='{url_for('.logout')}'>Logout</a>",
        "<h2>Guilds</h2>",
        f"<ul>{''.join(f'<li>{guild}</li>' for guild in guilds)}</ul>",
    ]))


@app.route("/me/<int:guild_id>")
@discord.require_discord_oauth
async def me_guild(guild_id):
    user = discord.user()
    member = discord.member(guild_id)
    return await render_template_string("\n".join([
        f"<h1>Hello {user}</h1>",
        f"<h4>Created: {user.created_at}</h4>",
        f"Logout: <a href='{url_for('.logout')}'>Logout</a>",
        "<h2>Guild</h2>",
        f"{member if member else 'Guild not found'}",
    ]))


app.run(port=config["port"])
