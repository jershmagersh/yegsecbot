#!/usr/bin/python

"""
    I wrote this in a couple afternoons while watching Netflix, so it can probably be better.
    -jmag
"""

from slackclient import SlackClient
import sys, json, sqlite3, time, re, datetime

MENTION_REGEX = "^<@(|[WU][A-Z0-9]+?)>(.*)"

class ConfigException(Exception):
    pass

class ConnectionException(Exception):
    pass

class YegsecDatabase:
    def __init__(self, db_path):
        self.path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def confirm_user(self, user, month, year, pref):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user,))
        result = self.cursor.fetchone()
        if not result:
            self.cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user,))
        self.cursor.execute("SELECT meetup_id FROM meetups WHERE month_id = ? and year_id = ?", (month, year))
        meeting_id_a = self.cursor.fetchone()
        if meeting_id_a:
            meeting_id = meeting_id_a[0]
            veg_bool = 0
            if pref:
                veg_bool = 1
            else:
                veg_bool = 0
            self.cursor.execute("SELECT * FROM confirmations WHERE meetup_id = ? AND user_id = ?", (meeting_id, user))
            if(self.cursor.fetchone()):
                return False
            else:
                self.cursor.execute("INSERT INTO confirmations (user_id, meetup_id, pizza_pref) VALUES (?, ?, ?)", (user, meeting_id, veg_bool))
                self.yegsec_commit()
                return True
        else:
            return False

    def remove_confirm_user(self, user, month, year):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user,))
        result = self.cursor.fetchone()
        #A user cannot remove a confirmation if they don't exist in the database already.
        if not result:
            return False
        else:
            self.cursor.execute("SELECT meetup_id FROM meetups WHERE month_id = ? and year_id = ?", (month, year))
            meeting_id_a = self.cursor.fetchone()
            if meeting_id_a:
                meeting_id = meeting_id_a[0]
                self.cursor.execute("DELETE FROM confirmations WHERE user_id = ? AND meetup_id = ?", (user, meeting_id))
                self.yegsec_commit()
            else:
                return False

    def yegsec_commit(self):
        self.conn.commit()
        #self.conn.close()

    def get_summary(self):
        result = self.cursor.execute("SELECT meetup_id FROM meetups")
        results = {}
        meetup_ids = []

        meetup_id = self.cursor.fetchone()
        while(meetup_id):
            meetup_ids.append(meetup_id)
            meetup_id = self.cursor.fetchone()

        for meetup_id_a in meetup_ids:
            meetup_id = meetup_id_a[0]
            self.cursor.execute("SELECT count(*) FROM confirmations WHERE meetup_id = ? AND pizza_pref = 1", (meetup_id,))
            veg_count = self.cursor.fetchone()
            self.cursor.execute("SELECT count(*) FROM confirmations WHERE meetup_id = ? AND pizza_pref = 0", (meetup_id,))
            other_count = self.cursor.fetchone()
            self.cursor.execute("SELECT day_id, month_id, year_id FROM meetups WHERE meetup_id = ?", (meetup_id,))
            date_result = self.cursor.fetchone()

            results[meetup_id] = { "veg": veg_count[0],
                                   "other": other_count[0],
                                   "day": date_result[0],
                                   "month": date_result[1],
                                   "year": date_result[2]
            }

        return results

