import json
import sys
import os
import logging
from os.path import join, dirname

# Get the dependencies for this project
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "../vendored"))
sys.path.append(os.path.join(here, "../shared"))

# Now import the dependency libraries
import requests
from dotenv import load_dotenv
import telegram
from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler

# Import shared modules
from OverwatchAPI import OverwatchAPI
from BadgeGenerator import BadgeGenerator

# Set-up the environment variables
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Instantiate
telegram_api_key = os.environ.get("TELEGRAM_API_KEY")

# Instatiate the bot
bot = Bot(telegram_api_key)
dispatcher = Dispatcher(bot, None, workers=0)

# Instatiate the other classes
overwatch = OverwatchAPI(logger, requests, BadgeGenerator)


def respond(err, res=None):
    """Return status message back to Telegram's webhook."""
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def start(bot, update):
    """Initial conversation started with the bot."""
    msg = "Hey there! I'm the Overwatch stats api\n"
    msg += "If you give me your Overwatch battletag, " \
        "I can look up your latest stats\n"
    msg += "*Remember your battletag is case-sensitive!*\n"
    msg += "`/overwatch [battletag] [region]` - " \
        "Will return latest stats for this battletag." \
        "_Region defaults to US_\n"
    msg += "`/stats [battletag] [region]` - " \
        "Will return latest stats for this battletag." \
        " _Region defaults to US_\n"
    bot.sendMessage(update.message.chat_id, text=msg, parse_mode='Markdown')
    return respond(None, {'message': 'sendMessage complete'})


def error(bot, update, error):
    """Log errors received by the bot."""
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def processCommand(event, context):
    """Event given to the bot are decoded and handled here."""
    logger.info('event: %s', event)
    logger.info('context: %s', context)

    body = json.loads(event['body'])
    logger.info('body: %s', body)
    update = telegram.Update.de_json(body)
    dispatcher.process_update(update)

    return respond(None, {'message': 'OK'})


dispatcher.add_handler(CommandHandler(
    "start",
    start
))
dispatcher.add_handler(CommandHandler(
    "overwatch",
    overwatch.getUserStats,
    pass_args=True
))
dispatcher.add_handler(CommandHandler(
    "stats",
    overwatch.getUserStats,
    pass_args=True
))
dispatcher.add_error_handler(error)
