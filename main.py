# -*- coding: utf-8 -*-
import re
import urllib.request

from bs4 import BeautifulSoup

from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from slack.web.classes import extract_json
from slack.web.classes.blocks import *
from slack.web.classes.elements import *
from slack.web.classes.interactions import MessageInteractiveEvent

from config import *

app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)

# 명령어 목록을 보여주는 함수
def _crawl_command(text):

    return text

# 가이드 함수
def _crawl_guide(text):
    menu = text[15:]
    # print(menu)
    if menu == '1' : # gold
        menu_url = 'guide/exp'
        title_block = SectionBlock(
            text="*ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 골드 수익 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ*"
        )
    elif menu == '2': # exp
        menu_url = 'guide/exp'
        title_block = SectionBlock(
            text="*ㅡㅡㅡㅡㅡㅡㅡ 레벨별 필요 경험치 ㅡㅡㅡㅡㅡㅡㅡ*"
        )
    elif menu == '3': # 단축키
        menu_url = 'guide/hotkeys'
        title_block = SectionBlock(
            text="*ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 단축키 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ*"
        )
    elif menu == '4': # 리롤
        menu_url = 'guide/reroll'
        title_block = SectionBlock(
            text="*ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 리롤 확률 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ*"
        )
    elif menu == '5': # 아이템 정보
        menu_url = 'items'
        title_block = SectionBlock(
            text="*ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 아이템 정보 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ*"
        )
    else: # guide 뒤에 잘못된 글자를 썼을 때
        block1 = SectionBlock(
            fields=["*Guide에는 다음과 같은 메뉴가 있습니다.*", '\n', "1.  골드", "2.  경험치", "3.  단축키", "4.  리롤 확률", "5.  아이템 정보", '\n',
                    "`@loltochessbot guide 1 or g 1`과 같은 방법으로 입력해주세요"]
        )
        return [block1]

    url = "https://lolchess.gg/" + menu_url + "?hl=ko-KR"
    req = urllib.request.Request(url)
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    # 표에 있는 데이터들 가져오기
    columns = soup.select('table > tbody > tr')
    df = []
    alltd = []
    allth = []
    for column in columns:
        ths = column.find_all("th")
        tds = column.find_all("td")
        for td in tds:
            df.append(td.text)
        for th in ths:
            allth.append(th.text)
        alltd.append(df)
        df = []
    # print(allth)
    # 글씨 굵게
    bold = []
    for i in allth:
        i = "*" + i + "*"
        bold.append(i)
    # block 만들기
    block = []
    if menu == '1':
        for i in range(0, 5):
            td = alltd[i]
            temp = SectionBlock(
                fields=[bold[i], "\n", td[0], td[1]]
            )
            block.append([temp])
        img = ImageBlock(
            image_url= "https://raw.githubusercontent.com/gahu/lolChess/master/guideImage/gold.png",
            alt_text = "응 안나와"
        )
        # 바깥의 list 제거
        message = [title_block] + [item for sublist in block for item in sublist] + [img]
    elif menu == '2':
        for i in range(19, 26):
            td = alltd[i]
            temp = SectionBlock(
                fields=[bold[i], td[0]]
            )
            block.append([temp])
        # 바깥의 list 제거
        message = [title_block] + [item for sublist in block for item in sublist]
    elif menu == '3': # 단축키
        img = ImageBlock(
            image_url="https://raw.githubusercontent.com/gahu/lolChess/master/guideImage/hotkey.png",
            alt_text="응 안나와"
        )
        message = [title_block]+[img]
    elif menu == '4': #리롤
        img = ImageBlock(
            image_url="https://raw.githubusercontent.com/gahu/lolChess/master/guideImage/reroll.png",
            alt_text="응 안나와"
        )
        message = [title_block] + [img]
    else: # 아이템
        img = ImageBlock(
            image_url="https://raw.githubusercontent.com/gahu/lolChess/master/guideImage/item.png",
            alt_text="응 안나와"
        )
        message = [title_block] + [img]

    # print(message)
    return message