class YegsecBot:
    def __init__(self, config):
        db, token, rtm_delay = self.read_config(config)
        self.db = YegsecDatabase(db)
        self.bot = SlackClient(token)
        self.rtm_delay = rtm_delay

        if self.bot.rtm_connect(with_team_state=False):
            self.bot_id = self.bot.api_call("auth.test")["user_id"]
            try:
                self.start()
            except KeyboardInterrupt:
                self.db.yegsec_commit()
        else:
            raise ConnectionException("Connection to Slack failed.")

    def read_config(self, config_path):
        f = open(config_path)
        try:
            frj = json.loads(f.read())
        except:
            raise ConfigException("Unable to read provided configuration: {}".format(config_path))
        return frj['database'], frj['token'], frj['rtm_delay']

    #Source: https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
    def parse_bot_commands(self, slack_events):
        """
            Parses a list of events coming from the Slack RTM API to find bot commands.
            If a bot command is found, this function returns a tuple of command and channel.
            If its not found, then this function returns None, None.
        """
        for event in slack_events:
            if event["type"] == "message" and not "subtype" in event:
                user_id, message = self.parse_direct_mention(event["text"])
                if user_id == self.bot_id:
                    #print(event)
                    return message, event["channel"], event["user"]
        return None, None, None

    def parse_direct_mention(self, message_text):
        """
            Finds a direct mention (a mention that is at the beginning) in message text
            and returns the user ID which was mentioned. If there is no direct mention, returns None
        """
        matches = re.search(MENTION_REGEX, message_text)
        # the first group contains the username, the second group contains the remaining message
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    def get_next_meet(self):
        return 3,2019

    def add_user(self, command, channel, user):
        """
            Main function of the bot. We use this command for adding user numbers and their preferred vegetarian options
            to the database.
        """
        rs = re.findall("add me for ([0-9]{1,2}), ?([0-9]{4}) (vegetarian|any)", command, re.IGNORECASE)
        rsm = re.findall("add me next (vegetarian|any)", command, re.IGNORECASE)
        if(len(rs) == 1 or len(rsm) == 1):
            try:
                if len(rs) == 1:
                    month = int(rs[0][0])
                    year = int(rs[0][1])
                elif len(rsm) == 1:
                    month, year = self.get_next_meet()
                    rs = rsm
                month_str = datetime.datetime(year, month, 1).strftime("%B")
                vegetarian = None
                if("VEG" in rs[0][2].upper()):
                    vegetarian = False
                    resp_veg = "vegetarian"
                    vegetarian = True
                else:
                    vegetarian = True
                    resp_veg = "non-vegetarian"
                    vegetarian = False
                result = self.db.confirm_user(user, month, year, vegetarian)
                if result:
                    return(":pizza::pizza::pizza:Thank you <@{}>, I will add you to the pizza numbers for the month {} for the year {} as a {} option:pizza::pizza::pizza:".format(user, month_str, year, resp_veg))
                else:
                    return(":pizza::pizza::pizza:Sorry, <@{}> it looks like you've already been added for that month.:pizza::pizza::pizza:".format(user))
            except:
                return("Sorry, I tried to add you with that command, but I couldn't quite understand it. Please try again.")

    def remove_user(self, command, channel, user):
        """
            Another main function of the bot. We use this command for removing user numbers and their preferred vegetarian options
            from the database.
        """
        rs = re.findall("remove me for ([0-9]{1,2}), ?([0-9]{4})", command, re.IGNORECASE)
        rsm = re.findall("remove me next", command, re.IGNORECASE)
        if(len(rs) == 1 or len(rsm) == 1):
            try:
                if len(rs) == 1:
                    month = int(rs[0][0])
                    year = int(rs[0][1])
                elif len(rsm) == 1:
                    month, year = self.get_next_meet()
                    rs = rsm
                month_str = datetime.datetime(year, month, 1).strftime("%B")
                self.db.remove_confirm_user(user, month, year)
                return(":pizza::pizza::pizza:Thank you <@{}>, I will remove you to the pizza numbers for the month {} for the year {}:pizza::pizza::pizza:".format(user, month_str, year))
            except:
                return("Sorry, I tried to remove you with that command, but I couldn't quite understand it. Please try again.")

    def get_summary(self):
            result = self.db.get_summary()
            response = ""
            for meetup_id, meetup in result.items():
                total_pizza_count = meetup['other'] + meetup['veg']
                response += "*Summary*\nMeetup Date: `{}/{}/{}`\nTotal Pizza Count: `{}`\nNon-Vegetarian: `{}`\nVegetarian: `{}`\n\n".format(meetup['day'], meetup['month'], meetup['year'], total_pizza_count, meetup['other'], meetup['veg'])
            return response

    def get_help(self):
            return "You can send me the following commands:\n\
                    To get added to the next meetup's pizza count do: `add me next [any|vegetarian]`\n\
                    To get added to a future meetup's pizza count do: `add me for [month],[year]`\n\
                    To get removed from the next meetup's pizza count do: `remove me next`\n\
                    To be removed from a future meetup's pizza count do: `remove me [month],[year]`"

    def handle_command(self, command, channel, user):
        """
            Executes bot command if the command is known
        """
        print("Received command: {}".format(command))
        # Default response is help text for the user
        default_response = "Not sure what you mean. Try `{}`".format("help")

        # Finds and executes the given command, filling in response
        response = None
        print("Command received: {}".format(command))
        if command.startswith("add me for") or command.startswith("add me next"):
            response = self.add_user(command, channel, user)

        if command.startswith("remove me for") or command.startswith("remove me next"):
            response = self.remove_user(command, channel, user)

        if command.startswith("summary"):
            response = self.get_summary()

        if command.startswith("help"):
            response = self.get_help()

        # Sends the response back to the channel
        # That only requested user can see
        self.bot.api_call(
            "chat.postEphemeral",
            channel=channel,
            user=user,
            text=response or default_response,
            as_user=True,
        )

    def start(self):
        """
        self.bot.api_call(
            "chat.postMessage",
            channel="general",
            text="I'm alive!",
            as_user=True
        )
        """
        while True:
            command, channel, user = self.parse_bot_commands(self.bot.rtm_read())
            if command:
                self.handle_command(command, channel, user)
            time.sleep(self.rtm_delay)

if __name__ == "__main__":
    bot = YegsecBot("config.json")
