# FMEA Analysis Plugin for Claude Code

AIAG-VDA 2019 FMEA Handbook 기반 변압기 FMEA 자동 생성 시스템.
Claude Code + MCP Server + Subagent Architecture.

## Quick Start

### 1. Clone

```bash
git clone https://github.com/jungmanyoon/FMEA.git
cd FMEA
```

### 2. Python Dependencies

```bash
pip install -r .claude/skills/fmea-analysis/mcp-server/requirements.txt
```

### 3. Directory Structure

Clone 후 아래 폴더를 직접 생성하고 데이터를 넣어야 합니다:

```
FMEA/
+-- 01.회의/                     # 회의 자료 (다이어그램 JSON 등)
+-- 02.참고자료/                  # 내부 기술문서
|   +-- _converted/              # 변환된 텍스트 파일 (convert 스크립트 실행)
|   +-- _fmea_index/             # 문서 인덱스 (rebuild_index 스크립트 실행)
+-- 03.FMEA/                     # FMEA 출력물 (자동 생성됨)
```

### 4. Claude Code 실행

```bash
claude
```

Claude Code가 자동으로 인식하는 것들:
- `.claude/agents/` - FMEA 에이전트 4개 (Leader, Collector, Generator, Fixer)
- `.claude/skills/fmea-analysis/` - FMEA 스킬 + MCP 서버
- `.claude/settings.json` - 권한 및 Hook 설정

### 5. FMEA 작성

`프롬프트.txt`의 내용을 Claude Code에 붙여넣으면 FMEA 작성이 시작됩니다.

## Architecture

```
[Leader (Main Session)]
    |
    +-- [Worker A+D: Collector] --- 다이어그램 + 온톨로지 + 내부문서
    +-- [Worker B: Collector]   --- 설계/재료 문서
    +-- [Worker C: Collector]   --- 제작/시험 문서
    |
    +-- [Generator]             --- FMEA 항목 생성 + 4-Round 사전검증
    +-- [Fixer]                 --- 다이아몬드 구조 보완 + 용어 통일
    |
    +-- [MCP Server: 16 Tools]  --- E/C/F/G/H/J열 자동 검증
    +-- [Scripts: 21 Python]    --- Excel 생성 + 후처리 + 정규화
```

### MCP Server (16 Tools)

| Tool | Description |
|------|-------------|
| `fmea_validate_failure_mode` | E열 (고장형태) 검증 |
| `fmea_validate_effect` | C열 (고장영향) 검증 |
| `fmea_validate_cause` | G열 (고장원인) 검증 |
| `fmea_validate_mechanism` | F열 (고장 메커니즘) 검증 |
| `fmea_validate_prevention` | H열 (예방 조치) 검증 |
| `fmea_validate_detection` | J열 (검출 조치) 검증 |
| `fmea_validate_causal_chain` | 인과관계 체인 검증 |
| `fmea_validate_cause_mechanism` | F-G 연동 검증 |
| `fmea_validate_function_effect` | B-C 기능-영향 검증 |
| `fmea_validate_row_context` | 행 전체 컨텍스트 검증 |
| `fmea_validate_batch` | 배치 검증 |
| `fmea_register_read` | 문서 읽기 등록 |
| `fmea_check_read_status` | 문서 읽기 상태 확인 |
| `fmea_create_item` | FMEA 항목 생성 |
| `fmea_get_forbidden_words` | 금지어 목록 조회 |
| `fmea_get_invalid_causal_combinations` | 금지 인과관계 조합 조회 |

### 4-Round Validation

```
Round 1 (parallel): E + F + G + C 개별 검증
Round 2 (parallel): E-F + F-G + B-C + H + J 연동 검증
Round 3:            row_context 행 전체 검증
Round 4:            S/O/D 점수 검증
```

## Key Files

| File | Description |
|------|-------------|
| `프롬프트.txt` | FMEA 작성 프롬프트 (v2.7) |
| `.claude/agents/fmea-leader.md` | Leader Playbook |
| `.claude/agents/fmea-worker-*.md` | Worker Agents (3) |
| `.claude/skills/fmea-analysis/SKILL.md` | Skill Definition |
| `.claude/skills/fmea-analysis/mcp-server/server.py` | MCP Server (v2.5) |
| `.claude/skills/fmea-analysis/scripts/generate_fmea_excel.py` | Excel Generator |
| `.claude/skills/fmea-analysis/references/` | 42 Reference Documents |

## Requirements

- Python 3.11+
- Claude Code CLI (with Anthropic API key)
- Windows (tested on Windows 10/11)