# 챔피언 함수
def _crawl_champion(text):
    command = text.split(" ")
    """
    text에 담겨 들어오는 데이터
    ['<@UL9M9DUQG>', 'champion', '루시안']
    """
    # 예외처리
    if len(command[1]) > 8:
        return "champion 명령어와 챔피언 이름 사이를 띄워주세요."

    filename = "champions.txt"
    champion = ""
    # 한글 챔피언 이름 받아서 영어로 치환
    with open(filename, 'rt', encoding='UTF8') as file:
        for line in file:
            chamKo, chamEn = line.split(',')
            if command[2] == chamKo:
                champion = chamEn.replace("\n", "")
                break
            elif command[2] == chamEn:
                champion = chamEn.replace("\n", "")
                break
            else:
                continue

    if champion == "":
        return "챔피언 이름을 잘 못 입력하셨습니다.\n 확인하시고 다시 시도해주세요."

    url = "https://lolchess.gg/champions/" + champion + "?hl=ko-KR"
    req = urllib.request.Request(url)

    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    # 챔피언 이미지
    championImageBlock = ImageBlock(
        image_url="//static.lolchess.gg/images/lol/champion-splash-modified/"+champion[0].upper()+champion[1:]+".jpg",
        alt_text="캐릭터 이미지를 띄워주는 블럭"
    )

    synergies = []
    skills = []
    synergies_champ = []
    synergies_ch2 = []

    for champ in soup.find_all("div", class_="guide-champion-detail"):
        # 챔피언 이름
        name = champ.find("span", class_="guide-champion-detail__name").get_text()
        nameText = "*영웅 이름* : "+name

        detail = champ.find("div", class_="guide-champion-detail__stats-small px-3 py-2 d-md-none")
        # 챔피언 비용
        cost = detail.find("div", class_="col-4").find("div", class_="").get_text().strip()
        costText = "*비용* : "+cost+"\n"

        # 챔피언 시너지(종족, 직업)
        for dep in detail.find_all("span", class_="align-middle"):
            synergies.append(dep.get_text())
        job = "*종족, 직업* : || "
        for dep in synergies:
            job += dep+" || "

        # 종족, 직업 이미지 넣기(미완성)
        # jjongjok = ""
        # with open("synergies.txt", 'rt', encoding='UTF8') as sy:
        #     for line in sy:
        #         for jj in synergies:
        #             if line in jj:
        #                 jjongjok += line

        # jongjokBlock = ImageBlock(
        #     image_url="//static.lolchess.gg/images/tft/traiticons-white/trait_icon_"+jjongjok+".png",
        #         #         #     alt_text="jongjok"
        # )

        # 스킬
        skillText = "*스킬* : "
        skill = champ.find("div", class_="guide-champion-detail__skill")
        skillname = skill.find("strong", class_="d-block font-size-14").get_text()
        skillurl = skill.find("img", class_="guide-champion-detail__skill__icon")["src"]
        skills.append(skillname)
        skillclass = ""
        for k in skill.find("div", class_="text-gray").find_all("span"):
            skillclass += k.get_text().strip() + " "
        skills.append(skillclass)
        skilldetail = skill.find("span", class_="d-block mt-1").get_text()
        skills.append(skilldetail)
        for dep in skills:
            skillText += dep+"\n"
        skill_Image = ImageBlock(
            image_url=skillurl,
            alt_text="skill Image"
        )
        skillBlock = SectionBlock(
            text=skillText,
            accessory=skill_Image
        )

        # 시너지 챔피언
        synText = "*시너지* : \n"
        synergies_detail = champ.find("div", class_="guide-champion-detail__synergies__content")
        cnt = 0
        # tft-hexagon tft-hexagon--knight
        # 시너지 영웅들 및 이미지(미구현)
        # for c, de in enumerate(synergies_detail.find_all("span", class_="name")):
        #     if c < 6:
        #         # print("위", de.get_text())
        #         synergies_ch2.append(de.get_text())
        #     else:
        #         # print("아래", de.get_text())
        #         synergies_ch2.append(de.get_text())

        for de in synergies_detail.find_all("div", class_="text-gray"):
            synergies_champ.append(synergies[cnt])
            synergies_champ.append(de.find("strong").get_text().strip())
            for de2 in de.find_all("div", class_="guide-champion-detail__synergy__stat mt-2"):
                synergies_champ.append(de2.get_text().strip())
            cnt += 1
        for dep in synergies_champ:
            synText += dep+"\n"

        # 추천아이템
        items = "*추천 아이템* : \n|| "
        src = []
        for dep in champ.find_all("div", class_="d-inline-block mr-2"):
            items += dep.find("img")["alt"] + " || "
        # for dep in champ.find_all("div", class_="guide-champion-detail__recommend-items mt-2"):
        #     for depth in dep.find_all("img"):
        #         src.append(depth["src"])

        itemImageUrl = "https://raw.githubusercontent.com/gahu/lolChess/master/itemsImage/"+champion+".png"

        item_image_block = ImageBlock(
            image_url=itemImageUrl,
            alt_text="items"
        )
        item_text_block = SectionBlock(
            text=items
        )

        textBlock = SectionBlock(
            fields=[nameText, costText, job, synText]
        )

    return [championImageBlock, textBlock, skillBlock, item_text_block, item_image_block]

