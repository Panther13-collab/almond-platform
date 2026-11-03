import re

p = r"d:\Projects\AntigtavityApps\JobHunt\SK\platform\templates\index.html"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update resend & spam notice
old_resend = """                    <div class="flex items-center justify-between text-[11px] pt-1">
                        <button type="button" onclick="handleResendOtp()" class="text-violet-700 font-bold hover:underline cursor-pointer">
                            Resend Code
                        </button>
                        <button type="button" onclick="cancelOtpVerification()" class="text-slate-500 hover:text-slate-800 cursor-pointer">
                            &larr; Change Email
                        </button>
                    </div>"""

new_resend = """                    <!-- Cooldown Countdown & Resend Button (120s timer) -->
                    <div class="flex items-center justify-between text-[11px] pt-1">
                        <div id="resendCountdownContainer">
                            <span id="resendTimerNotice" class="text-slate-400 font-semibold flex items-center gap-1.5 select-none">
                                <span class="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse"></span>
                                <span>Resend Code in <strong id="resendTimerSecs" class="font-mono text-violet-700 font-bold">120</strong>s</span>
                            </span>
                            <button type="button" id="resendActiveBtn" onclick="handleResendOtp()" class="hidden text-violet-700 font-bold hover:underline cursor-pointer flex items-center gap-1">
                                <i data-lucide="rotate-cw" class="w-3.5 h-3.5"></i>
                                <span>Resend OTP Code</span>
                            </button>
                        </div>
                        <button type="button" onclick="cancelOtpVerification()" class="text-slate-500 hover:text-slate-800 cursor-pointer transition">
                            &larr; Change Email
                        </button>
                    </div>

                    <!-- Spam Folder Alert & Guidance -->
                    <div id="authSpamNotice" class="p-2.5 rounded-xl bg-amber-50/90 border border-amber-200/90 text-amber-950 text-xs flex items-start gap-2 shadow-2xs">
                        <i data-lucide="mail-question" class="w-4 h-4 text-amber-600 shrink-0 mt-0.5"></i>
                        <div>
                            <p class="font-black text-[11px] text-amber-950 flex items-center gap-1">
                                <span>Can't find the email in your inbox?</span>
                            </p>
                            <p id="authSpamNoticeText" class="text-[10.5px] text-amber-800 font-medium leading-relaxed mt-0.5">
                                Please check your <strong>Spam / Junk</strong> folder. If it arrived there, tap <em>"Report Not Spam"</em> so future job alerts and direct portals reach you instantly.
                            </p>
                        </div>
                    </div>"""

# 2. Add authWelcomeView right after authProfileView
old_profile_view_end = """                    <button type="button" onclick="handleLogout()" class="py-2 px-4 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs transition cursor-pointer flex items-center gap-1.5">
                        <i data-lucide="log-out" class="w-3.5 h-3.5 text-rose-600"></i>
                        <span>Log Out</span>
                    </button>
                </div>
            </div>"""

new_welcome_view = """                    <button type="button" onclick="handleLogout()" class="py-2 px-4 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs transition cursor-pointer flex items-center gap-1.5">
                        <i data-lucide="log-out" class="w-3.5 h-3.5 text-rose-600"></i>
                        <span>Log Out</span>
                    </button>
                </div>
            </div>

            <!-- VIEW 3: WELCOME NOTE / CELEBRATION (Shown after OTP verification succeeds) -->
            <div id="authWelcomeView" class="hidden text-center py-2 space-y-4 animate-in fade-in zoom-in-95 duration-200">
                <div class="relative w-16 h-16 mx-auto flex items-center justify-center rounded-3xl bg-gradient-to-tr from-violet-600 to-indigo-600 text-white shadow-xl shadow-violet-500/25">
                    <i data-lucide="check" class="w-8 h-8 text-white stroke-[3]"></i>
                    <span class="absolute -top-1 -right-1 flex h-4 w-4">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                    </span>
                </div>

                <div>
                    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-bold mb-2">
                        <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                        <span>Candidate Account Verified</span>
                    </div>
                    <h3 class="text-xl font-black text-slate-950 tracking-tight">
                        Welcome to Almond Jobs, <span id="welcomeUserName" class="text-violet-600">Candidate</span>!
                    </h3>
                    <p class="text-xs text-slate-600 mt-1 max-w-xs mx-auto leading-relaxed">
                        Your account has been verified. You now have full direct corporate application access.
                    </p>
                </div>

                <!-- Verified Features Card -->
                <div class="bg-slate-50 border border-slate-200/90 rounded-2xl p-3.5 text-left space-y-2.5 text-xs">
                    <div class="flex items-center gap-2.5 text-slate-800">
                        <div class="w-5 h-5 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                            <i data-lucide="check" class="w-3.5 h-3.5 stroke-[3]"></i>
                        </div>
                        <span class="text-[11.5px] font-medium"><strong>Direct Enterprise Access:</strong> Ashby, Greenhouse, Lever, Workday</span>
                    </div>
                    <div class="flex items-center gap-2.5 text-slate-800">
                        <div class="w-5 h-5 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                            <i data-lucide="check" class="w-3.5 h-3.5 stroke-[3]"></i>
                        </div>
                        <span class="text-[11.5px] font-medium"><strong>0% Recruiter Spread:</strong> Zero third-party headhunters</span>
                    </div>
                    <div class="flex items-center gap-2.5 text-slate-800">
                        <div class="w-5 h-5 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                            <i data-lucide="check" class="w-3.5 h-3.5 stroke-[3]"></i>
                        </div>
                        <span class="text-[11.5px] font-medium"><strong>Skill Gap Vector Intelligence:</strong> Live keyword optimizer ready</span>
                    </div>
                </div>

                <button type="button" onclick="handleWelcomeDone()" class="w-full py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-black text-xs uppercase tracking-wider rounded-xl shadow-lg transition transform active:scale-98 cursor-pointer flex items-center justify-center gap-2">
                    <span>Enter Platform & Explore Feeds</span>
                    <i data-lucide="arrow-right" class="w-4 h-4 text-white"></i>
                </button>
            </div>"""

updated = False
# Try LF and CRLF replacements
for target, repl in [(old_resend, new_resend), (old_profile_view_end, new_welcome_view)]:
    if target in text:
        text = text.replace(target, repl)
        updated = True
    elif target.replace("\n", "\r\n") in text:
        text = text.replace(target.replace("\n", "\r\n"), repl.replace("\n", "\r\n"))
        updated = True
    else:
        print(f"Warning: target not found for {target[:40]}")

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated index.html successfully! Updated flag:", updated)
