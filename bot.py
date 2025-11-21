import discord
import os
import asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- Komendy -----------------
@bot.event
async def on_ready():
    print(f"✔️ Zalogowano jako: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print("Błąd synchronizacji:", e)

# godzina
@bot.tree.command(name="godzina", description="Pokazuje aktualną godzinę w Polsce")
async def godzina(interaction: discord.Interaction):
    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    await interaction.response.send_message(f"⏰ Jest godzina {now.hour:02d}:{now.minute:02d}")

# clear
@bot.tree.command(name="clear", description="Czyści wiadomości w kanale")
@app_commands.describe(ilosc="Ile wiadomości usunąć? (max 100)")
async def clear(interaction: discord.Interaction, ilosc: int):
    if ilosc < 1 or ilosc > 100:
        await interaction.response.send_message("❌ Podaj liczbę od 1 do 100.", ephemeral=True)
        return
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Nie masz uprawnień!", ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
        await interaction.response.send_message("❌ Nie mogę usuwać wiadomości!", ephemeral=True)
        return
    await interaction.response.send_message(f"🧹 Usuwam {ilosc} wiadomości...", ephemeral=True)
    deleted = await interaction.channel.purge(limit=ilosc)
    msg = await interaction.channel.send(f"🧹 Usunięto {len(deleted)} wiadomości.")
    await asyncio.sleep(5)
    await msg.delete()

# komendy
@bot.tree.command(name="komendy", description="Lista komend bota")
async def komendy(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 Lista Komend Bota", color=discord.Color.blurple())
    embed.add_field(name="/godzina", value="Pokazuje godzinę.", inline=False)
    embed.add_field(name="/clear <ilość>", value="Czyści wiadomości.", inline=False)
    await interaction.response.send_message(embed=embed)

# ---------------- GIVEAWAY SYSTEM -----------------

class GiveawayView(discord.ui.View):
    def __init__(self, host, prize, end_time):
        super().__init__(timeout=None)
        self.host = host
        self.prize = prize
        self.end_time = end_time
        self.participants = set()

    @discord.ui.button(label="🎉 Dołącz", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("Już bierzesz udział!", ephemeral=True)
            return

        self.participants.add(interaction.user.id)
        await interaction.response.send_message("Dołączono do giveaway 🎉", ephemeral=True)

    @discord.ui.button(label="❌ Wypisz się", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.participants:
            await interaction.response.send_message("Nie jesteś zapisany!", ephemeral=True)
            return

        self.participants.remove(interaction.user.id)
        await interaction.response.send_message("Wypisano z giveaway ❌", ephemeral=True)


def parse_time(time_str: str):
    try:
        unit = time_str[-1]
        value = int(time_str[:-1])

        if unit == "s": return value
        if unit == "m": return value * 60
        if unit == "h": return value * 3600
        if unit == "d": return value * 86400
        return None
    except:
        return None


@bot.tree.command(name="giveaway", description="Tworzy giveaway z przyciskami.")
@app_commands.describe(time="Czas trwania (np. 10s, 5m, 2h, 1d)", prize="Nagroda giveaway")
async def giveaway(interaction: discord.Interaction, time: str, prize: str):
    seconds = parse_time(time)
    if seconds is None:
        await interaction.response.send_message(
            "❌ Niepoprawny format czasu! Użyj: 10s / 5m / 2h / 1d",
            ephemeral=True
        )
        return

    end_time = datetime.now() + timedelta(seconds=seconds)

    view = GiveawayView(interaction.user, prize, end_time)

    embed = discord.Embed(
        title="🎉 GIVEAWAY!",
        description=f"🎁 **Nagroda:** {prize}\n"
                    f"⏳ **Koniec za:** {time}\n"
                    f"👤 Host: {interaction.user.mention}",
        color=discord.Color.gold()
    )
    embed.set_footer(text="Kliknij przyciski niżej, by dołączyć!")

    await interaction.response.send_message("Giveaway utworzony!", ephemeral=True)
    msg = await interaction.channel.send(embed=embed, view=view)

    # Timer do zakończenia
    await asyncio.sleep(seconds)

    # Losowanie
    if len(view.participants) == 0:
        await interaction.channel.send("❌ Nikt nie wziął udziału w giveaway 😭")
        return

    winner_id = random.choice(list(view.participants))
    winner = interaction.guild.get_member(winner_id)

    result_embed = discord.Embed(
        title="🏆 GIVEAWAY ZAKOŃCZONY!",
        description=f"🎁 **Nagroda:** {prize}\n"
                    f"🏆 **Zwycięzca:** {winner.mention if winner else 'Nie znaleziono'}",
        color=discord.Color.green()
    )

    await interaction.channel.send(embed=result_embed)

# ---------------- Uruchomienie -----------------
bot.run(TOKEN)
