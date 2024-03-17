from discord import app_commands, Permissions
from discord.ext import commands
import discord

from datetime import datetime, timedelta
from rw_json import read_write_json_class

from typing import List
from Cogs import Commands

@app_commands.guild_only()
class Group(app_commands.Group):

# ----------------------------[ 자동완성 및 보조 함수 ]----------------------------------------

    async def make_embed(self, title, sub_ttle, color):
        embed = discord.Embed(title=f"{title}", description=f"{sub_ttle}", color=color)
        embed.set_footer(text="TIMESTEAMP")
        embed.timestamp = datetime.now()
        return embed 

    async def date_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        choices = await Commands.Commands.get_date_list(read_write_json_class.command_self_data)
        choices = [app_commands.Choice(name=choice, value=choice) for choice in choices if current.lower() in choice.lower()][:25]
        return choices

    async def item_name_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        choices = []
        for k, v in read_write_json_class.item.copy().items():
            for p, _ in v.copy().items():
                choices.append(f"{p} ({k})")
        choices = [app_commands.Choice(name=choice, value=choice) for choice in choices if current.lower() in choice.lower()][:25]
        return choices
    
# ----------------------------[ 메인 함수 ]----------------------------------------
    
    @app_commands.command(description="[관리자] 경매 채널을 지정합니다.")
    @app_commands.describe(채널='경매 채널을 지정합니다.')
    async def 채널(self, interaction: discord.Interaction, 채널:discord.TextChannel) -> None:
        await interaction.response.defer(ephemeral=True)

        await Commands.Commands.set_channel(read_write_json_class.command_self_data, 채널)
        embed = await self.make_embed("🧾 │ 경매 채널 지정 완료", f"경매 채널을 {채널.name} ({채널.mention}) 으로 설정했습니다.", 0xe9c724)
        await interaction.followup.send(embed=embed, ephemeral=True)

    group2 = app_commands.Group(name="아이템", description="경매 아이템을 편집합니다.")
    
    @group2.command(description="[관리자] 새로운 경매 일정을 등록합니다.")
    @app_commands.describe(상품이름='상품이름을 입력합니다.')
    @app_commands.autocomplete(날짜=date_autocomplete)
    @app_commands.describe(날짜='날짜를 선택합니다.')
    async def 등록(self, interaction: discord.Interaction, 상품이름:str, 날짜:str) -> None:
        await interaction.response.defer(ephemeral=True)

        try:           
            상품이름 = 상품이름.strip()
            date_list = await Commands.Commands.get_date_list(read_write_json_class.command_self_data)
            if 날짜 not in date_list:
                embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"해당 날짜 ({날짜})(은)는 등록할 수 없습니다.\n보기의 날짜 중에서 선택해 주세요.", 0xff0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if 날짜 in read_write_json_class.item and 상품이름 in read_write_json_class.item[날짜].keys():
                embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"해당 날짜 ({날짜})에 해당 아이템 ({상품이름}) 이 이미 등록되어 있습니다.", 0xff0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if 날짜 not in read_write_json_class.item:
                read_write_json_class.item[날짜] = {}
                read_write_json_class.write_json("item", read_write_json_class.item)
            
            read_write_json_class.item[날짜][상품이름] = [0, None]
            read_write_json_class.write_json("item", read_write_json_class.item)

            embed = await self.make_embed("📜 │ 등록 완료", f"경매 물품 등록 명세서\n\n◇ date : {날짜}\n◇ item : {상품이름}", 0x514fc5)  
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"경매 아이템 등록 명령어에서 오류가 발생했습니다. : {e}")
            await interaction.followup.send(f"경매 아이템 등록 명령어에서 오류가 발생했습니다. : {e}")

    @group2.command(description="[관리자] 등록된 경매 일정을 제거합니다.")
    @app_commands.describe(상품이름='상품이름을 입력합니다.')
    @app_commands.autocomplete(상품이름=item_name_autocomplete)
    async def 제거(self, interaction: discord.Interaction, 상품이름:str) -> None:
        await interaction.response.defer(ephemeral=True)

        try:
            item_name, date = 상품이름[:-18].strip(), (상품이름[-18:])[1:-1]
            if date in read_write_json_class.item and item_name in read_write_json_class.item[date]:

                del read_write_json_class.item[date][item_name]
                read_write_json_class.write_json("item", read_write_json_class.item)

                embed = await self.make_embed("🧾 │ 제거 완료", f"경매 물품 제거 명세서\n\n◇ date : {date}\n◇ item : {item_name}", 0x514fc5)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return 
            else:
                embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"해당 아이템을 찾을 수 없습니다.", 0xff0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        except Exception as e:
            print(f"경매 아이템 제거 명령어에서 오류가 발생했습니다. : {e}")
            await interaction.followup.send(f"경매 아이템 제거 명령어에서 오류가 발생했습니다. : {e}")

    @group2.command(description="[관리자] 등록된 경매 일정을 확인합니다.")
    @app_commands.autocomplete(날짜=date_autocomplete)
    @app_commands.describe(날짜='날짜를 선택합니다.')
    async def 현황(self, interaction: discord.Interaction, 날짜:str) -> None:
        await interaction.response.defer(ephemeral=True)

        try:
            date_list = await Commands.Commands.get_date_list(read_write_json_class.command_self_data)
            if 날짜 not in date_list:
                embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"해당 날짜 ({날짜})(은)는 등록할 수 없습니다.\n보기의 날짜 중에서 선택해 주세요.", 0xff0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if 날짜 not in read_write_json_class.item or not read_write_json_class.item[날짜]:
                embed = await self.make_embed("⚠️ │ 오류가 발생했습니다.", f"해당 일자에 등록된 아이템이 없습니다.", 0xff0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            string = f"일자 : {날짜}\n\n"
            for idx, (k, _) in enumerate(read_write_json_class.item[날짜].copy().items(), start=1):
                string += f"{idx}. {k}\n"

            embed = await self.make_embed("📊 │ 경매 아이템 현황", string, 0xff3d00)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"경매 아이템 현황 명령어에서 오류가 발생했습니다. : {e}")
            await interaction.followup.send(f"경매 아이템 현황 명령어에서 오류가 발생했습니다. : {e}")
        
async def setup(bot: commands.Bot):
    bot.tree.add_command(Group(name="경매", description="경매 관련 명령어 모음", default_permissions=Permissions(administrator=True)))
