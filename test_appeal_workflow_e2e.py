import httpx
import sys

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"

def test_full_workflow():
    client = httpx.Client(timeout=30.0)
    print("=" * 60)
    print(" CLAIMFORGE APPEAL WORKFLOW: COMPLETE END-TO-END VERIFICATION")
    print("=" * 60)

    # 1. Health check
    print("\n[1] Checking Backend & Frontend Health...")
    r = client.get(f"{BACKEND_URL}/health")
    assert r.status_code == 200, f"Backend failed: {r.text}"
    print(f"    [OK] Backend API: HTTP 200 ({r.json()['status']})")

    r_fe = client.get(FRONTEND_URL)
    assert r_fe.status_code == 200, f"Frontend failed: {r_fe.status_code}"
    print(f"    [OK] Frontend Server: HTTP 200")

    # 2. Reset and seed demo scenarios
    print("\n[2] Seeding Demo Cases via Backend API...")
    r_seed = client.post(f"{BACKEND_URL}/api/demo/seed")
    assert r_seed.status_code in [200, 201], f"Seeding failed: {r_seed.text}"
    seed_data = r_seed.json()
    seeded_ids = seed_data["seeded_claim_ids"]
    print(f"    [OK] Seeded {len(seeded_ids)} claims successfully.")

    # 3. Retrieve first case: Emergency Appendectomy
    claim_id = seeded_ids[0]
    print(f"\n[3] Loading Target Case (ID: {claim_id})...")
    r_claim = client.get(f"{BACKEND_URL}/api/claims/{claim_id}")
    assert r_claim.status_code == 200
    claim = r_claim.json()
    print(f"    [OK] Claim Ref: {claim['claim_reference']}")
    print(f"    [OK] Insurer: {claim['insurer_name']}")
    print(f"    [OK] Disputed Amount: ${claim['claim_amount']:,.2f}")
    print(f"    [OK] Denial Reason: '{claim['rejection_reason']}' (Code: {claim['rejection_code']})")

    # 4. Check Frontend Claim Detail Page
    print(f"\n[4] Verifying Frontend Claim Details Route (/claims/{claim_id})...")
    r_detail_page = client.get(f"{FRONTEND_URL}/claims/{claim_id}")
    assert r_detail_page.status_code == 200
    print(f"    [OK] Claim Detail Page: HTTP 200 OK")

    # 5. Fetch Categorized Findings
    print(f"\n[5] Fetching Extracted Findings for Claim...")
    r_findings = client.get(f"{BACKEND_URL}/api/claims/{claim_id}/findings")
    assert r_findings.status_code == 200
    findings_data = r_findings.json()
    all_findings = []
    for cat in ["rejection_analysis", "cross_document_inconsistencies", "missing_evidence", "extracted_facts", "recommended_actions", "document_integrity_indicators"]:
        all_findings.extend(findings_data.get(cat, []))
    print(f"    [OK] Total Findings Discovered: {len(all_findings)}")
    assert len(all_findings) >= 2, "Expected multiple findings"

    # Select specific findings for the appeal
    selected_findings = all_findings[:2]
    selected_ids = [f["id"] for f in selected_findings]
    print(f"    [OK] Reviewer Selected {len(selected_ids)} Findings:")
    for f in selected_findings:
        print(f"      * [{f['category'].upper()}] {f['title']}")

    # 6. Generate Appeal with Selected Findings
    print(f"\n[6] Generating Grounded Appeal Draft with Selected Findings...")
    r_appeal = client.post(
        f"{BACKEND_URL}/api/claims/{claim_id}/appeals",
        json={
            "tone": "assertive_legal",
            "selected_finding_ids": selected_ids,
            "custom_instructions": "Patient presented with acute peritonitis requiring immediate surgical stabilization."
        }
    )
    assert r_appeal.status_code == 201, f"Appeal generation failed: {r_appeal.text}"
    appeal = r_appeal.json()
    appeal_id = appeal["id"]
    print(f"    [OK] Appeal Created: ID={appeal_id}")
    print(f"    [OK] Title: '{appeal['appeal_title']}'")
    print(f"    [OK] Approval Status: {appeal['approval_status']}")
    print(f"    [OK] Included Findings Count: {len(appeal['included_finding_ids'])}")
    assert appeal["included_finding_ids"] == selected_ids

    # Verify no invented facts
    draft = appeal["draft_content"]
    assert claim["claim_reference"] in draft
    assert claim["insurer_name"] in draft
    assert f"${claim['claim_amount']:,.2f}" in draft
    assert "EMTALA" in draft  # Emergency exception properly cited for emergency claim
    assert "acute peritonitis" in draft
    print("    [OK] Grounding Verified: Real claim info, EMTALA statutory grounds, and reviewer context matched.")

    # 7. Check Frontend Appeal Editor Route
    print(f"\n[7] Verifying Frontend Appeal Workspace Route (/claims/{claim_id}/appeal)...")
    r_appeal_page = client.get(f"{FRONTEND_URL}/claims/{claim_id}/appeal")
    assert r_appeal_page.status_code == 200
    print(f"    [OK] Appeal Workspace Page: HTTP 200 OK")

    # 8. Test Reviewer Editing & Saving Draft
    print(f"\n[8] Testing Reviewer Edit & Save Cycle...")
    edited_text = draft + "\n\n**Reviewer Clinical Confirmation:** Surgeon confirmed direct transfer from ER to OR without delay."
    r_save = client.patch(
        f"{BACKEND_URL}/api/appeals/{appeal_id}",
        json={
            "appeal_title": f"Expedited EMTALA Appeal - {claim['claim_reference']}",
            "draft_content": edited_text,
            "reviewer_notes": "Reviewed and amended with emergency room timeline."
        }
    )
    assert r_save.status_code == 200
    updated_appeal = r_save.json()
    assert "Surgeon confirmed direct transfer" in updated_appeal["draft_content"]
    assert updated_appeal["appeal_title"] == f"Expedited EMTALA Appeal - {claim['claim_reference']}"
    print("    [OK] Draft Edit Saved and Persisted Successfully.")

    # 9. Test Reviewer Rejection Flow
    print(f"\n[9] Testing Reviewer Rejection Flow...")
    r_reject = client.patch(
        f"{BACKEND_URL}/api/appeals/{appeal_id}",
        json={
            "approval_status": "rejected",
            "reviewer_notes": "Returned for revision: Please verify attending surgeon NPI."
        }
    )
    assert r_reject.status_code == 200
    rejected_appeal = r_reject.json()
    assert rejected_appeal["approval_status"] == "rejected"
    assert rejected_appeal["approved_at"] is None
    
    # Check claim status updated to in_review
    r_claim_after_reject = client.get(f"{BACKEND_URL}/api/claims/{claim_id}")
    assert r_claim_after_reject.json()["status"] == "in_review"
    print("    [OK] Rejection Verified: Status updated to 'rejected', parent claim status set to 'in_review'.")

    # 10. Test Reviewer Approval Flow
    print(f"\n[10] Testing Reviewer Approval Flow...")
    r_approve = client.patch(
        f"{BACKEND_URL}/api/appeals/{appeal_id}",
        json={
            "approval_status": "approved",
            "approved_by": "Dr. Sarah Jenkins, MD - Chief Medical Reviewer",
            "reviewer_notes": "Attending surgeon NPI confirmed. All statutory grounds verified for submission."
        }
    )
    assert r_approve.status_code == 200
    approved_appeal = r_approve.json()
    assert approved_appeal["approval_status"] == "approved"
    assert approved_appeal["approved_by"] == "Dr. Sarah Jenkins, MD - Chief Medical Reviewer"
    assert approved_appeal["approved_at"] is not None

    # Check claim status updated to completed
    r_claim_after_approve = client.get(f"{BACKEND_URL}/api/claims/{claim_id}")
    assert r_claim_after_approve.json()["status"] == "completed"
    print("    [OK] Approval Verified: Status updated to 'approved', audit timestamp recorded, claim status set to 'completed'.")

    # 11. Test Working PDF Export
    print(f"\n[11] Testing Working PDF Export...")
    r_pdf = client.get(f"{BACKEND_URL}/api/appeals/{appeal_id}/export?format=pdf")
    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"] == "application/pdf"
    assert r_pdf.content.startswith(b"%PDF-")
    print(f"    [OK] Official PDF Export: HTTP 200, Content-Type: application/pdf, Size: {len(r_pdf.content):,} bytes")

    # 12. Test Working TXT Export
    print(f"\n[12] Testing Working Text Export...")
    r_txt = client.get(f"{BACKEND_URL}/api/appeals/{appeal_id}/export?format=txt")
    assert r_txt.status_code == 200
    assert "text/plain" in r_txt.headers["content-type"]
    assert claim["claim_reference"] in r_txt.text
    print(f"    [OK] Text Export: HTTP 200, Content-Type: text/plain, Characters: {len(r_txt.text):,}")

    print("\n" + "=" * 60)
    print(" ALL 12 WORKFLOW STEPS VERIFIED & PASSING WITH 100% SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    test_full_workflow()
