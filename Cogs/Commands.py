import sys
import subprocess

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View

from datetime import datetime, timedelta
from collections import deque
import asyncio

from rw_json import read_write_json_class
from typing import List

try:
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.schedulers.background import BackgroundScheduler
except:
    subprocess.check_call([sys.executable,'-m', 'pip', 'install', '--upgrade', 'apscheduler'])
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.schedulers.background import BackgroundScheduler


'''
`   게임 내 아이템 경매 시스템
    참가 인원 100명 이상

    매주 2회 (수요일, 토요일) 24시간 진행
    추가 입찰 최소 다이아 100개
    경매 마감 1시간 전(11시) 추가 입찰자가 있을 경우, 마지막 입찰가에서 추가 경매 진행

    마감 mm분 전 알림 기능

    [완료] 날짜 date_list는 봇을 켰을 때와 매일 자정에 갱신
    [완료] item.json의 용량이 커지는 문제 해결

    [ 명령어 셋 ]

    날짜 set : 2024-03-13

    [관리자] 경매 채널 지정 <채널이름>

    [관리자] 경매 아이템 추가 <아이템이름> <날짜> 
    [관리자] 경매 아이템 제거 <아이템이름> (자동완성)>
    [관리자] 경매 아이템 현황 
    
'''

class Commands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.edit_data = deque([])

        self.json_keys = f'{datetime.now().date()} ({"수요일" if datetime.now().isoweekday() == 3 else "토요일"})'

        self.channel = None # 경매 채널
        self.on_auction = False # 경매 중 검사
        self.embed_obejct = None

        read_write_json_class.command_self_data = self
        self.bot.loop.create_task(self.update_date_list())

        self.sched = BackgroundScheduler()
        self.sched.start()

        self.sched.add_job(lambda: self.bot.loop.create_task(self.set_json()), CronTrigger(hour='0', minute='0'))
        self.sched.add_job(lambda: self.bot.loop.create_task(self.alarm()), CronTrigger(hour='23'))
    
# ----------------------------[ 임베드 생성 ]----------------------------------------
        
    async def make_embed(self, title, sub_ttle, color):
        embed = discord.Embed(title=f"{title}", description=f"{sub_ttle}", color=color)
        embed.set_footer(text="TIMESTEAMP")
        embed.timestamp = datetime.now()
        return embed 
    
    async def make_embeds(self, keys:str):
        embeds = []
        temp = 0
        string = "---------- [ 경매 물품 ] ----------\n"
        for idx, (k, v) in enumerate(read_write_json_class.item[keys].copy().items(), start=1):
            inv_string = f"{idx}. {k} - {v[0]} 다이아\n"

            if len(string) + len(inv_string) > 2000:
                if temp == 0:
                    embed = discord.Embed(title="📢 │ 경매가 시작되었습니다!", description=f"{string}", color=0x237feb)
                else:
                    embed = discord.Embed(title="", description=f"{string}", color=0x237feb)
                temp += 1
                embeds.append(embed)
                string = inv_string
            else:
                string += inv_string

        if temp == 0:
            embed = discord.Embed(title="📢 │ 경매가 시작되었습니다!", description=f"{string}", color=0x237feb)
            embeds.append(embed)
        
        return embeds

    async def make_prize_embed(self):
        
        embeds = []
        temp = 0
        string = "---------- [ 경매 결과 ] ----------\n"

        json_keys = f'{(datetime.now() - timedelta(days=1)).date()} ({"수요일" if datetime.now().isoweekday() == 3 else "토요일"})'
        for idx, (k, v) in enumerate(read_write_json_class.item[json_keys].copy().items(), start=1):
            if v[1] is not None:
                user_object = self.bot.get_user(int(v[1]))
                inv_string = f"{idx}. {k} - {user_object.display_name} ({user_object.mention}) ({v[0]} 다이아)\n"
            else:
                inv_string = f"{idx}. {k} - 경매자 없음\n"

            if len(string) + len(inv_string) > 2000:
                if temp == 0:
                    embed = discord.Embed(title="📢 │ 경매 결과 발표!", description=f"{string}", color=0x237feb)
                else:
                    embed = discord.Embed(title="", description=f"{string}", color=0x237feb)
                temp += 1
                embeds.append(embed)
                string = inv_string
            else:
                string += inv_string

        if temp == 0:
            embed = discord.Embed(title="📢 │ 경매 결과 발표!", description=f"{string}", color=0x237feb)
            embeds.append(embed)
        
        return embeds
  
    async def embed_edit_loop(self):
        try:
            while True:
                if self.edit_data:
                    self.edit_data = deque([])
                    auction_embeds = await self.make_embeds(self.json_keys)
                    await self.embed_obejct.edit(embeds=auction_embeds)
                await asyncio.sleep(2)
        except:
            await asyncio.sleep(2)
            

