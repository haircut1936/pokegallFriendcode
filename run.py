import os
import time
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창 숨기기
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized") 
chrome_options.page_load_strategy = 'eager'
chrome_options.binary_location = "chrome-win64/chrome.exe"

# ChromeDriver 경로 설정
service = Service("chromedriver-win64/chromedriver.exe") # ChromeDriver가 있는 경로

# 웹드라이버 시작
driver = webdriver.Chrome(service=service, options=chrome_options)

def get_post_no(post_url):
    """URL에서 게시글 번호(no)를 추출."""
    query_params = parse_qs(urlparse(post_url).query)
    post_no = query_params.get("no", [None])[0]  # "no" 값 가져오기
    if post_no is None:
        raise ValueError("URL에 게시글 번호(no)가 포함되어 있지 않습니다.")
    return post_no

def prompt_for_missing_settings(settings, default_settings):
    """누락된 설정에 대해 사용자 입력을 요청."""
    questions = {
        "주소": "사이트 주소를 입력해주세요 (예: https://gall.dcinside.com/mgallery/board/view/?id=pokemontcgpocket&no=205860): ",
        "반복": "반복을 활성화 하시겠습니까? (True/False): ",
        "새로고침간격": "새로고침 간격을 몇 초로 설정하시겠습니까? (기본값: 180초, 최소값: 30초): ",
        "글댓합": "글댓합 조건을 설정해주세요 (기본값: 100): ",
        "친구코드": "방명록에 남길 친구 코드를 입력해주세요: ",
        "아이디": "로그인할 아이디를 입력해주세요: ",
        "비밀번호": "로그인할 비밀번호를 입력해주세요: "
    }
    
    for key, default in default_settings.items():
        if key not in settings or not settings[key]:
            # 질문 딕셔너리에서 해당 키의 질문을 가져와 출력
            question = questions.get(key, f"{key}를 입력해주세요: ")
            value = input(question) or default
            settings[key] = value
    
    return settings

def load_or_prompt_settings():
    """설정 파일을 읽거나, 필요 시 사용자 입력을 받아 설정 파일을 생성."""
    settings_file = "설정.txt"
    settings = {}
    
    # 기본 설정 항목
    default_settings = {
        "주소": "",
        "반복": "True",
        "새로고침간격": "180",
        "글댓합": "100",
        "친구코드": "",
        "아이디": "",
        "비밀번호": ""
    }
    
    # 설정 파일 읽기
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            for line in f:
                key, value = line.strip().split(" ", 1)
                settings[key] = value
    else:
        print("설정 파일이 없습니다. 새로 작성합니다.")
    
    # 누락된 설정 입력 요청
    settings = prompt_for_missing_settings(settings, default_settings)
    
    # 설정 파일 저장
    with open(settings_file, "w", encoding="utf-8") as f:
        for key, value in settings.items():
            f.write(f"{key} {value}\n")
    
    print("설정이 완료되었습니다.")
    return settings

def load_blacklist():
    """블랙리스트 파일을 읽거나 생성."""
    blacklist_file = "블랙리스트.txt"
    if not os.path.exists(blacklist_file):
        with open(blacklist_file, "w", encoding="utf-8") as f:
            pass  # 빈 파일 생성
        print("블랙리스트 파일을 생성했습니다.")
        return set()
    
    with open(blacklist_file, "r", encoding="utf-8") as f:
        blacklist = set(line.strip() for line in f if line.strip())
    
    print(f"블랙리스트.txt 로드 완료: {len(blacklist)}명")
    return blacklist

def load_or_create_user_log(post_no):
    """게시글별 유저 로그 파일을 읽거나 생성."""
    user_log_file = f"{post_no}.txt"
    if not os.path.exists(user_log_file):
        with open(user_log_file, "w", encoding="utf-8") as f:
            pass  # 빈 파일 생성
        print(f"{user_log_file} 파일을 생성했습니다.")
        return []
    
    with open(user_log_file, "r", encoding="utf-8") as f:
        user_log = list(set(line.strip() for line in f if line.strip()))
    
    print(f"{post_no}.txt 로드 완료: {len(user_log)}명")
    return user_log

def save_user_log(post_no, new_users, user_log):
    """새로운 유저를 로그 파일에 저장."""
    user_log_file = f"{post_no}.txt"
    with open(user_log_file, "a", encoding="utf-8") as f:
        for user in new_users:
            f.write(user + "\n")
            user_log.append(user)
    print(f"{len(new_users)}명의 새로운 유저를 {post_no}.txt에 저장했습니다.")

