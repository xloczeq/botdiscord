COOLDOWN = 2.5  # sekundy



# fish
@bot.tree.command(name="fish", description="Idź połowić ryby!")
async def fish(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}, 'last_fish':0, 'gold':0, 'bait':0}

    embed = discord.Embed(title="🎣 Łowienie Ryb!", description="Kliknij **Łów!** aby spróbować złowić rybę", color=discord.Color.blue())
    embed.set_footer(text=f"Masz 60 sekund na kliknięcie przycisku. Cooldown: {COOLDOWN}s")
    view = FishView(user_id)
    await interaction.response.send_message(embed=embed, view=view)

# profile
@bot.tree.command(name="profile", description="Pokazuje Twój profil w grze łowienia ryb")
async def profile(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in players:
        await interaction.response.send_message("Nie złowiłeś jeszcze żadnej ryby!", ephemeral=True)
        return
    player = players[user_id]
    embed = discord.Embed(title=f"🎣 Profil {interaction.user.display_name}", color=discord.Color.orange())
    embed.add_field(name="Poziom", value=f"{player['level']}", inline=True)
    embed.add_field(name="XP", value=f"{player['xp']}/{player['level']*100} {xp_bar(player)}", inline=True)
    fish_list = "\n".join([f"{fishes[f]['emoji']} {f}: {c}" for f,c in player['fish'].items()])
    embed.add_field(name="Twoje ryby", value=fish_list if fish_list else "Brak", inline=False)
    embed.add_field(name="Gold", value=f"{player['gold']}", inline=True)
    embed.add_field(name="Przynęty", value=f"{player['bait']}", inline=True)
    await interaction.response.send_message(embed=embed)

# shop
@bot.tree.command(name="shop", description="Otwórz sklep z przedmiotami")
async def shop(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}, 'last_fish':0, 'gold':0, 'bait':0}
    player = players[user_id]

    embed = discord.Embed(title="🏪 Sklep", color=discord.Color.gold())
    embed.add_field(name="Waluta", value=f"{player['gold']} złota", inline=False)
    for item, info in shop_items.items():
        embed.add_field(name=f"{item} - {info['price']} zł", value=info['desc'], inline=False)
    await interaction.response.send_message(embed=embed)

# buy
@bot.tree.command(name="buy", description="Kup przedmiot w sklepie")
@app_commands.describe(item="Co chcesz kupić?", amount="Ile sztuk?")
async def buy(interaction: discord.Interaction, item: str, amount: int = 1):
    user_id = interaction.user.id
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}, 'last_fish':0, 'gold':0, 'bait':0}
    player = players[user_id]

    if item not in shop_items:
        await interaction.response.send_message("Nie ma takiego przedmiotu w sklepie!", ephemeral=True)
        return

    total_price = shop_items[item]['price'] * amount
    if player['gold'] < total_price:
        await interaction.response.send_message("Nie masz wystarczająco złota!", ephemeral=True)
        return

    player['gold'] -= total_price
    if item == "przynęta":
        player['bait'] += amount

    await interaction.response.send_message(f"✅ Kupiłeś {amount}x {item}!")

# sell
@bot.tree.command(name="sell", description="Sprzedaj swoje ryby za złoto")
@app_commands.describe(fish_name="Jaką rybę chcesz sprzedać?", amount="Ile sztuk sprzedać?")
async def sell(interaction: discord.Interaction, fish_name: str, amount: int):
    user_id = interaction.user.id
    if user_id not in players:
        await interaction.response.send_message("Nie masz jeszcze żadnych ryb!", ephemeral=True)
        return
    player = players[user_id]

    if fish_name not in player['fish'] or player['fish'][fish_name] < amount:
        await interaction.response.send_message(f"Nie masz tylu ryb: {fish_name}", ephemeral=True)
        return

    player['fish'][fish_name] -= amount
    if player['fish'][fish_name] == 0:
        del player['fish'][fish_name]

    gold_earned = fishes.get(fish_name, {}).get("price", 0) * amount
    player['gold'] += gold_earned

    await interaction.response.send_message(f"💰 Sprzedałeś {amount}x {fish_name} i otrzymałeś {gold_earned} złota!")




    # ----------------- Button do łowienia -----------------
