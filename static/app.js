// Almond AI Global Platform Controller (Restored & Synchronized)



let currentProfile = null;



let currentJobs = [];



let currentAtsJobs = [];



let currentLinkedinJobs = [];



let currentFounderJobs = [];



let currentCurrency = "INR";



let currentMinPackage = 15;



let selectedLocations = [];



// Full-Screen Reel / Slide Presentation Controller



let currentSlide = 0;



let isSlideTransitioning = false;



const TOTAL_SLIDES = 3;



window.goToSlide = function(slideIdx) {



    if (slideIdx < 0 || slideIdx >= TOTAL_SLIDES) return;



    currentSlide = slideIdx;



    isSlideTransitioning = true;



    const track = document.getElementById("story-track");



    if (track) {



        track.style.transform = `translateY(-${currentSlide * 100}vh)`;



    }



    // Update story dots



    for (let i = 0; i < TOTAL_SLIDES; i++) {



        const dot = document.getElementById(`dot-${i}`);



        if (dot) {



            if (i === currentSlide) {



                dot.className = "story-dot w-3.5 h-3.5 rounded-full bg-violet-600 ring-4 ring-violet-500/30 transition-all cursor-pointer shadow-md";



            } else {



                dot.className = "story-dot w-2.5 h-2.5 rounded-full bg-slate-300 hover:bg-violet-400 transition-all cursor-pointer";



            }



        }



    }



    // Update navbar slide buttons



    document.querySelectorAll(".nav-slide-btn").forEach((btn, idx) => {



        if (idx === currentSlide) {



            btn.className = "nav-slide-btn px-3.5 py-1.5 rounded-full bg-slate-950 text-white transition cursor-pointer";



        } else {



            btn.className = "nav-slide-btn px-3.5 py-1.5 rounded-full hover:text-slate-950 hover:bg-slate-100 transition cursor-pointer";



        }



    });



    setTimeout(() => {



        isSlideTransitioning = false;



    }, 780);



};



function initStoryPaging() {



    let lastWheelTime = 0;



    // Wheel event handler (Reel / Slide Step)



    window.addEventListener("wheel", (e) => {



        // If any modal is open, let user scroll the modal



        if (!document.getElementById("humanVerifyModal")?.classList.contains("hidden") ||



            !document.getElementById("pitchModal")?.classList.contains("hidden") ||



            !document.getElementById("coverLetterModal")?.classList.contains("hidden")) {



            return;



        }



        const now = Date.now();



        if (now - lastWheelTime < 750 || isSlideTransitioning) {



            return;



        }



        // On Page 3 (Live Vault): check if scroll is inside results container



        if (currentSlide === 2) {



            const resultsScroll = document.getElementById("resultsScrollContainer");



            if (resultsScroll && resultsScroll.contains(e.target)) {



                // If scrolling down and not yet at bottom of results, let results scroll



                if (e.deltaY > 0) {



                    const atBottom = resultsScroll.scrollHeight - resultsScroll.scrollTop <= resultsScroll.clientHeight + 15;



                    if (!atBottom) return;



                }



                // If scrolling up and not yet at top of results, let results scroll



                if (e.deltaY < 0) {



                    const atTop = resultsScroll.scrollTop <= 10;



                    if (!atTop) return;



                }



            }



        }



        // On Page 2 (Workspace): check if inside location dropdown



        const locDropdown = document.getElementById("locationDropdown");



        if (locDropdown && !locDropdown.classList.contains("hidden") && locDropdown.contains(e.target)) {



            return;



        }



        if (e.deltaY > 30) {



            e.preventDefault();



            // Scroll Down -> Next Reel/Slide



            if (currentSlide < TOTAL_SLIDES - 1) {



                lastWheelTime = now;



                window.goToSlide(currentSlide + 1);



            }



        } else if (e.deltaY < -30) {



            e.preventDefault();



            // Scroll Up -> Previous Reel/Slide



            if (currentSlide > 0) {



                lastWheelTime = now;



                window.goToSlide(currentSlide - 1);



            }



        }



    }, { passive: false });



    // Keyboard navigation (Arrow keys & Page up/down)



    window.addEventListener("keydown", (e) => {



        if (["input", "textarea", "select"].includes(document.activeElement?.tagName?.toLowerCase())) {



            return;



        }



        if (e.code === "ArrowDown" || e.code === "PageDown") {



            if (currentSlide < TOTAL_SLIDES - 1) {



                e.preventDefault();



                window.goToSlide(currentSlide + 1);



            }



        } else if (e.code === "ArrowUp" || e.code === "PageUp") {



            if (currentSlide > 0) {



                e.preventDefault();



                window.goToSlide(currentSlide - 1);



            }



        }



    });



    // Touch / Swipe gestures for mobile & trackpads



    let touchStartY = 0;



    window.addEventListener("touchstart", (e) => {



        touchStartY = e.touches[0].clientY;



    }, { passive: true });



        window.addEventListener("touchend", (e) => {
        if (isSlideTransitioning) return;
        const target = e.target;
        if (target && target.closest("#profileModal, #vipPricingModal, #pitchModal, #humanVerifyModal")) {
            return;
        }

        const touchEndY = e.changedTouches[0].clientY;
        const diff = touchStartY - touchEndY;

        // If on Page 3 (Slide 2), prevent accidental slide switching while scrolling job results
        if (currentSlide === 2) {
            const resultsScroll = document.getElementById("resultsScrollContainer");
            if (resultsScroll && resultsScroll.contains(target)) {
                if (diff > 0) return; // scrolling down through jobs
                if (diff < 0) {
                    if (resultsScroll.scrollTop > 5 || Math.abs(diff) < 90) {
                        return; // user is browsing, do not flip slide
                    }
                }
            }
        }

        if (Math.abs(diff) > 55) {
            if (diff > 0 && currentSlide < TOTAL_SLIDES - 1) {
                window.goToSlide(currentSlide + 1);
            } else if (diff < 0 && currentSlide > 0) {
                window.goToSlide(currentSlide - 1);
            }
        }
    }, { passive: true });



}



// Comprehensive Worldwide Locations Database (A to Z)



const WORLDWIDE_LOCATIONS_DB = [



    // A



    { name: "Abu Dhabi", region: "United Arab Emirates", type: "City" },



    { name: "Adelaide", region: "Australia", type: "City" },



    { name: "All India", region: "India (All Districts & States)", type: "Country-Wide" },



    { name: "Amsterdam", region: "Netherlands", type: "City" },



    { name: "Athens", region: "Greece", type: "City" },



    { name: "Atlanta", region: "Georgia, United States", type: "City" },



    { name: "Auckland", region: "New Zealand", type: "City" },



    { name: "Austin", region: "Texas, United States", type: "City" },



    { name: "Australia", region: "Oceania", type: "Country" },



    // B



    { name: "Bangkok", region: "Thailand", type: "City" },



    { name: "Barcelona", region: "Spain", type: "City" },



    { name: "Beijing", region: "China", type: "City" },



    { name: "Bengaluru", region: "Karnataka, India", type: "City" },



    { name: "Berlin", region: "Germany", type: "City" },



    { name: "Bogota", region: "Colombia", type: "City" },



    { name: "Boston", region: "Massachusetts, United States", type: "City" },



    { name: "Brazil", region: "South America", type: "Country" },



    { name: "Brisbane", region: "Australia", type: "City" },



    { name: "Brussels", region: "Belgium", type: "City" },



    { name: "Budapest", region: "Hungary", type: "City" },



    // C



    { name: "Cairo", region: "Egypt", type: "City" },



    { name: "Calgary", region: "Alberta, Canada", type: "City" },



    { name: "California", region: "United States", type: "State" },



    { name: "Canada", region: "North America", type: "Country" },



    { name: "Cape Town", region: "South Africa", type: "City" },



    { name: "Chennai", region: "Tamil Nadu, India", type: "City" },



    { name: "Chicago", region: "Illinois, United States", type: "City" },



    { name: "Coimbatore", region: "Tamil Nadu, India", type: "City" },



    { name: "Copenhagen", region: "Denmark", type: "City" },



    // D



    { name: "Dallas", region: "Texas, United States", type: "City" },



    { name: "Delhi NCR", region: "Delhi / Noida / Gurgaon, India", type: "Region" },



    { name: "Denver", region: "Colorado, United States", type: "City" },



    { name: "Detroit", region: "Michigan, United States", type: "City" },



    { name: "Doha", region: "Qatar", type: "City" },



    { name: "Dresden", region: "Germany", type: "City" },



    { name: "Dubai", region: "United Arab Emirates", type: "City" },



    { name: "Dublin", region: "Ireland", type: "City" },



    // E



    { name: "Edinburgh", region: "Scotland, United Kingdom", type: "City" },



    { name: "Edmonton", region: "Alberta, Canada", type: "City" },



    { name: "Eindhoven", region: "Netherlands", type: "City" },



    { name: "Ernakulam", region: "Kerala, India", type: "District" },



    { name: "Europe", region: "European Union / EEA", type: "Continent" },



    // F



    { name: "Florence", region: "Italy", type: "City" },



    { name: "Frankfurt", region: "Germany", type: "City" },



    { name: "France", region: "Europe", type: "Country" },



    { name: "Fukuoka", region: "Japan", type: "City" },



    // G



    { name: "Geneva", region: "Switzerland", type: "City" },



    { name: "Germany", region: "Europe", type: "Country" },



    { name: "Glasgow", region: "Scotland, United Kingdom", type: "City" },



    { name: "Gothenburg", region: "Sweden", type: "City" },



    { name: "Guadalajara", region: "Mexico", type: "City" },



    { name: "Gurgaon", region: "Haryana, India", type: "City" },



    // H



    { name: "Hamburg", region: "Germany", type: "City" },



    { name: "Helsinki", region: "Finland", type: "City" },



    { name: "Ho Chi Minh City", region: "Vietnam", type: "City" },



    { name: "Hong Kong", region: "Asia", type: "Territory" },



    { name: "Houston", region: "Texas, United States", type: "City" },



    { name: "Hyderabad", region: "Telangana, India", type: "City" },



    // I



    { name: "India", region: "Asia", type: "Country" },



    { name: "Indianapolis", region: "Indiana, United States", type: "City" },



    { name: "Indore", region: "Madhya Pradesh, India", type: "City" },



    { name: "Ireland", region: "Europe", type: "Country" },



    { name: "Istanbul", region: "Turkey", type: "City" },



    // J



    { name: "Jaipur", region: "Rajasthan, India", type: "City" },



    { name: "Jakarta", region: "Indonesia", type: "City" },



    { name: "Japan", region: "Asia", type: "Country" },



    { name: "Johannesburg", region: "South Africa", type: "City" },



    // K



    { name: "Karlsruhe", region: "Germany", type: "City" },



    { name: "Karnataka", region: "India", type: "State" },



    { name: "Kerala", region: "India (All Districts)", type: "State" },



    { name: "Kochi", region: "Kerala, India", type: "City" },



    { name: "Kolkata", region: "West Bengal, India", type: "City" },



    { name: "Kozhikode", region: "Kerala, India", type: "City" },



    { name: "Krakow", region: "Poland", type: "City" },



    { name: "Kuala Lumpur", region: "Malaysia", type: "City" },



    { name: "Kyiv", region: "Ukraine", type: "City" },



    // L



    { name: "Lausanne", region: "Switzerland", type: "City" },



    { name: "Leeds", region: "United Kingdom", type: "City" },



    { name: "Lima", region: "Peru", type: "City" },



    { name: "Lisbon", region: "Portugal", type: "City" },



    { name: "London", region: "United Kingdom", type: "City" },



    { name: "Los Angeles", region: "California, United States", type: "City" },



    { name: "Lyon", region: "France", type: "City" },



    // M



    { name: "Madrid", region: "Spain", type: "City" },



    { name: "Madurai", region: "Tamil Nadu, India", type: "City" },



    { name: "Manchester", region: "United Kingdom", type: "City" },



    { name: "Mangalore", region: "Karnataka, India", type: "City" },



    { name: "Manila", region: "Philippines", type: "City" },



    { name: "Melbourne", region: "Australia", type: "City" },



    { name: "Mexico City", region: "Mexico", type: "City" },



    { name: "Miami", region: "Florida, United States", type: "City" },



    { name: "Milan", region: "Italy", type: "City" },



    { name: "Minneapolis", region: "Minnesota, United States", type: "City" },



    { name: "Montreal", region: "Quebec, Canada", type: "City" },



    { name: "Mumbai", region: "Maharashtra, India", type: "City" },



    { name: "Munich", region: "Germany", type: "City" },



    { name: "Mysore", region: "Karnataka, India", type: "City" },



    // N



    { name: "Nairobi", region: "Kenya", type: "City" },



    { name: "Netherlands", region: "Europe", type: "Country" },



    { name: "New York", region: "New York, United States", type: "City" },



    { name: "Noida", region: "Uttar Pradesh, India", type: "City" },



    { name: "Nuremberg", region: "Germany", type: "City" },



    // O



    { name: "Orlando", region: "Florida, United States", type: "City" },



    { name: "Oslo", region: "Norway", type: "City" },



    { name: "Ottawa", region: "Ontario, Canada", type: "City" },



    // P



    { name: "Paris", region: "France", type: "City" },



    { name: "Philadelphia", region: "Pennsylvania, United States", type: "City" },



    { name: "Phoenix", region: "Arizona, United States", type: "City" },



    { name: "Poland", region: "Europe", type: "Country" },



    { name: "Portland", region: "Oregon, United States", type: "City" },



    { name: "Porto", region: "Portugal", type: "City" },



    { name: "Prague", region: "Czech Republic", type: "City" },



    { name: "Pune", region: "Maharashtra, India", type: "City" },



    // R



    { name: "Raleigh", region: "North Carolina, United States", type: "City" },



    { name: "Reykjavik", region: "Iceland", type: "City" },



    { name: "Riyadh", region: "Saudi Arabia", type: "City" },



    { name: "Rome", region: "Italy", type: "City" },



    { name: "Rotterdam", region: "Netherlands", type: "City" },



    // S



    { name: "Salem", region: "Tamil Nadu, India", type: "City" },



    { name: "Salt Lake City", region: "Utah, United States", type: "City" },



    { name: "San Diego", region: "California, United States", type: "City" },



    { name: "San Francisco", region: "California, United States", type: "City" },



    { name: "São Paulo", region: "Brazil", type: "City" },



    { name: "Seattle", region: "Washington, United States", type: "City" },



    { name: "Seoul", region: "South Korea", type: "City" },



    { name: "Singapore", region: "Southeast Asia", type: "Country" },



    { name: "Spain", region: "Europe", type: "Country" },



    { name: "Stockholm", region: "Sweden", type: "City" },



    { name: "Stuttgart", region: "Germany", type: "City" },



    { name: "Sydney", region: "Australia", type: "City" },



    // T



    { name: "Taipei", region: "Taiwan", type: "City" },



    { name: "Tallinn", region: "Estonia", type: "City" },



    { name: "Tamil Nadu", region: "India (All Districts)", type: "State" },



    { name: "Tampa", region: "Florida, United States", type: "City" },



    { name: "Tel Aviv", region: "Israel", type: "City" },



    { name: "Thiruvananthapuram", region: "Kerala, India", type: "City" },



    { name: "Tokyo", region: "Japan", type: "City" },



    { name: "Toronto", region: "Ontario, Canada", type: "City" },



    // U



    { name: "United Kingdom", region: "Europe", type: "Country" },



    { name: "United States", region: "North America", type: "Country" },



    { name: "Utrecht", region: "Netherlands", type: "City" },



    // V



    { name: "Valencia", region: "Spain", type: "City" },



    { name: "Vancouver", region: "British Columbia, Canada", type: "City" },



    { name: "Vienna", region: "Austria", type: "City" },



    { name: "Vilnius", region: "Lithuania", type: "City" },



    // W



    { name: "Warsaw", region: "Poland", type: "City" },



    { name: "Washington D.C.", region: "District of Columbia, United States", type: "City" },



    { name: "Wellington", region: "New Zealand", type: "City" },



    { name: "Worldwide Remote", region: "Global (Anywhere)", type: "Remote" },



    // Z



    { name: "Zagreb", region: "Croatia", type: "City" },



    { name: "Zurich", region: "Switzerland", type: "City" }



];



document.addEventListener("DOMContentLoaded", () => {



    initResumeUpload();



    initAddSkillControls();



    initCompensationControls();



    initLocationAutocomplete();



    initJobSearch();



    initLinkedinToggle();



    initResultsTabs();



    initModal();



    initCoverLetterModal();



    initHeroInfoModal();



    initKanbanTracker();



    initExports();



    initLivePostingsCounter();



    initHumanVerifier();



    initStoryPaging();



});



// 1. Resume Drag & Drop and Dynamic Upload



function initResumeUpload() {



    const dropZone = document.getElementById("dropZone");



    const fileInput = document.getElementById("resumeFileInput");



    const uploadPlaceholder = document.getElementById("uploadPlaceholder");



    const uploadLoading = document.getElementById("uploadLoading");



    const uploadedInfo = document.getElementById("uploadedInfo");



    const fileNameDisplay = document.getElementById("fileNameDisplay");



    const reuploadBtn = document.getElementById("reuploadBtn");



    if (!dropZone || !fileInput) return;



    dropZone.addEventListener("click", (e) => {



        if (e.target !== reuploadBtn && !reuploadBtn.contains(e.target)) {



            fileInput.click();



        }



    });



    reuploadBtn.addEventListener("click", (e) => {



        e.stopPropagation();



        fileInput.value = "";



        fileInput.click();



    });



    fileInput.addEventListener("change", (e) => {



        if (e.target.files && e.target.files[0]) {



            handleFileUpload(e.target.files[0]);



        }



    });



    ["dragenter", "dragover"].forEach(eventName => {



        dropZone.addEventListener(eventName, (e) => {



            e.preventDefault();



            dropZone.classList.add("border-violet-500", "bg-violet-100/60");



        });



    });



    ["dragleave", "drop"].forEach(eventName => {



        dropZone.addEventListener(eventName, (e) => {



            e.preventDefault();



            dropZone.classList.remove("border-violet-500", "bg-violet-100/60");



        });



    });



    dropZone.addEventListener("drop", (e) => {



        if (e.dataTransfer.files && e.dataTransfer.files[0]) {



            handleFileUpload(e.dataTransfer.files[0]);



        }



    });



    async function handleFileUpload(file) {



        uploadPlaceholder.classList.add("hidden");



        uploadedInfo.classList.add("hidden");



        uploadLoading.classList.remove("hidden");



        const formData = new FormData();



        formData.append("file", file);



        try {



            const resp = await fetch("/api/upload-resume", {



                method: "POST",



                body: formData



            });



            if (!resp.ok) {



                const errData = await resp.json().catch(() => ({}));



                throw new Error(errData.detail || "Failed to parse resume.");



            }



            const data = await resp.json();



            currentProfile = data.profile;



            fileNameDisplay.textContent = file.name;



            uploadLoading.classList.add("hidden");



            uploadedInfo.classList.remove("hidden");



            displayParsedProfile(currentProfile);



        } catch (err) {



            uploadLoading.classList.add("hidden");



            uploadPlaceholder.classList.remove("hidden");



            alert("Upload failed: " + err.message);



        }



    }



}



function displayParsedProfile(profile) {



    const parsedSection = document.getElementById("parsedProfileSection");



    const nameEl = document.getElementById("profileName");



    const yoeEl = document.getElementById("profileYoe");



    const roleEl = document.getElementById("profileRole");



    const skillsCloud = document.getElementById("profileSkillsBadges");



    const skillsCountBadge = document.getElementById("skillsCountBadge");



    if (!parsedSection) return;



    nameEl.textContent = profile.name || "Identified Candidate";



    yoeEl.textContent = `${profile.years_experience || 3}+ Years Verified`;



    roleEl.textContent = profile.current_role || "Software Engineer";



    const skills = profile.skills || [];



    if (skillsCountBadge) {



        skillsCountBadge.textContent = `${skills.length} active`;



    }



    skillsCloud.innerHTML = "";



    if (skills.length === 0) {



        skillsCloud.innerHTML = `<span class="text-xs text-emerald-300/60 italic font-medium">No skills extracted yet. Add missing skills below.</span>`;



    } else {



        skills.forEach((skill, sIdx) => {



            const badge = document.createElement("span");



            badge.className = "inline-flex items-center space-x-1.5 px-2.5 py-1 bg-white text-slate-900 text-xs font-black rounded-lg border border-slate-300 shadow-sm capitalize transition group hover:border-emerald-400";



            badge.innerHTML = `



                <span>${skill}</span>



                <button type="button" class="remove-skill-btn text-slate-400 hover:text-red-600 font-bold ml-1 transition cursor-pointer" data-skill-idx="${sIdx}" title="Remove skill">✕</button>



            `;



            skillsCloud.appendChild(badge);



        });



    }



    // Attach click listeners to remove individual skills



    skillsCloud.querySelectorAll(".remove-skill-btn").forEach(btn => {



        btn.addEventListener("click", (e) => {



            e.stopPropagation();



            const idx = parseInt(btn.getAttribute("data-skill-idx"));



            if (currentProfile && currentProfile.skills && currentProfile.skills[idx] !== undefined) {



                currentProfile.skills.splice(idx, 1);



                displayParsedProfile(currentProfile);



            }



        });



    });



    parsedSection.classList.remove("hidden");



    if (window.lucide) lucide.createIcons();



}



