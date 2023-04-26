import discord
import asyncio
import os
import requests
import random
import gspread_asyncio
import re

from google.oauth2.service_account import Credentials
from discord import Embed
from discord import Interaction
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import Select
from datetime import datetime, timedelta, date
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.typing = False
intents.presences = False

TOKEN = os.environ['TOKEN']
PREFIX = os.environ['PREFIX']

prefix = '!'
bot = commands.Bot(command_prefix=prefix, intents=intents)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_info = {
  "type": "service_account",
  "project_id": "thematic-bounty-382700",
  "private_key_id": "502d8dd4f035d15b57bff64ee323d544d28aedc4",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQD4Kze3Hn/yxevG\nzHUklYGSDDs8qKQeyYdd1eWaR0PNKZ2+nwKFGmXGENS6vuy3U81dqI3AVgA3w6UW\nHEaVfPvc31OX5yNCIS0eQxxqWWGJJ5+MbvUC06qXi/7hCup0WK+hoqwjHtUX7AYu\nEDgtf6xd29gSvb3YXs6pvi+2tpwPt0SED6HGPU7qPRsAaPnyUsVCj/mW04ca2iea\nxMsIqxKT6ufNssiXX7qhKyziowneM0lp8BB3k2z+/FGPQOCdi/lIscC9zKbDOIcb\nOZw+B2sd2opp7Dwo3JMIkh3NJevw9hjp0+CFeqemGNsCAiSuFkvydx6BagWaWAPs\nC48nZLNZAgMBAAECggEAF3uUbTMZQZZVoAU5CPYOMY0PfmcJR6IDeX8715BKg8N+\nOhtHBGQJ8Rbm4Ehgcxz+i/AfAK4KnXw5dvkEO1E9Lmph+Tfdg9yKjchlLBGK24z4\nqZPWwpaXl/k+7BnJs2pwbROs5PJeEOJMN+fgPvrrqyJ6RNS4Pf0Dond9AZWwOQLL\naJPFZryK7Bmvtt0H8mDDWdfqmCQTtPJ9PUyDEUeenlyhuek8wH3GHcghOSlsCDF1\nW/3YXM9Vr/arE4V6hTLwXofrUnTuXTfo+DcaOIXpHqIPS+nCyzWZ0kAJ7/uKjhnN\nF4kgv9aXDX9Y7S+3irXazRhowfu2rGuPRO/2+FCuMQKBgQD+JRDctOrKvpl9zDaw\nWT2a3qmYuFf90+b8EkKsWzVBM7neEJlw1ZWxUZzkdHXwkxcM7w93BjZeXJRnI7HZ\n5sHMrRw3p7Cwy0REqC3GSbYMCIZ/98y5Ot5sOXamUCOtYnic1NG2PBzr9h94Nt7d\nZu9D7cD/kaogm9Fl9t1VMD3REQKBgQD5+vvxY0nUkzrPEHfAOnPRqt3fM9ryzmk9\n8WyffmWqaDcvb9pl1F/+/51u00cvh2Q6etvL0J850AB0AKC9QdYzIaSj4LeRNzjA\ns+K6Po5+HAYezxC1cYzFh+slAfX3gX9pa11f3aOltj4h7IXvqBB0iH4rl/i2KQ/G\ntSDa62K9yQKBgAXXEDYiKisSijBr2u3efx3p8/fAdLUug2ZTfRi819Jxv9msg/ol\nzlTOzU4qpvMqTiNL8w0HJYSxl+9u0I1zUgzEBZv5zIOjiCQTwUmHNBm+sGiMZzXy\ndl4CTAmyWb+IPcFM2qzXYMrDUyHOEP0BeooTEpZM4J3zNrKjI57rhuAhAoGAKWDC\nE1K8BdPZCC1RpSAHy8zcrPWIaGiCQx6TPFNPwMU/XTrGi9R7j1oAVTfjsJpYnNV5\nTGNb99XWPV1dPfaH3i7TcczglcjuO/eKsAlqzLUWzkK4IVCKXKgC5D1O2Yk17d03\nt4aYb/Wak0LzaJgJIUD2oYCmSoDBe8K/jX0o+wECgYBnxk9HR/23hjWaxrSnXGDB\nHxLXg9Wz5w0N+gdC/FNxknFOft+nsCMKWMocOtGYhJU3OvkTYYqL1iDsKoMb74xG\nVwB1fuoNrNp+aJ/CzbtZVT1WLzXG41e9cu2TuOy+wpDlryfJAZ6KNVgDOmhh8TR2\nz7T0rt1QSfOZILpiwpR4jg==\n-----END PRIVATE KEY-----\n",
  "client_email": "noisycontents@thematic-bounty-382700.iam.gserviceaccount.com",
  "client_id": "107322055541690533468",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/noisycontents%40thematic-bounty-382700.iam.gserviceaccount.com"
}
credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
aio_creds = credentials

