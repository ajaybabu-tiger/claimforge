import os
import sys
import json
import httpx
from pathlib import Path

# Add backend directory to sys.path so we can use ReportLab to generate a brand new synthetic PDF
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
from app.services.demo_seeder import DemoSeeder

BASE_URL = "http://127.0.0.1:8000"

def test_vertical_slice():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    print("=== STEP 1: VERIFY HEALTH ENDPOINT ===")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print(f"Health OK: {health_data['status']} | Database: {health_data['database']} | Mode: {health_data['ai_active_mode']}")

    print("\n=== STEP 2: CREATE A NEW CLAIM VIA API ===")
    claim_payload = {
        "claim_reference": "CLM-SLICE-2026-001",
        "patient_reference": "PAT-VERIFY-772",
        "insurer_name": "Aetna Premier Choice",
        "claim_amount": 9500.00,
        "rejection_reason": "Claim denied: Missing prior authorization for emergency surgical admission.",
        "rejection_code": "CO-197",
        "policy_number": "AET-POL-8841",
        "date_of_service": "2026-02-18",
        "review_priority": "urgent",
        "reviewer_notes": "Live test of vertical slice pipeline."
    }
    res = client.post("/api/claims", json=claim_payload)
    if res.status_code == 409:
        # Already exists, fetch it
        list_res = client.get("/api/claims?search=CLM-SLICE-2026-001")
        claim = list_res.json()[0]
    else:
        assert res.status_code == 201, f"Claim creation failed: {res.text}"
        claim = res.json()

    claim_id = claim["id"]
    print(f"Claim Created: ID={claim_id} | Ref={claim['claim_reference']} | Amount=${claim['claim_amount']:,.2f}")

    print("\n=== STEP 3: GENERATE & UPLOAD REAL SYNTHETIC MEDICAL PDFS ===")
    # 1. Hospital itemized bill
    bill_pdf = "temp_itemized_bill.pdf"
    DemoSeeder.create_sample_pdf(
        bill_pdf,
        "METRO GENERAL HOSPITAL - BILLING LEDGER",
        [
            "Patient Name: Samuel Taylor | Member ID: AET-POL-8841",
            "Date of Service: 2026-02-18 | Facility: Metro General Hospital Emergency Dept",
            "Attending Physician: Dr. Catherine Hall, MD",
            "TABLE:Rev Code|CPT Code|Description|Charge;0450|99285|Emergency Dept Visit Level 5|$1,950.00;0360|44970|Laparoscopic Surgery|$6,200.00;0250|J3490|IV Anesthesia & Sedation|$1,350.00",
            "Total Charges Billed: $9,500.00"
        ]
    )

    with open(bill_pdf, "rb") as f:
        res = client.post(
            f"/api/claims/{claim_id}/documents",
            files={"file": (bill_pdf, f.read(), "application/pdf")},
            data={"document_type": "medical_bill"}
        )
    assert res.status_code == 201, f"Bill upload failed: {res.text}"
    bill_doc = res.json()
    print(f"Uploaded Bill: ID={bill_doc['id']} | Status={bill_doc['processing_status']} | Words Extracted={len(bill_doc['extracted_text'].split())}")

    # 2. Emergency Discharge Summary (Proves Emergency under EMTALA)
    discharge_pdf = "temp_discharge_summary.pdf"
    DemoSeeder.create_sample_pdf(
        discharge_pdf,
        "EMERGENCY CLINICAL DISCHARGE & OPERATIVE SUMMARY",
        [
            "Patient: Samuel Taylor | Admission Date: 2026-02-18 | Discharge Date: 2026-02-19",
            "Attending Surgeon: Dr. Catherine Hall, MD (General Surgery)",
            "Clinical Presentation: Acute severe abdominal pain, high fever, peritonitis.",
            "Clinical Assessment & Diagnosis: Acute Appendicitis (ICD-10 K35.80). Emergency surgical intervention mandatory.",
            "Emergency Admission under EMTALA regulations (42 U.S.C. § 1395dd). Direct transfer from Emergency Room to Operating Room.",
            "Procedure Performed: Laparoscopic Appendectomy (CPT 44970).",
            "Outcome: Patient stabilized, discharged in good condition."
        ]
    )

    with open(discharge_pdf, "rb") as f:
        res = client.post(
            f"/api/claims/{claim_id}/documents",
            files={"file": (discharge_pdf, f.read(), "application/pdf")},
            data={"document_type": "discharge_summary"}
        )
    assert res.status_code == 201, f"Discharge summary upload failed: {res.text}"
    discharge_doc = res.json()
    print(f"Uploaded Discharge Summary: ID={discharge_doc['id']} | Status={discharge_doc['processing_status']}")

    # Clean up temp files
    if os.path.exists(bill_pdf): os.remove(bill_pdf)
    if os.path.exists(discharge_pdf): os.remove(discharge_pdf)

    print("\n=== STEP 4: VERIFY TEXT EXTRACTION & ENTITIES ===")
    res = client.get(f"/api/documents/{bill_doc['id']}/text")
    assert res.status_code == 200
    text_data = res.json()
    entities = text_data.get("extracted_metadata") or {}
    print(f"Extracted Diagnoses: {entities.get('diagnosis_codes', [])}")
    print(f"Extracted Procedures: {entities.get('procedure_codes', [])}")
    print(f"Extracted Amounts: {entities.get('amounts', [])}")
    print(f"Extracted Dates: {entities.get('dates', [])}")

    print("\n=== STEP 5: TRIGGER CROSS-DOCUMENT ANALYSIS ===")
    res = client.post(f"/api/claims/{claim_id}/analyze")
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    analysis_res = res.json()
    print(f"Analysis Status: {analysis_res['status']}")
    print(f"Findings Generated: {analysis_res['findings_generated']}")
    print(f"Appeal Readiness Score: {analysis_res['readiness_score']}/100 ({analysis_res['readiness_level']})")
    print(f"Executive Summary: {analysis_res['summary']}")

    print("\n=== STEP 6: VERIFY CATEGORIZED FINDINGS IN DATABASE ===")
    res = client.get(f"/api/claims/{claim_id}/findings")
    assert res.status_code == 200
    findings = res.json()
    print(f"Total Findings: {findings['total_findings']}")
    for cat_name, items in [
        ("Extracted Facts", findings["extracted_facts"]),
        ("Rejection Analysis", findings["rejection_analysis"]),
        ("Cross-Doc Inconsistencies", findings["cross_document_inconsistencies"]),
        ("Missing Evidence", findings["missing_evidence"]),
        ("Document Integrity", findings["document_integrity_indicators"]),
        ("Recommended Actions", findings["recommended_actions"])
    ]:
        print(f"\n- Category [{cat_name}] ({len(items)} findings):")
        for f in items[:2]:
            print(f"  * [{f['severity'].upper()}] {f['title']}: {f['explanation'][:100]}...")

    print("\n=== STEP 7: VERIFY APPEAL READINESS SCORE BREAKDOWN ===")
    res = client.get(f"/api/claims/{claim_id}/readiness")
    assert res.status_code == 200
    score_breakdown = res.json()
    print(f"Overall Score: {score_breakdown['readiness_score']}% ({score_breakdown['readiness_level']})")
    for comp in score_breakdown["components"]:
        print(f"  * {comp['name']}: {comp['score']}/100 ({comp['weight']}% weight) -> {comp['impact']}")

    print("\n=== STEP 8: GENERATE EVIDENCE-LINKED APPEAL DRAFT ===")
    res = client.post(f"/api/claims/{claim_id}/appeals", json={"tone": "assertive_legal"})
    assert res.status_code == 201, f"Appeal generation failed: {res.text}"
    appeal = res.json()
    appeal_id = appeal["id"]
    print(f"Appeal Generated: ID={appeal_id} | Title='{appeal['appeal_title']}'")
    print(f"Initial Approval Status: {appeal['approval_status']}")
    assert "EMTALA" in appeal["draft_content"]
    assert "CLM-SLICE-2026-001" in appeal["draft_content"]
    print("Verified: Appeal draft cites EMTALA emergency exception and exact claim reference.")

    print("\n=== STEP 9: HUMAN REVIEWER APPROVAL & AUDIT ===")
    res = client.patch(
        f"/api/appeals/{appeal_id}",
        json={
            "approval_status": "approved",
            "reviewer_notes": "Reviewed by Lead Patient Advocate. Emergency surgery under EMTALA substantiated.",
            "approved_by": "Senior Reviewer Dr. Alan Ross, MD"
        }
    )
    assert res.status_code == 200
    updated_appeal = res.json()
    print(f"Updated Approval Status: {updated_appeal['approval_status']} by {updated_appeal['approved_by']}")

    print("\n=== STEP 10: EXPORT FINAL APPEAL TO PDF ===")
    res = client.get(f"/api/appeals/{appeal_id}/export?format=pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    pdf_bytes = res.content
    print(f"Exported PDF Successfully! Size: {len(pdf_bytes):,} bytes")
    assert len(pdf_bytes) > 1000

    print("\n=== STEP 11: VERIFY FRONTEND RENDERS CLAIM DETAIL (HTTP 200) ===")
    fe_res = httpx.get(f"http://localhost:3000/claims/{claim_id}", timeout=30.0)
    assert fe_res.status_code == 200, f"Frontend detail page failed: {fe_res.status_code}"
    print(f"Frontend Claim Detail: HTTP {fe_res.status_code} OK")

    fe_appeal_res = httpx.get(f"http://localhost:3000/claims/{claim_id}/appeal", timeout=30.0)
    assert fe_appeal_res.status_code == 200, f"Frontend appeal page failed: {fe_appeal_res.status_code}"
    print(f"Frontend Appeal Editor: HTTP {fe_appeal_res.status_code} OK")

    print("\n=======================================================")
    print(">>> VERTICAL SLICE FULLY VERIFIED AND PASSING 100% <<<")
    print("=======================================================")

if __name__ == "__main__":
    test_vertical_slice()