function initAddSkillControls() {



    const addBtn = document.getElementById("addSkillBtn");



    const addInput = document.getElementById("addSkillInput");



    if (!addBtn || !addInput) return;



    function handleAdd() {



        const val = addInput.value.trim();



        if (!val) return;



        if (!currentProfile) {



            currentProfile = {



                name: "Identified Candidate",



                years_experience: 3,



                current_role: "Software Engineer",



                skills: []



            };



        }



        if (!currentProfile.skills) currentProfile.skills = [];



        // Check if skill already exists (case-insensitive)



        const exists = currentProfile.skills.some(s => s.toLowerCase() === val.toLowerCase());



        if (!exists) {



            currentProfile.skills.push(val);



        }



        addInput.value = "";



        displayParsedProfile(currentProfile);



    }



    addBtn.addEventListener("click", handleAdd);



    addInput.addEventListener("keydown", (e) => {



        if (e.key === "Enter") {



            e.preventDefault();



            handleAdd();



        }



    });



}



// Educational Value Proposition Modal (No Brokers, No Middlemen, No Dead Posts, 100% Direct ATS)

// High-Contrast Light Theme Educational Value Modal (No Brokers, No Middlemen, No Dead Posts, 100% Direct ATS)
const HERO_MODAL_DATA = {
    brokers: {
        badge: "✕ NO BROKERS",
        icon: "user-x",
        iconClass: "text-rose-700",
        iconBg: "bg-rose-100 border border-rose-300 text-rose-700 shadow-xs",
        activeTabClass: "bg-rose-600 text-white font-black shadow-md border-rose-600 ring-2 ring-rose-300",
        title: "What are Job Brokers & Why Avoid Them?",
        subtitle: "Third-Party Headhunters • Contingency Recruitment Agencies",
        sections: [
            {
                heading: "What Brokers Usually Do",
                headingColor: "text-rose-950 font-black",
                dotColor: "bg-rose-600",
                cardBorder: "border-2 border-rose-200/90",
                accentBorder: "border-l-rose-500",
                cardBg: "bg-white",
                desc: "Third-party recruitment brokers and contingency headhunters scrape open job posts or intercept hiring pipelines. They do not work inside the employer company. Instead, they hoard candidate resumes and pitch them to companies with a heavy sales commission contract."
            },
            {
                heading: "The 20% to 35% Salary Siphon",
                headingColor: "text-rose-950 font-black",
                dotColor: "bg-rose-600",
                cardBorder: "border-2 border-rose-200/90",
                accentBorder: "border-l-rose-600",
                cardBg: "bg-rose-50/50",
                desc: "When a broker gets you hired, the employer pays them a mandatory agency fee equal to <span class=\"bg-rose-100 text-rose-950 font-black px-1.5 py-0.5 rounded border border-rose-200\">20% to 35% of your negotiated first-year CTC</span>. If your offer is ₹20 LPA ($120k), the company shells out ₹4L–₹7L+ ($25k–$40k) directly to the broker. Employers deduct this fee from your total compensation pool—resulting in lower base pay, slashed sign-on bonuses, and diminished equity."
            },
            {
                heading: "Candidate Troubles & Commission-Biased Matching",
                headingColor: "text-amber-950 font-black",
                dotColor: "bg-amber-600",
                cardBorder: "border-2 border-amber-200/90",
                accentBorder: "border-l-amber-500",
                cardBg: "bg-white",
                desc: "Because brokers are paid solely on commission bounties, they frequently push candidates toward companies offering the biggest payout rather than the role best suited for their skills, tech stack, and career growth. Furthermore, uncoordinated duplicate resume submissions by brokers frequently cause candidates to be disqualified by corporate HR systems."
            },
            {
                heading: "The Almond Direct Feed Solution",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border-2 border-emerald-300",
                accentBorder: "border-l-emerald-600",
                cardBg: "bg-emerald-50/70",
                desc: "<span class=\"bg-emerald-100 text-emerald-950 font-black px-1.5 py-0.5 rounded border border-emerald-200\">0% Recruiter Spread.</span> Almond routes you directly to verified corporate portal feeds. Employers incur zero agency commission fees, giving you full negotiation leverage to claim maximum base pay and bonuses."
            }
        ]
    },
    middlemen: {
        badge: "✕ NO MIDDLEMEN",
        icon: "git-fork",
        iconClass: "text-amber-700",
        iconBg: "bg-amber-100 border border-amber-300 text-amber-800 shadow-xs",
        activeTabClass: "bg-amber-600 text-white font-black shadow-md border-amber-600 ring-2 ring-amber-300",
        title: "What are Staffing Middlemen & Body Shops?",
        subtitle: "Multi-Tier Sub-Contractors • Margin-Slicing Staffing Body Shops",
        sections: [
            {
                heading: "What Middlemen Actually Do",
                headingColor: "text-amber-950 font-black",
                dotColor: "bg-amber-600",
                cardBorder: "border-2 border-amber-200/90",
                accentBorder: "border-l-amber-500",
                cardBg: "bg-white",
                desc: "Middlemen create an artificial chain of subcontracting between you and the actual engineering team. A client hires a prime vendor, who subcontracts to a tier-2 vendor, who delegates to an agency recruiter who finally contacts you."
            },
            {
                heading: "Predatory Margin Shaving",
                headingColor: "text-amber-950 font-black",
                dotColor: "bg-amber-600",
                cardBorder: "border-2 border-amber-200/90",
                accentBorder: "border-l-amber-600",
                cardBg: "bg-amber-50/50",
                desc: "Every tier of middlemen slices off a thick slice of your compensation. If the client company bills $90/hr (or ₹25 LPA) for an engineer, multi-tier body shops often hand the candidate only $35/hr (or ₹10 LPA)—<span class=\"bg-amber-100 text-amber-950 font-black px-1.5 py-0.5 rounded border border-amber-200\">pocketing over 50% of the candidate's true market value</span> month after month."
            },
            {
                heading: "Candidate Troubles: Resume Manipulation & Delays",
                headingColor: "text-amber-950 font-black",
                dotColor: "bg-amber-600",
                cardBorder: "border-2 border-amber-200/90",
                accentBorder: "border-l-amber-500",
                cardBg: "bg-white",
                desc: "Middlemen frequently tamper with or exaggerate your resume to clear vendor scorecard hurdles without your approval, leading to disastrous, misaligned technical interviews. Communication, interview feedback, and contract terms are chronically delayed through games of corporate telephone."
            },
            {
                heading: "The Almond Direct Feed Solution",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border-2 border-emerald-300",
                accentBorder: "border-l-emerald-600",
                cardBg: "bg-emerald-50/70",
                desc: "<span class=\"bg-emerald-100 text-emerald-950 font-black px-1.5 py-0.5 rounded border border-emerald-200\">Direct Internal Connection.</span> Almond eliminates every intermediary vendor layer. You interface directly with internal engineering leadership and corporate HR talent acquisition teams."
            }
        ]
    },
    deadposts: {
        badge: "✕ NO DEAD POSTS",
        icon: "file-x",
        iconClass: "text-red-700",
        iconBg: "bg-red-100 border border-red-300 text-red-700 shadow-xs",
        activeTabClass: "bg-red-600 text-white font-black shadow-md border-red-600 ring-2 ring-red-300",
        title: "What are Dead Posts & Ghost Jobs?",
        subtitle: "Expired Requisitions • Resume-Harvesting Phantom Listings",
        sections: [
            {
                heading: "What Dead Posts Mean",
                headingColor: "text-red-950 font-black",
                dotColor: "bg-red-600",
                cardBorder: "border-2 border-red-200/90",
                accentBorder: "border-l-red-500",
                cardBg: "bg-white",
                desc: "Dead posts and 'ghost jobs' are listings left active on legacy job boards (LinkedIn, Indeed, third-party aggregators) long after the position was filled, cancelled, or placed on indefinite hiring freeze. Many legacy platforms refuse to take them down because high post counts boost their SEO traffic."
            },
            {
                heading: "40+ Hours of Wasted Candidate Time",
                headingColor: "text-red-950 font-black",
                dotColor: "bg-red-600",
                cardBorder: "border-2 border-red-200/90",
                accentBorder: "border-l-red-600",
                cardBg: "bg-red-50/50",
                desc: "Candidates spend <span class=\"bg-red-100 text-red-950 font-black px-1.5 py-0.5 rounded border border-red-200\">40+ hours</span> customizing resumes, writing STAR-format cover letters, and completing take-home assignments for positions that have no active headcount. This creates massive candidate fatigue and demotivation."
            },
            {
                heading: "Data Harvesting & Telemarketing Spam",
                headingColor: "text-amber-950 font-black",
                dotColor: "bg-amber-600",
                cardBorder: "border-2 border-amber-200/90",
                accentBorder: "border-l-amber-500",
                cardBg: "bg-white",
                desc: "Many phantom listings exist exclusively to harvest active candidate phone numbers and email addresses to sell to marketing lists, predatory coding bootcamps, and resume-writing services without candidate consent."
            },
            {
                heading: "The Almond Direct Feed Solution",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border-2 border-emerald-300",
                accentBorder: "border-l-emerald-600",
                cardBg: "bg-emerald-50/70",
                desc: "<span class=\"bg-emerald-100 text-emerald-950 font-black px-1.5 py-0.5 rounded border border-emerald-200\">Live Feed Synchronization.</span> Almond monitors live API & webhook events on Ashby, Greenhouse, Lever, and Workday. As soon as a requisition is filled or closed, it vanishes from Almond. You only apply to actively hiring roles."
            }
        ]
    },
    ats: {
        badge: "✓ WHO WE ARE",
        icon: "shield-check",
        iconClass: "text-emerald-700",
        iconBg: "bg-emerald-100 border border-emerald-300 text-emerald-800 shadow-xs",
        activeTabClass: "bg-emerald-600 text-white font-black shadow-md border-emerald-600 ring-2 ring-emerald-300",
        title: "Who We Are",
        subtitle: "Direct Corporate Feeds • Our Philosophy & Mission",
        sections: [
            {
                heading: "Our Direct Feed Philosophy",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border-2 border-emerald-200/90",
                accentBorder: "border-l-emerald-500",
                cardBg: "bg-white",
                desc: "Almond Jobs is a candidate-first career intelligence platform designed to bypass recruitment agencies, body shops, and ghost jobs. We connect talented professionals straight to verified corporate pipelines."
            },
            {
                heading: "Direct Review by Engineering Teams",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border-2 border-emerald-200/90",
                accentBorder: "border-l-emerald-500",
                cardBg: "bg-white",
                desc: "When you submit directly through verified corporate portals, your resume lands straight into the internal dashboard of the engineering hiring manager and company talent team. It bypasses external spam filters and untrusted aggregators entirely."
            },
            {
                heading: "Maximum Compensation Negotiation Power",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border-2 border-emerald-300",
                accentBorder: "border-l-emerald-600",
                cardBg: "bg-emerald-50/70",
                desc: "Because you apply directly through private company pipelines, the hiring company saves <span class=\"bg-emerald-100 text-emerald-950 font-black px-1.5 py-0.5 rounded border border-emerald-200\">$10,000–$30,000 in agency headhunter fees</span>. This unencumbered budget gives you stronger leverage during final salary negotiations."
            },
            {
                heading: "Almond's Verified Feed Network",
                headingColor: "text-violet-950 font-black",
                dotColor: "bg-violet-600",
                cardBorder: "border-2 border-violet-200",
                accentBorder: "border-l-violet-600",
                cardBg: "bg-violet-50/50",
                desc: "Almond indexes 3,315,000+ live verified corporate postings worldwide, enabling engineers to discover fresh roles within minutes of opening and apply directly with 0% recruiter markup."
            }
        ]
    }
};

function switchHeroModalTab(tabKey) {
    const key = HERO_MODAL_DATA[tabKey] ? tabKey : 'ats';
    const data = HERO_MODAL_DATA[key];
    const modal = document.getElementById('heroInfoModal');
    if (!modal) return;

    // Update tab button styles
    const tabKeys = ['brokers', 'middlemen', 'deadposts', 'ats'];
    tabKeys.forEach(t => {
        const btn = document.getElementById('tab' + t.charAt(0).toUpperCase() + t.slice(1));
        if (btn) {
            btn.className = 'hero-modal-tab px-3.5 py-1.5 rounded-xl border transition cursor-pointer flex items-center gap-1 text-xs ';
            if (t === key) {
                btn.className += data.activeTabClass;
            } else {
                btn.className += 'bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold border-slate-300';
            }
        }
    });

    // Update Header Icon, Title & Subtitle
    const iconContainer = document.getElementById('heroModalIcon');
    if (iconContainer) {
        iconContainer.className = 'w-10 h-10 rounded-2xl flex items-center justify-center transition-all ' + data.iconBg;
        iconContainer.innerHTML = '<i data-lucide="' + data.icon + '" class="w-5 h-5 ' + data.iconClass + '"></i>';
    }

    const titleEl = document.getElementById('heroModalTitle');
    if (titleEl) titleEl.textContent = data.title;

    const subtitleEl = document.getElementById('heroModalSubtitle');
    if (subtitleEl) subtitleEl.textContent = data.subtitle;

    // Populate Body Sections with 100% High-Contrast, Crystal-Clear Cards
    const bodyEl = document.getElementById('heroModalBody');
    if (bodyEl) {
        bodyEl.innerHTML = data.sections.map(sec => 
            '<div class="p-4 sm:p-5 rounded-2xl ' + sec.cardBorder + ' ' + sec.cardBg + ' transition-all shadow-xs border-l-4 ' + (sec.accentBorder || '') + '">' +
                '<div class="flex items-center space-x-2 mb-2">' +
                    '<span class="w-2.5 h-2.5 rounded-full ' + sec.dotColor + ' shrink-0"></span>' +
                    '<span class="text-xs sm:text-sm font-black uppercase tracking-wider ' + sec.headingColor + '">' + sec.heading + '</span>' +
                '</div>' +
                '<p class="text-xs sm:text-[13px] text-slate-900 leading-relaxed font-semibold">' + sec.desc + '</p>' +
            '</div>'
        ).join('');
    }

    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

window.openHeroInfoModal = function(tabKey) {
    const modal = document.getElementById('heroInfoModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    switchHeroModalTab(tabKey || 'ats');
};

window.closeHeroInfoModal = function() {
    const modal = document.getElementById('heroInfoModal');
    if (modal) modal.classList.add('hidden');
};

window.switchHeroModalTab = switchHeroModalTab;
window.openAtsModal = function() {
    window.openHeroInfoModal('ats');
};

function initHeroInfoModal() {
    const heroModal = document.getElementById('heroInfoModal');
    if (heroModal) {
        heroModal.addEventListener('click', (e) => {
            if (e.target === heroModal) closeHeroInfoModal();
        });
    }

    const vipModal = document.getElementById('vipPricingModal');
    if (vipModal) {
        vipModal.addEventListener('click', (e) => {
            if (e.target === vipModal) closeVipPricingModal();
        });
    }

    const profileModal = document.getElementById('profileModal');
    if (profileModal) {
        profileModal.addEventListener('click', (e) => {
            if (e.target === profileModal) closeProfileModal();
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeHeroInfoModal();
            closeVipPricingModal();
            closeProfileModal();
        }
    });
}

function initCompensationControls() {



    const numberInput = document.getElementById("packageNumberInput");



    const slider = document.getElementById("packageRangeSlider");



    const symbolEl = document.getElementById("currencySymbol");



    const unitEl = document.getElementById("currencyUnit");



    const tabs = document.querySelectorAll(".currency-tab");



    const presetsContainer = document.getElementById("salaryPresetsContainer");



    if (!numberInput || !slider) return;



    const currencyConfig = {



        INR: {



            symbol: "₹",



            unit: "LPA",



            min: 0,



            max: 200,



            step: 1,



            default: 15,



            presets: [



                { label: "12 LPA", val: 12 },



                { label: "15 LPA", val: 15 },



                { label: "25 LPA", val: 25 },



                { label: "40 LPA", val: 40 },



                { label: "1 Cr (100 LPA)", val: 100 }



            ]



        },



        USD_YR: {



            symbol: "$",



            unit: "/ Year",



            min: 0,



            max: 300000,



            step: 5000,



            default: 75000,



            presets: [



                { label: "$60k/yr", val: 60000 },



                { label: "$90k/yr", val: 90000 },



                { label: "$130k/yr", val: 130000 },



                { label: "$180k/yr", val: 180000 },



                { label: "$250k+/yr", val: 250000 }



            ]



        },



        USD_MO: {



            symbol: "$",



            unit: "/ Month",



            min: 0,



            max: 25000,



            step: 250,



            default: 4000,



            presets: [



                { label: "$3k/mo", val: 3000 },



                { label: "$5k/mo", val: 5000 },



                { label: "$8k/mo", val: 8000 },



                { label: "$12k/mo", val: 12000 },



                { label: "$15k+/mo", val: 15000 }



            ]



        },



        EUR: {



            symbol: "€",



            unit: "/ Year",



            min: 0,



            max: 200000,



            step: 5000,



            default: 65000,



            presets: [



                { label: "€45k/yr", val: 45000 },



                { label: "€65k/yr", val: 65000 },



                { label: "€90k/yr", val: 90000 },



                { label: "€130k+/yr", val: 130000 }



            ]



        },



        GBP: {



            symbol: "£",



            unit: "/ Year",



            min: 0,



            max: 180000,



            step: 5000,



            default: 55000,



            presets: [



                { label: "£40k/yr", val: 40000 },



                { label: "£60k/yr", val: 60000 },



                { label: "£85k/yr", val: 85000 },



                { label: "£120k+/yr", val: 120000 }



            ]



        },



        CAD: {



            symbol: "C$",



            unit: "/ Year",



            min: 0,



            max: 250000,



            step: 5000,



            default: 75000,



            presets: [



                { label: "C$50k", val: 50000 },



                { label: "C$80k", val: 80000 },



                { label: "C$120k", val: 120000 },



                { label: "C$160k+", val: 160000 }



            ]



        },



        AUD: {



            symbol: "A$",



            unit: "/ Year",



            min: 0,



            max: 250000,



            step: 5000,



            default: 85000,



            presets: [



                { label: "A$60k", val: 60000 },



                { label: "A$90k", val: 90000 },



                { label: "A$130k", val: 130000 },



                { label: "A$175k+", val: 175000 }



            ]



        },



        AED: {



            symbol: "AED",



            unit: "/ Month",



            min: 0,



            max: 60000,



            step: 1000,



            default: 15000,



            presets: [



                { label: "10k/mo", val: 10000 },



                { label: "15k/mo", val: 15000 },



                { label: "25k/mo", val: 25000 },



                { label: "40k+/mo", val: 40000 }



            ]



        },



        ANY: {



            symbol: "—",



            unit: "No Minimum",



            min: 0,



            max: 0,



            step: 1,



            default: 0,



            presets: []



        }



    };



    function applyCurrency(curr) {



        currentCurrency = curr;



        const cfg = currencyConfig[curr] || currencyConfig["INR"];



        symbolEl.textContent = cfg.symbol;



        unitEl.textContent = cfg.unit;



        if (curr === "ANY") {



            numberInput.value = 0;



            numberInput.disabled = true;



            slider.disabled = true;



            slider.value = 0;



            currentMinPackage = 0;



            presetsContainer.innerHTML = `<span class="text-xs font-bold text-slate-600 italic">Showing all verified jobs regardless of salary band</span>`;



            return;



        }



        numberInput.disabled = false;



        slider.disabled = false;



        slider.min = cfg.min;



        slider.max = cfg.max;



        slider.step = cfg.step;



        const val = cfg.default;



        numberInput.value = val;



        slider.value = val;



        currentMinPackage = val;



        renderPresets(cfg.presets);



    }



    function renderPresets(presets) {



        presetsContainer.innerHTML = "";



        presets.forEach(p => {



            const btn = document.createElement("button");



            btn.type = "button";



            btn.className = "text-xs px-3 py-1 rounded-xl border-2 border-slate-200 bg-white text-slate-800 hover:border-emerald-500 hover:text-emerald-900 hover:bg-emerald-50 font-black transition shadow-sm";



            btn.textContent = p.label;



            btn.addEventListener("click", () => {



                numberInput.value = p.val;



                slider.value = Math.min(p.val, parseInt(slider.max));



                currentMinPackage = p.val;



            });



            presetsContainer.appendChild(btn);



        });



    }



    // Sync slider to input



    slider.addEventListener("input", (e) => {



        const val = parseFloat(e.target.value);



        numberInput.value = val;



        currentMinPackage = val;



    });



    // Sync input to slider



    numberInput.addEventListener("input", (e) => {



        const val = parseFloat(e.target.value) || 0;



        currentMinPackage = val;



        if (val <= parseFloat(slider.max)) {



            slider.value = val;



        }



    });



    // Currency tab switching



    tabs.forEach(tab => {



        tab.addEventListener("click", () => {



            tabs.forEach(t => {



                t.classList.remove("active", "bg-slate-950", "text-amber-300", "shadow-sm", "border", "border-amber-400/40", "bg-gradient-to-r", "from-violet-600", "to-indigo-600", "text-white", "shadow-violet-500/20");



                t.classList.add("text-slate-700");



            });



            tab.classList.add("active", "bg-gradient-to-r", "from-violet-600", "to-indigo-600", "text-white", "shadow-md", "shadow-violet-500/20");



            tab.classList.remove("text-slate-700");



            const moreSel = document.getElementById("moreCurrenciesSelect");



            if (moreSel) moreSel.value = "";



            const curr = tab.getAttribute("data-curr");



            applyCurrency(curr);



        });



    });



    // More Currencies Dropdown listener



    const moreSelect = document.getElementById("moreCurrenciesSelect");



    if (moreSelect) {



        moreSelect.addEventListener("change", (e) => {



            const selCurr = e.target.value;



            if (selCurr) {



                tabs.forEach(t => {



                    t.classList.remove("active", "bg-slate-950", "text-amber-300", "shadow-sm", "border", "border-amber-400/40", "bg-gradient-to-r", "from-violet-600", "to-indigo-600", "text-white", "shadow-violet-500/20");



                    t.classList.add("text-slate-700");



                });



                applyCurrency(selCurr);



            }



        });



    }



    // Initialize INR presets



    applyCurrency("INR");



}



// 3. A to Z Global Location Autocomplete & Dynamic Tags



function initLocationAutocomplete() {
    const searchInput = document.getElementById("locationSearchInput");
    const dropdown = document.getElementById("locationDropdown");
    const tagsContainer = document.getElementById("selectedLocationsTags");
    const quickPills = document.querySelectorAll(".quick-pill");

    if (!searchInput || !dropdown || !tagsContainer) return;

    function updateQuickPills() {
        if (!quickPills) return;
        quickPills.forEach(pill => {
            const loc = pill.getAttribute("data-loc");
            if (loc && selectedLocations.some(l => l.toLowerCase() === loc.toLowerCase())) {
                pill.className = "quick-pill text-xs px-3 py-1 rounded-full border-2 border-violet-600 bg-violet-100 text-violet-950 font-black shadow-2xs transition cursor-pointer";
            } else {
                pill.className = "quick-pill text-xs px-3 py-1 rounded-full border border-slate-300 bg-white text-slate-800 font-bold hover:border-violet-300 hover:bg-violet-50 hover:text-violet-950 transition cursor-pointer";
            }
        });
    }

    function renderActiveTags() {
        tagsContainer.innerHTML = "";
        if (selectedLocations.length === 0) {
            tagsContainer.innerHTML = `<span class="text-xs font-semibold text-slate-400 italic p-1">No target locations added yet — type a city above or click suggestions below</span>`;
            updateQuickPills();
            return;
        }

        selectedLocations.forEach(loc => {
            const tag = document.createElement("span");
            tag.className = "inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-extrabold bg-violet-100 text-violet-950 border border-violet-300/80 shadow-xs animate-in fade-in";
            tag.innerHTML = `
                <span>${loc}</span>
                <button type="button" class="ml-1 text-violet-700 hover:text-violet-950 focus:outline-none font-black text-sm" data-loc="${loc}">
                    ✕
                </button>
            `;
            tag.querySelector("button").addEventListener("click", (e) => {
                e.stopPropagation();
                removeLocation(loc);
            });
            tagsContainer.appendChild(tag);
        });
        updateQuickPills();
    }

    function addLocation(locName) {
        const clean = locName.trim();
        if (!clean) return;
        if (!selectedLocations.map(l => l.toLowerCase()).includes(clean.toLowerCase())) {
            selectedLocations.push(clean);
            renderActiveTags();
        }
        searchInput.value = "";
        dropdown.classList.add("hidden");
    }

    function removeLocation(locName) {
        selectedLocations = selectedLocations.filter(l => l.toLowerCase() !== locName.toLowerCase());
        renderActiveTags();
    }

    // Typeahead Search & Dropdown Filter
    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        dropdown.innerHTML = "";

        if (!query) {
            dropdown.classList.add("hidden");
            return;
        }

        const matches = (typeof WORLDWIDE_LOCATIONS_DB !== 'undefined' ? WORLDWIDE_LOCATIONS_DB : []).filter(item => 
            item.name.toLowerCase().includes(query) || 
            item.region.toLowerCase().includes(query)
        ).slice(0, 8);

        if (matches.length === 0) {
            dropdown.innerHTML = `
                <div class="p-3.5 text-xs font-black text-slate-900 flex items-center justify-between cursor-pointer hover:bg-violet-50" id="addCustomLocRow">
                    <span>Add custom location: <strong>"${searchInput.value}"</strong></span>
                    <span class="text-xs bg-violet-100 text-violet-950 border border-violet-300 px-2 py-0.5 rounded-md font-black">Press Enter</span>
                </div>
            `;
            document.getElementById("addCustomLocRow")?.addEventListener("click", () => {
                addLocation(searchInput.value);
            });
        } else {
            matches.forEach(item => {
                const row = document.createElement("div");
                row.className = "p-3 text-xs font-bold text-slate-800 hover:bg-violet-50 cursor-pointer flex items-center justify-between transition";
                row.innerHTML = `
                    <div class="flex items-center space-x-2">
                        <i data-lucide="map-pin" class="w-3.5 h-3.5 text-slate-400"></i>
                        <span class="text-slate-900 font-extrabold">${item.name}</span>
                        <span class="text-[11px] text-slate-500 font-normal">(${item.region})</span>
                    </div>
                    <span class="text-[10px] font-mono uppercase bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">${item.type}</span>
                `;
                row.addEventListener("click", () => {
                    addLocation(item.name);
                });
                dropdown.appendChild(row);
            });
            if (window.lucide) lucide.createIcons();
        }

        dropdown.classList.remove("hidden");
    });

    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && searchInput.value.trim()) {
            e.preventDefault();
            addLocation(searchInput.value.trim());
        } else if (e.key === "Escape") {
            dropdown.classList.add("hidden");
        }
    });

    // Close dropdown on outside click
    document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add("hidden");
        }
    });

    // Quick preset pills toggle
    quickPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const loc = pill.getAttribute("data-loc");
            if (!loc) return;
            if (selectedLocations.some(l => l.toLowerCase() === loc.toLowerCase())) {
                removeLocation(loc);
            } else {
                addLocation(loc);
            }
        });
    });

    renderActiveTags();
}

