import unittest
import os
import time
import json
from fastapi.testclient import TestClient

from app import app
from core.config import Config
from core.auth_db import (
    save_candidate_feedback,
    get_all_candidate_feedback,
    reply_to_candidate_feedback,
    get_revenue_analytics,
    record_successful_payment,
    record_contribution_payment
)
from core.doc_exporter import (
    is_export_job_locked,
    export_to_docx,
    _export_pdf_pure_python,
    export_to_csv,
    VIP_PORTAL_URL
)

class TestPlatformUpgradesAndFeedback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.admin_key = Config.ADMIN_SECRET_KEY

    def test_01_candidate_feedback_lifecycle(self):
        """Test submitting feedback, retrieving in admin, and replying."""
        # 1. Submit feature suggestion
        res = self.client.post("/api/feedback/submit", json={
            "category": "feature_suggestion",
            "rating": 5,
            "message": "Add an alert when a tier-1 company posts a new SDE-1 opening!",
            "user_email": "candidate_test@example.com",
            "user_id": "cand_test_uid_101"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("ok") or data.get("status") == "success")
        fb_id = data.get("id")
        self.assertIsNotNone(fb_id)

        # 2. Submit hired celebration
        res2 = self.client.post("/api/feedback/submit", json={
            "category": "praise_hired",
            "rating": 5,
            "message": "Just got offer letter from Swiggy! Applied directly via Almond Jobs.",
            "hired_company": "Swiggy",
            "user_email": "swiggy_hire@example.com"
        })
        self.assertEqual(res2.status_code, 200)

        # 3. Submit broken link
        res3 = self.client.post("/api/feedback/submit", json={
            "category": "broken_link",
            "rating": 4,
            "message": "Greenhouse link expired on Job #482",
            "page_url": "https://almondjobs.com/#discovery"
        })
        self.assertEqual(res3.status_code, 200)

        # 4. Reject empty message
        res_fail = self.client.post("/api/feedback/submit", json={
            "category": "feature_suggestion",
            "message": ""
        })
        self.assertEqual(res_fail.status_code, 400)

        # 5. Admin unauthorized check
        res_unauth = self.client.get("/api/admin/feedback")
        self.assertEqual(res_unauth.status_code, 401)

        # 6. Admin authorized fetch
        res_admin = self.client.get(f"/api/admin/feedback?key={self.admin_key}")
        self.assertEqual(res_admin.status_code, 200)
        admin_data = res_admin.json()
        self.assertEqual(admin_data.get("status"), "success")
        items = admin_data.get("feedback", [])
        self.assertTrue(len(items) >= 3)

        # Check category filter
        res_filt = self.client.get(f"/api/admin/feedback?category=praise_hired&key={self.admin_key}")
        self.assertEqual(res_filt.status_code, 200)
        filt_items = res_filt.json().get("feedback", [])
        self.assertTrue(all(f.get("category") == "praise_hired" for f in filt_items))

        # 7. Reply to feedback
        res_reply = self.client.post("/api/admin/feedback/reply", json={
            "id": fb_id,
            "reply": "Thank you for the idea! Real-time alerts for tier-1 roles are now in active rollout.",
            "key": self.admin_key
        })
        self.assertEqual(res_reply.status_code, 200)
        self.assertEqual(res_reply.json().get("status"), "success")

    def test_02_revenue_analytics_and_gateway_verification(self):
        """Test revenue metrics computation, daily trends, and HMAC signature ledger."""
        now = time.time()
        # Seed test VIP and Coffee payments
        record_successful_payment(
            user_id="rev_test_cand_1@example.com",
            payment_id=f"pay_vip_test_{int(now)}",
            order_id=f"order_vip_{int(now)}",
            amount_inr=2599.0,
            plan_name="VIP Pass (3-Month)"
        )
        record_contribution_payment(
            user_id="coffee_supporter_test",
            payment_id=f"pay_coffee_test_{int(now)}",
            order_id=f"order_coffee_{int(now)}",
            amount_inr=1455.0,
            plan_name="Coffee Contribution (3 Coffees)",
            supporter_name="Aarav K",
            supporter_message="Thanks for keeping jobs broker-free!",
            currency="INR"
        )

        # Admin route unauthorized check
        res_unauth = self.client.get("/api/admin/revenue-analytics")
        self.assertEqual(res_unauth.status_code, 401)

        # Admin authorized check
        res = self.client.get(f"/api/admin/revenue-analytics?key={self.admin_key}")
        self.assertEqual(res.status_code, 200)
        rev = res.json()
        self.assertEqual(rev.get("status"), "success")

        summary = rev.get("summary", {})
        self.assertGreaterEqual(summary.get("total_revenue_inr", 0), 4054.0)
        self.assertGreaterEqual(summary.get("vip_revenue_inr", 0), 2599.0)
        self.assertGreaterEqual(summary.get("coffee_revenue_inr", 0), 1455.0)
        self.assertGreaterEqual(summary.get("total_orders", 0), 2)

        # Daily trends
        trends = rev.get("daily_trends", [])
        self.assertTrue(len(trends) >= 1)

        # Verified transactions ledger
        txns = rev.get("transactions", [])
        self.assertTrue(len(txns) >= 2)
        # Verify HMAC verification flag on all transactions
        for t in txns:
            self.assertTrue(t.get("is_verified_hmac"))
            self.assertEqual(t.get("gateway"), "Razorpay Direct Gateway")
            self.assertIn("amount_formatted", t)

    def test_03_document_exporter_url_security_and_cleanliness(self):
        """Verify URL masking in PDF, Word, and CSV for free tier users and zero GitHub leaks."""
        test_jobs = [
            {
                "id": "job_locked_1",
                "title": "Staff Backend Engineer",
                "company": "Stripe",
                "source": "Greenhouse",
                "days_ago": 1,
                "is_locked": True,
                "url": "https://boards.greenhouse.io/stripe/jobs/998877",
                "cvmatch_score": 94,
                "comp_display": "₹45 LPA"
            },
            {
                "id": "job_unlocked_2",
                "title": "Software Engineer",
                "company": "Swiggy",
                "source": "Lever",
                "days_ago": 14,
                "is_locked": False,
                "url": "https://jobs.lever.co/swiggy/112233",
                "cvmatch_score": 88,
                "comp_display": "₹28 LPA"
            }
        ]
        profile = {
            "name": "Arjun Dev",
            "email": "arjun@example.com",
            "current_role": "Backend Engineer",
            "years_experience": 4,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]
        }

        # Verify lock detector
        self.assertTrue(is_export_job_locked(test_jobs[0], is_paid=False))
        self.assertFalse(is_export_job_locked(test_jobs[1], is_paid=False))
        self.assertFalse(is_export_job_locked(test_jobs[0], is_paid=True))

        out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "test_exports")
        os.makedirs(out_dir, exist_ok=True)

        # 1. Word export (.docx)
        docx_path = os.path.join(out_dir, "test_dossier.docx")
        export_to_docx(profile, test_jobs, docx_path, is_paid=False)
        self.assertTrue(os.path.exists(docx_path))
        # Inspect Word document text: locked URL must NOT be in text
        import docx
        doc = docx.Document(docx_path)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        self.assertNotIn("boards.greenhouse.io", full_text)
        self.assertNotIn("github", full_text.lower())
        self.assertIn("Confidential Role (VIP Pass Required)", full_text)

        # 2. Pure Python PDF fallback
        pdf_path = os.path.join(out_dir, "test_dossier.pdf")
        _export_pdf_pure_python(profile, test_jobs, pdf_path, is_paid=False)
        self.assertTrue(os.path.exists(pdf_path))

        # 3. CSV export
        csv_path = os.path.join(out_dir, "test_tracker.csv")
        export_to_csv(test_jobs, csv_path, is_paid=False)
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read()
        self.assertNotIn("boards.greenhouse.io", csv_content)
        self.assertIn(VIP_PORTAL_URL, csv_content)
        self.assertIn("[VIP LOCKED]", csv_content)
        self.assertNotIn("github", csv_content.lower())

    def test_04_templates_and_static_app_js_invariants(self):
        """Verify frontend invariants for hero freshers clarity, autocomplete, tickers, and badges."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        with open(os.path.join(base_dir, "templates", "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        with open(os.path.join(base_dir, "templates", "admin.html"), "r", encoding="utf-8") as f:
            admin_html = f.read()
        with open(os.path.join(base_dir, "static", "app.js"), "r", encoding="utf-8") as f:
            js = f.read()

        # index.html checks
        self.assertIn("Freshers &amp; Campus Notice", html)
        self.assertIn("0% recruiter spread", html)
        self.assertIn("heroLiveCrawlTicker", html)
        self.assertIn("curatedAutocompleteMenu", html)
        self.assertIn("Campus &amp; Freshers (0&ndash;1 YOE)", html)
        self.assertIn("coffeeHiredCheckbox", html)
        self.assertIn("Candidates hired directly via Almond Jobs at", html)
        self.assertIn("floatingFeedbackBtn", html)
        self.assertIn("candidateFeedbackModal", html)

        # admin.html checks
        self.assertIn("tab-btn-feedback", admin_html)
        self.assertIn("tab-btn-revenue", admin_html)
        self.assertIn("panel-feedback", admin_html)
        self.assertIn("panel-revenue", admin_html)
        self.assertIn("HMAC Gateway Status", admin_html)
        self.assertIn("100% HMAC Verified", admin_html)

        # app.js checks
        self.assertIn("Unlocks for public in", js)
        self.assertIn("VIPs are applying now", js)
        self.assertIn("🔥 Urgent Hiring", js)
        self.assertIn("US Remote (EST/PST)", js)
        self.assertIn("UK Remote (GMT)", js)
        self.assertIn("EU Remote (CET/GMT)", js)
        self.assertIn("India / IST Remote", js)
        self.assertIn("detectUserTimezoneCurrency", js)
        self.assertIn("launchOfferConfetti", js)
        self.assertIn("submitCandidateFeedback", js)
        self.assertIn("setCuratedSearchFilter", js)
        self.assertIn("renderCuratedAutocomplete", js)

if __name__ == "__main__":
    unittest.main()