#------------------------------------------------투표------------------------------------------------------#  
def get_emoji(emoji):
    if isinstance(emoji, str):
        return emoji
    elif isinstance(emoji, discord.Emoji):
        return f'{emoji.name}:{emoji.id}'
    elif isinstance(emoji, discord.PartialEmoji):
        return f'{emoji.name}:{emoji.id}'
    else:
        return None

polls = {}

@bot.command(name='투표')
async def vote(ctx, *, args):
    if not args:
        embed = discord.Embed(title=f'Vote Help', description=f'')
        embed.add_field(name=f'Like/Dislike', value=f'!vote title')
        embed.add_field(name=f'multiple options (1-9)', value=f'!vote title, option 1, option 2, ..., option 9')
        await ctx.send(embed=embed)
    else:
        # Split title and options
        parts = [part.strip() for part in args.split(',')]
        title = parts[0]
        options = parts[1:]
        # rest of the code

        # Create embed
        embed = discord.Embed(title=title)
        if not options:
            # Like/Dislike
            message = await ctx.send(embed=embed)
            await message.add_reaction('👍')
            await message.add_reaction('👎')
        else:
            # Multiple responses (1-9)
            emoji_list = [chr(0x31) + '\u20E3', chr(0x32) + '\u20E3', chr(0x33) + '\u20E3', chr(0x34) + '\u20E3', chr(0x35) + '\u20E3', chr(0x36) + '\u20E3', chr(0x37) + '\u20E3', chr(0x38) + '\u20E3', chr(0x39) + '\u20E3'] # Option number label

            s = ''
            emoji = iter(emoji_list)
            unicode_options = []  # New list for storing Unicode representation of options
            for option in options:
                try:
                    current_emoji = next(emoji)                    
                    s += f'{current_emoji} {option}\n'
                    unicode_options.append(current_emoji)
                except StopIteration:
                    await ctx.send('Maximum of 9 options allowed.')
                    return

            # Output title and poll ID to Discord
            embed.add_field(name='Options', value=s)
            embed.add_field(name='현재 투표 현황', value='투표를 시작하신 후에 확인이 가능합니다.')

            # Send poll message
            random_poll_id = str(random.randint(1000, 9999))
            poll_message = await ctx.send(f'투표가 생성되었어요! 투표 번호는: {random_poll_id}', embed=embed)

            # Add reactions to poll message
            for i in range(len(options)):
                await poll_message.add_reaction(emoji_list[i])

            # Save poll information
            poll_info = {'title': title, 'options': unicode_options, 'votes': {}, 'closed': False, 'message_id': poll_message.id} # Use unicode_options instead of options
            polls[poll_message.id] = poll_info
            
#------------------------------------------------고정------------------------------------------------------# 

# Set up Google Sheets worksheet
async def get_sheet4():
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet4 = await spreadsheet.worksheet('독독독')
    rows = await sheet4.get_all_values()
    return sheet4, rows 
  
sticky_messages = {}
    
def has_specific_roles(allowed_role_ids):
    async def predicate(ctx):
        allowed_roles = [ctx.guild.get_role(role_id) for role_id in allowed_role_ids]
        return any(role in ctx.author.roles for role in allowed_roles)

    return commands.check(predicate)