def simulate_crawling(post_url):
    user_ids = []
    current_page = 1
    max_page = 10000
    
    try:
        driver.get(post_url)
        # # JavaScript가 로드될 시간 대기
        driver.implicitly_wait(3)  # 필요에 따라 조정

        # 댓글 리스트 가져오기
        while True:
            print(f"댓글 페이지 {current_page} 탐색중...")
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            reply_no = soup.find_all("li",{"class":"ub-content"})
            for r in reply_no:
                try:
                    user_id = r.find("span",{"class":"gall_writer ub-writer"}).get("data-uid")
                    if user_id:
                        user_ids.append(user_id)
                except:
                    continue
            if max_page == 10000:
                try:
                    max_page = int(soup.find("a",{"class":"sp_pagingicon page_end"}).get("href").split('(')[1].split(',')[0])
                except:
                    max_page = 1  # 기본값
                    paging_div = soup.find("div",{"class":"cmt_paging"})
                    for link in paging_div.find_all("a"):
                        href = link.get("href")
                        if href and "viewComments" in href:
                            # href에서 숫자만 추출
                            page_number = int(href.split("viewComments(")[1].split(",")[0])
                            max_page = max(max_page, page_number)
            current_page += 1
            if current_page > max_page:
                break
            js_command = f"viewComments({current_page}, 'D')"
            driver.execute_script(js_command)
            driver.implicitly_wait(3)
        
        
        user_ids = list(set(user_ids))
        return user_ids

    except Exception as e:
        print(f"페이지 로드 오류 발생: {e}")
        return user_ids
    
def log_in(id, password):
    try:
        driver.get("https://sign.dcinside.com/login?s_url=https://www.dcinside.com/")
        driver.implicitly_wait(5)

        id_input = driver.find_element(By.ID, "id")
        id_input.clear()
        id_input.send_keys(id)

        pw_input = driver.find_element(By.ID, "pw")
        pw_input.clear()
        pw_input.send_keys(password)

         # 로그인 버튼 클릭
        login_button = driver.find_element(By.CLASS_NAME, "btn_blue")
        login_button.click()
        return 0
    except Exception as e:
        print(f"페이지 로드 오류 발생: {e}")
        return -1

def guestbook_writing(user, pivot, code):
    print(f"'{user}'의 글댓합 확인중...")
    try:
        driver.get("https://gallog.dcinside.com/"+user)
        driver.implicitly_wait(3)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        if int(soup.find("div",{"class":"gallog_cont"}).find("span", {"class": "num"}).text.strip("()").replace(",", "")) + \
        int(soup.find("div",{"class":"gallog_cont comments"}).find("span", {"class": "num"}).text.strip("()").replace(",", "")) \
        < pivot:
            print(f"'{user}'의 글댓합이 조건에 충족되지 않습니다.")
            return 0
        print(f"'{user}'의 방명록에 친구 코드 작성 중...",end="")
        driver.get(f"https://gallog.dcinside.com/{user}/guestbook")
        driver.implicitly_wait(3)

        # 방명록 작성 허용 여부 확인
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        restricted_element = soup.find("div", {"class": "nomem_comment_info"})
        if restricted_element:
            print(f"\n'{user}'의 방명록은 허용된 사용자만 작성할 수 있습니다.")
            return -1

        # 텍스트 영역 선택 및 입력
        textarea = driver.find_element(By.NAME, "memo")
        textarea.clear()
        textarea.send_keys(code)

        # 체크박스 선택
        checkbox = driver.find_element(By.ID, "comment_chk")
        if not checkbox.is_selected():
            checkbox.click()
        
        # "등록" 버튼 클릭
        submit_button = driver.find_element(By.XPATH,'//*[@id="gb_form"]/div[2]/div[2]/div[2]/button')
        submit_button.click()
        print("완료")

        return 0
    except Exception as e:
        print(f"\n페이지 로드 오류 발생: {e}")
        return -1

def main():
    # 설정 및 파일 로드
    settings = load_or_prompt_settings()
    
    blacklist = load_blacklist()
    post_url = settings["주소"]
    
    try:
        post_no = get_post_no(post_url)
    except ValueError as e:
        print(e)
        print("유효하지 않은 URL입니다. 프로그램을 종료합니다.")
        time.sleep(3)
        return
    
    user_log = load_or_create_user_log(post_no)
    
    # 크롤링 반복 작업
    while True:
        # 크롤링 시뮬레이션
        current_ids = simulate_crawling(post_url)
        
        # 새로운 유저 판별
        new_users = [user for user in current_ids if user not in user_log and user not in blacklist]
        if not new_users:
            print("갱신된 아이디가 없습니다.")
        else:
            print(f"추출된 사용자 ID: {new_users}")
        
        time.sleep(3)

        # 로그인
        if new_users:
            status = log_in(settings["아이디"], settings["비밀번호"])
            if status == -1:
                print("로그인 과정 중 문제가 발생했습니다.")
                new_users = []
            else:
                print("로그인 완료.")
        
            time.sleep(3)

        # 작업 처리
        for user in new_users:
            status = guestbook_writing(user, int(settings["글댓합"]), settings["친구코드"])
            if status == -1:
                print(f"{user}에 대해 작업 중 오류 발생.")
                new_users.remove(user)

        # 로그 업데이트
        save_user_log(post_no, new_users, user_log)
        
        # 반복 여부 확인
        if settings["반복"].lower() != "true":
            print("반복이 True가 아니므로 작업이 종료됩니다.")
            time.sleep(3)
            break
        
        # 새로고침 간격 대기
        refresh_interval = max(int(settings["새로고침간격"]), 30)
        print(f"{refresh_interval}초 동안 대기 중...")
        time.sleep(refresh_interval)

if __name__ == "__main__":
    main()
