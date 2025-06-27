import discord
import asyncio
import os
import requests
import random
import gspread_asyncio
import re
import time
import pytz
import asyncio

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
SECRET = os.environ['SECRET']

private_key = os.environ['SECRET'].replace("\\n", "\n")

prefix = '!'

bot = commands.Bot(command_prefix=prefix, intents=intents)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_info = {
  "type": "service_account",
  "project_id": "server-439817",
  "private_key_id": "45202b8f054ef38af115cf72e0c9d3bed3d8a008",
  "private_key": private_key,
  "client_email": "server@server-439817.iam.gserviceaccount.com",
  "client_id": "100976887028503717064",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/server%40server-439817.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
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
            
@bot.event
async def on_reaction_add(reaction, user):
    # Check if the reaction is for a poll message
    message_id = reaction.message.id
    poll_id = None
    for pid, poll in polls.items():
        if 'message_id' in poll and poll['message_id'] == message_id:
            poll_id = pid
            break

    if not poll_id:
        print(f"Reaction received for non-poll message with message ID {message_id}")
        return

    # Check if the reaction was added to a message sent by the bot
    if user == bot.user:
        return

    # Check if the reaction is for a valid option
    emoji = get_emoji(reaction.emoji)
    poll_data = polls[poll_id]
    option_index = -1
    for i, option in enumerate(poll_data['options']):
        if emoji == option:
            option_index = i
            break
    if option_index == -1:
        print(f"User {user.name} reacted with invalid emoji {emoji} for poll {poll_data['title']} ({poll_id})")
        return

    # Add or update user vote
    user_id = str(user.id)
    if user_id not in poll_data['votes']:
        poll_data['votes'][user_id] = emoji
    else:
        poll_data['votes'][user_id] = emoji

    print(f"User {user.name} voted for option {emoji} in poll {poll_data['title']} ({poll_id})")

    # Update poll embed with current vote count
    poll_message_id = poll_data['message_id']
    poll_message = await reaction.message.channel.fetch_message(poll_message_id)

    poll_results = {}
    for option in poll_data['options']:
        poll_results[option] = 0
    for reaction in poll_message.reactions:
        emoji = get_emoji(reaction.emoji)
        if emoji in poll_data['options']:
            async for user in reaction.users():
                if user != bot.user:
                    poll_results[emoji] += 1

    result_message = ''
    for option in poll_data['options']:
        count = poll_results[option]
        result_message += f'{option}: {count} vote(s)\n'

    poll_embed = poll_message.embeds[0]
    poll_embed.set_field_at(1, name='현재 투표 현황', value=result_message)

    await poll_message.edit(embed=poll_embed)

    print(f"Poll {poll_data['title']} ({poll_id}) updated with current vote count")
    
#------------------------------------------------고정------------------------------------------------------# 

# 각각의 시트 이름은 달라야 하며 서버기록 내 시트이름으로 변경하면 됩니다. 전체 코드에서 시트이름이 중복되면 
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

# 1일 1독
async def get_sheet5():
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet5 = await spreadsheet.worksheet('1일1독2025')
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

#------------------------------------------------!1일1독을 입력하였을 때 뜨는 명령어 모음입니다------------------------------------------------------#             
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
            empty_row = len(existing_users) + 1
            await sheet5.insert_row([str(self.user)], empty_row)  # A열에서 2행부터 입력
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
    button = AuthButton(ctx, ctx.author, date) 
    while True:
        try:
            if button.stop_loop: 
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
        if interaction.user.id != self.ctx.author.id:
            # Interaction was not initiated by the same user who invoked the command
            await interaction.response.send_message("본인의 메시지만 취소할 수 있어요", ephemeral=True)
            return
        await interaction.message.delete()
        
@bot.command(name='인증')
async def authentication(ctx, date):
    
    if not date:
        await ctx.send("날짜를 입력해주세요! 예) 0101")
        return

    # Validate the input date
    if not re.match(r'^(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$', date):
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

    if overall_ranking_value >= 1 and not discord.utils.get(ctx.author.roles, id=1103561648767258655):
        role = discord.utils.get(ctx.guild.roles, id=1103561648767258655)
        if role is not None:
            await ctx.author.add_roles(role)
            embed.add_field(name="축하합니다!", value=f"{role.mention} 롤을 획득하셨습니다!")

    await ctx.send(embed=embed)

#-----------북클럽 종료 후 채널만 ------------#
# 북클럽으로 시트 지정 
async def get_sheet7():  
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet7 = await spreadsheet.worksheet('북클럽')
    rows = await sheet7.get_all_values()
    return sheet7, rows 

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
        if self.values[0] == "북클럽인증":
            await interaction.response.send_message("'!북클럽인증' 명령어를 통해 북클럽 학습 인증을 할 수 있습니다. 예시)!북클럽인증", ephemeral=True)
        elif self.values[0] == "북클럽누적":
            await interaction.response.send_message("'!북클럽누적' 현재까지 인증한 누적현황을 볼 수 있어요. 30회 인증이 확인되면 완주자 역할을 소유하게 됩니다 예시)!북클럽누적", ephemeral=True)
            
def is_allowed_channel(channel_id):
    allowed_channels = ["1097731096206119033", "1057567679281647706", "929917732537909288"]
    return str(channel_id) in allowed_channels
  
@bot.command(name="")
async def one_per_day(ctx):
    await ctx.message.delete()  # 명령어 삭제
    if not is_allowed_channel(ctx.channel.id):
        await ctx.send("해당 명령어는 북클럽 채널에서만 사용할 수 있어요")
        return
      
    embed = discord.Embed(title="북클럽 명령어 모음집", description=f"{ctx.author.mention}님 원하시는 명령어를 아래에서 골라주세요")
    embed.set_footer(text="이 창은 1분 후 자동 삭제됩니다")

    message = await ctx.send(embed=embed, ephemeral=True)

    select = CustomSelect(
        options=[
            discord.SelectOption(label="북클럽인증", value="북클럽인증"),
            discord.SelectOption(label="북클럽누적", value="북클럽누적")
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

kst = pytz.timezone('Asia/Seoul') # 한국 시간대로 설정 
now = datetime.now(kst).replace(tzinfo=None)
today1 = now.strftime('%m%d') 

@bot.command(name='')
async def book_club_auth(ctx):
    required_role = "1097785865566175272" 
    sheet7, rows = await get_sheet7()  # get_sheet3 호출 결과값 받기
    username = str(ctx.message.author)

    now = datetime.now(kst).replace(tzinfo=None)  # 날짜 업데이트 코드 수정
    today1 = now.strftime('%m%d')

    user_row = None
    for row in await sheet7.get_all_values():
        if username in row:
            user_row = row
            break

    if user_row is None:
        embed = discord.Embed(title='오류', description='2023 북클럽에 등록된 멤버가 아닙니다')
        await ctx.send(embed=embed)
        return

    user_cell = await find_user(username, sheet7)

    if user_cell is None:
        embed = discord.Embed(title='오류', description='2023 북클럽에 등록된 멤버가 아닙니다')
        await ctx.send(embed=embed)
        return

    today1_col = None
    for i, col in enumerate(await sheet7.row_values(1)):
        if today1 in col:
            today1_col = i + 1
            break

    if today1_col is None:
        embed = discord.Embed(title='Error', description='2023 북클럽 기간이 아닙니다')
        await ctx.send(embed=embed)
        return

    if (await sheet7.cell(user_cell.row, today1_col)).value == '1':
        embed = discord.Embed(title='오류', description='이미 오늘의 인증을 하셨습니다')
        await ctx.send(embed=embed)
        return
      
    await update_embed_book_auth(ctx, username, today1, sheet7)
        
class AuthButton3(discord.ui.Button):
    def __init__(self, ctx, username, today1, sheet7):
        super().__init__(style=discord.ButtonStyle.green, label="학습인증")
        self.ctx = ctx
        self.username = username
        self.sheet7 = sheet7
        self.auth_event = asyncio.Event()
        self.stop_loop = False
        self.today1 = today1  # 인스턴스 변수로 today1 저장

    async def callback(self, interaction: discord.Interaction):
        if interaction.user == self.ctx.author:
            # If the user is the button creator, send an error message
            embed = discord.Embed(title='Error', description='자신이 생성한 버튼은 사용할 수 없습니다 :(')
            await interaction.response.edit_message(embed=embed, view=None)
            return

        try:
            user_cell = await find_user(self.username, self.sheet7)
            if user_cell is None:
                embed = discord.Embed(title='오류', description='2023 북클럽에 등록된 멤버가 아닙니다')
                await interaction.response.edit_message(embed=embed, view=None)
                return
            user_row = user_cell.row
        except gspread.exceptions.CellNotFound:
            embed = discord.Embed(title='오류', description='2023 북클럽에 등록된 멤버가 아닙니다')
            await interaction.response.edit_message(embed=embed, view=None)
            return

        now = datetime.now(kst).replace(tzinfo=None)  # 날짜 업데이트 코드 수정
        self.today = now.strftime('%m%d')

        # Authenticate the user in the spreadsheet
        today1_col = (await self.sheet7.find(self.today)).col
        await self.sheet7.update_cell(user_row, today1_col, '1')

        # Set the auth_event to stop the loop
        self.auth_event.set()

        # Remove the button from the view
        self.view.clear_items()

        # Send a success message
        await interaction.message.edit(embed=discord.Embed(title="인증완료!", description=f"{interaction.user.mention}님이 {self.ctx.author.mention}의 학습인증을 인증했습니다👍"), view=None)
        self.stop_loop = True

async def update_embed_book_auth(ctx, username, today1, sheet7):
    embed = discord.Embed(title="학습인증", description=f' 버튼을 눌러 {ctx.author.mention}님의 학습을 인증해주세요')
    button = AuthButton3(ctx, username, today1, sheet7)
    view = discord.ui.View(timeout=None)
    view.add_item(button)
    message = await ctx.send(embed=embed, view=view)

    while not button.stop_loop:
        await asyncio.sleep(60)
        now = datetime.now(kst).replace(tzinfo=None)
        today1 = now.strftime('%m%d')
        if not button.stop_loop:
            view = discord.ui.View(timeout=None)
            button = AuthButton3(ctx, username, today1, sheet7)
            view.add_item(button)
            await message.edit(embed=embed, view=view)

    view.clear_items()
    await message.edit(view=view)
            
@bot.command(name='')
async def mission_count(ctx):
    if not is_allowed_channel(ctx.channel.id):
        await ctx.send("해당 명령어는 북클럽 채널에서만 사용할 수 있어요")
        return
    username = str(ctx.message.author)
    sheet7, rows = await get_sheet7()
    
    # Find the user's row in the Google Sheet
    user_row = None
    for row in await sheet7.get_all_values():
        if username in row:
            user_row = row
            break

    if user_row is None:
        embed = discord.Embed(title='Error', description='북클럽 멤버가 아닙니다')
        await ctx.send(embed=embed)
        return

    user_cell = await sheet7.find(username)
    count = int((await sheet7.cell(user_cell.row, 2)).value)  # Column I is the 9th column

    # Send the embed message with the user's authentication count
    embed = discord.Embed(description=f"{ctx.author.mention}님은 현재까지 {count} 회 인증하셨어요!", color=0x00FF00)
    await ctx.send(embed=embed)


#---------------------필사클럽2506기------------------------#  

#------------------------------------------------#    

async def get_sheet50():  
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet11 = await spreadsheet.worksheet('필사클럽(2506)')
    rows = await sheet11.get_all_values()
    return sheet11, rows 

async def find_user(username, sheet):
    cell = None
    try:
        cells = await sheet.findall(username)
        print(f"find_user: Searching for {username}. Found: {cells}")  # 디버깅 로그
        if cells:
            cell = cells[0]
    except gspread.exceptions.APIError as e:
        print(f"find_user error: {e}")
    return cell
            
def is_allowed_channel(channel_id):
    allowed_channels = ["1020187965739253760", "1194273995319685120", "1057267651405152256"]
    return str(channel_id) in allowed_channels
  
kst = pytz.timezone('Asia/Seoul') # 한국 시간대로 설정 
now = datetime.now(kst).replace(tzinfo=None)
today3 = now.strftime('%m%d') 


@bot.command(name='필사인증')
async def bixie_auth(ctx):
    required_role_id = 1388054635687710750  # 역할 ID (숫자)
    role = discord.utils.get(ctx.guild.roles, id=required_role_id)

    # 역할이 존재하지 않을 경우
    if role is None:
        embed = discord.Embed(
            title='오류',
            description=f"서버에 '필사클럽(2506)' 역할이 존재하지 않습니다. 관리자에게 문의하세요."
        )
        await ctx.send(embed=embed)
        return

    # 사용자에게 해당 역할이 없는 경우
    if role not in ctx.author.roles:
        embed = discord.Embed(
            title='오류',
            description=f"{ctx.author.mention}님은 필사클럽(2506)에 등록된 멤버가 아닙니다."
        )
        await ctx.send(embed=embed)
        return

    # 역할이 있는 경우 계속 진행
    sheet11, rows = await get_sheet11()  # get_sheet11 호출 결과값 받기
    username = str(ctx.message.author)

    now = datetime.now(kst).replace(tzinfo=None)  # 현재 한국 시간대의 날짜 및 시간 가져오기
    today3 = now.strftime('%m%d')  # 현재 날짜를 계산하여 문자열로 변환

    user_row = None
    for row in await sheet11.get_all_values():
        if username in row:
            user_row = row
            break

    if user_row is None:
        embed = discord.Embed(
            title='오류',
            description=f"{ctx.author.mention}님은 필사클럽(2506)에 등록된 멤버가 아닙니다."
        )
        await ctx.send(embed=embed)
        return

    user_cell = await find_user(username, sheet11)

    if user_cell is None:
        embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 필사클럽(2506)에 등록된 멤버가 아닙니다.')
        await ctx.send(embed=embed)
        return

    today3_col = None
    for i, col in enumerate(await sheet11.row_values(1)):
        if today3 in col:
            today3_col = i + 1
            break

    if today3_col is None:
        embed = discord.Embed(title='Error', description=f'{ctx.author.mention}님 현재는 필사클럽(2506) 기간이 아닙니다')
        await ctx.send(embed=embed)
        return

    if (await sheet11.cell(user_cell.row, today3_col)).value == '1':
        embed = discord.Embed(title='오류', description='이미 오늘의 인증을 하셨습니다')
        await ctx.send(embed=embed)
        return
      
    await update_embed_book_auth(ctx, username, today3, sheet11)
        
class AuthButton3(discord.ui.Button):
    def __init__(self, ctx, username, today3, sheet11):
        super().__init__(style=discord.ButtonStyle.green, label="필사클럽 인증")
        self.ctx = ctx
        self.username = username
        self.sheet11 = sheet11
        self.auth_event = asyncio.Event()
        self.stop_loop = False
        self.today3 = today3  # 인스턴스 변수로 today3 저장

    async def callback(self, interaction: discord.Interaction):
        if interaction.user == self.ctx.author:
            # If the user is the button creator, send an error message
            embed = discord.Embed(title='Error', description='자신이 생성한 버튼은 사용할 수 없습니다 :(')
            await interaction.response.edit_message(embed=embed, view=None)
            return

        try:
            user_cell = await find_user(self.username, self.sheet11)
            if user_cell is None:
                embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 필사클럽(2506)에 등록된 멤버가 아닙니다.')
                await interaction.response.edit_message(embed=embed, view=None)
                return
            user_row = user_cell.row
        except gspread.exceptions.CellNotFound:
            embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 필사클럽(2506)에 등록된 멤버가 아닙니다.')
            await interaction.response.edit_message(embed=embed, view=None)
            return

        now = datetime.now(kst).replace(tzinfo=None)  # 날짜 업데이트 코드 수정
        self.today = now.strftime('%m%d')

        # Authenticate the user in the spreadsheet
        today3_col = (await self.sheet11.find(self.today)).col
        await self.sheet11.update_cell(user_row, today3_col, '1')

        # Set the auth_event to stop the loop
        self.auth_event.set()

        # Remove the button from the view
        self.view.clear_items()

        # Send a success message
        await interaction.message.edit(embed=discord.Embed(title="인증완료!", description=f"{interaction.user.mention}님이 {self.ctx.author.mention}의 필사클럽을 인증했습니다👍"), view=None)
        self.stop_loop = True

async def update_embed_book_auth(ctx, username, today3, sheet11):
    embed = discord.Embed(title="학습인증", description=f' 버튼을 눌러 {ctx.author.mention}님의 {today3} 필사클럽을 인증해주세요')
    button = AuthButton3(ctx, username, today3, sheet11)
    view = discord.ui.View(timeout=None)
    view.add_item(button)
    message = await ctx.send(embed=embed, view=view)

    while not button.stop_loop:
        await asyncio.sleep(60)
        now = datetime.now(kst).replace(tzinfo=None)
        today3 = now.strftime('%m%d')
        if not button.stop_loop:
            view = discord.ui.View(timeout=None)
            button = AuthButton3(ctx, username, today3, sheet11)
            view.add_item(button)
            await message.edit(embed=embed, view=view)

    view.clear_items()
    await message.edit(view=view)
            
@bot.command(name='필사누적')
async def bixie_count(ctx):
    if not is_allowed_channel(ctx.channel.id):
        await ctx.send("해당 명령어는 <#1194273995319685120>에서만 사용할 수 있어요")
        return
    username = str(ctx.message.author)
    sheet11, rows = await get_sheet11()
    
    # Find the user's row in the Google Sheet
    user_row = None
    for row in await sheet11.get_all_values():
        if username in row:
            user_row = row
            break

    if user_row is None:
        embed = discord.Embed(title='Error', description=f'{ctx.author.mention}님은 필사클럽(2506)에 등록된 멤버가 아닙니다 \n !필사등록 명령어를 통해 먼저 등록해주세요!')
        await ctx.send(embed=embed)
        return

    user_cell = await sheet11.find(username)
    count = int((await sheet11.cell(user_cell.row, 2)).value)  # Column I is the 9th column

    # Send the embed message with the user's authentication count
    embed = discord.Embed(description=f"{ctx.author.mention}님은 현재까지 {count} 회 인증하셨어요!", color=0x00FF00)
    await ctx.send(embed=embed) 

#------------------------------------------------슬독------------------------------------------------------# 

# 슬독생 서버 시트 설정
async def get_sheet8():
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet8 = await spreadsheet.worksheet('슬독생')
    rows = await sheet8.get_all_values()
    return sheet8, rows 

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
        if self.values[0] == "슬독생학습인증":
            await interaction.response.send_message("슬독생 '!슬독생인증 인증하려는 날짜'를 입력해주세요! 예시)!슬독생인증 0425", ephemeral=True)
        elif self.values[0] == "슬독생누적현황":
            await interaction.response.send_message("현재까지의 슬독생 누적 인증 횟수를 조회하시려면 '!슬독생누적'을 입력해주세요! 예시)!슬독생누적", ephemeral=True)
            
@bot.command(name="")
async def sul_study(ctx):
    await ctx.message.delete()  # 명령어 삭제
    
    embed = discord.Embed(title="슬독생 명령어 모음집", description=f"{ctx.author.mention} 원하시는 명령어를 아래에서 골라주세요")
    embed.set_footer(text="이 창은 1분 후 자동 삭제됩니다")

    message = await ctx.send(embed=embed, ephemeral=True)

    select = CustomSelect(
        options=[
            discord.SelectOption(label="슬독생학습인증", value="슬독생학습인증"),
            discord.SelectOption(label="슬독생누적현황", value="슬독생누적현황")
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

class AuthButton4(discord.ui.Button):
    def __init__(self, ctx, user, date):
        super().__init__(style=discord.ButtonStyle.green, label="확인")
        self.ctx = ctx
        self.user = user
        self.date = date
        self.stop_loop = False  # Add the stop_loop attribute
    
    async def callback(self, interaction: discord.Interaction):
        
        sheet8, rows = await get_sheet8()
        
        allowed_roles = [1019165662364586034, 1003257850799341615]
        if not any(role.id in allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message("죄송합니다, 이 버튼은 권한이 없는 사용자가 클릭할 수 없습니다.", ephemeral=True)
            return
          
        if interaction.user == self.ctx.author:
            return
        existing_users = await sheet8.col_values(1)
        if str(self.user) not in existing_users:
            empty_row = len(existing_users) + 1
            await sheet8.update_cell(empty_row, 1, str(self.user))
            existing_dates = await sheet8.row_values(1)
            if self.date not in existing_dates:
                empty_col = len(existing_dates) + 1
                await sheet8.update_cell(1, empty_col, self.date)
                await sheet8.update_cell(empty_row, empty_col, "1")
            else:
                col = existing_dates.index(self.date) + 1
                await sheet8.update_cell(empty_row, col, "1")
        else:
            index = existing_users.index(str(self.user)) + 1
            existing_dates = await sheet8.row_values(1)
            if self.date not in existing_dates:
                empty_col = len(existing_dates) + 1
                await sheet8.update_cell(1, empty_col, self.date)
                await sheet8.update_cell(index, empty_col, "1")
            else:
                col = existing_dates.index(self.date) + 1
                await sheet8.update_cell(index, col, "1")
        await interaction.message.edit(embed=discord.Embed(title="인증상황", description=f"{interaction.user.mention}님이 {self.ctx.author.mention}의 {self.date} 슬독생을 인증했습니다👍"), view=None)
        self.stop_loop = True

class CancelButton4(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(style=discord.ButtonStyle.red, label="취소")
        self.ctx = ctx
        self.stop_loop = False  # Add the stop_loop attribute
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.author.id != self.ctx.author.id:
            await interaction.message.delete()
            self.stop_loop = True

async def update_embed_sul(ctx, date, msg):
    button = AuthButton4(ctx, ctx.author, date) # Move button creation outside of the loop
    cancel = CancelButton4(ctx)  # Create a CancelButton instance
    while True:
        try:
            if button.stop_loop or cancel.stop_loop: # Check if any button's stop_loop is True before updating the message
                break

            view = discord.ui.View(timeout=None)
            view.add_item(button)
            view.add_item(cancel)  # Add the CancelButton to the view

            embed = discord.Embed(title="인증요청", description=f"{ctx.author.mention}님의 {date} 슬독생 인증 요청입니다")
            await msg.edit(embed=embed, view=view)
            await asyncio.sleep(60)
        except discord.errors.NotFound:
            break
        
@bot.command(name='')
async def sul_Authentication(ctx, date=None):
    if not date:
        await ctx.send("날짜를 입력해주세요! 예) 0101")
        return

    # Validate the input date
    if not re.match(r'^(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$', date):
        await ctx.send("정확한 네자리 숫자를 입력해주세요! 1월1일 인증을 하시려면 0101을 입력하시면 됩니다 :)")
        return
    
    sheet8, rows = await get_sheet8()
    existing_users = await sheet8.col_values(1)
    if str(ctx.author) in existing_users:
        user_index = existing_users.index(str(ctx.author)) + 1
        existing_dates = await sheet8.row_values(1)
        if date in existing_dates:
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet8.cell(user_index, date_index)
            if cell_value.value == "1":
                await ctx.send(embed=discord.Embed(title="인증현황", description=f"{ctx.author.mention}님, 해당 날짜는 이미 인증되었습니다!"))
                return

    embed = discord.Embed(title="인증상태", description=f"{ctx.author.mention}님의 {date} 슬독생 인증 요청입니다")
    view = discord.ui.View()
    button = AuthButton4(ctx, ctx.author, date)
    view.add_item(button)
    view.add_item(CancelButton(ctx)) # Add the CancelButton to the view
    msg = await ctx.send(embed=embed, view=view)
    
    asyncio.create_task(update_embed_sul(ctx, date, msg))

    def check(interaction: discord.Interaction):
        return interaction.message.id == msg.id and interaction.data.get("component_type") == discord.ComponentType.button.value

    await bot.wait_for("interaction", check=check)

    
@bot.command(name='')
async def sul_count(ctx):
    sheet8, rows = await get_sheet8()
    existing_users = await sheet8.col_values(1)
    
    if str(ctx.author) not in existing_users:
        await ctx.send(f"{ctx.author.mention}님,기록이 없습니다")
        return

    user_index = existing_users.index(str(ctx.author)) + 1
    total = 0
    monday, sunday = get_week_range()
    existing_dates = await sheet8.row_values(1)
    for date in existing_dates:
        if date and monday.strftime('%m%d') <= date <= sunday.strftime('%m%d'):
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet8.cell(user_index, date_index)
            if cell_value.value:
                total += int(cell_value.value)
    
    overall_sul = await sheet8.cell(user_index, 2) # Read the value of column B
    
    embed = discord.Embed(title="누적 인증 현황", description=f"{ctx.author.mention}님, 누적 인증 횟수는 {overall_sul.value}회 입니다.")

    await ctx.send(embed=embed)

@bot.command(name='')
async def sul_attendance(ctx):
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst).replace(tzinfo=None)
    today1 = now.strftime('%m%d')

    sheet8, rows = await get_sheet8()
    existing_users = await sheet8.col_values(1)

    if str(ctx.author) not in existing_users:
        await ctx.send(f"{ctx.author.mention}님,기록이 없습니다")
        return

    user_index = existing_users.index(str(ctx.author)) + 1
    existing_dates = await sheet8.row_values(1)

    start_date = datetime(year=now.year, month=5, day=8)
    missing_dates = []
    for i in range((now - start_date).days + 1):
        date = (start_date + timedelta(days=i)).strftime('%m%d')
        if date not in existing_dates:
            missing_dates.append(date)
        elif date <= today1:  # Only consider dates up to today
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet8.cell(user_index, date_index)
            if not cell_value.value:
                missing_dates.append(date)

    attendance_rate = await sheet8.cell(user_index, 3)  # Load the value from column C

    if missing_dates:
        missing_dates_str = ', '.join(missing_dates)
        message = f"{ctx.author.mention}님, {missing_dates_str} 에 출석하지 않으셨습니다. " \
                  f"현재까지의 누적 출석률은 {attendance_rate.value} 입니다."
    else:
        message = f"{ctx.author.mention}님, 오늘 날짜기준으로 전체 출석하셨습니다. 현재까지의 누적 출석률은 {attendance_rate.value} 입니다."

    await ctx.send(message)
    
#------------------------------------------------문법사용안함------------------------------------------------------# 

# Set up Google Sheets worksheet
async def get_sheet9():
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet9 = await spreadsheet.worksheet('문법')
    rows = await sheet9.get_all_values()
    return sheet9, rows 

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
        if self.values[0] == "문법인증":
            await interaction.response.send_message("문법스터디를 인증하려면 '!문법인증 인증하려는 날짜'를 입력해주세요! 예시)!문법인증 0425", ephemeral=True)
        elif self.values[0] == "문법누적현황":
            await interaction.response.send_message("현재까지의 문법스터디 누적 인증 횟수를 조회하시려면 '!문법누적'을 입력해주세요! 예시)!문법누적", ephemeral=True)
            
@bot.command(name="")
async def gra_study(ctx):
    await ctx.message.delete()  # 명령어 삭제
    
    embed = discord.Embed(title="문법스터디 명령어 모음집", description=f"{ctx.author.mention} 원하시는 명령어를 아래에서 골라주세요")
    embed.set_footer(text="이 창은 1분 후 자동 삭제됩니다")

    message = await ctx.send(embed=embed, ephemeral=True)

    select = CustomSelect(
        options=[
            discord.SelectOption(label="문법인증", value="문법인증"),
            discord.SelectOption(label="문법누적현황", value="문법누적현황")
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

class AuthButton5(discord.ui.Button):
    def __init__(self, ctx, user, date):
        super().__init__(style=discord.ButtonStyle.green, label="확인")
        self.ctx = ctx
        self.user = user
        self.date = date
        self.stop_loop = False  # Add the stop_loop attribute
    
    async def callback(self, interaction: discord.Interaction):
        
        allowed_roles = [1019165662364586034, 1003257850799341615]
        if not any(role.id in allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message("죄송합니다, 이 버튼은 권한이 없는 사용자가 클릭할 수 없습니다.", ephemeral=True)
            return
      
        sheet9, rows = await get_sheet9()
        
        if interaction.user == self.ctx.author:
            return
        existing_users = await sheet9.col_values(1)
        if str(self.user) not in existing_users:
            empty_row = len(existing_users) + 1
            await sheet9.update_cell(empty_row, 1, str(self.user))
            existing_dates = await sheet9.row_values(1)
            if self.date not in existing_dates:
                empty_col = len(existing_dates) + 1
                await sheet9.update_cell(1, empty_col, self.date)
                await sheet9.update_cell(empty_row, empty_col, "1")
            else:
                col = existing_dates.index(self.date) + 1
                await sheet9.update_cell(empty_row, col, "1")
        else:
            index = existing_users.index(str(self.user)) + 1
            existing_dates = await sheet9.row_values(1)
            if self.date not in existing_dates:
                empty_col = len(existing_dates) + 1
                await sheet9.update_cell(1, empty_col, self.date)
                await sheet9.update_cell(index, empty_col, "1")
            else:
                col = existing_dates.index(self.date) + 1
                await sheet9.update_cell(index, col, "1")
        await interaction.message.edit(embed=discord.Embed(title="인증상황", description=f"{interaction.user.mention}님이 {self.ctx.author.mention}의 {self.date} 문법스터디를 인증했습니다👍"), view=None)
        self.stop_loop = True

class CancelButton5(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(style=discord.ButtonStyle.red, label="취소")
        self.ctx = ctx
        self.stop_loop = False  # Add the stop_loop attribute
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.author.id != self.ctx.author.id:
            await interaction.message.delete()
            self.stop_loop = True

async def update_embed_gra(ctx, date, msg):
    button = AuthButton5(ctx, ctx.author, date) # Move button creation outside of the loop
    cancel = CancelButton5(ctx)  # Create a CancelButton instance
    while True:
        try:
            if button.stop_loop or cancel.stop_loop: # Check if any button's stop_loop is True before updating the message
                break

            view = discord.ui.View(timeout=None)
            view.add_item(button)
            view.add_item(cancel)  # Add the CancelButton to the view

            embed = discord.Embed(title="인증요청", description=f"{ctx.author.mention}님의 {date} 문법스터디 인증 요청입니다")
            await msg.edit(embed=embed, view=view)
            await asyncio.sleep(60)
        except discord.errors.NotFound:
            break
        
@bot.command(name='')
async def gra_Authentication(ctx, date=None):
    if not date:
        await ctx.send("날짜를 입력해주세요! 예) 0101")
        return

    # Validate the input date
    if not re.match(r'^(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$', date):
        await ctx.send("정확한 네자리 숫자를 입력해주세요! 1월1일 인증을 하시려면 0101을 입력하시면 됩니다 :)")
        return
    
    sheet9, rows = await get_sheet9()
    existing_users = await sheet9.col_values(1)
    if str(ctx.author) in existing_users:
        user_index = existing_users.index(str(ctx.author)) + 1
        existing_dates = await sheet9.row_values(1)
        if date in existing_dates:
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet9.cell(user_index, date_index)
            if cell_value.value == "1":
                await ctx.send(embed=discord.Embed(title="인증현황", description=f"{ctx.author.mention}님, 해당 날짜는 이미 인증되었습니다!"))
                return

    embed = discord.Embed(title="인증상태", description=f"{ctx.author.mention}님의 {date} 문법스터디 인증 요청입니다")
    view = discord.ui.View()
    button = AuthButton5(ctx, ctx.author, date)
    view.add_item(button)
    view.add_item(CancelButton(ctx)) # Add the CancelButton to the view
    msg = await ctx.send(embed=embed, view=view)
    
    asyncio.create_task(update_embed_gra(ctx, date, msg))

    def check(interaction: discord.Interaction):
        return interaction.message.id == msg.id and interaction.data.get("component_type") == discord.ComponentType.button.value

    await bot.wait_for("interaction", check=check)

    
@bot.command(name='')
async def gra_count(ctx):
    sheet9, rows = await get_sheet9()
    existing_users = await sheet9.col_values(1)
    
    if str(ctx.author) not in existing_users:
        await ctx.send(f"{ctx.author.mention}님,기록이 없습니다")
        return

    user_index = existing_users.index(str(ctx.author)) + 1
    total = 0
    monday, sunday = get_week_range()
    existing_dates = await sheet9.row_values(1)
    for date in existing_dates:
        if date and monday.strftime('%m%d') <= date <= sunday.strftime('%m%d'):
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet9.cell(user_index, date_index)
            if cell_value.value:
                total += int(cell_value.value)
    
    overall_gra = await sheet9.cell(user_index, 2) # Read the value of column B
    
    embed = discord.Embed(title="누적 인증 현황", description=f"{ctx.author.mention}님, 누적 인증 횟수는 {overall_gra.value}회 입니다.")

    await ctx.send(embed=embed)



@bot.command(name='')
async def gra_attendance(ctx):
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst).replace(tzinfo=None)
    today1 = now.strftime('%m%d')

    sheet9, rows = await get_sheet9()
    existing_users = await sheet9.col_values(1)

    if str(ctx.author) not in existing_users:
        await ctx.send(f"{ctx.author.mention}님,기록이 없습니다")
        return

    user_index = existing_users.index(str(ctx.author)) + 1
    existing_dates = await sheet9.row_values(1)

    start_date = datetime(year=now.year, month=5, day=8)
    missing_dates = []
    for i in range((now - start_date).days + 1):
        date = (start_date + timedelta(days=i)).strftime('%m%d')
        if date not in existing_dates:
            missing_dates.append(date)
        elif date <= today1:  # Only consider dates up to today
            date_index = existing_dates.index(date) + 1
            cell_value = await sheet9.cell(user_index, date_index)
            if not cell_value.value:
                missing_dates.append(date)

    attendance_rate = await sheet9.cell(user_index, 3)  # Load the value from column C

    if missing_dates:
        missing_dates_str = ', '.join(missing_dates)
        message = f"{ctx.author.mention}님, {missing_dates_str} 에 출석하지 않으셨습니다. " \
                  f"현재까지의 누적 출석률은 {attendance_rate.value} 입니다."
    else:
        message = f"{ctx.author.mention}님, 오늘 날짜기준으로 전체 출석하셨습니다. 현재까지의 누적 출석률은 {attendance_rate.value} 입니다."

    await ctx.send(message)
    
#------------------------------------------------#
@bot.command(name="역할")
async def show_roles(ctx):
    roles = ctx.author.roles[1:]  # Exclude the everyone role
    embed = discord.Embed(title=f"{ctx.author.name}님의 역할입니다", color=0x00ff00)
    
    # Add each role and its icon to the embed's description
    for role in roles:
        embed.description = f"{embed.description}\n{role.name}"
        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
            
    await ctx.send(embed=embed)
  
#-----------2023어린왕자 ------------#
# 북클럽으로 시트 지정 
async def get_sheet10():  
    client_manager = gspread_asyncio.AsyncioGspreadClientManager(lambda: aio_creds)
    client = await client_manager.authorize()
    spreadsheet = await client.open('서버기록')
    sheet10 = await spreadsheet.worksheet('2024신데렐라')
    rows = await sheet10.get_all_values()
    return sheet10, rows 

async def find_user(username, sheet):
    cell = None
    try:
        cells = await sheet.findall(username)
        if cells:
            cell = cells[0]
    except gspread.exceptions.APIError as e:
        print(f'find_user error: {e}')
    return cell
            
def is_allowed_channel(channel_id):
    allowed_channels = ["929917732537909288", "1186235167262646383","1057567679281647706"]
    return str(channel_id) in allowed_channels
  
kst = pytz.timezone('Asia/Seoul') # 한국 시간대로 설정 
now = datetime.now(kst).replace(tzinfo=None)
today3 = now.strftime('%m%d') 

@bot.command(name='등록')
async def register_user(ctx):
    sheet10, rows = await get_sheet10()  # get_sheet10 호출 결과값 받기
    username = str(ctx.message.author)

    user_cell = await find_user(username, sheet10)

    if user_cell is not None:
        embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 이미 등록된 사용자입니다')
        await ctx.send(embed=embed)
        return

    # 새로운 사용자 정보 기록
    new_user_row = [username] + ["0"] * (len(rows[0]))  # 새로운 사용자 정보 생성
    await sheet10.insert_row(new_user_row, 2)  # 2행에 새로운 사용자 정보 추가

    embed = discord.Embed(title='등록 완료', description=f'{ctx.author.mention}님 2024 신데렐라-북클럽에 성공적으로 등록되었습니다')
    await ctx.send(embed=embed)

@bot.command(name='북클럽인증')
async def book_club_auth(ctx):
    required_role = "1186236303365386262" 
    role = discord.utils.get(ctx.guild.roles, id=int(required_role))
    
    if role is None or role not in ctx.author.roles:
        embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 2024 신데렐라-북클럽에 등록된 멤버가 아닙니다 \n !등록 명령어를 통해 먼저 등록해주세요!')
        await ctx.send(embed=embed)
        return
      
    sheet10, rows = await get_sheet10()  # get_sheet10 호출 결과값 받기
    username = str(ctx.message.author)

    now = datetime.now(kst).replace(tzinfo=None)  # 현재 한국 시간대의 날짜 및 시간 가져오기
    today3 = now.strftime('%m%d')  # 현재 날짜를 계산하여 문자열로 변환

    user_row = None
    for row in await sheet10.get_all_values():
        if username in row:
            user_row = row
            break

    if user_row is None:
        embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 2024 신데렐라-북클럽에 등록된 멤버가 아닙니다 \n !등록 명령어를 통해 먼저 등록해주세요!')
        await ctx.send(embed=embed)
        return

    user_cell = await find_user(username, sheet10)

    if user_cell is None:
        embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 2024 신데렐라-북클럽에 등록된 멤버가 아닙니다 \n !등록 명령어를 통해 먼저 등록해주세요!')
        await ctx.send(embed=embed)
        return

    today3_col = None
    for i, col in enumerate(await sheet10.row_values(1)):
        if today3 in col:
            today3_col = i + 1
            break

    if today3_col is None:
        embed = discord.Embed(title='Error', description=f'{ctx.author.mention}님 현재는 2024 신데렐라-북클럽 기간이 아닙니다')
        await ctx.send(embed=embed)
        return

    if (await sheet10.cell(user_cell.row, today3_col)).value == '1':
        embed = discord.Embed(title='오류', description='이미 오늘의 인증을 하셨습니다')
        await ctx.send(embed=embed)
        return
      
    await update_embed_book_auth(ctx, username, today3, sheet10)
        
class AuthButton3(discord.ui.Button):
    def __init__(self, ctx, username, today3, sheet10):
        super().__init__(style=discord.ButtonStyle.green, label="북클럽 인증")
        self.ctx = ctx
        self.username = username
        self.sheet10 = sheet10
        self.auth_event = asyncio.Event()
        self.stop_loop = False
        self.today3 = today3  # 인스턴스 변수로 today3 저장

    async def callback(self, interaction: discord.Interaction):
        if interaction.user == self.ctx.author:
            # If the user is the button creator, send an error message
            embed = discord.Embed(title='Error', description='자신이 생성한 버튼은 사용할 수 없습니다 :(')
            await interaction.response.edit_message(embed=embed, view=None)
            return

        try:
            user_cell = await find_user(self.username, self.sheet10)
            if user_cell is None:
                embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 2024 신데렐라-북클럽에 등록된 멤버가 아닙니다 \n !등록 명령어를 통해 먼저 등록해주세요!')
                await interaction.response.edit_message(embed=embed, view=None)
                return
            user_row = user_cell.row
        except gspread.exceptions.CellNotFound:
            embed = discord.Embed(title='오류', description=f'{ctx.author.mention}님은 2024 신데렐라-북클럽에 등록된 멤버가 아닙니다 \n !등록 명령어를 통해 먼저 등록해주세요!')
            await interaction.response.edit_message(embed=embed, view=None)
            return

        now = datetime.now(kst).replace(tzinfo=None)  # 날짜 업데이트 코드 수정
        self.today = now.strftime('%m%d')

        # Authenticate the user in the spreadsheet
        today3_col = (await self.sheet10.find(self.today)).col
        await self.sheet10.update_cell(user_row, today3_col, '1')

        # Set the auth_event to stop the loop
        self.auth_event.set()

        # Remove the button from the view
        self.view.clear_items()

        # Send a success message
        await interaction.message.edit(embed=discord.Embed(title="인증완료!", description=f"{interaction.user.mention}님이 {self.ctx.author.mention}의 북클럽을 인증했습니다👍"), view=None)
        self.stop_loop = True

async def update_embed_book_auth(ctx, username, today3, sheet10):
    embed = discord.Embed(title="학습인증", description=f' 버튼을 눌러 {ctx.author.mention}님의 {today3} 북클럽을 인증해주세요')
    button = AuthButton3(ctx, username, today3, sheet10)
    view = discord.ui.View(timeout=None)
    view.add_item(button)
    message = await ctx.send(embed=embed, view=view)

    while not button.stop_loop:
        await asyncio.sleep(60)
        now = datetime.now(kst).replace(tzinfo=None)
        today3 = now.strftime('%m%d')
        if not button.stop_loop:
            view = discord.ui.View(timeout=None)
            button = AuthButton3(ctx, username, today3, sheet10)
            view.add_item(button)
            await message.edit(embed=embed, view=view)

    view.clear_items()
    await message.edit(view=view)
            
@bot.command(name='북클럽누적')
async def mission_count(ctx):
    if not is_allowed_channel(ctx.channel.id):
        await ctx.send("해당 명령어는 <#1186235167262646383>에서만 사용할 수 있어요")
        return
    username = str(ctx.message.author)
    sheet10, rows = await get_sheet10()
    
    # Find the user's row in the Google Sheet
    user_row = None
    for row in await sheet10.get_all_values():
        if username in row:
            user_row = row
            break

    if user_row is None:
        embed = discord.Embed(title='Error', description=f'{ctx.author.mention}님은 2024 신데렐라-북클럽에 등록된 멤버가 아닙니다 \n !등록 명령어를 통해 먼저 등록해주세요!')
        await ctx.send(embed=embed)
        return

    user_cell = await sheet10.find(username)
    count = int((await sheet10.cell(user_cell.row, 2)).value)  # Column I is the 9th column

    # Send the embed message with the user's authentication count
    embed = discord.Embed(description=f"{ctx.author.mention}님은 현재까지 {count} 회 인증하셨어요!", color=0x00FF00)
    await ctx.send(embed=embed)    
  
#봇 실행
bot.run(TOKEN)
