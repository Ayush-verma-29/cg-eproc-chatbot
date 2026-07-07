"""
Script: create_crn_pdf.py
Creates a detailed PDF about CRN (Customer Reference Number) for the
CG e-Procurement Portal and ingests it into the vendor vector store.
"""
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

OUTPUT_PDF = (
    Path(__file__).parent.parent
    / "backend" / "data" / "vendor_manuals"
    / "CRN_Customer_Reference_Number_Guide.pdf"
)

CRN_CONTENT = """\
--- Page 1 ---
CRN - Customer Reference Number
Complete Guide for Vendors on the Chhattisgarh e-Procurement Portal

WHAT IS CRN?

CRN stands for Customer Reference Number.
It is a unique identification number issued by CHiPS (Chhattisgarh Infotech Promotion Society)
to vendors who register on the Chhattisgarh e-Procurement Portal (eproc.cgstate.gov.in).

CHiPS is the implementing agency of the CG e-Procurement Portal on behalf of the
Government of Chhattisgarh.

CRN is a mandatory field during online vendor registration if the vendor belongs to
Class A, B, C, or D. New vendors of these classes must upload a scanned copy of their
CRN Certificate issued by CHiPS during the registration process.

--- Page 2 ---
WHO NEEDS A CRN?

CRN is required for:
1. Vendors with Vendor Class A, B, C, or D who were previously enrolled with CHiPS.
2. Vendors who have physically submitted their registration documents to CHiPS office.
3. Vendors who have already obtained a Customer Reference Number through the offline process.

CRN may NOT be required for:
- Vendors registering for the first time without any prior CHiPS enrollment.
  (They will receive a CRN after completing registration.)
- Vendors in vendor classes other than A, B, C, D (subject to portal configuration).

--- Page 3 ---
HOW TO OBTAIN A CRN?

Step 1: Visit the CHiPS Office
   Contact CHiPS - Chhattisgarh Infotech Promotion Society, Raipur, Chhattisgarh.
   Alternatively, call the Integrated e-Procurement Help Desk: 1800-419-9140

Step 2: Submit Required Documents
   - PAN Card (mandatory)
   - Company or Firm registration documents
   - GST registration certificate (if applicable)
   - Bank account details
   - Authorized signatory details and contact information

Step 3: Receive CRN Certificate
   - After verification of documents, CHiPS issues the CRN Certificate.
   - The certificate contains your unique Customer Reference Number.
   - Keep a scanned copy of this certificate ready for online portal registration.

Step 4: Use CRN for Online Registration
   - Log on to eproc.cgstate.gov.in
   - During Supplier or Vendor Registration, enter your CRN (Customer Reference Number).
   - Upload the scanned copy of the CRN Certificate when prompted.

--- Page 4 ---
CRN DURING ONLINE VENDOR REGISTRATION - STEP BY STEP

When registering as a new vendor on the CG e-Procurement Portal, the CRN field appears
in the registration form. Below is how CRN fits into the overall vendor registration:

Step 1: Visit eproc.cgstate.gov.in
   Click on "Supplier Registration" or "New Supplier Registration".

Step 2: Enter Basic Details
   - Fill in PAN Card number (mandatory)
   - Enter preferred Login Code
   - Enter all business coordinates related to bidding

Step 3: Enter CRN (Customer Reference Number)
   - If your Vendor Class is A, B, C, or D: enter your CRN in the designated field.
   - Upload scanned copy of your CRN Certificate (clear, legible scan in PDF or JPG).
   - If you do not have a CRN yet, contact CHiPS at 1800-419-9140.

Step 4: Complete Registration Form
   - Fill in Authorized Signatory details
   - Fill in Contact Person details
   - Add Additional Contact information
   - Enter Bank Account details (for EMD refunds and payments)
   - Fill in Vendor Business Partner information

Step 5: Upload CRN Certificate
   - After entering all details, you will be asked for validation.
   - Upload the scanned CRN certificate at the designated upload section.
   - Press "Save Next" to continue (Section 3.4 of Vendor Registration Manual).

Step 6: Complete DSC Selection
   - After CRN upload and captcha entry, save changes (Section 3.5).
   - Select the appropriate Digital Signature Certificate (DSC) (Section 3.6).
   - Click "Confirmation" to accept terms and conditions (Sections 3.7 and 3.8).

--- Page 5 ---
WHAT INFORMATION IS ON THE CRN CERTIFICATE?

A CRN Certificate issued by CHiPS typically contains:
- Vendor or Supplier Full Name or Company Name
- Customer Reference Number (CRN)
- Vendor Class (A, B, C, or D)
- Date of issue
- CHiPS official stamp and signature
- Registration validity period (if applicable)

VENDOR CLASSES ON THE CG e-PROCUREMENT PORTAL

The portal classifies vendors into different classes:
- Class A: Large enterprises or corporations
- Class B: Medium enterprises
- Class C: Small enterprises
- Class D: Micro and small enterprises or Startups

MSME and Startup vendors may be eligible for EMD exemption and price preference
as per Government of India policy.

--- Page 6 ---
CRN FOR EXISTING VENDORS

If you are an existing vendor previously registered with CHiPS:
- Your CRN may already be on record with CHiPS.
- When updating registration details on the portal, the system may display
  previously submitted data including your CRN (Customer Reference Number).
- Contact CHiPS Help Desk (1800-419-9140) if your CRN is lost or forgotten.
- CHiPS can verify your identity and reissue or confirm your CRN.

IMPORTANT NOTES ABOUT CRN:
- CRN is unique to each vendor. Do not share your CRN with others.
- CRN must be entered accurately during portal registration.
- Incorrect CRN will result in registration failure or rejection.
- If there is a discrepancy between your submitted CRN and CHiPS records,
  the registration may be put on hold.
- All disputes or queries related to CRN must be resolved through CHiPS Help Desk.

--- Page 7 ---
DIGITAL SIGNATURE CERTIFICATE (DSC) AND CRN

After completing CRN entry and other registration details, vendors must have a valid DSC:
- DSC (Digital Signature Certificate) is mandatory for online registration and bid submission.
- Class II or Class III DSC with Signing and Encryption capability is required.
- Approved Certifying Authorities (CA): e-Mudhra, GNFC, IDRBT, MTNLTrustline, NIC, Safescrypt.
- Refer to http://www.cca.gov.in for the list of licensed CAs.
- DSC procurement may take 7-10 working days. Obtain it early before registering.

ENROLLMENT FEE
- One-time Enrollment Fee: Rs. 500 (payable online during registration)
- Annual Renewal Fee: Rs. 100 per year thereafter

--- Page 8 ---
CONTACT INFORMATION AND SUPPORT FOR CRN QUERIES

For any queries related to CRN (Customer Reference Number), CHiPS Registration,
or Vendor Registration:

Integrated e-Procurement Help Desk:
- Toll-Free Number: 1800-419-9140
- Available for support and assistance regarding CRN and registration issues.

CHiPS Office:
- Organization: Chhattisgarh Infotech Promotion Society (CHiPS)
- Portal: eproc.cgstate.gov.in

COMMON CRN ISSUES AND SOLUTIONS:

Issue: "CRN not found" error during registration
Solution: Contact CHiPS Help Desk at 1800-419-9140 with your company details
          and previous enrollment reference.

Issue: CRN Certificate is damaged or lost
Solution: Visit CHiPS office or contact Help Desk for re-issuance with identity proof.

Issue: CRN mismatch with portal records
Solution: Contact CHiPS Help Desk immediately. Do not attempt multiple registrations
          with incorrect CRN.

Issue: First-time vendor without any CHiPS history
Solution: Proceed with registration without CRN if your vendor class does not require it,
          or contact CHiPS to initiate enrollment and obtain your Customer Reference Number.
"""


