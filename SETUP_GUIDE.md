# FMEA 플러그인 설치 가이드

이미 FMEA 폴더(업무 데이터)와 Claude Code가 설치된 팀원을 위한 가이드입니다.
플러그인 코드만 추가하면 바로 사용할 수 있습니다.

---

## 1. 플러그인 설치 (최초 1회)

### 1.1 GitHub 초대 수락

이 프로젝트는 비공개(Private)입니다. 팀장이 보낸 초대 이메일에서:
1. "Accept invitation" 클릭
2. GitHub 계정이 없으면 먼저 가입: https://github.com/signup

### 1.2 FMEA 폴더에서 CMD 열기

본인의 FMEA 폴더를 Windows 탐색기에서 엽니다.

**CMD 여는 방법:**
1. 탐색기 상단의 주소창(폴더 경로가 표시되는 곳)을 클릭
2. 주소창에 `cmd` 입력
3. Enter

이렇게 하면 FMEA 폴더 위치에서 CMD가 바로 열립니다.

### 1.3 플러그인 코드 다운로드

CMD에서 아래 명령어를 **한 줄씩** 입력하고 Enter를 누르세요:

```
git init
```

```
git remote add origin https://github.com/jungmanyoon/FMEA.git
```

```
git fetch origin main
```

```
git checkout origin/main -- .claude .gitattributes
```

> 처음 실행 시 GitHub 로그인 창이 뜰 수 있습니다. 로그인하면 됩니다.

### 1.4 프롬프트 파일 다운로드

```
git checkout origin/main -- 프롬프트.txt
```

> 이미 프롬프트.txt가 있는 경우 덮어쓰기됩니다.

### 1.5 Python 패키지 설치

```
pip install -r .claude/skills/fmea-analysis/mcp-server/requirements.txt
```

설치 완료 메시지가 나오면 성공입니다.

---

## 2. FMEA 작성하기

### 2.1 Claude Code 실행

FMEA 폴더에서 CMD를 열고 (1.2 방법 참고):

```
claude
```

**처음 실행 시:**
1. API 키 입력 화면이 나옵니다 -> 팀장에게 받은 키를 붙여넣기
2. 권한 승인 요청이 나옵니다 -> "Yes" 또는 "y" 입력

### 2.2 FMEA 작성 시작

FMEA 폴더의 **프롬프트.txt** 파일을 메모장으로 엽니다.

**첫 줄만 수정**합니다 (작성할 대상 지정):

```
# 예시 1: 단자 카테고리의 지지철
"단자" 카테고리의 "지지철" 도면의 모든 부품에 대해 FMEA를 한개의 엑셀 파일로 작성해줘

# 예시 2: 권선 카테고리의 권선자재표
"권선" 카테고리의 "권선자재표" 도면의 모든 부품에 대해 FMEA를 한개의 엑셀 파일로 작성해줘
```

수정한 프롬프트.txt를 **전체 선택**(Ctrl+A) -> **복사**(Ctrl+C)해서
Claude Code 채팅창에 **붙여넣기**(Ctrl+V) 후 Enter를 누르세요.

> [!] 주의: 첫 줄만 수정하세요! 나머지는 시스템 지시사항이므로 수정하면 안 됩니다.

### 2.3 자동 실행 (기다리면 됩니다)

```
[1단계] 데이터 수집 (약 5-10분)
  -> 다이어그램에서 부품 목록과 기능을 추출합니다
  -> 내부 기술문서에서 설계/제작/시험 정보를 수집합니다

[2단계] FMEA 항목 생성 (약 20-40분)
  -> 부품별 고장형태, 원인, 영향, 예방/검출 조치를 자동 생성합니다
  -> 16개 검증 도구로 자동 검증합니다

[3단계] Excel 생성 (약 5분)
  -> AIAG-VDA 양식의 Excel 파일을 자동 생성합니다
```

실행 중 권한 승인을 요청하면 "Yes"를 입력하세요.
총 소요 시간: 부품 수에 따라 30분 ~ 1시간

### 2.4 결과 확인

완료되면 아래 위치에 Excel 파일이 생성됩니다:

```
03.FMEA/{카테고리}/{도면명}/{도면명}_FMEA.xlsx
```

예시: 03.FMEA/03.단자/지지철/지지철_FMEA.xlsx

---

## 3. 플러그인 업데이트

팀장이 플러그인을 업데이트하면 아래 명령어로 최신 버전을 받으세요.

FMEA 폴더에서 CMD를 열고:

```
git fetch origin main
```

```
git checkout origin/main -- .claude .gitattributes
```

```
pip install -r .claude/skills/fmea-analysis/mcp-server/requirements.txt
```

> 업데이트 후 Claude Code가 실행 중이면 종료(Ctrl+C)하고 다시 시작하세요.

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

### "git" 명령어를 찾을 수 없음
-> https://git-scm.com/download/win 에서 Git을 설치하세요.
   설치 후 CMD를 새로 열어야 합니다.

### GitHub 로그인이 안 됨
-> 팀장에게 GitHub 초대를 요청하세요.
   초대 이메일에서 "Accept invitation"을 클릭해야 합니다.

### "pip" 명령어를 찾을 수 없음
-> https://www.python.org/downloads/ 에서 Python을 설치하세요.
   설치 시 "Add Python to PATH" 반드시 체크!

### Claude Code에서 도구 오류
-> Claude Code를 종료(Ctrl+C)하고 다시 실행해보세요.

### 실행 중 화면이 멈춘 경우
-> Enter를 한번 눌러보세요.
   반응이 없으면 Ctrl+C 후 `claude`로 재시작.

### Excel 파일이 생성되지 않음
-> `pip install openpyxl pandas` 입력 후 다시 실행

---

## 6. 전체 순서 요약

```
[플러그인 설치 - 최초 1회]
  1. GitHub 초대 수락 (이메일 확인)
  2. FMEA 폴더 열기 -> 주소창에 cmd 입력 -> Enter
  3. git init
  4. git remote add origin https://github.com/jungmanyoon/FMEA.git
  5. git fetch origin main
  6. git checkout origin/main -- .claude .gitattributes
  7. git checkout origin/main -- 프롬프트.txt
  8. pip install -r .claude/skills/fmea-analysis/mcp-server/requirements.txt

[FMEA 작성 - 매번]
  9. FMEA 폴더에서 CMD 열기
  10. claude 입력
  11. 프롬프트.txt 첫 줄 수정 -> 전체 복사 -> 붙여넣기
  12. 자동 실행 대기 (30분~1시간)
  13. 03.FMEA 폴더에서 Excel 결과 확인
```

---

## 7. 연락처

설치나 사용 중 문제가 있으면 팀장(유정만)에게 연락해주세요.
