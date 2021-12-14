from quart import Quart, redirect, url_for, render_template_string
from quart_discord import DiscordOAuth
from quart_discord.exceptions import NotSignedIn

CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
REDIRECT_URI = "redirect_uri"

app = Quart(__name__)
app.config["SECRET_KEY"] = CLIENT_SECRET

discord = DiscordOAuth(
    app, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI,
    debug=True
)


@app.route("/login/")
async def login():
    return discord.prepare_login("scope", "identify")


@app.route("/callback/")
async def callback():
    discord.callback()
    return redirect(url_for(".me"))


@app.errorhandler(NotSignedIn)
async def redirect_unauthorized(e):
    return redirect(url_for("login"))


@app.route("/me")
@discord.require_discord_oauth
async def me():
    user = discord.user()
    return await render_template_string(
        f"<h1>Hello {user['username']}</h1>"
    )


app.run(port=8080)
