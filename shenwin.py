#!/usr/bin/env python3
"""
SHENWIN - OSINT Username Hunter
Kullanım: python3 shenwin.py -w <username>
"""

import sys
import time
import argparse
import threading
import urllib.request
import urllib.error
from datetime import datetime

R  = "\033[0;31m"
G  = "\033[0;32m"
Y  = "\033[1;33m"
B  = "\033[0;34m"
C  = "\033[0;36m"
M  = "\033[0;35m"
W  = "\033[1;37m"
DG = "\033[2;37m"
RESET = "\033[0m"
BOLD  = "\033[1m"

RABBIT = f"""{W}
    {C}(\\ /)
    {C}( . .)  {W}S H E N W I N
    {C}c{W}("{C}){W}("{C})   {DG}OSINT Username Hunter{W}
    {C} |   |
    {C}_|___|_{RESET}
"""

BANNER = f"""
{C}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  {W} ███████╗██╗  ██╗███████╗███╗   ██╗██╗    ██╗██╗███╗   ██╗ {C}║
║  {W} ██╔════╝██║  ██║██╔════╝████╗  ██║██║    ██║██║████╗  ██║ {C}║
║  {W} ███████╗███████║█████╗  ██╔██╗ ██║██║ █╗ ██║██║██╔██╗ ██║ {C}║
║  {W} ╚════██║██╔══██║██╔══╝  ██║╚██╗██║██║███╗██║██║██║╚██╗██║ {C}║
║  {W} ███████║██║  ██║███████╗██║ ╚████║╚███╔███╔╝██║██║ ╚████║ {C}║
║  {W} ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝ {C}║
║                                                              ║
║  {DG} v0.01  |  OSINT Username & Variation Hunter  |  by LatenT  {C}║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""

# ─── PLATFORM DATABASE ──────────────────────────────────────────────────
PLATFORMS = {

    # ══ SOCIAL MEDIA ═══════════════════════════════════════════════════════════
    "Twitter/X":           "https://twitter.com/{}",
    "Instagram":           "https://www.instagram.com/{}/",
    "TikTok":              "https://www.tiktok.com/@{}",
    "YouTube":             "https://www.youtube.com/@{}",
    "Facebook":            "https://www.facebook.com/{}",
    "Pinterest":           "https://www.pinterest.com/{}/",
    "Snapchat":            "https://www.snapchat.com/add/{}",
    "Tumblr":              "https://{}.tumblr.com",
    "Reddit":              "https://www.reddit.com/user/{}",
    "Mastodon":            "https://mastodon.social/@{}",
    "Twitch":              "https://www.twitch.tv/{}",
    "Kick":                "https://kick.com/{}",
    "LinkedIn":            "https://www.linkedin.com/in/{}",
    "Quora":               "https://www.quora.com/profile/{}",
    "VK":                  "https://vk.com/{}",
    "OK.ru":               "https://ok.ru/{}",
    "Weibo":               "https://weibo.com/{}",
    "Minds":               "https://www.minds.com/{}",
    "Gab":                 "https://gab.com/{}",
    "Clubhouse":           "https://www.joinclubhouse.com/@{}",
    "Livejournal":         "https://{}.livejournal.com",
    "Ello":                "https://ello.co/{}",
    "Plurk":               "https://www.plurk.com/{}",
    "Blogger":             "https://{}.blogspot.com",
    "Wordpress":           "https://{}.wordpress.com",
    "Substack":            "https://{}.substack.com",
    "Hashnode":            "https://hashnode.com/@{}",
    "Bluesky":             "https://bsky.app/profile/{}.bsky.social",
    "Threads":             "https://www.threads.net/@{}",
    "BeReal":              "https://bere.al/{}",
    "Cara":                "https://cara.app/{}",
    "Cohost":              "https://cohost.org/{}",
    "Micro.blog":          "https://micro.blog/{}",
    "Mewe":                "https://mewe.com/i/{}",
    "Diaspora":            "https://diaspora.social/u/{}",
    "Fosstodon":           "https://fosstodon.org/@{}",
    "Lemmy":               "https://lemmy.ml/u/{}",
    "Kbin":                "https://kbin.social/u/{}",
    "Beehaw":              "https://beehaw.org/u/{}",
    "Tildes":              "https://tildes.net/user/{}",
    "Koo":                 "https://www.kooapp.com/profile/{}",
    "Parler":              "https://parler.com/{}",
    "Amino":               "https://aminoapps.com/u/{}",

    # ══ DEVELOPER / TECH ═══════════════════════════════════════════════════════
    "GitHub":              "https://github.com/{}",
    "GitLab":              "https://gitlab.com/{}",
    "Bitbucket":           "https://bitbucket.org/{}",
    "Codeberg":            "https://codeberg.org/{}",
    "Gitea":               "https://gitea.com/{}",
    "Sourcehut":           "https://sr.ht/~{}",
    "HackerNews":          "https://news.ycombinator.com/user?id={}",
    "Dev.to":              "https://dev.to/{}",
    "Replit":              "https://replit.com/@{}",
    "Codepen":             "https://codepen.io/{}",
    "StackOverflow":       "https://stackoverflow.com/users/{}",
    "StackExchange":       "https://stackexchange.com/users/{}",
    "Keybase":             "https://keybase.io/{}",
    "DockerHub":           "https://hub.docker.com/u/{}",
    "NPM":                 "https://www.npmjs.com/~{}",
    "PyPI":                "https://pypi.org/user/{}/",
    "Crates.io":           "https://crates.io/users/{}",
    "RubyGems":            "https://rubygems.org/profiles/{}",
    "Packagist":           "https://packagist.org/users/{}",
    "Nuget":               "https://www.nuget.org/profiles/{}",
    "Launchpad":           "https://launchpad.net/~{}",
    "Sourceforge":         "https://sourceforge.net/u/{}/profile",
    "Lobsters":            "https://lobste.rs/u/{}",
    "Hackaday":            "https://hackaday.io/{}",
    "Hackster":            "https://www.hackster.io/{}",
    "Instructables":       "https://www.instructables.com/member/{}",
    "DevRant":             "https://devrant.com/users/{}",
    "Daily.dev":           "https://app.daily.dev/{}",
    "Showwcase":           "https://www.showwcase.com/{}",
    "Peerlist":            "https://peerlist.io/{}",
    "Indie Hackers":       "https://www.indiehackers.com/{}",
    "WIP":                 "https://wip.co/@{}",
    "Makerlog":            "https://getmakerlog.com/@{}",
    "GNOME GitLab":        "https://gitlab.gnome.org/{}",
    "Freedesktop":         "https://gitlab.freedesktop.org/{}",
    "OSF":                 "https://osf.io/profile/{}",
    "ResearchGate":        "https://www.researchgate.net/profile/{}",
    "Academia.edu":        "https://independent.academia.edu/{}",
    "ORCID":               "https://orcid.org/{}",

    # ══ CYBERSECURITY / CTF ════════════════════════════════════════════════════
    "HackTheBox":          "https://app.hackthebox.com/users/{}",
    "TryHackMe":           "https://tryhackme.com/p/{}",
    "CTFtime":             "https://ctftime.org/user/{}",
    "PicoCTF":             "https://play.picoctf.org/users/{}",
    "PortSwigger":         "https://portswigger.net/web-security/users/{}",
    "Bugcrowd":            "https://bugcrowd.com/{}",
    "HackerOne":           "https://hackerone.com/{}",
    "Intigriti":           "https://app.intigriti.com/researcher/{}",
    "RootMe":              "https://www.root-me.org/{}",
    "ExploitDB":           "https://www.exploit-db.com/author/{}",
    "Shodan":              "https://www.shodan.io/user/{}",
    "ImmersiveLabs":       "https://dca.immersivelabs.online/profile/{}",
    "VulnHub":             "https://www.vulnhub.com/author/{}/",

    # ══ GAMING ═════════════════════════════════════════════════════════════════
    "Steam":               "https://steamcommunity.com/id/{}",
    "Roblox":              "https://www.roblox.com/user.aspx?username={}",
    "Chess.com":           "https://www.chess.com/member/{}",
    "Lichess":             "https://lichess.org/@/{}",
    "Itch.io":             "https://{}.itch.io",
    "GameBanana":          "https://gamebanana.com/members/{}",
    "Nexusmods":           "https://www.nexusmods.com/users/{}",
    "Speedrun.com":        "https://www.speedrun.com/user/{}",
    "Faceit":              "https://www.faceit.com/en/players/{}",
    "ESEA":                "https://play.esea.net/users/{}",
    "Leetify":             "https://leetify.com/app/profile/{}",
    "HLTV":                "https://www.hltv.org/profile/{}",
    "Battlefy":            "https://battlefy.com/users/{}",
    "Challonge":           "https://challonge.com/users/{}",
    "Game Jolt":           "https://gamejolt.com/@{}",
    "Kongregate":          "https://www.kongregate.com/accounts/{}",
    "Newgrounds":          "https://{}.newgrounds.com",
    "Armor Games":         "https://armorgames.com/user/{}",
    "GOG":                 "https://www.gog.com/u/{}",
    "Overwolf":            "https://www.overwolf.com/app/{}",
    "Giant Bomb":          "https://www.giantbomb.com/profile/{}",
    "GameFAQs":            "https://gamefaqs.gamespot.com/community/{}",
    "IGDB":                "https://www.igdb.com/users/{}",
    "Backloggd":           "https://www.backloggd.com/u/{}",
    "Grouvee":             "https://www.grouvee.com/user/{}",
    "Fortnite Tracker":    "https://fortnitetracker.com/profile/all/{}",
    "R6 Tracker":          "https://r6.tracker.network/profile/{}",
    "Chess24":             "https://chess24.com/en/profile/{}",
    "Toornament":          "https://www.toornament.com/en_US/player/{}",

    # ══ MUSIC / AUDIO ══════════════════════════════════════════════════════════
    "Spotify":             "https://open.spotify.com/user/{}",
    "SoundCloud":          "https://soundcloud.com/{}",
    "LastFm":              "https://www.last.fm/user/{}",
    "Bandcamp":            "https://{}.bandcamp.com",
    "ReverbNation":        "https://www.reverbnation.com/{}",
    "Audiomack":           "https://audiomack.com/{}",
    "Mixcloud":            "https://www.mixcloud.com/{}",
    "Musescore":           "https://musescore.com/user/{}",
    "Musixmatch":          "https://www.musixmatch.com/profile/{}",
    "Genius":              "https://genius.com/{}",
    "Songkick":            "https://www.songkick.com/users/{}",
    "Setlist.fm":          "https://www.setlist.fm/user/{}",
    "Rate Your Music":     "https://rateyourmusic.com/~{}",
    "Discogs":             "https://www.discogs.com/user/{}",
    "Deezer":              "https://www.deezer.com/en/profile/{}",

    # ══ VIDEO / STREAMING ══════════════════════════════════════════════════════
    "Vimeo":               "https://vimeo.com/{}",
    "Dailymotion":         "https://www.dailymotion.com/{}",
    "Rumble":              "https://rumble.com/user/{}",
    "Odysee":              "https://odysee.com/@{}",
    "BitChute":            "https://www.bitchute.com/channel/{}",
    "Peertube":            "https://peertube.social/accounts/{}",
    "Bilibili":            "https://space.bilibili.com/{}",
    "Niconico":            "https://www.nicovideo.jp/user/{}",
    "Streamlabs":          "https://streamlabs.com/{}",
    "Glimesh":             "https://glimesh.tv/{}",
    "Trovo":               "https://trovo.live/s/{}",
    "Caffeine":            "https://www.caffeine.tv/{}",
    "Throne":              "https://throne.com/{}",

    # ══ PHOTOGRAPHY / ART / DESIGN ═════════════════════════════════════════════
    "Flickr":              "https://www.flickr.com/people/{}",
    "500px":               "https://500px.com/p/{}",
    "Unsplash":            "https://unsplash.com/@{}",
    "Pexels":              "https://www.pexels.com/@{}",
    "DeviantArt":          "https://www.deviantart.com/{}",
    "ArtStation":          "https://www.artstation.com/{}",
    "Behance":             "https://www.behance.net/{}",
    "Dribbble":            "https://dribbble.com/{}",
    "Figma":               "https://www.figma.com/@{}",
    "Pixiv":               "https://www.pixiv.net/en/users/{}",
    "Sketchfab":           "https://sketchfab.com/{}",
    "Thingiverse":         "https://www.thingiverse.com/{}",
    "Cults3D":             "https://cults3d.com/en/users/{}",
    "Printables":          "https://www.printables.com/@{}",
    "CGTrader":            "https://www.cgtrader.com/{}",
    "Turbosquid":          "https://www.turbosquid.com/Search/Artists/{}",
    "VSCO":                "https://vsco.co/{}",
    "Glass":               "https://glass.photo/{}",
    "EyeEm":               "https://www.eyeem.com/u/{}",
    "Pixilart":            "https://www.pixilart.com/{}",
    "Adobe Portfolio":     "https://{}.myportfolio.com",

    # ══ WRITING / BLOGGING ═════════════════════════════════════════════════════
    "Medium":              "https://medium.com/@{}",
    "Ghost":               "https://{}.ghost.io",
    "Write.as":            "https://write.as/{}",
    "Mirror.xyz":          "https://mirror.xyz/{}",
    "Wattpad":             "https://www.wattpad.com/user/{}",
    "Fanfiction.net":      "https://www.fanfiction.net/u/{}",
    "Archive of Our Own":  "https://archiveofourown.org/users/{}",
    "Quotev":              "https://www.quotev.com/{}",
    "Inkitt":              "https://www.inkitt.com/{}",
    "Bear Blog":           "https://{}.bearblog.dev",
    "Prose":               "https://prose.sh/{}",

    # ══ Q&A / FORUMS ═══════════════════════════════════════════════════════════
    "Disqus":              "https://disqus.com/by/{}/",
    "Discourse":           "https://meta.discourse.org/u/{}",
    "XDA Developers":      "https://forum.xda-developers.com/member.php?username={}",
    "Spiceworks":          "https://community.spiceworks.com/people/{}",
    "LinusTechTips":       "https://linustechtips.com/profile/{}",
    "AnandTech":           "https://forums.anandtech.com/member.php?username={}",
    "MetaFilter":          "https://www.metafilter.com/user/{}",
    "Slashdot":            "https://slashdot.org/~{}",
    "Know Your Meme":      "https://knowyourmeme.com/users/{}",
    "Urban Dictionary":    "https://www.urbandictionary.com/author.php?author={}",
    "TV Tropes":           "https://tvtropes.org/pmwiki/pmwiki.php/Tropers/{}",
    "Fandom":              "https://{}.fandom.com",
    "Tildes-Forum":        "https://tildes.net/user/{}",

    # ══ EDUCATION / CODING PRACTICE ════════════════════════════════════════════
    "Duolingo":            "https://www.duolingo.com/profile/{}",
    "Khan Academy":        "https://www.khanacademy.org/profile/{}",
    "Codecademy":          "https://www.codecademy.com/profiles/{}",
    "freeCodeCamp":        "https://www.freecodecamp.org/{}",
    "Leetcode":            "https://leetcode.com/{}",
    "HackerRank":          "https://www.hackerrank.com/{}",
    "Codewars":            "https://www.codewars.com/users/{}",
    "Exercism":            "https://exercism.org/profiles/{}",
    "CodinGame":           "https://www.codingame.com/profile/{}",
    "TopCoder":            "https://www.topcoder.com/members/{}",
    "Codeforces":          "https://codeforces.com/profile/{}",
    "AtCoder":             "https://atcoder.jp/users/{}",
    "SPOJ":                "https://www.spoj.com/users/{}",
    "Edabit":              "https://edabit.com/user/{}",

    # ══ PROFESSIONAL / FREELANCE ═══════════════════════════════════════════════
    "ProductHunt":         "https://www.producthunt.com/@{}",
    "AngelList":           "https://angel.co/u/{}",
    "Wellfound":           "https://wellfound.com/u/{}",
    "Crunchbase":          "https://www.crunchbase.com/person/{}",
    "Freelancer":          "https://www.freelancer.com/u/{}",
    "Upwork":              "https://www.upwork.com/freelancers/{}",
    "Fiverr":              "https://www.fiverr.com/{}",
    "Guru":                "https://www.guru.com/freelancers/{}",
    "PeoplePerHour":       "https://www.peopleperhour.com/freelancer/{}",
    "Contra":              "https://contra.com/{}",
    "Polywork":            "https://www.polywork.com/{}",

    # ══ LINK-IN-BIO / IDENTITY ═════════════════════════════════════════════════
    "Linktree":            "https://linktr.ee/{}",
    "About.me":            "https://about.me/{}",
    "Gravatar":            "https://en.gravatar.com/{}",
    "Carrd":               "https://{}.carrd.co",
    "Bio.link":            "https://bio.link/{}",
    "Stan.store":          "https://stan.store/{}",
    "Beacons":             "https://beacons.ai/{}",
    "Campsite":            "https://campsite.bio/{}",
    "Koji":                "https://koji.to/{}",
    "Tap.bio":             "https://tap.bio/@{}",

    # ══ SUPPORT / MONETIZATION ═════════════════════════════════════════════════
    "Patreon":             "https://www.patreon.com/{}",
    "Ko-fi":               "https://ko-fi.com/{}",
    "Buy Me a Coffee":     "https://www.buymeacoffee.com/{}",
    "Gumroad":             "https://gumroad.com/{}",
    "Kickstarter":         "https://www.kickstarter.com/profile/{}",
    "Indiegogo":           "https://www.indiegogo.com/individuals/{}",
    "GoFundMe":            "https://www.gofundme.com/{}",
    "Cash.app":            "https://cash.app/${}",
    "Venmo":               "https://venmo.com/u/{}",
    "PayPal.me":           "https://www.paypal.me/{}",

    # ══ SPORTS / FITNESS ═══════════════════════════════════════════════════════
    "Strava":              "https://www.strava.com/athletes/{}",
    "Garmin Connect":      "https://connect.garmin.com/modern/profile/{}",
    "MyFitnessPal":        "https://www.myfitnesspal.com/profile/{}",
    "Runkeeper":           "https://runkeeper.com/user/{}",
    "Zwift":               "https://www.zwift.com/athlete/{}",
    "Peloton":             "https://members.onepeloton.com/members/{}/overview",

    # ══ TRAVEL / LOCAL ═════════════════════════════════════════════════════════
    "Couchsurfing":        "https://www.couchsurfing.com/users/{}",
    "Tripadvisor":         "https://www.tripadvisor.com/members/{}",
    "Yelp":                "https://www.yelp.com/user_details?userid={}",
    "Foursquare":          "https://foursquare.com/{}",
    "Untappd":             "https://untappd.com/user/{}",
    "Vivino":              "https://www.vivino.com/users/{}",
    "AllTrails":           "https://www.alltrails.com/members/{}",
    "Komoot":              "https://www.komoot.com/user/{}",

    # ══ SHOPPING / MARKETPLACE ═════════════════════════════════════════════════
    "Etsy":                "https://www.etsy.com/people/{}",
    "eBay":                "https://www.ebay.com/usr/{}",
    "Depop":               "https://www.depop.com/{}",
    "Poshmark":            "https://poshmark.com/closet/{}",
    "Vinted":              "https://www.vinted.com/member/{}",
    "Grailed":             "https://www.grailed.com/{}",
    "StockX":              "https://stockx.com/{}",
    "Reverb":              "https://reverb.com/shop/{}",
    "Mercari":             "https://www.mercari.com/u/{}",

    # ══ BOOKS / ANIME / MEDIA ══════════════════════════════════════════════════
    "Letterboxd":          "https://letterboxd.com/{}",
    "Goodreads":           "https://www.goodreads.com/{}",
    "LibraryThing":        "https://www.librarything.com/profile/{}",
    "Storygraph":          "https://app.thestorygraph.com/profile/{}",
    "MyAnimeList":         "https://myanimelist.net/profile/{}",
    "AniList":             "https://anilist.co/user/{}",
    "Kitsu":               "https://kitsu.io/users/{}",
    "Anime-Planet":        "https://www.anime-planet.com/users/{}",
    "Mangadex":            "https://mangadex.org/user/{}",
    "Crunchyroll":         "https://www.crunchyroll.com/user/{}",
    "TV Time":             "https://www.tvtime.com/en/user/{}/profile",
    "IMDb":                "https://www.imdb.com/user/{}",
    "Simkl":               "https://simkl.com/{}",
    "Trakt":               "https://trakt.tv/users/{}",
    "Flipboard":           "https://flipboard.com/@{}",
    "Pocket":              "https://getpocket.com/@{}",

    # ══ CRYPTO / WEB3 ══════════════════════════════════════════════════════════
    "OpenSea":             "https://opensea.io/{}",
    "Rarible":             "https://rarible.com/user/{}",
    "Foundation":          "https://foundation.app/@{}",
    "SuperRare":           "https://superrare.com/{}",
    "Zora":                "https://zora.co/{}",
    "Gitcoin":             "https://gitcoin.co/{}",

    # ══ WIKI / KNOWLEDGE ═══════════════════════════════════════════════════════
    "Wikipedia":           "https://en.wikipedia.org/wiki/User:{}",
    "Wikimedia Commons":   "https://commons.wikimedia.org/wiki/User:{}",
    "Fandom-Wiki":         "https://www.fandom.com/u/{}",
    "ArchWiki":            "https://wiki.archlinux.org/index.php/User:{}",
    "Gentoo Wiki":         "https://wiki.gentoo.org/wiki/User:{}",
    "Ubuntu Wiki":         "https://wiki.ubuntu.com/{}",
    "Fedora Wiki":         "https://fedoraproject.org/wiki/User:{}",
    "Debian Wiki":         "https://wiki.debian.org/{}",
    "OpenSUSE Wiki":       "https://en.opensuse.org/User:{}",
}

# ─── VARIATION ENGINE ──────────────────────────────────────────────────────────
def generate_variations(username: str) -> list:
    u = username.lower()
    variations = set()
    variations.add(u)

    for sep in ["_", ".", "-"]:
        variations.add(f"{u}{sep}")

    for n in ["1", "2", "3", "0", "99", "01", "007", "69", "404", "x", "666", "777", "42"]:
        variations.add(f"{u}{n}")
        variations.add(f"{n}{u}")

    if len(u) > 2:
        variations.add(f"{u}{u[-1]}")

    for pre in ["the", "i_am", "iam", "real", "official", "xX", "its", "im", "mr", "dr"]:
        variations.add(f"{pre}{u}")
        variations.add(f"{pre}_{u}")

    for suf in ["_official", "_real", "_irl", "hq", "tv", "yt", "_pro", "_og", "_xx"]:
        variations.add(f"{u}{suf}")

    for yr in ["2003", "2004", "2005", "2006", "2007", "2023", "2024", "2025"]:
        variations.add(f"{u}{yr}")

    tr_map = {"ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c"}
    ascii_u = u
    for k, v in tr_map.items():
        ascii_u = ascii_u.replace(k, v)
    if ascii_u != u:
        variations.add(ascii_u)
        variations.add(f"{ascii_u}_")
        variations.add(f"{ascii_u}1")

    leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
    leet_u = u
    for k, v in leet_map.items():
        leet_u = leet_u.replace(k, v)
    if leet_u != u:
        variations.add(leet_u)

    return sorted(list(variations))

# ─── HTTP CHECK ────────────────────────────────────────────────────────────────
def check_url(url: str, timeout: int = 8) -> tuple:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
        )
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ms = int((time.time() - t0) * 1000)
            return (resp.status, ms)
    except urllib.error.HTTPError as e:
        return (e.code, 0)
    except Exception:
        return (0, 0)

# ─── SPINNER ──────────────────────────────────────────────────────────────────
class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    def __init__(self):
        self._running = False
        self._thread = None
        self.msg = ""
    def _spin(self):
        i = 0
        while self._running:
            sys.stdout.write(f"\r{C}{self.FRAMES[i % len(self.FRAMES)]} {self.msg}{RESET}  ")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
    def start(self, msg=""):
        self.msg = msg
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        sys.stdout.write("\r" + " " * 70 + "\r")
        sys.stdout.flush()

# ─── MODES ────────────────────────────────────────────────────────────────────

def mode_whoami(username, timeout=8, verbose=False, output="", **kw):
    print(f"\n{C}┌─ {W}[WHOAMI MODE]{C} ─────────────────────────────────────────────")
    print(f"{C}│  {Y}Hedef   : {W}{username}")
    print(f"{C}│  {Y}Platform: {W}{len(PLATFORMS)}")
    print(f"{C}└──────────────────────────────────────────────────────────{RESET}\n")

    found = []
    lock = threading.Lock()

    def check(name, url_t):
        url = url_t.format(username)
        code, ms = check_url(url, timeout)
        hit = code in (200, 301, 302)
        with lock:
            if hit:
                found.append((name, url, ms))
                print(f"  {G}[✓]{RESET} {W}{name:<22}{RESET} {DG}{url} {G}({ms}ms){RESET}")
            elif verbose:
                print(f"  {R}[✗]{RESET} {DG}{name:<22} HTTP {code}{RESET}")

    threads = [threading.Thread(target=check, args=(n, u), daemon=True) for n, u in PLATFORMS.items()]
    spinner = Spinner()
    spinner.start(f"Tarıyor: {username}  [{len(PLATFORMS)} platform]")
    for t in threads:
        t.start()
        time.sleep(0.01)
    for t in threads:
        t.join()
    spinner.stop()

    print(f"\n{C}╔══════════════════════════════════════════════════════╗")
    print(f"║  {G}{len(found)}{W} platform bulundu  /  {len(PLATFORMS)} tarandı{C}              ║")
    print(f"╚══════════════════════════════════════════════════════╝{RESET}\n")

    if output:
        _save(username, found, output)


def mode_wildcard(username, timeout=8, verbose=False, output="", **kw):
    variations = generate_variations(username)
    print(f"\n{M}┌─ {W}[WILDCARD MODE]{M} ────────────────────────────────────────────")
    print(f"{M}│  {Y}Kaynak      : {W}{username}")
    print(f"{M}│  {Y}Varyasyon   : {W}{len(variations)}")
    print(f"{M}│  {Y}Platform    : {W}{len(PLATFORMS)}")
    print(f"{M}│  {Y}Toplam istek: {W}{len(variations) * len(PLATFORMS)}")
    print(f"{M}└──────────────────────────────────────────────────────────{RESET}\n")

    print(f"{DG}Üretilen varyasyonlar:{RESET}")
    for i, v in enumerate(variations):
        end = "\n" if (i + 1) % 6 == 0 else "  "
        print(f"  {C}{v:<22}{RESET}", end=end)
    print("\n")

    confirm = input(f"{Y}Tüm varyasyonları tara? [y/N]: {RESET}").strip().lower()
    if confirm != "y":
        print(f"{DG}İptal.{RESET}")
        return

    all_found = {}
    for var in variations:
        print(f"\n{C}[>>] {W}{var}{RESET}")
        _scan_quiet(var, timeout, all_found)

    total = sum(len(v) for v in all_found.values())
    print(f"\n{M}╔══════════════════════════════════════════════════════╗")
    print(f"║  {G}{total}{W} hit  |  {G}{len(all_found)}{W} aktif varyasyon  {M}                ║")
    print(f"╚══════════════════════════════════════════════════════╝{RESET}\n")

    for var, hits in all_found.items():
        print(f"  {Y}▸ {var}{RESET}")
        for name, url, ms in hits:
            print(f"      {G}[✓] {W}{name:<22}{RESET} {DG}{url}{RESET}")

    if output:
        _save_wildcard(username, all_found, output)


def mode_recon(username, timeout=8, verbose=False, output="", **kw):
    hacker_keys = [
        "GitHub", "GitLab", "Bitbucket", "Codeberg", "Gitea", "Sourcehut",
        "HackerNews", "Dev.to", "Replit", "Codepen", "StackOverflow",
        "Keybase", "HackTheBox", "TryHackMe", "CTFtime", "PicoCTF",
        "PortSwigger", "Bugcrowd", "HackerOne", "Intigriti", "RootMe",
        "ExploitDB", "DockerHub", "NPM", "PyPI", "Crates.io", "Hackaday",
        "Hackster", "Leetcode", "HackerRank", "Codewars", "Codeforces",
        "Reddit", "DevRant", "Lobsters", "Daily.dev", "Peerlist",
    ]
    plat = {k: v for k, v in PLATFORMS.items() if k in hacker_keys}

    print(f"\n{R}┌─ {W}[RECON MODE]{R} ────────────────────────────────────────────────")
    print(f"{R}│  {Y}Hedef    : {W}{username}")
    print(f"{R}│  {Y}Platform : {W}{len(plat)} (hacker/dev odaklı)")
    print(f"{R}└──────────────────────────────────────────────────────────{RESET}\n")

    found = []
    lock = threading.Lock()

    def check(name, url_t):
        url = url_t.format(username)
        code, ms = check_url(url, timeout)
        if code in (200, 301, 302):
            with lock:
                found.append((name, url, ms))
                print(f"  {G}[✓]{RESET} {W}{name:<22}{RESET} {DG}{url} {G}({ms}ms){RESET}")
        elif verbose:
            with lock:
                print(f"  {R}[✗]{RESET} {DG}{name:<22} HTTP {code}{RESET}")

    threads = [threading.Thread(target=check, args=(n, u), daemon=True) for n, u in plat.items()]
    spinner = Spinner()
    spinner.start(f"Recon: {username}")
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    spinner.stop()

    print(f"\n{R}[RECON]{RESET}  {G}{len(found)}{W} / {len(plat)} platformda bulundu{RESET}\n")
    if output:
        _save(username, found, output)


def mode_vargen(username, **kw):
    variations = generate_variations(username)
    print(f"\n{Y}┌─ {W}[VARGEN MODE]{Y} ─────────────────────────────────────────────")
    print(f"{Y}│  {W}{username} {DG}için {len(variations)} varyasyon")
    print(f"{Y}└──────────────────────────────────────────────────────────{RESET}\n")
    for v in variations:
        print(f"  {C}▸{RESET}  {v}")
    print()


def mode_single(username, site="", timeout=8, **kw):
    match = {k: v for k, v in PLATFORMS.items() if site.lower() in k.lower()}
    if not match:
        print(f"{R}[!] '{site}' bulunamadı.{RESET}")
        return
    print(f"\n{B}┌─ {W}[SINGLE MODE]{B} ─────────────────────────────────────────────")
    print(f"{B}│  {Y}Hedef: {W}{username}  {Y}Platform: {W}{site}")
    print(f"{B}└──────────────────────────────────────────────────────────{RESET}\n")
    for name, url_t in match.items():
        url = url_t.format(username)
        code, ms = check_url(url, timeout)
        if code in (200, 301, 302):
            print(f"  {G}[✓] {W}{name}{RESET}  {DG}{url}  {G}({ms}ms){RESET}")
        else:
            print(f"  {R}[✗] {W}{name}{RESET}  {DG}HTTP {code}{RESET}")


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _scan_quiet(username, timeout, results_dict):
    found = []
    lock = threading.Lock()
    def check(name, url_t):
        url = url_t.format(username)
        code, ms = check_url(url, timeout)
        if code in (200, 301, 302):
            with lock:
                found.append((name, url, ms))
                print(f"    {G}[✓]{RESET} {W}{name:<22}{RESET} {DG}{url}{RESET}")
    threads = [threading.Thread(target=check, args=(n, u), daemon=True) for n, u in PLATFORMS.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if found:
        results_dict[username] = found


def _save(username, found, filepath):
    with open(filepath, "w") as f:
        f.write(f"SHENWIN — {username} — {datetime.now().isoformat()}\n{'='*60}\n")
        for name, url, ms in found:
            f.write(f"[FOUND] {name}: {url} ({ms}ms)\n")
    print(f"\n{G}[✓] Kaydedildi: {W}{filepath}{RESET}")


def _save_wildcard(username, all_found, filepath):
    with open(filepath, "w") as f:
        f.write(f"SHENWIN Wildcard — {username} — {datetime.now().isoformat()}\n{'='*60}\n")
        for var, hits in all_found.items():
            if hits:
                f.write(f"\n[VAR] {var}\n")
                for name, url, _ in hits:
                    f.write(f"  [FOUND] {name}: {url}\n")
    print(f"\n{G}[✓] Kaydedildi: {W}{filepath}{RESET}")


# ─── HELP ─────────────────────────────────────────────────────────────────────

def print_help():
    print(RABBIT)
    print(f"{W}KULLANIM:{RESET}")
    print(f"  {C}shenwin {Y}-w  {W}<username>          {DG}# Whoami: {len(PLATFORMS)} platformda ara{RESET}")
    print(f"  {C}shenwin {Y}-ww {W}<username>          {DG}# Wildcard: varyasyonlarla tara{RESET}")
    print(f"  {C}shenwin {Y}-r  {W}<username>          {DG}# Recon: hacker/dev platformları{RESET}")
    print(f"  {C}shenwin {Y}-v  {W}<username>          {DG}# Vargen: sadece varyasyon listele{RESET}")
    print(f"  {C}shenwin {Y}-s  {W}<username> <site>   {DG}# Single: tek platformda ara{RESET}")
    print(f"\n{W}SEÇENEKLER:{RESET}")
    print(f"  {C}--timeout N    {DG}# HTTP zaman aşımı (varsayılan: 8s){RESET}")
    print(f"  {C}--verbose      {DG}# 404'leri de göster{RESET}")
    print(f"  {C}--output FILE  {DG}# Sonuçları .txt olarak kaydet{RESET}")
    print(f"  {C}--no-color     {DG}# Renksiz çıktı{RESET}")
    print(f"\n{W}ÖRNEKLER:{RESET}")
    print(f"  {DG}$ python3 shenwin.py -w LatenT{RESET}")
    print(f"  {DG}$ python3 shenwin.py -ww LatenT --output sonuc.txt{RESET}")
    print(f"  {DG}$ python3 shenwin.py -r elliot --verbose{RESET}")
    print(f"  {DG}$ python3 shenwin.py -s LatenT github{RESET}\n")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    # Hiç argüman girilmediyse veya yardım istendiyse
    if len(sys.argv) < 2 or any(arg in sys.argv for arg in ("-h", "--help")):
        print(BANNER)
        print_help()
        sys.exit(0)

    # Ana parser (add_help=False diyoruz çünkü kendi yardım menümüzü kullanıyoruz)
    parser = argparse.ArgumentParser(add_help=False)
    
    # Bayrakları (flags) tanımlıyoruz
    parser.add_argument("-w", "--whoami", dest="whoami")
    parser.add_argument("-ww", "--wildcard", dest="wildcard")
    parser.add_argument("-r", "--recon", dest="recon")
    parser.add_argument("-v", "--vargen", dest="vargen")
    parser.add_argument("-s", "--single", nargs=2, metavar=('USER', 'SITE'))
    
    # Seçenekleri tanımlıyoruz
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--output", dest="output", default="")
    parser.add_argument("--no-color", action="store_true")

    # Bilinmeyen argüman hatasını önlemek için parse_known_args kullanabiliriz
    args, unknown = parser.parse_known_args()

    # Renk ayarı
    if args.no_color:
        global R, G, Y, B, C, M, W, DG, RESET, BOLD
        R = G = Y = B = C = M = W = DG = RESET = BOLD = ""

    print(BANNER)

    try:
        # Hangi modun aktif olduğunu kontrol et
        if args.whoami:
            mode_whoami(username=args.whoami, timeout=args.timeout, verbose=args.verbose, output=args.output)
        
        elif args.wildcard:
            mode_wildcard(username=args.wildcard, timeout=args.timeout, verbose=args.verbose, output=args.output)
        
        elif args.recon:
            mode_recon(username=args.recon, timeout=args.timeout, verbose=args.verbose, output=args.output)
        
        elif args.vargen:
            mode_vargen(username=args.vargen)
        
        elif args.single:
            # args.single bir liste döndürür: [username, site]
            mode_single(username=args.single[0], site=args.single[1], timeout=args.timeout)
            
        else:
            # Eğer hiçbiri yoksa ama argüman varsa (hatalı kullanım)
            print(f"{R}[!] Hatalı parametre kullanımı.{RESET}")
            print_help()

    except KeyboardInterrupt:
        print(f"\n\n{R}[!] İşlem kullanıcı tarafından durduruldu.{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{R}[!] Beklenmedik hata: {e}{RESET}")

if __name__ == "__main__":
    main()