allowed_role_ids = [1019165662364586034, 1003257850799341615]    
    
# 스프레드시트에서 초기 고정 메시지를 가져옵니다.
async def refresh_sticky_messages(sheet4):
    global sticky_messages
    global last_sticky_messages
    sheet4_values = await sheet4.get_all_values()

    new_sticky_messages = {}
    for row in sheet4_values:
        if len(row) == 2 and row[0].isdigit():
            channel_id = int(row[0])
            message = row[1]
            new_sticky_messages[channel_id] = message

    deleted_channel_ids = set(sticky_messages.keys()) - set(new_sticky_messages.keys())
    for channel_id in deleted_channel_ids:
        if channel_id in last_sticky_messages:
            old_message = last_sticky_messages[channel_id]
            try:
                asyncio.create_task(old_message.delete())
            except discord.NotFound:
                pass

    sticky_messages = new_sticky_messages
    last_sticky_messages = {}
    
@bot.command(name='고정')
@has_specific_roles(allowed_role_ids)
async def sticky(ctx, *, message):
    global sticky_messages
    channel_id = ctx.channel.id
    sticky_messages[channel_id] = message

    # 스프레드시트에 고정 메시지를 저장합니다.
    sheet4, _ = await get_sheet4()
    if str(channel_id) in await sheet4.col_values(1):
        row_num = (await sheet4.col_values(1)).index(str(channel_id)) + 1
    else:
        row_num = len(await sheet4.col_values(1)) + 1

    await sheet4.update_cell(row_num, 1, str(channel_id))
    await sheet4.update_cell(row_num, 2, message)

    # 스프레드시트에 저장된 내용을 업데이트합니다.
    await refresh_sticky_messages(sheet4)

    await ctx.send(f'메시지가 고정됐습니다!')

@bot.command(name='해제')
@has_specific_roles(allowed_role_ids)
async def unsticky(ctx):
    global sticky_messages
    channel_id = ctx.channel.id

    if channel_id in sticky_messages:
        del sticky_messages[channel_id]

        # 스프레드시트에서 고정 메시지를 삭제합니다.
        sheet4, _ = await get_sheet4()
        row_num = (await sheet4.col_values(1)).index(str(channel_id)) + 1
        await sheet4.delete_row(row_num)

        # 스프레드시트에 저장된 내용을 업데이트합니다.
        await refresh_sticky_messages(sheet4)

        await ctx.send('고정이 해제됐어요!')
    else:
        await ctx.send('이 채널에는 고정된 메시지가 없어요')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    global sticky_messages
    global last_sticky_messages

    channel_id = message.channel.id

    if channel_id in sticky_messages:
        if channel_id in last_sticky_messages:
            old_message = last_sticky_messages[channel_id]
            try:
                await old_message.delete()
            except discord.NotFound:
                pass

        new_message = await message.channel.send(sticky_messages[message.channel.id])
        last_sticky_messages[message.channel.id] = new_message

#------------------------------------------------1일1독------------------------------------------------------# 

# Set up Google Sheets worksheet
async def get_sheet5():
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet5 = await spreadsheet.worksheet('1일1독')
    rows = await sheet5.get_all_values()
    return sheet5, rows 

async def find_user(username, sheet):
    cell = None
    try:
        cells = await sheet.findall(username)
        if cells:
            cell = cells[0]
    except gspread.exceptions.APIError as e:
        print(f'find_user error: {e}')
    return cell

class CustomSelect(discord.ui.Select):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "학습인증":
            await interaction.response.send_message("1일1독을 인증하시려면 '!인증 인증하려는 날짜를 입력해주세요!' 예시)!인증 0425", ephemeral=True)
        elif self.values[0] == "누적현황":
            await interaction.response.send_message("현재까지의 1일1독 누적 횟수를 조회하시려면 '!누적'을 입력해주세요! 예시)!누적", ephemeral=True)
            
