# GamersPlaneClient
Client built to be used in a cron job, to periodically poll the GamersPlane site and send a discord message to a server when a new post is found.

This software is designed for Python3.9.2

Usage:
python gp_client.py config.json

This will pull any updates from the forums and threads listed in config.json, and send a roll-up of the updates to the specified Discord server.

config.json:

"update_offset" is the number of minutes between updates, as specified in your crontab (or Task Scheduler, though that has some issues).

The "gp_auth" field needs your GamersPlane credentials - "username" and "password".

The "discord_auth" field needs the Discord bot's credentials and the ID of the discord channel where messages are to be posted - "bot_token" and "channel_id".
A Discord bot can be created using the Discord Developer Portal: https://discord.com/developers/applications. The Token can be generated by going to the 'Bot' tab on your specific bot's page.

The "forums" field is a list containing a dict for each forum, describing which threads to monitor.

The config.json should look something like this:

    {
        "update_offset": <int>,

        "gp_auth": {
            "username": <str>,
            "password": <str>,
        },
        "discord_auth": {
            "bot_token": <str>,
            "channel_id": <str>,
        }
        "forums": [
            {
                "name": <str>,
                "id": <int>,
                "threads": [
                    <str>, ...
                ]
            }, ...
        ]
    }
