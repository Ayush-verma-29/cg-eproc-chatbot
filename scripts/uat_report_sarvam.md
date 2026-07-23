# CG e-Procurement Chatbot — UAT Report (Sarvam 30B)

**Date:** 2026-07-20 15:35:40  
**Total Questions:** 50  
**LLM Judge:** Sarvam 30B (`sarvam-30b`)  
**Backend:** http://localhost:8001

---

## Final Summary Report

| Metric | Value |
|--------|-------|
| Actor Accuracy | 100.0% |
| Intent Accuracy | 0.0% |
| Retrieval Accuracy | 0.0% |
| Answer Accuracy | 50.0% |
| Citation Accuracy | 0.0% |
| Pass | 0 / 50 (0.0%) |
| Partial | 50 / 50 (100.0%) |
| Fail | 0 / 50 (0.0%) |
| Fallback Count | 0 |
| Avg Latency | 4665ms |
| P95 Latency | 2099ms |

### ✅ Questions Safe For Demo

### ⚠️ Questions NOT Safe For Demo
- **A01** (Partial): Our office needs 30 laptops. How should we decide whether to use GeM or a tender — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A02** (Partial): Department ko ₹4 lakh ka furniture kharidna hai. Kaunsa procurement method use k — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A03** (Partial): Can we buy an item directly if only one quotation is available on GeM? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A04** (Partial): Agar item GeM par available nahi hai, department ko next kya karna chahiye? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A05** (Partial): Can a department invite quotations from three local suppliers instead of issuing — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A06** (Partial): Hamare office ko urgently printers chahiye, lekin emergency nahi hai. Fastest la — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A07** (Partial): What factors should be checked before choosing Limited Tender? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A08** (Partial): When should an Open Tender be preferred over Limited Tender? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A09** (Partial): Can Single Tender be used because the earlier supplier already knows our system? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A10** (Partial): Ek proprietary software sirf ek company provide karti hai. Kya Single Tender all — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A11** (Partial): Can the department purchase spare parts only from the original equipment manufac — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A12** (Partial): Government department ko dusre government undertaking se goods purchase karne ha — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A13** (Partial): Can we split a ₹10 lakh requirement into five smaller purchase orders? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A14** (Partial): Same item alag-alag months mein chahiye. Kya har month direct purchase kar sakte — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **A15** (Partial): How should the department estimate the total procurement value before selecting  — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B01** (Partial): Purchase start karne se pehle administrative approval aur financial sanction mei — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B02** (Partial): Who should confirm budget availability before a tender is published? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B03** (Partial): Can a tender be initiated before the budget is formally available? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B04** (Partial): Department ke paas budget hai, lekin financial sanction pending hai. Kya GeM ord — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B05** (Partial): What records should be kept to prove that the selected procurement method was ju — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B06** (Partial): Can the competent authority approve a purchase after the order has already been  — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B07** (Partial): What is delegated financial power, and how does it affect procurement method sel — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B08** (Partial): Agar purchase value officer ki delegated power se zyada hai, to next approval ki — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B09** (Partial): Can the department use last year's approved rate without conducting a fresh proc — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B10** (Partial): How should price reasonableness be established when only one valid bid is receiv — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B11** (Partial): Kya lowest quotation milne ka matlab price reasonable hai? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B12** (Partial): What should the department do if all received bids are much higher than the esti — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B13** (Partial): Can negotiations be conducted with the L1 bidder after opening financial bids? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B14** (Partial): Tender cancel karne ke liye kya reasons record karne chahiye? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **B15** (Partial): Can the department reject all bids without giving any reason? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C01** (Partial): Can we mention a preferred brand and write "or equivalent" in the technical spec — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C02** (Partial): Laptop specification banate waqt processor brand mention karna allowed hai kya? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C03** (Partial): How can specifications be written so that they do not favour one vendor? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C04** (Partial): Can experience and turnover requirements be higher than the estimated tender val — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C05** (Partial): Tender mein three-year experience mandatory rakhna kab justified hota hai? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C06** (Partial): Can a startup be exempted from prior experience and turnover requirements? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C07** (Partial): Does MSME registration automatically make a bidder eligible for every tender? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C08** (Partial): Can EMD exemption be claimed without uploading the required registration certifi — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C09** (Partial): What should happen if a bidder meets the technical specification but misses one  — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **C10** (Partial): A bidder uploaded an expired certificate. Should the bid be rejected or can clar — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D01** (Partial): Technical evaluation ke baad financial bids kin bidders ki open honi chahiye? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D02** (Partial): Can a technically non-responsive bidder be selected because its price is the low — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D03** (Partial): L1 bidder ki rate estimate se 25% zyada hai. Department ko kya karna chahiye? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D04** (Partial): How should the evaluation committee record reasons for rejecting a bidder? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D05** (Partial): Can tender conditions be changed after bids have already been opened? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D06** (Partial): Purchase Order issue hone ke baad vendor delivery delay kare to department kya a — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D07** (Partial): Goods receive ho gaye, but specification match nahi kar rahi. Payment release ka — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **D08** (Partial): What documents should be completed before processing payment to the supplier? — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **E01** (Partial): Bid submit karne ke baad corrigendum se specifications change ho gayi. Kya mujhe — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_
- **E02** (Partial): EMD payment successful hai but portal par status pending dikh raha hai, aur dead — _Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip'_

