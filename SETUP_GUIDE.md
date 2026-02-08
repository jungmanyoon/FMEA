# FMEA 플러그인 설치 가이드

이미 FMEA 폴더(업무 데이터)와 Claude Code가 설치된 팀원을 위한 가이드입니다.

---

## 1. 플러그인 설치 (최초 1회)

### 1단계: 파일 다운로드

1. https://github.com/jungmanyoon/FMEA 접속
2. 초록색 **Code** 버튼 클릭
3. **Download ZIP** 클릭
4. 다운로드된 ZIP 파일을 열기

### 2단계: 파일 복사

ZIP 안에 있는 아래 2개를 본인의 **FMEA 폴더**에 복사합니다:

| 복사할 항목 | 설명 |
|------------|------|
| **.claude** 폴더 | 플러그인 코드 (에이전트, 검증도구, 스크립트) |
| **프롬프트.txt** 파일 | FMEA 작성 프롬프트 |

> .claude 폴더가 안 보이면: 탐색기 상단 "보기" -> "숨긴 항목" 체크

### 3단계: 설치 실행

FMEA 폴더에 복사한 **install.bat** 파일을 더블클릭합니다.

"설치 완료!" 메시지가 나오면 끝입니다.

> install.bat이 없으면: FMEA 폴더에서 CMD를 열고 아래 입력
> `pip install -r .claude/skills/fmea-analysis/mcp-server/requirements.txt`

---

## 2. FMEA 작성하기

### CMD 열기

FMEA 폴더를 탐색기에서 열고:
1. 상단 주소창 클릭
2. `cmd` 입력
3. Enter

### Claude Code 실행

```
claude
```

처음 실행 시 API 키를 물어봅니다 -> 팀장에게 받은 키를 붙여넣기

### FMEA 작성

1. **프롬프트.txt**를 메모장으로 열기
2. **첫 줄만 수정** (작성할 대상 지정):

```
"단자" 카테고리의 "지지철" 도면의 모든 부품에 대해 FMEA를 한개의 엑셀 파일로 작성해줘
```

3. 전체 선택(Ctrl+A) -> 복사(Ctrl+C)
4. Claude Code 채팅창에 붙여넣기(Ctrl+V) -> Enter

> 첫 줄만 수정하세요! 나머지는 시스템 지시사항이므로 수정 금지.

### 자동 실행 (기다리면 됩니다)

30분~1시간 자동으로 실행됩니다.
권한 승인을 물어보면 "Yes" 입력.

### 결과 확인

`03.FMEA/{카테고리}/{도면명}/{도면명}_FMEA.xlsx` 에 Excel이 생성됩니다.

---

## 3. 플러그인 업데이트

팀장이 업데이트를 공지하면:
1. https://github.com/jungmanyoon/FMEA 에서 다시 ZIP 다운로드
2. .claude 폴더를 덮어쓰기로 복사
3. install.bat 더블클릭

> Claude Code가 실행 중이면 종료(Ctrl+C) 후 다시 시작하세요.

---

## 4. 카테고리 및 도면

| 카테고리 | 도면 예시 |
|---------|----------|
| 중신 | 철심, 철심자재표 |
| 권선 | 권선자재표, 절연물자재표 |
| 단자 | 지지철, 부싱 CT |
| 외함 | 본체, 방열기 |
| 외장 | 변압기 외장 |

---

## 5. 문제 해결

| 문제 | 해결 |
|------|------|
| install.bat에서 오류 | Python 설치 확인. 없으면 https://www.python.org/downloads/ 에서 설치 ("Add to PATH" 체크!) |
| claude 명령어 안됨 | Node.js 설치 후 `npm install -g @anthropic-ai/claude-code` |
| 화면이 멈춤 | Enter 한번 눌러보기. 안되면 Ctrl+C 후 `claude` 재시작 |
| Excel 안 생성됨 | `pip install openpyxl pandas` 입력 후 재시작 |

---

## 6. 전체 순서 요약

```
[설치 - 최초 1회]
  1. GitHub에서 ZIP 다운로드
  2. .claude 폴더 + 프롬프트.txt를 FMEA 폴더에 복사
  3. install.bat 더블클릭

[FMEA 작성 - 매번]
  4. FMEA 폴더에서 CMD 열기 (주소창에 cmd)
  5. claude 입력
  6. 프롬프트.txt 첫 줄 수정 -> 전체 복사 -> 붙여넣기
  7. 자동 실행 대기 (30분~1시간)
  8. 03.FMEA 폴더에서 Excel 확인
```

---

문제가 있으면 팀장(유정만)에게 연락해주세요.
