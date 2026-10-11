"""prayers_source.txt -> guide-data.json / guide-data.js 변환 스크립트
마크업 규칙
  @@ id        : 항목 시작 (다음 줄 = 제목)
  =텍스트      : 소제목(heading)
  #텍스트      : 전례 지시(rubric, 예: 꿇는다)
  ~텍스트      : 괄호 안내(note, 예: 성모송)
  >텍스트      : 인용(성경 구절)
  L| A| 1| 2|  : 역할 — L=주례(十/†), A=다같이(◎), 1=○편, 2=●편
  *라벨|본문   : 묵주기도 신비(단)
  %처|제목|묵상기도[|지시] : 십자가의 길 각 처
  $경로|설명  : 이미지(악보)
  !WEEKLY      : 요일별 독서 삽입 위치
  접두어 없는 줄 : 앞 화자 계속(continuation) 또는 일반 문단
"""
import json, re, sys, pathlib

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])

# 원문 오탈자 교정 (원문 → 교정) : 앱에는 교정본 사용, 목록은 정리문서에 기록
FIXES = [
    ("자비를 베프소서", "자비를 베푸소서"),
    ("단죄하지 않의시고", "단죄하지 않으시고"),
    ("어떠힌 어려움", "어떠한 어려움"),
    ("예수님의 도음 없이는", "예수님의 도움 없이는"),
    ("많은 고날을", "많은 고난을"),
    ("제 입시 울을", "제 입술을"),
    ("귀를 귀울이고", "귀를 기울이고"),
    ("내려 주시를 비오니", "내려 주시기를 비오니"),
    ("A|아멘.,", "A|아멘."),
    ("하느님，아침", "하느님, 아침"),
    ("우리 주그리스도를", "우리 주 그리스도를"),
    ("주님께서는길 잃은", "주님께서는 길 잃은"),
    ("주님께서는회개한", "주님께서는 회개한"),
    ("영원히 . 아멘", "영원히. 아멘"),
]

META = {
 "gj_cur_pray001": ("morning",   "기도",     "아침기도",                 7),
 "gj_cur_pray006": ("open-close","기도",     "시작기도 / 마침기도",       14),
 "gj_cur_pray002": ("rosary",    "기도",     "묵주기도",                 18),
 "gj_cur_pray003": ("evening",   "기도",     "저녁기도와 양심성찰",       25),
 "gj_cur_pray005": ("cursillista-prayer","기도","꾸르실리스따의 기도",   101),
 "gj_cur_medi01":  ("meditation","묵상·십자가의 길","묵상",              13),
 "gj_cur_pray004": ("stations",  "묵상·십자가의 길","십자가의 길 (꾸르실리스따용)", 66),
 "gj_cur_sado":    ("apostle-hour","성체강복 · 사도의 시간","사도의 시간",      28),
 "gj_benediction": ("benediction","성체강복 · 사도의 시간","성체강복",       39),
 "gj_cur_refl01":  ("reflection","성체강복 · 사도의 시간","꾸르실리스따의 성찰", 89),
 "gj_cur_meeting": ("ultreya",   "회합",     "울뜨레야 순서",            None),
 "gj_cur_team":    ("team",      "회합",     "팀 회합",                  None),
 "gj_cur_sunle_s": ("pilgrim-start","순례기도·연도","순례의 길을 떠나면서 바치는 기도", None),
 "gj_cur_sunle_e": ("pilgrim-end","순례기도·연도","순례의 길을 마치면서 바치는 기도", None),
 "gj_cur_sunle_p": ("martyrs",   "순례기도·연도","한국 순교자들에게 바치는 기도", None),
 "gj_cur_y-do":    ("yeondo",    "순례기도·연도","연도",                 None),
}

