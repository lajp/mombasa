import discord, youtube_dl, time, math, secrets

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "no_color": True,
    "default_search": "auto",
    "source_address": "0.0.0.0"
}

ffmpeg_options = {
    "options": "-vn"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        self.prefix = "?"
        self.queue = []
        self.looping = False
        self.current = None
        self.skipped = False

    async def on_message(self, message):
        if(message.author.id == self.user.id):
            return

        if(message.content.startswith(self.prefix)):
            command = message.content.split()[0][1:]
            if(command == "join"):
                if(message.author.voice is None):
                    return await message.reply("You are not connected to a voice channel!")
                channel = message.author.voice.channel
                return await self.join(channel)

            if(command == "play" or command == "p"):
                if(message.author.voice is None):
                    return await message.reply("You are not connected to a voice channel!")
                channel = message.author.voice.channel
                await self.join(channel)
                query = message.content[message.content.find(" ")+1:]
                if(query == message.content):
                    if(self.voice_clients[0].is_paused()):
                        self.voice_clients[0].resume()
                        return await message.channel.send("Playback resumed!")
                    return await message.channel.send("Please provide a link or a searchterm!")
                try:
                    data = ytdl.extract_info(query, download=False)
                except Exception as error:
                    return await message.channel.send("Ran into an error while processing the request: {}".format(repr(error)))
                if data["_type"] == "playlist" and len(data["entries"]) > 1:
                    started = self.voice_clients[0].is_playing()
                    oldstarted = 0
                    for entry in data["entries"]:
                        if not "title" in entry:
                            print(entry)
                            continue
                        if not started:
                            self.current = entry
                            self.play(entry.copy())
                            await message.channel.send("Started playing `{}`!".format(entry["title"]))
                            started = True
                            oldstarted = 1
                        else:
                            self.queue.append(entry)
                    if(not "title" in data):
                        title = "an unknown playlist"
                    else:
                        title = data["title"]
                    return await message.channel.send("Enqueued `{0}` tracks from playlist `{1}`".format(len(data["entries"])-oldstarted, title))
                else:
                    if "entries" in data:
                        data = data["entries"][0]
                    if not "title" in data:
                        print(data)
                        return await message.channel.send("We ran into an unknown error while processing the request")
                    if(self.voice_clients[0].is_playing()):
                        self.queue.append(data)
                        return await message.channel.send("`{0}` has been put in the queue and it's currently on the position #{1}".format(data["title"], len(self.queue)))
                    else:
                        self.current = data
                        self.play(data.copy())
                        return await message.channel.send("Started playing {}".format(data["title"]))

            if(command == "mombasa"):
                if(message.author.voice is None):
                    return await message.reply("You are not connected to a voice channel!")
                channel = message.author.voice.channel
                await self.join(channel)
                self.looping = True
                mombasa = ytdl.extract_info("https://www.youtube.com/watch?v=EFrrEUNlH0c", download=False)
                self.queue = []
                if(self.voice_clients[0].is_playing()):
                    self.voice_clients[0].stop()
                self.current = mombasa
                self.play(mombasa.copy())
                return await message.channel.send("Jäi Mombasaan, vain päivä elämää! Ja elämään, nyt Mombasa vain jää! :notes:")

            if(command == "np"):
                if(self.voice_clients[0].is_playing()):
                    return await message.channel.send("Now playing `{}`".format(self.current["title"]))
                return await message.channel.send("Nothing's playing right now!")

            if(command == "disconnect" or command == "dis"):
                await self.leave()

            if(command == "q" or command == "queue"):
                if(self.queue == []):
                    return await message.channel.send("The queue is empy.")
                embed=discord.Embed(title="The queue ({0} tracks in total)".format(len(self.queue)), color=discord.Color.blue())
                try:
                    en = int(message.content.split()[1])-1
                except:
                    en = 0
                for i in range(en*10, min(en*10+10, len(self.queue))):
                    minutes = math.floor(self.queue[i]["duration"]/60)
                    seconds = self.queue[i]["duration"]-(minutes*60)
                    embed.add_field(name="{0}. {1} ({2}:{3} min)".format(self.queue.index(self.queue[i])+1, self.queue[i]["title"], minutes, seconds),
                            value="[Link to the video](https://www.youtube.com/watch?v={})".format(self.queue[i]["id"]), inline=False)
                embed.set_footer(text="Page {0}/{1}".format(en+1, math.ceil(len(self.queue)/10)))

                return await message.channel.send(embed=embed)

            if(command == "skip" or command == "s"):
                if self.voice_clients[0].is_playing():
                    self.current = None
                    self.skipped = True
                    self.voice_clients[0].stop()
                    return await message.channel.send("Skipped!")
                return await message.channel.send("Nothing's playing!")

            if(command == "pause"):
                if self.voice_clients[0].is_playing():
                    self.voice_clients[0].pause()
                    return await message.channel.send("Playback paused!")
                return await message.channel.send("Nothing's playing!")

            if(command == "clear"):
                self.queue = []
                return await message.channel.send("Queue cleared!")

            if(command == "rm" or command == "remove"):
                try:
                    index = int(message.content.split()[1])-1
                    entry = self.queue.pop(index)
                except:
                    return await message.channel.send("Please provide a valid index!")
                return await message.channel.send("Removed {} from the queue!".format(entry["title"]))

            if(command == "loop"):
                if(self.looping):
                    self.looping = False
                    return await message.channel.send("Looping disabled!")
                self.looping = True
                return await message.channel.send("Looping enabled!")

            if(command == "prefix"):
                try:
                    newprefix = message.content.split()[1]
                except:
                    return await message.channel.send("Please give a valid prefix")
                self.prefix = newprefix
                return await message.channel.send("Prefix set to `{}`!".format(self.prefix))

            if(command == "skipto" or command == "st"):
                try:
                    index = int(message.content.split()[1])
                    if(len(self.queue) < index):
                        raise IndexError
                except:
                    return await message.channel.send("Please give a valid index")
                self.queue = self.queue[index-1:]
                self.voice_clients[0].stop()
                return await message.channel.send("Skipped `{}` elements in the queue".format(index))


    def play_queue(self, *args):
        try:
            if(self.voice_clients[0].is_playing()):
                return
        except IndexError:
            return
        if(self.current == None and not self.skipped):
            return
        if (not self.looping) or self.current == None:
            self.skipped = False
            if(self.queue != []):
                try:
                    data = self.queue.pop(0)
                    self.current = data
                except:
                    return
            else:
                return
        else:
            data = self.current
        return self.loop.run_in_executor(None, self.play, data)

    def play(self, data):
        try:
            filename = data["url"]
        except:
            return -1
        player = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
        return self.voice_clients[0].play(player, after=self.play_queue)


    async def join(self, channel):
        if(self.voice_clients != []):
            if(self.voice_clients[0].channel.id == channel.id):
                return
            return await self.voice_clients[0].move_to(channel)
        return await channel.connect()

    async def leave(self):
        if(self.voice_clients != []):
            for vc in self.voice_clients:
                vc.stop()
                await vc.disconnect()
        return

client = MyClient()

client.run(secrets.token)
