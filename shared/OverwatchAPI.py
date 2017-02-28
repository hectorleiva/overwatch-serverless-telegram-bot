class OverwatchAPI:
    def __init__(self, logger, requests, BadgeGenerator):
        self.logger = logger
        self.OverwatchAPIDomain = 'https://owapi.net'
        self.requests = requests
        self.BadgeGenerator = BadgeGenerator(self.logger, self.requests)
        self.regions = ['us', 'eu', 'any', 'kr'] # Supported regions from owapi.net
        self.defaultRegion = 'us'

    # Format prestige rating as stars after their current level
    def prestigeFormatting(self, prestigeLevel, currentLevel):
        prestigeSign = str(currentLevel)
        if prestigeLevel > 0:
            for i in range(prestigeLevel):
                prestigeSign += " *"
            return prestigeSign
        else:
            return prestigeSign

    # args is the array of text passed from the user for their battle info
    def parseBattleInfoArgs(self, args):
        battleInfo = dict()

        if len(args) == 1:
            # Access the only argument given, which should be their battletag
            info = args[0]
            """
            The API can only take in '-' as the delimiter instead of the pound-sign
            that is often used
            """
            if "#" in info:
                battleInfo['battleTagOrg'] = info
                battleInfo['battleTag'] = info.replace('#', '-')
            else:
                battleInfo['battleTag'] = False

            battleInfo['region'] = self.defaultRegion
        elif len(args) > 1:
            for index, info in enumerate(args):
                self.logger.info('info: %s', info)
                # Should be the username to search
                if index == 0:
                    """
                    The API can only take in '-' as the delimiter instead of the pound-sign
                    that is often used
                    """
                    if "#" in info:
                        battleInfo['battleTagOrg'] = info
                        battleInfo['battleTag'] = info.replace('#', '-')
                    else:
                        battleInfo['battleTag'] = False
                # If this exists, then the user is specifying a region value
                elif index == 1:
                    if info in self.regions:
                        battleInfo['region'] = info
                    else:
                        battleInfo['region'] = self.defaultRegion

        return battleInfo

    def htmlFormatBattleInfo(self, title, val):
        # If there is no data returned for the specified stat information
        if not val:
            return ""
        else:
            return "<i>{title}</i>: <strong>{val}</strong>\n".format(
                    title=title,
                    val=val)

    def getUserStats(self, bot, update, args):
        self.logger.info('update: %s', update)
        self.logger.info('args: %s', args)

        if not len(args):
            msg = "Please enter your battletag, it should be something like `<your-name>#1234`\n"
            msg += "The full command should be `/overwatch <your-name>#1234`. You can also add your region"
            msg += " like this: `/overwatch <your-name>#1234 us`"
            return bot.send_message(chat_id=update.message.chat_id,
                text=msg,
                parse_mode='Markdown')

        bot.send_message(chat_id=update.message.chat_id,
                text="Ok, looking up the information, one moment...")

        if len(args) > 2:
            msg = "Sorry! I can only support at most 2 arguments. Your battletag `<your-name>#1234`"
            msg += " and the region `us` or `eu`. the command should look like `<your-name>#1234"
            msg += " or like `<your-name>#1234 us`."
            return bot.send_message(chat_id=update.message.chat_id,
                    text=msg,
                    parse_mode='Markdown')

        battleInfo = self.parseBattleInfoArgs(args)

        self.logger.info('battleInfo: %s', battleInfo)

        if battleInfo:
            if not battleInfo['battleTag']:
                msg = "Please enter your battletag, it should be something like `<your-name>#1234`\n"
                msg += "The full command should be `/overwatch <your-name>#1234`"
                return bot.send_message(chat_id=update.message.chat_id,
                    text=msg,
                    parse_mode='Markdown')

            battleTagStr = str(battleInfo['battleTag'])
            requestUrl = "{apiDomain}/api/v3/u/{battleTag}/stats".format(
                apiDomain=self.OverwatchAPIDomain,
                battleTag=battleTagStr
            )
            headers = { 'user-agent': "{botname}/0.1".format(botname=bot.name) }

            r = self.requests.get(requestUrl, headers=headers)

            self.logger.info('the response: %s', r)

            if r.status_code == 200:
                response = r.json()
                if battleInfo['region'] in response and response[battleInfo['region']] is not None:
                    gameStats = response[battleInfo['region']]['stats']
                    self.logger.info('Game Stats: %s', gameStats)
                    self.logger.info('attempting badge generator for {battleTag}'.format(
                        battleTag=battleTagStr)
                    )
                    badge = self.BadgeGenerator.generateBadge(gameStats, battleTagStr)
                    bot.send_photo(chat_id=update.message.chat_id,
                        photo=badge
                    )
                else:
                    bot.send_message(chat_id=update.message.chat_id,
                            text='Hmmm, the battletag does not exist. Battletags are case-sensitive and region specific. Please double-check that the battletag is correct!')

            elif r.status_code == 500:
                bot.send_message(chat_id=update.message.chat_id,
                        text='Seems like the API is not responding properly. Please try back later!')
            else:
                bot.send_message(chat_id=update.message.chat_id,
                        text='Hmmm, the battletag passed might not exist. Battletags are case-sensitive and region specific. Please double-check that the battletag is correct!')
