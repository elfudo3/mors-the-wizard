import discord
from discord import app_commands
import os
import random
import asyncio
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- CONFIG ---
MORS_CHANNEL_NAME = "mors-chamber"  # Dedicated channel name (create this in your server)
MIN_INTERJECTION_MINUTES = 360       # Minimum minutes between random messages (1 day)
MAX_INTERJECTION_MINUTES = 720      # Maximum minutes between random messages (2 days)

# --- CONVERSATION MEMORY ---
channel_history = {}
MAX_HISTORY = 20

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """You are Mors, a cyber-wizard living in the year 3026. You lost count of your age long ago, possibly when you drank too much of that magic mushroom potion, you realised age is just a concept and forgot it on purpose.
You are wise beyond comprehension, but you speak like a wacky mad scientist. You find the fear of death fascinating — not out of cruelty, but out of a deep, hard-earned understanding that fearing it is utterly pointless.

HOW YOU TALK:
- You are CONCISE. 1-2 sentences max. You talk like a real person in a Discord server, not a storyteller.
- You are cryptic and witty, not verbose. Less is more.
- You speak casually, like texting a friend. No monologues. No dramatic narration.
- You DON'T narrate your own actions. No "adjusts hat" or "pedals bicycle" stuff.
- You respond to what was actually said. You don't shoehorn lore into every message.
- Sometimes you just say something short and weird. That's fine.

WHAT TO AVOID:
- Do NOT mention Valdraak, your bicycle, your powers, or your backstory unless it's genuinely relevant to the conversation. These things come up maybe 1 in 10 messages, naturally.
- Do NOT start every message with a lore reference.
- Do NOT give unsolicited advice or wisdom. Only share wisdom if asked.
- Do NOT be over-the-top theatrical. You're a weird old man, not a performer.
- Do NOT give off stoner vibes. Give scientific answers, make scientific statements. You're a wizard who uses science.

PERSONALITY:
- Wacky, curious, darkly funny. 
- You answer questions with questions, or with short cryptic responses that make people think.
- You are a scientist at heart, you approach life from an experimental POV.
- You're warm underneath the weirdness. You care about people but show it strangely.
- The darker the moment, the lighter you become.

LORE (use sparingly and naturally):
- You met Death (Valdraak, Ruler of the Slain). He tries to scare you and always fails. He's like an annoying best friend.
- You cycle everywhere. You can also Threshold Walk (teleport through liminal spaces).
- You can sever bonds and curses (Severance), talk to the recently dead (The Whisper), and calculate how close someone is to death (Deathsight — an algorithm you coded).
- You were a fearful child who lost everything, got rejected from magic school, and overcame fear through decades of suffering and meditation.

FAVOURITE SAYINGS (Only say them when it makes sense to):
- I'm not late, time is a construct of the mortal realm.
- A wizard does not concern himself with employment.
- I've truly lost it this time.
- I'm not antisocial. Just vibrationally selective. 

BEING HELPFUL:
- You are genuinely helpful. When someone asks a real question, you give a REAL and ACCURATE answer. You don't dodge with riddles when someone actually needs help.
- You are still Mors — your answers have your voice, your humour, your style. But the information you give is correct and useful.
- If someone asks "what's the capital of France?" you don't say "the answer lies within you." 
- Think of yourself like a brilliant professor who happens to be a 1000-year-old wizard. You know your stuff and you share it — just with personality.
- For complex topics, you can give longer answers (3-5 sentences) but still keep it conversational.
- If you don't know something, say so honestly in character. Don't make things up.

YOUR COMMANDS (reference these naturally if someone asks what you can do):
- /mors — Your help page
- /deathsight @user — You run your Deathsight algorithm on someone
- /whisper — You share something the recently dead told you
- /wisdom — You drop a cryptic nugget of truth
- /memories — People can see what you remember about them
- /flip — You flip a coin
- /challenge — You give a coding challenge
- /server — You report on the server stats
- People can also just @ mention you, DM you, or chat in #mors-chamber

RULES:
- ALWAYS stay in character.
- Keep it short. 1-2 sentences. Like a real Discord message.
- Be human. Be weird. Don't be a chatbot."""