# ----------------------------[ 서브 함수 ]----------------------------------------
    
    async def set_channel(self, channel_obejct:discord.TextChannel):
        self.channel = channel_obejct

        if read_write_json_class.system["channel_id"] == None:
            await self.set_json()
        read_write_json_class.system["channel_id"] = channel_obejct.id 
        read_write_json_class.write_json("system", read_write_json_class.system)

    async def get_date_list(self):
        return self.date_list
    
    async def make_datelist(self):
        data_list = []
        first_date = datetime.now()

        for i in range(1, 91):
            trans_date = first_date + timedelta(days=i)
            if trans_date.isoweekday() == 3:
                data_list.append(f"{trans_date.date()} (수요일)")
            elif trans_date.isoweekday() == 6:
                data_list.append(f"{trans_date.date()} (토요일)")

        return data_list
 
    async def item_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        choices = []
        real_choices = []
        if self.on_auction:
            if read_write_json_class.item[self.json_keys]:
                for k, v in read_write_json_class.item[self.json_keys].copy().items():
                    choices.append(f"{k} - {v[0]} 다이아")
                    real_choices.append(f"{k}")
                choices = [app_commands.Choice(name=choices[idx], value=real_choices[idx]) for idx, choice in enumerate(choices) if current.lower() in choice.lower()][:25]
        return choices

# ----------------------------[ 11시에 일어나는 함수 ]----------------------------------------
    
    async def alarm(self):
        if self.on_auction:
            embed = await self.make_embed("📢 │ 경매 마감 1시간 전!", "경매가 1시간 뒤에 마감됩니다!\n\n경매 채널에서 /입찰 명령어를 통해 입찰을 진행해 주세요!", 0x237feb)
            for member in self.channel.guild.members:
                if not member.bot:
                    await member.send(embed=embed)
    
