import discord
from discord.ext import commands
import os
import json
from flask import Flask
from threading import Thread

# ===== KEEP ALIVE FOR FREE RENDER =====
app = Flask('')
@app.route('/')
def home():
    return "NEXUS-BUILD is online!"
def run_web():
    app.run(host='0.0.0.0', port=8080)
Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== PREMIUM LOCK SYSTEM - PER USER =====
OWNER_ID = 1545810202232885258

try:
    with open("premium.json", "r") as f:
        PREMIUM_USERS = json.load(f)
except:
    PREMIUM_USERS = []

try:
    with open("locked.json", "r") as f:
        LOCKED_MODE = json.load(f)
except:
    LOCKED_MODE = {"global_lock": True}

def save_premium():
    with open("premium.json", "w") as f:
        json.dump(PREMIUM_USERS, f, indent=2)
    with open("locked.json", "w") as f:
        json.dump(LOCKED_MODE, f, indent=2)

def is_owner(ctx):
    return ctx.author.id == OWNER_ID

def is_premium_user(user_id):
    return str(user_id) in PREMIUM_USERS or user_id in PREMIUM_USERS

@bot.check
async def premium_check(ctx):
    if ctx.author.id == OWNER_ID:
        return True
    if not LOCKED_MODE.get("global_lock", False):
        return True
    if is_premium_user(ctx.author.id):
        return True
    await ctx.send(f"🔒 **This bot is Premium / Locked.**\n{ctx.author.mention} you are not unlocked.\nDM the owner to get access.\n\nType `!premium` to check your status.")
    return False

# ===== TEMPLATES =====
TEMPLATES = {
    "gaming": {
        "📢 INFO": ["welcome", "rules", "announcements"],
        "💬 CHAT": ["general", "gaming-chat", "memes", "clips"],
        "🎮 GAME ZONES": ["valorant", "fortnite", "minecraft"],
        "🔊 VOICE": ["lobby", "gaming-1", "gaming-2", "music"],
        "🛡️ STAFF": ["staff-chat", "mod-logs"],
    },
    "community": {
        "📢 INFO": ["welcome", "rules", "announcements"],
        "💬 CHAT": ["general", "introductions", "off-topic", "photos"],
        "🔊 VOICE": ["lounge", "chill-zone"],
        "🛡️ STAFF": ["staff-chat"],
    },
    "school": {
        "📢 INFO": ["welcome", "rules", "announcements"],
        "📚 STUDY": ["general-study", "homework-help", "resources"],
        "💬 CHAT": ["general", "memes"],
        "🔊 VOICE": ["study-room-1", "study-room-2"],
        "🛡️ STAFF": ["teachers-only"],
    },
    "esports": {
        "📢 INFO": ["welcome", "rules", "announcements", "tryouts"],
        "🏆 TEAM": ["team-chat", "strategies", "scrim-results"],
        "💬 CHAT": ["general", "fan-chat"],
        "🔊 VOICE": ["team-voice", "scrim-voice"],
        "🛡️ STAFF": ["coach-only", "management"],
    }
}

ROLES_PRESET = [
    ("👑 Owner", 0xe74c3c),
    ("🛡️ Admin", 0x9b59b6),
    ("🔨 Moderator", 0x3498db),
    ("⭐ VIP", 0xf1c40f),
    ("🎮 Gamer", 0x2ecc71),
    ("👤 Member", 0x95a5a6),
    ("🤖 Bots", 0x34495e),
]

WELCOME_TEXT = "👋 **Welcome to {server}!**\n\n✅ Read #rules\n💬 Chat in #general\nHave fun!"
RULES_TEXT = "📜 **SERVER RULES**\n\n1. Be respectful - no hate, no spam\n2. No NSFW in public channels\n3. No advertising without permission\n4. Listen to Staff\n5. Have fun!"

try:
    with open("welcome.json", "r") as f:
        WELCOME_CONFIG = json.load(f)
except:
    WELCOME_CONFIG = {}

def save_welcome():
    with open("welcome.json", "w") as f:
        json.dump(WELCOME_CONFIG, f, indent=2)

