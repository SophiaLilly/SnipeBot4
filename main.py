# pip install -U discord-py-interactions
# pip install -u interactions-get
# pip install -U git+https://github.com/interactions-py/library@unstable
import json, os, asyncio
from tracker import SnipeTracker
from data_types.interactions import CustomInteractionsClient

with open("config.json") as f:
    DISCORD_CONFIG_DATA = json.load(f)["discord"]
    TOKEN = DISCORD_CONFIG_DATA["token"]

# Define Bot

# IMPORTANT: IF NOT CHANGING ANY COGS - ENABLE DISABLE_SYNC BELOW
# WHEN DISABLE_SYNC IS TRUE IT DOES NOT CALL THE DISCORD API FOR INTERACTIONS
client = CustomInteractionsClient(TOKEN, disable_sync=True)
client.tracker: SnipeTracker = SnipeTracker(client)
client.running: bool = False

# Bot Online
@client.event
async def on_ready():
    print("\n\n\n\n\n\n\n\n")
    try:
        print("Bot Connected To Discord")
        if client.running == False:
            client.running = True
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    client.load(f"cogs.{filename[:-3]}")
            print("All cogs loaded successfully")
            print("Starting main loop in 3 seconds")
            await asyncio.sleep(3)
            await client.tracker.start_loop()
        else:
            pass
    except Exception as e:
        print(f"An Error Occured: {e}")

# must be final line
if __name__ == '__main__':
    client.start()