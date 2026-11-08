"""
Almond Jobs — Official Legal & Compliance Pages Renderer
Generates clean, professional Terms of Service, Privacy Policy,
Refund/Cancellation Policy, and Contact Us pages strictly meeting
Razorpay, RBI, and international digital commerce compliance standards.
"""

def _base_legal_layout(title: str, subtitle: str, content_html: str, canonical_path: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Almond Jobs</title>
    <meta name="description" content="{subtitle}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://almondjobs.com{canonical_path}">
    <link rel="icon" type="image/x-icon" href="/favicon.ico?v=4">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-stone-50 text-slate-900 min-h-screen flex flex-col justify-between antialiased">

    <!-- Top Navigation Header -->
    <header class="w-full bg-white/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40 px-4 sm:px-8 py-3.5 shadow-2xs">
        <div class="max-w-5xl mx-auto flex items-center justify-between">
            <a href="/" class="flex items-center gap-2.5 hover:opacity-90 transition">
                <img src="/static/logo.png" alt="Almond Jobs Logo" class="w-7 h-7 object-contain">
                <span class="font-black text-lg tracking-tight text-slate-950">Almond<span class="text-violet-600">Jobs</span></span>
            </a>
            <div class="flex items-center gap-3">
                <a href="/" class="px-4 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition">
                    &larr; Back to Platform
                </a>
                <a href="/#contribute" onclick="if(window.opener){{window.close();}}else{{window.location.href='/';}}" class="px-4 py-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold text-xs shadow-xs hover:scale-105 transition">
                    ☕ Support Almond
                </a>
            </div>
        </div>
    </header>

    <!-- Main Content Container -->
    <main class="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14 w-full flex-1">
        <div class="bg-white rounded-3xl p-6 sm:p-10 border border-slate-200 shadow-sm space-y-8">
            <div class="border-b border-slate-100 pb-5">
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-50 border border-violet-200 text-violet-800 text-[11px] font-bold mb-3">
                    <span>Official Policy Document</span>
                    <span class="text-slate-400">•</span>
                    <span>Last Updated: November 2026</span>
                </div>
                <h1 class="text-2xl sm:text-4xl font-black text-slate-950 tracking-tight">{title}</h1>
                <p class="text-slate-600 text-xs sm:text-sm mt-2">{subtitle}</p>
            </div>

            <div class="prose prose-slate max-w-none text-xs sm:text-sm leading-relaxed text-slate-700 space-y-6">
                {content_html}
            </div>
        </div>
    </main>

    <!-- Footer Links -->
    <footer class="w-full bg-white border-t border-slate-200 py-8 px-4 text-center text-xs text-slate-500">
        <div class="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <span>&copy; 2026 Almond Jobs Technologies. Direct Enterprise Career Intelligence.</span>
            <div class="flex items-center gap-4 font-semibold text-slate-600 flex-wrap justify-center">
                <a href="/terms" class="hover:text-violet-600 transition">Terms of Service</a>
                <span>•</span>
                <a href="/privacy" class="hover:text-violet-600 transition">Privacy Policy</a>
                <span>•</span>
                <a href="/refund-policy" class="hover:text-violet-600 transition">Refund &amp; Cancellation</a>
                <span>•</span>
                <a href="/contact" class="hover:text-violet-600 transition">Contact Us</a>
            </div>
        </div>
    </footer>

</body>
</html>
"""

def render_terms_page() -> str:
    content = """
    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">1. Acceptance of Terms</h2>
        <p>By accessing or using the services provided by Almond Jobs ("Almond Jobs", "we", "our", or "us") via https://almondjobs.com (the "Platform"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">2. Description of Service</h2>
        <p>Almond Jobs provides an AI-powered corporate applicant tracking system (ATS) ingestion and direct career discovery engine. We index public enterprise hiring portals (including Ashby, Greenhouse, Lever, Workday, and SmartRecruiters) and offer candidate dossier generation, keyword optimization, and direct employer application links without intermediary agency markups.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">3. User Accounts and Verification</h2>
        <p>Users may create accounts using verified email addresses or Google authentication. You agree to provide accurate, current, and complete information and are responsible for safeguarding your login credentials. You are solely responsible for all activities occurring under your account.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">4. Payments, Subscriptions, and Contributions</h2>
        <p>Access to certain features or voluntary support contributions ("Buy Almond Jobs a Coffee") are processed securely through our authorized payment gateway partner, <strong>Razorpay</strong>. All charges are in Indian Rupees (INR) or specified local currency. By initiating a payment, you authorize Razorpay and our payment infrastructure to process the specified amount via UPI, NetBanking, Debit/Credit Card, or Wallets.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">5. Prohibited Conduct</h2>
        <p>Users agree not to:</p>
        <ul class="list-disc pl-5 space-y-1">
            <li>Engage in unauthorized automated scraping, rate-limiting violations, or denial-of-service attempts against the Platform.</li>
            <li>Use the Platform for fraudulent job postings, unauthorized recruitment solicitations, or deceptive representations.</li>
            <li>Circumvent or tamper with security, authentication, or payment verification mechanisms.</li>
        </ul>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">6. Intellectual Property & Disclaimers</h2>
        <p>All proprietary code, algorithms, visual layouts, and content on Almond Jobs are the intellectual property of Almond Jobs Technologies. Employer trademarks (e.g. Ashby, Greenhouse, Lever, Workday) belong to their respective owners and are referenced solely for nominative identification of career portals.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">7. Governing Law & Jurisdiction</h2>
        <p>These Terms shall be governed by and construed in accordance with the laws of India. Any disputes arising from these Terms or Platform usage shall be subject to the exclusive jurisdiction of the competent courts in India.</p>
    </section>
    """
    return _base_legal_layout(
        title="Terms of Service",
        subtitle="Governing terms and conditions for using the Almond Jobs platform.",
        content_html=content,
        canonical_path="/terms"
    )

def render_privacy_page() -> str:
    content = """
    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">1. Information We Collect</h2>
        <p>We respect your privacy and collect only the minimum information necessary to deliver high-quality career intelligence services:</p>
        <ul class="list-disc pl-5 space-y-1">
            <li><strong>Account Information:</strong> Name, verified email address, and profile picture (when authenticating via Google OAuth).</li>
            <li><strong>Resume & Career Data:</strong> Text extracted from candidate resumes uploaded to synthesize STAR pitches and match direct ATS vacancies.</li>
            <li><strong>Transaction Records:</strong> Razorpay order ID, payment ID, amount, and timestamp. <em>We never store credit card numbers, CVVs, or UPI PINs; all sensitive payment credentials are securely handled by Razorpay in compliance with PCI-DSS.</em></li>
        </ul>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">2. How We Use Your Data</h2>
        <p>Your data is used solely to:</p>
        <ul class="list-disc pl-5 space-y-1">
            <li>Provide real-time matching between candidate skills and unadvertised enterprise job openings.</li>
            <li>Generate tailored STAR pitches and application dossiers on demand.</li>
            <li>Process payments and voluntary support contributions through Razorpay.</li>
            <li>Maintain platform security, prevent duplicate spam, and ensure reliable service delivery.</li>
        </ul>
        <p><strong>Zero Recruiter Selling:</strong> We do NOT sell, rent, or distribute your resume or contact details to third-party headhunters, staffing brokers, or marketing lists.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">3. Data Retention and Security</h2>
        <p>Uploaded documents and temporary processing artifacts are stored in encrypted environments with strict access controls. Users may request full account and data deletion at any time by contacting our privacy desk at <a href="mailto:privacy@almondjobs.com" class="text-violet-600 underline font-semibold">privacy@almondjobs.com</a>.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">4. Cookies and Analytics</h2>
        <p>We use lightweight local storage and session tokens to preserve authentication states across visits. Optional Google Analytics 4 (GA4) measurements track aggregate visitor interactions without capturing personally identifiable credentials.</p>
    </section>
    """
    return _base_legal_layout(
        title="Privacy Policy",
        subtitle="How Almond Jobs protects, uses, and respects candidate data.",
        content_html=content,
        canonical_path="/privacy"
    )

def render_refund_page() -> str:
    content = """
    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">1. Overview of Digital Services & Voluntary Contributions</h2>
        <p>Almond Jobs provides instant digital career tools, candidate profile optimizations, and a voluntary community support model ("Buy Almond Jobs a Coffee"). Because digital features and application dossiers are generated instantaneously upon access, please review our refund and cancellation terms below.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">2. 7-Day Refund Policy for Technical Billing Issues</h2>
        <p>We are committed to fair and transparent transactions. You are eligible for a <strong>100% full refund</strong> under any of the following circumstances:</p>
        <ul class="list-disc pl-5 space-y-1">
            <li><strong>Duplicate Charges:</strong> You were billed more than once for a single order due to network timeouts or gateway anomalies.</li>
            <li><strong>Service Delivery Failure:</strong> Your account was charged by Razorpay, but the corresponding feature or service was not activated within 24 hours.</li>
            <li><strong>Unauthorized Transactions:</strong> Documented unauthorized transaction reported immediately to our support team.</li>
        </ul>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">3. How to Request a Refund</h2>
        <p>To request a refund, please send an email to <a href="mailto:support@almondjobs.com" class="text-violet-600 underline font-semibold">support@almondjobs.com</a> within <strong>7 days</strong> of the transaction date with the following details:</p>
        <ul class="list-disc pl-5 space-y-1">
            <li>Registered Email Address used during payment</li>
            <li>Razorpay Payment ID (e.g. <code>pay_XXXXXXXXXXXXXX</code>)</li>
            <li>Brief description of the issue encountered</li>
        </ul>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">4. Refund Processing Timeline</h2>
        <p>Once approved, your refund will be initiated immediately through Razorpay and credited back to the <strong>original source of payment</strong> (Bank Account, UPI, Debit/Credit Card) within <strong>5 to 7 business days</strong>, depending on your bank's clearing cycle.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">5. Cancellation of Voluntary Support</h2>
        <p>Voluntary support contributions (one-time coffee purchases) do not recur automatically and carry zero recurring obligations. No cancellation is required as there are no hidden subscription renewals.</p>
    </section>
    """
    return _base_legal_layout(
        title="Cancellation & Refund Policy",
        subtitle="Transparent refund and billing dispute resolution guidelines.",
        content_html=content,
        canonical_path="/refund-policy"
    )

def render_contact_page() -> str:
    content = """
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pb-4">
        <div class="p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <h3 class="font-black text-slate-950 text-sm uppercase tracking-wider">Customer Support & Inquiries</h3>
            <p class="text-slate-600 text-xs leading-relaxed">For billing assistance, platform questions, technical troubleshooting, or contribution queries:</p>
            <div class="pt-2">
                <a href="mailto:support@almondjobs.com" class="inline-flex items-center gap-2 font-bold text-violet-700 hover:text-violet-900 text-sm">
                    <span>✉ support@almondjobs.com</span>
                </a>
                <p class="text-[11px] text-slate-500 mt-1">Average response time: 24–48 business hours</p>
            </div>
        </div>

        <div class="p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <h3 class="font-black text-slate-950 text-sm uppercase tracking-wider">Business & Partnerships</h3>
            <p class="text-slate-600 text-xs leading-relaxed">For corporate direct ATS ingestion, API access, or verified employer career feed integration:</p>
            <div class="pt-2">
                <a href="mailto:contact@almondjobs.com" class="inline-flex items-center gap-2 font-bold text-emerald-700 hover:text-emerald-900 text-sm">
                    <span>✉ contact@almondjobs.com</span>
                </a>
                <p class="text-[11px] text-slate-500 mt-1">Direct corporate integrations desk</p>
            </div>
        </div>
    </div>

    <section class="space-y-3 pt-4 border-t border-slate-100">
        <h2 class="text-base sm:text-lg font-black text-slate-900">Platform Operating Details</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-700">
            <div>
                <p class="font-bold text-slate-900">Operating Entity:</p>
                <p class="text-slate-600">Almond Jobs Technologies</p>
            </div>
            <div>
                <p class="font-bold text-slate-900">Operating Hours:</p>
                <p class="text-slate-600">Monday to Friday, 9:00 AM – 6:00 PM IST</p>
            </div>
            <div>
                <p class="font-bold text-slate-900">Official Website:</p>
                <p class="text-slate-600"><a href="https://almondjobs.com" class="underline hover:text-violet-600">https://almondjobs.com</a></p>
            </div>
            <div>
                <p class="font-bold text-slate-900">Grievance & Compliance Desk:</p>
                <p class="text-slate-600"><a href="mailto:grievance@almondjobs.com" class="underline hover:text-violet-600">grievance@almondjobs.com</a></p>
            </div>
        </div>
    </section>
    """
    return _base_legal_layout(
        title="Contact Us",
        subtitle="Get in touch with the Almond Jobs support and compliance desk.",
        content_html=content,
        canonical_path="/contact"
    )