async def build_server(guild, template_name):
    template = TEMPLATES.get(template_name.lower(), TEMPLATES["gaming"])
    for role_name, color_int in ROLES_PRESET:
        if not discord.utils.get(guild.roles, name=role_name):
            await guild.create_role(name=role_name, color=discord.Color(color_int), reason="NEXUS SETUP")
    admin_role = discord.utils.get(guild.roles, name="🛡️ Admin")
    owner_role = discord.utils.get(guild.roles, name="👑 Owner")
    overwrites_staff = {}
    if admin_role:
        overwrites_staff = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            admin_role: discord.PermissionOverwrite(view_channel=True),
        }
        if owner_role:
            overwrites_staff[owner_role] = discord.PermissionOverwrite(view_channel=True)
    for cat_name, channels in template.items():
        category = discord.utils.get(guild.categories, name=cat_name)
        if not category:
            if "STAFF" in cat_name or "🛡️" in cat_name:
                category = await guild.create_category(cat_name, overwrites=overwrites_staff)
            else:
                category = await guild.create_category(cat_name)
        for ch_name in channels:
            if discord.utils.get(guild.channels, name=ch_name):
                continue
            if cat_name.startswith("🔊"):
                await guild.create_voice_channel(ch_name, category=category)
            else:
                await guild.create_text_channel(ch_name, category=category)
    welcome_ch = discord.utils.get(guild.text_channels, name="welcome")
    if welcome_ch:
        try: await welcome_ch.send(WELCOME_TEXT.format(server=guild.name))
        except: pass
    rules_ch = discord.utils.get(guild.text_channels, name="rules")
    if rules_ch:
        try: await rules_ch.send(RULES_TEXT)
        except: pass

class SetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for name in TEMPLATES.keys():
            self.add_item(SetupButton(name))