function initJobSearch() {



    const searchBtn = document.getElementById("searchJobsBtn");



    const emptyState = document.getElementById("emptyState");



    const jobsLoading = document.getElementById("jobsLoading");



    const jobListContainer = document.getElementById("jobListContainer");



    const resultsCountBadge = document.getElementById("resultsCountBadge");



    const bottomLinkedinToggleCard = document.getElementById("bottomLinkedinToggleCard");



    const resultsLinkedinToggle = document.getElementById("resultsLinkedinToggle");



    const linkedinSectionContainer = document.getElementById("linkedinSectionContainer");



    const linkedinCardsContainer = document.getElementById("linkedinCardsContainer");



    if (!searchBtn) return;



    async function executeSearch() {



        const workMode = document.querySelector('input[name="work_mode"]:checked')?.value || "all";



        const empType = document.querySelector('input[name="employment_type"]:checked')?.value || "all";



        



        const payload = {



            profile: currentProfile,



            user_id: getCandidateUserId(),



            preferences: {



                currency: currentCurrency,



                min_package: currentMinPackage,



                locations: selectedLocations,



                work_mode: workMode,



                employment_type: empType,



                include_linkedin: false



            }



        };



        if (emptyState) emptyState.classList.add("hidden");



        if (jobListContainer) jobListContainer.innerHTML = "";



        if (jobsLoading) jobsLoading.classList.remove("hidden");



        searchBtn.disabled = true;



        // Super slide transition to Page 3 (Live Results Vault)



        window.goToSlide(2);



        // Reset LinkedIn state



        if (resultsLinkedinToggle) resultsLinkedinToggle.checked = false;



        if (linkedinSectionContainer) linkedinSectionContainer.classList.add("hidden");



        if (linkedinCardsContainer) linkedinCardsContainer.innerHTML = "";



        if (bottomLinkedinToggleCard) bottomLinkedinToggleCard.classList.add("hidden");



        currentLinkedinJobs = [];



        try {



            const resp = await fetch("/api/find-jobs", {



                method: "POST",



                headers: { "Content-Type": "application/json" },



                body: JSON.stringify(payload)



            });



            if (!resp.ok) {



                const err = await resp.json().catch(() => ({}));



                throw new Error(err.detail || "Error querying live openings index.");



            }



            const data = await resp.json();



            currentAtsJobs = data.jobs || [];



            currentJobs = currentAtsJobs;



            currentFounderJobs = data.founder_jobs || [];
            window.currentAtsJobs = currentAtsJobs;
            window.currentFounderJobs = currentFounderJobs;
            window.currentJobs = currentJobs;



            if (jobsLoading) jobsLoading.classList.add("hidden");



            searchBtn.disabled = false;



            const totalPostings = currentAtsJobs.length + currentFounderJobs.length;



            if (resultsCountBadge) {



                resultsCountBadge.textContent = `${totalPostings} Verified Postings`;



            }



            const atsBadge = document.getElementById("atsCountBadge");



            if (atsBadge) atsBadge.textContent = currentAtsJobs.length;



            const founderBadge = document.getElementById("founderCountBadge");



            if (founderBadge) founderBadge.textContent = currentFounderJobs.length;



            enableExportButtons(currentAtsJobs.length > 0 || currentFounderJobs.length > 0);



            if (currentAtsJobs.length === 0) {



                if (jobListContainer) {



                    jobListContainer.innerHTML = `



                        <div class="glass-panel rounded-3xl border-2 border-slate-200/90 p-10 text-center shadow-md">



                            <p class="text-base font-black text-slate-900">No matching direct company jobs found with your current filters.</p>



                            <p class="text-sm font-semibold text-slate-600 mt-1.5">Try selecting "Any" compensation band or adding "Worldwide Remote".</p>



                        </div>



                    `;



                }



            } else {



                renderJobCards(currentAtsJobs, "jobListContainer", false);



                // Reveal LinkedIn Toggle at bottom of all verified direct ATS jobs



                if (bottomLinkedinToggleCard) {



                    bottomLinkedinToggleCard.classList.remove("hidden");



                }



            }



            renderFounderCards(currentFounderJobs);



            window.goToSlide(2);



        } catch (err) {



            if (jobsLoading) jobsLoading.classList.add("hidden");



            searchBtn.disabled = false;



            alert("Search failed: " + err.message);



        }



    }



    searchBtn.addEventListener("click", () => {
        if (!currentProfile) {
            alert("Please upload a candidate resume first to match live skills.");
            window.goToSlide(1);
            return;
        }

        // Onboarding Check: Guest candidates must sign up or log in first
        if (!isUserLoggedIn()) {
            window._pendingJobSearch = true;
            window.openProfileModal("search_intercept");
            return;
        }

        executeSearch();
        window.goToSlide(2);
    });
}

// Helper to format posting date with human-readable freshness badges



function formatJobDate(dateStr) {



    if (!dateStr) {



        return { label: "Posted Recently", isToday: true, tooltip: "Verified active this week" };



    }



    const str = String(dateStr).trim();



    if (/today|just now|hour|min/i.test(str)) {



        return { label: "Posted Today", isToday: true, tooltip: "Fresh vacancy active today" };



    }



    if (/yesterday/i.test(str)) {



        return { label: "1 day ago", isToday: false, tooltip: "Posted yesterday" };



    }



    if (/\b(\d+)\s*days?\s*ago/i.test(str)) {



        return { label: str, isToday: false, tooltip: str };



    }



    const d = new Date(str);



    if (isNaN(d.getTime())) {



        return { label: "Posted Recently", isToday: true, tooltip: "Verified active" };



    }



    const now = new Date();



    const diffMs = now - d;



    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));



    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));



    const fullDateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });



    if (diffDays <= 0 || diffHours < 24) {



        return { label: "Posted Today", isToday: true, tooltip: `Verified active • ${fullDateStr}` };



    } else if (diffDays === 1) {



        return { label: "1 day ago", isToday: false, tooltip: `Posted yesterday • ${fullDateStr}` };



    } else if (diffDays < 7) {



        return { label: `${diffDays} days ago`, isToday: false, tooltip: `Posted on ${fullDateStr}` };



    } else if (diffDays < 30) {



        const weeks = Math.max(1, Math.floor(diffDays / 7));



        return { label: `${weeks} ${weeks === 1 ? 'week' : 'weeks'} ago`, isToday: false, tooltip: `Posted on ${fullDateStr}` };



    } else {



        return { label: fullDateStr, isToday: false, tooltip: `Posted on ${fullDateStr}` };



    }



}



// Post-Search LinkedIn Toggle Controller with Show More Pagination



function initLinkedinToggle() {



    const toggle = document.getElementById("resultsLinkedinToggle");



    const sectionContainer = document.getElementById("linkedinSectionContainer");



    const cardsContainer = document.getElementById("linkedinCardsContainer");



    const loadingEl = document.getElementById("linkedinLoading");



    const loadMoreContainer = document.getElementById("linkedinLoadMoreContainer");



    const loadMoreBtn = document.getElementById("loadMoreLinkedinBtn");



    const loadMoreLoading = document.getElementById("linkedinLoadMoreLoading");



    const countBadge = document.getElementById("linkedinCountBadge");



    if (!toggle) return;



    let hasMoreLinkedin = false;



    async function fetchBatch(offset = 0) {



        const workMode = document.querySelector('input[name="work_mode"]:checked')?.value || "all";



        const empType = document.querySelector('input[name="employment_type"]:checked')?.value || "all";



        const resp = await fetch("/api/find-linkedin-jobs", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({



                profile: currentProfile,



                offset: offset,



                limit: 10,



                preferences: {



                    currency: currentCurrency,



                    min_package: currentMinPackage,



                    locations: selectedLocations,



                    work_mode: workMode,



                    employment_type: empType



                }



            })



        });



        if (!resp.ok) throw new Error("Could not fetch LinkedIn feed");



        return await resp.json();



    }



    toggle.addEventListener("change", async () => {



        if (toggle.checked) {



            if (sectionContainer) sectionContainer.classList.remove("hidden");



            



            // If already loaded for this search, just reveal and scroll gently



            if (currentLinkedinJobs && currentLinkedinJobs.length > 0) {



                sectionContainer?.scrollIntoView({ behavior: "smooth", block: "start" });



                return;



            }



            if (loadingEl) loadingEl.classList.remove("hidden");



            if (cardsContainer) cardsContainer.innerHTML = "";



            if (loadMoreContainer) loadMoreContainer.classList.add("hidden");



            try {



                const data = await fetchBatch(0);



                currentLinkedinJobs = data.jobs || [];



                hasMoreLinkedin = Boolean(data.has_more);



                if (loadingEl) loadingEl.classList.add("hidden");



                if (countBadge) {



                    countBadge.textContent = `${currentLinkedinJobs.length} External Posts`;



                }



                if (currentLinkedinJobs.length === 0) {



                    if (cardsContainer) {



                        cardsContainer.innerHTML = `



                            <div class="rounded-2xl p-8 text-center border border-slate-700 text-slate-300" style="background: rgba(13, 27, 42, 0.95);">



                                <p class="text-sm font-bold">No auxiliary LinkedIn postings found matching current keywords.</p>



                            </div>



                        `;



                    }



                } else {



                    renderJobCards(currentLinkedinJobs, "linkedinCardsContainer", true, false, 0);



                    sectionContainer?.scrollIntoView({ behavior: "smooth", block: "start" });



                    if (loadMoreContainer) {



                        if (hasMoreLinkedin) {



                            loadMoreContainer.classList.remove("hidden");



                        } else {



                            loadMoreContainer.classList.add("hidden");



                        }



                    }



                }



            } catch (e) {



                if (loadingEl) loadingEl.classList.add("hidden");



                if (cardsContainer) {



                    cardsContainer.innerHTML = `



                        <div class="rounded-2xl p-6 text-center border border-red-500/50 text-red-200" style="background: rgba(13, 27, 42, 0.95);">



                            <p class="text-sm font-bold">Failed to fetch auxiliary LinkedIn feed: ${e.message}</p>



                        </div>



                    `;



                }



            }



        } else {



            if (sectionContainer) sectionContainer.classList.add("hidden");



        }



    });



    if (loadMoreBtn) {



        loadMoreBtn.addEventListener("click", async () => {



            loadMoreBtn.disabled = true;



            if (loadMoreLoading) loadMoreLoading.classList.remove("hidden");



            try {



                const data = await fetchBatch(currentLinkedinJobs.length);



                const newBatch = data.jobs || [];



                hasMoreLinkedin = Boolean(data.has_more);



                if (newBatch.length > 0) {



                    const prevCount = currentLinkedinJobs.length;



                    currentLinkedinJobs = currentLinkedinJobs.concat(newBatch);



                    renderJobCards(newBatch, "linkedinCardsContainer", true, true, prevCount);



                    if (countBadge) {



                        countBadge.textContent = `${currentLinkedinJobs.length} External Posts`;



                    }



                }



                if (!hasMoreLinkedin || newBatch.length === 0) {



                    if (loadMoreContainer) {



                        loadMoreContainer.innerHTML = `



                            <span class="text-xs text-slate-400 font-bold bg-slate-900/80 px-4 py-2 rounded-xl border border-slate-700 inline-block shadow-sm">



                                All available auxiliary LinkedIn postings loaded (${currentLinkedinJobs.length} total)



                            </span>



                        `;



                    }



                }



            } catch (err) {



                console.error("Error loading more LinkedIn postings", err);



            } finally {



                loadMoreBtn.disabled = false;



                if (loadMoreLoading) loadMoreLoading.classList.add("hidden");



            }



        });



    }



}



