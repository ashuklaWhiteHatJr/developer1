import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import webserver

DISCORD_TOKEN = os.getenv('discordkey')
FLAGGED_IDS = {1410637363457032222}
warning_channels = {}

SETUP_KEY = "MY_SECRET_KEY_123"  # <-- your required setup key

GUILD_ID = discord.Object(id=1467272661674492049)


class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} commands.')
        except Exception as e:
            print(f'Error syncing commands: {e}')

    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id

        if guild_id not in warning_channels:
            return

        if member.id not in FLAGGED_IDS:
            return

        channel = member.guild.get_channel(warning_channels[guild_id])
        if not channel:
            return

        view = WarningButtons(member)
        await channel.send(
            f"⚠️ **Flagged user joined:**\n"
            f"**User:** {member}\n"
            f"**ID:** {member.id}",
            view=view
        )


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = Client(command_prefix="!", intents=intents)


# -----------------------------
# BUTTONS
# -----------------------------
class WarningButtons(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.member = member

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.danger)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.member.kick(reason="Flagged user")
        await interaction.response.send_message(f"{self.member} has been kicked.")

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.member.ban(reason="Flagged user")
        await interaction.response.send_message(f"{self.member} has been banned.")


# -----------------------------
# SETUP MODAL
# -----------------------------
class SetupModal(discord.ui.Modal, title="Server Setup"):
    channel_id = discord.ui.TextInput(
        label="Warning Channel ID",
        placeholder="Enter the channel ID",
        required=True
    )

    key = discord.ui.TextInput(
        label="Setup Key",
        placeholder="Enter your authentication key",
        required=True,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.key.value != SETUP_KEY:
            return await interaction.response.send_message(
                "❌ Invalid setup key. Setup denied.",
                ephemeral=True
            )

        try:
            channel_id = int(self.channel_id.value)
            channel = interaction.guild.get_channel(channel_id)

            if channel is None:
                return await interaction.response.send_message(
                    "❌ Invalid channel ID.",
                    ephemeral=True
                )

            warning_channels[interaction.guild.id] = channel_id

            await interaction.response.send_message(
                f"✅ Setup complete! Warning channel set to {channel.mention}",
                ephemeral=True
            )

        except ValueError:
            await interaction.response.send_message(
                "❌ Channel ID must be a number.",
                ephemeral=True
            )


# -----------------------------
# /setup COMMAND
# -----------------------------
@client.tree.command(name="setup", description="Setup the bot for this server")
async def setup(interaction: discord.Interaction):
    await interaction.response.send_modal(SetupModal())


# -----------------------------
# /checkmembers COMMAND
# -----------------------------
@client.tree.command(name="checkmembers", description="Check current members against flagged list")
async def checkmembers(interaction: discord.Interaction):
    flagged = [m for m in interaction.guild.members if m.id in FLAGGED_IDS]

    if not flagged:
        return await interaction.response.send_message("No flagged members are currently in the server.")

    msg = "**Flagged members currently in the server:**\n"
    for m in flagged:
        msg += f"- {m} ({m.id})\n"

    await interaction.response.send_message(msg)

webserver.keep_alive()
client.run(DISCORD_TOKEN)