class SetupButton(discord.ui.Button):
    def __init__(self, template_name):
        super().__init__(label=template_name.capitalize(), style=discord.ButtonStyle.primary, custom_id=template_name)
        self.template_name = template_name
    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need Administrator to build the server.", ephemeral=True)
            return
        await interaction.response.send_message(f"🔨 Building **{self.template_name}** server...", ephemeral=True)
        await build_server(interaction.guild, self.template_name)
        await interaction.followup.send(f"✅ **{self.template_name}** server built! Check your categories.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"{bot.user} is online - SETUP BOT READY")

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    config = WELCOME_CONFIG.get(guild_id)
    if not config:
        return
    channel_name = config.get("channel", "welcome")
    message = config.get("message", "Welcome {user} to {server}! 🎉")
    final_msg = message.replace("{user}", member.mention).replace("{name}", member.name).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
    channel = discord.utils.get(member.guild.text_channels, name=channel_name)
    if channel:
        try: await channel.send(final_msg)
        except: pass
    if config.get("dm", False):
        try: await member.send(final_msg)
        except: pass@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="🛠️ Build Your Server", description="Pick a template below. I will create Categories, Channels, Roles with colors, Welcome & Rules automatically.", color=0x3498db)
    embed.add_field(name="Templates", value="🎮 Gaming\n💬 Community\n📚 School\n🏆 Esports", inline=False)
    await ctx.send(embed=embed, view=SetupView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_gaming(ctx):
    await ctx.send("🔨 Building Gaming server...")
    await build_server(ctx.guild, "gaming")
    await ctx.send("✅ Gaming server done!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_community(ctx):
    await ctx.send("🔨 Building Community server...")
    await build_server(ctx.guild, "community")
    await ctx.send("✅ Community server done!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_school(ctx):
    await ctx.send("🔨 Building School server...")
    await build_server(ctx.guild, "school")
    await ctx.send("✅ School server done!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_esports(ctx):
    await ctx.send("🔨 Building Esports server...")
    await build_server(ctx.guild, "esports")
    await ctx.send("✅ Esports server done!")

@bot.command()
async def template(ctx):
    msg = "**Available Templates:**\n"
    for name, data in TEMPLATES.items():
        msg += f"\n**{name.capitalize()}** - {len(data)} categories, {sum(len(v) for v in data.values())} channels"
    msg += "\n\nUse `!setup` and click a button"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def fixserver(ctx):
    await ctx.send("🔧 Checking for missing channels/roles...")
    await build_server(ctx.guild, "gaming")
    await ctx.send("✅ Server fixed! Missing stuff added back.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def addcategories(ctx, *, text: str):
    names = [n.strip() for n in text.split(",") if n.strip()]
    if not names:
        await ctx.send("❌ Usage: `!addcategories 🎮 GAMING, 💬 CHAT, 🔊 VOICE`")
        return
    created = []
    for name in names:
        if discord.utils.get(ctx.guild.categories, name=name):
            created.append(f"⏭️ Already exists: **{name}**")
            continue
        cat = await ctx.guild.create_category(name)
        created.append(f"✅ Category: **{cat.name}**")
    await ctx.send("\n".join(created))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def addchannels(ctx, *, text: str):
    if "|" not in text:
        await ctx.send("❌ Usage: `!addchannels 💬 CHAT | general, memes, clips`\nUse `|` for category, `,` for channels.")
        return
    cat_name, channels_part = text.split("|", 1)
    cat_name = cat_name.strip()
    channel_names = [c.strip() for c in channels_part.split(",") if c.strip()]
    category = discord.utils.get(ctx.guild.categories, name=cat_name)
    if not category:
        category = await ctx.guild.create_category(cat_name)
        await ctx.send(f"✅ Category created: **{cat_name}**")
    created = []
    for ch_name in channel_names:
        is_voice = False
        clean_name = ch_name
        if ch_name.endswith("🔊"):
            is_voice = True
            clean_name = ch_name.replace("🔊", "").strip()
        elif "[voice]" in ch_name.lower():
            is_voice = True
            clean_name = ch_name.lower().replace("[voice]", "").strip()
        elif "(voice)" in ch_name.lower():
            is_voice = True
            clean_name = ch_name.lower().replace("(voice)", "").strip()
        if discord.utils.get(ctx.guild.channels, name=clean_name.lower().replace(" ", "-")):
            created.append(f"⏭️ Already exists: **{clean_name}**")
            continue
        if is_voice:
            ch = await ctx.guild.create_voice_channel(clean_name, category=category)
            created.append(f"🔊 Voice: **{ch.name}**")
        else:
            ch = await ctx.guild.create_text_channel(clean_name, category=category)
            created.append(f"💬 Text: **{ch.name}**")
    await ctx.send(f"In **{category.name}**:\n" + "\n".join(created))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def addcategory(ctx, *, name: str):
    cat = await ctx.guild.create_category(name)
    await ctx.send(f"✅ Category created: {cat.name}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def addchannel(ctx, category_name: str, channel_name: str, type: str = "text"):
    cat = discord.utils.get(ctx.guild.categories, name=category_name)
    if not cat:
        await ctx.send("❌ Category not found. Use `!addcategory` first.")
        return
    if type.lower() == "voice":
        await ctx.guild.create_voice_channel(channel_name, category=cat)
    else:
        await ctx.guild.create_text_channel(channel_name, category=cat)
    await ctx.send(f"✅ Channel #{channel_name} created in {category_name}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addroles(ctx, *, text: str):
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        await ctx.send("❌ Usage: `!addroles VIP #ff00ff, MOD #3498db, 👑 OWNER #e74c3c`")
        return
    created = []
    for part in parts:
        tokens = part.rsplit(" ", 1)
        if len(tokens) == 2 and tokens[1].startswith("#"):
            role_name = tokens[0].strip()
            color_str = tokens[1].strip()
        else:
            role_name = part
            color_str = "#3498db"
        try:
            color_int = int(color_str.replace("#", ""), 16)
        except:
            color_int = 0x3498db
        existing = discord.utils.get(ctx.guild.roles, name=role_name)
        if existing:
            await existing.edit(color=discord.Color(color_int))
            created.append(f"🔄 Updated: {existing.mention} to {color_str}")
        else:
            role = await ctx.guild.create_role(name=role_name, color=discord.Color(color_int))
            created.append(f"✅ Role: {role.mention} - {color_str}")
    await ctx.send("\n".join(created))

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, role_name: str, color: str = "#3498db"):
    try:
        hex_val = int(color.replace("#", ""), 16)
    except:
        hex_val = 0x3498db
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        role = await ctx.guild.create_role(name=role_name, color=discord.Color(hex_val))
        await ctx.send(f"✅ Role created: {role.mention} with color {color}")
    else:
        await role.edit(color=discord.Color(hex_val))
        await ctx.send(f"✅ Role color updated: {role.mention} to {color}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send("❌ Role not found. Create it with `!addrole` first.")
        return
    await member.add_roles(role)
    await ctx.send(f"✅ Gave {member.mention} the role {role.mention}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role and role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"✅ Removed {role.mention} from {member.mention}")

@bot.command()
async def roles(ctx):
    msg = "**Roles:**\n"
    for r in ctx.guild.roles[::-1]:
        if r.name != "@everyone":
            msg += f"{r.mention} - `{str(r.color)}`\n"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def build(ctx, *, text: str):
    await ctx.send("🔨 Building... parsing your request...")
    chunks = [c.strip() for c in text.split("|")]
    for i in range(0, len(chunks)-1, 2):
        cat_name = chunks[i]
        channels_part = chunks[i+1]
        channel_names = [c.strip() for c in channels_part.split(",") if c.strip()]
        category = discord.utils.get(ctx.guild.categories, name=cat_name)
        if not category:
            category = await ctx.guild.create_category(cat_name)
        for ch_name in channel_names:
            is_voice = ch_name.endswith("🔊")
            clean = ch_name.replace("🔊", "").strip() if is_voice else ch_name
            if discord.utils.get(ctx.guild.channels, name=clean.lower().replace(" ", "-")):
                continue
            if is_voice:
                await ctx.guild.create_voice_channel(clean, category=category)
            else:
                await ctx.guild.create_text_channel(clean, category=category)
    await ctx.send("✅ **Done!** All categories + channels created from your message.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: str = "welcome", *, message: str = None):
    if not message:
        await ctx.send("❌ Usage: `!setwelcome welcome Welcome {user} to {server}! You are member #{count} 🎉`\n\nPlaceholders: `{user}` `{name}` `{server}` `{count}`")
        return
    guild_id = str(ctx.guild.id)
    WELCOME_CONFIG[guild_id] = {"channel": channel, "message": message, "dm": False}
    save_welcome()
    preview = message.replace('{user}', ctx.author.mention).replace('{name}', ctx.author.name).replace('{server}', ctx.guild.name).replace('{count}', str(ctx.guild.member_count))
    await ctx.send(f"✅ Welcome message set!\nChannel: **#{channel}**\nMessage: `{message}`\n\nPreview: {preview}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome_dm(ctx, *, message: str = None):
    if not message:
        await ctx.send("❌ Usage: `!setwelcome_dm Welcome {user} to {server}! Check #rules`")
        return
    guild_id = str(ctx.guild.id)
    existing = WELCOME_CONFIG.get(guild_id, {})
    existing["message"] = message
    existing["dm"] = True
    WELCOME_CONFIG[guild_id] = existing
    save_welcome()
    await ctx.send(f"✅ Welcome DM set! New members will get DM: `{message}`")

@bot.command()
async def showwelcome(ctx):
    config = WELCOME_CONFIG.get(str(ctx.guild.id))
    if not config:
        await ctx.send("❌ No custom welcome set. Use `!setwelcome welcome Your message here`")
        return
    await ctx.send(f"**Current Welcome:**\nChannel: #{config.get('channel')}\nDM: {config.get('dm')}\nMessage: `{config.get('message')}`")

@bot.command()
@commands.has_permissions(administrator=True)
async def deleteme(ctx, *, text: str = None):
    if not text:
        await ctx.send("❌ Usage:\n`!deleteme channels general, memes, clips`\n`!deleteme categories 🎮 GAMING, 💬 CHAT`\n`!deleteme roles VIP, MOD`\n`!deleteme all`")
        return
    text_lower = text.lower().strip()
    if text_lower == "all":
        await ctx.send("⚠️ **ARE YOU SURE?** This will delete ALL channels, categories and roles.\nType `!deleteme confirm` to confirm.")
        return
    if text_lower == "confirm":
        deleted = 0
        for channel in list(ctx.guild.channels):
            try:
                await channel.delete(reason="NEXUS SETUP cleanup")
                deleted += 1
            except: pass
        for role in list(ctx.guild.roles):
            if role.name != "@everyone" and not role.managed:
                try:
                    await role.delete(reason="NEXUS SETUP cleanup")
                    deleted += 1
                except: pass
        await ctx.send(f"🧹 **Cleaned!** Deleted {deleted} channels/categories/roles. Use `!setup` to rebuild.")
        return
    if text_lower.startswith("channels"):
        names_part = text[len("channels"):].strip()
        names = [n.strip() for n in names_part.split(",") if n.strip()]
        deleted = []
        for name in names:
            ch = discord.utils.get(ctx.guild.channels, name=name.lower().replace(" ", "-"))
            if not ch:
                ch = discord.utils.get(ctx.guild.channels, name=name)
            if ch:
                await ch.delete(reason="NEXUS SETUP deleteme")
                deleted.append(f"🗑️ Deleted channel: **{name}**")
            else:
                deleted.append(f"❌ Not found: **{name}**")
        await ctx.send("\n".join(deleted))
        return
    if text_lower.startswith("categories"):
        names_part = text[len("categories"):].strip()
        names = [n.strip() for n in names_part.split(",") if n.strip()]
        deleted = []
        for name in names:
            cat = discord.utils.get(ctx.guild.categories, name=name)
            if cat:
                for ch in list(cat.channels):
                    await ch.delete()
                await cat.delete()
                deleted.append(f"🗑️ Deleted category + its channels: **{name}**")
            else:
                deleted.append(f"❌ Not found: **{name}**")
        await ctx.send("\n".join(deleted))
        return
    if text_lower.startswith("roles"):
        names_part = text[len("roles"):].strip()
        names = [n.strip() for n in names_part.split(",") if n.strip()]
        deleted = []
        for name in names:
            role = discord.utils.get(ctx.guild.roles, name=name)
            if role:
                await role.delete(reason="NEXUS SETUP deleteme")
                deleted.append(f"🗑️ Deleted role: **{name}**")
            else:
                deleted.append(f"❌ Not found: **{name}**")
        await ctx.send("\n".join(deleted))
        return
    await ctx.send("❌ Use `channels`, `categories`, `roles` or `all`. Example: `!deleteme channels general, memes`")

@bot.command()
async def lock(ctx, user: discord.Member = None):
    if not is_owner(ctx):
        await ctx.send("❌ Only the owner can lock.")
        return
    if user:
        uid = str(user.id)
        if uid in PREMIUM_USERS:
            PREMIUM_USERS.remove(uid)
            save_premium()
            await ctx.send(f"🔒 Locked **{user.mention}** (`{user.id}`). He can no longer use the bot.")
        elif user.id in PREMIUM_USERS:
            PREMIUM_USERS.remove(user.id)
            save_premium()
            await ctx.send(f"🔒 Locked **{user.mention}**.")
        else:
            await ctx.send(f"⚠️ {user.mention} was already locked.")
    else:
        LOCKED_MODE["global_lock"] = True
        save_premium()
        await ctx.send("🔒 **Bot is now LOCKED globally.** Only premium users + owner can use it.")

@bot.command()
async def unlock(ctx, user: discord.Member = None):
    if not is_owner(ctx):
        await ctx.send("❌ Only the owner can unlock.")
        return
    if user:
        uid = str(user.id)
        if uid not in PREMIUM_USERS:
            PREMIUM_USERS.append(uid)
            save_premium()
        await ctx.send(f"✅ **Unlocked {user.mention}** (`{user.id}`) - He now has Premium access in ANY server!")
    else:
        LOCKED_MODE["global_lock"] = False
        save_premium()
        await ctx.send("✅ **Bot is now OPEN for everyone.** Free mode.")

@bot.command()
async def premium(ctx, user: discord.Member = None):
    target = user or ctx.author
    if not is_owner(ctx) and user:
        await ctx.send("❌ Only owner can check other users.")
        return
    if is_owner(ctx) and not user:
        if not PREMIUM_USERS:
            await ctx.send(f"📋 No premium users yet.\nGlobal Lock: {LOCKED_MODE.get('global_lock')}\nUse `!unlock @user` to add one.")
            return
        msg = f"📋 **Premium Users ({len(PREMIUM_USERS)}):**\nGlobal Lock: {LOCKED_MODE.get('global_lock')}\n"
        for uid in PREMIUM_USERS:
            msg += f"- <@{uid}> (`{uid}`)\n"
        await ctx.send(msg)
        return
    if is_premium_user(target.id):
        await ctx.send(f"✅ {target.mention} **IS Premium** - All commands unlocked in any server.")
    else:
        await ctx.send(f"🔒 {target.mention} is **NOT Premium**.\nDM the owner to unlock.")

@bot.command()
async def myid(ctx):
    await ctx.send(f"Your ID is: `{ctx.author.id}`\nUse this for OWNER_ID")

bot.run(os.environ.get("TOKEN"))
