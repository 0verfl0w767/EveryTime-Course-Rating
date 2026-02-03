import os
import time
import random
import json
import re

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

KYO_JSON_PATH = os.path.join(os.path.dirname(__file__), "교양.json")
try:
  with open(KYO_JSON_PATH, encoding="utf-8") as f:
    kyo = json.load(f)
  COURSE_LIST = sorted({entry.get("강좌명") for entry in kyo.get("data", []) if entry.get("강좌명")})
except Exception as e:
  print(f"교양 목록을 불러오는데 실패했습니다: {e}")
  COURSE_LIST = []

COURSE_PROF_MAP = {}
try:
  for entry in kyo.get("data", []):
    name = entry.get("강좌명")
    prof = entry.get("교수명") or "미지정"
    if name:
      COURSE_PROF_MAP.setdefault(name, set()).add(prof)
except Exception:
  COURSE_PROF_MAP = {}

options = Options()
options.add_argument("--start-maximized")

SLEEP_DEFAULT_MIN = 0
SLEEP_DEFAULT_MAX = 1

def sleep_rand(min_s: float = None, max_s: float = None):
  mn = SLEEP_DEFAULT_MIN if min_s is None else min_s
  mx = SLEEP_DEFAULT_MAX if max_s is None else max_s
  time.sleep(random.uniform(mn, mx))

DRIVER = webdriver.Chrome(options=options)
DRIVER.get("https://everytime.kr")
time.sleep(10)

#################################################################################### - 최근 강의평 클릭
WebDriverWait(DRIVER, 10).until(
  EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, \"/lecture\")]"))
).click()
# print("최근 강의평이 클릭되었습니다.")
sleep_rand()
out_records = []
first_search = True
for COURSE_NAME in COURSE_LIST:
  
  #################################################################################### - 교수명 검색 입력
  if first_search:
    xpath_input = "/html/body/div/div/div[1]/div/form/input[1]"
    xpath_button = "/html/body/div/div/div[1]/div/form/input[2]"
  else:
    xpath_input = "/html/body/div/div/div[1]/form/input[1]"
    xpath_button = "/html/body/div/div/div[1]/form/input[2]"

  SEARCH_BTN = WebDriverWait(DRIVER, 10).until(
    EC.element_to_be_clickable((By.XPATH, xpath_input))
  )
  SEARCH_BTN.click()
  SEARCH_BTN.clear()
  SEARCH_BTN.send_keys(COURSE_NAME)
  # print("강좌명 검색이 입력되었습니다.")
  sleep_rand()
  first_search = False
  ####################################################################################

  #################################################################################### - 교수명 검색 클릭
  WebDriverWait(DRIVER, 10).until(
    EC.element_to_be_clickable((By.XPATH, xpath_button))
  ).click()
  # print("강좌명 검색이 클릭되었습니다.")
  sleep_rand()
  ####################################################################################
  
  #################################################################################### - 바디 스크롤
  BODY = DRIVER.find_element(By.TAG_NAME, "body")
  
  for i in range(20):
    BODY.send_keys(Keys.PAGE_DOWN)

  for i in range(20):
      BODY.send_keys(Keys.PAGE_UP)
  ####################################################################################

  #################################################################################### - 강의 목록 확인
  LECTURE_DIV = DRIVER.find_element(By.XPATH, "/html/body/div/div/div[2]")
  LECTURES = list(LECTURE_DIV.find_elements(By.TAG_NAME, "a"))
  print(f"검색어 '{COURSE_NAME}' 관련 강의가 {len(LECTURES)}개 확인되었습니다.")
  sleep_rand()

  for LECTURE in LECTURES:
    LECTURE_NAME = LECTURE.find_element(By.CLASS_NAME, "name").text.strip()

    try:
      PROF_TEXT = LECTURE.find_element(By.CLASS_NAME, "professor").text.strip()
    except:
      PROF_TEXT = "미지정"

    STYLE = LECTURE.find_element(By.CLASS_NAME, "on").get_attribute("style")

    # normalize helper (remove parentheses and whitespace, case-insensitive)
    def _norm(x):
      return re.sub(r"\s+", "", re.sub(r"\([^)]*\)", "", x)).lower()

    if _norm(LECTURE_NAME) == _norm(COURSE_NAME) and PROF_TEXT in COURSE_PROF_MAP.get(COURSE_NAME, set()):
      print(f"Matched: {COURSE_NAME} - {PROF_TEXT} -> {STYLE}")

    if STYLE == "width: 0%;":
      print(LECTURE_NAME + " 강의는 평가 정보가 없습니다.")
      BODY.send_keys(Keys.ARROW_DOWN)
      BODY.send_keys(Keys.ARROW_DOWN)
      continue

    print(LECTURE_NAME, end=" ")
    print(PROF_TEXT, end=" ")
    print(STYLE)

    LECTURE_NEW_NAME = re.sub(pattern=r"\([^)]*\)", repl="", string=LECTURE_NAME).replace(" ", "")

    out_records.append({
      "course": COURSE_NAME,
      "professor": PROF_TEXT,
      "style": STYLE
    })

    sleep_rand(0, 1)
  ####################################################################################


OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "교양평점.json")
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
  json.dump({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "data": out_records}, f, ensure_ascii=False, indent=2)
print(f"Saved all ratings to {OUTPUT_PATH}")
