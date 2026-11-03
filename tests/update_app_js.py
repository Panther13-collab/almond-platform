import re

p = r"d:\Projects\AntigtavityApps\JobHunt\SK\platform\static\app.js"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add window.startResendOtpTimer and window.handleWelcomeDone
timer_code = """
window.startResendOtpTimer = function(durationSecs = 120) {
    if (window._resendOtpInterval) {
        clearInterval(window._resendOtpInterval);
        window._resendOtpInterval = null;
    }
    const timerNotice = document.getElementById("resendTimerNotice");
    const activeBtn = document.getElementById("resendActiveBtn");
    const timerSecs = document.getElementById("resendTimerSecs");
    const spamText = document.getElementById("authSpamNoticeText");

    if (timerNotice) timerNotice.classList.remove("hidden");
    if (activeBtn) activeBtn.classList.add("hidden");
    if (timerSecs) timerSecs.textContent = durationSecs;
    if (spamText) {
        spamText.innerHTML = `Please check your <strong>Spam / Junk</strong> folder. If it arrived there, tap <em>"Report Not Spam"</em> so future job alerts and direct portals reach you instantly.`;
    }

    let remaining = durationSecs;
    window._resendOtpInterval = setInterval(() => {
        remaining -= 1;
        if (timerSecs) timerSecs.textContent = remaining;
        if (remaining <= 0) {
            clearInterval(window._resendOtpInterval);
            window._resendOtpInterval = null;
            if (timerNotice) timerNotice.classList.add("hidden");
            if (activeBtn) activeBtn.classList.remove("hidden");
            if (spamText) {
                spamText.innerHTML = `120 seconds elapsed. If still not visible in your inbox or spam folder, tap <strong>Resend OTP Code</strong> above.`;
            }
            if (window.lucide) lucide.createIcons();
        }
    }, 1000);
};

window.handleWelcomeDone = function() {
    const authWelcomeView = document.getElementById("authWelcomeView");
    if (authWelcomeView) authWelcomeView.classList.add("hidden");
    window.cancelOtpVerification();
    window.closeProfileModal();
    window.updateTopProfileBar();

    // Resume pending search if any
    if (window._pendingJobSearch) {
        window._pendingJobSearch = false;
        const searchBtn = document.getElementById("searchJobsBtn");
        if (searchBtn && typeof executeSearch === "function") {
            executeSearch();
            window.goToSlide(2);
        }
    }
};
"""

# Insert before window.handleAuthSubmit
if "window.startResendOtpTimer" not in text:
    text = text.replace("window.handleAuthSubmit = async function(e) {", timer_code + "\nwindow.handleAuthSubmit = async function(e) {")

# 2. Trigger timer when OTP step is shown in handleAuthSubmit
old_trigger = """            if (otpInput) {
                otpInput.value = "";
                setTimeout(() => otpInput.focus(), 150);
            }"""

new_trigger = """            if (otpInput) {
                otpInput.value = "";
                setTimeout(() => otpInput.focus(), 150);
            }

            if (typeof window.startResendOtpTimer === "function") {
                window.startResendOtpTimer(120);
            }"""

if old_trigger in text:
    text = text.replace(old_trigger, new_trigger)
elif old_trigger.replace("\n", "\r\n") in text:
    text = text.replace(old_trigger.replace("\n", "\r\n"), new_trigger.replace("\n", "\r\n"))

# 3. Update handleVerifyOtpSubmit to show Welcome View instead of alert()
old_verify_success = """        window.cancelOtpVerification();
        window.updateTopProfileBar();
        window.closeProfileModal();

        alert(`Welcome to Almond Jobs, ${data.full_name || 'Candidate'}! Your account has been verified.`);

        // Resume pending search if any
        if (window._pendingJobSearch) {
            window._pendingJobSearch = false;
            const searchBtn = document.getElementById("searchJobsBtn");
            if (searchBtn && typeof executeSearch === "function") {
                executeSearch();
                window.goToSlide(2);
            }
        }"""

new_verify_success = """        if (window._resendOtpInterval) {
            clearInterval(window._resendOtpInterval);
            window._resendOtpInterval = null;
        }

        // Show celebratory in-app Welcome View instead of browser alert()
        const authFormView = document.getElementById("authFormView");
        const authContextNotice = document.getElementById("authContextNotice");
        const authWelcomeView = document.getElementById("authWelcomeView");
        const welcomeUserName = document.getElementById("welcomeUserName");
        const modalTitleText = document.getElementById("modalTitleText");
        const modalSubtitleText = document.getElementById("modalSubtitleText");

        if (authFormView) authFormView.classList.add("hidden");
        if (authContextNotice) authContextNotice.classList.add("hidden");
        if (modalTitleText) modalTitleText.textContent = "Welcome to Almond Jobs";
        if (modalSubtitleText) modalSubtitleText.textContent = "Account Verified & Active";
        if (welcomeUserName) welcomeUserName.textContent = data.full_name || "Candidate";
        if (authWelcomeView) authWelcomeView.classList.remove("hidden");
        if (window.lucide) lucide.createIcons();

        // Update brand bar indicators immediately
        window.updateTopProfileBar();"""

