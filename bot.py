import os
import openai
import discord
from discord.ext import commands

# Import and load the .env file
from dotenv import load_dotenv
load_dotenv()

# Set up the OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

conversation_histories = {}

# Set up intents to allow the bot to read messages and members
intents = discord.Intents.default()
intents.members = True
intents.typing = True
intents.message_content = True

# Set up bot to accept commands
bot = commands.Bot(command_prefix="!", intents=intents)

system_prompt = "You are a helpful Discord bot that responds to users' questions. Keep the answers short and to the point."
system_model = "gpt-3.5-turbo"


async def generate_gpt_response(prompt, user_id):
    # Retrieve conversation history or create a new one
    conversation_history = conversation_histories.get(user_id, [
        {"role": "system", "content": system_prompt}
    ])

    # Add the user's message to the conversation history
    conversation_history.append({"role": "user", "content": prompt})

    # Generate the response using the conversation history
    response = openai.ChatCompletion.create(
        model=system_model,
        messages=conversation_history
    )

    # Extract the bot's response and add it to the conversation history
    bot_response = str(response['choices'][0]['message']['content'])
    conversation_history.append({"role": "assistant", "content": bot_response})

    # Save the updated conversation history
    conversation_histories[user_id] = conversation_history

    return bot_response


@bot.event
async def on_ready():
    print(f"{bot.user} is connected to Discord!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        if "forget me" in message.content.lower():
            # If message content contains "forget me", delete the conversation history for the user
            user_id = message.author.id
            conversation_histories[user_id] = [
                {"role": "system", "content": system_prompt}
            ]
            await message.channel.send("Conversation history reset.")
        else:
            # Otherwise, generate a response using GPT-3.5-turbo
            async with message.channel.typing():
                response = await generate_gpt_response(message.content, message.author.id)
                await message.channel.send(response, reference=message)
    else:
        await bot.process_commands(message)


# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
