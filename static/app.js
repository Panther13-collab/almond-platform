// Almond AI Global Platform Controller (Restored & Synchronized)

let currentProfile = null;
let currentJobs = [];
let currentAtsJobs = [];
let currentLinkedinJobs = [];
let currentCurrency = "INR";
let currentMinPackage = 15;
let selectedLocations = ["Worldwide Remote", "All India", "Coimbatore", "Chennai", "Bengaluru", "Kerala"];

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
    initCompensationControls();
    initLocationAutocomplete();
    initJobSearch();
    initLinkedinToggle();
    initModal();
    initExports();
    initLivePostingsCounter();
    initHumanVerifier();
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
            dropZone.classList.add("border-blue-600", "bg-blue-100/60");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove("border-blue-600", "bg-blue-100/60");
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

    if (!parsedSection) return;

    nameEl.textContent = profile.name || "Identified Candidate";
    yoeEl.textContent = `${profile.years_experience || 3}+ Years Verified`;
    roleEl.textContent = profile.current_role || "Software Engineer";

    skillsCloud.innerHTML = "";
    (profile.skills || []).forEach(skill => {
        const badge = document.createElement("span");
        badge.className = "px-3 py-1 bg-white text-slate-900 text-xs font-black rounded-lg border border-slate-300 shadow-sm capitalize hover:border-violet-400 hover:text-violet-800 transition";
        badge.textContent = skill;
        skillsCloud.appendChild(badge);
    });

    parsedSection.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
}

// 2. Unrestricted Compensation & Currency Controls
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
                t.classList.remove("active", "bg-white", "text-blue-700", "shadow-sm", "border", "border-slate-200");
                t.classList.add("text-slate-700");
            });
            tab.classList.add("active", "bg-white", "text-blue-700", "shadow-sm", "border", "border-slate-200");
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
                    t.classList.remove("active", "bg-white", "text-blue-700", "shadow-sm", "border", "border-slate-200");
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

    function renderActiveTags() {
        tagsContainer.innerHTML = "";
        if (selectedLocations.length === 0) {
            tagsContainer.innerHTML = `<span class="text-xs font-bold text-slate-500 italic p-1">No location filters active (All worldwide locations accepted)</span>`;
            return;
        }

        selectedLocations.forEach(loc => {
            const tag = document.createElement("span");
            tag.className = "inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-extrabold bg-violet-100 text-violet-900 border-2 border-violet-300 shadow-sm animate-in fade-in";
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
        if (!query) {
            dropdown.classList.add("hidden");
            return;
        }

        const matches = WORLDWIDE_LOCATIONS_DB.filter(item => 
            item.name.toLowerCase().includes(query) || item.region.toLowerCase().includes(query)
        ).slice(0, 8);

        dropdown.innerHTML = "";

        if (matches.length === 0) {
            dropdown.innerHTML = `
                <div class="p-3.5 text-xs font-black text-slate-900 flex items-center justify-between cursor-pointer hover:bg-violet-50" id="addCustomLocRow">
                    <span>Add custom location: <strong>"${searchInput.value}"</strong></span>
                    <span class="text-xs bg-violet-200 text-violet-900 px-2 py-0.5 rounded-md font-black">Press Enter</span>
                </div>
            `;
            document.getElementById("addCustomLocRow")?.addEventListener("click", () => {
                addLocation(searchInput.value);
            });
        } else {
            matches.forEach(item => {
                const row = document.createElement("div");
                row.className = "p-3 hover:bg-violet-50/80 cursor-pointer flex items-center justify-between text-xs font-bold transition border-b border-slate-100 last:border-0";
                row.innerHTML = `
                    <div class="flex items-center space-x-2">
                        <span class="text-blue-700 font-black">📍 ${item.name}</span>
                        <span class="text-xs text-slate-600 font-medium">(${item.region})</span>
                    </div>
                    <span class="text-xs font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">${item.type}</span>
                `;
                row.addEventListener("click", () => {
                    addLocation(item.name);
                });
                dropdown.appendChild(row);
            });
        }

        dropdown.classList.remove("hidden");
    });

    // Enter Key
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

    // Quick preset buttons
    quickPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const loc = pill.getAttribute("data-loc");
            addLocation(loc);
        });
    });

    renderActiveTags();
}