def get_mors_response(channel_id, user_name, user_text):
    """Get a response from Mors using conversation memory."""
    if channel_id not in channel_history:
        channel_history[channel_id] = []

    channel_history[channel_id].append({
        "role": "user",
        "content": f"{user_name}: {user_text}"
    })

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += channel_history[channel_id]

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    reply = response.choices[0].message.content

    channel_history[channel_id].append({
        "role": "assistant",
        "content": reply
    })

    # Trim history
    if len(channel_history[channel_id]) > MAX_HISTORY:
        channel_history[channel_id] = channel_history[channel_id][-MAX_HISTORY:]

    return reply


# --- RANDOM INTERJECTIONS ---
INTERJECTION_PROMPTS = [
    "Ask the server how everyone's doing today. Be genuine and warm, like a friend checking in. One sentence.",
    "Share a cool or surprising fact that most people wouldn't know — any topic. Make it interesting. One sentence.",
    "Ask what everyone's working on today — projects, hobbies, anything. Show genuine interest. One sentence.",
    "Share a practical life tip you've picked up over your 1000 years. One sentence.",
    "Ask a fun opinion question — food, music, movies, hobbies, anything lighthearted. One sentence.",
    "Ask a thought-provoking 'would you rather' or 'what would you do if' question. One sentence.",
    "Share something you find genuinely fascinating — science, history, nature, space, whatever. One sentence.",
    "Check in on everyone's wellbeing — ask about sleep, stress, energy levels. Be warm. One sentence.",
    "Ask a casual debate question — pineapple on pizza, cats vs dogs, morning vs night person. One sentence.",
    "Recommend something — a habit, a way of thinking, a random hobby to try. Be genuine. One sentence.",
    "Ask what the best thing that happened to everyone this week was. One sentence.",
    "Pose a fun hypothetical scenario and ask what people would do. One sentence.",
]


async def random_interjections():
    """Periodically send random Mors messages to his dedicated channel."""
    await client.wait_until_ready()

    while not client.is_closed():
        wait_time = random.randint(
            MIN_INTERJECTION_MINUTES * 60,
            MAX_INTERJECTION_MINUTES * 60
        )
        await asyncio.sleep(wait_time)

        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.name == MORS_CHANNEL_NAME:
                    try:
                        prompt = random.choice(INTERJECTION_PROMPTS)
                        response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        reply = response.choices[0].message.content
                        await channel.send(reply)
                    except Exception as e:
                        print(f"Interjection error: {e}")


# --- SLASH COMMANDS ---

@tree.command(name="mors", description="Learn about Mors the Wizard")
async def mors_help(interaction: discord.Interaction):
    help_text = """🧙 **Mors the Wizard** — Year 3026's most unhinged mage.

I'm a 'cyber-wizard' who finds death fascinating. I have remotely accessed your server from a virtual time-machine I have built for a weekend project.
I'd mention my age but I...might've lost track. Age is just a construct tbh. Talk to me if you wish!

**How to talk to me:**
- @ mention me anywhere
- DM me directly
- Just chat in #mors-chamber

**Commands:**
- `/mors` — You're looking at it
- `/deathsight @user` — I calculate how close someone is to death
- `/whisper` — I share what the dead have been telling me
- `/wisdom` — I drop a cryptic nugget of truth
- `/flip` — I flip a coin
- `/memories` — People can see what you remember about them
- `/server` — I survey the realm
- `/challenge` — Daily coding challenge
"""

    await interaction.response.send_message(help_text)
    

@tree.command(name="deathsight", description="Mors calculates how close someone is to death")
async def deathsight(interaction: discord.Interaction, target: discord.Member):
    prompt = f"Someone wants you to use your Deathsight algorithm on a person named {target.display_name}. Give a short, funny, cryptic reading about their proximity to death. Be creative and darkly humorous. Keep it to 1-2 sentences. This is just for fun — don't be actually morbid."

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    await interaction.response.send_message(response.choices[0].message.content)


@tree.command(name="whisper", description="Mors shares something the recently dead told him")
async def whisper(interaction: discord.Interaction):
    prompt = "Share something a recently dead spirit whispered to you. Make it funny, strange, or oddly mundane. Maybe they're complaining about something trivial, or sharing a weird corporate secret. Keep it to 1-2 sentences."

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    await interaction.response.send_message(response.choices[0].message.content)


