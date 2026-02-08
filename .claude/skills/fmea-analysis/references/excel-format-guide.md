# Excel 양식 가이드 (일진전기 FMEA)

## [DATA] Excel 파일 양식 표준

### 파일 구조
**일진전기 FMEA Excel 파일은 1개 시트에 모든 내용을 작성합니다.**

#### 시트 구조
```
Sheet: "FMEA"
┌─────────────────────────────────────────────────────┐
│ Row 1: 제목 "{부품명}_FMEA" (굵게, 16pt, 가운데)    │
│ Row 2: "프로젝트: 변압기"                           │
│ Row 3: "자료 출처: [실제 사용한 출처만]"            │
│        (예: IEC 60076-1, CIGRE TB 642, Claude)      │
│ Row 4: 빈 행 (구분선)                                │
│ Row 5: AIAG-VDA 7-Step 프로세스 구분 (Step 2-6)     │
│ Row 6: FMEA 테이블 헤더                              │
│ Row 7~: FMEA 데이터                                  │
└─────────────────────────────────────────────────────┘

[!] Row 3 주의: WebSearch로 실제 참조한 출처만 작성!
```

**Row 5 상세 (Step 구분)**:
- A5: 구조분석(step 2)
- B5: 기능분석(step 3)
- C5:G5 병합: 고장분석(step 4)
- H5:L5 병합: 리스크분석(step 5)
- M5:T5 병합: 최적화(step 6)
- **배경색**: `70AD47` (녹색)
- **폰트**: 굵게, 11pt, 흰색
- **행 높이**: 40 pixels (글자 잘림 방지)
- **테두리**: thin border (모든 셀, A5:T5)

### 색상 표준
**일진전기 FMEA Excel 파일은 파란색 계열을 기본으로 사용합니다.**

#### 프로젝트 정보 영역 (Row 1-4)
**[!] 수정**: Row 5는 Step 구분, Row 6은 헤더, Row 7+는 데이터
- **라벨 셀 배경색**: `D9E1F2` (연한 하늘색)
- **폰트**: 굵게, 11pt
- **테두리**: 모든 셀에 thin border
- **위치**: A1:B7

#### FMEA 결과 테이블 (Row 5~)
- **Row 5 (Step 구분)**:
  - **배경색**: `70AD47` (녹색)
  - **폰트**: 굵게, 11pt, 흰색
- **Row 6 (헤더)**:
  - **배경색**: `4472C4` (진한 파란색) - **주의: C65911(주황색) 사용 금지**
  - **폰트**: 굵게, 10pt, 흰색
- **Row 7~ (데이터 셀)**: 일반 폰트
- **테두리**: 모든 셀에 thin border (표 형식)
- **위치**: A5:T(마지막행)

### 테두리 설정
**모든 데이터 영역에는 표 형식의 테두리가 필요합니다.**

```python
from openpyxl.styles import Border, Side

# 테두리 스타일 정의
thin_border = Border(
    left=Side(style='thin', color='000000'),
    right=Side(style='thin', color='000000'),
    top=Side(style='thin', color='000000'),
    bottom=Side(style='thin', color='000000')
)

# 셀에 적용
cell.border = thin_border
```

### 셀 병합 (CRITICAL!)
**FMEA 결과 시트에서 1:N 구조 표현 시 셀 병합이 필수입니다.**

**병합 규칙**:
- 같은 고장 형태에 여러 원인이 있을 때
- **부품명, 기능, 고장 영향, S, 고장 형태** 열을 세로로 병합
- 빈 문자열("")이 있는 행들을 이전 행과 병합

**병합 대상 열**:
- A열: 부품명
- B열: 기능
- C열: 고장 영향
- D열: S (심각도)
- E열: 고장 형태

```python
# 셀 병합 예시
# Row 7-10: 같은 고장 형태 "접촉 불량 가능성"
ws.merge_cells('A7:A10')  # 부품명 병합
ws.merge_cells('B7:B10')  # 기능 병합
ws.merge_cells('C7:C10')  # 고장 영향 병합
ws.merge_cells('D7:D10')  # S 병합
ws.merge_cells('E7:E10')  # 고장 형태 병합

# 병합 후 정렬 설정
ws['A7'].alignment = Alignment(vertical='center', horizontal='left')
```

