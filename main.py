import logging
import os

from dotenv import load_dotenv
from pyowm import OWM
from pyowm.weatherapi25.observation import Observation
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR
)

logger = logging.getLogger(__name__)

# Default values for the webhook server.
DEFAULT_WEBHOOK_ADDR = "0.0.0.0"
DEFAULT_WEBHOOK_PORT = 8080


# Message displayed when we call /start or /help commands.
help_msg = (
    "/start - bot says 'Hi'\n"
    "/help - show help\n"
    # "/weather - device location weather\n"
    "/weather <write your city> - city weather\n"
)


def start_handler(update: Update, _: CallbackContext) -> None:
    update.message.reply_text(f"Hi {update.effective_user.name}!\n\n{help_msg}")


def help_handler(update: Update, _: CallbackContext) -> None:
    update.message.reply_text(help_msg)


def error_handler(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')


def weather_handler(update: Update, context: CallbackContext):
    # We get text after /weather command.
    args_location = " ".join(context.args).strip()

    # If the user has enabled geolocation, we should
    # be able to retrieve their latitude and longitude.
    user_location = update.message.location

    # We declare our observation instance to use it
    # later to format our bot answer.
    observation: Observation = None

    # We instantiate our PyOWM OWM instance with our API token,
    # then get the weather_manager.
    owm = OWM(os.environ.get("OWM_TOKEN"))
    mgr = owm.weather_manager()

    # Get the weather from the user's device current location.
    if user_location is not None:
        try:
            observation = mgr.weather_at_coords(
                lat=user_location["latitude"], lon=user_location["longitude"]
            )
        except:
            pass
    # The user has disabled geolocation.
    # Get the weather from the city/country passed to the command.
    else:
        try:
            observation = mgr.weather_at_place(args_location)
        except:
            pass

    # We didn't find anything.
    # Let's early return and inform the user.
    if observation is None:
        update.message.reply_text("Sorry, I'm unable to find your location.")
        return

    # Success!
    update.message.reply_text(
        "{} ({})\n\n{}\n{}°C (feels like {}°C)\n{}% humidity".format(
            observation.location.name,
            observation.location.country,
            observation.weather.detailed_status.capitalize(),
            int(observation.weather.temperature(unit="celsius")["temp"]),
            int(observation.weather.temperature(unit="celsius")["feels_like"]),
            observation.weather.humidity,
        )
    )


def main():
    # We load environment variables from .env file.
    load_dotenv()

    # We retrieve the environment mode: development (default) or production.
    # This variable is used to choose between long polling or webhooks.
    env = os.environ.get("ENV", "development").lower()

    # We retrieve the Telegram API token from the environment.
    token = os.environ.get("TG_TOKEN")

    # We retrieve the webhook server settings from the environment.
    webhook_addr = os.environ.get("WEBHOOK_ADDR", DEFAULT_WEBHOOK_ADDR)
    webhook_port = os.environ.get("WEBHOOK_PORT", DEFAULT_WEBHOOK_PORT)
    webhook_url = os.environ.get("WEBHOOK_URL")

    # We create an Updater instance with our API token.
    updater = Updater(token)

    # We register our command handlers.
    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(CommandHandler("help", help_handler))
    updater.dispatcher.add_handler(CommandHandler("weather", weather_handler))
    updater.dispatcher.add_error_handler(error_handler)

    # We are going to use webhooks on production server
    # but long polling for development on local machine.
    if env == "production":
        # Start a small HTTP server to listen for updates via webhook.
        updater.start_webhook(
            listen=webhook_addr,
            port=webhook_port,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}",
        )
        logger.info(f"Start webhook HTTP server - {webhook_addr}:{webhook_port}")
    else:
        # Start polling updates from Telegram.
        updater.start_polling()
        logger.info(f"Start polling updates")

    # Run the bot until you press Ctrl-C.
    # Or until the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == "__main__":
    main()