### 🔴 Top 10 Failure Clusters (Missing Concepts)
- `parse error` — missed in **50** questions

### 🔧 Recommended Fixes (Ranked by Impact)
1. **Complete partial answers** — 50 questions partially answered; add missing concepts via QA overrides or prompt tuning.
2. **Improve retrieval** — Only 0.0% of expected source families retrieved; tune vector store keyword boosts.
3. **Improve citation accuracy** — 0.0% citation accuracy; add page-level references to chunked documents.

---

## Per-Question Results

---

### ⚠️ A01: Our office needs 30 laptops. How should we decide whether to use GeM or a tender?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | procurement_method_selection |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2074ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A02: Department ko ₹4 lakh ka furniture kharidna hai. Kaunsa procurement method use karna chahiye?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | procurement_method_selection |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2055ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A03: Can we buy an item directly if only one quotation is available on GeM?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | GeM_direct_purchase_rules |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2046ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A04: Agar item GeM par available nahi hai, department ko next kya karna chahiye?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | alternate_procurement_method |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2087ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A05: Can a department invite quotations from three local suppliers instead of issuing an open tender?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | limited_tender_eligibility |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2056ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A06: Hamare office ko urgently printers chahiye, lekin emergency nahi hai. Fastest lawful option kya hai?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | fastest_procurement_method |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2070ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A07: What factors should be checked before choosing Limited Tender?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | limited_tender_prerequisites |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2070ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A08: When should an Open Tender be preferred over Limited Tender?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | open_vs_limited_tender |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2032ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A09: Can Single Tender be used because the earlier supplier already knows our system?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | single_tender_eligibility |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2080ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A10: Ek proprietary software sirf ek company provide karti hai. Kya Single Tender allowed hoga?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | proprietary_single_tender |
| **Detected Intent** | parse_error |
| **Expected Sources** | Chhattisgarh Store Purchase Rules, GFR Rule 166 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2085ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A11: Can the department purchase spare parts only from the original equipment manufacturer?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | OEM_spare_parts_procurement |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2088ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A12: Government department ko dusre government undertaking se goods purchase karne hain. Kya tender zaroori hai?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | inter_government_procurement |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2071ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A13: Can we split a ₹10 lakh requirement into five smaller purchase orders?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | purchase_splitting_prohibition |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR Rule 157, CVC guidelines, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2047ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A14: Same item alag-alag months mein chahiye. Kya har month direct purchase kar sakte hain?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | purchase_splitting_prohibition |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR Rule 157, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2077ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ A15: How should the department estimate the total procurement value before selecting the method?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | cost_estimation_methodology |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2048ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B01: Purchase start karne se pehle administrative approval aur financial sanction mein kya difference hai?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | administrative_vs_financial_approval |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2054ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B02: Who should confirm budget availability before a tender is published?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | budget_confirmation_authority |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2069ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B03: Can a tender be initiated before the budget is formally available?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | tender_without_budget |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2058ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B04: Department ke paas budget hai, lekin financial sanction pending hai. Kya GeM order place kar sakte hain?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | GeM_order_without_sanction |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2050ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B05: What records should be kept to prove that the selected procurement method was justified?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | procurement_documentation |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2058ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B06: Can the competent authority approve a purchase after the order has already been placed?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | post_facto_approval |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2071ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B07: What is delegated financial power, and how does it affect procurement method selection?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | delegated_financial_powers |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2069ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B08: Agar purchase value officer ki delegated power se zyada hai, to next approval kis stage par lena chahiye?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | escalation_of_approval |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2082ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B09: Can the department use last year's approved rate without conducting a fresh procurement?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | rate_contract_reuse |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2057ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B10: How should price reasonableness be established when only one valid bid is received?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | price_reasonableness_single_bid |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2076ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B11: Kya lowest quotation milne ka matlab price reasonable hai?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | price_reasonableness_lowest_bid |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2087ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B12: What should the department do if all received bids are much higher than the estimated cost?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | all_high_bids_action |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2055ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B13: Can negotiations be conducted with the L1 bidder after opening financial bids?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | L1_negotiation |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2034ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B14: Tender cancel karne ke liye kya reasons record karne chahiye?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | tender_cancellation_documentation |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2037ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ B15: Can the department reject all bids without giving any reason?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | bid_rejection_authority |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2065ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C01: Can we mention a preferred brand and write "or equivalent" in the technical specifications?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | specification_brand_mention |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2068ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C02: Laptop specification banate waqt processor brand mention karna allowed hai kya?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | specification_brand_restriction |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2053ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C03: How can specifications be written so that they do not favour one vendor?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | neutral_specification_writing |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2053ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C04: Can experience and turnover requirements be higher than the estimated tender value?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | eligibility_criteria_proportionality |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2072ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C05: Tender mein three-year experience mandatory rakhna kab justified hota hai?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | experience_requirement_justification |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2085ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C06: Can a startup be exempted from prior experience and turnover requirements?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | startup_exemption |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, DPIIT startup policy |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2038ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C07: Does MSME registration automatically make a bidder eligible for every tender?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | MSME_eligibility |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, MSME procurement policy |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2075ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C08: Can EMD exemption be claimed without uploading the required registration certificate?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | EMD_exemption_documentation |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR Rule 170, MSME policy |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2080ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C09: What should happen if a bidder meets the technical specification but misses one mandatory document?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | bid_document_deficiency |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, tender evaluation guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2070ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ C10: A bidder uploaded an expired certificate. Should the bid be rejected or can clarification be requested?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | expired_certificate_bid_evaluation |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2086ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D01: Technical evaluation ke baad financial bids kin bidders ki open honi chahiye?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | financial_bid_opening_eligibility |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2067ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D02: Can a technically non-responsive bidder be selected because its price is the lowest?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | non_responsive_bid_selection |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2071ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D03: L1 bidder ki rate estimate se 25% zyada hai. Department ko kya karna chahiye?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | high_L1_rate_action |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2070ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D04: How should the evaluation committee record reasons for rejecting a bidder?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | bid_rejection_documentation |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2088ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D05: Can tender conditions be changed after bids have already been opened?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | post_bid_condition_change |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, CVC guidelines |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2025ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D06: Purchase Order issue hone ke baad vendor delivery delay kare to department kya action le sakta hai?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | vendor_delivery_delay_action |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2058ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D07: Goods receive ho gaye, but specification match nahi kar rahi. Payment release karna chahiye kya?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | non_conforming_goods_payment |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017, Chhattisgarh Store Purchase Rules |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2065ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ D08: What documents should be completed before processing payment to the supplier?