@bot.command(name="1일1독")
async def one_per_day(ctx):
    await ctx.message.delete()  # 명령어 삭제
    
    embed = discord.Embed(title="1일1독 명령어 모음집", description=f"{ctx.author.mention} 원하시는 명령어를 아래에서 골라주세요")
    embed.set_footer(text="이 창은 1분 후 자동 삭제됩니다")

    message = await ctx.send(embed=embed, ephemeral=True)

    select = CustomSelect(
        options=[
            discord.SelectOption(label="학습인증", value="학습인증"),
            discord.SelectOption(label="누적현황", value="누적현황")
        ],
        placeholder="명령어를 선택하세요",
        min_values=1,
        max_values=1
    )

    select_container = discord.ui.View()
    select_container.add_item(select)

    message = await message.edit(embed=embed, view=select_container)

    await asyncio.sleep(60)  # 1분 대기
    await message.delete()  # 임베드 메시지와 셀렉트 메뉴 삭제

class AuthButton(discord.ui.Button):
    def __init__(self, ctx, user, date):
        super().__init__(style=discord.ButtonStyle.green, label="확인 ")
        self.ctx = ctx
        self.user = user
        self.date = date
        self.stop_loop = False  # Add the stop_loop attribute
    
    async def callback(self, interaction: discord.Interaction):
        
        sheet5, rows = await get_sheet5()
        
        if interaction.user == self.ctx.author:
            return
        existing_users = await sheet5.col_values(1)
        if str(self.user) not in existing_users:
            empty_row = len(existing_users) + 2
            await sheet5.update_cell(empty_row, 1, str(self.user))  # A열에서 2행부터 입력
            existing_dates = await sheet5.row_values(1)
            if self.date not in existing_dates:
                empty_col = len(existing_dates) + 1
                await sheet5.update_cell(1, empty_col, self.date)
                await sheet5.update_cell(empty_row, empty_col, "1")  # 날짜에 맞는 셀에 1 입력
            else:
                col = existing_dates.index(self.date) + 1
                await sheet5.update_cell(empty_row, col, "1")  # 날짜에 맞는 셀에 1 입력
        else:
            index = existing_users.index(str(self.user)) + 1
            existing_dates = await sheet5.row_values(1)
            if self.date not in existing_dates:
                empty_col = len(existing_dates) + 1
                await sheet5.update_cell(1, empty_col, self.date)
                await sheet5.update_cell(index, empty_col, "1")  # 날짜에 맞는 셀에 1 입력
            else:
                col = existing_dates.index(self.date) + 1
                await sheet5.update_cell(index, col, "1")  # 날짜에 맞는 셀에 1 입력
        await interaction.message.edit(embed=discord.Embed(title="인증상황", description=f"{interaction.user.mention}님이 {self.ctx.author.mention}의 {self.date} 1일1독 인증했습니다🥳"), view=None)
        self.stop_loop = True

async def update_embed(ctx, date, msg):
    button = AuthButton(ctx, ctx.author, date) # Move button creation outside of the loop
    while True:
        try:
            if button.stop_loop: # Check if stop_loop is True before updating the message
                break

            view = discord.ui.View(timeout=None)
            view.add_item(button)
            view.add_item(CancelButton(ctx))

            embed = discord.Embed(title="인증요청", description=f"{ctx.author.mention}님의 {date} 1일1독 인증 요청입니다")
            await msg.edit(embed=embed, view=view)
            await asyncio.sleep(60)
        except discord.errors.NotFound:
            break
