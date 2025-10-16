import nextcord
from nextcord.ext import commands
import asyncio
from asyncio_throttle.throttler import Throttler
import os  

# =========================================
# 設定
# =========================================
BOT_TOKEN = os.getenv('DISCORD_TOKEN')

if not BOT_TOKEN:  # ← これを追加
    print("エラー: DISCORD_TOKENが設定されていません")
    exit(1)

# =========================================
# ボタンクラス（実行中は連打不可・通知なし）
# =========================================
class SafeExecuteButton(nextcord.ui.View):
    def __init__(self, message_content: str = None, embed: nextcord.Embed = None, times: int = 5, allowed_mentions=None):
        super().__init__(timeout=None)
        self.message_content = message_content
        self.embed = embed
        self.times = times
        self.allowed_mentions = allowed_mentions
        self.executing_users = set()  # 実行中のユーザーIDを記録
    
    @nextcord.ui.button(label="実行", style=nextcord.ButtonStyle.primary, emoji="▶️")
    async def execute_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        user_id = interaction.user.id
        
        # 既に実行中の場合は何もせず無視
        if user_id in self.executing_users:
            await interaction.response.defer()
            return
        
        # 実行中リストに追加
        self.executing_users.add(user_id)
        await interaction.response.defer()
        
        try:
            # 安全にまとめて送信
            async with bot.throttler:
                for _ in range(self.times):
                    try:
                        if self.embed:
                            await interaction.followup.send(
                                content=self.message_content, 
                                embed=self.embed,
                                allowed_mentions=self.allowed_mentions
                            )
                        else:
                            await interaction.followup.send(
                                self.message_content,
                                allowed_mentions=self.allowed_mentions
                            )
                        await asyncio.sleep(0.4)
                    except Exception:
                        pass
        finally:
            # 実行中リストから削除（通知なし）
            self.executing_users.discard(user_id)

# =========================================
# 文字を大きくする関数
# =========================================
def text_to_big(text: str) -> str:
    """文字を # *** で囲んで大きく見せる（5回分）"""
    lines = []
    for char in text:
        lines.append(f"**# {char}**")
    one_big_text = "\n".join(lines)
    return "\n".join([one_big_text] * 5)

# =========================================
# Bot 定義
# =========================================
class MyBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        super().__init__(command_prefix="!", intents=intents)
        self.throttler = Throttler(rate_limit=5, period=1)
    
    async def on_ready(self):
        print(f"Bot起動完了: {self.user}")
        print(f"招待されているサーバー数: {len(self.guilds)}")
        try:
            synced = await self.sync_application_commands()
            print(f"スラッシュコマンドを同期しました: {len(synced)} コマンド")
        except Exception as e:
            print(f"スラッシュコマンド同期エラー: {e}")
        await self.change_presence(activity=nextcord.Game(name="!"))
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        await self.process_commands(message)

bot = MyBot()

# =========================================
# /send コマンド
# =========================================
@bot.slash_command(name="send", description="メッセージを送信します", guild_ids=None)
async def slash_send_message(interaction: nextcord.Interaction, message: str):
    view = SafeExecuteButton(message, times=5)
    await interaction.response.send_message(
        f"送信予定のメッセージ:\n```{message}```\n\n**実行ボタンで開始してください。**",
        view=view,
        ephemeral=True
    )

# =========================================
# /bigtext コマンド
# =========================================
@bot.slash_command(name="bigtext", description="文字を大きくして送信します", guild_ids=None)
async def slash_bigtext(interaction: nextcord.Interaction, text: str):
    big_text = text_to_big(text)
    view = SafeExecuteButton(big_text, times=5)
    await interaction.response.send_message(
        f"送信予定の大きい文字:\n{big_text[:500]}{'...' if len(big_text) > 500 else ''}\n\n**実行ボタンで開始してください。**",
        view=view,
        ephemeral=True
    )

# =========================================
# /ping_all_gif コマンド
# =========================================
@bot.slash_command(name="ping_all_gif", description="全員メンション＋GIF送信", guild_ids=None)
async def slash_ping_all_gif(interaction: nextcord.Interaction):
    message_content = (
        "@everyone\n"
        "https://discord.gg/FbyBc7Pwyn\n"
        "https://cdn.discordapp.com/attachments/1396755606374842479/1422236835001929758/Vexel.gif\n"
        "https://cdn.discordapp.com/attachments/1396755606374842479/1422238265762779228/Vexel.gif"
    )
    allowed = nextcord.AllowedMentions(everyone=True, users=True, roles=True)
    view = SafeExecuteButton(message_content, times=5, allowed_mentions=allowed)
    await interaction.response.send_message(
        "全員メンション＆GIF送信予定\n**ボタンは何回でも押せます。**",
        view=view,
        ephemeral=True
    )


