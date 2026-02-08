# 변압기 제조 공정 흐름 (Process Flow)

**일진전기 초고압 변압기 실제 제조 공정 단계**

---

## 설계 공정 (Design Phase) - 8 Phases

### Phase 1: 사양 검토 및 설계 입력

- Input: Rated MVA, Voltage/Taps, Frequency, Cooling, Insulation Levels, Standards
- Output: Design Basis, ITP/QCP Draft

### Phase 2: 전자기 기본 설계 (EM Design)

- Core Design (Bmax, CRGO Grade, Step-lap)
- Winding Design (CTC/Foil, %Z Target, Force Distribution)
- Loss Design (P₀/Pcu/Stray Loss)

### Phase 3: 절연 설계 (Insulation Design)

- Electric Field FEM, Clearance/Creepage
- Test Requirements: Applied/Induced+PD, LI/SI

### Phase 4: 단락 기계 설계 (Short-Circuit Design)

- Radial Pressure/Axial Force Calculation
- Winding/Spacer/Clamp Stability (IEC 60076-5)

### Phase 5: 열/유압 설계 (Thermal/Hydraulic)

- HST/Top-oil Target
- CFD for Flow Uniformity, Dead Zone Elimination

### Phase 6: 보조 장비 (Auxiliary Equipment)

- OLTC, Bushing, Buchholz, PRD, OTI/WTI, Conservator

### Phase 7: 구조 설계 (Structural Design)

- 7.1 전기 구조부: Winding, Core/Clamp, Terminal (Lead/Bushing/OLTC)
- 7.2 기계 구조부: Tank, Cooling, Piping, Painting

### Phase 8: 통합 검토 (Integration)

- PDR/CDR, FMEA, Configuration Freeze
- Final Output: GA, Design Book, EBOM→MBOM, ITP/QCP

---

## 생산 공정 (Manufacturing Phase) - 12 Steps

### Step 1: 철심 절단/슬리팅 (Core Cutting)

- CTQ: Iron Loss ≤ Design +10%

### Step 2: 철심 적층/조립 (Core Lamination)

- CTQ: Single-point Grounding <10V, Core Building Factor

### Step 3: 권선 제조 (Winding Manufacturing)

- CTQ: DCWR ±1%, Dimension ±0.5%, Duct/Spacer Position

### Step 4: 반성 작업 (Core-Coil Marriage)

- CTQ: Gap within Tolerance

### Step 5: 중신 제작 (Active Part Assembly)

- CTQ: Preload ±5%, Grounding <10V, Lead Clearance/Creepage

### Step 6: VPD 건조 (Vacuum Pressure Drying)

- CTQ: Moisture Target, IR Trend Stable

### Step 7: Tanking (탱크 삽입)

- CTQ: Time Minimized (Moisture Re-absorption Prevention)

### Step 8: 진공 주유 (Vacuum Oil Filling)

- CTQ: Vacuum <0.1 mbar, BDV ≥70kV, Moisture ≤10ppm, Tank Leak <1 mbar/h

### Step 9: 최종 조립 (Final Assembly)

- CTQ: All Connections Verified, Interlock Functional

### Step 10: FAT (Factory Acceptance Test per IEC 60076)

- CTQ: PD (UHV <50pC, EHV <100pC), Noise <65 dB(A), All Tests Pass

### Step 11: 출하 준비 (Shipping)

- CTQ: Complete Documentation Package

### Step 12: SAT (Site Acceptance Test)

- CTQ: Oil Quality, All Tests Pass, Customer Sign-off

---

## 7단계 라이프사이클 → 실제 공정 매핑