# 시너지 함수
# 크롤링 함수 구현하기
def _crawl_synergies(text):
    url = "https://lolchess.gg/synergies?hl=ko-KR"
    source_code = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source_code, "html.parser")
    # 전체 시너지 내용
    synergy_content = []
    # 시너지 옵션
    synergy_option = []
    # 시너지 효과
    synergy_effect = []
    # 요구하는 시너지 내용
    synergy_out1 =[]
    synergy_out2 =[]
    # 시너지 챔피언
    synergy_champion = []

    synergy_index ={
        0: '공허',
        1: '귀족',
        2: '닌자',
        3: '로봇',
        4: '빙하',
        5: '악마',
        6: '야생',
        7: '요들',
        8: '용',
        9: '유령',
        10: '제국',
        11: '추방자',
        12: '해적',
        13: '검사',
        14: '기사',
        15: '마법사',
        16: '수호자',
        17: '싸움꾼',
        18: '암살자',
        19: '원소술사',
        20: '정찰대',
        21: '총잡이' ,
        22: '형상변환자'
    }
    champion_index = [
    '트위스티드페이트' ,
    '가렌',
    '갱플랭크' ,
    '그레이브즈' ,
    '나르' ,
    '니달리' ,
    '다리우스',
    '드레이븐',
    '레오나',
    '렉사이' ,
    '렝가' ,
    '루시안' ,
    '룰루' ,
    '리산드라',
    '모데카이저' ,
    '모르가나' ,
    '미스포츈',
    '바루스',
    '베이가',
    '베인' ,
    '볼리베어' ,
    '브라움' ,
    '브랜드' ,
    '블리츠크랭크',
    '뽀삐',
    '세주아니',
    '쉔',
    '쉬바나' ,
    '스웨인',
    '아리',
    '아우렐리온솔',
    '아칼리',
    '아트록스',
    '애니비아',
    '애쉬',
    '야스오',
    '엘리스',
    '워윅' ,
    '이블린',
    '제드',
    '초가스',
    '카사딘',
    '카서스',
    '카직스',
    '카타리나',
    '케넨' ,
    '케일' ,
    '킨드레드',
    '트리스타나',
    '파이크',
    '피오라']
    synergy_index_en={
        0: 'void',
        1: 'noble',
        2: 'ninja',
        3: 'robot',
        4: 'glacial',
        5: 'demon',
        6: 'wild',
        7: 'yordle',
        8: 'dragon',
        9: 'phantom',
        10: 'imperial',
        11 : 'exile',
        12: 'pirate',
        13: 'blademaster',
        14: 'knight',
        15: 'sorcerer',
        16: 'guardian',
        17: 'brawler',
        18: 'assassin',
        19: 'elementalist',
        20: 'ranger',
        21: 'gunslinger',
        22: 'shapeshifter',
    }


    #시너지 모든 효과 & 옵션 크롤링
    for contents in soup.find_all("div", class_="guide-synergy__content"):
        for effect in contents.find_all("div", class_="guide-synergy__description"):
            synergy_effect.append('*시너지* : ' + effect.get_text().replace('\n', ''))
        if synergy_effect == []:
            synergy_effect.append('')
        for option in contents.find_all("div", class_="guide-synergy__stats"):
            synergy_option.append('*세부사항* : ' + option.get_text().replace('\n', ''))
        for champion in contents.find_all("div",class_="guide-synergy__champions"):
            synergy_champion.append('*챔피언* :' + champion.get_text().replace('\n', '').replace('$',',')
                                    .replace('1',' ').replace('2',' ').replace('3',' ').replace('4',' ').replace('5',' '))

        #모든내용 synergy_content에 담는다.
        synergy_content.append(synergy_effect + synergy_option + synergy_champion)

        synergy_option = []
        synergy_effect = []
        synergy_champion =[]
        synergy_count = []
        synergy_url = []  # 고친부분
    #print(synergy_content) :총 시너지 내용

    command = text.split()
    print(command)

    message =[]
    bin = False
    #입력받은 text에서 시너지 이름 나오면 옵션, 효과, 해당 챔피언 리턴
    for idx in range(len(synergy_index)):
            for cmd in range(len(command)):
                if synergy_index[idx] in command[cmd]:
                    bin = True
                    print(synergy_index[idx] + " " + command[cmd])
                    synergy_out1.append('*'+ synergy_index[idx] +'*')
                    synergy_out1.append(synergy_content[idx][0])
                    synergy_url.append(synergy_index_en[idx])  # 고친부분
                    if synergy_content[idx][0]=='':
                        synergy_out1.pop()
                    synergy_out1.append(synergy_content[idx][1])
                    synergy_out1.append(synergy_content[idx][2][:7] + synergy_content[idx][2][8:])
                    synergy_out1.append('')
                    synergy_out3 ='a'

                    img_src = ImageElement(
                        image_url="//static.lolchess.gg/images/tft/traiticons-darken/trait_icon_" +synergy_index_en[idx] + ".png",
                        alt_text="keyword"
                        )
                    message.append(
                        SectionBlock(
                            text='\n'.join(synergy_out1),
                            accessory=img_src
                        )
                    )
                    synergy_out1 =[]
            if bin:
                synergy_out2.append("")

    # 시너지 카운트
    # for idx in range(len(champion_index)):

    # print(champion_index)
    # for idx in range(len(champion_index)):
    #     for cmd in range(len(command)):
    #         if champion_index[idx] in command[cmd]:

    for cnt in range(len(champion_index)):
        for cmd in range(len(command)):
            if champion_index[cnt] in command[cmd]: #가렌이 있어!-> 시너지 찾아
                for i in range(len(synergy_content)):
                    if champion_index[cnt] in synergy_content[i][2]:
                        # print(synergy_index[i])
                        synergy_count.append(synergy_index[i]) #시너지 다 가져왔어

    count_list = [0 for i in range(23)]
    if len(synergy_count) >0:
        synergy_out2.append('*보유하고 있는 챔피언 시너지*')
        synergy_out2.append('(시너지 : 챔피언 수)')
        #각 시너지가 몇개인지 체크
        for i in range(len(synergy_count)):
            for j in range(len(synergy_index)):
                # print(synergy_index[j])
                if synergy_count[i] == synergy_index[j]:
                    count_list[j] += 1
        #1개 이상이면 출력
        for i in range(23):
            if count_list[i] > 0:
                synergy_out2.append(synergy_index[i]+ ' : ' + str(count_list[i]))

    if synergy_out2 == []:
        synergy_out2.append("제공할 시너지 정보가 없습니다. 다시 입력해 주세요")

    message.append(
        SectionBlock(
            text='\n'.join(synergy_out2)
        )
    )
    print((synergy_content[4][2]))
    # return '\n'.join(synergy_out)

    return message