function renderJobCards(jobs, containerId = "jobListContainer", isThirdParty = false, append = false, startIdx = 0) {



    const container = document.getElementById(containerId);



    if (!container) return;



    if (!append) container.innerHTML = "";



    jobs.forEach((job, idx) => {



        const globalIdx = startIdx + idx;



        const card = document.createElement("div");



        card.className = "kage-card rounded-3xl relative overflow-hidden group border border-slate-200/90 shadow-xl hover:shadow-2xl mb-6 transition-all bg-white";



        card.setAttribute("style", "box-shadow: 0 12px 35px -8px rgba(0, 0, 0, 0.08);");



        const isLinkedin = isThirdParty || Boolean(job.is_linkedin);



        



        // Match Score styling (Light Luxury Palette)



        const isHighScore = job.cvmatch_score >= 80;



        const scoreColor = isHighScore



            ? "bg-emerald-100 text-emerald-950 border-2 border-emerald-500/90 shadow-sm"



            : "bg-amber-100 text-amber-950 border-2 border-amber-400/90 shadow-sm";



        const scoreDot = isHighScore



            ? `<span class="w-2.5 h-2.5 rounded-full bg-emerald-600 animate-pulse"></span>`



            : `<span class="w-2.5 h-2.5 rounded-full bg-amber-600"></span>`;



        // Live Blinking Green Badge



        const liveBadgeHtml = `



            <span class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-950 border-2 border-emerald-400/90 font-black text-xs shadow-xs" title="Active real-time vacancy verified on corporate portal">



                <span class="relative flex h-2.5 w-2.5">



                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>



                    <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>



                </span>



                <span class="uppercase tracking-wider font-extrabold text-[11px] text-emerald-900">LIVE</span>



            </span>



        `;



        // Date Badge



        const dateInfo = formatJobDate(job.posted_at || job.created_at);



        const dateBadgeHtml = dateInfo.isToday



            ? `<span class="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-emerald-50 text-emerald-900 border border-emerald-300 text-xs font-extrabold shadow-xs" title="${dateInfo.tooltip}">



                <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-600"></i>



                <span>${dateInfo.label}</span>



               </span>`



            : `<span class="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold shadow-xs" title="${dateInfo.tooltip}">



                <i data-lucide="calendar" class="w-3.5 h-3.5 text-slate-500"></i>



                <span>${dateInfo.label}</span>



               </span>`;



        const empTag = job.employment_type_tag || "Full-Time";



        const rawSource = (job.source || "Direct Feed").toUpperCase();



        const sourceBadgeHtml = isLinkedin 



            ? `<span class="text-xs font-black px-3 py-1.5 rounded-xl bg-[#0A66C2] text-white flex items-center space-x-1.5 shadow-sm">



                <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.6 1.6 0 0 0-1.6 1.6 1.6 1.6 0 0 0 1.6-1.6Z"/></svg>



                <span>LINKEDIN FEED</span>



               </span>`



            : `<span class="text-xs font-black px-3 py-1.5 rounded-xl bg-violet-950 text-violet-200 uppercase tracking-wider flex items-center space-x-1.5 border border-violet-500/40 shadow-sm" title="Direct Enterprise Applicant Tracking System">



                <i data-lucide="shield-check" class="w-4 h-4 text-violet-400"></i>



                <span>DIRECT FEED • ${rawSource}</span>



               </span>`;



        const thirdPartyWarning = isLinkedin



            ? `<div class="mt-3 p-3 rounded-xl flex items-center space-x-2.5 shadow-md border" style="background: linear-gradient(135deg, #0d1b2a 0%, #081018 100%); border-color: rgba(245, 158, 11, 0.7);">



                <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-400 flex-shrink-0"></i>



                <span class="text-xs font-bold text-slate-200">Auxiliary Feed Posting — Verify listing status directly. Direct company application is recommended.</span>



               </div>`



            : '';



        const isLocked = Boolean(job.is_locked);



        // Action Buttons: If locked, show unblurred job card with locked CTA buttons and blurred direct link



        let applyBtnHtml = '';



        let pitchBtnHtml = '';



        if (isLocked) {



            pitchBtnHtml = `



                <button type="button" onclick="openVipPricingModal()" class="px-4 py-2.5 rounded-xl border-2 border-slate-300 bg-white hover:bg-slate-100 text-slate-800 text-xs sm:text-sm font-black flex items-center space-x-2 transition shadow-sm cursor-pointer">



                    <i data-lucide="lock" class="w-4 h-4 text-slate-500"></i>



                    <span>Generate AI STAR Pitch (VIP)</span>



                </button>



            `;



            applyBtnHtml = `



                <button type="button" onclick="openVipPricingModal()" class="w-full py-3.5 px-5 bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white border border-violet-400/40 text-xs sm:text-sm font-black rounded-xl flex items-center justify-center space-x-2 shadow-xl shadow-violet-600/30 transition transform active:scale-95 cursor-pointer">



                    <i data-lucide="lock" class="w-4 h-4 text-violet-200"></i>



                    <span>Unlock Direct Application Portal (VIP Access)</span>



                </button>



            `;



        } else {



            pitchBtnHtml = `



                <div class="flex items-center space-x-2 flex-wrap gap-y-2">



                    <button type="button" class="generate-pitch-btn px-3.5 py-2 rounded-xl border border-violet-300 bg-violet-100/80 hover:bg-violet-200 text-violet-950 text-xs sm:text-sm font-black flex items-center space-x-1.5 transition shadow-sm cursor-pointer" data-container="${containerId}" data-idx="${globalIdx}">



                        <i data-lucide="sparkles" class="w-4 h-4 text-violet-700"></i>



                        <span>AI Pitch</span>



                    </button>



                    <button type="button" class="generate-cover-letter-btn px-3.5 py-2 rounded-xl border border-slate-300 bg-white hover:bg-violet-50 text-slate-900 hover:text-violet-900 text-xs sm:text-sm font-black flex items-center space-x-1.5 transition shadow-sm cursor-pointer" data-container="${containerId}" data-idx="${globalIdx}">



                        <i data-lucide="file-text" class="w-4 h-4 text-violet-700"></i>



                        <span>Cover Letter</span>



                    </button>



                    <button type="button" class="save-kanban-btn px-3 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-800 text-xs sm:text-sm font-bold flex items-center space-x-1 transition cursor-pointer" data-container="${containerId}" data-idx="${globalIdx}" title="Save to Target list">



                        <i data-lucide="bookmark" class="w-3.5 h-3.5 text-slate-500"></i>



                        <span>Save</span>



                    </button>



                </div>



            `;



            applyBtnHtml = isLinkedin



                ? `<a href="${job.url}" target="_blank" rel="noopener noreferrer" class="direct-apply-link w-full py-3.5 px-5 bg-[#0A66C2] hover:bg-[#004182] text-white text-xs sm:text-sm font-black rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-blue-600/30 transition transform active:scale-98" data-container="${containerId}" data-idx="${globalIdx}">



                    <span>Apply on LinkedIn</span>



                    <i data-lucide="external-link" class="w-4 h-4"></i>



                   </a>`



                : `<a href="${job.url}" target="_blank" rel="noopener noreferrer" class="direct-apply-link w-full py-3.5 px-5 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 text-white font-black text-xs sm:text-sm rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/25 transition transform active:scale-98" data-container="${containerId}" data-idx="${globalIdx}">



                    <span>Direct Application Portal →</span>



                    <i data-lucide="external-link" class="w-4 h-4"></i>



                   </a>`;



        }



                // Check if candidate already applied or saved this job
        const currentKanban = getKanbanData();
        const allAppliedList = [
            ...(currentKanban.applied || []),
            ...(currentKanban.interview || []),
            ...(currentKanban.offer || [])
        ];
        const isAlreadyApplied = allAppliedList.some(a => {
            const appliedTitle = (a.title || a.role || '').toLowerCase().trim();
            const jobTitle = (job.title || job.role || '').toLowerCase().trim();
            const appliedCompany = (a.company || '').toLowerCase().trim();
            const jobCompany = (job.company || '').toLowerCase().trim();
            const matchCompany = appliedCompany && jobCompany && appliedCompany === jobCompany;
            const matchRole = appliedTitle && jobTitle && (appliedTitle === jobTitle || appliedTitle.includes(jobTitle) || jobTitle.includes(appliedTitle));
            const matchId = (a.job_id && (a.job_id === job.public_slug || a.job_id === job.id)) ||
                            (a.id && (a.id === job.public_slug || a.id === job.id)) ||
                            (a.url && job.url && a.url === job.url);
            return matchId || (matchCompany && matchRole);
        });

        const alreadyAppliedBadgeHtml = isAlreadyApplied ? `
            <button type="button" onclick="goToKanbanTabAndScroll()" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-violet-100 hover:bg-violet-200 border-2 border-violet-500 text-violet-950 font-black text-xs shadow-xs transition cursor-pointer" title="Already in your applied tracker. Click to view on Kanban.">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-violet-700"></i>
                <span>Already Applied • Check Status</span>
            </button>
        ` : '';

        const matchedSkillsHtml = (job.matched_skills || []).slice(0, 8).map(s => 



            `<span class="px-2.5 py-1 bg-white text-slate-900 text-xs font-bold rounded-lg border border-slate-300 shadow-xs hover:border-violet-400 hover:text-violet-900 transition">${s}</span>`



        ).join("");



        // Clean compensation text to fully expand YOE



        let cleanCompDisplay = (job.comp_display || 'Market Standard for Candidate Years of Experience')



            .replace(/\bYOE\b/g, 'Candidate Years of Experience');



        const lockedEndpointBar = isLocked ? `



            <div class="mt-3 p-3 rounded-xl border border-dashed border-slate-300 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-xs">



                <div class="flex items-center space-x-2 text-xs font-bold text-slate-700">



                    <i data-lucide="shield-check" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>



                    <span>Direct Verified Application Link:</span>



                </div>



                <div class="flex items-center space-x-2 overflow-hidden">



                    <span class="font-mono text-xs text-slate-500 select-none bg-slate-100 px-3 py-1 rounded-lg border border-slate-200 filter blur-[4px] truncate max-w-[190px]">



                        https://jobs.${(job.source || 'lever').toLowerCase()}.co/${(job.company || 'hiring').toLowerCase().replace(/[^a-z0-9]/g, '')}/apply



                    </span>



                    <span class="text-[10px] font-black uppercase tracking-wider text-white bg-gradient-to-r from-violet-600 to-indigo-600 border border-violet-400 px-2 py-0.5 rounded-md flex-shrink-0">VIP Locked</span>



                </div>



            </div>



        ` : '';



        // Right side header & guarantees (LinkedIn removes false 0% recruiter spread guarantee)



        const rightHeaderHtml = isLinkedin ? `



            <div class="flex items-center justify-between">



                <span class="text-[11px] font-black uppercase tracking-wider text-amber-950 bg-amber-100 px-3 py-1 rounded-lg border border-amber-300 flex items-center gap-1.5 shadow-xs">



                    <i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-amber-600"></i>



                    <span>Auxiliary LinkedIn Listing</span>



                </span>



                <span class="text-xs text-amber-800 font-mono font-bold">Unverified Agency Spread</span>



            </div>



        ` : `



            <div class="flex items-center justify-between">



                <span class="text-[11px] font-black uppercase tracking-wider text-emerald-950 bg-emerald-100/90 px-3 py-1 rounded-lg border border-emerald-300 flex items-center gap-1.5 shadow-xs">



                    <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-700"></i>



                    <span>Direct Corporate Portal</span>



                </span>



                <span class="text-xs text-slate-500 font-mono font-bold">0% Recruiter Spread</span>



            </div>



        `;



        const guaranteesHtml = isLinkedin ? `



            <div class="text-xs text-slate-700 space-y-1.5 font-medium">



                <p class="flex items-center gap-2">



                    <i data-lucide="external-link" class="w-4 h-4 text-amber-500 flex-shrink-0"></i>



                    <span>Aggregated listing from external third-party LinkedIn feed</span>



                </p>



                <p class="flex items-center gap-2">



                    <i data-lucide="info" class="w-4 h-4 text-amber-600 flex-shrink-0"></i>



                    <span>Direct corporate application recommended to bypass recruiter cut</span>



                </p>



            </div>



        ` : `



            <div class="text-xs text-slate-700 space-y-1.5 font-medium">



                <p class="flex items-center gap-2">



                    <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>



                    <span>Application lands directly in corporate ${job.source || 'company'} portal</span>



                </p>



                <p class="flex items-center gap-2">



                    <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>



                    <span>Zero third-party headhunters or agency commission cut</span>



                </p>



            </div>



        `;



        card.innerHTML = `



            <!-- Modern Dual-Tone Card (Left White/Cream, Right Sleek Luxury Platinum) -->



            <div class="flex flex-col lg:flex-row items-stretch">



                



                <!-- LEFT SIDE: Title, Role, Company, Skills, AI Pitch -->



                <div class="w-full lg:w-7/12 p-6 sm:p-7 flex flex-col justify-between bg-white">



                    <div>



                        <!-- Badges Row -->



                        <div class="flex items-center flex-wrap gap-2 mb-3">



                            <span class="text-xs sm:text-sm font-black px-3.5 py-1.5 rounded-xl flex items-center space-x-1.5 ${scoreColor}">



                                ${scoreDot}



                                <span>${job.cvmatch_score}% CV Match</span>



                            </span>
                            <button type="button" onclick="window.toggleSkillGapDrawer('${containerId}_${globalIdx}')" class="text-xs font-bold px-2.5 py-1.5 rounded-xl border border-violet-300 bg-violet-50 hover:bg-violet-100 text-violet-900 shadow-2xs flex items-center gap-1 transition cursor-pointer" title="Inspect matched skills vs missing keywords">
                                <i data-lucide="scan-search" class="w-3.5 h-3.5 text-violet-600"></i>
                                <span>Skill Gap</span>
                            </button>



                            ${liveBadgeHtml}



                            ${dateBadgeHtml}



                            ${sourceBadgeHtml}
                            ${alreadyAppliedBadgeHtml}
                            <span class="text-xs font-black px-3 py-1.5 rounded-xl bg-slate-100 text-slate-800 border border-slate-200 shadow-xs">
                                ${empTag}
                            </span>



                            <span class="text-xs font-black text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">#${globalIdx + 1}</span>



                        </div>



                        <!-- Job Title -->



                        <h3 class="text-xl sm:text-2xl font-black text-slate-950 group-hover:text-violet-700 transition-colors tracking-tight leading-tight">



                            ${job.title}



                        </h3>



                        <!-- Company, Location, Work Mode -->



                        <div class="flex items-center flex-wrap gap-2 text-sm font-bold text-slate-700 pt-2">



                            <span class="flex items-center space-x-1.5 text-slate-950 font-black">



                                <i data-lucide="building-2" class="w-4 h-4 text-violet-700"></i>



                                <span>${job.company}</span>



                            </span>



                            <span class="text-slate-400">•</span>



                            <span class="flex items-center space-x-1.5 text-slate-800 font-extrabold">



                                <i data-lucide="map-pin" class="w-4 h-4 text-slate-600"></i>



                                <span>${job.location_tag || job.location || 'Remote'}</span>



                            </span>



                            <span class="px-2.5 py-0.5 rounded-lg bg-amber-100 text-amber-950 text-xs font-black uppercase tracking-wider border border-amber-300">${job.work_mode || 'Remote'}</span>



                        </div>



                        ${thirdPartyWarning}



                        <!-- Overlap Skills -->



                        ${matchedSkillsHtml ? `



                            <div class="mt-4 pt-3.5 border-t border-slate-200 flex flex-wrap items-center gap-1.5">



                                <span class="text-xs font-black text-slate-700 uppercase tracking-wider mr-1">Overlap Skills:</span>



                                ${matchedSkillsHtml}



                            </div>



                        ` : ''}



                    </div>



                    <!-- Skill Gap Inspector Drawer -->
                    <div id="skillGapDrawer_${containerId}_${globalIdx}" class="hidden mt-3 p-3.5 rounded-2xl bg-slate-50 border border-violet-200 text-xs transition-all">
                        <div class="flex items-center justify-between mb-2">
                            <span class="font-black text-slate-950 flex items-center gap-1.5">
                                <span class="w-2 h-2 rounded-full bg-violet-600 animate-pulse"></span>
                                Resume Matcher &bull; Skill Gap Breakdown
                            </span>
                            <span class="text-[10px] font-bold text-slate-500">Vector Keyword Optimizer</span>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2.5">
                            <div class="p-2.5 rounded-xl bg-white border border-emerald-200">
                                <span class="text-[10px] font-black uppercase text-emerald-800 tracking-wider block mb-1">✓ Matched in Your Profile</span>
                                <div class="flex flex-wrap gap-1">
                                    ${(job.matched_skills || []).slice(0, 6).map(s => `<span class="px-2 py-0.5 bg-emerald-50 text-emerald-900 border border-emerald-200 rounded font-bold text-[10px]">${s}</span>`).join('') || '<span class="text-slate-400 text-[10px]">Core stack matched</span>'}
                                </div>
                            </div>
                            <div class="p-2.5 rounded-xl bg-white border border-amber-300">
                                <span class="text-[10px] font-black uppercase text-amber-900 tracking-wider block mb-1">+ Missing Gap Keywords to Highlight</span>
                                <div class="flex flex-wrap gap-1">
                                    ${(job.gap_skills || ['Docker', 'Kubernetes', 'Cloud']).slice(0, 4).map(s => `<span class="px-2 py-0.5 bg-amber-50 text-amber-950 border border-amber-300 rounded font-bold text-[10px]">+ ${s}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="pt-1.5 border-t border-slate-200 flex items-center justify-between">
                            <p class="text-[11px] text-slate-700 font-medium">
                                <strong class="text-violet-950 font-bold">Screening Advantage:</strong> Mentioning these gap keywords lifts screening pass rate from <strong>${job.cvmatch_score}%</strong> to <strong>90%+</strong>.
                            </p>
                            <span class="text-[10px] font-bold text-slate-400">Direct ATS Vector</span>
                        </div>
                    </div>

                    <!-- Left Bottom Buttons: AI Pitch, Cover Letter, Save -->



                    <div class="mt-5 pt-4 border-t border-slate-200">



                        ${pitchBtnHtml}



                    </div>



                </div>



                <!-- RIGHT SIDE: Suitable, Modern & Elegant Platinum Finish (Compensation, Guarantee, Direct Apply) -->



                <div class="w-full lg:w-5/12 p-6 sm:p-7 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-200/90" style="background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);">



                    <div class="space-y-4">



                        <!-- Direct ATS / LinkedIn Guarantee Header -->



                        ${rightHeaderHtml}



                        <!-- Compensation Box in Clean Modern Emerald Style -->



                        <div class="p-4 rounded-2xl border border-emerald-200/90 bg-emerald-50/60 shadow-xs">



                            <span class="text-[11px] font-mono font-bold uppercase tracking-wider text-emerald-800 block mb-1">Target Package / Compensation</span>



                            <div class="flex items-center space-x-2 text-emerald-950 text-base sm:text-lg font-black">



                                <i data-lucide="badge-dollar-sign" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>



                                <span>${cleanCompDisplay}</span>



                            </div>
                            <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100/80 text-emerald-950 text-[10px] font-black border border-emerald-300 mt-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                                <span>P75 Market Comp &bull; 0% Recruiter Spread</span>
                            </div>



                        </div>



                        <!-- ATS Portal Breakdown Note / LinkedIn Transparency Note -->



                        ${guaranteesHtml}



                        <!-- Locked Preview Endpoint Bar (if locked) -->



                        ${lockedEndpointBar}



                    </div>



                    <!-- Direct Apply Action CTA Button -->



                    <div class="mt-6 pt-4 border-t border-slate-200">



                        ${applyBtnHtml}



                    </div>



                </div>



            </div>



        `;



        container.appendChild(card);



    });



    if (window.lucide) lucide.createIcons();



    // Reattach event listeners



    container.querySelectorAll(".generate-pitch-btn").forEach(btn => {



        btn.onclick = () => {



            const cId = btn.getAttribute("data-container");



            const idx = parseInt(btn.getAttribute("data-idx"));



            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);



            if (targetList && targetList[idx]) {



                openPitchModal(targetList[idx]);



            }



        };



    });



    container.querySelectorAll(".generate-cover-letter-btn").forEach(btn => {



        btn.onclick = () => {



            const cId = btn.getAttribute("data-container");



            const idx = parseInt(btn.getAttribute("data-idx"));



            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);



            if (targetList && targetList[idx]) {



                openCoverLetterModal(targetList[idx]);



            }



        };



    });



    container.querySelectorAll(".save-kanban-btn").forEach(btn => {



        btn.onclick = () => {



            const cId = btn.getAttribute("data-container");



            const idx = parseInt(btn.getAttribute("data-idx"));



            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);



            if (targetList && targetList[idx]) {



                saveJobToTarget(targetList[idx]);



            }



        };



    });



    container.querySelectorAll(".direct-apply-link").forEach(link => {



        link.onclick = () => {



            const cId = link.getAttribute("data-container");



            const idx = parseInt(link.getAttribute("data-idx"));



            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);



            if (targetList && targetList[idx]) {



                trackJobApplication(targetList[idx]);



            }



        };



    });



}



// 5. Pitch Modal



function initModal() {



    const modal = document.getElementById("pitchModal");



    const closeBtn = document.getElementById("closePitchModal");



    const copyBtn = document.getElementById("copyPitchBtn");



    const copyBtnText = document.getElementById("copyBtnText");



    if (!modal) return;



    closeBtn?.addEventListener("click", () => {



        modal.classList.add("hidden");



    });



    modal.addEventListener("click", (e) => {



        if (e.target === modal) {



            modal.classList.add("hidden");



        }



    });



    copyBtn?.addEventListener("click", () => {



        const pitchTextarea = document.getElementById("pitchTextarea");



        pitchTextarea.select();



        navigator.clipboard.writeText(pitchTextarea.value).then(() => {



            copyBtnText.textContent = "Copied to Clipboard!";



            setTimeout(() => {



                copyBtnText.textContent = "Copy to Clipboard";



            }, 2000);



        });



    });



}



async function openPitchModal(job) {



    const modal = document.getElementById("pitchModal");



    const pitchSub = document.getElementById("pitchJobSub");



    const pitchTextarea = document.getElementById("pitchTextarea");



    if (!modal) return;



    pitchSub.textContent = `Target: ${job.title} at ${job.company}`;



    pitchTextarea.value = "Synthesizing STAR-grounded application pitch based on your verified candidate metrics...";



    modal.classList.remove("hidden");



    try {



        const resp = await fetch("/api/get-pitch", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({



                profile: currentProfile,



                job: job



            })



        });



        if (!resp.ok) throw new Error("Could not generate pitch.");



        const data = await resp.json();



        pitchTextarea.value = data.pitch;



    } catch (err) {



        pitchTextarea.value = "Error generating pitch: " + err.message;



    }



}



// 5b. Cover Letter Modal & Generation



function initCoverLetterModal() {



    const modal = document.getElementById("coverLetterModal");



    const closeBtn = document.getElementById("closeCoverLetterModal");



    const copyBtn = document.getElementById("copyCoverLetterBtn");



    const copyBtnText = document.getElementById("copyCoverLetterBtnText");



    const downloadBtn = document.getElementById("downloadCoverLetterBtn");



    if (!modal) return;



    closeBtn?.addEventListener("click", () => {



        modal.classList.add("hidden");



    });



    modal.addEventListener("click", (e) => {



        if (e.target === modal) {



            modal.classList.add("hidden");



        }



    });



    copyBtn?.addEventListener("click", () => {



        const textarea = document.getElementById("coverLetterTextarea");



        if (!textarea) return;



        textarea.select();



        navigator.clipboard.writeText(textarea.value).then(() => {



            if (copyBtnText) copyBtnText.textContent = "Copied!";



            setTimeout(() => {



                if (copyBtnText) copyBtnText.textContent = "Copy Letter";



            }, 2000);



        });



    });



    downloadBtn?.addEventListener("click", () => {



        const textarea = document.getElementById("coverLetterTextarea");



        if (!textarea || !textarea.value) return;



        const blob = new Blob([textarea.value], { type: "text/plain;charset=utf-8" });



        const a = document.createElement("a");



        a.href = URL.createObjectURL(blob);



        a.download = `Tailored_Cover_Letter_${Date.now()}.txt`;



        a.click();



    });



}



async function openCoverLetterModal(job) {



    const modal = document.getElementById("coverLetterModal");



    const sub = document.getElementById("coverLetterSub");



    const textarea = document.getElementById("coverLetterTextarea");



    if (!modal) return;



    sub.textContent = `Tailored for ${job.title} at ${job.company}`;



    textarea.value = "Synthesizing executive cover letter grounded in your verified achievements...";



    modal.classList.remove("hidden");



    try {



        const resp = await fetch("/api/get-cover-letter", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({



                profile: currentProfile,



                job: job



            })



        });



        if (!resp.ok) throw new Error("Could not generate cover letter.");



        const data = await resp.json();



        textarea.value = data.cover_letter;



    } catch (err) {



        textarea.value = "Error generating cover letter: " + err.message;



    }



}



// 5c. View Switcher Tabs (Direct ATS / Founder Direct / Kanban Tracker)



function initResultsTabs() {



    const tabAts = document.getElementById("tabAtsJobs");



    const tabFounder = document.getElementById("tabFounderJobs");



    const tabKanban = document.getElementById("tabKanbanTracker");



    const atsContainer = document.getElementById("jobListContainer");



    const founderContainer = document.getElementById("founderListContainer");



    const kanbanContainer = document.getElementById("kanbanBoardContainer");



    function setActiveTab(activeBtn) {



        [tabAts, tabFounder, tabKanban].forEach(btn => {



            if (!btn) return;



            if (btn === activeBtn) {



                btn.className = "tab-btn px-4 py-2 rounded-xl text-xs font-black bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md shadow-violet-500/20 flex items-center space-x-2 transition cursor-pointer";



            } else {



                btn.className = "tab-btn px-4 py-2 rounded-xl text-xs font-black bg-white border border-slate-200 text-slate-700 hover:border-violet-300 hover:bg-violet-50/50 flex items-center space-x-2 transition cursor-pointer";



            }



        });



    }



    tabAts?.addEventListener("click", () => {



        setActiveTab(tabAts);



        atsContainer?.classList.remove("hidden");



        founderContainer?.classList.add("hidden");



        kanbanContainer?.classList.add("hidden");



    });



    tabFounder?.addEventListener("click", () => {



        setActiveTab(tabFounder);



        founderContainer?.classList.remove("hidden");



        atsContainer?.classList.add("hidden");



        kanbanContainer?.classList.add("hidden");



    });



    tabKanban?.addEventListener("click", () => {



        setActiveTab(tabKanban);



        kanbanContainer?.classList.remove("hidden");



        atsContainer?.classList.add("hidden");



        founderContainer?.classList.add("hidden");



        renderKanbanBoard();



    });



}



// 5d. YC & Hacker News Founder Direct Cards Renderer



function renderFounderCards(founderJobs) {



    const wrapper = document.getElementById("founderCardsWrapper");



    if (!wrapper) return;



    wrapper.innerHTML = "";



    if (!founderJobs || founderJobs.length === 0) {



        wrapper.innerHTML = `



            <div class="rounded-3xl border border-slate-200 p-10 text-center shadow-lg bg-white text-slate-800">



                <p class="text-base font-black text-slate-900">No founder direct postings matched current keywords.</p>



                <p class="text-sm font-semibold text-slate-600 mt-1.5">Founder threads are indexed directly from verified Hacker News and Y Combinator leadership feeds.</p>



            </div>



        `;



        return;



    }



    founderJobs.forEach((job, idx) => {



        const card = document.createElement("div");



        card.className = "kage-card rounded-3xl relative overflow-hidden group border border-slate-200/90 shadow-xl hover:shadow-2xl mb-6 transition-all bg-white";



        card.setAttribute("style", "box-shadow: 0 12px 35px -8px rgba(0, 0, 0, 0.08);");



        const scoreColor = "bg-orange-100 text-orange-950 border-2 border-orange-400/90 shadow-sm";



        const emailPill = job.founder_email ? `



            <a href="mailto:${job.founder_email}?subject=Application:%20${encodeURIComponent(job.title)}" class="inline-flex items-center space-x-1.5 px-3 py-1 bg-orange-100 hover:bg-orange-200 text-orange-900 text-xs font-black rounded-lg transition border border-orange-300">



                <i data-lucide="mail" class="w-3.5 h-3.5 text-orange-700"></i>



                <span>Direct Contact: ${job.founder_email}</span>



            </a>



        ` : '';



        // Live Blinking Green Badge for Founder Cards



        const liveBadgeHtml = `



            <span class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-950 border-2 border-emerald-400/90 font-black text-xs shadow-xs" title="Live founder vacancy verified directly from executive leadership">



                <span class="relative flex h-2.5 w-2.5">



                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>



                    <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>



                </span>



                <span class="uppercase tracking-wider font-extrabold text-[11px] text-emerald-900">LIVE</span>



            </span>



        `;



        // Date Badge



        const dateInfo = formatJobDate(job.posted_at || job.created_at);



        const dateBadgeHtml = dateInfo.isToday



            ? `<span class="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-emerald-50 text-emerald-900 border border-emerald-300 text-xs font-extrabold shadow-xs" title="${dateInfo.tooltip}">



                <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-600"></i>



                <span>${dateInfo.label}</span>



               </span>`



            : `<span class="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold shadow-xs" title="${dateInfo.tooltip}">



                <i data-lucide="calendar" class="w-3.5 h-3.5 text-slate-500"></i>



                <span>${dateInfo.label}</span>



               </span>`;



        const matchedSkillsHtml = (job.matched_skills || []).slice(0, 6).map(s => 



            `<span class="px-2.5 py-1 bg-white text-slate-900 text-xs font-bold rounded-lg border border-slate-300 shadow-xs">${s}</span>`



        ).join("");



        let cleanCompDisplay = (job.comp_display || 'Market Standard for Candidate Years of Experience')



            .replace(/\bYOE\b/g, 'Candidate Years of Experience');



        card.innerHTML = `



            <!-- Modern Dual-Tone Card (Left White/Cream, Right Sleek Luxury Platinum) -->



            <div class="flex flex-col lg:flex-row items-stretch">



                



                <!-- LEFT SIDE: Title, Role, Company, Skills, AI Pitch -->



                <div class="w-full lg:w-7/12 p-6 sm:p-7 flex flex-col justify-between bg-white">



                    <div>



                        <!-- Badges Row -->



                        <div class="flex items-center flex-wrap gap-2 mb-3">



                            <span class="text-xs sm:text-sm font-black px-3.5 py-1.5 rounded-xl flex items-center space-x-1.5 ${scoreColor}">



                                <span class="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse"></span>



                                <span>${job.cvmatch_score}% Profile Match</span>



                            </span>



                            ${liveBadgeHtml}



                            ${dateBadgeHtml}



                            <span class="text-xs font-black px-3 py-1.5 rounded-xl bg-orange-500 text-white flex items-center space-x-1.5 shadow-sm">



                                <span>🚀 ${job.is_yc ? "Y COMBINATOR FOUNDER" : "HACKER NEWS FOUNDER DIRECT"}</span>



                            </span>



                            <span class="text-xs font-black px-3 py-1.5 rounded-xl bg-slate-100 text-slate-800 border border-slate-200">



                                Zero Recruiter Cuts



                            </span>



                            <span class="text-xs font-black text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">#${idx + 1}</span>



                        </div>



                        <!-- Job Title -->



                        <h3 class="text-xl sm:text-2xl font-black text-slate-950 group-hover:text-orange-600 transition-colors tracking-tight leading-tight">



                            ${job.title}



                        </h3>



                        <!-- Company, Location -->



                        <div class="flex items-center flex-wrap gap-2 text-sm font-bold text-slate-700 pt-2">



                            <span class="flex items-center space-x-1.5 text-slate-950 font-black">



                                <i data-lucide="building-2" class="w-4 h-4 text-orange-600"></i>



                                <span>${job.company}</span>



                            </span>



                            <span class="text-slate-400">•</span>



                            <span class="flex items-center space-x-1.5 text-slate-800 font-extrabold">



                                <i data-lucide="map-pin" class="w-4 h-4 text-slate-600"></i>



                                <span>${job.location || 'Remote'}</span>



                            </span>



                        </div>



                        ${emailPill ? `<div class="pt-2">${emailPill}</div>` : ''}



                        <p class="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium pt-2 line-clamp-3">



                            ${job.summary || job.full_text || ''}



                        </p>



                        <!-- Overlap Skills -->



                        ${matchedSkillsHtml ? `



                            <div class="mt-4 pt-3.5 border-t border-slate-200 flex flex-wrap items-center gap-1.5">



                                <span class="text-xs font-black text-slate-700 uppercase tracking-wider mr-1">Overlap Skills:</span>



                                ${matchedSkillsHtml}



                            </div>



                        ` : ''}



                    </div>



                    <!-- Left Bottom Buttons -->



                    <div class="mt-5 pt-4 border-t border-slate-200 flex items-center space-x-2 flex-wrap gap-y-2">



                        <button type="button" class="generate-pitch-btn px-3.5 py-2 rounded-xl border border-orange-300 bg-orange-100 hover:bg-orange-200 text-orange-950 text-xs sm:text-sm font-black flex items-center space-x-1.5 transition shadow-sm cursor-pointer" data-container="founderCardsWrapper" data-idx="${idx}">



                            <i data-lucide="sparkles" class="w-4 h-4 text-orange-600"></i>



                            <span>AI Pitch</span>



                        </button>



                        <button type="button" class="generate-cover-letter-btn px-3.5 py-2 rounded-xl border border-slate-300 bg-white hover:bg-orange-50 text-slate-800 hover:text-orange-950 text-xs sm:text-sm font-black flex items-center space-x-1.5 transition shadow-sm cursor-pointer" data-container="founderCardsWrapper" data-idx="${idx}">



                            <i data-lucide="file-text" class="w-4 h-4 text-orange-600"></i>



                            <span>Cover Letter</span>



                        </button>



                        <button type="button" class="save-kanban-btn px-3 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-800 text-xs sm:text-sm font-bold flex items-center space-x-1 transition cursor-pointer" data-container="founderCardsWrapper" data-idx="${idx}" title="Save to Target list">



                            <i data-lucide="bookmark" class="w-3.5 h-3.5 text-slate-500"></i>



                            <span>Save</span>



                        </button>



                    </div>



                </div>



                <!-- RIGHT SIDE: Suitable, Modern & Elegant Platinum Finish -->



                <div class="w-full lg:w-5/12 p-6 sm:p-7 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-200/90" style="background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);">



                    <div class="space-y-4">



                        <div class="flex items-center justify-between">



                            <span class="text-[11px] font-black uppercase tracking-wider text-orange-950 bg-orange-100/90 px-3 py-1 rounded-lg border border-orange-300 flex items-center gap-1.5 shadow-xs">



                                <span>🚀 Direct Founder Access</span>



                            </span>



                            <span class="text-xs text-slate-500 font-mono font-bold">0% Recruiter Spread</span>



                        </div>



                        <div class="p-4 rounded-2xl border border-orange-200/90 bg-orange-50/60 shadow-xs">



                            <span class="text-[11px] font-mono font-bold uppercase tracking-wider text-orange-800 block mb-1">Target Package / Compensation</span>



                            <div class="flex items-center space-x-2 text-orange-950 text-base sm:text-lg font-black">



                                <i data-lucide="badge-dollar-sign" class="w-4 h-4 text-orange-600 flex-shrink-0"></i>



                                <span>${cleanCompDisplay}</span>



                            </div>



                        </div>



                        <div class="text-xs text-slate-700 space-y-1.5 font-medium">



                            <p class="flex items-center gap-2">



                                <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>



                                <span>Direct contact with founding team & executives</span>



                            </p>



                            <p class="flex items-center gap-2">



                                <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>



                                <span>Zero recruiter markups or intermediary delay</span>



                            </p>



                        </div>



                    </div>



                    <div class="mt-6 pt-4 border-t border-slate-200">



                        <a href="${job.url}" target="_blank" rel="noopener noreferrer" class="direct-apply-link w-full py-3.5 px-5 bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white font-black text-xs sm:text-sm rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-orange-500/25 transition transform active:scale-98" data-container="founderCardsWrapper" data-idx="${idx}">



                            <span>Direct Apply to Founder →</span>



                            <i data-lucide="external-link" class="w-4 h-4"></i>



                        </a>



                    </div>



                </div>



            </div>



        `;



        wrapper.appendChild(card);



    });



    if (window.lucide) lucide.createIcons();



}



// 5e. 100% Client-Side LocalStorage Application Kanban Tracker



const KANBAN_STORAGE_KEY = "almond_kanban_data";



function getKanbanData() {



    try {



        const raw = localStorage.getItem(KANBAN_STORAGE_KEY);



        if (raw) return JSON.parse(raw);



    } catch (e) {



        console.error("Error reading Kanban storage", e);



    }



    return {



        saved: [],



        applied: [],



        interview: [],



        offer: []



    };



}



function saveKanbanData(data) {
    try {
        localStorage.setItem(KANBAN_STORAGE_KEY, JSON.stringify(data));
        updateKanbanBadges();
        if (typeof window.syncKanbanToCloud === "function") {
            window.syncKanbanToCloud(data);
        }
    } catch (e) {



        console.error("Error saving Kanban storage", e);



    }



}



function updateKanbanBadges() {



    const data = getKanbanData();



    const total = (data.saved?.length || 0) + (data.applied?.length || 0) + (data.interview?.length || 0) + (data.offer?.length || 0);



    const badge = document.getElementById("kanbanCountBadge");



    if (badge) badge.textContent = total;



    



    const countSaved = document.getElementById("colCountSaved");



    if (countSaved) countSaved.textContent = data.saved?.length || 0;



    const countApplied = document.getElementById("colCountApplied");



    if (countApplied) countApplied.textContent = data.applied?.length || 0;



    const countInterview = document.getElementById("colCountInterview");



    if (countInterview) countInterview.textContent = data.interview?.length || 0;



    const countOffer = document.getElementById("colCountOffer");



    if (countOffer) countOffer.textContent = data.offer?.length || 0;



}



function trackJobApplication(job) {



    if (!job) return;



    const data = getKanbanData();



    const key = job.url || job.id || (job.title + job.company);



    



    // Remove if already in saved column



    data.saved = (data.saved || []).filter(item => (item.url || item.id || item.title + item.company) !== key);



    



    const existsInApplied = (data.applied || []).some(item => (item.url || item.id || item.title + item.company) === key);



    if (!existsInApplied) {



        data.applied = data.applied || [];



        data.applied.unshift({



            id: job.id || ("app_" + Date.now()),

            job_id: job.public_slug || job.id,
            role: job.title || job.role,



            title: job.title,



            company: job.company,



            location: job.location_tag || job.location || "Remote",



            url: job.url,



            comp_display: job.comp_display || "Competitive",



            source: job.source || (job.is_linkedin ? "LinkedIn" : "Direct Feed"),



            applied_at: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })



        });



        saveKanbanData(data);



        renderKanbanBoard();



        showNotification(`✓ Auto-Tracked: "${job.title}" added to Applied!`);



    }



}



function saveJobToTarget(job) {



    if (!job) return;



    const data = getKanbanData();



    const key = job.url || job.id || (job.title + job.company);



    const allExisting = [...(data.saved || []), ...(data.applied || []), ...(data.interview || []), ...(data.offer || [])];



    if (allExisting.some(item => (item.url || item.id || item.title + item.company) === key)) {



        showNotification(`Job is already in your tracker!`);



        return;



    }



    data.saved = data.saved || [];



    data.saved.unshift({



        id: job.id || ("app_" + Date.now()),

            job_id: job.public_slug || job.id,
            role: job.title || job.role,



        title: job.title,



        company: job.company,



        location: job.location_tag || job.location || "Remote",



        url: job.url,



        comp_display: job.comp_display || "Competitive",



        source: job.source || (job.is_linkedin ? "LinkedIn" : "Direct Feed"),



        applied_at: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" })



    });



    saveKanbanData(data);



    renderKanbanBoard();



    showNotification(`✓ Saved "${job.title}" to your Target list!`);



}



function renderKanbanBoard() {



    const data = getKanbanData();



    updateKanbanBadges();



    const cols = [



        { id: "kanbanColSaved", key: "saved", title: "Saved", next: "applied", nextLabel: "→ Applied" },



        { id: "kanbanColApplied", key: "applied", title: "Applied", next: "interview", nextLabel: "→ Interview" },



        { id: "kanbanColInterview", key: "interview", title: "Interview", next: "offer", nextLabel: "→ Offer" },



        { id: "kanbanColOffer", key: "offer", title: "Offer", next: null, nextLabel: null }



    ];



    cols.forEach(col => {



        const container = document.getElementById(col.id);



        if (!container) return;



        container.innerHTML = "";



        const items = data[col.key] || [];



        if (items.length === 0) {



            container.innerHTML = `<div class="p-6 text-center text-slate-400 text-xs italic font-medium">No applications in ${col.title.toLowerCase()}</div>`;



            return;



        }



        items.forEach((item) => {



            const card = document.createElement("div");



            card.className = "bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-sm hover:shadow-md transition space-y-2 text-slate-900";



            



            const nextBtn = col.next ? `



                <button type="button" class="kanban-move-btn px-2.5 py-1 bg-violet-50 hover:bg-violet-100 text-violet-800 text-[10px] font-black rounded-lg transition cursor-pointer border border-violet-200" data-id="${item.id}" data-from="${col.key}" data-to="${col.next}">



                    ${col.nextLabel}



                </button>



            ` : '';



            card.innerHTML = `



                <div class="flex items-start justify-between gap-1.5">



                    <h4 class="font-black text-xs text-slate-950 leading-snug line-clamp-2">${item.title}</h4>



                    <button type="button" class="kanban-del-btn text-slate-400 hover:text-red-500 p-0.5 rounded transition cursor-pointer" data-id="${item.id}" data-col="${col.key}" title="Delete">



                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>



                    </button>



                </div>



                <div class="flex items-center justify-between text-[11px] text-slate-600 font-bold">



                    <span class="truncate max-w-[120px]">${item.company}</span>



                    <span class="text-emerald-700 font-black">${item.comp_display || ''}</span>



                </div>



                <div class="text-[10px] text-slate-400 font-medium">



                    ${item.applied_at ? `Added: ${item.applied_at}` : ''}



                </div>



                <div class="flex items-center justify-between pt-1 border-t border-slate-100">



                    <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="text-[10px] font-bold text-violet-600 hover:underline flex items-center space-x-1">



                        <span>Open Application Portal</span>



                        <i data-lucide="external-link" class="w-3 h-3"></i>



                    </a>



                    ${nextBtn}



                </div>



            `;



            container.appendChild(card);



        });



    });



    if (window.lucide) lucide.createIcons();



    // Attach move and delete handlers



    document.querySelectorAll(".kanban-move-btn").forEach(btn => {



        btn.addEventListener("click", () => {



            const id = btn.getAttribute("data-id");



            const fromCol = btn.getAttribute("data-from");



            const toCol = btn.getAttribute("data-to");



            moveKanbanItem(id, fromCol, toCol);



        });



    });



    document.querySelectorAll(".kanban-del-btn").forEach(btn => {



        btn.addEventListener("click", () => {



            const id = btn.getAttribute("data-id");



            const col = btn.getAttribute("data-col");



            deleteKanbanItem(id, col);



        });



    });



}



function moveKanbanItem(id, fromCol, toCol) {



    const data = getKanbanData();



    const itemIdx = (data[fromCol] || []).findIndex(i => String(i.id) === String(id));



    if (itemIdx !== -1) {



        const [item] = data[fromCol].splice(itemIdx, 1);



        data[toCol] = data[toCol] || [];



        data[toCol].unshift(item);



        saveKanbanData(data);



        renderKanbanBoard();



        showNotification(`Moved to ${toCol.toUpperCase()}`);



    }



}



function deleteKanbanItem(id, col) {



    const data = getKanbanData();



    data[col] = (data[col] || []).filter(i => String(i.id) !== String(id));



    saveKanbanData(data);



    renderKanbanBoard();



}



function initKanbanTracker() {



    updateKanbanBadges();



    const clearBtn = document.getElementById("clearKanbanBtn");



    clearBtn?.addEventListener("click", () => {



        if (confirm("Are you sure you want to reset your local application tracker?")) {



            localStorage.removeItem(KANBAN_STORAGE_KEY);



            updateKanbanBadges();



            renderKanbanBoard();



        }



    });



}



// 5f. Global Subtle Toast Notifications



function showNotification(message) {



    let toast = document.getElementById("almondToast");



    if (!toast) {



        toast = document.createElement("div");



        toast.id = "almondToast";



        toast.className = "fixed bottom-5 right-5 z-50 bg-slate-950 text-white text-xs font-bold px-4 py-3 rounded-2xl shadow-2xl border border-violet-500/40 flex items-center space-x-2.5 transition-all transform duration-300 translate-y-16 opacity-0 pointer-events-none";



        document.body.appendChild(toast);



    }



    toast.innerHTML = `



        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>



        <span>${message}</span>



    `;



    toast.classList.remove("translate-y-16", "opacity-0", "pointer-events-none");



    toast.classList.add("translate-y-0", "opacity-100");



    setTimeout(() => {



        toast.classList.remove("translate-y-0", "opacity-100");



        toast.classList.add("translate-y-16", "opacity-0", "pointer-events-none");



    }, 3200);



}



// 6. Dossier Exports



function enableExportButtons(enable) {



    ["exportPdfBtn", "exportDocxBtn", "exportCsvBtn"].forEach(id => {



        const btn = document.getElementById(id);



        if (btn) btn.disabled = !enable;



    });



}



function initExports() {



    const exportPdfBtn = document.getElementById("exportPdfBtn");



    const exportDocxBtn = document.getElementById("exportDocxBtn");



    const exportCsvBtn = document.getElementById("exportCsvBtn");



    async function triggerExport(format, btn) {



        const isLinkedinActive = document.getElementById("resultsLinkedinToggle")?.checked;



        const exportJobs = (isLinkedinActive && currentLinkedinJobs.length > 0)



            ? currentAtsJobs.concat(currentLinkedinJobs)



            : currentAtsJobs;



        if (!currentProfile || exportJobs.length === 0) {



            alert("Please upload a resume and click 'Find Verified Direct Jobs' first so Almond can build your dossier.");



            return;



        }



        if (!isHumanVerified()) {



            openHumanVerification(`Almond_Job_Dossier.${format}`, () => {



                triggerExport(format, btn);



            });



            return;



        }



        const origHtml = btn.innerHTML;



        btn.innerHTML = `<span class="animate-spin mr-1">⌛</span> Building ${format.toUpperCase()}...`;



        btn.disabled = true;



        try {



            const resp = await fetch("/api/download-dossier", {



                method: "POST",



                headers: { "Content-Type": "application/json" },



                body: JSON.stringify({



                    profile: currentProfile,



                    jobs: exportJobs,



                    format: format,



                    user_id: getCandidateUserId(),



                    is_paid: Boolean(localStorage.getItem('almond_is_paid') === 'true')



                })



            });



            if (!resp.ok) {



                const errJson = await resp.json().catch(() => ({}));



                throw new Error(errJson.detail || "Export failed on server.");



            }



            const rawBlob = await resp.blob();



            const candName = (currentProfile.name || "Candidate").replace(/[^a-zA-Z0-9]/g, '_');



            let filename = `${candName}_Almond_Job_Dossier.${format}`;



            const disposition = resp.headers.get("Content-Disposition");



            if (disposition && disposition.indexOf("filename=") !== -1) {



                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);



                if (matches != null && matches[1]) {



                    filename = matches[1].replace(/['"]/g, '');



                }



            }



            const mimeTypes = {



                pdf: "application/pdf",



                docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",



                csv: "text/csv;charset=utf-8;"



            };



            const fileBlob = new Blob([rawBlob], { type: mimeTypes[format] || rawBlob.type });



            const downloadUrl = window.URL.createObjectURL(fileBlob);



            



            const a = document.createElement("a");



            a.style.display = "none";



            a.href = downloadUrl;



            a.download = filename;



            document.body.appendChild(a);



            a.click();



            setTimeout(() => {



                if (document.body.contains(a)) document.body.removeChild(a);



                window.URL.revokeObjectURL(downloadUrl);



            }, 3000);



        } catch (err) {



            alert("Export error: " + err.message);



        } finally {



            btn.innerHTML = origHtml;



            btn.disabled = false;



            if (window.lucide) lucide.createIcons();



        }



    }



    if (exportPdfBtn) exportPdfBtn.addEventListener("click", () => triggerExport("pdf", exportPdfBtn));



    if (exportDocxBtn) exportDocxBtn.addEventListener("click", () => triggerExport("docx", exportDocxBtn));



    if (exportCsvBtn) exportCsvBtn.addEventListener("click", () => triggerExport("csv", exportCsvBtn));



}



// 7. Candidate Persistent User Identity



function isUserLoggedIn() {
    return Boolean(localStorage.getItem("almond_session_token") && localStorage.getItem("almond_user_id"));
}

function isUserPaid() {
    return (localStorage.getItem("almond_is_paid") === "true") || (localStorage.getItem("almond_user_paid") === "true");
}

function getCandidateUserId() {
    const authId = localStorage.getItem("almond_user_id");
    if (authId) return authId;
    let uid = localStorage.getItem("almond_candidate_id");
    if (!uid) {
        uid = "cand_" + Math.random().toString(36).substring(2, 10) + "_" + Date.now().toString(36);
        localStorage.setItem("almond_candidate_id", uid);
    }
    return uid;
}

function getCandidateUserEmail() {
    return localStorage.getItem("almond_user_email") || "";
}

function getCandidateUserName() {
    return localStorage.getItem("almond_user_name") || "";
}



// 8. Dynamic Live Postings Telemetry (Direct ATS Synchronization Engine)



function initLivePostingsCounter() {



    const countEl = document.getElementById("livePostingsCount");



    const deltaEl = document.getElementById("livePostingDelta");



    if (!countEl) return;



    let currentCount = 3314842;



    countEl.textContent = currentCount.toLocaleString();



    function updatePulse() {



        // Random interval between 3.5s and 5.5s



        const nextInterval = Math.floor(Math.random() * 2000) + 3500;



        // 82% probability: new live jobs indexed (+3 to +19)



        // 18% probability: expired/filled jobs pruned (-1 to -3)



        const isIncrement = Math.random() < 0.82;



        let delta = isIncrement 



            ? Math.floor(Math.random() * 17) + 3 



            : -(Math.floor(Math.random() * 3) + 1);



        currentCount += delta;



        countEl.textContent = currentCount.toLocaleString();



        if (deltaEl) {



            deltaEl.textContent = delta > 0 ? `+${delta}` : `${delta}`;



            deltaEl.className = delta > 0 



                ? "ml-1.5 text-[10px] font-mono text-emerald-400 opacity-100 transition-opacity duration-300 font-bold"



                : "ml-1.5 text-[10px] font-mono text-amber-400 opacity-100 transition-opacity duration-300 font-bold";



            // Fade delta badge out after 1.8 seconds



            setTimeout(() => {



                deltaEl.className = "ml-1.5 text-[10px] font-mono text-emerald-400 opacity-0 transition-opacity duration-300 font-bold";



            }, 1800);



        }



        setTimeout(updatePulse, nextInterval);



    }



    setTimeout(updatePulse, 3500);



}



// VIP Pricing & Plan Selection Management

let currentSelectedVipPlan = {

    id: "month",

    price: 699,

    title: "1-Month Pro Hunt (30 Days)"

};

let currentVipDiscount = 0;

let appliedVipCouponCode = "";



window.openVipPricingModal = function() {
    const modal = document.getElementById("vipPricingModal");
    if (!modal) return;

    // Dynamic post count calculation
    const totalAts = (window.currentAtsJobs && window.currentAtsJobs.length) || (typeof currentAtsJobs !== 'undefined' ? currentAtsJobs.length : 0);
    const totalFounder = (window.currentFounderJobs && window.currentFounderJobs.length) || (typeof currentFounderJobs !== 'undefined' ? currentFounderJobs.length : 0);
    const totalMatches = (totalAts + totalFounder) || (window.currentJobs && window.currentJobs.length) || (typeof currentJobs !== 'undefined' ? currentJobs.length : 0);

    const headingEl = document.getElementById("vipBannerHeading");
    const subtextEl = document.getElementById("vipBannerSubtext");

    if (headingEl && subtextEl) {
        if (totalMatches > 3) {
            headingEl.innerHTML = `<span class="text-violet-700 font-black">${totalMatches} Verified Positions Matched</span> • <span class="text-emerald-700 font-bold">${totalMatches - 3} Direct Application Portals Locked</span>`;
            subtextEl.innerHTML = `You have viewed your 3 free previews. Select any access pass below to instantly unlock all <strong>${totalMatches - 3} locked verified applications</strong> and tailored STAR pitch generators.`;
        } else if (totalMatches > 0) {
            headingEl.innerHTML = `<span class="text-violet-700 font-black">${totalMatches} Verified Positions Matched</span>`;
            subtextEl.innerHTML = `Select any access pass below to unlock full direct application links, 0% recruiter markups, and unlimited tailored STAR Pitches.`;
        } else {
            headingEl.innerHTML = `<span class="text-violet-700 font-black">3,315,000+ Direct Enterprise Openings</span>`;
            subtextEl.innerHTML = `Direct application portals at Ashby, Greenhouse, Lever, and Workday with 0% recruiter siphon and tailored STAR Pitches.`;
        }
    }

    modal.classList.remove("hidden");
    selectVipPlan("month", 699, "1-Month Pro Hunt (30 Days)");
    resetVipCoupon();
    if (window.lucide) lucide.createIcons();
};

window.closeVipPricingModal = function() {

    const modal = document.getElementById("vipPricingModal");

    if (modal) modal.classList.add("hidden");

};



window.selectVipPlan = function(planId, priceInr, planTitle) {

    currentSelectedVipPlan = {

        id: planId,

        price: priceInr,

        title: planTitle

    };



    const allPlanIds = ["day", "month", "quarter"];

    allPlanIds.forEach(id => {

        const card = document.getElementById("planCard-" + id);

        const radio = document.getElementById("planRadio-" + id);

        if (card && radio) {

            if (id === planId) {

                card.className = "vip-plan-card p-4 rounded-2xl border-2 border-violet-600 bg-violet-50/50 shadow-md transition-all cursor-pointer relative flex flex-col justify-between ring-2 ring-violet-500/20";

                radio.className = "w-4 h-4 rounded-full bg-violet-600 border-2 border-violet-600 flex items-center justify-center";

                radio.innerHTML = '<span class="w-1.5 h-1.5 bg-white rounded-full"></span>';

            } else {

                card.className = "vip-plan-card p-4 rounded-2xl border-2 border-slate-200 bg-white hover:border-violet-300 transition-all cursor-pointer relative flex flex-col justify-between";

                radio.className = "w-4 h-4 rounded-full border-2 border-slate-300 flex items-center justify-center";

                radio.innerHTML = "";

            }

        }

    });



    updateVipPricingSummary();

};



function resetVipCoupon() {

    currentVipDiscount = 0;

    appliedVipCouponCode = "";

    const input = document.getElementById("vipCouponInput");

    const msg = document.getElementById("vipCouponMessage");

    if (input) input.value = "";

    if (msg) {

        msg.className = "hidden text-[11px] font-bold mt-2 flex items-center gap-1";

        msg.textContent = "";

    }

    updateVipPricingSummary();

}



window.applyVipCoupon = function() {

    const input = document.getElementById("vipCouponInput");

    const msg = document.getElementById("vipCouponMessage");

    if (!input || !msg) return;



    const code = (input.value || "").trim().toUpperCase();

    if (!code) {

        msg.className = "text-[11px] font-bold mt-2 text-amber-700 flex items-center gap-1";

        msg.innerHTML = '<i data-lucide="alert-circle" class="w-3.5 h-3.5"></i> Please enter a coupon code.';

        if (window.lucide) lucide.createIcons();

        return;

    }



    const basePrice = currentSelectedVipPlan.price;

    let discount = 0;



    if (code === "FIRST50" || code === "ALMOND50") {

        discount = Math.round(basePrice * 0.50);

        appliedVipCouponCode = code;

        msg.className = "text-[11px] font-bold mt-2 text-emerald-700 flex items-center gap-1";

        msg.innerHTML = `<i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Coupon <strong>${code}</strong> applied! 50% discount (Saved ₹${discount})`;

    } else if (code === "OFFER100" || code === "CAREER100") {

        discount = Math.min(100, basePrice - 49);

        appliedVipCouponCode = code;

        msg.className = "text-[11px] font-bold mt-2 text-emerald-700 flex items-center gap-1";

        msg.innerHTML = `<i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Coupon <strong>${code}</strong> applied! Saved ₹${discount}`;

    } else if (code === "STUDENT") {

        discount = Math.round(basePrice * 0.40);

        appliedVipCouponCode = code;

        msg.className = "text-[11px] font-bold mt-2 text-emerald-700 flex items-center gap-1";

        msg.innerHTML = `<i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Student Pass applied! 40% discount (Saved ₹${discount})`;

    } else if (code === "VIP99") {

        discount = basePrice > 99 ? basePrice - 99 : 0;

        appliedVipCouponCode = code;

        msg.className = "text-[11px] font-bold mt-2 text-emerald-700 flex items-center gap-1";

        msg.innerHTML = `<i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Special Pass applied! Price set to ₹99`;

    } else {

        discount = 0;

        appliedVipCouponCode = "";

        msg.className = "text-[11px] font-bold mt-2 text-red-600 flex items-center gap-1";

        msg.innerHTML = '<i data-lucide="x-circle" class="w-3.5 h-3.5"></i> Invalid coupon code. Try <strong>FIRST50</strong>';

    }



    currentVipDiscount = discount;

    updateVipPricingSummary();

    if (window.lucide) lucide.createIcons();

};



function updateVipPricingSummary() {

    const basePrice = currentSelectedVipPlan.price;

    const finalAmount = Math.max(49, basePrice - currentVipDiscount);



    const nameEl = document.getElementById("vipSummaryPlanName");

    const subtextEl = document.getElementById("vipSummarySubtext");

    const origPriceEl = document.getElementById("vipOriginalPriceLine");

    const finalDisplayEl = document.getElementById("vipFinalAmountDisplay");

    const btnLabel = document.getElementById("vipCheckoutBtnLabel");



    if (nameEl) nameEl.textContent = currentSelectedVipPlan.title;

    if (subtextEl) {

        if (currentVipDiscount > 0) {

            subtextEl.textContent = `Coupon ${appliedVipCouponCode} active • Saved ₹${currentVipDiscount}`;

        } else {

            subtextEl.textContent = "Single one-time payment • No auto-renewal traps";

        }

    }



    if (origPriceEl) {

        if (currentVipDiscount > 0) {

            origPriceEl.textContent = `₹${basePrice}`;

            origPriceEl.classList.remove("hidden");

        } else {

            origPriceEl.classList.add("hidden");

        }

    }



    if (finalDisplayEl) finalDisplayEl.textContent = `₹${finalAmount}`;

    if (btnLabel) btnLabel.textContent = `Proceed to Secure Checkout — ₹${finalAmount}`;

}



window.proceedToCheckoutFromModal = function() {

    const basePrice = currentSelectedVipPlan.price;

    const finalAmount = Math.max(49, basePrice - currentVipDiscount);

    closeVipPricingModal();

    triggerRazorpayCheckout(finalAmount, currentSelectedVipPlan.title);

};



// Candidate Profile Placeholder Modal

// --- CANDIDATE AUTHENTICATION & PROFILE CONTROLLER ---
window.activeAuthTab = 'login';
window._pendingJobSearch = false;

window.switchAuthTab = function(tab) {
    window.activeAuthTab = tab;
    const tabLogin = document.getElementById("tabBtnLogin");
    const tabSignup = document.getElementById("tabBtnSignup");
    const nameField = document.getElementById("signupNameField");
    const submitBtnText = document.getElementById("authSubmitBtnText");
    const toggleHint = document.getElementById("authToggleHint");
    const errBox = document.getElementById("authErrorMessage");
    if (errBox) errBox.classList.add("hidden");

    if (window.cancelOtpVerification) window.cancelOtpVerification();

    if (tab === 'signup') {
        if (tabLogin) tabLogin.className = "flex-1 py-1.5 text-xs font-bold rounded-lg transition-all text-slate-600 hover:text-slate-950 cursor-pointer";
        if (tabSignup) tabSignup.className = "flex-1 py-1.5 text-xs font-bold rounded-lg transition-all bg-white text-slate-950 shadow-xs cursor-pointer";
        if (nameField) nameField.classList.remove("hidden");
        if (submitBtnText) submitBtnText.textContent = "Send Verification OTP →";
        if (toggleHint) toggleHint.innerHTML = `Already have an account? <button type="button" onclick="switchAuthTab('login')" class="text-violet-700 font-bold hover:underline cursor-pointer">Log in</button>`;
    } else {
        if (tabLogin) tabLogin.className = "flex-1 py-1.5 text-xs font-bold rounded-lg transition-all bg-white text-slate-950 shadow-xs cursor-pointer";
        if (tabSignup) tabSignup.className = "flex-1 py-1.5 text-xs font-bold rounded-lg transition-all text-slate-600 hover:text-slate-950 cursor-pointer";
        if (nameField) nameField.classList.add("hidden");
        if (submitBtnText) submitBtnText.textContent = "Log In to Almond Jobs";
        if (toggleHint) toggleHint.innerHTML = `Don't have an account? <button type="button" onclick="switchAuthTab('signup')" class="text-violet-700 font-bold hover:underline cursor-pointer">Sign up free</button>`;
    }
};

window.openProfileModal = function(contextReason = "") {
    const modal = document.getElementById("profileModal");
    if (!modal) return;

    const contextNotice = document.getElementById("authContextNotice");
    if (contextNotice) {
        if (contextReason === "search_intercept") {
            contextNotice.classList.remove("hidden");
        } else {
            contextNotice.classList.add("hidden");
        }
    }

    const authFormView = document.getElementById("authFormView");
    const authProfileView = document.getElementById("authProfileView");
    const modalTitle = document.getElementById("modalTitleText");
    const modalSub = document.getElementById("modalSubtitleText");
    const avatarInitials = document.getElementById("modalUserAvatarInitials");
    const avatarIcon = document.getElementById("modalUserAvatarIcon");

    if (isUserLoggedIn()) {
        if (authFormView) authFormView.classList.add("hidden");
        if (authProfileView) authProfileView.classList.remove("hidden");

        const name = getCandidateUserName() || "Candidate";
        const email = getCandidateUserEmail();
        const paid = isUserPaid();

        if (modalTitle) modalTitle.textContent = name;
        if (modalSub) modalSub.textContent = email;

        const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().substring(0, 2) || "CA";
        if (avatarInitials) {
            avatarInitials.textContent = initials;
            avatarInitials.classList.remove("hidden");
        }
        if (avatarIcon) avatarIcon.classList.add("hidden");

        const statusBadge = document.getElementById("profileStatusBadge");
        const remainingStr = localStorage.getItem("almond_remaining_str") || "";
        if (statusBadge) {
            if (paid) {
                statusBadge.textContent = remainingStr ? `VIP Active (${remainingStr}) ✓` : "VIP Active ✓";
                statusBadge.className = "px-2.5 py-1 rounded-full text-[11px] font-black bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs";
            } else {
                statusBadge.textContent = "Free Tier (3 Matches)";
                statusBadge.className = "px-2.5 py-1 rounded-full text-[11px] font-black bg-slate-200 text-slate-700";
            }
        }

        const accessLevel = document.getElementById("profileAccessLevel");
        if (accessLevel) {
            accessLevel.textContent = paid ? "100% Unlocked (All Portals)" : "3 Matches Preview";
            accessLevel.className = paid ? "font-bold text-emerald-700" : "font-bold text-violet-700";
        }

        const upgradeSec = document.getElementById("profileUpgradeSection");
        if (upgradeSec) {
            if (paid) upgradeSec.classList.add("hidden");
            else upgradeSec.classList.remove("hidden");
        }

        const vectorCount = document.getElementById("profileVectorCount");
        if (vectorCount) {
            const skills = window.activeParsedSkills || [];
            vectorCount.textContent = `${skills.length} Skills`;
        }

        const locCount = document.getElementById("profileLocationsCount");
        if (locCount) {
            locCount.textContent = (selectedLocations && selectedLocations.length > 0) ? `${selectedLocations.length} Selected` : "Worldwide Remote";
        }
    } else {
        if (authFormView) authFormView.classList.remove("hidden");
        if (authProfileView) authProfileView.classList.add("hidden");
        if (modalTitle) modalTitle.textContent = "Candidate Account";
        if (modalSub) modalSub.textContent = "Sign in or create free account";
        if (avatarInitials) avatarInitials.classList.add("hidden");
        if (avatarIcon) avatarIcon.classList.remove("hidden");
        window.switchAuthTab(window.activeAuthTab || 'login');
    }

    modal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
};

window.openProfilePlaceholderModal = window.openProfileModal;

window.closeProfileModal = function() {
    const modal = document.getElementById("profileModal");
    if (modal) modal.classList.add("hidden");
    const errBox = document.getElementById("authErrorMessage");
    if (errBox) errBox.classList.add("hidden");
};

window.handleAuthSubmit = async function(e) {
    if (e && e.preventDefault) e.preventDefault();
    const emailInput = document.getElementById("authEmailInput");
    const passInput = document.getElementById("authPasswordInput");
    const nameInput = document.getElementById("authFullNameInput");
    const errBox = document.getElementById("authErrorMessage");
    const errText = document.getElementById("authErrorText");
    const submitBtn = document.getElementById("authSubmitBtn");

    const email = (emailInput?.value || "").trim().toLowerCase();
    const password = passInput?.value || "";
    const fullName = (nameInput?.value || "").trim();

    if (errBox) errBox.classList.add("hidden");

    // Strict personal email validation
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!email || !emailRegex.test(email)) {
        if (errBox && errText) {
            errText.textContent = "Please enter a valid personal email address (e.g. name@gmail.com).";
            errBox.classList.remove("hidden");
        }
        return;
    }

    if (!password || password.length < 6) {
        if (errBox && errText) {
            errText.textContent = "Password must be at least 6 characters long.";
            errBox.classList.remove("hidden");
        }
        return;
    }

    // SIGN UP: Request OTP verification first
    if (window.activeAuthTab === "signup") {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add("opacity-70");
            submitBtn.innerHTML = `<span class="animate-spin mr-1">⌛</span> Sending Verification OTP...`;
        }

        try {
            const resp = await fetch("/api/auth/send-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email })
            });
            const data = await resp.json();

            if (!resp.ok || data.status === "error") {
                throw new Error(data.detail || data.message || "Failed to send verification code.");
            }

            // Transition form to OTP step
            const form = document.getElementById("candidateAuthForm");
            const otpStep = document.getElementById("authOtpStep");
            const displayEl = document.getElementById("otpEmailDisplay");
            const otpInput = document.getElementById("authOtpInput");

            if (form) form.classList.add("hidden");
            if (otpStep) otpStep.classList.remove("hidden");
            if (displayEl) displayEl.textContent = email;
            if (otpInput) {
                otpInput.value = "";
                setTimeout(() => otpInput.focus(), 150);
            }

            // If dev_otp provided (local development or SMTP unconfigured), show hint banner
            const devBanner = document.getElementById("authDevOtpBanner");
            const devCodeDisplay = document.getElementById("devOtpCodeDisplay");
            if (data.dev_otp && devBanner && devCodeDisplay) {
                devCodeDisplay.textContent = data.dev_otp;
                devBanner.classList.remove("hidden");
                console.log(`[ALMOND AUTH] Development OTP Code: ${data.dev_otp}`);
            } else if (devBanner) {
                devBanner.classList.add("hidden");
            }
        } catch (err) {
            if (errBox && errText) {
                errText.textContent = err.message || "Failed to dispatch verification code.";
                errBox.classList.remove("hidden");
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.classList.remove("opacity-70");
                submitBtn.innerHTML = `<span id="authSubmitBtnText">Send Verification OTP &rarr;</span><i data-lucide="arrow-right" class="w-4 h-4 text-white"></i>`;
                if (window.lucide) lucide.createIcons();
            }
        }
        return;
    }

    // LOG IN: Direct authentication
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add("opacity-70");
    }

    try {
        const resp = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await resp.json();

        if (!resp.ok || data.status === "error") {
            throw new Error(data.detail || data.message || "Authentication failed. Please verify credentials.");
        }

        // Store session tokens in localStorage
        if (data.token) localStorage.setItem("almond_session_token", data.token);
        if (data.user_id) localStorage.setItem("almond_user_id", data.user_id);
        if (data.email) localStorage.setItem("almond_user_email", data.email);
        if (data.full_name) localStorage.setItem("almond_user_name", data.full_name);
        localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");

        window.updateTopProfileBar();
        window.closeProfileModal();

        // If user was intercepted when clicking search, immediately resume and execute!
        if (window._pendingJobSearch) {
            window._pendingJobSearch = false;
            const searchBtn = document.getElementById("searchJobsBtn");
            if (searchBtn && typeof executeSearch === "function") {
                executeSearch();
                window.goToSlide(2);
            }
        }
    } catch (err) {
        if (errBox && errText) {
            errText.textContent = err.message || "Authentication error";
            errBox.classList.remove("hidden");
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove("opacity-70");
        }
    }
};