def parse(lines):
    blocks, last = [], None
    for ln in lines:
        ln = ln.rstrip()
        if not ln: continue
        if ln == "!WEEKLY":
            blocks.append({"type": "weekly"}); last = None; continue
        c = ln[0]
        if c == "=": blocks.append({"type": "heading", "text": ln[1:].strip()}); last=None; continue
        if c == "#": blocks.append({"type": "rubric", "text": ln[1:].strip()}); last=None; continue
        if c == "~": blocks.append({"type": "note", "text": ln[1:].strip()}); last=None; continue
        if c == ">": blocks.append({"type": "quote", "text": ln[1:].strip()}); last=None; continue
        if c == "^":                       # 절(①②…) — 새 블록으로 시작, 다음 줄은 이어 붙임
            blk = {"type": "line", "role": None, "text": [ln[1:]]}
            blocks.append(blk); last = blk; continue
        if c == "$":                       # 악보 이미지: $경로|설명
            src, _, cap = ln[1:].partition("|")
            blocks.append({"type": "image", "src": src, "caption": cap}); last=None; continue
        if c == "*":
            lab, txt = ln[1:].split("|", 1)
            blocks.append({"type": "mystery", "label": lab, "text": txt}); last=None; continue
        if c == "%":
            parts = ln[1:].split("|")
            st = {"type": "station", "no": int(parts[0]), "title": parts[1], "prayer": parts[2]}
            if len(parts) > 3: st["rubric"] = parts[3]
            blocks.append(st); last=None; continue
        m = re.match(r"^([LA12])\|(.*)$", ln)
        if m:
            b = {"type": "line", "role": m.group(1), "text": [m.group(2)]}
            blocks.append(b); last = b; continue
        if last is not None:
            last["text"].append(ln)          # 같은 화자 계속
        else:
            b = {"type": "line", "role": None, "text": [ln]}
            blocks.append(b); last = b
    for b in blocks:
        if b.get("type") == "line": b["text"] = "\n".join(b["text"])
    return blocks

raw = SRC.read_text(encoding="utf-8")
applied = []
for a, b in FIXES:
    n = raw.count(a)
    if n: raw = raw.replace(a, b); applied.append({"from": a, "to": b, "count": n})

items, weekly = [], {}
for chunk in raw.split("@@ ")[1:]:
    lines = chunk.split("\n")
    key, title = lines[0].strip(), lines[1].strip()
    if key.startswith("week_"):
        d = int(key[5:])
        ref = re.search(r"\((.*)\)", title).group(1)
        weekly[d] = {"day": title.split("(")[0].strip(), "ref": ref, "text": " ".join(l for l in lines[2:] if l.strip())}
        continue
    iid, cat, ttl, page = META[key]
    items.append({"id": iid, "category": cat, "title": ttl, "page": page,
                  "source": (None if key == "gj_benediction" else f"https://imdong.or.kr/m/{key}.html"), "blocks": parse(lines[2:])})

# 길잡이에서 '(성모송)' 등으로만 표기된 공통기도 — 사이트에 본문 없음 → 보충 (책자 대조 필요)
common = [
 {"id": "sign-of-cross", "title": "성호경", "text": "성부와 성자와 성령의 이름으로. 아멘."},
 {"id": "our-father", "title": "주님의 기도", "text": "하늘에 계신 우리 아버지, 아버지의 이름이 거룩히 빛나시며 아버지의 나라가 오시며 아버지의 뜻이 하늘에서와 같이 땅에서도 이루어지소서. 오늘 저희에게 일용할 양식을 주시고 저희에게 잘못한 이를 저희가 용서하오니 저희 죄를 용서하시고 저희를 유혹에 빠지지 않게 하시고 악에서 구하소서. 아멘."},
 {"id": "hail-mary", "title": "성모송", "text": "은총이 가득하신 마리아님, 기뻐하소서. 주님께서 함께 계시니 여인 중에 복되시며 태중의 아들 예수님 또한 복되시나이다. 천주의 성모 마리아님, 이제와 저희 죽을 때에 저희 죄인을 위하여 빌어주소서. 아멘."},
 {"id": "glory-be", "title": "영광송", "text": "영광이 성부와 성자와 성령께, 처음과 같이 이제와 항상 영원히. 아멘."},
 {"id": "fatima", "title": "구원을 비는 기도", "text": "예수님, 저희 죄를 용서하시며 저희를 지옥 불에서 구하시고 연옥 영혼을 돌보시며 가장 버림받은 영혼을 돌보소서."},
 {"id": "creed", "title": "사도신경", "text": "전능하신 천주 성부 천지의 창조주를 저는 믿나이다. 그 외아들 우리 주 예수 그리스도님, 성령으로 인하여 동정 마리아께 잉태되어 나시고, 본시오 빌라도 통치 아래서 고난을 받으시고, 십자가에 못박혀 돌아가시고 묻히셨으며, 저승에 가시어 사흗날에 죽은 이들 가운데서 부활하시고, 하늘에 올라 전능하신 천주 성부 오른편에 앉으시며, 그리로부터 산 이와 죽은 이를 심판하러 오시리라 믿나이다. 성령을 믿으며, 거룩하고 보편된 교회와 모든 성인의 통공을 믿으며, 죄의 용서와 육신의 부활을 믿으며 영원한 삶을 믿나이다. 아멘."},
]

