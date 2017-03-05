import sys
import os
from StringIO import StringIO
from io import BytesIO
from os.path import join, dirname

# Get the dependencies for this project
here = os.path.dirname(os.path.realpath(__file__))

fontsLoc = os.path.join(here, "../fonts")
imagesLoc = os.path.join(here, "../images")

sys.path.append(os.path.join(here, "../vendored"))
sys.path.append(os.path.join(here, "../shared"))

# Now import the dependency libraries
from PIL import Image, ImageDraw, ImageFont


class BadgeGenerator:
    def __init__(self, logger, requests):
        self.logger = logger
        self.requests = requests

    def move(self, posDiff, align='left', baseCanvas=None, elm=None):
        if align is 'right':
            if baseCanvas is None:
                print "Unable to align right if there is no baseCanvas"
            else:
                if len(posDiff) is 2:
                    displacement = ((baseCanvas.size[0] - elm.size[0] + posDiff[0]), posDiff[1])
                elif len(posDiff) is 1:
                    displacement = ((baseCanvas.size[0] - elm.size[0] + posDiff[0]), 0)
        else:
            if len(posDiff) > 2:
                print "The posDiff is too large, max is 2, min is 1. Length is {length}".format(length=len(posDiff))
                return
            elif len(posDiff) == 2:
                displacement = (posDiff[0], posDiff[1])
            elif len(posDiff) == 1:
                displacement = (posDiff[0], 0)

        return displacement

    def fontGen(self, size=10, fontName='BigNoodleToo'):
        return ImageFont.truetype('{fontsLoc}/{fontName}.ttf'.format(
            fontsLoc=fontsLoc,
            fontName=fontName
        ), size=size)


    def generateBadge(self, gameStats, battleTag):
        quickPlayGameStats = gameStats['quickplay']['game_stats']
        quickPlayOverallStats = gameStats['quickplay']['overall_stats']

        competitiveGameStats = gameStats['competitive']['game_stats']
        competitiveOverallStats = gameStats['competitive']['overall_stats']

        if quickPlayOverallStats['tier'] is not None:
            rank = quickPlayOverallStats['tier']
        else:
            rank = 'none'

        userData = {
            'quickplay': {
                'wins': quickPlayOverallStats['wins'],
                'kpd': quickPlayGameStats['kpd'],
                'time_played': quickPlayGameStats['time_played']
            },
            'comp': {
                'wins': competitiveOverallStats['wins'],
                'losses': competitiveOverallStats['losses'],
                'ties': competitiveOverallStats['ties'],
                'rank': rank,
                'win_rate': competitiveOverallStats['win_rate']
            },
        }

        # 16:9 ratio = (640/360)

        # Base Values
        baseSize = (640, 360)

        # Manual Sizes
        thumbnailSize = (128, 128)

        # Fills
        fontFill = (255, 255, 255, 255)
        greenFontFill = (18, 215, 53, 255)  # green
        redFontFill = (254, 78, 78, 255)  # red

        # Fonts
        fontSize = 45
        nameFontSize = 65
        winRateFontSize = 55
        fontDisplacement = 20
        fontName = 'BigNoodleToo'
        nameFontName = 'BigNoodleTooOblique'

        # Positioning Values
        nameLocation = (10, 10)

        compTitleLocation = self.move((10, nameFontSize + 20))
        compWinStatsLoc = self.move(
            (10,
            fontSize + compTitleLocation[1]) # Size of Font + Y-axis position of Comp Title
        )

        compLossesPosX = (fontDisplacement * ((len(str(userData['comp']['wins']))) + 3)) + compWinStatsLoc[0] # "Wins: " + Total numerical wins
        compLossesStatsLoc = self.move(
            (compLossesPosX,
            fontSize+compTitleLocation[1])
        )

        compTiesPosX = (((fontDisplacement - 1) * ((len(str(userData['comp']['losses']))) + 3)) + compLossesStatsLoc[0])
        compTiesStatsLoc = self.move(
            (compTiesPosX,
                fontSize + compTitleLocation[1])
        )

        winRatePosX = (fontDisplacement * (len(str(userData['comp']['ties'])) + 3) + compTiesPosX)
        winRateLoc = self.move(
            (winRatePosX,
                fontSize + compTitleLocation[1] - 7)
        )

        winRateFontFill = greenFontFill if userData['comp']['win_rate'] > 50 else redFontFill

        quickPlayTitleLoc = self.move((10, fontSize+compLossesStatsLoc[1] + 30))
        quickPlayWinsLoc = self.move((10, fontSize+quickPlayTitleLoc[1]))

        quickPlayKDPosX = (fontSize / 2.5) * (len(str(userData['quickplay']['wins'])) + 6) # "Wins: " + Total numerical wins
        quickPlayKDLoc = self.move((quickPlayKDPosX, fontSize+quickPlayTitleLoc[1]))

        totalHoursPlayedLoc = self.move((10, fontSize+quickPlayKDLoc[1]))

        # The Base Image
        base = Image.new('RGBA', baseSize, (153, 17, 153, 255))  # Purple
        # Generated Text
        txt = Image.new('RGBA', baseSize, (0, 0, 0, 0))

        # Avatar
        # Retrieve their avatar from Battlenet
        avatarResponse = self.requests.get(quickPlayOverallStats['avatar'])
        avatar = Image.open(StringIO(avatarResponse.content))
        avatar.thumbnail(thumbnailSize)
        avatar_pos = self.move((-10, 10), 'right', base, avatar)

        # Rank
        tierImageLoc = "{imagesLoc}/ranks/{rank}.png".format(
            imagesLoc=imagesLoc,
            rank=userData['comp']['rank']
        )
        rank = Image.open(tierImageLoc)
        rank.thumbnail(thumbnailSize)
        # rank.save('./images/ranks/thumbnails/{rank}.png'.format(rank=userData['comp']['rank']))
        rank_pos = self.move((-10, (avatar.size[1] + 10)), 'right', base, rank)

        nameFont = self.fontGen(nameFontSize, nameFontName)
        font = self.fontGen(fontSize, fontName)

        # Get a drawing context
        d = ImageDraw.Draw(txt)

        # BattleNet Name
        d.text(
            nameLocation,
            battleTag,
            font=nameFont,
            fill=fontFill
        )

        # Competitive Stats
        d.text(compTitleLocation, "Competitive Stats", font=font, fill=fontFill)

        # Wins
        d.text(
            compWinStatsLoc,
            "W: {wins}".format(wins=userData['comp']['wins']),
            font=font,
            fill=fontFill
        )

        # Losses
        d.text(
            compLossesStatsLoc,
            "L: {losses}".format(losses=userData['comp']['losses']),
            font=font,
            fill=fontFill
        )

        # Ties
        d.text(
            compTiesStatsLoc,
            "T: {ties}".format(ties=userData['comp']['ties']),
            font=font,
            fill=fontFill
        )

        # Win Rate
        d.text(
            winRateLoc,
            "{win_rate}%".format(
                win_rate=userData['comp']['win_rate']),
            font=self.fontGen(winRateFontSize),
            fill=winRateFontFill
        )

        # QuickPlay Stats
        d.text(quickPlayTitleLoc, "QuickPlay Stats", font=font, fill=fontFill)

        # Wins
        d.text(
            quickPlayWinsLoc,
            "Wins: {wins}".format(wins=userData['quickplay']['wins']),
            font=font,
            fill=fontFill
        )

        # Kill/Death
        d.text(
            quickPlayKDLoc,
            "K/D: {kpd}".format(kpd=userData['quickplay']['kpd']),
            font=font,
            fill=fontFill
        )

        # Total Hours Played
        d.text(
            totalHoursPlayedLoc,
            "Total Hours Played: {total}".format(total=userData['quickplay']['time_played']),
            font=font,
            fill=fontFill
        )

        # Texts placed on base image
        badge = Image.alpha_composite(base, txt)

        # Avatar placed on composite base image
        badge.paste(avatar, avatar_pos)

        # Rank placed on composite base + avatar image
        badge.paste(rank, rank_pos, rank)  # Rank is used twice so that it can mask itself

        # Generate and save the image in memory and return the raw image data in PNG format
        temp = BytesIO()  # File object
        badge.save(temp, format="jpeg")
        temp.seek(0)
        return temp
