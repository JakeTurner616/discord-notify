import asyncio
import configparser
import datetime
import discord
import pytz

# create a new Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# read the configuration file
config = configparser.ConfigParser()
config.read("config.ini")

# get the values from the configuration file
try:
    tz = pytz.timezone(config.get("General", "tz"))
    channel_id = int(config.get("General", "channel_id"))
    role_name = config.get("General", "role_name")
    role_id = int(config.get("General", "role_id"))
    voice_channel_id = int(config.get("General", "voice_channel_id"))
    text_channel_id = int(config.get("General", "text_channel_id"))
    role_name_vc_notify = config.get("General", "role_name_vc_notify")
    token = config.get("General", "token")
except (ValueError, KeyError) as e:
    print(f"Error: {e}")
    exit()
# convert the notification time to 12-hour format
notification_times = config["General"]["times"].split(",")

# Mention the special role using the role ID
mention = f"<@&{role_id}>"


async def send_notification():
    # Get the channel object
    channel = client.get_channel(channel_id)

    # Check if notification_times is empty
    if not notification_times:
        print("Error: No notification times found in config.")
        return
    

    last_notification_time = None

    while True:
        # Get the current time in Mountain Time
        now = datetime.datetime.now(tz)

        # Check if the current time matches any of the notification times
        for notification_time in notification_times:
            if now.strftime("%H:%M") == notification_time:
                # Convert notification_time to 12-hour clock format
                notification_time_12h = datetime.datetime.strptime(
                    notification_time, "%H:%M"
                ).strftime("%I:%M %p")

                # Check if this is the first notification or if the last notification was not at this time
                if last_notification_time is None or last_notification_time != notification_time:
                    # Define the message to be sent
                    message = f"{mention} the time is now: {notification_time_12h}"

                    # Send the message
                    await channel.send(message)

                    # Update the last notification time
                    last_notification_time = notification_time

        # Wait for 2 seconds before checking the time again
        await asyncio.sleep(2)


@client.event
async def on_voice_state_update(member, before, after):
    text_channel = client.get_channel(text_channel_id)
    if text_channel is not None:
        role = discord.utils.get(member.guild.roles, name=role_name_vc_notify)
        if role is not None:
            for member_with_role in role.members:
                permissions = member.guild.me.guild_permissions
                if not permissions.send_messages:
                    print("Error: Bot does not have permission to send DMs to members.")
                    return
                try:
                    dm_channel = await member_with_role.create_dm()
                    await dm_channel.send(
                        f"{member.display_name} joined {after.channel.name}!"
                    )
                except discord.HTTPException as e:
                    if e.status == 403:
                        print("Error: Bot does not have permission to DM this member.")
                    else:
                        print(f"Error sending DM to {member_with_role.display_name}: {e}")
        else:
            print(f"Error: Role with name {role_name_vc_notify} not found.")
    else:
        print(f"Error: Text channel with ID {text_channel_id} not found.")


# start the bot
@client.event
async def on_ready():
    print("Bot is online and ready.")
    # start sending notifications
    asyncio.ensure_future(send_notification())


# run the client
try:
    client.run(token)
except discord.LoginFailure:
    print("Error: Invalid token provided.")
    exit()