if old_verify_success in text:
    text = text.replace(old_verify_success, new_verify_success)
elif old_verify_success.replace("\n", "\r\n") in text:
    text = text.replace(old_verify_success.replace("\n", "\r\n"), new_verify_success.replace("\n", "\r\n"))

# 4. Update handleResendOtp to restart 120s timer and give in-app feedback without browser alert()
old_resend_fn = """window.handleResendOtp = async function() {
    const emailInput = document.getElementById("authEmailInput");
    const errBox = document.getElementById("authErrorMessage");
    const errText = document.getElementById("authErrorText");
    const email = (emailInput?.value || "").trim().toLowerCase();

    if (!email) return;

    try {
        const resp = await fetch("/api/auth/send-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await resp.json();
        if (!resp.ok || data.status === "error") throw new Error(data.detail || data.message);

        alert(`New 6-digit verification code sent to ${email}.`);
    } catch (err) {
        if (errBox && errText) {
            errText.textContent = err.message || "Failed to resend code.";
            errBox.classList.remove("hidden");
        }
    }
};"""

new_resend_fn = """window.handleResendOtp = async function() {
    const emailInput = document.getElementById("authEmailInput");
    const errBox = document.getElementById("authErrorMessage");
    const errText = document.getElementById("authErrorText");
    const spamText = document.getElementById("authSpamNoticeText");
    const email = (emailInput?.value || "").trim().toLowerCase();

    if (!email) return;

    try {
        const resp = await fetch("/api/auth/send-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await resp.json();
        if (!resp.ok || data.status === "error") throw new Error(data.detail || data.message);

        // Restart 120-second timer
        if (typeof window.startResendOtpTimer === "function") {
            window.startResendOtpTimer(120);
        }

        // Show feedback inside spam notice box
        if (spamText) {
            spamText.innerHTML = `<span class="text-emerald-800 font-bold">&#10003; Fresh 6-digit verification code sent to ${email}!</span> Please check your inbox or spam folder.`;
        }
    } catch (err) {
        if (errBox && errText) {
            errText.textContent = err.message || "Failed to resend code.";
            errBox.classList.remove("hidden");
        }
    }
};"""

if old_resend_fn in text:
    text = text.replace(old_resend_fn, new_resend_fn)
elif old_resend_fn.replace("\n", "\r\n") in text:
    text = text.replace(old_resend_fn.replace("\n", "\r\n"), new_resend_fn.replace("\n", "\r\n"))

# 5. Update cancelOtpVerification and closeProfileModal
old_cancel_fn = """window.cancelOtpVerification = function() {
    const form = document.getElementById("candidateAuthForm");
    const otpStep = document.getElementById("authOtpStep");
    const otpInput = document.getElementById("authOtpInput");
    const errBox = document.getElementById("authErrorMessage");

    if (form) form.classList.remove("hidden");
    if (otpStep) otpStep.classList.add("hidden");
    if (otpInput) otpInput.value = "";
    if (errBox) errBox.classList.add("hidden");
    const devBanner = document.getElementById("authDevOtpBanner");
    if (devBanner) devBanner.classList.add("hidden");
};"""

new_cancel_fn = """window.cancelOtpVerification = function() {
    if (window._resendOtpInterval) {
        clearInterval(window._resendOtpInterval);
        window._resendOtpInterval = null;
    }
    const form = document.getElementById("candidateAuthForm");
    const otpStep = document.getElementById("authOtpStep");
    const otpInput = document.getElementById("authOtpInput");
    const errBox = document.getElementById("authErrorMessage");

    if (form) form.classList.remove("hidden");
    if (otpStep) otpStep.classList.add("hidden");
    if (otpInput) otpInput.value = "";
    if (errBox) errBox.classList.add("hidden");
    const devBanner = document.getElementById("authDevOtpBanner");
    if (devBanner) devBanner.classList.add("hidden");
};"""

if old_cancel_fn in text:
    text = text.replace(old_cancel_fn, new_cancel_fn)
elif old_cancel_fn.replace("\n", "\r\n") in text:
    text = text.replace(old_cancel_fn.replace("\n", "\r\n"), new_cancel_fn.replace("\n", "\r\n"))

# Ensure closeProfileModal also resets welcome view
old_close_modal = """window.closeProfileModal = function() {
    const modal = document.getElementById("profileModal");
    if (modal) modal.classList.add("hidden");
    const errBox = document.getElementById("authErrorMessage");
    if (errBox) errBox.classList.add("hidden");
};"""

new_close_modal = """window.closeProfileModal = function() {
    const modal = document.getElementById("profileModal");
    if (modal) modal.classList.add("hidden");
    const errBox = document.getElementById("authErrorMessage");
    if (errBox) errBox.classList.add("hidden");
    const welcomeView = document.getElementById("authWelcomeView");
    if (welcomeView) welcomeView.classList.add("hidden");
};"""

if old_close_modal in text:
    text = text.replace(old_close_modal, new_close_modal)
elif old_close_modal.replace("\n", "\r\n") in text:
    text = text.replace(old_close_modal.replace("\n", "\r\n"), new_close_modal.replace("\n", "\r\n"))

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated app.js successfully!")