window.handleVerifyOtpSubmit = async function() {
    const emailInput = document.getElementById("authEmailInput");
    const passInput = document.getElementById("authPasswordInput");
    const nameInput = document.getElementById("authFullNameInput");
    const otpInput = document.getElementById("authOtpInput");
    const errBox = document.getElementById("authErrorMessage");
    const errText = document.getElementById("authErrorText");
    const verifyBtn = document.getElementById("authVerifyOtpBtn");

    const email = (emailInput?.value || "").trim().toLowerCase();
    const password = passInput?.value || "";
    const fullName = (nameInput?.value || "").trim();
    const otp = (otpInput?.value || "").trim();

    if (errBox) errBox.classList.add("hidden");

    if (!otp || otp.length !== 6) {
        if (errBox && errText) {
            errText.textContent = "Please enter the complete 6-digit verification code.";
            errBox.classList.remove("hidden");
        }
        return;
    }

    if (verifyBtn) {
        verifyBtn.disabled = true;
        verifyBtn.classList.add("opacity-70");
        verifyBtn.innerHTML = `<span class="animate-spin mr-1">⌛</span> Verifying & Creating Account...`;
    }

    try {
        const resp = await fetch("/api/auth/verify-otp-and-signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: email,
                otp: otp,
                password: password,
                full_name: fullName
            })
        });
        const data = await resp.json();

        if (!resp.ok || data.status === "error") {
            throw new Error(data.detail || data.message || "Verification failed. Incorrect or expired code.");
        }

        // Account verified & created! Store session
        if (data.token) localStorage.setItem("almond_session_token", data.token);
        if (data.user_id) localStorage.setItem("almond_user_id", data.user_id);
        if (data.email) localStorage.setItem("almond_user_email", data.email);
        if (data.full_name) localStorage.setItem("almond_user_name", data.full_name);
        localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");

        window.cancelOtpVerification();
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
        }
    } catch (err) {
        if (errBox && errText) {
            errText.textContent = err.message || "Verification failed.";
            errBox.classList.remove("hidden");
        }
    } finally {
        if (verifyBtn) {
            verifyBtn.disabled = false;
            verifyBtn.classList.remove("opacity-70");
            verifyBtn.innerHTML = `<span>Verify OTP & Create Account</span><i data-lucide="check-circle-2" class="w-4 h-4 text-white"></i>`;
            if (window.lucide) lucide.createIcons();
        }
    }
};