| Field | Value |
|-------|-------|
| **Expected Actor** | government_officer |
| **Detected Actor** | government_officer |
| **Expected Intent** | pre_payment_documentation |
| **Detected Intent** | parse_error |
| **Expected Sources** | GFR 2017 |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 2099ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
[ERROR] HTTP Error 401: Unauthorized
```

---

### ⚠️ E01: Bid submit karne ke baad corrigendum se specifications change ho gayi. Kya mujhe bid dobara submit karni hogi?

| Field | Value |
|-------|-------|
| **Expected Actor** | vendor |
| **Detected Actor** | vendor |
| **Expected Intent** | corrigendum_bid_resubmission |
| **Detected Intent** | parse_error |
| **Expected Sources** | CHiPS_Bid_Submission_Manual_English.pdf, faq.pdf |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 70239ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
**Corrigendum Se Specifications Change Ke Baad Bid Dubara Submit Karni Hogi Ya Nahi?**

- Agar corrigendum mein specifications change kiye gaye hain, toh apne bid ko dubara submit karne ka option hai.
- Corrigendum publish hone ke baad, apna bid update karna hoga taaki naya tender document ke hisab se hi bidding process chale.

**Follow-up Questions:**

1. Specifications change ke liye corrigendum publish karne ke baad, apna bid dubara submit karne ka process kya hai?
2. Corrigendum mein specifications update hone par, apka bid kaise update hoga?

**References:** Rule 162, Rule 166, Rule 3.1.1
```

---

### ⚠️ E02: EMD payment successful hai but portal par status pending dikh raha hai, aur deadline close hai. Main kya karun?

| Field | Value |
|-------|-------|
| **Expected Actor** | vendor |
| **Detected Actor** | vendor |
| **Expected Intent** | EMD_payment_status_issue |
| **Detected Intent** | parse_error |
| **Expected Sources** | CHiPS_Bid_Submission_Manual_English.pdf, FAQ_CHiPS_Online_EMD_V2.0.pdf, faq.pdf |
| **Retrieved Sources** | None |
| **Concept Coverage** | 0% |
| **Citation Correct** | No |
| **Response Time** | 63885ms |
| **Verdict** | Partial |
| **Missing Concepts** | parse error |
| **Root Cause** | Sarvam response could not be parsed: [SARVAM_ERROR] 'NoneType' object has no attribute 'strip' |

**Full Answer:**

```
**Tender Status Update Ke Liye Kya Kar Sakte Hain?**

- Agar EMD payment successful hai lekin tender status pending dikh raha hai, toh apko corrigendum jari karna hoga taaki tender due date extension ho sake.
- Corrigendum publish hone ke baad hi tender deadline extend kiya ja sakta hai.

**Follow-up Questions:**

1. EMD payment successful hone par bhi tender status pending dikh raha hai, toh iske liye corrigendum kaise jari kiya ja sakta hai?
2. Tender deadline extension ke liye corrigendum publish karne ke baad kaun se process follow kiya jaata hai?

**References:** Rule 3.1.1, Rule 162, Rule 166
```
