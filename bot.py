import asyncio
import configparser
import datetime
import discord
import pytz

# Create a new Discord client
intents = discord.Intents.default()
intents.voice_states = True  # Enable voice state intents
intents.guilds = True  # Enable guild intents
intents.members = True  # Enable members intent
client = discord.Client(intents=intents)

# Read the configuration file
config = configparser.ConfigParser()
config.read("config.ini")

# Get the values from the configuration file
try:
    tz = pytz.timezone(config.get("General", "tz"))
    channel_id = int(config.get("General", "channel_id"))
    role_name = config.get("General", "role_name")
    role_id = int(config.get("General", "role_id"))
    voice_channel_id = int(config.get("General", "voice_channel_id"))
    text_channel_id = int(config.get("General", "text_channel_id"))
    role_name_vc_notify = config.get("General", "role_name_vc_notify")
    token = config.get("General", "token")
    test_user_id = int(config.get("General", "test_user_id"))  # Add test user ID from config
except (ValueError, KeyError) as e:
    print(f"Error: {e}")
    exit()

# Convert the notification time to 12-hour format
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
        # Get the current time in the specified time zone
        now = datetime.datetime.now(tz)

        # Check if the current time matches any of the notification times
        for notification_time in notification_times:
            if now.strftime("%H:%M") == notification_time:
                # Convert notification_time to 12-hour clock format
                notification_time_12h = datetime.datetime.strptime(notification_time, "%H:%M").strftime("%I:%M %p")

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
    print(f"Voice state update: {member} moved from {before.channel} to {after.channel}")

    # Check if the member joined the specified voice channel
    if before.channel != after.channel and after.channel is not None and after.channel.id == voice_channel_id:
        print(f"Member {member} joined the voice channel {after.channel.name}.")
        text_channel = client.get_channel(text_channel_id)
        if text_channel is not None:
            role = discord.utils.get(member.guild.roles, name=role_name_vc_notify)
            if role is not None:
                for member_with_role in role.members:
                    print(f"Checking member: {member_with_role.display_name}")
                    if (member_with_role.voice is None and member_with_role != member and not member_with_role.bot) or member.id == test_user_id:
                        permissions = member.guild.me.guild_permissions
                        if not permissions.send_messages:
                            print("Error: Bot does not have permission to send DMs to members.")
                            return
                        try:
                            dm_channel = await member_with_role.create_dm()
                            await dm_channel.send(f"{member.display_name} joined {after.channel.name}!")
                            print(f"Sent DM to {member_with_role.display_name}")
                        except discord.Forbidden:
                            print(f"Error: Cannot send DM to {member_with_role.display_name}.")
        else:
            print(f"Error: Text channel with ID {text_channel_id} not found.")

@client.event
async def on_ready():
    print("Bot is online and ready.")
    # Start sending notifications
    asyncio.ensure_future(send_notification())

# Run the client
try:
    client.run(token)
except discord.LoginFailure:
    print("Error: Invalid token provided.")
    exit()