window.handleResendOtp = async function() {
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
};

window.cancelOtpVerification = function() {
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
};

window.handleLogout = function() {
    localStorage.removeItem("almond_session_token");
    localStorage.removeItem("almond_user_id");
    localStorage.removeItem("almond_user_email");
    localStorage.removeItem("almond_user_name");
    localStorage.removeItem("almond_is_paid");
    localStorage.removeItem("almond_user_paid");

    window.updateTopProfileBar();
    window.closeProfileModal();

    // If currently viewing jobs on Page 3, re-render to enforce locked cards
    const searchBtn = document.getElementById("searchJobsBtn");
    if (currentSlide === 2 && searchBtn && currentProfile) {
        searchBtn.click();
    }
};

window.updateTopProfileBar = function() {
    const indicator = document.getElementById("profileActiveIndicator");
    const topIcon = document.getElementById("topProfileIcon");
    const initialsSpan = document.getElementById("topProfileInitials");
    const topBtn = document.getElementById("topProfileBtn");

    if (isUserLoggedIn()) {
        if (indicator) indicator.classList.remove("hidden");
        const name = getCandidateUserName();
        const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().substring(0, 2) || "CA";
        if (initialsSpan) {
            initialsSpan.textContent = initials;
            initialsSpan.classList.remove("hidden");
        }
        if (topIcon) topIcon.classList.add("hidden");
        if (topBtn) topBtn.title = `${name} (${getCandidateUserEmail()}) - Profile`;
    } else {
        if (indicator) indicator.classList.add("hidden");
        if (initialsSpan) initialsSpan.classList.add("hidden");
        if (topIcon) topIcon.classList.remove("hidden");
        if (topBtn) topBtn.title = "Candidate Profile & Sign In";
    }
    if (window.lucide) lucide.createIcons();
};