# =========================================
# /invites コマンド
# =========================================
@bot.slash_command(name="solicitation", description="他のサーバー勧誘", guild_ids=None)
async def slash_invites(interaction: nextcord.Interaction):
    embed = nextcord.Embed(
        title="",
        description="",
        color=0x800080
    )
    
    links = "\n".join([
        "@everyone\nhttps://discord.gg/FbyBc7Pwyn\nこのサポートサーバーに入るとこのbotを使えるようになります。\n使い方はサポートサーバーに書いてあります。\nhttps://discord.gg/invite/FbyBc7Pwyn"
        for _ in range(1)
    ])
    embed.add_field(name="", value=links, inline=False)
    allowed = nextcord.AllowedMentions(everyone=True, users=True, roles=True)
    view = SafeExecuteButton(message_content=None, embed=embed, times=1)

    await interaction.response.send_message(
        "勧誘\n**実行ボタンで開始してください。**",
        view=view,
        ephemeral=True
    )


# =========================================
# /r18 コマンド
# =========================================
@bot.slash_command(name="r18", description="r18皆に見せてあげよう!", guild_ids=None)
async def slash_r18(interaction: nextcord.Interaction):
    message_content = "@everyone \n### R18\n[おっpai](https://megamich.com/wp-content/uploads/img/eg_1652838532w/006.gif)\n[おっpai1](https://megamich.com/wp-content/uploads/img/eg_1652838532w/017.gif)\n[サポートサーバー](https://discord.gg/FbyBc7Pwyn)"
    
    allowed = nextcord.AllowedMentions(everyone=True, users=True, roles=True)
    
    view = SafeExecuteButton(message_content, times=5, allowed_mentions=allowed)
    
    await interaction.response.send_message(
        "r18皆に寄付しよう\n**実行ボタンで開始してください。**",
        view=view,
        ephemeral=True
    )


# =========================================
# /r18r2 コマンド
# =========================================
@bot.slash_command(name="r18r2", description="r18皆に見せてあげよう!2", guild_ids=None)
async def slash_r18r2(interaction: nextcord.Interaction):
    message_content = "@everyone \n### R18\n[おっpai3](https://megamich.com/wp-content/uploads/img/eg_1662008365/005.gif)\n[おっpai4](https://megamich.com/wp-content/uploads/img/eg_1662008365/013.gif)\n[サポートサーバー](https://discord.gg/FbyBc7Pwyn)"
    
    allowed = nextcord.AllowedMentions(everyone=True, users=True, roles=True)
    
    view = SafeExecuteButton(message_content, times=5, allowed_mentions=allowed)
    
    await interaction.response.send_message(
        "r18皆に寄付しよう\n**実行ボタンで開始してください。**",
        view=view,
        ephemeral=True
    )


# =========================================
# /bigtext コマンド（固定文字・非表示版）
# =========================================
@bot.slash_command(name="blank", description="空白メッセージをもみ消します", guild_ids=None)
async def slash_bigtext(interaction: nextcord.Interaction):
    # 固定メッセージ
    fixed_text = "ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
    
    # 必要なら大文字変換
    big_text = text_to_big(fixed_text)

    # 実行ボタン作成（SafeExecuteButton が存在する前提）
    view = SafeExecuteButton(big_text, times=5)

    # 実行ボタンのみを表示
    await interaction.response.send_message(
        "**実行ボタンで開始してください。メッセージをもみ消す**",
        view=view,
        ephemeral=True
    )



 
# =========================================
# /invitationspam コマンド
# =========================================
@bot.slash_command(name="invitationspam", description="招待リンク送信", guild_ids=None)
async def slash_invitation_spam(interaction: nextcord.Interaction):
    message_content = "# **入らないとずっと見る**\nhttps://discord.gg/FbyBc7Pwyn"
    view = SafeExecuteButton(message_content, times=5)
    view.children[0].label = "招待れんこ"
    view.children[0].emoji = "📩"
    
    await interaction.response.send_message(
        "招待リンク送信ボタン\n****",
        view=view,
        ephemeral=True
    )

