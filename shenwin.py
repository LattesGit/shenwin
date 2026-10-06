#!/usr/bin/env python3

import sys
import re
import csv
import json
import time
import html
import random
import argparse
import hashlib
import threading
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from html.parser import HTMLParser

VERSION = "3.0.0"
DEFAULT_TIMEOUT = 8
DEFAULT_RETRIES = 2
DEFAULT_WORKERS = 12
MAX_BODY = 524288
USER_AGENT = f"SHENWIN/{VERSION} (+username-osint)"

R = "\033[0;31m"
G = "\033[0;32m"
Y = "\033[1;33m"
B = "\033[0;34m"
C = "\033[0;36m"
M = "\033[0;35m"
W = "\033[1;37m"
DG = "\033[2;37m"
RESET = "\033[0m"
BOLD = "\033[1m"

RABBIT_TEMPLATE = """
{W}
    {C}(\\ /)
    {C}( . .)  {W}S H E N W I N
    {C}c{W}("{C}){W}("{C})   {DG}OSINT Username Hunter{W}
    {C} |   |
    {C}_|___|_{RESET}
"""

BANNER_TEMPLATE = """
{C}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  {W} ███████╗██╗  ██╗███████╗███╗   ██╗██╗    ██╗██╗███╗   ██╗ {C}║
║  {W} ██╔════╝██║  ██║██╔════╝████╗  ██║██║    ██║██║████╗  ██║ {C}║
║  {W} ███████╗███████║█████╗  ██╔██╗ ██║██║ █╗ ██║██║██╔██╗ ██║ {C}║
║  {W} ╚════██║██╔══██║██╔══╝  ██║╚██╗██║██║███╗██║██║██║╚██╗██║ {C}║
║  {W} ███████║██║  ██║███████╗██║ ╚████║╚███╔███╔╝██║██║ ╚████║ {C}║
║  {W} ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝ {C}║
║                                                              ║
║  {DG} v{VERSION}  |  OSINT Username Intelligence Engine  |  LatenT {C}║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""

def rabbit():
    return RABBIT_TEMPLATE.format(
        R=R, G=G, Y=Y, B=B, C=C, M=M, W=W, DG=DG, RESET=RESET, BOLD=BOLD
    )

def banner():
    return BANNER_TEMPLATE.format(
        R=R, G=G, Y=Y, B=B, C=C, M=M, W=W, DG=DG, RESET=RESET, BOLD=BOLD,
        VERSION=VERSION
    )

class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = []
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            data = dict(attrs)
            key = data.get("name") or data.get("property")
            value = data.get("content")
            if key and value:
                self.meta[key.lower()] = value

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)

    def result(self):
        return " ".join(" ".join(self.title).split()), self.meta

@dataclass(frozen=True)
class Platform:
    name: str
    category: str
    url: str
    negative_markers: tuple = ()
    positive_markers: tuple = ()
    strong_positive: tuple = ()
    strong_negative: tuple = ()

@dataclass
class CheckResult:
    username: str
    platform: str
    category: str
    url: str
    status: str
    confidence: int
    score: int
    http_status: int
    reason: str
    elapsed_ms: int
    final_url: str
    title: str
    fingerprint: str
    evidence: list
    error: str = ""

NEGATIVE_COMMON = (
    "page not found",
    "user not found",
    "profile not found",
    "account not found",
    "does not exist",
    "doesn't exist",
    "not found",
    "404",
    "this page isn't available",
    "this page is unavailable",
    "sorry, that page",
    "couldn't find",
    "cannot find",
    "no such user",
    "unknown user",
    "user does not exist",
    "account doesn't exist",
)

POSITIVE_COMMON = (
    "profile",
    "followers",
    "following",
    "member",
    "joined",
    "posts",
    "followers",
    "bio",
    "repositories",
    "projects",
    "activity",
)

PLATFORMS = []

def add(name, category, url, negative=NEGATIVE_COMMON, positive=POSITIVE_COMMON, strong_positive=(), strong_negative=()):
    PLATFORMS.append(
        Platform(
            name=name,
            category=category,
            url=url,
            negative_markers=tuple(x.lower() for x in negative),
            positive_markers=tuple(x.lower() for x in positive),
            strong_positive=tuple(x.lower() for x in strong_positive),
            strong_negative=tuple(x.lower() for x in strong_negative),
        )
    )

add("GitHub", "Development", "https://github.com/{}",
    strong_positive=("repositories", "contributions", "github"))

add("GitLab", "Development", "https://gitlab.com/{}",
    strong_positive=("projects", "gitlab"))
add("Bitbucket", "Development", "https://bitbucket.org/{}",
    strong_positive=("repositories", "bitbucket"))
add("Codeberg", "Development", "https://codeberg.org/{}",
    strong_positive=("repositories", "codeberg"))
add("Gitea", "Development", "https://gitea.com/{}",
    strong_positive=("repositories", "gitea"))
add("SourceHut", "Development", "https://sr.ht/~{}",
    strong_positive=("projects", "sourcehut"))
add("Hacker News", "Development", "https://news.ycombinator.com/user?id={}",
    strong_positive=("karma", "hacker news"))
add("Dev.to", "Development", "https://dev.to/{}",
    strong_positive=("articles", "dev.to"))
add("Replit", "Development", "https://replit.com/@{}",
    strong_positive=("repls", "replit"))
add("CodePen", "Development", "https://codepen.io/{}",
    strong_positive=("pens", "codepen"))
add("Keybase", "Development", "https://keybase.io/{}",
    strong_positive=("proofs", "keybase"))
add("Docker Hub", "Development", "https://hub.docker.com/u/{}",
    strong_positive=("repositories", "docker hub"))
add("NPM", "Development", "https://www.npmjs.com/~{}",
    strong_positive=("packages", "npm"))
add("PyPI", "Development", "https://pypi.org/user/{}/",
    strong_positive=("projects", "pypi"))
add("Crates.io", "Development", "https://crates.io/users/{}",
    strong_positive=("crates", "crates.io"))
add("RubyGems", "Development", "https://rubygems.org/profiles/{}",
    strong_positive=("gems", "rubygems"))
add("Packagist", "Development", "https://packagist.org/users/{}",
    strong_positive=("packages", "packagist"))
add("NuGet", "Development", "https://www.nuget.org/profiles/{}",
    strong_positive=("packages", "nuget"))
add("Launchpad", "Development", "https://launchpad.net/~{}",
    strong_positive=("launchpad", "projects"))
add("SourceForge", "Development", "https://sourceforge.net/u/{}/profile",
    strong_positive=("sourceforge", "projects"))
add("Lobsters", "Development", "https://lobste.rs/u/{}",
    strong_positive=("stories", "lobsters"))
add("Hackaday", "Development", "https://hackaday.io/{}",
    strong_positive=("projects", "hackaday"))
add("Hackster", "Development", "https://www.hackster.io/{}",
    strong_positive=("projects", "hackster"))
add("Instructables", "Development", "https://www.instructables.com/member/{}",
    strong_positive=("instructables", "projects"))
add("DevRant", "Development", "https://devrant.com/users/{}",
    strong_positive=("devrant", "rants"))
add("Daily.dev", "Development", "https://app.daily.dev/{}",
    strong_positive=("daily.dev",))
add("Peerlist", "Development", "https://peerlist.io/{}",
    strong_positive=("peerlist",))
add("Indie Hackers", "Development", "https://www.indiehackers.com/{}",
    strong_positive=("indie hackers",))
add("WIP", "Development", "https://wip.co/@{}",
    strong_positive=("wip",))
add("Makerlog", "Development", "https://getmakerlog.com/@{}",
    strong_positive=("makerlog",))
add("OSF", "Development", "https://osf.io/profile/{}",
    strong_positive=("osf",))
add("ResearchGate", "Development", "https://www.researchgate.net/profile/{}",
    strong_positive=("researchgate",))
add("ORCID", "Development", "https://orcid.org/{}",
    strong_positive=("orcid",))

add("X", "Social", "https://x.com/{}",
    positive=("followers", "following", "posts"),
    strong_positive=("joined", "x.com"))
add("Instagram", "Social", "https://www.instagram.com/{}/",
    positive=("followers", "following", "posts"),
    strong_positive=("instagram",))
add("TikTok", "Social", "https://www.tiktok.com/@{}",
    positive=("followers", "following", "videos"),
    strong_positive=("tiktok",))
add("YouTube", "Social", "https://www.youtube.com/@{}",
    positive=("subscribers", "videos", "channel"),
    strong_positive=("youtube", "subscribers"))
add("Facebook", "Social", "https://www.facebook.com/{}",
    positive=("friends", "posts", "profile"),
    strong_positive=("facebook",))
add("Pinterest", "Social", "https://www.pinterest.com/{}/",
    positive=("followers", "following", "pins"),
    strong_positive=("pinterest",))
add("Snapchat", "Social", "https://www.snapchat.com/add/{}",
    strong_positive=("snapchat",))
add("Tumblr", "Social", "https://{}.tumblr.com",
    positive=("posts", "followers"),
    strong_positive=("tumblr",))
add("Reddit", "Social", "https://www.reddit.com/user/{}",
    positive=("karma", "post karma", "comment karma"),
    strong_positive=("reddit", "karma"))
add("Mastodon", "Social", "https://mastodon.social/@{}",
    positive=("followers", "following", "posts"),
    strong_positive=("mastodon",))
add("Bluesky", "Social", "https://bsky.app/profile/{}.bsky.social",
    positive=("followers", "following", "posts"),
    strong_positive=("bluesky",))
add("Threads", "Social", "https://www.threads.net/@{}",
    positive=("followers", "following", "replies"),
    strong_positive=("threads",))
add("LinkedIn", "Social", "https://www.linkedin.com/in/{}",
    positive=("experience", "education", "connections"),
    strong_positive=("linkedin",))
add("Quora", "Social", "https://www.quora.com/profile/{}",
    positive=("answers", "followers", "following"),
    strong_positive=("quora",))
add("VK", "Social", "https://vk.com/{}",
    positive=("friends", "followers", "photos"),
    strong_positive=("vk",))
add("OK.ru", "Social", "https://ok.ru/{}",
    positive=("friends", "photos", "groups"),
    strong_positive=("одноклассники",))
add("Weibo", "Social", "https://weibo.com/{}",
    positive=("followers", "following", "posts"),
    strong_positive=("weibo",))
add("Minds", "Social", "https://www.minds.com/{}",
    positive=("followers", "following", "posts"),
    strong_positive=("minds",))
add("Gab", "Social", "https://gab.com/{}",
    positive=("followers", "following", "posts"),
    strong_positive=("gab",))
add("Clubhouse", "Social", "https://www.joinclubhouse.com/@{}",
    strong_positive=("clubhouse",))
add("LiveJournal", "Social", "https://{}.livejournal.com",
    positive=("entries", "friends"),
    strong_positive=("livejournal",))
add("Ello", "Social", "https://ello.co/{}",
    strong_positive=("ello",))
add("Plurk", "Social", "https://www.plurk.com/{}",
    strong_positive=("plurk",))
add("Blogger", "Social", "https://{}.blogspot.com",
    strong_positive=("blogger",))
add("WordPress.com", "Social", "https://{}.wordpress.com",
    strong_positive=("wordpress",))
add("Substack", "Social", "https://{}.substack.com",
    strong_positive=("substack",))
add("Hashnode", "Social", "https://hashnode.com/@{}",
    strong_positive=("hashnode",))
add("BeReal", "Social", "https://bere.al/{}",
    strong_positive=("bereal",))
add("Cara", "Social", "https://cara.app/{}",
    strong_positive=("cara",))
add("Cohost", "Social", "https://cohost.org/{}",
    strong_positive=("cohost",))
add("Micro.blog", "Social", "https://micro.blog/{}",
    strong_positive=("micro.blog",))
add("MeWe", "Social", "https://mewe.com/i/{}",
    strong_positive=("mewe",))
add("Diaspora", "Social", "https://diaspora.social/u/{}",
    strong_positive=("diaspora",))
add("Fosstodon", "Social", "https://fosstodon.org/@{}",
    strong_positive=("fosstodon",))
add("Lemmy", "Social", "https://lemmy.ml/u/{}",
    strong_positive=("lemmy",))
add("Beehaw", "Social", "https://beehaw.org/u/{}",
    strong_positive=("beehaw",))
add("Tildes", "Social", "https://tildes.net/user/{}",
    strong_positive=("tildes",))
add("Amino", "Social", "https://aminoapps.com/u/{}",
    strong_positive=("amino",))

add("Twitch", "Streaming", "https://www.twitch.tv/{}",
    positive=("followers", "following", "videos"),
    strong_positive=("twitch",))
add("Kick", "Streaming", "https://kick.com/{}",
    positive=("followers", "following", "videos"),
    strong_positive=("kick",))
add("Vimeo", "Streaming", "https://vimeo.com/{}",
    positive=("videos", "followers"),
    strong_positive=("vimeo",))
add("Dailymotion", "Streaming", "https://www.dailymotion.com/{}",
    positive=("videos", "followers"),
    strong_positive=("dailymotion",))
add("Rumble", "Streaming", "https://rumble.com/user/{}",
    positive=("followers", "videos"),
    strong_positive=("rumble",))
add("Odysee", "Streaming", "https://odysee.com/@{}",
    positive=("followers", "videos"),
    strong_positive=("odysee",))
add("BitChute", "Streaming", "https://www.bitchute.com/channel/{}",
    positive=("subscribers", "videos"),
    strong_positive=("bitchute",))
add("PeerTube", "Streaming", "https://peertube.social/accounts/{}",
    positive=("followers", "videos"),
    strong_positive=("peertube",))
add("Bilibili", "Streaming", "https://space.bilibili.com/{}",
    positive=("followers", "videos"),
    strong_positive=("bilibili",))
add("Niconico", "Streaming", "https://www.nicovideo.jp/user/{}",
    positive=("videos", "followers"),
    strong_positive=("nicovideo",))
add("Streamlabs", "Streaming", "https://streamlabs.com/{}",
    strong_positive=("streamlabs",))
add("Trovo", "Streaming", "https://trovo.live/s/{}",
    positive=("followers", "following"),
    strong_positive=("trovo",))

add("Steam", "Gaming", "https://steamcommunity.com/id/{}",
    positive=("games", "friends", "level"),
    strong_positive=("steam community",))
add("Roblox", "Gaming", "https://www.roblox.com/user.aspx?username={}",
    positive=("roblox", "profile", "friends"),
    strong_positive=("roblox",))
add("Chess.com", "Gaming", "https://www.chess.com/member/{}",
    positive=("games", "rating", "followers"),
    strong_positive=("chess.com",))
add("Lichess", "Gaming", "https://lichess.org/@/{}",
    positive=("games", "rating", "followers"),
    strong_positive=("lichess",))
add("Itch.io", "Gaming", "https://{}.itch.io",
    positive=("games", "projects"),
    strong_positive=("itch.io",))
add("GameBanana", "Gaming", "https://gamebanana.com/members/{}",
    positive=("submissions", "followers"),
    strong_positive=("gamebanana",))
add("Nexus Mods", "Gaming", "https://www.nexusmods.com/users/{}",
    positive=("mods", "posts"),
    strong_positive=("nexus mods",))
add("Speedrun.com", "Gaming", "https://www.speedrun.com/user/{}",
    positive=("runs", "games"),
    strong_positive=("speedrun.com",))
add("FACEIT", "Gaming", "https://www.faceit.com/en/players/{}",
    positive=("matches", "wins", "friends"),
    strong_positive=("faceit",))
add("ESEA", "Gaming", "https://play.esea.net/users/{}",
    strong_positive=("esea",))
add("Leetify", "Gaming", "https://leetify.com/app/profile/{}",
    strong_positive=("leetify",))
add("HLTV", "Gaming", "https://www.hltv.org/profile/{}",
    positive=("matches", "teams"),
    strong_positive=("hltv",))
add("Battlefy", "Gaming", "https://battlefy.com/users/{}",
    strong_positive=("battlefy",))
add("Challonge", "Gaming", "https://challonge.com/users/{}",
    strong_positive=("challonge",))
add("Game Jolt", "Gaming", "https://gamejolt.com/@{}",
    strong_positive=("gamejolt",))
add("Kongregate", "Gaming", "https://www.kongregate.com/accounts/{}",
    strong_positive=("kongregate",))
add("Newgrounds", "Gaming", "https://{}.newgrounds.com",
    strong_positive=("newgrounds",))
add("Armor Games", "Gaming", "https://armorgames.com/user/{}",
    strong_positive=("armor games",))
add("GOG", "Gaming", "https://www.gog.com/u/{}",
    strong_positive=("gog",))
add("IGDB", "Gaming", "https://www.igdb.com/users/{}",
    strong_positive=("igdb",))
add("Backloggd", "Gaming", "https://www.backloggd.com/u/{}",
    strong_positive=("backloggd",))
add("Grouvee", "Gaming", "https://www.grouvee.com/user/{}",
    strong_positive=("grouvee",))
add("Fortnite Tracker", "Gaming", "https://fortnitetracker.com/profile/all/{}",
    strong_positive=("fortnite tracker",))
add("R6 Tracker", "Gaming", "https://r6.tracker.network/profile/{}",
    strong_positive=("r6 tracker",))
add("Toornament", "Gaming", "https://www.toornament.com/en_US/player/{}",
    strong_positive=("toornament",))

add("Spotify", "Music", "https://open.spotify.com/user/{}",
    positive=("playlists", "followers", "following"),
    strong_positive=("spotify",))
add("SoundCloud", "Music", "https://soundcloud.com/{}",
    positive=("followers", "following", "tracks"),
    strong_positive=("soundcloud",))
add("Last.fm", "Music", "https://www.last.fm/user/{}",
    positive=("scrobbles", "tracks", "artists"),
    strong_positive=("last.fm",))
add("Bandcamp", "Music", "https://{}.bandcamp.com",
    positive=("music", "albums", "tracks"),
    strong_positive=("bandcamp",))
add("ReverbNation", "Music", "https://www.reverbnation.com/{}",
    strong_positive=("reverbnation",))
add("Audiomack", "Music", "https://audiomack.com/{}",
    positive=("followers", "tracks"),
    strong_positive=("audiomack",))
add("Mixcloud", "Music", "https://www.mixcloud.com/{}",
    positive=("followers", "shows"),
    strong_positive=("mixcloud",))
add("MuseScore", "Music", "https://musescore.com/user/{}",
    positive=("scores", "followers"),
    strong_positive=("musescore",))
add("Musixmatch", "Music", "https://www.musixmatch.com/profile/{}",
    strong_positive=("musixmatch",))
add("Genius", "Music", "https://genius.com/{}",
    positive=("songs", "artists", "contributions"),
    strong_positive=("genius",))
add("Songkick", "Music", "https://www.songkick.com/users/{}",
    positive=("concerts", "artists"),
    strong_positive=("songkick",))
add("Setlist.fm", "Music", "https://www.setlist.fm/user/{}",
    positive=("setlists", "concerts"),
    strong_positive=("setlist",))
add("Rate Your Music", "Music", "https://rateyourmusic.com/~{}",
    strong_positive=("rate your music",))
add("Discogs", "Music", "https://www.discogs.com/user/{}",
    positive=("collection", "wantlist"),
    strong_positive=("discogs",))
add("Deezer", "Music", "https://www.deezer.com/en/profile/{}",
    strong_positive=("deezer",))

add("Flickr", "Art", "https://www.flickr.com/people/{}",
    positive=("photos", "followers", "following"),
    strong_positive=("flickr",))
add("500px", "Art", "https://500px.com/p/{}",
    positive=("photos", "followers"),
    strong_positive=("500px",))
add("Unsplash", "Art", "https://unsplash.com/@{}",
    positive=("photos", "followers"),
    strong_positive=("unsplash",))
add("Pexels", "Art", "https://www.pexels.com/@{}",
    positive=("photos", "followers"),
    strong_positive=("pexels",))
add("DeviantArt", "Art", "https://www.deviantart.com/{}",
    positive=("deviations", "watchers"),
    strong_positive=("deviantart",))
add("ArtStation", "Art", "https://www.artstation.com/{}",
    positive=("projects", "followers"),
    strong_positive=("artstation",))
add("Behance", "Art", "https://www.behance.net/{}",
    positive=("projects", "followers"),
    strong_positive=("behance",))
add("Dribbble", "Art", "https://dribbble.com/{}",
    positive=("shots", "followers"),
    strong_positive=("dribbble",))
add("Figma", "Art", "https://www.figma.com/@{}",
    strong_positive=("figma",))
add("Pixiv", "Art", "https://www.pixiv.net/en/users/{}",
    positive=("illustrations", "followers"),
    strong_positive=("pixiv",))
add("Sketchfab", "Art", "https://sketchfab.com/{}",
    positive=("models", "followers"),
    strong_positive=("sketchfab",))
add("Thingiverse", "Art", "https://www.thingiverse.com/{}",
    positive=("designs", "followers"),
    strong_positive=("thingiverse",))
add("Cults3D", "Art", "https://cults3d.com/en/users/{}",
    strong_positive=("cults3d",))
add("Printables", "Art", "https://www.printables.com/@{}",
    positive=("models", "followers"),
    strong_positive=("printables",))
add("CGTrader", "Art", "https://www.cgtrader.com/{}",
    strong_positive=("cgtrader",))
add("TurboSquid", "Art", "https://www.turbosquid.com/Search/Artists/{}",
    strong_positive=("turbosquid",))
add("VSCO", "Art", "https://vsco.co/{}",
    positive=("followers", "photos"),
    strong_positive=("vsco",))
add("Glass", "Art", "https://glass.photo/{}",
    strong_positive=("glass",))
add("Pixilart", "Art", "https://www.pixilart.com/{}",
    strong_positive=("pixilart",))

add("Medium", "Writing", "https://medium.com/@{}",
    positive=("followers", "following", "stories"),
    strong_positive=("medium",))
add("Write.as", "Writing", "https://write.as/{}",
    strong_positive=("write.as",))
add("Mirror", "Writing", "https://mirror.xyz/{}",
    strong_positive=("mirror",))
add("Wattpad", "Writing", "https://www.wattpad.com/user/{}",
    positive=("stories", "followers", "following"),
    strong_positive=("wattpad",))
add("FanFiction.net", "Writing", "https://www.fanfiction.net/u/{}",
    strong_positive=("fanfiction",))
add("Archive of Our Own", "Writing", "https://archiveofourown.org/users/{}",
    positive=("works", "bookmarks"),
    strong_positive=("archive of our own",))
add("Quotev", "Writing", "https://www.quotev.com/{}",
    strong_positive=("quotev",))
add("Inkitt", "Writing", "https://www.inkitt.com/{}",
    strong_positive=("inkitt",))
add("Prose.sh", "Writing", "https://prose.sh/{}",
    strong_positive=("prose",))

add("Disqus", "Forums", "https://disqus.com/by/{}/",
    positive=("comments", "following"),
    strong_positive=("disqus",))
add("Discourse", "Forums", "https://meta.discourse.org/u/{}",
    positive=("posts", "topics", "replies"),
    strong_positive=("discourse",))
add("XDA Developers", "Forums", "https://forum.xda-developers.com/member.php?username={}",
    strong_positive=("xda",))
add("Spiceworks", "Forums", "https://community.spiceworks.com/people/{}",
    strong_positive=("spiceworks",))
add("Linus Tech Tips", "Forums", "https://linustechtips.com/profile/{}",
    strong_positive=("linus tech tips",))
add("MetaFilter", "Forums", "https://www.metafilter.com/user/{}",
    strong_positive=("metafilter",))
add("Slashdot", "Forums", "https://slashdot.org/~{}",
    strong_positive=("slashdot",))
add("Know Your Meme", "Forums", "https://knowyourmeme.com/users/{}",
    strong_positive=("know your meme",))
add("Urban Dictionary", "Forums", "https://www.urbandictionary.com/author.php?author={}",
    strong_positive=("urban dictionary",))
add("TV Tropes", "Forums", "https://tvtropes.org/pmwiki/pmwiki.php/Tropers/{}",
    strong_positive=("tv tropes",))
add("Fandom", "Forums", "https://{}.fandom.com",
    strong_positive=("fandom",))

add("Hack The Box", "Cybersecurity", "https://app.hackthebox.com/users/{}",
    positive=("rank", "points", "machines"),
    strong_positive=("hack the box",))
add("TryHackMe", "Cybersecurity", "https://tryhackme.com/p/{}",
    positive=("rooms", "badges", "rank"),
    strong_positive=("tryhackme",))
add("CTFtime", "Cybersecurity", "https://ctftime.org/user/{}",
    positive=("rating", "teams", "events"),
    strong_positive=("ctftime",))
add("PicoCTF", "Cybersecurity", "https://play.picoctf.org/users/{}",
    positive=("points", "solves"),
    strong_positive=("picoctf",))
add("PortSwigger", "Cybersecurity", "https://portswigger.net/web-security/users/{}",
    strong_positive=("portswigger",))
add("Bugcrowd", "Cybersecurity", "https://bugcrowd.com/{}",
    positive=("bug", "researcher", "reputation"),
    strong_positive=("bugcrowd",))
add("HackerOne", "Cybersecurity", "https://hackerone.com/{}",
    positive=("reputation", "reports", "hacktivity"),
    strong_positive=("hackerone",))
add("Intigriti", "Cybersecurity", "https://app.intigriti.com/researcher/{}",
    strong_positive=("intigriti",))
add("Root-Me", "Cybersecurity", "https://www.root-me.org/{}",
    positive=("points", "challenges"),
    strong_positive=("root-me",))
add("Exploit DB", "Cybersecurity", "https://www.exploit-db.com/author/{}",
    strong_positive=("exploit database",))
add("Shodan", "Cybersecurity", "https://www.shodan.io/user/{}",
    strong_positive=("shodan",))
add("VulnHub", "Cybersecurity", "https://www.vulnhub.com/author/{}/",
    strong_positive=("vulnhub",))
add("Hack Club", "Cybersecurity", "https://hackclub.com/{}",
    strong_positive=("hack club",))

add("Duolingo", "Education", "https://www.duolingo.com/profile/{}",
    positive=("followers", "following", "streak"),
    strong_positive=("duolingo",))
add("Khan Academy", "Education", "https://www.khanacademy.org/profile/{}",
    positive=("courses", "badges", "points"),
    strong_positive=("khan academy",))
add("Codecademy", "Education", "https://www.codecademy.com/profiles/{}",
    positive=("courses", "skills"),
    strong_positive=("codecademy",))
add("freeCodeCamp", "Education", "https://www.freecodecamp.org/{}",
    positive=("certifications", "projects"),
    strong_positive=("freecodecamp",))
add("LeetCode", "Education", "https://leetcode.com/{}",
    positive=("solved", "ranking", "contest"),
    strong_positive=("leetcode",))
add("HackerRank", "Education", "https://www.hackerrank.com/{}",
    positive=("badges", "certificates", "skills"),
    strong_positive=("hackerrank",))
add("Codewars", "Education", "https://www.codewars.com/users/{}",
    positive=("honor", "kata", "rank"),
    strong_positive=("codewars",))
add("Exercism", "Education", "https://exercism.org/profiles/{}",
    positive=("exercises", "solutions"),
    strong_positive=("exercism",))
add("CodinGame", "Education", "https://www.codingame.com/profile/{}",
    positive=("puzzles", "score"),
    strong_positive=("codingame",))
add("TopCoder", "Education", "https://www.topcoder.com/members/{}",
    positive=("rating", "competitions"),
    strong_positive=("topcoder",))
add("Codeforces", "Education", "https://codeforces.com/profile/{}",
    positive=("rating", "contests", "solved"),
    strong_positive=("codeforces",))
add("AtCoder", "Education", "https://atcoder.jp/users/{}",
    positive=("rating", "contests"),
    strong_positive=("atcoder",))
add("SPOJ", "Education", "https://www.spoj.com/users/{}",
    positive=("problems solved", "rank"),
    strong_positive=("spoj",))
add("Edabit", "Education", "https://edabit.com/user/{}",
    positive=("challenges", "points"),
    strong_positive=("edabit",))
add("Kaggle", "Education", "https://www.kaggle.com/{}",
    positive=("competitions", "datasets", "notebooks"),
    strong_positive=("kaggle",))

add("Product Hunt", "Professional", "https://www.producthunt.com/@{}",
    positive=("followers", "following", "posts"),
    strong_positive=("product hunt",))
add("Wellfound", "Professional", "https://wellfound.com/u/{}",
    strong_positive=("wellfound",))
add("Crunchbase", "Professional", "https://www.crunchbase.com/person/{}",
    strong_positive=("crunchbase",))
add("Freelancer", "Professional", "https://www.freelancer.com/u/{}",
    positive=("reviews", "jobs", "portfolio"),
    strong_positive=("freelancer",))
add("Upwork", "Professional", "https://www.upwork.com/freelancers/{}",
    positive=("jobs", "reviews", "portfolio"),
    strong_positive=("upwork",))
add("Fiverr", "Professional", "https://www.fiverr.com/{}",
    positive=("gigs", "reviews"),
    strong_positive=("fiverr",))
add("Guru", "Professional", "https://www.guru.com/freelancers/{}",
    strong_positive=("guru",))
add("Contra", "Professional", "https://contra.com/{}",
    strong_positive=("contra",))
add("Polywork", "Professional", "https://www.polywork.com/{}",
    strong_positive=("polywork",))

add("Linktree", "Identity", "https://linktr.ee/{}",
    positive=("links", "followers"),
    strong_positive=("linktree",))
add("About.me", "Identity", "https://about.me/{}",
    positive=("about", "contact"),
    strong_positive=("about.me",))
add("Gravatar", "Identity", "https://en.gravatar.com/{}",
    positive=("profile", "email"),
    strong_positive=("gravatar",))
add("Carrd", "Identity", "https://{}.carrd.co",
    strong_positive=("carrd",))
add("Bio.link", "Identity", "https://bio.link/{}",
    strong_positive=("bio.link",))
add("Beacons", "Identity", "https://beacons.ai/{}",
    strong_positive=("beacons",))
add("Campsite", "Identity", "https://campsite.bio/{}",
    strong_positive=("campsite",))

add("Patreon", "Monetization", "https://www.patreon.com/{}",
    positive=("posts", "members", "followers"),
    strong_positive=("patreon",))
add("Ko-fi", "Monetization", "https://ko-fi.com/{}",
    positive=("supporters", "posts"),
    strong_positive=("ko-fi",))
add("Buy Me a Coffee", "Monetization", "https://www.buymeacoffee.com/{}",
    positive=("supporters", "posts"),
    strong_positive=("buy me a coffee",))
add("Gumroad", "Monetization", "https://gumroad.com/{}",
    strong_positive=("gumroad",))
add("Kickstarter", "Monetization", "https://www.kickstarter.com/profile/{}",
    positive=("backed", "projects"),
    strong_positive=("kickstarter",))
add("GoFundMe", "Monetization", "https://www.gofundme.com/{}",
    positive=("fundraiser", "donations"),
    strong_positive=("gofundme",))

add("Strava", "Fitness", "https://www.strava.com/athletes/{}",
    positive=("activities", "followers", "following"),
    strong_positive=("strava",))
add("Garmin Connect", "Fitness", "https://connect.garmin.com/modern/profile/{}",
    strong_positive=("garmin",))
add("MyFitnessPal", "Fitness", "https://www.myfitnesspal.com/profile/{}",
    strong_positive=("myfitnesspal",))
add("Runkeeper", "Fitness", "https://runkeeper.com/user/{}",
    strong_positive=("runkeeper",))
add("Zwift", "Fitness", "https://www.zwift.com/athlete/{}",
    strong_positive=("zwift",))

add("Couchsurfing", "Travel", "https://www.couchsurfing.com/users/{}",
    positive=("references", "friends"),
    strong_positive=("couchsurfing",))
add("Tripadvisor", "Travel", "https://www.tripadvisor.com/members/{}",
    positive=("reviews", "contributions"),
    strong_positive=("tripadvisor",))
add("Yelp", "Travel", "https://www.yelp.com/user_details?userid={}",
    positive=("reviews", "friends"),
    strong_positive=("yelp",))
add("Foursquare", "Travel", "https://foursquare.com/{}",
    strong_positive=("foursquare",))
add("Untappd", "Travel", "https://untappd.com/user/{}",
    positive=("beers", "friends"),
    strong_positive=("untappd",))
add("Vivino", "Travel", "https://www.vivino.com/users/{}",
    positive=("wines", "followers"),
    strong_positive=("vivino",))
add("AllTrails", "Travel", "https://www.alltrails.com/members/{}",
    positive=("trails", "reviews"),
    strong_positive=("alltrails",))
add("Komoot", "Travel", "https://www.komoot.com/user/{}",
    positive=("tours", "followers"),
    strong_positive=("komoot",))

add("Etsy", "Marketplace", "https://www.etsy.com/people/{}",
    positive=("favorites", "shops"),
    strong_positive=("etsy",))
add("eBay", "Marketplace", "https://www.ebay.com/usr/{}",
    positive=("feedback", "items"),
    strong_positive=("ebay",))
add("Depop", "Marketplace", "https://www.depop.com/{}",
    positive=("followers", "items"),
    strong_positive=("depop",))
add("Poshmark", "Marketplace", "https://poshmark.com/closet/{}",
    positive=("listings", "followers"),
    strong_positive=("poshmark",))
add("Vinted", "Marketplace", "https://www.vinted.com/member/{}",
    positive=("items", "followers"),
    strong_positive=("vinted",))
add("Grailed", "Marketplace", "https://www.grailed.com/{}",
    positive=("listings", "followers"),
    strong_positive=("grailed",))
add("StockX", "Marketplace", "https://stockx.com/{}",
    strong_positive=("stockx",))
add("Reverb", "Marketplace", "https://reverb.com/shop/{}",
    strong_positive=("reverb",))
add("Mercari", "Marketplace", "https://www.mercari.com/u/{}",
    strong_positive=("mercari",))

add("Letterboxd", "Media", "https://letterboxd.com/{}",
    positive=("films", "reviews", "followers"),
    strong_positive=("letterboxd",))
add("Goodreads", "Media", "https://www.goodreads.com/{}",
    positive=("books", "reviews", "followers"),
    strong_positive=("goodreads",))
add("LibraryThing", "Media", "https://www.librarything.com/profile/{}",
    strong_positive=("librarything",))
add("StoryGraph", "Media", "https://app.thestorygraph.com/profile/{}",
    strong_positive=("storygraph",))
add("MyAnimeList", "Media", "https://myanimelist.net/profile/{}",
    positive=("anime", "manga", "friends"),
    strong_positive=("myanimelist",))
add("AniList", "Media", "https://anilist.co/user/{}",
    positive=("anime", "manga", "followers"),
    strong_positive=("anilist",))
add("Kitsu", "Media", "https://kitsu.io/users/{}",
    strong_positive=("kitsu",))
add("Anime-Planet", "Media", "https://www.anime-planet.com/users/{}",
    strong_positive=("anime-planet",))
add("MangaDex", "Media", "https://mangadex.org/user/{}",
    strong_positive=("mangadex",))
add("Crunchyroll", "Media", "https://www.crunchyroll.com/user/{}",
    strong_positive=("crunchyroll",))
add("TV Time", "Media", "https://www.tvtime.com/en/user/{}/profile",
    strong_positive=("tv time",))
add("IMDb", "Media", "https://www.imdb.com/user/{}",
    positive=("ratings", "reviews", "watchlist"),
    strong_positive=("imdb",))
add("Simkl", "Media", "https://simkl.com/{}",
    strong_positive=("simkl",))
add("Trakt", "Media", "https://trakt.tv/users/{}",
    positive=("watched", "ratings"),
    strong_positive=("trakt",))

add("OpenSea", "Web3", "https://opensea.io/{}",
    positive=("items", "followers"),
    strong_positive=("opensea",))
add("Rarible", "Web3", "https://rarible.com/user/{}",
    strong_positive=("rarible",))
add("Foundation", "Web3", "https://foundation.app/@{}",
    strong_positive=("foundation",))
add("SuperRare", "Web3", "https://superrare.com/{}",
    strong_positive=("superrare",))
add("Zora", "Web3", "https://zora.co/{}",
    strong_positive=("zora",))
add("Gitcoin", "Web3", "https://gitcoin.co/{}",
    positive=("grants", "contributions"),
    strong_positive=("gitcoin",))

add("Wikipedia", "Wiki", "https://en.wikipedia.org/wiki/User:{}",
    positive=("user page", "edits", "contributions"),
    strong_positive=("wikipedia",))
add("Wikimedia Commons", "Wiki", "https://commons.wikimedia.org/wiki/User:{}",
    positive=("contributions", "files"),
    strong_positive=("wikimedia commons",))
add("ArchWiki", "Wiki", "https://wiki.archlinux.org/index.php/User:{}",
    strong_positive=("arch linux",))
add("Gentoo Wiki", "Wiki", "https://wiki.gentoo.org/wiki/User:{}",
    strong_positive=("gentoo",))
add("Ubuntu Wiki", "Wiki", "https://wiki.ubuntu.com/{}",
    strong_positive=("ubuntu wiki",))
add("Fedora Wiki", "Wiki", "https://fedoraproject.org/wiki/User:{}",
    strong_positive=("fedora",))
add("Debian Wiki", "Wiki", "https://wiki.debian.org/{}",
    strong_positive=("debian",))
add("OpenSUSE Wiki", "Wiki", "https://en.opensuse.org/User:{}",
    strong_positive=("opensuse",))

PLATFORM_MAP = {p.name.lower(): p for p in PLATFORMS}
HOST_LOCKS = {}
HOST_LOCKS_GUARD = threading.Lock()

class Scanner:
    def __init__(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, workers=DEFAULT_WORKERS, delay=0.0, verbose=False, quiet=False):
        self.timeout = timeout
        self.retries = retries
        self.workers = workers
        self.delay = delay
        self.verbose = verbose
        self.quiet = quiet
        self.counter = 0
        self.total = 0
        self.counter_lock = threading.Lock()

    def host_lock(self, host):
        with HOST_LOCKS_GUARD:
            if host not in HOST_LOCKS:
                HOST_LOCKS[host] = threading.Lock()
            return HOST_LOCKS[host]

    def fetch(self, url):
        parsed = urllib.parse.urlparse(url)
        lock = self.host_lock(parsed.netloc)

        last_error = ""
        for attempt in range(self.retries + 1):
            try:
                if self.delay:
                    time.sleep(self.delay)

                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.8",
                        "Connection": "close"
                    }
                )

                started = time.perf_counter()

                with lock:
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        status = response.status
                        final_url = response.geturl()
                        headers = dict(response.headers)
                        body = response.read(MAX_BODY)

                elapsed = int((time.perf_counter() - started) * 1000)
                return {
                    "status": status,
                    "final_url": final_url,
                    "headers": headers,
                    "body": body,
                    "elapsed": elapsed,
                    "error": ""
                }

            except urllib.error.HTTPError as e:
                elapsed = int((time.perf_counter() - started) * 1000) if "started" in locals() else 0
                try:
                    body = e.read(MAX_BODY)
                except Exception:
                    body = b""

                if e.code in (429, 500, 502, 503, 504):
                    if attempt < self.retries:
                        time.sleep((2 ** attempt) + random.uniform(0.1, 0.5))
                        continue

                return {
                    "status": e.code,
                    "final_url": getattr(e, "url", url),
                    "headers": dict(getattr(e, "headers", {}) or {}),
                    "body": body,
                    "elapsed": elapsed,
                    "error": str(e)
                }

            except Exception as e:
                last_error = str(e)
                if attempt < self.retries:
                    time.sleep((2 ** attempt) + random.uniform(0.1, 0.5))
                    continue

        return {
            "status": 0,
            "final_url": url,
            "headers": {},
            "body": b"",
            "elapsed": 0,
            "error": last_error
        }

    def fingerprint(self, body):
        normalized = re.sub(rb"\s+", b" ", body[:MAX_BODY]).strip()
        return hashlib.sha256(normalized[:65536]).hexdigest()[:16]

    def analyze(self, platform, username, url, response):
        status = response["status"]
        body_bytes = response["body"]
        final_url = response["final_url"]
        elapsed = response["elapsed"]
        error = response["error"]

        try:
            text = body_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

        lowered = text.lower()
        parser = TitleParser()

        try:
            parser.feed(text[:MAX_BODY])
            title, meta = parser.result()
        except Exception:
            title = ""
            meta = {}

        title_lower = title.lower()
        url_lower = final_url.lower()
        username_lower = username.lower()

        score = 0
        evidence = []

        if status == 429:
            return CheckResult(
                username, platform.name, platform.category, url,
                "RATE_LIMITED", 0, 0, status,
                "HTTP 429 rate limit", elapsed, final_url, title,
                self.fingerprint(body_bytes), ["HTTP 429"], error
            )

        if status in (502, 503, 504):
            return CheckResult(
                username, platform.name, platform.category, url,
                "RATE_LIMITED", 0, 0, status,
                f"HTTP {status}", elapsed, final_url, title,
                self.fingerprint(body_bytes), [f"HTTP {status}"], error
            )

        if status == 0:
            return CheckResult(
                username, platform.name, platform.category, url,
                "ERROR", 0, 0, 0,
                error or "connection error", elapsed, final_url, title,
                self.fingerprint(body_bytes), [], error
            )

        if status in (401, 403):
            return CheckResult(
                username, platform.name, platform.category, url,
                "UNKNOWN", 20, 0, status,
                f"HTTP {status} access restricted", elapsed, final_url, title,
                self.fingerprint(body_bytes), [f"HTTP {status}"], error
            )

        for marker in platform.strong_negative:
            if marker in lowered or marker in title_lower:
                score -= 45
                evidence.append(f"strong-negative:{marker}")

        for marker in platform.negative_markers:
            if marker in lowered or marker in title_lower:
                score -= 15
                evidence.append(f"negative:{marker}")

        for marker in platform.positive_markers:
            if marker in lowered or marker in title_lower:
                score += 8
                evidence.append(f"positive:{marker}")

        for marker in platform.strong_positive:
            if marker in lowered or marker in title_lower:
                score += 25
                evidence.append(f"strong-positive:{marker}")

        if username_lower in lowered:
            score += 18
            evidence.append("username-in-response")

        if username_lower in title_lower:
            score += 20
            evidence.append("username-in-title")

        if username_lower in url_lower:
            score += 8
            evidence.append("username-in-final-url")

        if status in range(200, 300):
            score += 15
            evidence.append(f"http-{status}")

        elif status in (301, 302, 303, 307, 308):
            score += 7
            evidence.append(f"redirect-{status}")

        if title:
            score += 3
            evidence.append("html-title")

        if meta.get("description"):
            score += 3
            evidence.append("meta-description")

        if len(text) < 100:
            score -= 5
            evidence.append("very-small-response")

        if len(evidence) >= 8:
            score += 5

        score = max(-100, min(100, score))

        if score >= 65:
            state = "FOUND"
            confidence = min(99, 80 + score // 5)
            reason = "strong profile evidence"

        elif score >= 42:
            state = "FOUND"
            confidence = min(90, 60 + score // 4)
            reason = "multiple positive indicators"

        elif score <= -35:
            state = "NOT_FOUND"
            confidence = min(99, 75 + abs(score) // 5)
            reason = "negative profile indicators"

        elif status in range(200, 400):
            state = "UNCERTAIN"
            confidence = max(20, min(65, 45 + score // 4))
            reason = "page reachable but identity evidence is weak"

        else:
            state = "UNKNOWN"
            confidence = 20
            reason = f"HTTP {status}"

        return CheckResult(
            username=username,
            platform=platform.name,
            category=platform.category,
            url=url,
            status=state,
            confidence=confidence,
            score=score,
            http_status=status,
            reason=reason,
            elapsed_ms=elapsed,
            final_url=final_url,
            title=title[:200],
            fingerprint=self.fingerprint(body_bytes),
            evidence=evidence,
            error=error
        )

    def check(self, platform, username):
        encoded = urllib.parse.quote(username, safe="")
        url = platform.url.format(encoded)
        response = self.fetch(url)
        return self.analyze(platform, username, url, response)

    def scan(self, username, platforms):
        self.total = len(platforms)
        self.counter = 0
        results = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self.check, platform, username): platform
                for platform in platforms
            }

            for future in as_completed(futures):
                platform = futures[future]

                try:
                    result = future.result()
                except Exception as e:
                    result = CheckResult(
                        username=username,
                        platform=platform.name,
                        category=platform.category,
                        url=platform.url.format(urllib.parse.quote(username, safe="")),
                        status="ERROR",
                        confidence=0,
                        score=0,
                        http_status=0,
                        reason="scanner exception",
                        elapsed_ms=0,
                        final_url="",
                        title="",
                        fingerprint="",
                        evidence=[],
                        error=str(e)
                    )

                results.append(result)

                with self.counter_lock:
                    self.counter += 1
                    current = self.counter

                if not self.quiet:
                    print_progress(current, self.total)

        print()
        return sorted(results, key=lambda x: (-x.confidence, x.platform.lower()))

def print_progress(current, total):
    width = 28
    ratio = current / total if total else 1
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    percent = int(ratio * 100)
    sys.stdout.write(
        f"\r{C}⠿{RESET} {DG}[{bar}] {percent:3d}% {current}/{total}{RESET}"
    )
    sys.stdout.flush()

def status_color(status):
    return {
        "FOUND": G,
        "NOT_FOUND": R,
        "UNCERTAIN": Y,
        "RATE_LIMITED": M,
        "UNKNOWN": B,
        "ERROR": R
    }.get(status, W)

def status_symbol(status):
    return {
        "FOUND": "✓",
        "NOT_FOUND": "✗",
        "UNCERTAIN": "~",
        "RATE_LIMITED": "!",
        "UNKNOWN": "?",
        "ERROR": "×"
    }.get(status, "?")

def print_result(result):
    color = status_color(result.status)
    symbol = status_symbol(result.status)

    confidence = f"{result.confidence:02d}%"
    latency = f"{result.elapsed_ms}ms" if result.elapsed_ms else "---"

    print(
        f"  {color}[{symbol}]{RESET} "
        f"{W}{result.platform:<24}{RESET} "
        f"{color}{result.status:<13}{RESET} "
        f"{DG}{confidence:<4} {latency:<8}{RESET}"
    )

def print_scan_header(username, platforms, mode, workers):
    print()
    print(f"{C}┌─ {W}[{mode}]{C} ───────────────────────────────────────────────")
    print(f"{C}│  {Y}Target     : {W}{username}")
    print(f"{C}│  {Y}Platforms  : {W}{len(platforms)}")
    print(f"{C}│  {Y}Workers    : {W}{workers}")
    print(f"{C}│  {Y}Engine     : {W}Confidence + Fingerprint")
    print(f"{C}└────────────────────────────────────────────────────────────{RESET}")
    print()

def print_summary(results, started, username):
    elapsed = time.perf_counter() - started
    counts = defaultdict(int)

    for result in results:
        counts[result.status] += 1

    print()
    print(f"{C}╔══════════════════════════════════════════════════════════════╗")
    print(f"║{W}                         SCAN SUMMARY                       {C}║")
    print(f"╠══════════════════════════════════════════════════════════════╣")
    print(f"║  {Y}Target       {W}{username:<43}{C}║")
    print(f"║  {Y}Scanned      {W}{len(results):<43}{C}║")
    print(f"║  {Y}Found        {G}{counts['FOUND']:<43}{C}║")
    print(f"║  {Y}Uncertain    {Y}{counts['UNCERTAIN']:<43}{C}║")
    print(f"║  {Y}Not Found    {R}{counts['NOT_FOUND']:<43}{C}║")
    print(f"║  {Y}Rate Limited {M}{counts['RATE_LIMITED']:<43}{C}║")
    print(f"║  {Y}Unknown      {B}{counts['UNKNOWN']:<43}{C}║")
    print(f"║  {Y}Errors       {R}{counts['ERROR']:<43}{C}║")
    print(f"║  {Y}Duration     {W}{elapsed:.2f}s{'':<38}{C}║")
    print(f"╚══════════════════════════════════════════════════════════════╝{RESET}")

def print_found_details(results):
    found = [r for r in results if r.status == "FOUND"]

    if not found:
        return

    print()
    print(f"{G}┌─ FOUND PROFILES ────────────────────────────────────────────{RESET}")

    for result in found:
        print(
            f"{G}│{RESET} {W}{result.platform:<24}{RESET} "
            f"{G}{result.confidence}%{RESET} "
            f"{DG}{result.final_url}{RESET}"
        )

        if result.evidence:
            evidence = ", ".join(result.evidence[:6])
            print(f"{DG}│   evidence: {evidence}{RESET}")

    print(f"{G}└────────────────────────────────────────────────────────────{RESET}")

def generate_variations(username):
    u = username.lower().strip()
    variations = {u}

    separators = ["_", ".", "-", ""]
    prefixes = [
        "the", "real", "official", "its", "im", "iam",
        "i_am", "mr", "dr", "x", "xx"
    ]
    suffixes = [
        "official", "real", "irl", "hq", "tv", "yt",
        "pro", "og", "dev", "sec", "x", "xx"
    ]
    numbers = [
        "0", "1", "2", "3", "7", "9", "01", "007",
        "10", "11", "12", "13", "21", "42", "69",
        "99", "404", "420", "666", "777", "1337",
        "2000", "2001", "2002", "2003", "2004",
        "2005", "2006", "2007", "2008", "2009",
        "2010", "2020", "2021", "2022", "2023",
        "2024", "2025", "2026"
    ]

    for sep in separators:
        variations.add(f"{u}{sep}")

    for n in numbers:
        variations.add(f"{u}{n}")
        variations.add(f"{n}{u}")

    for prefix in prefixes:
        variations.add(f"{prefix}{u}")
        variations.add(f"{prefix}_{u}")
        variations.add(f"{prefix}.{u}")

    for suffix in suffixes:
        variations.add(f"{u}{suffix}")
        variations.add(f"{u}_{suffix}")
        variations.add(f"{u}.{suffix}")

    if len(u) > 2:
        variations.add(u + u[-1])
        variations.add(u[:-1])
        variations.add(u[::-1])

    tr_map = {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c"
    }

    ascii_u = u
    for old, new in tr_map.items():
        ascii_u = ascii_u.replace(old, new)

    if ascii_u != u:
        variations.add(ascii_u)
        variations.add(f"{ascii_u}_")
        variations.add(f"{ascii_u}1")

    leet = {
        "a": "4",
        "e": "3",
        "i": "1",
        "o": "0",
        "s": "5",
        "t": "7"
    }

    leet_u = u
    for old, new in leet.items():
        leet_u = leet_u.replace(old, new)

    if leet_u != u:
        variations.add(leet_u)

    return sorted(v for v in variations if v)

def validate_username(username):
    if not username:
        return False, "username boş olamaz"

    if len(username) > 64:
        return False, "username 64 karakterden uzun"

    if username.startswith(("http://", "https://")):
        return False, "username yerine URL verildi"

    if any(ord(ch) < 32 for ch in username):
        return False, "geçersiz kontrol karakteri"

    return True, ""

def resolve_platforms(names=None, categories=None, excludes=None):
    selected = list(PLATFORMS)

    if names:
        lowered = [x.lower() for x in names]
        selected = [
            p for p in selected
            if any(x in p.name.lower() for x in lowered)
        ]

    if categories:
        lowered = [x.lower() for x in categories]
        selected = [
            p for p in selected
            if p.category.lower() in lowered
        ]

    if excludes:
        lowered = [x.lower() for x in excludes]
        selected = [
            p for p in selected
            if not any(x in p.name.lower() for x in lowered)
        ]

    unique = {}
    for platform in selected:
        unique[platform.name] = platform

    return list(unique.values())

def save_json(results, path, username):
    data = {
        "tool": "SHENWIN",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "username": username,
        "total": len(results),
        "results": [asdict(r) for r in results]
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(results, path):
    fields = [
        "username",
        "platform",
        "category",
        "url",
        "status",
        "confidence",
        "score",
        "http_status",
        "reason",
        "elapsed_ms",
        "final_url",
        "title",
        "fingerprint",
        "evidence",
        "error"
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for result in results:
            row = asdict(result)
            row["evidence"] = " | ".join(result.evidence)
            writer.writerow(row)

def save_txt(results, path, username):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"SHENWIN {VERSION}\n")
        f.write(f"Username: {username}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 90 + "\n\n")

        for result in results:
            f.write(
                f"[{result.status}] "
                f"{result.platform} | "
                f"{result.confidence}% | "
                f"{result.final_url or result.url}\n"
            )

            if result.reason:
                f.write(f"Reason: {result.reason}\n")

            if result.evidence:
                f.write(f"Evidence: {', '.join(result.evidence)}\n")

            f.write("\n")

def save_html(results, path, username):
    rows = []

    for result in results:
        color_class = result.status.lower().replace("_", "-")

        rows.append(
            "<tr>"
            f"<td>{html.escape(result.platform)}</td>"
            f"<td>{html.escape(result.category)}</td>"
            f"<td class='{color_class}'>{html.escape(result.status)}</td>"
            f"<td>{result.confidence}%</td>"
            f"<td>{result.http_status}</td>"
            f"<td>{result.elapsed_ms}ms</td>"
            f"<td><a href='{html.escape(result.final_url or result.url)}' target='_blank'>open</a></td>"
            f"<td>{html.escape(result.reason)}</td>"
            "</tr>"
        )

    document = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>SHENWIN - {html.escape(username)}</title>
<style>
body{{background:#0b0f14;color:#d7dde5;font-family:Arial,sans-serif;margin:40px}}
h1{{color:#55ffff}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:10px;border-bottom:1px solid #26313d;text-align:left}}
th{{color:#55ffff}}
.found{{color:#55ff88}}
.not-found{{color:#ff5555}}
.uncertain{{color:#ffff55}}
.rate-limited{{color:#ff55ff}}
.unknown{{color:#5599ff}}
.error{{color:#ff5555}}
a{{color:#55ffff}}
</style>
</head>
<body>
<h1>SHENWIN {VERSION}</h1>
<p>Username: <b>{html.escape(username)}</b></p>
<table>
<thead>
<tr>
<th>Platform</th>
<th>Category</th>
<th>Status</th>
<th>Confidence</th>
<th>HTTP</th>
<th>Latency</th>
<th>URL</th>
<th>Reason</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(document)

def save_results(results, username, output, fmt):
    if not output:
        return

    if fmt == "json":
        save_json(results, output, username)
    elif fmt == "csv":
        save_csv(results, output)
    elif fmt == "html":
        save_html(results, output, username)
    else:
        save_txt(results, output, username)

    print(f"\n{G}[✓] Saved: {W}{output}{RESET}")

def save_baseline(results, path, username):
    data = {
        "tool": "SHENWIN",
        "version": VERSION,
        "username": username,
        "generated_at": datetime.now().isoformat(),
        "profiles": {
            r.platform: {
                "status": r.status,
                "confidence": r.confidence,
                "fingerprint": r.fingerprint,
                "url": r.final_url or r.url
            }
            for r in results
        }
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def compare_baseline(results, path):
    with open(path, "r", encoding="utf-8") as f:
        old = json.load(f)

    old_profiles = old.get("profiles", {})
    changes = []

    for result in results:
        previous = old_profiles.get(result.platform)

        if not previous:
            changes.append(
                f"{result.platform}: NEW -> {result.status}"
            )
            continue

        if previous.get("status") != result.status:
            changes.append(
                f"{result.platform}: "
                f"{previous.get('status')} -> {result.status}"
            )

        elif previous.get("fingerprint") != result.fingerprint:
            changes.append(
                f"{result.platform}: CONTENT_CHANGED"
            )

    if not changes:
        print(f"\n{G}[✓] Baseline karşılaştırmasında değişiklik yok.{RESET}")
        return

    print()
    print(f"{Y}┌─ BASELINE CHANGES ─────────────────────────────────────────{RESET}")

    for change in changes:
        print(f"{Y}│{RESET} {change}")

    print(f"{Y}└────────────────────────────────────────────────────────────{RESET}")

def print_platforms():
    categories = defaultdict(list)

    for platform in PLATFORMS:
        categories[platform.category].append(platform.name)

    print()
    print(f"{C}╔══════════════════════════════════════════════════════════════╗")
    print(f"║{W}                     PLATFORM DATABASE                     {C}║")
    print(f"╠══════════════════════════════════════════════════════════════╣")

    for category in sorted(categories):
        print(f"║ {Y}{category:<18}{W} {len(categories[category]):>4} platforms{C}{' ' * 26}║")

    print(f"╠══════════════════════════════════════════════════════════════╣")
    print(f"║ {G}TOTAL{W} {len(PLATFORMS):<51}{C}║")
    print(f"╚══════════════════════════════════════════════════════════════╝{RESET}")

    for category in sorted(categories):
        print()
        print(f"{M}[{category}]{RESET}")

        for name in sorted(categories[category]):
            print(f"  {C}▸{RESET} {name}")

def print_stats():
    categories = defaultdict(int)

    for platform in PLATFORMS:
        categories[platform.category] += 1

    print()
    print(f"{C}SHENWIN {VERSION}{RESET}")
    print(f"{DG}Platform database statistics{RESET}\n")
    print(f"{W}Total platforms : {G}{len(PLATFORMS)}{RESET}")
    print(f"{W}Categories      : {G}{len(categories)}{RESET}")
    print()

    for category, count in sorted(categories.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {C}{category:<18}{RESET} {W}{count:>3}{RESET}")

def run_scan(username, mode, platforms, args):
    scanner = Scanner(
        timeout=args.timeout,
        retries=args.retries,
        workers=args.workers,
        delay=args.delay,
        verbose=args.verbose,
        quiet=args.quiet
    )

    print_scan_header(username, platforms, mode, args.workers)

    started = time.perf_counter()
    results = scanner.scan(username, platforms)

    if args.quiet:
        print()

    for result in results:
        if args.quiet:
            continue

        if result.status == "FOUND":
            print_result(result)
        elif args.verbose:
            print_result(result)

    print_summary(results, started, username)
    print_found_details(results)

    save_results(results, username, args.output, args.format)

    if args.save_baseline:
        save_baseline(results, args.save_baseline, username)
        print(f"{G}[✓] Baseline saved: {W}{args.save_baseline}{RESET}")

    if args.compare:
        compare_baseline(results, args.compare)

    return results

def mode_vargen(username):
    variations = generate_variations(username)

    print()
    print(f"{Y}┌─ {W}[VARGEN MODE]{Y} ─────────────────────────────────────────────")
    print(f"{Y}│  {W}{username} {DG}için {len(variations)} varyasyon")
    print(f"{Y}└────────────────────────────────────────────────────────────{RESET}")
    print()

    for i, variation in enumerate(variations, 1):
        print(f"  {C}{i:03d}{RESET} {W}{variation}{RESET}")

def mode_single(username, site, args):
    platforms = resolve_platforms(names=[site])

    if not platforms:
        print(f"{R}[!] Platform bulunamadı: {site}{RESET}")
        return

    run_scan(username, "SINGLE MODE", platforms, args)

def mode_wildcard(username, args):
    variations = generate_variations(username)

    print()
    print(f"{M}┌─ {W}[WILDCARD MODE]{M} ──────────────────────────────────────────")
    print(f"{M}│  {Y}Source       : {W}{username}")
    print(f"{M}│  {Y}Variations   : {W}{len(variations)}")
    print(f"{M}│  {Y}Platforms    : {W}{len(resolve_platforms(names=args.platform))}")
    print(f"{M}│  {Y}Total checks : {W}{len(variations) * len(resolve_platforms(names=args.platform))}")
    print(f"{M}└────────────────────────────────────────────────────────────{RESET}")
    print()

    preview = variations[:30]

    for variation in preview:
        print(f"  {C}▸{RESET} {variation}")

    if len(variations) > len(preview):
        print(f"  {DG}... {len(variations) - len(preview)} more{RESET}")

    print()

    if not args.yes:
        confirm = input(f"{Y}Tüm varyasyonları tara? [y/N]: {RESET}").strip().lower()
        if confirm != "y":
            print(f"{DG}İptal.{RESET}")
            return

    all_results = []

    for index, variation in enumerate(variations, 1):
        print(f"\n{M}[{index}/{len(variations)}] {W}{variation}{RESET}")

        platforms = resolve_platforms(
            names=args.platform,
            categories=args.category,
            excludes=args.exclude
        )

        results = run_scan(
            variation,
            "WILDCARD SCAN",
            platforms,
            args
        )

        all_results.extend(results)

    found = [r for r in all_results if r.status == "FOUND"]

    print()
    print(f"{M}╔══════════════════════════════════════════════════════════════╗")
    print(f"║ {W}Wildcard completed{M}                                      ║")
    print(f"║ {Y}Variations : {W}{len(variations):<45}{M}║")
    print(f"║ {Y}Found      : {G}{len(found):<45}{M}║")
    print(f"╚══════════════════════════════════════════════════════════════╝{RESET}")

def print_help():
    print(rabbit())
    print(f"{W}KULLANIM{RESET}")
    print()
    print(f"  {C}python3 shenwin.py -w {Y}<username>{RESET}")
    print(f"  {C}python3 shenwin.py -ww {Y}<username>{RESET}")
    print(f"  {C}python3 shenwin.py -r {Y}<username>{RESET}")
    print(f"  {C}python3 shenwin.py -v {Y}<username>{RESET}")
    print(f"  {C}python3 shenwin.py -s {Y}<username> <site>{RESET}")
    print()
    print(f"{W}TARAMA{RESET}")
    print()
    print(f"  {C}-w, --whoami       {DG}Tüm platformlarda username taraması{RESET}")
    print(f"  {C}-ww, --wildcard    {DG}Username varyasyonlarıyla tarama{RESET}")
    print(f"  {C}-r, --recon        {DG}Development + cybersecurity odaklı tarama{RESET}")
    print(f"  {C}-v, --vargen       {DG}Varyasyonları üret ve göster{RESET}")
    print(f"  {C}-s, --single       {DG}Tek platform taraması{RESET}")
    print()
    print(f"{W}FİLTRELER{RESET}")
    print()
    print(f"  {C}-p, --platform     {DG}Platform filtresi, tekrar edilebilir{RESET}")
    print(f"  {C}-c, --category     {DG}Kategori filtresi, tekrar edilebilir{RESET}")
    print(f"  {C}-x, --exclude      {DG}Platform hariç tut{RESET}")
    print()
    print(f"{W}PERFORMANS{RESET}")
    print()
    print(f"  {C}-wkr, --workers N  {DG}Worker sayısı{RESET}")
    print(f"  {C}--timeout N        {DG}HTTP timeout{RESET}")
    print(f"  {C}--retries N        {DG}Retry sayısı{RESET}")
    print(f"  {C}--delay N          {DG}İstekler arası gecikme{RESET}")
    print()
    print(f"{W}ÇIKTI{RESET}")
    print()
    print(f"  {C}-o, --output FILE  {DG}Çıktı dosyası{RESET}")
    print(f"  {C}--format FORMAT    {DG}txt/json/csv/html{RESET}")
    print(f"  {C}--save-baseline F  {DG}Baseline kaydet{RESET}")
    print(f"  {C}--compare F        {DG}Baseline karşılaştır{RESET}")
    print()
    print(f"{W}DİĞER{RESET}")
    print()
    print(f"  {C}--list-platforms   {DG}Platform database'i göster{RESET}")
    print(f"  {C}--stats            {DG}Database istatistikleri{RESET}")
    print(f"  {C}--verbose          {DG}Tüm sonuçları göster{RESET}")
    print(f"  {C}--quiet            {DG}Minimum terminal çıktısı{RESET}")
    print(f"  {C}--yes              {DG}Wildcard onayını otomatik geç{RESET}")
    print(f"  {C}--no-color         {DG}Renkleri kapat{RESET}")
    print()
    print(f"{W}ÖRNEKLER{RESET}")
    print()
    print(f"  {DG}$ python3 shenwin.py -w LatenT{RESET}")
    print(f"  {DG}$ python3 shenwin.py -w LatenT -p GitHub -p Reddit{RESET}")
    print(f"  {DG}$ python3 shenwin.py -r LatenT{RESET}")
    print(f"  {DG}$ python3 shenwin.py -ww LatenT --yes{RESET}")
    print(f"  {DG}$ python3 shenwin.py -s LatenT github{RESET}")
    print(f"  {DG}$ python3 shenwin.py -w LatenT -c Development{RESET}")
    print(f"  {DG}$ python3 shenwin.py --list-platforms{RESET}")
    print(f"  {DG}$ python3 shenwin.py --stats{RESET}")
    print()

def main():
    global R, G, Y, B, C, M, W, DG, RESET, BOLD

    parser = argparse.ArgumentParser(
        description="SHENWIN OSINT Username Intelligence Engine"
    )

    parser.add_argument("-w", "--whoami")
    parser.add_argument("-ww", "--wildcard")
    parser.add_argument("-r", "--recon")
    parser.add_argument("-v", "--vargen")
    parser.add_argument("-s", "--single", nargs=2, metavar=("USER", "SITE"))

    parser.add_argument("-p", "--platform", action="append", default=[])
    parser.add_argument("-c", "--category", action="append", default=[])
    parser.add_argument("-x", "--exclude", action="append", default=[])

    parser.add_argument("-wkr", "--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--delay", type=float, default=0.0)

    parser.add_argument("-o", "--output", default="")
    parser.add_argument("--format", choices=["txt", "json", "csv", "html"], default="txt")
    parser.add_argument("--save-baseline", default="")
    parser.add_argument("--compare", default="")

    parser.add_argument("--list-platforms", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-color", action="store_true")

    args = parser.parse_args()

    if args.no_color:
        R = G = Y = B = C = M = W = DG = RESET = BOLD = ""

    if args.workers < 1:
        print(f"{R}[!] workers 1 veya daha büyük olmalı.{RESET}")
        return 2

    if args.timeout < 1:
        print(f"{R}[!] timeout 1 veya daha büyük olmalı.{RESET}")
        return 2

    if args.retries < 0:
        print(f"{R}[!] retries negatif olamaz.{RESET}")
        return 2

    if args.delay < 0:
        print(f"{R}[!] delay negatif olamaz.{RESET}")
        return 2

    if len(sys.argv) == 1:
        print(banner())
        print_help()
        return 0

    if args.list_platforms:
        print(banner())
        print_platforms()
        return 0

    if args.stats:
        print(banner())
        print_stats()
        return 0

    username = None
    mode = None

    if args.whoami:
        username = args.whoami
        mode = "WHOAMI MODE"

    elif args.wildcard:
        username = args.wildcard
        mode = "WILDCARD MODE"

    elif args.recon:
        username = args.recon
        mode = "RECON MODE"

    elif args.vargen:
        username = args.vargen
        mode = "VARGEN MODE"

    elif args.single:
        username = args.single[0]
        mode = "SINGLE MODE"

    if not username:
        print(banner())
        print(f"{R}[!] Bir tarama modu seçmelisin.{RESET}\n")
        print_help()
        return 2

    valid, reason = validate_username(username)

    if not valid:
        print(f"{R}[!] Geçersiz username: {reason}{RESET}")
        return 2

    print(banner())

    try:
        if mode == "VARGEN MODE":
            mode_vargen(username)
            return 0

        if mode == "SINGLE MODE":
            mode_single(username, args.single[1], args)
            return 0

        if mode == "WILDCARD MODE":
            mode_wildcard(username, args)
            return 0

        if mode == "RECON MODE":
            recon_categories = ["Development", "Cybersecurity", "Education"]
            platforms = resolve_platforms(
                names=args.platform,
                categories=args.category or recon_categories,
                excludes=args.exclude
            )
            results = run_scan(username, mode, platforms, args)
            return 0 if any(r.status == "FOUND" for r in results) else 1

        platforms = resolve_platforms(
            names=args.platform,
            categories=args.category,
            excludes=args.exclude
        )

        if not platforms:
            print(f"{R}[!] Filtrelerle eşleşen platform bulunamadı.{RESET}")
            return 2

        results = run_scan(username, mode, platforms, args)

        return 0 if any(r.status == "FOUND" for r in results) else 1

    except KeyboardInterrupt:
        print(f"\n\n{R}[!] İşlem kullanıcı tarafından durduruldu.{RESET}")
        return 130

    except FileNotFoundError as e:
        print(f"\n{R}[!] Dosya bulunamadı: {e}{RESET}")
        return 2

    except json.JSONDecodeError:
        print(f"\n{R}[!] JSON dosyası okunamadı.{RESET}")
        return 2

    except Exception as e:
        print(f"\n{R}[!] Beklenmedik hata: {e}{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