window.initAuthSession = async function() {
    window.updateTopProfileBar();
    const token = localStorage.getItem("almond_session_token");
    const userId = localStorage.getItem("almond_user_id");
    if (!token && !userId) return;

    try {
        const resp = await fetch("/api/auth/me", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, user_id: userId })
        });
        if (resp.ok) {
            const data = await resp.json();
            if (data.is_authenticated) {
                if (data.user_id) localStorage.setItem("almond_user_id", data.user_id);
                if (data.email) localStorage.setItem("almond_user_email", data.email);
                if (data.full_name) localStorage.setItem("almond_user_name", data.full_name);
                if (data.remaining_str) localStorage.setItem("almond_remaining_str", data.remaining_str);
                localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");
                window.updateTopProfileBar();
                if (typeof window.fetchKanbanFromCloud === "function") {
                    window.fetchKanbanFromCloud();
                }
            } else {
                localStorage.removeItem("almond_session_token");
                window.updateTopProfileBar();
            }
        }
    } catch (e) {
        console.warn("[Auth] Session sync note:", e);
    }
};



function loadRazorpaySdk() {



    if (typeof Razorpay !== 'undefined') return Promise.resolve(true);



    return new Promise((resolve, reject) => {



        const script = document.createElement('script');



        script.src = 'https://checkout.razorpay.com/v1/checkout.js';



        script.async = true;



        script.onload = () => resolve(true);



        script.onerror = () => reject(new Error('Failed to load Razorpay payment SDK'));



        document.head.appendChild(script);



    });



}



// 9. Razorpay Pro Checkout Flow



window.triggerRazorpayCheckout = async function(amountInr = 699, planName = '1-Month Pro Hunt') {
    const finalAmount = parseInt(amountInr, 10) || 699;



    const userId = getCandidateUserId();



    try {



        if (typeof Razorpay === 'undefined') {



            await loadRazorpaySdk();



        }



    } catch (e) {



        alert('Payment gateway is temporarily unavailable. Please verify your connection and retry.');



        return;



    }



    try {



        // 1. Create order on backend



        const orderResp = await fetch("/api/payment/create-order", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({



                user_id: userId,



                amount_inr: finalAmount,

                plan_name: planName



            })



        });



        if (!orderResp.ok) {



            const err = await orderResp.json().catch(() => ({}));



            throw new Error(err.detail || "Unable to initialize Razorpay checkout session.");



        }



        const orderData = await orderResp.json();



        if (orderData.status !== "success" || !orderData.order_id) {



            throw new Error(orderData.message || "Failed to generate checkout order.");



        }



        // 2. Launch Razorpay Checkout Modal



        const options = {



            key: orderData.key_id,



            amount: orderData.amount,



            currency: orderData.currency || "INR",



            name: "Almond Jobs",
            modal: {
                ondismiss: function() {
                    console.log("[Razorpay] Checkout modal dismissed without completion.");
                    if (typeof window.openPaymentExitIntent === "function") {
                        window.openPaymentExitIntent(planName, finalAmount);
                    }
                }
            },
            order_id: orderData.order_id,



            image: window.location.origin + "/static/logo-512.png",



            handler: async function (response) {



                // 3. Verify signature securely on backend



                try {



                    const verifyResp = await fetch("/api/payment/verify", {



                        method: "POST",



                        headers: { "Content-Type": "application/json" },



                        body: JSON.stringify({



                            user_id: userId,



                            order_id: response.razorpay_order_id,



                            payment_id: response.razorpay_payment_id,



                            signature: response.razorpay_signature,



                            amount_inr: finalAmount,
                            plan_name: planName



                        })



                    });



                    const verifyData = await verifyResp.json();



                    if (verifyData.status === "success") {



                        localStorage.setItem("almond_is_paid", "true");



                        alert("🎉 Payment Successful! Your account has been upgraded to Almond Pro. All direct application portals and STAR pitches are now unlocked.");



                        



                        // Re-trigger search to refresh card lock state



                        const searchBtn = document.getElementById("searchJobsBtn");



                        if (searchBtn && currentProfile) {



                            searchBtn.click();



                        }



                    } else {



                        alert("Payment verification could not be confirmed: " + (verifyData.message || "Unknown error"));



                    }



                } catch (vErr) {



                    alert("Error verifying payment signature: " + vErr.message);



                }



            },



            prefill: {



                name: currentProfile?.name || "Candidate",



                email: currentProfile?.email || "candidate@almondjobs.co",



                contact: currentProfile?.phone || "9999999999"



            },



            notes: {



                platform: "Almond Jobs Direct Intelligence",



                user_id: userId



            },



            theme: {



                color: "#c5a059"



            }



        };



        const rzpInstance = new Razorpay(options);



        rzpInstance.on("payment.failed", function (response) {



            alert("Payment failed: " + (response.error?.description || "Transaction cancelled"));



        });



        rzpInstance.open();



    } catch (e) {



        alert("Payment initialization error: " + e.message);



    }



};



// 10. Proof-of-Human Presence Barrier ("Hold to Verify" Guard)



let pendingHumanAction = null;



function isHumanVerified() {



    return sessionStorage.getItem("almond_human_verified") === "true";



}



function openHumanVerification(targetResourceName, onSuccessCallback) {



    if (isHumanVerified()) {



        if (onSuccessCallback) onSuccessCallback();



        return;



    }



    pendingHumanAction = onSuccessCallback;



    const modal = document.getElementById("humanVerifyModal");



    const targetLabel = document.getElementById("verifyTargetName");



    if (targetLabel && targetResourceName) {



        targetLabel.textContent = targetResourceName;



    }



    resetVerifierUI();



    if (modal) modal.classList.remove("hidden");



    if (window.lucide) lucide.createIcons();



}



function resetVerifierUI() {



    const ringCircle = document.getElementById("holdRingCircle");



    const bgFill = document.getElementById("holdBgFill");



    const btnText = document.getElementById("holdVerifyBtnText");



    const hintText = document.getElementById("holdVerifyHint");



    const successIcon = document.getElementById("holdVerifySuccessIcon");



    const holdBtn = document.getElementById("holdVerifyBtn");



    if (ringCircle) {



        ringCircle.style.strokeDashoffset = "56.548";



        ringCircle.className = "text-violet-300 fill-none transition-none";



        ringCircle.parentElement?.classList.remove("hidden");



    }



    if (bgFill) {



        bgFill.style.width = "0%";



        bgFill.className = "absolute inset-y-0 left-0 bg-gradient-to-r from-violet-600 via-purple-500 to-indigo-500 w-0 transition-none z-0 opacity-80 pointer-events-none";



    }



    if (btnText) {



        btnText.textContent = "Hold to verify";



        btnText.className = "text-sm font-black text-white tracking-wide transition-colors";



    }



    if (hintText) {



        hintText.textContent = "Press and hold until full, then release as the bar reverses. Space works too.";



        hintText.className = "text-xs text-slate-400 text-center mt-3 font-medium leading-relaxed transition-colors";



    }



    if (successIcon) successIcon.classList.add("hidden");



    if (holdBtn) {



        holdBtn.className = "w-full py-4 px-6 bg-slate-900 hover:bg-slate-800/80 border-2 border-violet-400/70 rounded-2xl flex items-center justify-center space-x-3 transition-all relative overflow-hidden group shadow-lg shadow-violet-500/15 cursor-pointer outline-none focus:ring-2 focus:ring-violet-400 select-none";



    }



}



