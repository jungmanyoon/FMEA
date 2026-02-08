# FMEA 시스템 설치 및 사용 가이드

이 문서는 팀원이 FMEA 자동 생성 시스템을 처음부터 설정하고 사용하는 방법을 안내합니다.

---

## 1. 사전 준비 (최초 1회)

### 1.1 Python 설치

Python 3.11 이상이 필요합니다. 이미 설치되어 있다면 건너뛰세요.

```
# 버전 확인
python --version
```

설치되지 않은 경우: https://www.python.org/downloads/ 에서 다운로드
- 설치 시 "Add Python to PATH" 체크 필수!

### 1.2 Claude Code CLI 설치

Claude Code는 Anthropic의 AI 코딩 도구입니다.

```
# npm으로 설치 (Node.js 필요)
npm install -g @anthropic-ai/claude-code
```

Node.js가 없다면: https://nodejs.org/ 에서 LTS 버전 다운로드 후 설치

### 1.3 Anthropic API 키 설정

Claude Code를 처음 실행하면 API 키를 입력하라는 안내가 나옵니다.
- API 키는 팀장에게 요청하세요
- 또는 https://console.anthropic.com/ 에서 직접 발급

### 1.4 GitHub 접근 권한

이 리포지토리는 Private입니다. 팀장이 GitHub Collaborator로 초대해야 접근 가능합니다.
- 초대 이메일 확인 -> Accept invitation 클릭

---

## 2. 프로젝트 설치

### 2.1 리포지토리 Clone

```
git clone https://github.com/jungmanyoon/FMEA.git
cd FMEA
```

### 2.2 Python 패키지 설치

```
pip install -r .claude/skills/fmea-analysis/mcp-server/requirements.txt
```

설치되는 패키지:
- fastmcp (MCP 서버 프레임워크)
- pydantic (타입 검증)
- pandas (데이터 처리)
- openpyxl (Excel 파일 생성/편집)

---

## 3. 데이터 폴더 준비

Clone 받은 프로젝트에는 코드만 있고, 실제 업무 데이터는 별도로 준비해야 합니다.

### 3.1 폴더 구조 생성

아래 폴더들을 프로젝트 루트에 만들어주세요:

```
FMEA/                            <- git clone으로 생성됨
+-- .claude/                     <- (이미 포함) 에이전트 + 스킬 + 설정
+-- 프롬프트.txt                  <- (이미 포함) FMEA 작성 지시서
+-- README.md                    <- (이미 포함) 프로젝트 개요
|
+-- 01.회의/                     <- [직접 생성] 회의 자료
|   +-- 00.회의 자료/
|       +-- 01.용어정리/         <- 변압기_전문용어집_V2.2_xlsx.json
|       +-- 02.다이어그램_기능분석/ <- 변압기_FMEA_Step2_Step3_다이어그램_v2.9_xlsx.json
|
+-- 02.참고자료/                  <- [직접 생성] 내부 기술문서
|   +-- _converted/              <- 변환된 텍스트 파일 (3.2절 참고)
|   +-- _fmea_index/             <- 문서 인덱스 (3.3절 참고)
|   +-- 02.CHECK_SHEET/          <- 원본 체크시트 문서
|   +-- 03.Work_Flow_Sheet/      <- 원본 워크플로우 문서
|   +-- 97.도시바TD/             <- TD 시리즈 문서
|   +-- ...                      <- 기타 참고 자료
|
+-- 03.FMEA/                     <- [직접 생성] FMEA 출력물 (자동 생성됨)
|   +-- 01.중신/
|   +-- 02.권선/
|   +-- 03.단자/
|   +-- 04.외함/
|   +-- 05.외장/
|
+-- 04.HMS_DB/                   <- [선택] QA 품질이력 DB (있으면 자동 연동)
```

### 3.2 참고자료 변환 (_converted 폴더)

내부 기술문서(PDF, DOCX, XLSX 등)를 Claude가 읽을 수 있는 텍스트 파일로 변환해야 합니다.

변환 스크립트: 02.참고자료/_fmea_index/convert_all_docs.py

```
# 02.참고자료/ 폴더에 원본 문서를 넣은 후 실행
python 02.참고자료/_fmea_index/convert_all_docs.py
```

결과: 02.참고자료/_converted/ 폴더에 텍스트 파일이 생성됩니다.
- PDF -> .md 파일
- XLSX -> .json 파일
- DOCX -> .md 파일