// 4. Job Search Execution
function initJobSearch() {
    const searchBtn = document.getElementById("searchJobsBtn");
    const emptyState = document.getElementById("emptyState");
    const jobsLoading = document.getElementById("jobsLoading");
    const jobListContainer = document.getElementById("jobListContainer");
    const resultsCountBadge = document.getElementById("resultsCountBadge");
    const linkedinToggleToolbar = document.getElementById("linkedinToggleToolbar");
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

        // Reset LinkedIn state
        if (resultsLinkedinToggle) resultsLinkedinToggle.checked = false;
        if (linkedinSectionContainer) linkedinSectionContainer.classList.add("hidden");
        if (linkedinCardsContainer) linkedinCardsContainer.innerHTML = "";
        if (linkedinToggleToolbar) linkedinToggleToolbar.classList.add("hidden");
        currentLinkedinJobs = [];

        try {
            const resp = await fetch("/api/find-jobs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || "Error querying live ATS index.");
            }

            const data = await resp.json();
            currentAtsJobs = data.jobs || [];
            currentJobs = currentAtsJobs;

            if (jobsLoading) jobsLoading.classList.add("hidden");
            searchBtn.disabled = false;

            if (resultsCountBadge) {
                resultsCountBadge.textContent = `${currentAtsJobs.length} Verified Direct ATS`;
            }
            enableExportButtons(currentAtsJobs.length > 0);

            if (currentAtsJobs.length === 0) {
                if (jobListContainer) {
                    jobListContainer.innerHTML = `
                        <div class="glass-panel rounded-3xl border-2 border-slate-200/90 p-10 text-center shadow-md">
                            <p class="text-base font-black text-slate-900">No matching direct ATS jobs found with your current filters.</p>
                            <p class="text-sm font-semibold text-slate-600 mt-1.5">Try selecting "Any" compensation band or adding "Worldwide Remote".</p>
                        </div>
                    `;
                }
            } else {
                renderJobCards(currentAtsJobs, "jobListContainer", false);
                // Reveal LinkedIn Toggle in toolbar now that verified jobs are displayed
                if (linkedinToggleToolbar) {
                    linkedinToggleToolbar.classList.remove("hidden");
                }
            }

        } catch (err) {
            if (jobsLoading) jobsLoading.classList.add("hidden");
            searchBtn.disabled = false;
            alert("Search failed: " + err.message);
        }
    }

    searchBtn.addEventListener("click", () => {
        if (!currentProfile) {
            alert("Please upload a candidate resume first to match live skills.");
            document.getElementById("dropZone")?.scrollIntoView({ behavior: "smooth" });
            return;
        }

        if (!isHumanVerified()) {
            openHumanVerification("Almond-AI_Direct_ATS_Index.apks", () => {
                executeSearch();
            });
            return;
        }

        executeSearch();
    });
}

