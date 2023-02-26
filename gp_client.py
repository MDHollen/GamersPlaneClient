from bs4 import BeautifulSoup
from datetime import datetime as dt, timezone, timedelta
from dateutil.parser import parse as date_parse
from dateutil.tz import tzoffset
from discord import Intents

import discord
import json
import requests
import typer

app = typer.Typer()
session = requests.Session()

API_ENDPOINT = 'https://discord.com/api/v10'

@app.command()
def notify_update(
    config_file: str,
):
    """Check for updates in the specified forums/subforums and notify the user if updates exist."""

    with open(config_file, "r") as f:
        config = json.load(f)

    forum_list = config["forums"]

    _reauth_gamersplane(config["gp_auth"]["username"], config["gp_auth"]["password"])

    for forum in forum_list:
        updates = _check_for_updates(forum["name"], forum["id"], forum["threads"], config["update_offset"])

    if len(updates) > 0:
        _notify_user(updates, config["discord_auth"])
    
def _check_for_updates(forum_name, forum_id, watched_threads, update_offset):
    """Check specified forum_id to see if any of the specified subforums have been updated."""

    # Get thread info from forum page
    gp_url = "https://gamersplane.com"
    forum_url = f"{gp_url}/forums/{forum_id}/"
    forum_html = session.get(forum_url)
    forum_info = BeautifulSoup(forum_html.text, "html.parser")

    thread_list = forum_info.find_all("div", "td threadInfo")[1:]

    # Get the last post from each thread page
    last_post_time_list = forum_info.find_all("div", "lastPost")[1:]
    last_post_href_list = [
        a["href"] for a in forum_info.find_all("a")
        if "href" in a.__dict__["attrs"]
        and "lastPost#lastPost" in a["href"]
    ]

    # Get current time, using UTC (+8 from PST) - since GP also uses UTC on back-end.
    tzinfo = timezone(timedelta(hours=0))
    current_time = dt.now(tzinfo)

    # Format thread info using current timezone
    thread_names = [thread.find("a", "threadTitle").text for thread in thread_list if thread.find("a", "threadTitle")]
    post_time_list = [
        date_parse(last_post_time.find("span", "convertTZ").text, default=current_time)
        for last_post_time in last_post_time_list
        if last_post_time.find("span", "convertTZ")
    ]

    # For each thread, check if thread merits an update and check if it has updated.
    time_offset = update_offset * 60
    updated_threads = []
    for thread_name, post_time, last_post_href in zip(thread_names, post_time_list, last_post_href_list):
        if thread_name in watched_threads:
            time_diff = current_time - post_time
            if time_diff.seconds <= time_offset and time_diff.days == 0:
                updated_threads.append(
                    {
                        "forum_name": forum_name,
                        "thread_name": thread_name,
                        "last_post_time": post_time.replace(tzinfo=timezone(timedelta(hours=-8)), second=0, microsecond=0) + timedelta(hours=-8),
                        "last_post_href": last_post_href,
                    }
                )

    # For each thread that merits an update, get the last post and info about who posted it
    for updated_thread in updated_threads:
        last_post, last_poster, last_char = _get_last_post(gp_url, updated_thread["last_post_href"])
        updated_thread["last_post"] = last_post
        updated_thread["last_poster"] = last_poster
        updated_thread["last_char"] = last_char

    return updated_threads

def _get_last_post(gp_url, last_post_href):
    """Get latest post from specified thread URL."""

    thread_url = f"{gp_url}{last_post_href}"
    thread_html = session.get(thread_url)
    thread_info = BeautifulSoup(thread_html.text, "html.parser")
    last_post = thread_info.find_all("div", "post")[-2].text
    poster_info = thread_info.find_all("div", "postNames")[-2]
    poster_name = poster_info.find("p", "posterName").find("a", "username").text
    try:
        char_name = poster_info.find("p", "charName").find("a").text
    except:
        char_name = None
    return last_post, poster_name, char_name

def _reauth_gamersplane(gp_username, gp_password):
    gp_data = {"email": gp_username, "password": gp_password}
    response = session.post("https://gamersplane.com/login", data=gp_data)
    response.raise_for_status()

def _notify_user(updated_forum_list, discord_auth):
    """Notify the user of any forums which have been updated by sending a Discord message."""

    token = discord_auth["bot_token"]
    channel_id = discord_auth["channel_id"]
    client = discord.Client(intents=Intents.none())

    message = f"Got an update in the following threads:\n"
    for forum_update in updated_forum_list:
        message += f"\n**{forum_update['forum_name']}** - *{forum_update['thread_name']}* updated by "
        message += f"***{forum_update['last_char']} ({forum_update['last_poster']})*** " \
        if forum_update["last_char"] else f"***{forum_update['last_poster']}***"
        message == f"at {forum_update['last_post_time']}:\n"
        message += f"*{forum_update['last_post'][1:300]}...*"

    @client.event
    async def on_ready():
        channel = await client.fetch_channel(channel_id)
        await channel.send(message)
        await client.close()

    client.run(token)

def _get_discord_token(bot_token):
    """Get token for discord authentication"""

    auth = (client_id, secret)
    response = session.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers, auth=auth)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    app()