songs = [
 {"id": "de-colores",  "title": "데 꼴로레스",   "page": 108, "use": "울뜨레야 마침성가",
  "sheet": "https://imdong.or.kr/m/music/sheet/de_colores.jpg",  "audio": "https://imdong.or.kr/m/music/de_colores.mp3",  "source": "https://imdong.or.kr/m/gj_de_colores01.html"},
 {"id": "cursillista", "title": "꾸르실리스따",   "page": 112, "use": "울뜨레야 시작성가",
  "sheet": "https://imdong.or.kr/m/music/sheet/cursillista.jpg", "audio": "https://imdong.or.kr/m/music/cursillista.mp3", "source": "https://imdong.or.kr/m/gj_cursillista01.html"},
 {"id": "christian",   "title": "크리스찬 정신", "page": 114, "use": None,
  "sheet": "https://imdong.or.kr/m/music/sheet/christian.jpg",   "audio": "https://imdong.or.kr/m/music/christian.mp3",   "source": "https://imdong.or.kr/m/gj_christian01.html"},
 {"id": "manyanita",   "title": "마냐니따",       "page": 115, "use": None,
  "sheet": "https://imdong.or.kr/m/music/sheet/manyanita.jpg",   "audio": "https://imdong.or.kr/m/music/manyanita.mp3",   "source": "https://imdong.or.kr/m/gj_manyanita01.html"},
]

links = [
 {"title": "가톨릭 주요기도문", "url": "#/prayers"},
 {"title": "오늘의 미사 (굿뉴스)", "url": "https://maria.catholic.or.kr/mobile/missa/missa_view.asp?today=on"},
]

data = {
 "meta": {"title": "꾸르실료 길잡이", "publisher": "광주대교구 꾸르실료사무국",
          "source": "https://imdong.or.kr/m/gj_cur_menu.html", "collected": "2026-10-11",
          "roles": {"L": "十 주례/선창", "A": "◎ 다같이", "1": "○ 왼편(1그룹)", "2": "● 오른편(2그룹)"}},
 "categories": ["기도", "묵상·십자가의 길", "성체강복 · 사도의 시간", "회합", "순례기도·연도"],
 "items": items, "weeklyReadings": [weekly[i] for i in range(7)],
 "commonPrayers": common, "songs": songs, "links": links, "fixesApplied": applied,
}
OUT.mkdir(parents=True, exist_ok=True)
js = json.dumps(data, ensure_ascii=False, indent=1)
(OUT / "guide-data.json").write_text(js, encoding="utf-8")
(OUT / "guide-data.js").write_text("window.GUIDE_DATA = " + js + ";\n", encoding="utf-8")
print("items", len(items), "blocks", sum(len(i["blocks"]) for i in items), "fixes", len(applied))
for i in items: print(f"  {i['id']:20s} {len(i['blocks']):4d}  {i['title']}")
print(json.dumps(applied, ensure_ascii=False))