// Post-Search LinkedIn Toggle Controller
function initLinkedinToggle() {
    const toggle = document.getElementById("resultsLinkedinToggle");
    const sectionContainer = document.getElementById("linkedinSectionContainer");
    const cardsContainer = document.getElementById("linkedinCardsContainer");
    const loadingEl = document.getElementById("linkedinLoading");

    if (!toggle) return;

    toggle.addEventListener("change", async () => {
        if (toggle.checked) {
            if (sectionContainer) sectionContainer.classList.remove("hidden");
            
            // If already loaded for this search, just reveal
            if (currentLinkedinJobs && currentLinkedinJobs.length > 0) {
                cardsContainer?.scrollIntoView({ behavior: "smooth", block: "nearest" });
                return;
            }

            // Otherwise, fetch 10 live LinkedIn postings
            if (loadingEl) loadingEl.classList.remove("hidden");
            if (cardsContainer) cardsContainer.innerHTML = "";

            const workMode = document.querySelector('input[name="work_mode"]:checked')?.value || "all";
            const empType = document.querySelector('input[name="employment_type"]:checked')?.value || "all";

            try {
                const resp = await fetch("/api/find-linkedin-jobs", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        profile: currentProfile,
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
                const data = await resp.json();
                currentLinkedinJobs = data.jobs || [];

                if (loadingEl) loadingEl.classList.add("hidden");
                if (currentLinkedinJobs.length === 0) {
                    if (cardsContainer) {
                        cardsContainer.innerHTML = `
                            <div class="glass-panel rounded-3xl p-8 text-center text-slate-700 text-sm font-bold border-2 border-slate-200">
                                No third-party LinkedIn postings found matching current keywords.
                            </div>
                        `;
                    }
                } else {
                    renderJobCards(currentLinkedinJobs, "linkedinCardsContainer", true);
                    cardsContainer?.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }
            } catch (e) {
                if (loadingEl) loadingEl.classList.add("hidden");
                if (cardsContainer) {
                    cardsContainer.innerHTML = `
                        <div class="glass-panel rounded-3xl p-6 text-center text-amber-900 text-sm font-bold border-2 border-amber-300 bg-amber-50">
                            Failed to fetch third-party LinkedIn feed: ${e.message}
                        </div>
                    `;
                }
            }
        } else {
            if (sectionContainer) sectionContainer.classList.add("hidden");
        }
    });
}

function renderJobCards(jobs, containerId = "jobListContainer", isThirdParty = false) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    jobs.forEach((job, idx) => {
        const card = document.createElement("div");
        card.className = "glass-panel rounded-3xl p-6 sm:p-7 relative overflow-hidden group border-2 border-slate-200/90 hover:border-violet-400 transition-all shadow-md bg-white/95 mb-5";

        const isLinkedin = isThirdParty || Boolean(job.is_linkedin);
        
        // Match Score styling
        const isHighScore = job.cvmatch_score >= 80;
        const scoreColor = isHighScore
            ? "bg-emerald-50 text-emerald-900 border-2 border-emerald-400/90 shadow-sm"
            : "bg-violet-50 text-violet-900 border-2 border-violet-400/90 shadow-sm";
        const scoreDot = isHighScore
            ? `<span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>`
            : `<span class="w-2.5 h-2.5 rounded-full bg-violet-600"></span>`;

        const empTag = job.employment_type_tag || "Full-Time";

        const sourceBadgeHtml = isLinkedin 
            ? `<span class="text-xs font-black px-3 py-1.5 rounded-xl bg-[#0A66C2] text-white flex items-center space-x-1.5 shadow-sm">
                <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.6 1.6 0 0 0-1.6 1.6 1.6 1.6 0 0 0 1.6-1.6 1.6 1.6 0 0 0 1.6-1.6Z"/></svg>
                <span>LINKEDIN FEED</span>
               </span>`
            : `<span class="text-xs font-black px-3 py-1.5 rounded-xl bg-slate-950 text-white uppercase tracking-wider flex items-center space-x-1.5 border border-slate-700 shadow-sm">
                <i data-lucide="shield-check" class="w-4 h-4 text-emerald-400"></i>
                <span>${(job.source || "Direct ATS").toUpperCase()}</span>
               </span>`;

        const thirdPartyWarning = isLinkedin
            ? `<div class="mt-2.5 p-3 rounded-2xl bg-amber-50 border border-amber-300 text-amber-950 text-xs font-bold flex items-center space-x-2.5 shadow-sm">
                <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-700 flex-shrink-0"></i>
                <span>Third-Party Feed Posting — Verify listing status directly. Direct ATS application is recommended.</span>
               </div>`
            : '';

        const applyBtnHtml = isLinkedin
            ? `<a href="${job.url}" target="_blank" rel="noopener noreferrer" class="px-5 py-2.5 bg-[#0A66C2] hover:bg-[#004182] text-white text-xs sm:text-sm font-black rounded-xl flex items-center justify-center space-x-2 shadow-md transition transform active:scale-98">
                <span>Apply on LinkedIn</span>
                <i data-lucide="external-link" class="w-4 h-4"></i>
               </a>`
            : `<a href="${job.url}" target="_blank" rel="noopener noreferrer" class="px-5 py-2.5 bg-gradient-to-r from-blue-700 via-indigo-600 to-violet-700 hover:from-blue-800 hover:to-violet-800 text-white text-xs sm:text-sm font-black rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-indigo-500/25 transition transform active:scale-98">
                <span>Direct Apply to ATS</span>
                <i data-lucide="external-link" class="w-4 h-4"></i>
               </a>`;

        const matchedSkillsHtml = (job.matched_skills || []).slice(0, 8).map(s => 
            `<span class="px-3 py-1 bg-white text-slate-900 text-xs font-black rounded-lg border border-slate-300 shadow-sm hover:border-violet-400 hover:text-violet-800 transition">${s}</span>`
        ).join("");

        card.innerHTML = `
            <!-- Top Ambient Glow Edge -->
            <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 opacity-80 group-hover:opacity-100 transition-opacity"></div>

            <!-- Top Row: Match Score + Source + Comp -->
            <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pt-1">
                <div class="space-y-2 max-w-3xl">
                    <div class="flex items-center flex-wrap gap-2">
                        <span class="text-xs sm:text-sm font-black px-3.5 py-1.5 rounded-xl flex items-center space-x-1.5 ${scoreColor}">
                            ${scoreDot}
                            <span>${job.cvmatch_score}% CV Match</span>
                        </span>
                        ${sourceBadgeHtml}
                        <span class="text-xs font-black px-3 py-1.5 rounded-xl bg-violet-100 text-violet-900 border border-violet-300 shadow-sm">
                            ${empTag}
                        </span>
                        <span class="text-xs font-black text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">#${idx + 1}</span>
                    </div>

                    <h3 class="text-xl sm:text-2xl font-black text-slate-950 group-hover:text-blue-700 transition-colors tracking-tight leading-tight pt-1">
                        ${job.title}
                    </h3>

                    <div class="flex items-center flex-wrap gap-2 text-sm font-bold text-slate-700 pt-0.5">
                        <span class="flex items-center space-x-1.5 text-slate-950 font-black">
                            <i data-lucide="building-2" class="w-4 h-4 text-blue-600"></i>
                            <span>${job.company}</span>
                        </span>
                        <span class="text-slate-400">•</span>
                        <span class="flex items-center space-x-1.5 text-slate-800 font-extrabold">
                            <i data-lucide="map-pin" class="w-4 h-4 text-indigo-600"></i>
                            <span>${job.location_tag || job.location || 'Remote'}</span>
                        </span>
                        <span class="px-2.5 py-0.5 rounded-lg bg-blue-100 text-blue-900 text-xs font-black uppercase tracking-wider border border-blue-200">${job.work_mode || 'Remote'}</span>
                    </div>

                    ${thirdPartyWarning}
                </div>

                <div class="text-left sm:text-right flex-shrink-0 pt-1">
                    <div class="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-50 border-2 border-emerald-300 rounded-2xl text-emerald-900 text-sm sm:text-base font-black shadow-sm">
                        <i data-lucide="badge-dollar-sign" class="w-4 h-4 text-emerald-600"></i>
                        <span>${job.comp_display || 'Market Competitive'}</span>
                    </div>
                </div>
            </div>

            <!-- Matched Skills Bar -->
            ${matchedSkillsHtml ? `
                <div class="mt-4 pt-3.5 border-t border-slate-200/90 flex flex-wrap items-center gap-2">
                    <span class="text-xs font-black text-slate-700 uppercase tracking-wider mr-1">Overlap Skills:</span>
                    ${matchedSkillsHtml}
                </div>
            ` : ''}

            <!-- Action Buttons Row -->
            <div class="mt-5 pt-4 border-t border-slate-200/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <button type="button" class="generate-pitch-btn px-4 py-2.5 rounded-xl border-2 border-violet-300 bg-violet-50 hover:bg-violet-100 text-violet-900 text-xs sm:text-sm font-black flex items-center space-x-2 transition shadow-sm" data-container="${containerId}" data-idx="${idx}">
                    <i data-lucide="sparkles" class="w-4 h-4 text-violet-700"></i>
                    <span>Generate AI STAR Pitch</span>
                </button>

                ${applyBtnHtml}
            </div>
        `;

        // Render Paywall Lock Overlay for free users past index 3
        if (job.is_locked) {
            const overlay = document.createElement("div");
            overlay.className = "absolute inset-0 backdrop-blur-md bg-white/80 flex flex-col items-center justify-center p-6 text-center z-20 border-2 border-dashed border-violet-400 rounded-3xl";
            overlay.innerHTML = `
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-violet-600 text-white flex items-center justify-center mb-3 shadow-lg shadow-indigo-500/30">
                    <i data-lucide="lock" class="w-6 h-6"></i>
                </div>
                <h4 class="font-black text-slate-950 text-lg">Direct ATS Application Locked</h4>
                <p class="text-xs font-semibold text-slate-600 max-w-sm mt-1 mb-4">
                    Unlock all verified direct ATS links, exact recruiter-free endpoints, and custom STAR pitches for this opportunity.
                </p>
                <button onclick="triggerRazorpayCheckout()" class="px-6 py-2.5 bg-gradient-to-r from-blue-700 via-indigo-600 to-violet-700 hover:from-blue-800 hover:to-violet-800 text-white font-black text-xs uppercase tracking-wider rounded-xl shadow-xl shadow-indigo-500/25 flex items-center space-x-2 transition transform active:scale-95">
                    <i data-lucide="sparkles" class="w-4 h-4"></i>
                    <span>Unlock Almond Pro (₹699 / $19)</span>
                </button>
            `;
            card.appendChild(overlay);
        }

        container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();

    container.querySelectorAll(".generate-pitch-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const cId = btn.getAttribute("data-container");
            const idx = parseInt(btn.getAttribute("data-idx"));
            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : currentAtsJobs;
            if (targetList && targetList[idx]) {
                openPitchModal(targetList[idx]);
            }
        });
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
            alert("Please upload a resume and click 'Find Verified Direct ATS Jobs' first so Almond can build your dossier.");
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
                    format: format
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
function getCandidateUserId() {
    let uid = localStorage.getItem("almond_candidate_id");
    if (!uid) {
        uid = "cand_" + Math.random().toString(36).substring(2, 10) + "_" + Date.now().toString(36);
        localStorage.setItem("almond_candidate_id", uid);
    }
    return uid;
}

// 8. Dynamic Live Postings Telemetry (Crawler Simulation)
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

// 9. Razorpay Pro Checkout Flow
window.triggerRazorpayCheckout = async function() {
    const userId = getCandidateUserId();

    if (typeof Razorpay === "undefined") {
        alert("Razorpay payment gateway script is still loading. Please check your network connection and retry.");
        return;
    }

    try {
        // 1. Create order on backend
        const orderResp = await fetch("/api/payment/create-order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                amount_inr: 699
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
            name: "Almond AI",
            description: "Almond Pro Lifetime Access — Unrestricted Direct ATS Postings",
            order_id: orderData.order_id,
            image: "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
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
                            amount_inr: 699
                        })
                    });

                    const verifyData = await verifyResp.json();
                    if (verifyData.status === "success") {
                        localStorage.setItem("almond_is_paid", "true");
                        alert("🎉 Payment Successful! Your account has been upgraded to Almond Pro. All direct ATS endpoints and STAR pitches are now unlocked.");
                        
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
                email: currentProfile?.email || "candidate@almond.ai",
                contact: currentProfile?.phone || "9999999999"
            },
            notes: {
                platform: "Almond AI Direct ATS Intelligence",
                user_id: userId
            },
            theme: {
                color: "#6366f1"
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
    const progressBar = document.getElementById("holdProgressBar");
    const btnText = document.getElementById("holdVerifyBtnText");
    const hintText = document.getElementById("holdVerifyHint");
    const successIcon = document.getElementById("holdVerifySuccessIcon");
    const holdBtn = document.getElementById("holdVerifyBtn");

    if (ringCircle) {
        ringCircle.style.strokeDashoffset = "56.548";
        ringCircle.className = "text-blue-400 fill-none transition-none";
    }
    if (progressBar) {
        progressBar.style.width = "0%";
        progressBar.className = "absolute bottom-0 left-0 h-1 bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400 w-0 transition-none";
    }
    if (btnText) {
        btnText.textContent = "Hold to verify";
        btnText.className = "text-sm font-bold text-blue-400 tracking-wide transition-colors";
    }
    if (hintText) {
        hintText.textContent = "Press and hold until the ring fills, then let go. The Space bar works too.";
        hintText.className = "text-xs text-slate-400 text-center mt-3.5 font-medium leading-relaxed transition-colors";
    }
    if (successIcon) successIcon.classList.add("hidden");
    if (holdBtn) {
        holdBtn.className = "w-full py-4 px-6 bg-[#1e222d] hover:bg-[#252a37] active:bg-[#1a1e29] border-2 border-blue-500/80 rounded-2xl flex items-center justify-center space-x-3 transition-all relative overflow-hidden group shadow-lg shadow-blue-500/10 cursor-pointer outline-none focus:ring-2 focus:ring-blue-400";
    }
}

function initHumanVerifier() {
    const modal = document.getElementById("humanVerifyModal");
    const closeBtn = document.getElementById("closeVerifyModal");
    const holdBtn = document.getElementById("holdVerifyBtn");
    const ringCircle = document.getElementById("holdRingCircle");
    const progressBar = document.getElementById("holdProgressBar");
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

    const HOLD_DURATION = 1600; // 1.6 seconds
    const CIRCUMFERENCE = 56.548; // 2 * PI * 9
    let isHolding = false;
    let holdStartTime = 0;
    let animFrameId = null;
    let isFullyLoaded = false;

    function startHold(e) {
        if (e.type === "keydown" && e.code !== "Space") return;
        if (e.type === "keydown") e.preventDefault();
        if (isHolding || isFullyLoaded) return;

        isHolding = true;
        isFullyLoaded = false;
        holdStartTime = performance.now();

        if (hintText) hintText.textContent = "Keep holding until the ring completes...";

        function tick(now) {
            if (!isHolding) return;
            const elapsed = now - holdStartTime;
            const progress = Math.min(elapsed / HOLD_DURATION, 1.0);

            // Animate SVG circular ring & bottom progress bar
            if (ringCircle) {
                const offset = CIRCUMFERENCE * (1 - progress);
                ringCircle.style.strokeDashoffset = `${offset}`;
            }
            if (progressBar) {
                progressBar.style.width = `${progress * 100}%`;
            }

            if (progress >= 1.0) {
                isFullyLoaded = true;
                if (btnText) btnText.textContent = "Let go now";
                if (hintText) hintText.textContent = "Let go now";
                if (holdBtn) {
                    holdBtn.classList.add("border-cyan-400", "shadow-cyan-500/30");
                }
                return;
            }

            animFrameId = requestAnimationFrame(tick);
        }

        animFrameId = requestAnimationFrame(tick);
    }

    function releaseHold(e) {
        if (e.type === "keyup" && e.code !== "Space") return;
        if (!isHolding) return;
        isHolding = false;
        if (animFrameId) cancelAnimationFrame(animFrameId);

        if (isFullyLoaded) {
            // Human verified!
            sessionStorage.setItem("almond_human_verified", "true");
            if (btnText) {
                btnText.textContent = "Human Verified!";
                btnText.className = "text-sm font-black text-emerald-400 tracking-wide";
            }
            if (hintText) {
                hintText.textContent = "Verification complete! Launching...";
                hintText.className = "text-xs text-emerald-400 font-bold text-center mt-3.5";
            }
            if (successIcon) successIcon.classList.remove("hidden");
            if (holdBtn) {
                holdBtn.className = "w-full py-4 px-6 bg-emerald-950/80 border-2 border-emerald-400 rounded-2xl flex items-center justify-center space-x-3 transition-all relative overflow-hidden group shadow-lg shadow-emerald-500/20";
            }
            if (progressBar) {
                progressBar.className = "absolute bottom-0 left-0 h-1 bg-emerald-400 w-full";
            }

            setTimeout(() => {
                modal.classList.add("hidden");
                if (pendingHumanAction) {
                    const cb = pendingHumanAction;
                    pendingHumanAction = null;
                    cb();
                }
            }, 450);

        } else {
            // Released too early
            resetVerifierUI();
            if (btnText) btnText.textContent = "Hold longer";
            if (hintText) {
                hintText.textContent = "Released too early! Please press and hold until the ring fills.";
                hintText.className = "text-xs text-amber-400 font-bold text-center mt-3.5";
            }
            if (holdBtn) {
                holdBtn.classList.add("border-amber-400");
                setTimeout(() => {
                    holdBtn.classList.remove("border-amber-400");
                    if (hintText) {
                        hintText.textContent = "Press and hold until the ring fills, then let go. The Space bar works too.";
                        hintText.className = "text-xs text-slate-400 text-center mt-3.5 font-medium leading-relaxed";
                    }
                    if (btnText) btnText.textContent = "Hold to verify";
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