def create_pdf():
    try:
        from fpdf import FPDF

        class CRNGuide(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 9)
                self.set_text_color(0, 100, 0)
                self.cell(
                    0, 7,
                    "Chhattisgarh e-Procurement Portal - CRN (Customer Reference Number) Guide",
                    align="C", new_x="LMARGIN", new_y="NEXT"
                )
                self.set_text_color(0, 0, 0)
                self.ln(1)

            def footer(self):
                self.set_y(-11)
                self.set_font("Helvetica", "I", 7)
                self.set_text_color(128, 128, 128)
                self.cell(
                    0, 5,
                    f"Page {self.page_no()} | Help Desk: 1800-419-9140 | eproc.cgstate.gov.in",
                    align="C"
                )

        pdf = CRNGuide()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(20, 18, 20)   # left, top, right — generous margins

        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        usable_w = pdf.w - pdf.l_margin - pdf.r_margin  # safe width for multi_cell

        for line in CRN_CONTENT.split("\n"):
            stripped = line.strip()

            if not stripped:
                pdf.ln(2)

            elif stripped.startswith("--- Page"):
                pdf.add_page()
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(160, 160, 160)
                pdf.multi_cell(usable_w, 4, stripped)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(1)

            elif stripped.isupper() and len(stripped) > 8:
                # Section heading
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 80, 0)
                pdf.multi_cell(usable_w, 6, stripped)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", size=10)
                pdf.ln(1)

            elif stripped.startswith("Step "):
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(usable_w, 5, stripped)
                pdf.set_font("Helvetica", size=10)

            elif stripped.startswith("-"):
                # Bullet — indent with spaces instead of set_x to avoid overflow
                indent = "    "
                pdf.multi_cell(usable_w, 5, indent + stripped)

            elif stripped[0].isdigit() and len(stripped) > 2 and stripped[1] in ".":
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(usable_w, 5, stripped)
                pdf.set_font("Helvetica", size=10)

            elif stripped.startswith("Issue:") or stripped.startswith("Solution:"):
                pdf.set_font("Helvetica", "B" if stripped.startswith("Issue:") else "", 10)
                pdf.multi_cell(usable_w, 5, stripped)
                pdf.set_font("Helvetica", size=10)

            else:
                pdf.multi_cell(usable_w, 5, stripped)

        pdf.output(str(OUTPUT_PDF))
        print(f"[OK] CRN PDF created: {OUTPUT_PDF}")
        return True

    except Exception as e:
        print(f"[ERROR] PDF creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def ingest_single_file():
    """Ingest only the CRN PDF into the vendor vector store (adds to existing)."""
    from app.services.document_processor import DocumentProcessor
    from app.services.vector_store import VectorStoreManager
    from langchain.schema import Document

    processor = DocumentProcessor()
    vsm = VectorStoreManager()

    print(f"\nProcessing: {OUTPUT_PDF.name}")

    text, _ = processor.extract_text_from_pdf(str(OUTPUT_PDF))
    if not text.strip():
        print("No text extracted from CRN PDF")
        return

    doc = Document(
        page_content=text,
        metadata={
            "source": OUTPUT_PDF.name,
            "file_path": str(OUTPUT_PDF),
            "role": "vendor",
            "file_size": OUTPUT_PDF.stat().st_size,
            "processed_date": str(OUTPUT_PDF.stat().st_mtime),
            "topics": "crn, customer reference number, registration, vendor registration, portal, chips"
        }
    )

    chunks = processor.text_splitter.split_documents([doc])

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"vendor_{OUTPUT_PDF.stem}_chunk_{i:04d}"
        chunk.metadata["chunk_index"] = i
        chunk.metadata["total_chunks"] = len(chunks)
        chunk.metadata["role"] = "vendor"
        chunk.metadata["source_type"] = "pdf"

    print(f"   {len(chunks)} chunks created")
    vsm.add_vendor_documents(chunks)
    print(f"[OK] CRN PDF ingested into vendor vector store ({len(chunks)} chunks)")

    stats = vsm.get_collection_stats()
    print(f"\n[INFO] Vendor store total: {stats.get('vendor_documents', 0)} chunks")


if __name__ == "__main__":
    print("=" * 60)
    print("  CRN (Customer Reference Number) PDF Creator & Ingest")
    print("=" * 60)

    if create_pdf():
        ingest_single_file()
    else:
        print("\nFailed. Ensure fpdf2 is installed: pip install fpdf2")