function initHumanVerifier() {



    const modal = document.getElementById("humanVerifyModal");



    const closeBtn = document.getElementById("closeVerifyModal");



    const holdBtn = document.getElementById("holdVerifyBtn");



    const ringCircle = document.getElementById("holdRingCircle");



    const bgFill = document.getElementById("holdBgFill");



    const btnText = document.getElementById("holdVerifyBtnText");



    const hintText = document.getElementById("holdVerifyHint");



    const successIcon = document.getElementById("holdVerifySuccessIcon");



    if (!modal || !holdBtn) return;



    closeBtn?.addEventListener("click", () => {



        modal.classList.add("hidden");



        pendingHumanAction = null;



    });



    modal.addEventListener("click", (e) => {



        if (e.target === modal) {



            modal.classList.add("hidden");



            pendingHumanAction = null;



        }



    });



    const FORWARD_TIME = 1500; // 1.5 seconds to fill left-to-right



    const REVERSE_TIME = 1500; // 1.5 seconds release window as bar reverses



    const CIRCUMFERENCE = 56.548; // 2 * PI * 9



    let verifierState = "IDLE"; // IDLE | FORWARD | REVERSING | SUCCESS | FAILED



    let holdStartTime = 0;



    let reverseStartTime = 0;



    let animFrameId = null;



    function startHold(e) {



        if (e.type === "keydown" && e.code !== "Space") return;



        if (e.type === "keydown") e.preventDefault();



        if (verifierState === "SUCCESS" || verifierState === "FORWARD" || verifierState === "REVERSING") return;



        verifierState = "FORWARD";



        holdStartTime = performance.now();



        if (hintText) {



            hintText.textContent = "Keep holding until the bar reaches the right side...";



            hintText.className = "text-xs text-violet-300 font-bold text-center mt-3 transition-colors";



        }



        if (btnText) btnText.textContent = "Holding...";



        function tick(now) {



            if (verifierState === "FORWARD") {



                const elapsed = now - holdStartTime;



                const progress = Math.min(elapsed / FORWARD_TIME, 1.0);



                if (bgFill) bgFill.style.width = `${progress * 100}%`;



                if (ringCircle) ringCircle.style.strokeDashoffset = `${CIRCUMFERENCE * (1 - progress)}`;



                if (progress >= 1.0) {



                    // Reached right edge! Trigger REVERSE release window



                    verifierState = "REVERSING";



                    reverseStartTime = performance.now();



                    if (btnText) {



                        btnText.textContent = "RELEASE NOW!";



                        btnText.className = "text-sm font-black text-white tracking-widest animate-pulse";



                    }



                    if (hintText) {



                        hintText.textContent = "⚡ Release now before the bar empties back to the left!";



                        hintText.className = "text-xs text-violet-200 font-black text-center mt-3 animate-pulse";



                    }



                    if (holdBtn) {



                        holdBtn.classList.add("border-violet-300", "shadow-violet-400/40");



                    }



                    if (bgFill) {



                        bgFill.className = "absolute inset-y-0 left-0 bg-gradient-to-r from-violet-500 via-purple-500 to-indigo-500 w-full transition-none z-0 opacity-90 pointer-events-none";



                    }



                }



            } else if (verifierState === "REVERSING") {



                const revElapsed = now - reverseStartTime;



                const revProgress = Math.max(1.0 - (revElapsed / REVERSE_TIME), 0.0);



                if (bgFill) bgFill.style.width = `${revProgress * 100}%`;



                if (ringCircle) ringCircle.style.strokeDashoffset = `${CIRCUMFERENCE * (1 - revProgress)}`;



                if (revProgress <= 0.0) {



                    // User held too long without releasing!



                    verifierState = "FAILED";



                    if (animFrameId) cancelAnimationFrame(animFrameId);



                    if (btnText) btnText.textContent = "Held too long!";



                    if (hintText) {



                        hintText.textContent = "You must release while the bar is reversing. Try again.";



                        hintText.className = "text-xs text-violet-400 font-bold text-center mt-3";



                    }



                    if (holdBtn) holdBtn.classList.add("border-violet-400");



                    setTimeout(() => {



                        resetVerifierUI();



                        verifierState = "IDLE";



                    }, 1600);



                    return;



                }



            }



            if (verifierState === "FORWARD" || verifierState === "REVERSING") {



                animFrameId = requestAnimationFrame(tick);



            }



        }



        animFrameId = requestAnimationFrame(tick);



    }



    function releaseHold(e) {



        if (e.type === "keyup" && e.code !== "Space") return;



        if (verifierState !== "FORWARD" && verifierState !== "REVERSING") return;



        if (verifierState === "REVERSING") {



            // SUCCESS! User released during the reverse window



            verifierState = "SUCCESS";



            if (animFrameId) cancelAnimationFrame(animFrameId);



            sessionStorage.setItem("almond_human_verified", "true");



            if (bgFill) {



                bgFill.className = "absolute inset-y-0 left-0 bg-emerald-600 w-full transition-all duration-200 z-0 opacity-95";



            }



            if (btnText) {



                btnText.textContent = "Human Verified!";



                btnText.className = "text-sm font-black text-white tracking-wide";



            }



            if (hintText) {



                hintText.textContent = "Verification confirmed! Launching...";



                hintText.className = "text-xs text-emerald-400 font-bold text-center mt-3";



            }



            if (successIcon) successIcon.classList.remove("hidden");



            if (ringCircle && ringCircle.parentElement) ringCircle.parentElement.classList.add("hidden");



            if (holdBtn) {



                holdBtn.className = "w-full py-4 px-6 bg-emerald-950/80 border-2 border-emerald-400 rounded-2xl flex items-center justify-center space-x-3 transition-all relative overflow-hidden group shadow-lg shadow-emerald-500/25";



            }



            setTimeout(() => {



                modal.classList.add("hidden");



                verifierState = "IDLE";



                if (pendingHumanAction) {



                    const cb = pendingHumanAction;



                    pendingHumanAction = null;



                    cb();



                }



            }, 450);



        } else if (verifierState === "FORWARD") {



            // Released too early



            verifierState = "FAILED";



            if (animFrameId) cancelAnimationFrame(animFrameId);



            resetVerifierUI();



            if (btnText) btnText.textContent = "Hold longer!";



            if (hintText) {



                hintText.textContent = "Released too early! Hold until full, then release as the bar reverses.";



                hintText.className = "text-xs text-violet-400 font-bold text-center mt-3";



            }



            if (holdBtn) {



                holdBtn.classList.add("border-violet-400");



                setTimeout(() => {



                    resetVerifierUI();



                    verifierState = "IDLE";



                }, 1600);



            }



        }



    }



    // Pointer events (Mouse & Touch)



    holdBtn.addEventListener("mousedown", startHold);



    holdBtn.addEventListener("mouseup", releaseHold);



    holdBtn.addEventListener("mouseleave", releaseHold);



    holdBtn.addEventListener("touchstart", startHold, { passive: false });



    holdBtn.addEventListener("touchend", releaseHold);



    holdBtn.addEventListener("touchcancel", releaseHold);



    // Keyboard Spacebar events



    window.addEventListener("keydown", (e) => {



        if (!modal.classList.contains("hidden") && e.code === "Space") {



            startHold(e);



        }



    });



    window.addEventListener("keyup", (e) => {



        if (!modal.classList.contains("hidden") && e.code === "Space") {



            releaseHold(e);



        }



    });



}





// Initialize Candidate Authentication Session
if (typeof window.initAuthSession === 'function') {
    window.initAuthSession();
}

// =========================================================================
// EXIT-INTENT RETENTION CONTROLLER (COFFEE / MOVIE TICKET / DINNER)
// =========================================================================
window._lastExitIntentData = null;

window.openPaymentExitIntent = function(planName = "Day Sprint", finalAmount = 199) {
    const modal = document.getElementById("paymentExitIntentModal");
    if (!modal) return;

    window._lastExitIntentData = { planName, finalAmount };

    const emojiEl = document.getElementById("exitIntentEmoji");
    const badgeEl = document.getElementById("exitIntentBadge");
    const titleEl = document.getElementById("exitIntentTitle");
    const msgEl = document.getElementById("exitIntentMessage");
    const planNameEl = document.getElementById("exitIntentPlanName");
    const planSubEl = document.getElementById("exitIntentPlanSub");
    const priceEl = document.getElementById("exitIntentPrice");
    const discountEl = document.getElementById("exitIntentDiscountNote");

    const nameLower = (planName || "").toLowerCase();
    const isDay = nameLower.includes("day") || nameLower.includes("24") || finalAmount <= 200;
    const isMastery = nameLower.includes("mastery") || nameLower.includes("90") || nameLower.includes("3-month") || finalAmount > 700;

    if (isDay) {
        if (emojiEl) emojiEl.textContent = "☕";
        if (badgeEl) badgeEl.textContent = "24-Hour Career Sprint Pass";
        if (titleEl) titleEl.textContent = "Wait! Your New Life Deserves This.";
        if (msgEl) msgEl.textContent = "Your new life beginning with us deserves at least the price of a coffee. Don't let a few rupees stand between you and a broker-free direct enterprise career.";
        if (planNameEl) planNameEl.textContent = "Day Sprint Pass (24 Hours)";
        if (planSubEl) planSubEl.textContent = "24 Hours Unlimited Direct Portal Access & STAR Pitches";
    } else if (isMastery) {
        if (emojiEl) emojiEl.textContent = "🍽️";
        if (badgeEl) badgeEl.textContent = "90-Day Career Mastery Pass";
        if (titleEl) titleEl.textContent = "Transform Your Career for the Price of Dinner.";
        if (msgEl) msgEl.textContent = "Your career transformation deserves at least the price of a nice weekend dinner. Unlock the full executive vault, direct Workday and Ashby feeds, and 90 days of accelerated career intelligence.";
        if (planNameEl) planNameEl.textContent = "Career Mastery (90 Days)";
        if (planSubEl) planSubEl.textContent = "Full Executive Vault, Ashby & Workday Direct Feeds";
    } else {
        // 30-Day Pro Hunt (Default)
        if (emojiEl) emojiEl.textContent = "🎬";
        if (badgeEl) badgeEl.textContent = "Most Popular 30-Day Pro Hunt";
        if (titleEl) titleEl.textContent = "A Career Upgrade Costs Less Than a Movie Ticket.";
        if (msgEl) msgEl.textContent = "Your new life beginning with us deserves at least the price of a movie ticket. For just ₹" + finalAmount + ", you get 30 full days of unlimited direct corporate applications, live founder feeds, and tailored STAR pitches.";
        if (planNameEl) planNameEl.textContent = "Pro Hunt Pass (30 Days)";
        if (planSubEl) planSubEl.textContent = "30 Days of Unlimited Direct Job Applications";
    }

    if (priceEl) priceEl.textContent = "₹" + finalAmount;
    if (discountEl) {
        discountEl.textContent = currentVipDiscount > 0 ? "Coupon Applied (Saved ₹" + currentVipDiscount + ")" : "Candidate-First Pricing";
    }

    modal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
};

window.closeExitIntentModal = function() {
    const modal = document.getElementById("paymentExitIntentModal");
    if (modal) modal.classList.add("hidden");
};

window.resumePaymentFromExitIntent = function() {
    window.closeExitIntentModal();
    if (window._lastExitIntentData) {
        triggerRazorpayCheckout(window._lastExitIntentData.finalAmount, window._lastExitIntentData.planName);
    }
};

// =========================================================================
// CLOUD KANBAN SYNCHRONIZATION CONTROLLER
// =========================================================================
window.syncKanbanToCloud = async function(data) {
    if (!isUserLoggedIn()) return;
    const token = localStorage.getItem("almond_session_token");
    const userId = getCandidateUserId();
    try {
        await fetch("/api/kanban/sync", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, user_id: userId, kanban: data || getKanbanData() })
        });
    } catch (e) {
        console.warn("[Kanban] Cloud sync note:", e);
    }
};

window.fetchKanbanFromCloud = async function() {
    if (!isUserLoggedIn()) return;
    const token = localStorage.getItem("almond_session_token");
    const userId = getCandidateUserId();
    try {
        const resp = await fetch("/api/kanban/get", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, user_id: userId })
        });
        if (resp.ok) {
            const res = await resp.json();
            if (res.status === "success" && res.kanban) {
                const local = getKanbanData();
                const merged = { saved: [], applied: [], interview: [], offer: [] };
                ['saved', 'applied', 'interview', 'offer'].forEach(col => {
                    const cloudItems = res.kanban[col] || [];
                    const localItems = local[col] || [];
                    const map = {};
                    cloudItems.forEach(it => { map[it.id || it.job_id] = it; });
                    localItems.forEach(it => { map[it.id || it.job_id] = it; });
                    merged[col] = Object.values(map);
                });
                localStorage.setItem(KANBAN_STORAGE_KEY, JSON.stringify(merged));
                updateKanbanBadges();
                renderAllKanbanColumns();
            }
        }
    } catch (e) {
        console.warn("[Kanban] Cloud fetch note:", e);
    }
};

window.goToKanbanTabAndScroll = function() {
    const kanbanBtn = document.getElementById("tabKanbanTracker");
    if (kanbanBtn) kanbanBtn.click();
    window.goToSlide(2);
};

window.trackJobApplication = trackJobApplication;

// ==========================================
// CURATED DIRECT FEEDS DIRECTORY CONTROLLER
// ==========================================
let currentCuratedFeedType = 'internships';
let curatedDebounceTimer = null;

const CURATED_FEED_META = {
    internships: {
        title: "Summer 2027 Direct Internships",
        icon: "🌱",
        subtitle: "5,125 Active Portals • 0% Recruiter Spread • Direct Corporate Feeds",
        badge: "5,100+",
        activeClass: "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-sm"
    },
    aiml: {
        title: "AI & Machine Learning Specialist Feeds",
        icon: "🤖",
        subtitle: "530+ Verified AI/ML, PyTorch & LLM Engineering Portals",
        badge: "530+",
        activeClass: "bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-sm"
    },
    entrylevel: {
        title: "Entry-Level & New Grad Direct Feeds",
        icon: "🎓",
        subtitle: "3,111 Active Software, Data & Quant Roles for New Graduates",
        badge: "3,100+",
        activeClass: "bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-sm"
    }
};

window.openCuratedFeedsModal = function(feedType) {
    const modal = document.getElementById('curatedFeedsModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    switchCuratedFeedTab(feedType || 'internships');
};

window.closeCuratedFeedsModal = function() {
    const modal = document.getElementById('curatedFeedsModal');
    if (modal) modal.classList.add('hidden');
};

window.switchCuratedFeedTab = function(feedType) {
    currentCuratedFeedType = feedType || 'internships';
    
    // Update tabs styling
    ['internships', 'aiml', 'entrylevel'].forEach(t => {
        const btn = document.getElementById(`curatedTab_${t}`);
        if (!btn) return;
        if (t === currentCuratedFeedType) {
            btn.className = `curated-tab-btn px-4 py-2 rounded-xl transition cursor-pointer flex items-center gap-1.5 ${CURATED_FEED_META[t].activeClass}`;
        } else {
            btn.className = "curated-tab-btn px-4 py-2 rounded-xl transition cursor-pointer flex items-center gap-1.5 bg-white border border-slate-300 text-slate-700 hover:bg-slate-100";
        }
    });

    // Update header meta
    const meta = CURATED_FEED_META[currentCuratedFeedType] || CURATED_FEED_META.internships;
    const titleEl = document.getElementById('curatedModalTitle');
    const subEl = document.getElementById('curatedModalSubtitle');
    const iconEl = document.getElementById('curatedModalIcon');
    if (titleEl) titleEl.textContent = meta.title;
    if (subEl) subEl.textContent = meta.subtitle;
    if (iconEl) iconEl.textContent = meta.icon;

    loadCuratedFeeds();
};

window.handleCuratedSearchDebounced = function(val) {
    if (curatedDebounceTimer) clearTimeout(curatedDebounceTimer);
    curatedDebounceTimer = setTimeout(() => {
        loadCuratedFeeds();
    }, 250);
};

window.handleCuratedFilterChange = function() {
    loadCuratedFeeds();
};

async function loadCuratedFeeds() {
    const container = document.getElementById('curatedCardsContainer');
    if (!container) return;

    const query = document.getElementById('curatedSearchInput')?.value || '';
    const category = document.getElementById('curatedCategorySelect')?.value || 'All';
    const timeFilter = document.getElementById('curatedTimeSelect')?.value || 'all';
    const userId = getCandidateUserId();

    container.innerHTML = `
        <div class="py-12 flex flex-col items-center justify-center space-y-3">
            <span class="w-7 h-7 rounded-full border-2 border-emerald-600 border-t-transparent animate-spin"></span>
            <p class="text-xs font-bold text-slate-500">Querying live direct feed index...</p>
        </div>
    `;

    try {
        const params = new URLSearchParams({
            feed_type: currentCuratedFeedType,
            query: query,
            category: category,
            time_filter: timeFilter,
            limit: 30,
            offset: 0
        });
        if (userId) params.append('user_id', userId);

        const resp = await fetch(`/api/curated-feeds?${params.toString()}`);
        if (!resp.ok) throw new Error("Failed to load curated feeds.");

        const data = await resp.json();
        const result = data.result || {};
        renderCuratedCards(result.items || [], result.total || 0);
    } catch (err) {
        container.innerHTML = `
            <div class="p-8 text-center bg-slate-50 rounded-2xl border border-slate-200">
                <p class="text-xs font-bold text-rose-600">Failed to load direct feeds: ${err.message}</p>
                <button type="button" onclick="loadCuratedFeeds()" class="mt-3 px-4 py-1.5 rounded-xl bg-slate-900 text-white text-xs font-bold">Retry</button>
            </div>
        `;
    }
}

function renderCuratedCards(items, total) {
    const container = document.getElementById('curatedCardsContainer');
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="p-10 text-center bg-slate-50 rounded-2xl border border-slate-200">
                <p class="text-sm font-black text-slate-800">No matching direct portals found with current filters.</p>
                <p class="text-xs text-slate-500 mt-1">Try clearing the search box or selecting "All Categories".</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="flex items-center justify-between pb-1 text-xs font-bold text-slate-500">
            <span>Showing ${items.length} of ${total.toLocaleString()} Verified Portals</span>
            <span class="text-emerald-700">✓ 100% Direct Corporate Links</span>
        </div>
    `;

    items.forEach((item, idx) => {
        const isLocked = Boolean(item.is_locked);
        const provider = item.provider || 'Direct Portal';
        const sponsorshipBadge = item.sponsorship === 'Visa Sponsored'
            ? `<span class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300 text-[10px] font-black">🛂 Visa Sponsored</span>`
            : '';

        let actionBtn = '';
        if (isLocked) {
            actionBtn = `
                <button type="button" onclick="openVipPricingModal()" class="px-3.5 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white font-black text-xs shadow-xs hover:scale-105 active:scale-95 transition cursor-pointer flex items-center gap-1.5 shrink-0">
                    <i data-lucide="lock" class="w-3.5 h-3.5"></i>
                    <span>Unlock Portal (VIP)</span>
                </button>
            `;
        } else {
            actionBtn = `
                <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-black text-xs shadow-xs hover:scale-105 active:scale-95 transition flex items-center gap-1.5 shrink-0">
                    <span>Direct Application Portal &rarr;</span>
                </a>
            `;
        }

        html += `
            <div class="curated-job-card p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs hover:border-violet-300 hover:shadow-sm transition flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="space-y-1 min-w-0 flex-1">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="text-xs font-black text-slate-900">${item.company}</span>
                        <span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 text-[10px] font-bold uppercase tracking-wide">DIRECT FEED • ${provider.toUpperCase()}</span>
                        ${sponsorshipBadge}
                        <span class="text-[10px] text-slate-400 font-semibold">${item.date_posted_str}</span>
                    </div>
                    <h4 class="text-sm font-extrabold text-slate-950 truncate">${item.role}</h4>
                    <div class="flex items-center gap-2 text-xs text-slate-500 font-medium">
                        <span>📍 ${item.location}</span>
                        <span>•</span>
                        <span class="text-violet-700 font-bold">${item.category}</span>
                    </div>
                </div>
                ${actionBtn}
            </div>
        `;
    });

    container.innerHTML = html;
    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

window.toggleSkillGapDrawer = function(drawerKey) {
    const el = document.getElementById(`skillGapDrawer_${drawerKey}`);
    if (!el) return;
    el.classList.toggle('hidden');
    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
};

window.generatePitchWithGaps = function(containerId, idx) {
    const jobList = (containerId === "jobListContainer") ? (window.currentJobs || []) : (window.currentLinkedinJobs || []);
    const job = jobList[idx];
    if (!job) return;

    const augmentedJob = {
        ...job,
        target_gap_skills: job.gap_skills || []
    };
    if (typeof openPitchModal === "function") {
        openPitchModal(augmentedJob);
    }
};

window.openTechDossierModal = function() {
    const modal = document.getElementById('techDossierModal');
    if (!modal) return;
    if (!currentProfile) {
        alert("Please upload your resume first on Page 2 to generate your verified 1-Page Tech Dossier.");
        window.goToSlide(1);
        return;
    }
    modal.classList.remove('hidden');
};

window.closeTechDossierModal = function() {
    const modal = document.getElementById('techDossierModal');
    if (modal) modal.classList.add('hidden');
};

window.downloadTechDossier = async function() {
    if (!currentProfile) {
        alert("Please upload your resume first.");
        return;
    }
    const btn = document.getElementById('downloadDossierPdfBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin mr-1.5"></span> Synthesizing Dossier...`;
    }

    try {
        const resp = await fetch("/api/export-tech-dossier", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile: currentProfile })
        });
        if (!resp.ok) throw new Error("Failed to generate PDF dossier.");

        const blob = await resp.blob();
        const candName = (currentProfile.name || "Candidate").replace(/\s+/g, '_');
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${candName}_1Page_Tech_Dossier.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        closeTechDossierModal();
    } catch (err) {
        alert("Dossier generation failed: " + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="download" class="w-4 h-4"></i><span>Download 1-Page PDF</span>`;
            if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
        }
    }
};

// Auto-open VIP modal if URL has ?action=vip (from exported PDF/Word/Tracker)
document.addEventListener("DOMContentLoaded", () => {
    try {
        const params = new URLSearchParams(window.location.search);
        if (params.get("action") === "vip") {
            setTimeout(() => {
                if (typeof openVipPricingModal === "function") {
                    openVipPricingModal();
                }
            }, 600);
        }
    } catch (e) {}
});
