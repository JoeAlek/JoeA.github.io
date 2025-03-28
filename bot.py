import discord
import logging
import asyncio
import random
from discord.ext import commands
from commands import CommandsCog
from config import BOT_DESCRIPTION, BOT_PREFIX, BOT_NAME, BOT_OWNER

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Initialize with intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.presences = True
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            description=BOT_DESCRIPTION,
            intents=intents
        )
        
        # Initialize bot status rotation task
        self.status_rotation_task = None
    
    async def setup_hook(self):
        """Setup hook that runs when the bot starts."""
        # Add cogs - properly awaited
        await self.add_cog(CommandsCog(self))
        logger.info("Cogs loaded successfully")
        
        # Start status rotation
        self.status_rotation_task = self.loop.create_task(self.rotate_status())
    
    async def on_ready(self):
        """Event triggered when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Set initial bot activity
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{BOT_PREFIX}commands | {BOT_NAME}"
            ),
            status=discord.Status.online
        )
        
        # Log information about connected guilds
        guilds = [guild.name for guild in self.guilds]
        logger.info(f"Connected to {len(guilds)} guilds: {', '.join(guilds)}")
        
        # Print some usage stats
        member_count = sum(guild.member_count for guild in self.guilds)
        logger.info(f"Serving {member_count} members across all guilds")
    
    async def rotate_status(self):
        """Rotate the bot's status message periodically."""
        await self.wait_until_ready()
        
        statuses = [
            (discord.ActivityType.listening, f"{BOT_PREFIX}commands | {BOT_NAME}"),
            (discord.ActivityType.playing, f"in {len(self.guilds)} servers"),
            (discord.ActivityType.watching, "for your messages"),
            (discord.ActivityType.listening, f"{BOT_PREFIX}help | AI-powered"),
            (discord.ActivityType.playing, "with Discord automation"),
            (discord.ActivityType.watching, "over your server")
        ]
        
        while not self.is_closed():
            status_type, status_name = random.choice(statuses)
            
            # If it's the server count status, update it
            if "servers" in status_name:
                status_name = f"in {len(self.guilds)} servers"
            
            await self.change_presence(
                activity=discord.Activity(
                    type=status_type,
                    name=status_name
                ),
                status=discord.Status.online
            )
            
            # Status updates every 5 minutes
            await asyncio.sleep(300)
    
    async def on_guild_join(self, guild):
        """Event triggered when the bot joins a guild."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Try to find a system channel or default channel to send welcome message
        welcome_channel = guild.system_channel
        
        if not welcome_channel or not welcome_channel.permissions_for(guild.me).send_messages:
            for channel in guild.text_channels:
                if channel.name in ["general", "welcome", "chat", "lobby", "main"] and channel.permissions_for(guild.me).send_messages:
                    welcome_channel = channel
                    break
        
        if welcome_channel:
            embed = discord.Embed(
                title=f"👋 Hello, {guild.name}!",
                description=f"Thanks for adding {BOT_NAME} to your server! I'm your new AI-powered assistant and moderation bot.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Getting Started",
                value=f"• Use `{BOT_PREFIX}register` to register with the bot\n"
                      f"• Try `{BOT_PREFIX}chat` to talk with me\n"
                      f"• Check `{BOT_PREFIX}commands` for the full list of commands",
                inline=False
            )
            
            embed.add_field(
                name="Key Features",
                value="• AI Chat Assistance\n"
                      "• Server Moderation Tools\n"
                      "• User Management\n"
                      "• Utility Commands",
                inline=False
            )
            
            embed.set_footer(text=f"Created by {BOT_OWNER}")
            
            await welcome_channel.send(embed=embed)
    
    async def on_command_error(self, ctx, error):
        """Handle errors from commands."""
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command not found. Use `{BOT_PREFIX}commands` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}. Please check the command syntax.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument provided: {error}")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Please try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used in private messages.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I don't have permission to execute this command!")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"An error occurred: {error}")
            
    async def on_message(self, message):
        """Event triggered when a message is received."""
        # Don't respond to own messages
        if message.author == self.user:
            return
            
        # Process commands
        await self.process_commands(message)
        
        # Additional message handling
        if self.user.mentioned_in(message) and not message.mention_everyone:
            # Respond to mentions
            await message.channel.send(
                f"Hello {message.author.mention}! Use `{BOT_PREFIX}commands` to see what I can do."
            )