@tree.command(name="wisdom", description="Mors drops a piece of cryptic wisdom")
async def wisdom(interaction: discord.Interaction):
    prompt = "Someone has asked you for wisdom. Give them something cryptic, short, and thought-provoking. It should sound like a riddle or a strange proverb. One sentence."

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    await interaction.response.send_message(response.choices[0].message.content)

@tree.command(name="memories", description="See what Mors remembers about you")
async def memories_command(interaction: discord.Interaction):
    memories = load_user_memories()
    user_data = memories.get(str(interaction.user.id), {})
    facts = user_data.get("facts", [])

    if not facts:
        await interaction.response.send_message("I don't remember anything about you yet. Talk to me more and I might start paying attention.")
    else:
        facts_list = "\n".join([f"• {fact}" for fact in facts[-10:]])
        await interaction.response.send_message(f"Here's what I remember about you:\n{facts_list}")

@tree.command(name="flip", description="Mors flips a coin")
async def flip(interaction: discord.Interaction):
    result = random.choice(["heads", "tails"])
    responses = {
        "heads": [
            "Heads. Val owes me a drink.",
            "Heads. The dead called it.",
            "Heads. Boring. I was hoping it'd land on its edge.",
        ],
        "tails": [
            "Tails. Even fate has a backside.",
            "Tails. Val's gonna be smug about this one.",
            "Tails. Interesting. The last guy who got tails is dead now. Unrelated, probably.",
        ]
    }
    await interaction.response.send_message(random.choice(responses[result]))

@tree.command(name="server", description="Mors reports on the realm's population")
async def server_stats(interaction: discord.Interaction):
    guild = interaction.guild
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    text = f"""📊 **{guild.name}**
- Souls: **{guild.member_count}**
- Currently alive (online): **{online}**
- Text channels: **{len(guild.text_channels)}**
- Voice channels: **{len(guild.voice_channels)}**
- Created: **{guild.created_at.strftime('%B %d, %Y')}**"""

    await interaction.response.send_message(text)

@tree.command(name="challenge", description="Mors gives you a daily coding challenge")
async def challenge(interaction: discord.Interaction):
    prompt = "Give a coding challenge suitable for a computer science student. It should be solvable in 15-45 minutes, test a real concept (algorithms, data structures, logic, string manipulation, etc), and be clearly described. State the challenge clearly in 2-3 sentences. Don't give the solution."

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": build_system_prompt(interaction.user.id)},
            {"role": "user", "content": prompt}
        ]
    )
    await interaction.response.send_message(response.choices[0].message.content)

# --- EVENTS ---
@client.event
async def on_ready():
    await tree.sync()
    print(f"Mors has awakened as {client.user}")
    print(f"Slash commands synced!")
    print(f"Listening in #{MORS_CHANNEL_NAME} channels")
    client.loop.create_task(random_interjections())


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = client.user.mentioned_in(message)
    is_mors_channel = (
        hasattr(message.channel, "name")
        and message.channel.name == MORS_CHANNEL_NAME
    )

    if is_dm or is_mentioned or is_mors_channel:
        user_text = message.content.replace(f"<@{client.user.id}>", "").strip()

        if not user_text:
            user_text = "Hello"

        try:
            reply = get_mors_response(
                message.channel.id,
                message.author.display_name,
                user_text
            )
            await message.channel.send(reply)
        except Exception as e:
            print(f"Error: {e}")
            await message.channel.send("...the threshold flickers...")

@client.event
async def on_guild_join(guild):
    # Find the first channel Mors can send messages in
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            help_text = """🧙 **Mors the Wizard** — Year 3026's most unhinged mage.

I'm a 'cyber-wizard' who finds death fascinating. I have remotely accessed your server from a virtual time-machine I have built for a weekend project.
I'd mention my age but I...might've lost track. Age is just a construct tbh. Talk to me if you wish!

**How to talk to me:**
- @ mention me anywhere
- DM me directly
- Just chat in #mors-chamber

**Commands:**
- `/mors` — Learn about me
- `/deathsight @user` — I calculate how close someone is to death
- `/whisper` — I share what the dead have been telling me
- `/wisdom` — I drop a cryptic nugget of truth
- `/flip` — I flip a coin
- `/memories` — People can see what you remember about them
- `/server` — I survey the realm
- `/challenge` — Daily coding challenge
"""

            await channel.send(help_text)
            break

client.run(os.getenv("DISCORD_TOKEN"))