class FishView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @ui.button(label="🎣 Łów!", style=ButtonStyle.green)
    async def fish_button(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        now = time.time()

        if user_id != self.user_id:
            await interaction.response.send_message("To nie Twój fishing!", ephemeral=True)
            return

        # cooldown
        last = players.get(user_id, {}).get('last_fish', 0)
        if now - last < COOLDOWN:
            await interaction.response.send_message(f"⏱ Poczekaj {int(COOLDOWN - (now - last))}s przed kolejnym łowieniem.", ephemeral=True)
            return
        players[user_id]['last_fish'] = now

        # losowanie ryby z wagami, bonus od przynęty
        weights = [50,30,15,4,1]
        player = players[user_id]
        if player['bait'] > 0:
            bonus = [0,0,0,0,0]
            for i in range(1,len(weights)):
                bonus[i] = int(weights[i]*0.1*player['bait'])
                weights[i] += bonus[i]
            player['bait'] -= 1

        fish_name = random.choices(list(fishes.keys()), weights=weights)[0]
        fish_info = fishes[fish_name]
        xp_gained = add_xp(user_id, fish_info['xp'])

        # dodanie ryby
        player['fish'][fish_name] = player['fish'].get(fish_name, 0) + 1

        embed = discord.Embed(title="🎣 Łowienie Ryb!", color=discord.Color.green())
        embed.add_field(name="Złowiono:", value=f"{fish_info['emoji']} {fish_name} (+{xp_gained} XP)", inline=False)
        embed.add_field(name="Poziom", value=f"{player['level']}", inline=True)
        embed.add_field(name="XP", value=f"{player['xp']}/{player['level']*100} {xp_bar(player)}", inline=True)
        fish_list = "\n".join([f"{fishes[f]['emoji']} {f}: {c}" for f,c in player['fish'].items()])
        embed.add_field(name="Twoje ryby", value=fish_list if fish_list else "Brak", inline=False)
        embed.add_field(name="Gold", value=f"{player['gold']}", inline=True)
        embed.add_field(name="Przynęty", value=f"{player['bait']}", inline=True)
        embed.set_footer(text=f"Cooldown: {COOLDOWN}s")

        await interaction.response.edit_message(embed=embed, view=self)




# ----------------- Funkcje -----------------
def add_xp(user_id, xp):
    """Dodaje XP i sprawdza level"""
    if user_id not in players:
        players[user_id] = {'xp':0, 'level':1, 'fish':{}, 'last_fish':0, 'gold':0, 'bait':0}
    # XP mnożnik zależny od poziomu
    xp = int(xp * (1 + (players[user_id]['level'] - 1)*0.1))
    players[user_id]['xp'] += xp
    while players[user_id]['xp'] >= players[user_id]['level'] * 100:
        players[user_id]['xp'] -= players[user_id]['level'] * 100
        players[user_id]['level'] += 1
    return xp

def xp_bar(player):
    total = player['level']*100
    current = player['xp']
    filled = int((current/total)*20)
    return "🟩"*filled + "⬜"*(20-filled)




# ----------------- Baza graczy -----------------
# player_id: {'xp': int, 'level': int, 'fish': {name: count}, 'last_fish': timestamp, 'gold': int, 'bait': int}
players = {}

# ryby, XP, emotki i gold za sprzedaż
fishes = {
    "Karp": {"xp": 5, "emoji": "🐟", "price": 5},
    "Pstrąg": {"xp": 10, "emoji": "🐠", "price": 10},
    "Łosoś": {"xp": 15, "emoji": "🐡", "price": 20},
    "Rekin": {"xp": 50, "emoji": "🦈", "price": 100},
    "Legenda": {"xp": 100, "emoji": "🐋", "price": 500}
}

# sklep
shop_items = {
    "przynęta": {"price": 50, "desc": "Zwiększa szansę na złapanie rzadszych ryb o 10%"}
}