| 라이프사이클 단계      | 실제 공정 Phase/Step              | 주요 불량 유형                                        |
| ---------------------- | --------------------------------- | ----------------------------------------------------- |
| **1. 설계 불량** | Phase 1-8 (설계 공정 전체)        | 계산 오류, 도면 불량, 표준 미준수, Design Review 누락 |
| **2. 재료 불량** | Step 1-3 (철심/권선 재료 투입)    | 재질 불량, 자재 불량, 입고 검사 누락                  |
| **3. 제작 불량** | Step 1-5 (철심/권선 제조 및 조립) | 가공 불량, 조립 불량, 치수 불량, 권선 불량            |
| **4. 시험 불량** | Step 6-10 (VPD, 진공 주유, FAT)   | 시험 조건 부적절, 검사 누락, 판정 오류                |
| **5. 운송 불량** | Step 11 (출하 준비)               | 포장 불량, 운송 불량, 취급 부주의                     |
| **6. 설치 불량** | Step 12 (SAT - 현장 설치)         | 설치 불량, 시공 오류, 시운전 불량                     |
| **7. 운영 불량** | 현장 운영 (Post-SAT)              | 유지보수 불량, 과부하, 노화/열화                      |

---

## Critical Control Points (CTQ) - Top 10

| CTQ Item         | Acceptance Criteria | Step      | Record Document          |
| ---------------- | ------------------- | --------- | ------------------------ |
| Core Grounding   | Single-point, <10V  | Step 2, 5 | Core Inspection Sheet    |
| Winding Preload  | Design Value ±5%   | Step 5    | Press Record             |
| Vacuum Level     | < 0.1 mbar          | Step 8    | VPD Log                  |
| Oil BDV          | ≥ 70 kV            | Step 8    | Oil Quality Certificate  |
| Oil Moisture     | ≤ 10 ppm           | Step 8    | Oil Quality Certificate  |
| PD (UHV)         | < 50 pC             | Step 10   | PD Test Certificate      |
| PD (EHV)         | < 100 pC            | Step 10   | PD Test Certificate      |
| Tank Vacuum Leak | < 1 mbar/h          | Step 8    | Airtightness Test Report |
| Noise Level      | < 65 dB(A) @1m      | Step 10   | Noise Test Report        |
| Iron Loss        | Design +10% max     | Step 10   | FAT Certificate          |

---

## Component-Process Mapping (핵심 컴포넌트)

| Component             | Design Phase       | Manufacturing Step | Testing                 | Key CTQ                                   |
| --------------------- | ------------------ | ------------------ | ----------------------- | ----------------------------------------- |
| **CORE**        | Phase 2.1, 7.1.3   | Step 1-2           | Step 10 (P₀/I₀)       | Iron Loss, Grounding <10V                 |
| **CLAMP**       | Phase 4, 7.1.3     | Step 2, 5          | Step 10 (Noise)         | Preload ±5%                              |
| **WINDING**     | Phase 2.2, 7.1.1-2 | Step 3-5           | Step 10 (WR, Pk/%Z, PD) | DCWR ±1%, Dimension ±0.5%, Preload ±5% |
| **LEAD**        | Phase 2.2, 7.1.4   | Step 3, 5          | Step 10 (Applied)       | Clearance/Creepage, Temp Rise             |
| **TANK**        | Phase 7.2          | Step 7-8           | Step 8 (Leak Test)      | Vacuum Leak <1 mbar/h                     |
| **OIL**         | Phase 5            | Step 8             | Step 8, 10, 12          | BDV ≥70kV, Moisture ≤10ppm              |
| **TAP_CHANGER** | Phase 6            | Step 7, 9          | Step 10 (Operation)     | Contact Resistance, Interlock             |

---

## FMEA 작성 시 활용법

**Failure Cause 작성**: 해당 부품이 거치는 실제 공정 단계별로 원인 도출

**Detection Method**: 각 CTQ의 측정 방법 및 합격 기준 참조

**Responsible**: 공정 단계별 담당 팀 배정
- 설계 → 전기설계팀/구조설계팀
- 제작 → 생산팀
- 시험 → QA팀

**Current Control**: 각 Step의 검사 문서 및 Quality Gate 명시