# 예외처리
def _crawl_else():
    title_block = SectionBlock(
        text = "*LoLChess의 기능과 단축키는 다음과 같습니다*\n"
    )
    s_block = SectionBlock(
        fields = ["*1. 챔피언 정보*","@loltochessbot c 챔피언 이름","*2. 시너지 정보*", "@loltochessbot s 귀족 or 챔피언 이름","*3. 가이드*", "@loltochessbot g (1 ~ 5)"]
    )
    message = [title_block] + [s_block]
    return message

# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]

    if text[13:] == 'command':
        message = _crawl_command(text)
        slack_web_client.chat_postMessage(
            channel=channel,
            text="명령어 목록"
        )
    elif text[13:14] == "g":
        message = _crawl_guide(text)
        print(message)
        slack_web_client.chat_postMessage(
            channel=channel,
            blocks= extract_json(message)
        )
    elif text[13:14] == "c":
        messageBlock = _crawl_champion(text)
        slack_web_client.chat_postMessage(
            channel=channel,
            blocks=extract_json(messageBlock)
        )
    elif text[13:14] == "s":
        message = _crawl_synergies(text)
        slack_web_client.chat_postMessage(
            channel=channel,
            # text=message
            blocks=extract_json(message)
        )
    else:
        message = _crawl_else()
        print(message)
        slack_web_client.chat_postMessage(
            channel = channel,
            blocks = extract_json(message)
        )


# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
