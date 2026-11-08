import os

path = os.path.join(os.path.dirname(__file__), "legal_renderer.py")

with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target = '<h2 class="text-base sm:text-lg font-black text-slate-900">7. Governing Law & Jurisdiction</h2>'
target_full = """    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">7. Governing Law & Jurisdiction</h2>
        <p>These Terms shall be governed by and construed in accordance with the laws of India. Any disputes arising from these Terms or Platform usage shall be subject to the exclusive jurisdiction of the competent courts in India.</p>
    </section>"""

replacement = """    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">7. Governing Law & Jurisdiction</h2>
        <p>These Terms shall be governed by and construed in accordance with the laws of India. Any disputes arising from these Terms or Platform usage shall be subject to the exclusive jurisdiction of the competent courts in India.</p>
    </section>

    <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-black text-slate-900">8. Contact & Official Notices</h2>
        <p>For any legal inquiries, terms clarification, or official notices, please contact our legal desk at <a href="mailto:almondjobs.official@gmail.com" class="text-violet-600 underline font-semibold">almondjobs.official@gmail.com</a>.</p>
    </section>"""

if target_full in c:
    c = c.replace(target_full, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Added Section 8 to Terms of Service successfully!")
else:
    print("target_full not found, checking line endings...")
    c = c.replace("\r\n", "\n")
    target_full = target_full.replace("\r\n", "\n")
    replacement = replacement.replace("\r\n", "\n")
    if target_full in c:
        c = c.replace(target_full, replacement, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(c)
        print("Added Section 8 with normalized line endings!")
