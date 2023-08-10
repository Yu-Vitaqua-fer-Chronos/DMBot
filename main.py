from os import environ
from json import load
from datetime import datetime, timedelta

environ['HATA_CACHE_PRESENCE'] = 'False'
environ['HATA_CACHE_USERS'] = 'False'
environ['HATA_MESSAGE_CACHE_SIZE'] = '0'
environ['HATA_DOCS_ENABLED'] = 'False'

from hata import Client, Channel
from scarletio import Cycler, sleep

with open('config.json') as f:
  token = load(f)['token']

DMBot = Client(token=token)

blacklist = []

blacklist = [Channel.precreate(c) for c in blacklist]

loaded_channels = {}

cycler = None

def check_blacklist(channel):
  if channel in blacklist:
    return True

  for c in blacklist:
    if c.is_guild_thread_public() or c.is_guild_thread_private() or c.is_guild_thread_announcements() or c.is_guild_forum():
      if channel in c.threads:
        return True

    elif c.is_guild_category():
      if channel in c.channel_list:
        return True

  return False


def clear_loaded_list(_):
  now = datetime.now()

  for channel in loaded_channels:
    if (now - loaded_channels[channel]['last_msg']).total_seconds() >= 300:
      del loaded_channels[channel]

def load_channel(channel):
  if channel.is_in_group_textual():
    loaded_channels[channel.id] = {
      'last_msg': (datetime.now() - timedelta(hours=1)),
    }

  return loaded_channels[channel.id]


@DMBot.events
async def ready(client):
  global cycler

  print(f"{client:f} has joined the party!")

  if cycler is None:
    cycler = Cycler(DMBot.loop, 30, clear_loaded_list)

@DMBot.events
async def message_create(client, message):
  if message.author.bot or check_blacklist(message.channel):
    return

  loaded_channel = loaded_channels.get(message.channel.id, False)

  if loaded_channel == False:
    loaded_channel = load_channel(message.channel)

  # TODO: Work on allowing customisable time outs
  if (datetime.now() - loaded_channel['last_msg']).total_seconds() >= 300:
    loaded_channels[message.channel.id]['last_msg'] = datetime.now()

    if not getattr(message, 'content', '').startswith('-'):
      ping_message = await client.message_create(message.channel, '@everyone')
      await sleep(2)
      await client.message_delete(ping_message)

  loaded_channels[message.channel.id]['last_msg'] = datetime.now()

DMBot.start()
