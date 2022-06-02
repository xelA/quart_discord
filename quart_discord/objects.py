from . import utils

DISCORD_CDN = "https://cdn.discordapp.com"


class User:
    def __init__(self, data: dict):
        self.id = int(data["id"])
        self.name = data["username"]
        self.created_at = utils.snowflake_time(self.id)
        self.discriminator = data["discriminator"]
        self.avatar = data["avatar"]
        self.banner = data["banner"]

    def __int__(self):
        return self.id

    def __str__(self):
        return self.user

    def __repr__(self):
        return f"<User name={self.name} discriminator={self.discriminator} " \
            f"id={self.id}>"

    @property
    def user(self):
        return f"{self.name}#{self.discriminator}"

    @property
    def avatar_url(self):
        img_format = "gif" if self.avatar.startswith("a_") else "png"
        return f"{DISCORD_CDN}/avatars/{self.id}/{self.avatar}.{img_format}"

    @property
    def banner_url(self):
        img_format = "gif" if self.banner.startswith("a_") else "png"
        return f"{DISCORD_CDN}/banners/{self.id}/{self.banner}.{img_format}"


class Member:
    def __init__(self, data: dict, data_guild: dict):
        self.guild = Guild(data_guild)
        self.id = self._id(data)
        self.created_at = self._created_at()
        self.name = data.get("user", {}).get("username", None)
        self.joined_at = utils.parse_time(data.get("joined_at", None))
        self.discriminator = data.get("user", {}).get("discriminator", None)
        self.avatar = data.get("user", {}).get("avatar", None)
        self.nick = data.get("nick", None)
        self.roles = [int(role) for role in data.get("roles", [])]

    def __int__(self):
        return self.id

    def __str__(self):
        return self.name

    def _id(self, data):
        get_id = data.get("user", {}).get("id", None)
        if not get_id:
            return None
        return int(get_id)

    def _created_at(self):
        if not self.id:
            return None
        return utils.snowflake_time(self.id)

    def __repr__(self):
        return f"<Member id={self.id} name={self.name} discriminator={self.discriminator} " \
            f"guild=<Guild id={self.guild.id} name={self.guild.name}>>"


class Guild:
    def __init__(self, data: dict):
        self.id = int(data["id"])
        self.name = data["name"]
        self.owner = data["owner"]
        self.icon = data["icon"]
        self.permissions = data["permissions"]
        self.features = data["features"]

    def __str__(self):
        return self.name

    def __int__(self):
        return self.id

    def __repr__(self):
        return f"<Guild name={self.name} id={self.id}>"

    @property
    def icon_url(self):
        img_format = "gif" if self.icon.startswith("a_") else "png"
        return f"{DISCORD_CDN}/icons/{self.id}/{self.icon}.{img_format}"