**자동 병합 로직**:
```python
# FMEA 데이터 입력 후, 같은 고장 형태 찾아서 병합
merge_start = 7  # 데이터 시작 행 (Row 7부터)
for row_idx in range(7, len(fmea_data) + 7):
    # 빈 문자열("")이 아니면 새로운 고장 형태 시작
    if fmea_data[row_idx - 7][0] != "":
        # 이전 구간 병합
        if row_idx > merge_start + 1:
            for col in ['A', 'B', 'C', 'D', 'E']:
                ws.merge_cells(f'{col}{merge_start}:{col}{row_idx-1}')
        merge_start = row_idx

# 마지막 구간 병합
if len(fmea_data) + 6 > merge_start:
    for col in ['A', 'B', 'C', 'D', 'E']:
        ws.merge_cells(f'{col}{merge_start}:{col}{len(fmea_data)+6}')
```

### 열 너비 표준
- **짧은 열 (S, O, D, RPN 등)**: 5-7
- **중간 열 (부품명, 담당자 등)**: 12-15
- **긴 열 (고장 영향, 메커니즘, 대책 등)**: 18-20

### 정렬 표준
- **헤더**: 가운데 정렬, 상하 가운데, 텍스트 줄바꿈 활성화
- **숫자 열 (S, O, D, RPN, S', O', D', RPN')**: 가운데 정렬
- **텍스트 열**: 왼쪽 정렬, 상단 정렬, 텍스트 줄바꿈 활성화

### 행 높이 표준 (CRITICAL!)
- **데이터 행 (Row 7+)**: 충분한 높이 설정 필수 (권장: 100 pixels)
- **이유**: `wrap_text=True`만으로는 openpyxl에서 행 높이가 자동 조정되지 않음
- **적용 방법**:
```python
# 데이터 행에 충분한 높이 설정
for row_idx in range(7, ws.max_row + 1):
    ws.row_dimensions[row_idx].height = 100
```

### 프린터 설정 표준 (중요!)
**모든 시트에 다음 프린터 설정을 기본으로 적용합니다:**

1. **용지 방향**: 가로 (Landscape)
2. **용지 크기**: A3
3. **배율 조정**: 한 페이지에 모든 열 맞추기 (Fit to 1 page wide)
4. **높이**: 자동 (Fit to 0 pages tall)

```python
# 모든 시트에 적용
ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE  # 가로 방향
ws.page_setup.paperSize = ws.PAPERSIZE_A3  # A3 용지
ws.page_setup.fitToPage = True  # 페이지에 맞춤 활성화 (중요!)
ws.page_setup.fitToWidth = 1  # 한 페이지에 모든 열 맞추기
ws.page_setup.fitToHeight = 0  # 높이는 자동
```

**적용 대상**:
- 0.프로젝트정보 시트
- 5.기능분류표 시트
- 7.FMEA결과 시트 (가장 중요!)

## [!] 주의사항

### 색상 선택 이유
- **파란색 계열 사용**: 전문적이고 차분한 인상, 일진전기 표준 양식과 일치
- **주황색(C65911) 사용 금지**: 일진전기 내부 양식과 불일치
- **토스 앱 스타일**: 연한 파란색 계열(D9E1F2, 4472C4)로 통일

### 양식 통일성
- **모든 FMEA 파일은 동일한 색상과 테두리 스타일을 사용해야 합니다.**
- **기존 파일과의 일관성을 유지하세요.**

## Python 코드 예시

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 테두리 정의
thin_border = Border(
    left=Side(style='thin', color='000000'),
    right=Side(style='thin', color='000000'),
    top=Side(style='thin', color='000000'),
    bottom=Side(style='thin', color='000000')
)

# FMEA 결과 시트 헤더 생성
ws_fmea = wb.create_sheet("7.FMEA결과")

headers = [
    "부품명", "기능", "고장 영향", "S", "고장 형태",
    "고장 원인", "고장 메커니즘", "현재 예방", "O",
    "현재 검출", "D", "RPN", "예방 조치", "검출 조치",
    "담당자", "목표일", "S'", "O'", "D'", "RPN'", "상태"
]

# 헤더 스타일 적용
for col_idx, h in enumerate(headers, 1):
    cell = ws_fmea.cell(1, col_idx, h)
    cell.font = Font(bold=True, size=10, color="FFFFFF")
    cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")  # 파란색!
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = thin_border  # 테두리 추가!

# 데이터 행에도 테두리 적용
for row_idx, row_data in enumerate(fmea_data, 2):
    # 행 높이 설정 (텍스트 잘림 방지)
    ws_fmea.row_dimensions[row_idx].height = 100

    for col_idx, value in enumerate(row_data, 1):
        cell = ws_fmea.cell(row_idx, col_idx, value)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = thin_border  # 테두리 추가!

        # 숫자 열은 가운데 정렬
        if col_idx in [4, 9, 11, 12, 17, 18, 19, 20]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
```

## 참고
- 일진전기 기존 FMEA 파일 양식 준수
- 토스 앱 스타일의 연한 파란색 사용
- 전문적이고 깔끔한 인상 유지
