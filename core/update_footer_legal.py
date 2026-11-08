import os

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")

def update_footer():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        c = f.read()

    target = '<!-- Professional Company Navigation Links Attached at Bottom Right -->'
    replacement = '''<!-- Legal & Compliance Links for Razorpay Approval -->
                <div class="flex items-center gap-2 text-[9.5px] sm:text-[10px] text-slate-500 font-medium flex-wrap">
                    <a href="/terms" class="hover:text-violet-600 transition">Terms</a>
                    <span class="text-slate-300">•</span>
                    <a href="/privacy" class="hover:text-violet-600 transition">Privacy</a>
                    <span class="text-slate-300">•</span>
                    <a href="/refund-policy" class="hover:text-violet-600 transition">Refunds</a>
                    <span class="text-slate-300">•</span>
                    <a href="/contact" class="hover:text-violet-600 transition">Contact</a>
                </div>
                <!-- Professional Company Navigation Links Attached at Bottom Right -->'''

    if target in c and '/refund-policy' not in c:
        c = c.replace(target, replacement, 1)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write(c)
        print("Successfully updated footer with legal links!")
    else:
        print("Footer already updated or target not found.")

if __name__ == "__main__":
    update_footer()
