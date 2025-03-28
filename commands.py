import logging
import discord
import requests
import random
import datetime
import re
from discord.ext import commands
from database import Database
from ai_service import AIService
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(DATABASE_PATH)
        self.ai_service = AIService()
    
    async def cog_load(self):
        """Called when the cog is loaded."""
        await self.db.setup()
        
        # Check if AI service is available
        ai_available = await self.ai_service.is_available()
        if not ai_available:
            logger.warning("AI service is not available. Chat functionality will be limited.")
    
    @commands.command(
        name="register",
        description="Register yourself in the bot's database"
    )
    async def register(self, ctx, *, info: str = None):
        """Register a user in the database."""
        # Send initial response
        await ctx.send("Processing registration...")
        
        user_id = str(ctx.author.id)
        username = ctx.author.name
        display_name = ctx.author.display_name
        
        # Check if user is already registered
        if await self.db.is_user_registered(user_id):
            await ctx.send("You are already registered!")
            return
        
        # Register the user
        success = await self.db.register_user(user_id, username, display_name, info)
        
        if success:
            embed = discord.Embed(
                title="Registration Successful",
                description="You have been successfully registered in the database!",
                color=discord.Color.green()
            )
            embed.add_field(name="Username", value=username, inline=True)
            embed.add_field(name="Display Name", value=display_name, inline=True)
            if info:
                embed.add_field(name="Additional Info", value=info, inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("There was an error during registration. Please try again later.")
    
    @commands.command(
        name="information",
        description="Display a list of all registered users"
    )
    async def information(self, ctx):
        """Display information about registered users."""
        await ctx.send("Retrieving user information...")
        
        users = await self.db.get_all_users()
        
        if not users:
            await ctx.send("No users are registered yet.")
            return
        
        embed = discord.Embed(
            title="Registered Users",
            description=f"Total registered users: {len(users)}",
            color=discord.Color.blue()
        )
        
        # Add first 25 users to the embed (Discord has a limit)
        for i, user in enumerate(users[:25]):
            reg_date = user['registration_date'].split('T')[0] if user['registration_date'] else "Unknown"
            value = f"ID: {user['user_id']}\nRegistered: {reg_date}"
            if user['additional_info']:
                value += f"\nInfo: {user['additional_info']}"
            
            embed.add_field(
                name=f"{i+1}. {user['display_name'] or user['username']}",
                value=value,
                inline=False
            )
        
        if len(users) > 25:
            embed.set_footer(text=f"Showing 25 out of {len(users)} users")
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="chat",
        description="Start a conversation with the AI"
    )
    async def chat(self, ctx, *, message: str):
        """Chat with the AI."""
        await ctx.send("Thinking about your request...")
        
        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        # Generate AI response
        response = await self.ai_service.generate_response(message, ctx.author.id)
        
        # Store the interaction in the database
        await self.db.store_chat_interaction(ctx.author.id, message, response)
        
        # Create embed response
        embed = discord.Embed(
            title="AI Response",
            description=response,
            color=discord.Color.purple()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.add_field(name="Your message", value=message, inline=False)
        
        await ctx.send(embed=embed)

    # Command to ask AI about a specific message
    @commands.command(name="ask_ai")
    async def ask_ai_context(self, ctx, message_id: str):
        """Ask AI about a specific message by providing message ID."""
        await ctx.send("Processing your request...")
        
        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        try:
            # Try to fetch the message by ID
            message = await ctx.channel.fetch_message(int(message_id))
            content = message.content
            
            if not content:
                await ctx.send("The specified message has no text content to analyze.")
                return
                
            prompt = f"Respond to this message: {content}"
            
            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)
            
            # Store the interaction in the database
            await self.db.store_chat_interaction(ctx.author.id, prompt, response)
            
            # Create embed response
            embed = discord.Embed(
                title="AI Response",
                description=response,
                color=discord.Color.purple()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            embed.add_field(name="Original message", value=content, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error processing message: {str(e)}")
    
    @commands.command(name="news")
    async def news(self, ctx):
        """Provides information about an important event in the world today."""
        await ctx.send("Fetching today's news...")
        
        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        try:
            # Use AI to generate news about today
            prompt = f"Provide a short summary of ONE significant news event happening today (Date: {datetime.datetime.now().strftime('%B %d, %Y')}). Include only factual information. Format: Title, followed by 2-3 sentences of description. Don't mention this is AI-generated."
            
            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)
            
            # Create embed response
            embed = discord.Embed(
                title="Today's News",
                description=response,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"News as of {datetime.datetime.now().strftime('%B %d, %Y')}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in news command: {e}")
            await ctx.send("Sorry, I couldn't fetch the latest news at this time.")
    
    @commands.command(name="tdih")
    async def today_in_history(self, ctx):
        """Shows an interesting historical event that happened on this day."""
        await ctx.send("Looking up historical events for today...")
        
        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        try:
            today = datetime.datetime.now()
            
            # Use AI to generate historical events for today's date as requested
            prompt = "Tell me interesting events that happened today in history."
            
            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)
            
            # Create embed response
            embed = discord.Embed(
                title=f"This Day in History: {today.strftime('%B %d')}",
                description=response,
                color=discord.Color.gold()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in today_in_history command: {e}")
            await ctx.send("Sorry, I couldn't find historical events for today.")
    
    @commands.command(name="calc")
    async def calculate(self, ctx, *, expression: str):
        """Calculates the given mathematical expression."""
        try:
            # Strip any code block formatting if present
            expression = expression.strip('`')
            
            # Simple sanitization to prevent code execution
            # Only allow: digits, operators +,-,*,/,^,%, parentheses, and decimal points
            if not re.match(r'^[\d\+\-\*\/\^\%\(\)\.\s]+$', expression):
                await ctx.send("Invalid expression. Only basic mathematical operations are allowed.")
                return
            
            # Replace ^ with ** for exponentiation
            expression = expression.replace('^', '**')
            
            # Safe evaluation of the expression
            result = eval(expression)
            
            embed = discord.Embed(
                title="Calculator",
                description=f"Expression: `{expression}`\nResult: `{result}`",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Error calculating result: {str(e)}")
    
    @commands.command(name="weather")
    async def weather(self, ctx, *, city: str):
        """Shows the weather for the given city."""
        await ctx.send(f"Fetching weather for {city}...")
        
        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        try:
            # Use AI to generate weather information for the city
            prompt = f"What is the current weather in {city}? Provide temperature, conditions, and humidity. If you don't have real-time data, inform the user politely that you don't have access to real-time weather data."
            
            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)
            
            # Create embed response
            embed = discord.Embed(
                title=f"Weather in {city}",
                description=response,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Weather information provided by AI service")
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in weather command: {e}")
            await ctx.send("Sorry, I couldn't retrieve weather information at this time.")
    
    @commands.command(name="info")
    async def info(self, ctx):
        """Alias for the information command - displays a list of registered users."""
        await self.information(ctx)
    
    @commands.command(name="commands")
    async def help_command(self, ctx):
        """Shows all commands and their descriptions."""
        embed = discord.Embed(
            title="JoeA Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )
        
        # General commands embed
        general_embed = discord.Embed(
            title="General Commands",
            description="Commands everyone can use:",
            color=discord.Color.green()
        )
        
        general_commands = [
            ("!register [info]", "Registers you in the bot's database with optional info"),
            ("!news", "Provides information about an important world event today"),
            ("!tdih", "Today in history: Shows a historical event that happened on this day"),
            ("!calc [expression]", "Calculates the given mathematical expression"),
            ("!weather [city]", "Shows the weather for the specified city"),
            ("!info", "Displays the list of registered users"),
            ("!chat [message]", "Chat with the AI"),
            ("!help", "Shows this help message"),
            ("!translate [language] [text]", "Translates the text to the specified language"),
            ("!profile", "Displays your profile information"),
            ("!fact", "Shows an interesting random fact"),
            ("!serverinfo", "Displays detailed information about the server")
        ]
        
        for cmd, desc in general_commands:
            general_embed.add_field(name=cmd, value=desc, inline=False)
        
        # Moderation commands embed
        mod_embed = discord.Embed(
            title="Moderation Commands",
            description="Admin-only commands:",
            color=discord.Color.red()
        )
        
        mod_commands = [
            ("!ban [user_id] [reason]", "Bans the user from the server (requires ban permission)"),
            ("!unban [user_id]", "Removes the ban on the user (requires ban permission)"),
            ("!kick [user] [reason]", "Kicks the user from the server (requires kick permission)"),
            ("!slowmode [seconds]", "Sets slowmode delay for the channel (requires manage channels)"),
            ("!rerole [user] [role]", "Removes a specific role from the user (requires manage roles)"),
            ("!role [user] [role]", "Adds or removes a role from the specified user (requires manage roles)"),
            ("!clear [number]", "Deletes the specified number of recent messages (requires manage messages)")
        ]
        
        for cmd, desc in mod_commands:
            mod_embed.add_field(name=cmd, value=desc, inline=False)
        
        # Send both embeds
        await ctx.send(embed=general_embed)
        await ctx.send(embed=mod_embed)
    
    @commands.command(name="translate")
    async def translate(self, ctx, language: str, *, text: str):
        """Translates the given text to the specified language."""
        await ctx.send(f"Translating to {language}...")
        
        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        try:
            # Use AI to translate the text
            prompt = f"Translate the following text to {language}. Only respond with the translation, nothing else:\n\n{text}"
            
            # Generate AI response (translation)
            response = await self.ai_service.generate_response(prompt, ctx.author.id)
            
            # Create embed response
            embed = discord.Embed(
                title=f"Translation to {language}",
                color=discord.Color.green()
            )
            embed.add_field(name="Original Text", value=text, inline=False)
            embed.add_field(name="Translation", value=response, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in translate command: {e}")
            await ctx.send("Sorry, I couldn't translate the text at this time.")
    
    @commands.command(name="profile")
    async def profile(self, ctx):
        """Displays the user's profile information."""
        user_id = str(ctx.author.id)
        
        # Check if user is registered
        if not await self.db.is_user_registered(user_id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        try:
            # Get user data from database
            users = await self.db.get_all_users()
            user_data = None
            
            for user in users:
                if user['user_id'] == user_id:
                    user_data = user
                    break
            
            if not user_data:
                await ctx.send("Could not find your profile data.")
                return
            
            # Create embed for profile
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s Profile",
                color=discord.Color.purple()
            )
            
            reg_date = user_data['registration_date'].split('T')[0] if user_data['registration_date'] else "Unknown"
            
            embed.add_field(name="Username", value=user_data['username'], inline=True)
            embed.add_field(name="Display Name", value=user_data['display_name'], inline=True)
            embed.add_field(name="Registered On", value=reg_date, inline=True)
            
            if user_data['additional_info']:
                embed.add_field(name="Additional Info", value=user_data['additional_info'], inline=False)
            
            # Set user avatar as thumbnail if available
            if ctx.author.avatar:
                embed.set_thumbnail(url=ctx.author.avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            await ctx.send("Sorry, I couldn't retrieve your profile at this time.")
    
    @commands.command(name="role")
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, member: discord.Member, *, role_name: str):
        """Adds or removes a role from the specified user (admin only)."""
        try:
            # Find the role by name
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            
            if not role:
                await ctx.send(f"Role '{role_name}' not found.")
                return
            
            # Check if user already has the role
            if role in member.roles:
                # Remove role
                await member.remove_roles(role)
                await ctx.send(f"Removed role '{role_name}' from {member.display_name}.")
            else:
                # Add role
                await member.add_roles(role)
                await ctx.send(f"Added role '{role_name}' to {member.display_name}.")
                
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except Exception as e:
            logger.error(f"Error in role command: {e}")
            await ctx.send(f"An error occurred: {str(e)}")
    
    @commands.command(name="fact")
    async def fact(self, ctx):
        """Shows an interesting random fact."""
        await ctx.send("Generating an interesting fact...")
        
        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return
        
        try:
            # Use AI to generate a random fact
            prompt = "Share one interesting and unusual fact about anything (science, history, animals, etc.). Keep it brief (1-3 sentences) and make sure it's accurate. Don't include any introduction or conclusion text."
            
            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)
            
            # Create embed response
            embed = discord.Embed(
                title="Random Fact",
                description=response,
                color=discord.Color.gold()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in fact command: {e}")
            await ctx.send("Sorry, I couldn't generate a fact at this time.")
    
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Deletes the specified number of recent messages (admin only)."""
        if amount <= 0:
            await ctx.send("Please provide a positive number of messages to delete.")
            return
            
        if amount > 100:
            await ctx.send("You can only delete up to 100 messages at once.")
            return
            
        try:
            # Delete messages
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
            
            await ctx.send(f"Deleted {len(deleted) - 1} messages.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await ctx.send(f"Error deleting messages: {str(e)}")
    
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user_id: int, *, reason=None):
        """Bans the user from the server."""
        try:
            # Fetch user by ID
            user = await self.bot.fetch_user(user_id)
            if user:
                await ctx.guild.ban(user, reason=reason)
                ban_message = f"User {user.name}#{user.discriminator} (ID: {user_id}) has been banned."
                if reason:
                    ban_message += f" Reason: {reason}"
                await ctx.send(ban_message)
            else:
                await ctx.send(f"Could not find user with ID {user_id}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban members.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while banning the user: {str(e)}")
    
    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Removes the ban on the user."""
        try:
            # Fetch user by ID
            user = await self.bot.fetch_user(user_id)
            if user:
                await ctx.guild.unban(user)
                await ctx.send(f"User {user.name}#{user.discriminator} (ID: {user_id}) has been unbanned.")
            else:
                await ctx.send(f"Could not find user with ID {user_id}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban members.")
        except discord.NotFound:
            await ctx.send(f"User with ID {user_id} is not banned.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while unbanning the user: {str(e)}")
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        """Kicks the user from the server."""
        try:
            await user.kick(reason=reason)
            kick_message = f"User {user.name}#{user.discriminator} has been kicked."
            if reason:
                kick_message += f" Reason: {reason}"
            await ctx.send(kick_message)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick members.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while kicking the user: {str(e)}")
    
    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Sets how many seconds users must wait before sending another message."""
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode delay must be between 0 and 21600 seconds (6 hours).")
            return
            
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await ctx.send("Slowmode has been disabled for this channel.")
            else:
                await ctx.send(f"Slowmode set to {seconds} seconds for this channel.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to modify this channel.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while setting slowmode: {str(e)}")
    
    @commands.command(name="rerole")
    @commands.has_permissions(manage_roles=True)
    async def rerole(self, ctx, user: discord.Member, *, role_name: str):
        """Removes a specific role from the user."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"Role '{role_name}' not found in this server.")
            return
            
        try:
            if role in user.roles:
                await user.remove_roles(role)
                await ctx.send(f"Removed role '{role_name}' from {user.name}#{user.discriminator}.")
            else:
                await ctx.send(f"{user.name}#{user.discriminator} doesn't have the role '{role_name}'.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while removing the role: {str(e)}")
    
    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        """Displays server information including name, ID, owner, creation date, members, roles, and bot website."""
        guild = ctx.guild
        
        # Format creation time
        created_at = guild.created_at.strftime("%B %d, %Y")
        
        # Get owner
        owner = guild.owner
        
        # Create embed with server info
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            color=discord.Color.blue()
        )
        
        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add fields with server details
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=f"{owner.name}#{owner.discriminator}" if owner else "Unknown", inline=True)
        embed.add_field(name="Created On", value=created_at, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        
        # Add bot website link
        embed.add_field(name="Bot Website", value="[Visit JoeA Website](https://joea-bot.replit.app)", inline=False)
        
        # Set footer with timestamp
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    # Error handlers for missing permissions
    @role.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to use this command.")
    
    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need manage messages permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the number of messages to delete.")
    
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need ban members permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the user ID to ban.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid user ID (numbers only).")
    
    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need ban members permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the user ID to unban.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid user ID (numbers only).")
    
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need kick members permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the user to kick.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Please mention a user or provide a valid user ID.")
    
    @slowmode.error
    async def slowmode_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need manage channels permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the slowmode delay in seconds.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid number of seconds.")
    
    @rerole.error
    async def rerole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need manage roles permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            if "user" in str(error):
                await ctx.send("Please specify the user to remove a role from.")
            else:
                await ctx.send("Please specify the role name to remove.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Please mention a user or provide a valid user ID.")