class CancelButton(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(style=discord.ButtonStyle.red, label="취소")
        self.ctx = ctx
        self.stop_loop = False  # Add the stop_loop attribute
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.author.id != self.ctx.author.id:
            # Interaction was not initiated by the same user who invoked the command
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return

async def update_embed(ctx, date, msg):
    button = AuthButton(ctx, ctx.author, date) # Move button creation outside of the loop
    cancel = CancelButton(ctx)  # Create a CancelButton instance
    while True:
        try:
            if button.stop_loop or cancel.stop_loop: # Check if any button's stop_loop is True before updating the message
                break

            view = discord.ui.View(timeout=None)
            view.add_item(button)
            view.add_item(cancel)  # Add the CancelButton to the view

            embed = discord.Embed(title="인증요청", description=f"{ctx.author.mention}님의 {date} 1일1독 인증 요청입니다")
            await msg.edit(embed=embed, view=view)
            await asyncio.sleep(60)
        except discord.errors.NotFound:
            break
        
@bot.command(name='인증')
async def authentication(ctx, date):
    
    if not re.match(r'^(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$', date ):
        await ctx.send("정확한 네자리 숫자를 입력해주세요! 1월1일 인증을 하시려면 0101을 입력하시면 됩니다 :)")
        return
    
    sheet5, rows = await get_sheet5()
    existing_users = await sheet5.col_values(1)
    if str(ctx.author) in existing_users:
        user_index = existing_users.index(str(ctx.author)) + 1
        existing_dates = await sheet5.row_values(1)
        if date in existing_dates:
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet5.cell(user_index, date_index)
            if cell_value.value == "1":
                await ctx.send(embed=discord.Embed(title="Authorization Status", description=f"{ctx.author.mention}님, 해당 날짜는 이미 인증되었습니다!"))
                return

    embed = discord.Embed(title="인증상태", description=f"{ctx.author.mention}님의 {date} 1일1독 인증 요청입니다")
    view = discord.ui.View()
    button = AuthButton(ctx, ctx.author, date)
    view.add_item(button)
    view.add_item(CancelButton(ctx)) # Add the CancelButton to the view
    msg = await ctx.send(embed=embed, view=view)
    
    asyncio.create_task(update_embed(ctx, date, msg))

    def check(interaction: discord.Interaction):
        return interaction.message.id == msg.id and interaction.data.get("component_type") == discord.ComponentType.button.value

    await bot.wait_for("interaction", check=check)
   
    
def get_week_range(): 
    today = date.today() # 오늘 날짜 
    monday = today - timedelta(days=today.weekday()) #현재 날짜에서 오늘만큼의 요일을 빼서 월요일 날짜 획득
    sunday = monday + timedelta(days=6)
    return monday, sunday

    
@bot.command(name='누적')
async def accumulated_auth(ctx):
    sheet5, rows = await get_sheet5()
    existing_users = await sheet5.col_values(1)
    
    if str(ctx.author) not in existing_users:
        await ctx.send(f"{ctx.author.mention}님, 1일1독 기록이 없습니다")
        return

    user_index = existing_users.index(str(ctx.author)) + 1
    total = 0
    monday, sunday = get_week_range()
    existing_dates = await sheet5.row_values(1)
    for date in existing_dates:
        if date and monday.strftime('%m%d') <= date <= sunday.strftime('%m%d'):
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet5.cell(user_index, date_index)
            if cell_value.value:
                total += int(cell_value.value)
    
    overall_ranking = await sheet5.cell(user_index, 2) # Read the value of column B
    overall_ranking_value = int(overall_ranking.value)
    
    embed = discord.Embed(title="누적 인증 현황", description=f"{ctx.author.mention}님, 이번 주({monday.strftime('%m%d')}~{sunday.strftime('%m%d')}) 누적 인증은 {total}회 입니다.\n한 주에 5회 이상 인증하면 랭커로 등록됩니다!\n랭커 누적 횟수는 {overall_ranking_value}회 입니다.")
    
    if overall_ranking_value >= 10 and not discord.utils.get(ctx.author.roles, id=1040094410488172574):
        role = ctx.guild.get_role(1040094410488172574)
        await ctx.author.add_roles(role)
        embed.add_field(name="축하합니다!", value=f"{role.mention} 롤을 획득하셨습니다!")

    if overall_ranking_value >= 30 and not discord.utils.get(ctx.author.roles, id=1040094943722606602):
        role = ctx.guild.get_role(1040094943722606602)
        await ctx.author.add_roles(role)
        embed.add_field(name="축하합니다!", value=f"{role.mention} 롤을 획득하셨습니다!")

    await ctx.send(embed=embed)

# 월드와이드 #
# Set up Google Sheets worksheet
async def get_sheet6():
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet6 = await spreadsheet.worksheet('월드와이드')
    rows = await sheet6.get_all_values()
    return sheet6, rows 

async def find_user(username, sheet):
    cell = None
    try:
        cells = await sheet.findall(username)
        if cells:
            cell = cells[0]
    except gspread.exceptions.APIError as e:
        print(f'find_user error: {e}')
    return cell

@bot.command(name='등록')
async def Register(ctx):
    username = str(ctx.message.author)
    
    sheet3, rows = await get_sheet6()

    # Check if the user is already registered
    registered = False
    row = 2
    while (cell_value := (await sheet6.cell(row, 1)).value):
        if cell_value == username:
            registered = True
            break
        row += 1

    if registered:
        embed = discord.Embed(description=f"{ctx.author.mention}님, 이미 등록하셨어요!", color=0xFF0000)
        await ctx.send(embed=embed)
    else:
        await sheet6.update_cell(row, 1, username)

        role = discord.utils.get(ctx.guild.roles, id=1093781563508015105)
        await ctx.author.add_roles(role)

        embed = discord.Embed(description=f"{ctx.author.mention}님, 에 정상적으로 등록됐습니다!",
                              color=0x00FF00)
        await ctx.send(embed=embed)
        
# 브루마블 게임판

board = ["START", "도쿄", "무인도", "이벤트", "샌프란시스코", "런던", "뉴욕", "파리", "베를린", "시드니", "리우데자네이루",
         "방콕", "이벤트", "몬트리올", "바르셀로나", "이스탄불", "서울", "상하이", "홍콩", "싱가포르",
         "다카르", "리마", "카이로", "이벤트", "시카고"]

# 게임판의 각 칸의 설명
descriptions = ["시작점", "도쿄", "무인도", "이벤트", "샌프란시스코", "런던", "뉴욕", "파리", "베를린", "시드니", "리우데자네이루",
                "방콕", "이벤트", "몬트리올", "바르셀로나", "이스탄불", "서울", "상하이", "홍콩", "싱가포르",
                "다카르", "리마", "카이로", "이벤트", "시카고"]


class GameView(discord.ui.View):
    def __init__(self, user, sheet):
        super().__init__(timeout=None)
        self.user = user
        self.sheet = sheet
         self.add_item(discord.ui.Button(label="주사위 굴리기", style=discord.ButtonStyle.primary, custom_id=f"roll_dice_button_{user.id}"))

    @discord.ui.button(label="주사위 굴리기", style=discord.ButtonStyle.primary, custom_id=None)  # 수정된 부분
    async def roll_dice(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return

        cell = await find_user(str(self.user), self.sheet)
        if cell:
            remaining_rolls = int(await self.sheet.cell(cell.row, 2).value)
            if remaining_rolls > 0:
                await self.sheet.update_cell(cell.row, 2, remaining_rolls - 1)
                dice_result = random.randint(1, 6)
                # 게임보드 이동 등 게임 진행 로직 구현
            else:
                await interaction.response.send_message("더 굴릴 수 있는 주사위가 없습니다.", ephemeral=True)
        else:
            await interaction.response.send_message("등록되지 않은 사용자입니다.", ephemeral=True)

@bot.command(name='월드')
async def create_game(ctx):
    await ctx.message.delete()  # 명령어 삭제
    
    thread = await ctx.channel.create_thread(name=f"게임 스레드: {ctx.author.name}", type=discord.ChannelType.private_thread)
    sheet, rows = await get_sheet6()

    game_board = discord.Embed(title="월드와이드 게임 보드")
    for i in range(1, 26):
        game_board.add_field(name=f"칸 {i}", value="게임 칸 설명", inline=True)

    game_view = GameView(ctx.author, sheet)
    await thread.send(embed=game_board, view=game_view)
    
#봇 실행
bot.run(TOKEN)