### 3.3 문서 인덱스 생성 (_fmea_index 폴더)

부품별로 어떤 문서를 참고해야 하는지 자동으로 매핑하는 인덱스를 생성합니다.

인덱스 스크립트: 02.참고자료/_fmea_index/rebuild_index_v4.py

```
# _converted 폴더가 준비된 후 실행
python 02.참고자료/_fmea_index/rebuild_index_v4.py
```

결과: mandatory_docs_by_component.json 파일이 생성됩니다.
- 164개 부품 x 3,490개 문서 매핑 포함

### 3.4 필수 파일 체크리스트

FMEA를 작성하려면 최소한 아래 파일들이 있어야 합니다:

```
[필수]
  01.회의/00.회의 자료/02.다이어그램_기능분석/
    변압기_FMEA_Step2_Step3_다이어그램_v2.9_xlsx.json  <- 기능 다이어그램

  01.회의/00.회의 자료/01.용어정리/
    변압기_전문용어집_V2.2_xlsx.json                    <- 전문 용어사전

[권장]
  02.참고자료/_fmea_index/mandatory_docs_by_component.json  <- 문서 인덱스
  02.참고자료/_converted/                                    <- 변환된 기술문서
```

다이어그램과 용어사전이 없으면 FMEA 작성이 시작되지 않습니다!

---

## 4. FMEA 작성 방법

### 4.1 Claude Code 실행

프로젝트 폴더에서 Claude Code를 실행합니다:

```
cd FMEA
claude
```

처음 실행 시:
- API 키 입력 안내가 나옵니다
- .claude/settings.json의 권한 승인을 요청합니다 -> 승인해주세요

### 4.2 프롬프트 입력

프롬프트.txt 파일의 내용을 Claude Code 채팅창에 붙여넣습니다.

프롬프트 첫 줄을 원하는 대상으로 수정하세요:

```
# 원본 (예시)
"단자" 카테고리의 "지지철" 도면의 모든 부품에 대해 FMEA를 한개의 엑셀 파일로 작성해줘

# 다른 대상으로 변경 예시
"권선" 카테고리의 "권선자재표" 도면의 모든 부품에 대해 FMEA를 한개의 엑셀 파일로 작성해줘
"중신" 카테고리의 "철심" 도면의 모든 부품에 대해 FMEA를 한개의 엑셀 파일로 작성해줘
```

### 4.3 자동 실행 과정

프롬프트를 입력하면 시스템이 자동으로 3단계를 실행합니다:

```
Phase 1: 데이터 수집 (약 5-10분)
  +-- Worker A+D: 다이어그램에서 부품/기능 추출 + 온톨로지 로드
  +-- Worker B: 설계/재료 관련 내부문서 수집
  +-- Worker C: 제작/시험 관련 내부문서 수집
  -> GATE 1 검증 (모든 Worker 완료 확인)

Phase 2: FMEA 항목 생성 (약 20-40분, 부품 수에 따라)
  +-- Generator: 부품별 고장형태/원인/영향/예방/검출 생성
  +-- 4-Round MCP 사전검증 (E/F/G/C/H/J열 + 연동검증)
  -> GATE 2-3 검증 (항목 품질 확인)

Phase 3: Excel 생성 + 최종 검증 (약 5분)
  +-- Excel 자동 생성 (셀 병합, 서식, 검증 포함)
  +-- Fixer: 오류 자동 수정 (있는 경우)
  -> GATE 4 검증 (최종 Excel 품질 확인)
```

### 4.4 결과물 확인

완료되면 03.FMEA/ 폴더에 결과가 생성됩니다:

```
03.FMEA/{카테고리}/{도면명}/
  +-- {도면명}_FMEA.xlsx        <- 최종 FMEA Excel 파일
  +-- _work/                    <- 중간 작업 파일들
      +-- worker_a_diagram.json  <- 다이어그램 추출 결과
      +-- worker_b_*.json        <- 내부문서 수집 결과
      +-- worker_c_*.json        <- 내부문서 수집 결과
      +-- batch_*.json           <- FMEA 항목 JSON
```

Excel 파일을 열어서 검토하면 됩니다.

---

## 5. 카테고리 및 도면 목록

다이어그램에 정의된 5개 카테고리와 도면:

| 카테고리 | 도면 예시 |
|---------|----------|
| 중신 | 철심, 철심자재표 등 |
| 권선 | 권선자재표, 절연물자재표 등 |
| 단자 | 지지철, 부싱 CT 등 |
| 외함 | 본체, 방열기 등 |
| 외장 | 변압기 외장 등 |

정확한 도면 목록은 다이어그램 JSON 파일에서 확인할 수 있습니다.

---

## 6. 주의사항

### 실행 중 멈춘 경우
- Claude Code가 응답을 멈추면 Enter를 눌러보세요
- 그래도 안 되면 Ctrl+C로 중단 후 다시 실행

### API 비용
- FMEA 1개 도면 작성 시 약 $3-5 정도의 API 비용이 발생합니다
- 부품 수가 많을수록 비용 증가

### 프롬프트 수정 주의
- 프롬프트.txt의 첫 줄(대상 지정)만 수정하세요
- 나머지 지시사항은 수정하지 마세요 (시스템 동작에 영향)

### 파일 인코딩
- 모든 파일은 UTF-8 인코딩 사용
- Excel 파일명에 특수문자 사용 자제

### Git 업데이트
- 시스템이 업데이트되면 아래 명령으로 최신 버전을 받으세요:
```
git pull origin main
pip install -r .claude/skills/fmea-analysis/mcp-server/requirements.txt
```

---

## 7. 문제 해결 (FAQ)

### Q: "fmea_validate_..." 도구를 찾을 수 없다는 오류
A: MCP 서버 연결 문제입니다. Claude Code를 종료하고 다시 실행해보세요.
   Python 패키지가 정상 설치되었는지도 확인하세요.

### Q: "다이어그램 파일을 찾을 수 없습니다"
A: 01.회의/00.회의 자료/02.다이어그램_기능분석/ 폴더에 다이어그램 JSON 파일이 있는지 확인하세요.

### Q: Excel 생성 시 오류
A: pip install openpyxl pandas 로 패키지를 다시 설치해보세요.

### Q: "권한 거부" 오류
A: Claude Code 실행 시 .claude/settings.json의 권한 승인을 해야 합니다.
   처음 실행 시 나오는 권한 요청에 "Yes"를 선택하세요.

### Q: 참고자료 변환이 안 됨
A: 02.참고자료/_fmea_index/convert_all_docs.py 실행 시 원본 파일이
   02.참고자료/ 하위에 있는지 확인하세요.

### Q: Git pull 후 에이전트가 인식 안 됨
A: Claude Code를 완전히 종료하고 새 세션으로 시작해야 합니다.
   에이전트는 세션 시작 시 1회만 로드됩니다.

---

## 8. 파일 구조 설명

```
.claude/
+-- agents/                          <- FMEA 에이전트 (자동 인식)
|   +-- fmea-leader.md               <- Leader: 전체 워크플로우 조율
|   +-- fmea-worker-collector.md     <- Collector: 데이터 수집 (A+D/B/C)
|   +-- fmea-worker-generator.md     <- Generator: FMEA 항목 생성 + 검증
|   +-- fmea-worker-fixer.md         <- Fixer: 오류 수정 + 구조 보완
|
+-- skills/fmea-analysis/            <- FMEA 스킬 (자동 인식)
|   +-- SKILL.md                     <- 스킬 정의 + 경로 상수
|   +-- mcp-server/
|   |   +-- server.py                <- MCP 서버 (16개 검증 도구)
|   |   +-- requirements.txt         <- Python 의존성
|   |   +-- hooks/                   <- Pre/Post Write 검증 훅
|   +-- scripts/
|   |   +-- generate_fmea_excel.py   <- Excel 생성 (메인)
|   |   +-- postprocess_fmea.py      <- 후처리 검증
|   |   +-- normalize_gen_keys.py    <- JSON 키 정규화
|   |   +-- validate_*.py            <- 10개 검증 모듈
|   +-- references/                  <- 42개 참조 문서
|       +-- failure-mode-ontology.md <- 고장형태 온톨로지 + 금지어
|       +-- effect-ontology.md       <- 고장영향 온톨로지
|       +-- diamond-structure.md     <- 다이아몬드 구조 규칙
|       +-- ...                      <- 기타 FMEA 규칙/예시
|
+-- settings.json                    <- Claude Code 프로젝트 설정
```

---

## 9. 연락처

문의사항은 팀장(유정만)에게 연락해주세요.