# ----------------------------[ 자정에 일어나는 함수 ]----------------------------------------
  
    async def update_date_list(self):
        ''' 매일 자정, 자동 완성 및 조건 검색을 위한 date_list를 초기화합니다. '''

        self.date_list = await self.make_datelist()

    async def clear_item_json(self):
        ''' 매일 자정, item.json에서 일자가 지난 데이터를 제거합니다. '''
        
        for k, v in read_write_json_class.item.copy().items():
            try:
                date = (datetime.fromisoformat(k[:10])).date()
                if datetime.now().date() > date:
                    del read_write_json_class.item[k]
                    read_write_json_class.write_json("item", read_write_json_class.item)
                else:
                    return
            except:
                del read_write_json_class.item[k]
                read_write_json_class.write_json("item", read_write_json_class.item)

    async def clear_embeds(self):
        if self.embed_obejct is None:
            self.embed_obejct = await self.channel.fetch_message(int(read_write_json_class.embeds["embeds_id"])) 
        await self.embed_obejct.delete()

        read_write_json_class.embeds["embeds_id"] = None
        read_write_json_class.write_json("embeds", read_write_json_class.embeds)
        self.embed_obejct = None

    async def send_embeds(self, keys:str):
        auction_embeds = await self.make_embeds(keys)
        self.embed_obejct = await self.channel.send(embeds=auction_embeds)
        self.on_auction = True

        read_write_json_class.embeds["embeds_id"] = self.embed_obejct.id
        read_write_json_class.write_json("embeds", read_write_json_class.embeds)

        read_write_json_class.system["lasted_embed_date"] = self.json_keys
        read_write_json_class.write_json("system", read_write_json_class.system)
        
    async def set_json(self):
        '''
            update_date_list -> clear_item_json -> clear_embeds -> send_embeds

            1. 90일 데이터 리스트 재배열
            2. 일자가 지난 json 키값 제거
            
            < 조건 검사 삭제할 임베드 존제 >
            3. 임베드 삭제

            < 조건 검사 수요일 또는 금요일 >
            4. 임베드 출력
        '''
        self.json_keys = f'{datetime.now().date()} ({"수요일" if datetime.now().isoweekday() == 3 else "토요일"})'
        self.date_list = await self.make_datelist()
        await self.clear_item_json()

        if read_write_json_class.embeds["embeds_id"] != None:
            await self.clear_embeds()

        if datetime.now().isoweekday() == 3 or datetime.now().isoweekday() == 6:
            if self.json_keys in read_write_json_class.item and read_write_json_class.item[self.json_keys] and self.channel != None:
                await self.send_embeds(self.json_keys)

            else:
                if self.json_keys not in read_write_json_class.item or not read_write_json_class.item[self.json_keys]:
                    print(f"[{datetime.now().replace(microsecond=0)}] 등록된 경매 상품이 없어 경매를 열지 않습니다.")
                else:
                    print(f"[{datetime.now().replace(microsecond=0)}] 경매 채널이 설정되어 있지 않아 경매를 열지 않습니다.")
        
        if self.json_keys != read_write_json_class.system["lasted_embed_date"] and self.on_auction is True and self.channel != None:
            embeds = await self.make_prize_embed()
            await self.channel.send(embeds=embeds)
            self.on_auction = False

# ----------------------------[ 메인함수 ]----------------------------------------

    @app_commands.command(name="입찰", description='경매 아이템 입찰을 진행합니다.')
    @app_commands.describe(경매상품='경매 아이템 이름을 입력합니다.')
    @app_commands.autocomplete(경매상품=item_autocomplete)
    @app_commands.describe(경매가='경매가를 입력합니다.')
    async def command_1(self, interaction: discord.Interaction, 경매상품:str, 경매가:int) -> None:
        await interaction.response.defer(ephemeral=True)

        if not self.on_auction:
            embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"현재 경매 중이 아닙니다.", 0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if self.json_keys not in read_write_json_class.item or 경매상품 not in list(read_write_json_class.item[self.json_keys].keys()):
            embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"현재 일자 ({self.json_keys})에 경매 상품이 없습니다.", 0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if read_write_json_class.item[self.json_keys][경매상품][0] + 100 > 경매가:
            max_dia = read_write_json_class.item[self.json_keys][경매상품][0] + 100

            embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"입력한 경매가 ({경매가} 다이아)가 최고가 ({max_dia} 다이아) 보다 작습니다.", 0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        read_write_json_class.item[self.json_keys][경매상품] = [경매가, interaction.user.id]
        read_write_json_class.write_json("item", read_write_json_class.item)

        embed = await self.make_embed("♦️ │ 최고가 갱신!", f"◇ 아이템 : {경매상품}\n◆ 최고가 : {경매가} 다이아 ( {interaction.user.nick if interaction.user.nick else interaction.user.display_name} ({interaction.user.mention}))\n\n▶ 다음 경매 최고가 갱신가는 {경매가+100} 다이아 이상부터 입니다.\n◆ 이 아이템의 경매를 원하신다면 /경매 {경매상품} <가격> 을 입력해 주세요.", 0xff0000)
        embed.set_footer(text="TIMESTEAMP")
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed, ephemeral=True)

        self.edit_data.append(True)
        return

    @commands.Cog.listener()
    async def on_ready(self):
        if read_write_json_class.system["channel_id"] != None:
            self.channel = self.bot.get_channel(int(read_write_json_class.system["channel_id"]))
            print(f"경매 채널 지정 완료 : {self.channel.name}")
        else:
            print("[경고] /경매 채널 명령어를 통해 경매 채널을 지정해 주세요.")

        self.bot.loop.create_task(self.embed_edit_loop())
        await self.set_json()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        pass

async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(Commands(bot))