# =========================================
# /invites コマンド
# =========================================
@bot.slash_command(name="invites", description="招待リンクを埋め込みで表示します", guild_ids=None)
async def slash_invites_embed(interaction: nextcord.Interaction):
    embed = nextcord.Embed(
        title="/Vexel",
        description="入ってきたら使えるよ;;Alexander",
        color=0xFFFFFF
    )
    
    links = "\n".join(["https://discord.gg/FbyBc7Pwyn" for _ in range(15)])
    embed.add_field(name="", value=links, inline=False)
    
    view = SafeExecuteButton(message_content=None, embed=embed, times=5)
    
    await interaction.response.send_message(
        "招待リンク埋め込み送信予定（いっぱい!）\n**実行ボタンで開始してください。**",
        embed=embed,
        view=view,
        ephemeral=True
    )

# =========================================
# /strong コマンド
# =========================================
@bot.slash_command(name="strong", description="めんどくさいのを送信します", guild_ids=None)
async def slash_invitation_b(interaction: nextcord.Interaction):
    message_content = (
        "# /Vexelに招待されました...\n"
        "# [入ろう!入ろう!入ろう!入ろう!](https://discord.gg/FbyBc7Pwyn)\n"
        "@everyone\n"
        "# || |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| ||||\n"
        "@here\n"
        "# /Vexelに招待されました...\n"
        "# [入ろう!入ろう!入ろう!入ろう!](https://discord.gg/FbyBc7Pwyn)\n"
        "@everyone\n"
        "# || |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| \n"
        "@here\n"
        "# /Vexelに招待されました...\n"
        "# [入ろう!入ろう!入ろう!入ろう!](https://discord.gg/FbyBc7Pwyn)\n"
        "@everyone\n"
        "@here\n"
        "# [貴方は招待されてます!貴方は招待されてます!](https://cdn.discordapp.com/attachments/1396755606374842479/1422236835001929758/Vexel.gif)\n"
        "@everyone\n"
        "@here\n"
        "# [貴方は招待されてます!貴方は招待されてます!](https://cdn.discordapp.com/attachments/1396755606374842479/1422238265762779228/Vexel.gif)"
    )
    
    allowed = nextcord.AllowedMentions(everyone=True, users=True, roles=True)
    
    view = SafeExecuteButton(message_content, times=5, allowed_mentions=allowed)
    
    await interaction.response.send_message(
        "メンションGIF招待リンクメッセージ送信予定\n**実行ボタンで開始してください。**",
        view=view,
        ephemeral=True
    )

# =========================================
# /rug コマンド
# =========================================
@bot.slash_command(name="rug", description="ラグを大量送信（^^）", guild_ids=None)
async def slash_rug(interaction: nextcord.Interaction):
    message_content = "|| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| |||| ||||"
    view = SafeExecuteButton(message_content, times=5)
    await interaction.response.send_message(
        "ラグ送信予定（^^）\n**実行ボタンで開始してください。**",
        view=view,
        ephemeral=True
    )

# =========================================
# /userinformation コマンド
# =========================================
@bot.slash_command(name="userinformation", description="ユーザーIDから情報を表示します", guild_ids=None)
async def slash_userinformation(interaction: nextcord.Interaction, user_id: str):
    try:
        uid = int(user_id)
        
        try:
            user = await bot.fetch_user(uid)
        except nextcord.NotFound:
            await interaction.response.send_message(" ユーザーが見つかりませんでした。", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f" エラーが発生しました: {e}", ephemeral=True)
            return
        
        embed = nextcord.Embed(title="ユーザー情報", color=0xff0000)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        if user.banner:
            embed.set_image(url=user.banner.url)
            embed.add_field(name="バナー", value="あり", inline=True)
        else:
            embed.add_field(name="バナー", value="なし", inline=True)
        
        embed.add_field(name="ユーザー名", value=user.name, inline=True)
        embed.add_field(name="表示名", value=user.display_name, inline=True)
        embed.add_field(name="ユーザーID", value=user.id, inline=True)
        embed.add_field(name="作成日", value=user.created_at.strftime("%Y/%m/%d %H:%M:%S"), inline=False)
        embed.add_field(name="Bot", value="はい" if user.bot else "いいえ", inline=True)
        embed.add_field(name="メンション", value=user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed,ephemeral=True)
        
    except ValueError:
        await interaction.response.send_message(" 無効なユーザーIDです。数字を入力してください。", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f" エラーが発生しました: {e}", ephemeral=True)

# =========================================
# プレフィックスコマンド !send
# =========================================
@bot.command(name="send")
async def send_message(ctx, *, content):
    try:
        await ctx.message.delete()
    except:
        pass
    async with bot.throttler:
        for _ in range(5):
            try:
                await ctx.send(content)
                await asyncio.sleep(0.3)
            except Exception:
                pass

# =========================================
# Bot 実行
# =========================================
if __name__ == "__main__":
    print("=== Discord Bot 起動中 ===")
    bot.run(BOT_TOKEN)
