// Capture Meta Ads / Social UTM & fbclid Attribution on Initial Landing
(function initAdAttributionTracker() {
    try {
        const sp = new URLSearchParams(window.location.search || "");
        const utmSource = (sp.get("utm_source") || "").trim();
        const utmMedium = (sp.get("utm_medium") || "").trim();
        const utmCampaign = (sp.get("utm_campaign") || "").trim();
        const utmContent = (sp.get("utm_content") || "").trim();
        const fbclid = (sp.get("fbclid") || "").trim();
        if (utmSource || utmCampaign || fbclid) {
            sessionStorage.setItem("almond_ad_attribution", JSON.stringify({
                utm_source: utmSource || (fbclid ? "meta" : ""),
                utm_medium: utmMedium,
                utm_campaign: utmCampaign,
                utm_content: utmContent,
                fbclid: fbclid
            }));
        }
    } catch (_) {}
})();

window.almondTrackFunnel = function(eventName, extras = {}) {
    try {
        let saved = {};
        try {
            saved = JSON.parse(sessionStorage.getItem("almond_ad_attribution") || "{}") || {};
        } catch (_) {}

        const payload = {
            event_name: eventName,
            utm_source: saved.utm_source || "",
            utm_medium: saved.utm_medium || "",
            utm_campaign: saved.utm_campaign || "",
            utm_content: saved.utm_content || "",
            fbclid: saved.fbclid || "",
            user_name: extras.user_name || localStorage.getItem("almond_user_name") || "",
            user_email: extras.user_email || localStorage.getItem("almond_user_email") || "",
            amount_inr: extras.amount_inr || 0,
            meta: extras.meta || {}
        };

        fetch("/api/telemetry/event", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            keepalive: true,
            body: JSON.stringify(payload)
        }).catch(() => {});

        if (typeof window.fbq === "function") {
            const fbMap = {
                resume_upload: ["Lead", { content_name: "Resume Upload" }],
                signup: ["CompleteRegistration", { content_name: "Candidate Account" }],
                checkout_start: ["InitiateCheckout", { currency: extras.currency || "INR", value: extras.amount_inr || 0 }],
                purchase: ["Purchase", { currency: extras.currency || "INR", value: extras.amount_inr || 0 }]
            };
            const spec = fbMap[eventName];
            if (spec) window.fbq("track", spec[0], spec[1]);
        }
        if (typeof window.gtag === "function") {
            window.gtag("event", eventName, {
                utm_source: payload.utm_source,
                utm_campaign: payload.utm_campaign,
                value: payload.amount_inr || 0
            });
        }
    } catch (_) {}
};

// Curated Feeds Searchable Country/Location Filter Controller
const CURATED_WORLD_COUNTRIES = [
    { code: "all", name: "All Locations / Worldwide", flag: "🌐", keywords: "all worldwide global any remote" },
    { code: "India", name: "India", flag: "🇮🇳", keywords: "india in ind bharat bangalore bengaluru chennai hyderabad mumbai pune delhi" },
    { code: "United States", name: "United States (America)", flag: "🇺🇸", keywords: "united states america usa us u.s. california new york texas washington" },
    { code: "United Kingdom", name: "United Kingdom (UK)", flag: "🇬🇧", keywords: "united kingdom uk britain england scotland wales london manchester" },
    { code: "Canada", name: "Canada", flag: "🇨🇦", keywords: "canada can toronto vancouver montreal ontario" },
    { code: "Germany", name: "Germany", flag: "🇩🇪", keywords: "germany deutschland de berlin munich frankfurt" },
    { code: "Australia", name: "Australia", flag: "🇦🇺", keywords: "australia au aus sydney melbourne brisbane" },
    { code: "France", name: "France", flag: "🇫🇷", keywords: "france fr paris lyon" },
    { code: "Netherlands", name: "Netherlands", flag: "🇳🇱", keywords: "netherlands holland nl amsterdam" },
    { code: "Singapore", name: "Singapore", flag: "🇸🇬", keywords: "singapore sg" },
    { code: "Ireland", name: "Ireland", flag: "🇮🇪", keywords: "ireland ie dublin" },
    { code: "Switzerland", name: "Switzerland", flag: "🇨🇭", keywords: "switzerland ch swiss zurich geneva" },
    { code: "United Arab Emirates", name: "United Arab Emirates (UAE)", flag: "🇦🇪", keywords: "uae united arab emirates dubai abu dhabi" },
    { code: "Spain", name: "Spain", flag: "🇪🇸", keywords: "spain espana es madrid barcelona" },
    { code: "Japan", name: "Japan", flag: "🇯🇵", keywords: "japan tokyo jp" },
    { code: "Sweden", name: "Sweden", flag: "🇸🇪", keywords: "sweden se stockholm" },
    { code: "Poland", name: "Poland", flag: "🇵🇱", keywords: "poland pl warsaw krakow" },
    { code: "Brazil", name: "Brazil", flag: "🇧🇷", keywords: "brazil brasil br sao paulo" },
    { code: "Italy", name: "Italy", flag: "🇮🇹", keywords: "italy italia it rome milan" },
    { code: "Mexico", name: "Mexico", flag: "🇲🇽", keywords: "mexico mx" },
    { code: "South Africa", name: "South Africa", flag: "🇿🇦", keywords: "south africa za" },
    { code: "New Zealand", name: "New Zealand", flag: "🇳🇿", keywords: "new zealand nz auckland" },
    { code: "Austria", name: "Austria", flag: "🇦🇹", keywords: "austria at vienna" },
    { code: "Belgium", name: "Belgium", flag: "🇧🇪", keywords: "belgium be brussels" },
    { code: "Denmark", name: "Denmark", flag: "🇩🇰", keywords: "denmark dk copenhagen" },
    { code: "Finland", name: "Finland", flag: "🇫🇮", keywords: "finland fi helsinki" },
    { code: "Norway", name: "Norway", flag: "🇳🇴", keywords: "norway no oslo" },
    { code: "Portugal", name: "Portugal", flag: "🇵🇹", keywords: "portugal pt lisbon porto" },
    { code: "Israel", name: "Israel", flag: "🇮🇱", keywords: "israel il tel aviv" },
    { code: "South Korea", name: "South Korea", flag: "🇰🇷", keywords: "korea south korea kr seoul" },
    { code: "China", name: "China", flag: "🇨🇳", keywords: "china cn beijing shanghai" },
    { code: "Saudi Arabia", name: "Saudi Arabia", flag: "🇸🇦", keywords: "saudi arabia sa riyadh" },
    { code: "Argentina", name: "Argentina", flag: "🇦🇷", keywords: "argentina ar buenos aires" },
    { code: "Chile", name: "Chile", flag: "🇨🇱", keywords: "chile cl santiago" },
    { code: "Colombia", name: "Colombia", flag: "🇨🇴", keywords: "colombia co bogota" },
    { code: "Czech Republic", name: "Czech Republic", flag: "🇨🇿", keywords: "czech republic cz prague" },
    { code: "Greece", name: "Greece", flag: "🇬🇷", keywords: "greece gr athens" },
    { code: "Hungary", name: "Hungary", flag: "🇭🇺", keywords: "hungary hu budapest" },
    { code: "Indonesia", name: "Indonesia", flag: "🇮🇩", keywords: "indonesia id jakarta" },
    { code: "Malaysia", name: "Malaysia", flag: "🇲🇾", keywords: "malaysia my kuala lumpur" },
    { code: "Philippines", name: "Philippines", flag: "🇵🇭", keywords: "philippines ph manila" },
    { code: "Thailand", name: "Thailand", flag: "🇹🇭", keywords: "thailand th bangkok" },
    { code: "Vietnam", name: "Vietnam", flag: "🇻🇳", keywords: "vietnam vn hanoi ho chi minh" },
    { code: "Turkey", name: "Turkey", flag: "🇹🇷", keywords: "turkey tr turkiye istanbul ankara" },
    { code: "Egypt", name: "Egypt", flag: "🇪🇬", keywords: "egypt eg cairo" },
    { code: "Nigeria", name: "Nigeria", flag: "🇳🇬", keywords: "nigeria ng lagos" },
    { code: "Kenya", name: "Kenya", flag: "🇰🇪", keywords: "kenya ke nairobi" },
    { code: "Remote", name: "Worldwide / Remote Only", flag: "🌐", keywords: "remote worldwide anywhere global" }
];

window.toggleCuratedLocationDropdown = function(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById('curatedLocationMenu');
    if (!menu) return;
    const isHidden = menu.classList.contains('hidden');
    if (isHidden) {
        menu.classList.remove('hidden');
        renderCuratedLocationList();
        setTimeout(() => {
            const searchInput = document.getElementById('curatedLocationSearchInput');
            if (searchInput) {
                searchInput.value = "";
                searchInput.focus();
            }
        }, 50);
    } else {
        menu.classList.add('hidden');
    }
};

window.renderCuratedLocationList = function(filterQuery = "") {
    const listEl = document.getElementById('curatedLocationList');
    if (!listEl) return;
    const currentVal = document.getElementById('curatedLocationSelect')?.value || 'all';
    const q = filterQuery.trim().toLowerCase();

    const filtered = CURATED_WORLD_COUNTRIES.filter(c => {
        if (!q) return true;
        return c.name.toLowerCase().includes(q) || c.keywords.toLowerCase().includes(q);
    });

    if (filtered.length === 0) {
        listEl.innerHTML = `<div class="p-3 text-center text-xs text-slate-400 font-semibold">No countries matching "${filterQuery}"</div>`;
        return;
    }

    listEl.innerHTML = filtered.map(c => {
        const isSelected = c.code === currentVal;
        const activeClass = isSelected ? "bg-violet-600 text-white font-black" : "text-slate-800 hover:bg-violet-50 hover:text-violet-950 font-bold";
        return `
            <button type="button" class="w-full text-left px-2.5 py-1.5 rounded-xl ${activeClass} flex items-center justify-between transition cursor-pointer text-xs" onclick="selectCuratedLocation('${c.code}', '${c.name.replace(/'/g, "\\'")}', '${c.flag}')">
                <span class="flex items-center gap-2 truncate">
                    <span>${c.flag}</span>
                    <span class="truncate">${c.name}</span>
                </span>
                ${isSelected ? '<span class="text-xs">✓</span>' : ''}
            </button>
        `;
    }).join("");
};

window.filterCuratedLocationList = function(query) {
    renderCuratedLocationList(query);
};

window.selectCuratedLocation = function(code, name, flag) {
    const hiddenInput = document.getElementById('curatedLocationSelect');
    if (hiddenInput) hiddenInput.value = code;

    const triggerText = document.getElementById('curatedLocationTriggerText');
    if (triggerText) {
        if (code === 'all') {
            triggerText.innerHTML = `<span>🌐</span><span>All Countries</span>`;
        } else {
            triggerText.innerHTML = `<span>${flag}</span><span class="truncate">${name}</span>`;
        }
    }

    const menu = document.getElementById('curatedLocationMenu');
    if (menu) menu.classList.add('hidden');

    handleCuratedFilterChange();
};

document.addEventListener('click', (e) => {
    const container = document.getElementById('curatedLocationDropdownContainer');
    const menu = document.getElementById('curatedLocationMenu');
    if (container && menu && !container.contains(e.target)) {
        menu.classList.add('hidden');
    }
});


window.executeP2InternSearch = function() {
    const inp = document.getElementById("p2QuickKeywordInput");
    const val = (inp?.value || "").trim();
    window.openCuratedFeedsModal("internships", val);
};

window.executeP2EntrySearch = function() {
    const inp = document.getElementById("p2RoleSearchInput");
    const val = (inp?.value || "").trim();
    window.openCuratedFeedsModal("entrylevel", val);
};

window.executeP2RoleSearch = function() {
    const roleInput = document.getElementById("p2RoleSearchInput");
    const val = (roleInput?.value || "").trim();
    if (val) {
        const wsInput = document.getElementById("titleKeywordInput");
        if (wsInput) wsInput.value = val;
    }
    window.goToSlide(2);
};

window.executeP2KeywordSearch = function() {
    const kwInput = document.getElementById("p2QuickKeywordInput");
    const val = (kwInput?.value || "").trim();
    if (val) {
        const wsInput = document.getElementById("titleKeywordInput");
        if (wsInput) wsInput.value = val;
    }
    window.goToSlide(2);
};

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

const TOTAL_SLIDES = 4;

window.goToSlide = function(slideIdx) {
    if (slideIdx < 0) return;
    if (slideIdx >= 2) {
        const stream = document.getElementById("omniSearchResultsContainer");
        if (stream && !stream.classList.contains("hidden")) {
            const navOffset = 90;
            const elementPosition = stream.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - navOffset;
            window.scrollTo({ top: Math.max(0, offsetPosition), behavior: "smooth" });
        } else {
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
        return;
    }
    currentSlide = slideIdx;
    window.currentSlide = currentSlide;

    const anchorMap = {
        0: "hero",
        1: "discovery"
    };
    const targetId = anchorMap[slideIdx] || "hero";
    const targetEl = document.getElementById(targetId);

    // Responsive Fluid Smooth Navigation with header offset: keeps title and card tops fully visible
    if (targetEl) {
        if (slideIdx === 0) {
            window.scrollTo({ top: 0, behavior: "smooth" });
        } else {
            const navOffset = 90;
            const elementPosition = targetEl.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - navOffset;
            window.scrollTo({
                top: Math.max(0, offsetPosition),
                behavior: "smooth"
            });
        }
    }

    // Keep persistent background fixed at Page 2/3 positioning across all slides (0 zoom on scroll)
    const persistentBg = document.getElementById("persistentHeroBg");
    if (persistentBg) {
        persistentBg.style.transform = "scale(1.28) translate(-8.5%, 0)";
        persistentBg.style.opacity = "1";
    }

    // Update story dots
    for (let i = 0; i < TOTAL_SLIDES; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (dot) {
            dot.className = (i === currentSlide)
                ? "story-dot w-3.5 h-3.5 rounded-full bg-violet-600 ring-4 ring-violet-500/30 transition-all cursor-pointer shadow-md"
                : "story-dot w-2.5 h-2.5 rounded-full bg-slate-300 hover:bg-violet-400 transition-all cursor-pointer";
        }
    }

    // Update navbar slide buttons
    document.querySelectorAll(".nav-slide-btn").forEach((btn, idx) => {
        btn.className = (idx === currentSlide)
            ? "nav-slide-btn px-3.5 py-1.5 rounded-full bg-slate-950 text-white transition cursor-pointer"
            : "nav-slide-btn px-3.5 py-1.5 rounded-full hover:text-slate-950 hover:bg-slate-100 transition cursor-pointer";
    });
};

function initStoryPaging() {
    // 1. Maintain stationary background positioning across all pages (0 zoom on scroll)
    const persistentBg = document.getElementById("persistentHeroBg");
    if (persistentBg) {
        persistentBg.style.transform = "scale(1.28) translate(-8.5%, 0)";
        persistentBg.style.opacity = "1";
    }

    // 3. IntersectionObserver to sync currentSlide during natural scrolling across all viewports
    if (typeof IntersectionObserver !== "undefined") {
        const slideIds = ["hero", "discovery", "workspace", "results-stream"];
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && entry.intersectionRatio >= 0.35) {
                    const idx = slideIds.indexOf(entry.target.id);
                    if (idx !== -1) {
                        currentSlide = idx;
                        window.currentSlide = idx;
                        const persistentBg = document.getElementById("persistentHeroBg");
                        if (persistentBg) {
                            persistentBg.style.transform = "scale(1.28) translate(-8.5%, 0)";
                            persistentBg.style.opacity = "1";
                        }
                    }
                }
            });
        }, { threshold: [0.35] });

        slideIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) observer.observe(el);
        });
    }
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
    initTelemetryTicker();

    initResumeUpload();

    initAddSkillControls();

    initCompensationControls();

    initLocationAutocomplete();

    initWorkArrangementControls();

    if (typeof window.updateQuickLocationPillsUI === 'function') {
        window.updateQuickLocationPillsUI();
    }

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

    skillsCloud.replaceChildren();

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
            if (e.isComposing || e.keyCode === 229) return;
            handleAdd();
        }
    });

}

// Educational Value Proposition Modal (No Brokers, No Middlemen, No Dead Posts, 100% Direct Corporate)

// High-Contrast Light Theme Educational Value Modal (No Brokers, No Middlemen, No Dead Posts, 100% Direct Corporate)
const HERO_MODAL_DATA = {
    ingestion: {
        badge: "⚡ DIRECT JOB FEED",
        icon: "zap",
        iconClass: "text-violet-700",
        iconBg: "bg-violet-100 border border-violet-300 text-violet-800 shadow-xs",
        activeTabClass: "bg-violet-600 text-white font-black shadow-md border-violet-600 ring-2 ring-violet-300",
        title: "Direct Corporate Ingestion",
        subtitle: "How jobs reach you straight from company websites — fast & real",
        sections: [
            {
                heading: "1. Pulled Straight From Official Career Pages",
                headingColor: "text-violet-950 font-black",
                dotColor: "bg-violet-600",
                cardBorder: "border border-violet-200",
                accentBorder: "border-l-4 border-l-violet-600",
                cardBg: "bg-violet-50/40",
                desc: "Every job on Almond Jobs comes directly from official company career portals like Workday, Greenhouse, and Ashby — the exact same pages companies post to first."
            },
            {
                heading: "2. Zero Recruiter Agencies or Middlemen",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border border-emerald-200",
                accentBorder: "border-l-4 border-l-emerald-600",
                cardBg: "bg-emerald-50/40",
                desc: "You never have to talk to third-party consultancies asking for a cut of your salary, calling repeatedly, or forwarding your resume without permission."
            },
            {
                heading: "3. Real Active Openings Only",
                headingColor: "text-slate-950 font-black",
                dotColor: "bg-slate-700",
                cardBorder: "border border-slate-200",
                accentBorder: "border-l-4 border-l-slate-700",
                cardBg: "bg-white",
                desc: "When a company closes a role on their career page, our sync removes it automatically so students and job seekers don't waste hours applying to expired links."
            }
        ]
    },
    salary: {
        badge: "💰 SALARY RANGES",
        icon: "badge-check",
        iconClass: "text-emerald-700",
        iconBg: "bg-emerald-100 border border-emerald-300 text-emerald-800 shadow-xs",
        activeTabClass: "bg-emerald-600 text-white font-black shadow-md border-emerald-600 ring-2 ring-emerald-300",
        title: "Disclosed Salary & Stipend Bands",
        subtitle: "Know expected pay upfront before spending time applying",
        sections: [
            {
                heading: "1. Clear Pay & Stipend Estimates",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border border-emerald-200",
                accentBorder: "border-l-4 border-l-emerald-600",
                cardBg: "bg-emerald-50/40",
                desc: "For every internship and full-time job, Almond displays either the company's official disclosed salary range or an accurate industry benchmark (in ₹ LPA or monthly intern stipend)."
            },
            {
                heading: "2. Filter by Your Minimum Expectation",
                headingColor: "text-violet-950 font-black",
                dotColor: "bg-violet-600",
                cardBorder: "border border-violet-200",
                accentBorder: "border-l-4 border-l-violet-600",
                cardBg: "bg-violet-50/40",
                desc: "Choose 3 LPA, 7 LPA, 15 LPA, or any band in your Profile Vector. Selecting 7 LPA automatically includes 6 LPA all the way up to 30+ LPA roles so you never miss great offers."
            },
            {
                heading: "3. Better Offer Leverage",
                headingColor: "text-slate-950 font-black",
                dotColor: "bg-slate-700",
                cardBorder: "border border-slate-200",
                accentBorder: "border-l-4 border-l-slate-700",
                cardBg: "bg-white",
                desc: "Because companies don't pay 20% agency broker commissions when you apply directly through their portal, they have full budget flexibility for your final offer."
            }
        ]
    },
    routing: {
        badge: "🎯 DIRECT HIRING",
        icon: "send",
        iconClass: "text-indigo-700",
        iconBg: "bg-indigo-100 border border-indigo-300 text-indigo-800 shadow-xs",
        activeTabClass: "bg-indigo-600 text-white font-black shadow-md border-indigo-600 ring-2 ring-indigo-300",
        title: "Direct Hiring Team Routing",
        subtitle: "Your application goes straight to the company's actual recruiters",
        sections: [
            {
                heading: "1. One Click to Official Application Page",
                headingColor: "text-indigo-950 font-black",
                dotColor: "bg-indigo-600",
                cardBorder: "border border-indigo-200",
                accentBorder: "border-l-4 border-l-indigo-600",
                cardBg: "bg-indigo-50/40",
                desc: "Clicking Apply Direct opens the hiring company's official portal in a new tab — no middleman signup walls or spam redirects."
            },
            {
                heading: "2. Beat the 1,000+ Applicant Crowd",
                headingColor: "text-amber-950 font-black",
                dotColor: "bg-amber-600",
                cardBorder: "border border-amber-200",
                accentBorder: "border-l-4 border-l-amber-500",
                cardBg: "bg-amber-50/40",
                desc: "Most jobs reach LinkedIn days after opening, where 800+ people apply within hours. Applying directly right after opening puts your resume at the top of the company's review queue."
            },
            {
                heading: "3. Built-In AI Pitch & Job Tracker",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border border-emerald-200",
                accentBorder: "border-l-4 border-l-emerald-600",
                cardBg: "bg-white",
                desc: "Generate a tailored AI Pitch or Cover Letter for each role and save roles to your personal Kanban tracker so you stay organized from application to offer."
            }
        ]
    },
    about: {
        badge: "🛡️ WHO WE ARE",
        icon: "shield-check",
        iconClass: "text-emerald-700",
        iconBg: "bg-emerald-100 border border-emerald-300 text-emerald-800 shadow-xs",
        activeTabClass: "bg-emerald-600 text-white font-black shadow-md border-emerald-600 ring-2 ring-emerald-300",
        title: "About Almond Jobs",
        subtitle: "Built to help students & engineers skip spam and apply directly",
        sections: [
            {
                heading: "Why We Built Almond Jobs",
                headingColor: "text-emerald-950 font-black",
                dotColor: "bg-emerald-600",
                cardBorder: "border border-emerald-200",
                accentBorder: "border-l-4 border-l-emerald-600",
                cardBg: "bg-emerald-50/40",
                desc: "Students and developers waste too much time applying to closed listings and 1,000+ applicant crowds. Almond Jobs solves this by connecting you straight to verified company career portals."
            },
            {
                heading: "Free for Everyone (5+ Days) & Pro for Early Access",
                headingColor: "text-violet-950 font-black",
                dotColor: "bg-violet-600",
                cardBorder: "border border-violet-200",
                accentBorder: "border-l-4 border-l-violet-600",
                cardBg: "bg-violet-50/40",
                desc: "Every role posted 5+ days ago is 100% free to search, match, and apply. Optional Pro unlocks brand-new roles posted in the last 4 days so early applicants can move first."
            }
        ]
    }
};
HERO_MODAL_DATA.middlemen = HERO_MODAL_DATA.ingestion;
HERO_MODAL_DATA.brokers = HERO_MODAL_DATA.salary;
HERO_MODAL_DATA.deadposts = HERO_MODAL_DATA.routing;

function switchHeroModalTab(tabKey) {
    const aliasMap = { brokers: 'salary', middlemen: 'ingestion', deadposts: 'routing' };
    const resolvedKey = aliasMap[tabKey] || tabKey;
    const key = HERO_MODAL_DATA[resolvedKey] ? resolvedKey : 'ingestion';
    const data = HERO_MODAL_DATA[key];
    const modal = document.getElementById('heroInfoModal');
    if (!modal) return;

    const tabKeys = ['ingestion', 'salary', 'routing', 'about'];
    tabKeys.forEach(t => {
        const btn = document.getElementById('tab' + t.charAt(0).toUpperCase() + t.slice(1));
        if (btn) {
            btn.className = 'hero-modal-tab px-3.5 py-1.5 rounded-xl border transition cursor-pointer flex items-center gap-1 text-xs shrink-0 ';
            if (t === key) {
                btn.className += data.activeTabClass;
            } else {
                btn.className += 'bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold border-slate-300';
            }
        }
    });

    const iconContainer = document.getElementById('heroModalIcon');
    if (iconContainer) {
        iconContainer.className = 'w-10 h-10 rounded-2xl flex items-center justify-center transition-all ' + data.iconBg;
        iconContainer.innerHTML = '<i data-lucide="' + data.icon + '" class="w-5 h-5 ' + data.iconClass + '"></i>';
    }

    const titleEl = document.getElementById('heroModalTitle');
    if (titleEl) titleEl.textContent = data.title;

    const subtitleEl = document.getElementById('heroModalSubtitle');
    if (subtitleEl) subtitleEl.textContent = data.subtitle;

    const bodyEl = document.getElementById('heroModalBody');
    if (bodyEl) {
        bodyEl.innerHTML = data.sections.map(sec =>
            '<div class="p-4 rounded-2xl ' + sec.cardBorder + ' ' + sec.cardBg + ' transition-all shadow-2xs ' + (sec.accentBorder || '') + '">' +
                '<div class="flex items-center space-x-2 mb-1.5">' +
                    '<span class="w-2 h-2 rounded-full ' + sec.dotColor + ' shrink-0"></span>' +
                    '<span class="text-xs sm:text-sm font-black ' + sec.headingColor + '">' + sec.heading + '</span>' +
                '</div>' +
                '<p class="text-xs sm:text-[13px] text-slate-700 leading-relaxed font-medium">' + sec.desc + '</p>' +
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
    switchHeroModalTab(tabKey || 'about');
};

window.closeHeroInfoModal = function() {
    const modal = document.getElementById('heroInfoModal');
    if (modal) modal.classList.add('hidden');
};

window.switchHeroModalTab = switchHeroModalTab;
window.openAtsModal = function() {
    window.openHeroInfoModal('about');
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

    const vipPassModal = document.getElementById('vipPassModal');
    if (vipPassModal) {
        vipPassModal.addEventListener('click', (e) => {
            if (e.target === vipPassModal && typeof window.closeVipPassModal === 'function') closeVipPassModal();
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
            if (typeof window.closeVipPassModal === 'function') window.closeVipPassModal();
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

    if (!numberInput) return;

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

            if (slider) { slider.disabled = true; slider.value = 0; }

            currentMinPackage = 0;

            presetsContainer.innerHTML = `<span class="text-xs font-bold text-slate-600 italic">Showing all verified jobs regardless of salary band</span>`;

            return;

        }

        numberInput.disabled = false;

        if (slider) {
            slider.disabled = false;
            slider.min = cfg.min;
            slider.max = cfg.max;
            slider.step = cfg.step;
            slider.value = cfg.default;
        }
        const val = cfg.default;
        numberInput.value = val;

        currentMinPackage = val;

        renderPresets(cfg.presets);

    }

    function renderPresets(presets) {
        presetsContainer.replaceChildren();
        presets.forEach(p => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.setAttribute("data-val", p.val);
            if (p.val === currentMinPackage) {
                btn.className = "salary-preset-btn text-xs font-black px-3 py-1 rounded-xl bg-slate-950 text-white border-2 border-emerald-500 shadow-sm ring-1 ring-emerald-400 transition cursor-pointer";
            } else {
                btn.className = "salary-preset-btn text-xs font-bold px-3 py-1 rounded-xl bg-slate-50 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 hover:text-emerald-950 border border-slate-200 transition cursor-pointer";
            }
            btn.textContent = p.label;
            btn.addEventListener("click", () => {
                numberInput.value = p.val;
                if (slider && slider.max) {
                    slider.value = Math.min(p.val, parseInt(slider.max));
                }
                currentMinPackage = p.val;
                window.setSalaryPreset(p.val);
            });
            presetsContainer.appendChild(btn);
        });
    }

    // Sync slider to input if present
    if (slider) {
        slider.addEventListener("input", (e) => {
            const val = parseFloat(e.target.value);
            numberInput.value = val;
            currentMinPackage = val;
        });
    }

    // Sync input to state
    numberInput.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value) || 0;
        currentMinPackage = val;
        if (slider && val <= parseFloat(slider.max)) {
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

window.updateQuickLocationPillsUI = function() {
    const pills = document.querySelectorAll("#quickLocationPills button, .loc-preset-pill");
    pills.forEach(pill => {
        const loc = pill.getAttribute("data-loc") || pill.textContent.replace(/^[^\w\s]+/, '').trim();
        const isSel = selectedLocations.some(l => l.toLowerCase() === loc.toLowerCase());
        if (isSel) {
            pill.className = "loc-preset-pill text-xs font-black px-2.5 py-1 rounded-xl bg-slate-950 text-white border-2 border-emerald-500 shadow-sm ring-1 ring-emerald-400 transition cursor-pointer";
        } else {
            pill.className = "loc-preset-pill text-xs font-bold px-2.5 py-1 rounded-xl bg-slate-50 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 hover:text-emerald-950 border border-slate-200 transition cursor-pointer";
        }
    });
};

window.addLocationPreset = function(locName) {
    if (!locName) return;
    const clean = locName.trim();
    if (!clean) return;
    const lower = clean.toLowerCase();
    const idx = selectedLocations.findIndex(l => l.toLowerCase() === lower);
    if (idx >= 0) {
        selectedLocations.splice(idx, 1);
    } else {
        selectedLocations.push(clean);
    }
    if (typeof window.renderActiveLocationTags === 'function') {
        window.renderActiveLocationTags();
    }
    if (typeof window.updateQuickLocationPillsUI === 'function') {
        window.updateQuickLocationPillsUI();
    }
};

function initLocationAutocomplete() {
    const searchInput = document.getElementById("locationSearchInput");
    const dropdown = document.getElementById("locationDropdown");
    const tagsContainer = document.getElementById("selectedLocationsTags");
    const quickPills = document.querySelectorAll(".loc-preset-pill");

    if (!searchInput || !dropdown || !tagsContainer) return;

    function renderActiveTags() {
        tagsContainer.replaceChildren();
        if (selectedLocations.length === 0) {
            tagsContainer.classList.add("hidden");
            if (typeof window.updateQuickLocationPillsUI === 'function') window.updateQuickLocationPillsUI();
            return;
        }
        tagsContainer.classList.remove("hidden");

        selectedLocations.forEach(loc => {
            const tag = document.createElement("span");
            tag.className = "inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-950 border border-emerald-300 shadow-2xs animate-in fade-in";
            tag.innerHTML = `
                <span>${loc}</span>
                <button type="button" class="ml-1 text-emerald-700 hover:text-red-600 focus:outline-none font-black text-sm" data-loc="${loc}">
                    ✕
                </button>
            `;
            tag.querySelector("button").addEventListener("click", (e) => {
                e.stopPropagation();
                window.addLocationPreset(loc);
            });
            tagsContainer.appendChild(tag);
        });
        if (typeof window.updateQuickLocationPillsUI === 'function') window.updateQuickLocationPillsUI();
    }

    window.renderActiveLocationTags = renderActiveTags;

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
        dropdown.replaceChildren();

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
            if (e.isComposing || e.keyCode === 229) return;
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

    let _searchLoaderInterval = null;

    function startSearchLoader() {
        const loadingEl = document.getElementById("jobsLoading");
        const quoteEl = document.getElementById("loaderRotatingQuote");
        const progressEl = document.getElementById("loaderProgressBar");
        const stepTextEl = document.getElementById("loaderStepText");
        const percentTextEl = document.getElementById("loaderPercentText");

        if (!loadingEl) return;
        loadingEl.classList.remove("hidden");

        const messages = [
            {
                pct: 22,
                step: "Vectorizing candidate profile & key skills...",
                quote: "We are finding you the best matching jobs directly in corporate company portals. It might take a few seconds — wait for the best result!"
            },
            {
                pct: 48,
                step: "Scanning 3,315,000+ verified direct corporate openings...",
                quote: "Bypassing 100% of brokers and middlemen — landing you directly with internal hiring teams & HR."
            },
            {
                pct: 72,
                step: "Evaluating target locations & compensation thresholds...",
                quote: "You are going to be impressed with the jobs matching your application without any recruiters taking fee markups."
            },
            {
                pct: 90,
                step: "Scoring STAR pitch match & preparing direct HR portal links...",
                quote: "Connecting directly to verified hiring teams with zero middleman spread. Finalizing your results..."
            }
        ];

        let msgIdx = 0;
        if (progressEl) progressEl.style.width = "18%";
        if (percentTextEl) percentTextEl.textContent = "18%";
        if (stepTextEl) stepTextEl.textContent = messages[0].step;
        if (quoteEl) quoteEl.textContent = `"${messages[0].quote}"`;

        if (_searchLoaderInterval) clearInterval(_searchLoaderInterval);

        _searchLoaderInterval = setInterval(() => {
            msgIdx = (msgIdx + 1) % messages.length;
            const cur = messages[msgIdx];
            if (progressEl) progressEl.style.width = `${cur.pct}%`;
            if (percentTextEl) percentTextEl.textContent = `${cur.pct}%`;
            if (stepTextEl) stepTextEl.textContent = cur.step;
            if (quoteEl) {
                quoteEl.style.opacity = "0.2";
                setTimeout(() => {
                    quoteEl.textContent = `"${cur.quote}"`;
                    quoteEl.style.opacity = "1";
                }, 180);
            }
        }, 2200);
    }

    function stopSearchLoader() {
        if (_searchLoaderInterval) {
            clearInterval(_searchLoaderInterval);
            _searchLoaderInterval = null;
        }
        const progressEl = document.getElementById("loaderProgressBar");
        const percentTextEl = document.getElementById("loaderPercentText");
        const stepTextEl = document.getElementById("loaderStepText");
        if (progressEl) progressEl.style.width = "100%";
        if (percentTextEl) percentTextEl.textContent = "100%";
        if (stepTextEl) stepTextEl.textContent = "Match complete! Rendering direct postings...";

        setTimeout(() => {
            const loadingEl = document.getElementById("jobsLoading");
            if (loadingEl) loadingEl.classList.add("hidden");
        }, 350);
    }

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

        if (jobListContainer) jobListContainer.replaceChildren();

        startSearchLoader();

        searchBtn.disabled = true;

        // Slide transition to Page 3 (Live Results Vault)
        window.goToSlide(3);

        // Reset LinkedIn state

        if (resultsLinkedinToggle) resultsLinkedinToggle.checked = false;

        if (linkedinSectionContainer) linkedinSectionContainer.classList.add("hidden");

        if (linkedinCardsContainer) linkedinCardsContainer.replaceChildren();

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

            if (typeof data.is_paid === "boolean") {
                localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");
                if (typeof window.updateTopProfileBar === "function") window.updateTopProfileBar();
            }

            currentAtsJobs = data.jobs || [];

            currentJobs = currentAtsJobs;

            currentFounderJobs = data.founder_jobs || [];
            window.currentAtsJobs = currentAtsJobs;
            window.currentFounderJobs = currentFounderJobs;
            window.currentJobs = currentJobs;

            stopSearchLoader();

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

                // Reveal LinkedIn Toggle at bottom of all verified direct company jobs

                if (bottomLinkedinToggleCard) {

                    bottomLinkedinToggleCard.classList.remove("hidden");

                }

            }

            renderFounderCards(currentFounderJobs);

            window.goToSlide(3);

        } catch (err) {

            stopSearchLoader();

            searchBtn.disabled = false;

            alert("Search failed: " + err.message);

        }

    }

    searchBtn.addEventListener("click", () => {
        if (!currentProfile) {
            alert("Please upload a candidate resume first to match live skills.");
            window.goToSlide(2);
            return;
        }

        // Onboarding Check: Guest candidates must sign up or log in first
        if (!isUserLoggedIn()) {
            window._pendingJobSearch = true;
            window.openProfileModal("search_intercept");
            return;
        }

        executeSearch();
        window.goToSlide(3);
    });
}

// Helper to format posting date with human-readable freshness badges

function isJobLatestFeedLocked(job) {
    if (isUserPaid()) return false;
    if (!job || typeof job !== "object") return false;
    if (typeof job.is_locked === "boolean") return job.is_locked;
    if (typeof job.days_ago === "number") return job.days_ago <= 4;
    return false;
}

function formatJobDate(dateStr, daysAgo = null) {
    if (typeof daysAgo === "number" && Number.isFinite(daysAgo) && daysAgo >= 0) {
        if (daysAgo === 0) return { label: "Posted Today", isToday: true, tooltip: "Fresh vacancy active today" };
        if (daysAgo === 1) return { label: "1 day ago", isToday: false, tooltip: "Posted 1 day ago" };
        if (daysAgo < 7) return { label: `${daysAgo} days ago`, isToday: false, tooltip: `Posted ${daysAgo} days ago` };
    }

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

                user_id: getCandidateUserId(),

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

            if (cardsContainer) cardsContainer.replaceChildren();

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

    if (!append) container.replaceChildren();

    jobs.forEach((job, idx) => {
        const globalIdx = startIdx + idx;
        const card = document.createElement("div");

        // Direction B: Swiss Minimalist Luxury Atomic Card
        card.className = "kage-card rounded-2xl relative overflow-hidden group border bg-white hover:border-amber-400 mb-3.5 transition-all p-4 sm:p-5";
        card.setAttribute("style", "border-color: #e8dfd1; box-shadow: 0 4px 18px -3px rgba(0, 0, 0, 0.03), 0 0 1px 1px rgba(223, 183, 108, 0.1);");

        const isLinkedin = isThirdParty || Boolean(job.is_linkedin);

        // Match Score styling (Swiss Luxury Emerald & Warm Amber)
        const isHighScore = job.cvmatch_score >= 80;
        const scoreColor = isHighScore
            ? "bg-emerald-50 text-emerald-950 border border-emerald-300"
            : "bg-amber-50 text-amber-950 border border-amber-300";
        const scoreDot = isHighScore
            ? `<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>`
            : `<span class="w-2 h-2 rounded-full bg-amber-500"></span>`;

        // Live Blinking Green Badge
        const liveBadgeHtml = `
            <span class="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-950 border border-emerald-300 font-black text-[11px]" title="Active real-time vacancy verified on direct corporate portal">
                <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span class="uppercase tracking-wider">LIVE</span>
            </span>
        `;

        const isLocked = isJobLatestFeedLocked(job);
        const isAuthLocked = !isUserLoggedIn() || Boolean(job.is_auth_locked);

        // Date Badge (ALWAYS clearly visible even when latest post is blurred)
        const dateInfo = formatJobDate(job.posted_at || job.created_at, job.days_ago);
        const dateBadgeHtml = dateInfo.isToday
            ? `<span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-900 border border-emerald-200 text-[11px] font-black" title="${dateInfo.tooltip}">
                <i data-lucide="zap" class="w-3 h-3 text-emerald-600"></i>
                <span>${dateInfo.label}</span>
               </span>`
            : `<span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-slate-50 text-slate-700 border border-slate-200 text-[11px] font-bold" title="${dateInfo.tooltip}">
                <i data-lucide="calendar" class="w-3 h-3 text-slate-500"></i>
                <span>${dateInfo.label}</span>
               </span>`;

        const empTag = job.employment_type_tag || "Full-Time";
        const rawSource = (job.source || "Direct Feed").toUpperCase();

        const atsPill = isLinkedin
            ? `<span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-blue-50 text-blue-900 border border-blue-200 text-[11px] font-black uppercase">
                <svg class="w-3 h-3 fill-current" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.6 1.6 0 0 0-1.6 1.6 1.6 1.6 0 0 0 1.6-1.6Z"/></svg>
                <span>LINKEDIN</span>
               </span>`
            : `<span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-950 border border-emerald-300 text-[11px] font-black uppercase" title="Direct Enterprise Career Feed">
                <i data-lucide="shield-check" class="w-3 h-3 text-emerald-600"></i>
                <span>DIRECT COMPANY &bull; ${rawSource}</span>
               </span>`;

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
            <button type="button" onclick="goToKanbanTabAndScroll()" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-violet-50 hover:bg-violet-100 border border-violet-300 text-violet-950 font-black text-xs shadow-2xs transition cursor-pointer" title="Already in your applied tracker. Click to view on Kanban.">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-violet-700"></i>
                <span>Applied</span>
            </button>
        ` : '';

        // Action Buttons: AI Pitch, Cover Letter, Save, Direct Apply
        const pitchBtnHtml = `
            <button type="button" class="generate-pitch-btn px-3 py-1.5 rounded-xl border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-950 text-xs font-black flex items-center space-x-1.5 transition shadow-2xs cursor-pointer" data-container="${containerId}" data-idx="${globalIdx}">
                <i data-lucide="sparkles" class="w-3.5 h-3.5 text-amber-700"></i>
                <span>AI STAR Pitch</span>
            </button>
            <button type="button" class="generate-cover-letter-btn px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold flex items-center space-x-1.5 transition shadow-2xs cursor-pointer" data-container="${containerId}" data-idx="${globalIdx}">
                <i data-lucide="file-text" class="w-3.5 h-3.5 text-slate-600"></i>
                <span>Cover Letter</span>
            </button>
            <button type="button" class="save-kanban-btn px-2.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center space-x-1 transition cursor-pointer" data-container="${containerId}" data-idx="${globalIdx}" title="Save to Target list">
                <i data-lucide="bookmark" class="w-3.5 h-3.5 text-slate-500"></i>
                <span>Save</span>
            </button>
        `;

        const applyBtnHtml = isAuthLocked
            ? window.renderDirectApplyActionHtml({ isAuthLocked: true, isVipLocked: false, safeUrl: "#", compact: true })
            : (isLocked
                ? window.renderDirectApplyActionHtml({ isAuthLocked: false, isVipLocked: true, safeUrl: "#", compact: true })
                : (isLinkedin
                    ? `<a href="${job.url}" target="_blank" rel="noopener noreferrer" class="direct-apply-link inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-[#0A66C2] hover:bg-[#004182] text-white text-xs sm:text-sm font-black rounded-xl shadow-xs transition" data-container="${containerId}" data-idx="${globalIdx}">
                        <span>Apply on LinkedIn</span>
                        <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                       </a>`
                    : `<a href="${job.url}" target="_blank" rel="noopener noreferrer" class="direct-apply-link inline-flex items-center justify-center gap-1.5 px-5 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-black text-xs sm:text-sm rounded-xl shadow-xs shadow-emerald-600/20 transition transform active:scale-98" data-container="${containerId}" data-idx="${globalIdx}">
                        <span>Apply Direct ↗</span>
                        <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                       </a>`));

        const matchedSkillsHtml = (job.matched_skills || []).slice(0, 5).map(s => 
            `<span class="px-2 py-0.5 bg-slate-50 text-slate-800 text-[11px] font-bold rounded-lg border border-slate-200">${s}</span>`
        ).join("");

        let cleanCompDisplay = (job.comp_display || 'Market Standard for Candidate Years of Experience')
            .replace(/\bYOE\b/g, 'Candidate Years of Experience');

        const isUrgent = (job.days_ago !== undefined && job.days_ago <= 2) || dateInfo.isToday || job.is_urgent || job.urgent_hiring;
        const urgentBadgeHtml = isUrgent ? `
            <span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-rose-50 text-rose-900 border border-rose-300 text-[11px] font-black uppercase tracking-wider" title="High-priority corporate opening. Direct hiring underway.">
                <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                </span>
                <span>🔥 Urgent Hiring</span>
            </span>
        ` : '';

        const locLower = ((job.location_tag || job.location || '') + ' ' + (job.work_mode || '')).toLowerCase();
        let tzBadgeHtml = '';
        if (locLower.includes('us') || locLower.includes('united states') || locLower.includes('est') || locLower.includes('pst') || locLower.includes('cst') || locLower.includes('new york') || locLower.includes('san francisco') || locLower.includes('california')) {
            tzBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 text-blue-900 border border-blue-200 text-[10.5px] font-extrabold" title="US Timezone (EST/PST)">🇺🇸 US Remote (EST/PST)</span>`;
        } else if (locLower.includes('uk') || locLower.includes('london') || locLower.includes('gmt') || locLower.includes('great britain')) {
            tzBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-sky-50 text-sky-900 border border-sky-200 text-[10.5px] font-extrabold" title="UK Timezone (GMT)">🇬🇧 UK Remote (GMT)</span>`;
        } else if (locLower.includes('europe') || locLower.includes('eu') || locLower.includes('berlin') || locLower.includes('germany') || locLower.includes('amsterdam') || locLower.includes('cet')) {
            tzBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-900 border border-indigo-200 text-[10.5px] font-extrabold" title="European Timezone (CET)">🇪🇺 EU Remote (CET/GMT)</span>`;
        } else if (locLower.includes('india') || locLower.includes('bengaluru') || locLower.includes('bangalore') || locLower.includes('mumbai') || locLower.includes('delhi') || locLower.includes('hyderabad') || locLower.includes('pune') || locLower.includes('ist')) {
            tzBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-900 border border-emerald-200 text-[10.5px] font-extrabold" title="India Standard Time (IST)">🇮🇳 India / IST Remote</span>`;
        } else if (locLower.includes('remote') || locLower.includes('worldwide') || locLower.includes('global')) {
            tzBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-teal-50 text-teal-900 border border-teal-200 text-[10.5px] font-extrabold" title="Global Worldwide Remote">🌐 Global Remote</span>`;
        }

        let countdownStr = "4d 12h";
        const postTs = job.posted_at || job.created_at || (job.date_posted_ts ? job.date_posted_ts : 0);
        if (postTs > 0) {
            const unlockTs = postTs + (7 * 86400);
            const diffSec = Math.max(0, unlockTs - Math.floor(Date.now() / 1000));
            const diffDays = Math.floor(diffSec / 86400);
            const diffHours = Math.floor((diffSec % 86400) / 3600);
            countdownStr = diffDays > 0 ? `${diffDays}d ${diffHours}h` : `${diffHours}h ${Math.floor((diffSec % 3600)/60)}m`;
        } else {
            const daysLeft = Math.max(1, 7 - (job.days_ago !== undefined ? job.days_ago : 0));
            countdownStr = `${daysLeft}d 12h`;
        }

        const companyInitial = ((job.company || 'AJ').replace(/[^a-zA-Z0-9]/g, '').substring(0, 2) || 'AJ').toUpperCase();

        const titleBlurCls = isLocked ? "blur-[5px] select-none pointer-events-none opacity-80" : "";
        const vipLockBannerHtml = isLocked ? `
            <div class="my-2.5 p-3 rounded-xl bg-gradient-to-r from-amber-50 via-violet-50 to-indigo-50 border border-violet-200/90 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 shadow-2xs">
                <div class="flex items-center gap-2.5 flex-wrap text-xs font-extrabold text-slate-900">
                    <span class="w-6 h-6 rounded-lg bg-violet-600 text-white flex items-center justify-center shrink-0">🔒</span>
                    <span>Designation blurred &bull; Unlocked with VIP Pass (${dateInfo.label})</span>
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-950 border border-amber-300 font-extrabold text-[11px] animate-pulse">
                        <span>⏳</span>
                        <span>Unlocks for public in ${countdownStr} (VIPs are applying now)</span>
                    </span>
                </div>
                <button type="button" onclick="openVipPassModal()" class="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-black text-xs shadow-sm hover:scale-105 active:scale-95 transition cursor-pointer shrink-0">
                    👑 Unlock VIP for Latest Feed
                </button>
            </div>
        ` : "";

        card.innerHTML = `
            <!-- Line 1: Identity, Title, Direct Company Verification & Live Badges -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2.5 border-b border-slate-100">
                <div class="flex items-center gap-3 min-w-0">
                    <!-- Unblurred Company Initial -->
                    <div class="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200/90 text-amber-950 font-black text-xs sm:text-sm flex items-center justify-center flex-shrink-0 shadow-2xs">
                        ${companyInitial}
                    </div>
                    <div class="min-w-0">
                        <div class="flex items-center gap-2 flex-wrap">
                            <!-- Only Designation/Title is Blurred When Locked -->
                            <h3 class="text-base sm:text-lg font-black text-slate-950 group-hover:text-amber-900 transition-colors tracking-tight truncate ${titleBlurCls}">
                                ${job.title}
                            </h3>
                            <!-- Unblurred Company Name (Always Crisp & Visible to Tempt Candidates) -->
                            <span class="text-xs font-black text-slate-900 bg-amber-50/90 px-2.5 py-0.5 rounded-lg border border-amber-300 shadow-2xs">@ ${job.company}</span>
                        </div>
                        <!-- Unblurred Location & Work Mode -->
                        <div class="flex items-center gap-2 text-xs font-semibold text-slate-600 flex-wrap">
                            <span class="flex items-center gap-1 font-bold text-slate-700"><i data-lucide="map-pin" class="w-3.5 h-3.5 text-slate-500"></i>${job.location_tag || job.location || 'Remote'}</span>
                            <span>&bull;</span>
                            <span class="text-slate-800 font-extrabold">${job.work_mode || 'Remote'}</span>
                            <span>&bull;</span>
                            <span class="font-bold text-slate-600">${empTag}</span>
                            ${tzBadgeHtml}
                        </div>
                    </div>
                </div>

                <!-- Always crisp & unblurred Freshness / Match Header -->
                <div class="flex items-center gap-2 flex-wrap sm:flex-nowrap flex-shrink-0">
                    ${isLocked ? `<span class="px-2.5 py-1 rounded-full bg-amber-100 text-amber-950 border border-amber-300 text-[10px] font-black uppercase tracking-wider">🔒 VIP Latest</span>` : atsPill}
                    ${liveBadgeHtml}
                    ${urgentBadgeHtml}
                    ${dateBadgeHtml}
                    <span class="text-xs sm:text-sm font-black px-2.5 py-1 rounded-xl flex items-center gap-1.5 ${scoreColor}">
                        ${scoreDot}
                        <span>${job.cvmatch_score}% Match</span>
                    </span>
                    <span class="text-[11px] font-bold text-slate-400">#${globalIdx + 1}</span>
                </div>
            </div>

            ${vipLockBannerHtml}

            <!-- Line 2: Unblurred Compensation & Estimated Package + Matched Skills -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 py-2.5 text-xs">
                <!-- Unblurred Estimated Package Display -->
                <div class="flex items-center gap-2">
                    <span class="font-black text-xs sm:text-sm text-slate-950 bg-amber-50/80 border border-amber-300 px-2.5 py-1 rounded-xl flex items-center gap-1 shadow-2xs">
                        <i data-lucide="badge-dollar-sign" class="w-3.5 h-3.5 text-emerald-700"></i>
                        <span>${cleanCompDisplay}</span>
                    </span>
                    <span class="text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200 hidden md:inline-flex">
                        0% Recruiter Spread
                    </span>
                </div>

                <!-- Secondary Info: Skills & Skill Gap -->
                <div class="flex items-center gap-1.5 flex-wrap ${isLocked ? 'blur-[4px] select-none pointer-events-none opacity-60' : ''}">
                    ${matchedSkillsHtml ? `
                        <span class="text-[11px] font-bold text-slate-500">Skills:</span>
                        ${matchedSkillsHtml}
                    ` : ''}
                    <button type="button" onclick="window.toggleSkillGapDrawer('${containerId}_${globalIdx}')" class="text-[11px] font-bold px-2 py-0.5 rounded-lg border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-950 transition cursor-pointer flex items-center gap-1" title="Inspect matched skills vs missing keywords">
                        <i data-lucide="scan-search" class="w-3 h-3 text-amber-700"></i>
                        <span>Skill Gap</span>
                    </button>
                </div>
            </div>

            <!-- Line 3: Direct Action Toolbar -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pt-2.5 border-t border-slate-100">
                <div class="flex items-center gap-2 flex-wrap ${isLocked ? 'opacity-40 pointer-events-none' : ''}">
                    ${pitchBtnHtml}
                    ${alreadyAppliedBadgeHtml}
                </div>
                <div class="sm:w-auto w-full">
                    ${applyBtnHtml}
                </div>
            </div>

            <!-- Collapsible Skill Gap Drawer -->
            <div id="skillGapDrawer_${containerId}_${globalIdx}" class="hidden mt-3 p-3.5 rounded-2xl bg-slate-50 border border-amber-200 text-xs transition-all">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-black text-slate-950 flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-600 animate-pulse"></span>
                        Resume Matcher &bull; Skill Gap Breakdown
                    </span>
                    <span class="text-[10px] font-bold text-slate-500">Vector Keyword Optimizer</span>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
                    <div class="p-2.5 rounded-xl bg-white border border-emerald-200">
                        <span class="text-[10px] font-black uppercase text-emerald-800 tracking-wider block mb-1">✓ Matched in Your Profile</span>
                        <div class="flex flex-wrap gap-1">
                            ${(job.matched_skills || []).slice(0, 6).map(s => `<span class="px-2 py-0.5 bg-emerald-50 text-emerald-900 border border-emerald-200 rounded font-bold text-[10px]">${s}</span>`).join('') || '<span class="text-slate-400 text-[10px]">Core stack matched</span>'}
                        </div>
                    </div>
                    <div class="p-2.5 rounded-xl bg-white border border-amber-300">
                        <span class="text-[10px] font-black uppercase text-amber-900 tracking-wider block mb-1">+ Recommended Gap Keywords</span>
                        <div class="flex flex-wrap gap-1">
                            ${(job.gap_skills || ['Docker', 'Kubernetes', 'Cloud']).slice(0, 4).map(s => `<span class="px-2 py-0.5 bg-amber-50 text-amber-950 border border-amber-300 rounded font-bold text-[10px]">+ ${s}</span>`).join('')}
                        </div>
                    </div>
                </div>
                <div class="pt-1.5 border-t border-slate-200 flex items-center justify-between">
                    <p class="text-[11px] text-slate-700 font-medium">
                        <strong class="text-slate-950 font-bold">Screening Edge:</strong> Adding these gap keywords lifts match score from <strong>${job.cvmatch_score}%</strong> to <strong>90%+</strong>.
                    </p>
                    <button type="button" onclick="window.generatePitchWithGaps('${containerId}', ${globalIdx})" class="text-[11px] font-black text-emerald-800 hover:text-emerald-950 underline cursor-pointer">Generate Gap-Tailored Pitch &rarr;</button>
                </div>
            </div>
        `;

        container.appendChild(card);
    });

    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }

    // Reattach event listeners for pitch, cover letter, save, and apply
    container.querySelectorAll(".generate-pitch-btn").forEach(btn => {
        btn.onclick = () => {
            const cId = btn.getAttribute("data-container");
            const idx = parseInt(btn.getAttribute("data-idx"), 10);
            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);
            if (targetList && targetList[idx]) {
                openPitchModal(targetList[idx]);
            }
        };
    });

    container.querySelectorAll(".generate-cover-letter-btn").forEach(btn => {
        btn.onclick = () => {
            const cId = btn.getAttribute("data-container");
            const idx = parseInt(btn.getAttribute("data-idx"), 10);
            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);
            if (targetList && targetList[idx]) {
                openCoverLetterModal(targetList[idx]);
            }
        };
    });

    container.querySelectorAll(".save-kanban-btn").forEach(btn => {
        btn.onclick = () => {
            const cId = btn.getAttribute("data-container");
            const idx = parseInt(btn.getAttribute("data-idx"), 10);
            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);
            if (targetList && targetList[idx]) {
                saveJobToTarget(targetList[idx]);
            }
        };
    });

    container.querySelectorAll(".direct-apply-link").forEach(link => {
        link.onclick = () => {
            const cId = link.getAttribute("data-container");
            const idx = parseInt(link.getAttribute("data-idx"), 10);
            const targetList = (cId === "linkedinCardsContainer") ? currentLinkedinJobs : (cId === "founderCardsWrapper" ? currentFounderJobs : currentAtsJobs);
            if (targetList && targetList[idx]) {
                trackJobApplication(targetList[idx]);
            }
        };
    });
}

window.renderJobCards = renderJobCards;

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

window.almondAiSessionCache = window.almondAiSessionCache || { pitch: {}, coverLetter: {} };

function _getAiCacheKey(job) {
    if (!job) return "";
    const uid = (typeof getCandidateUserId === "function" ? getCandidateUserId() : "") || "anon";
    const idPart = String(job.id || "").trim();
    const urlPart = String(job.url || "").trim();
    const fallbackPart = `${job.company || ""}_${job.title || job.role || ""}`.trim();
    const uniqueKey = [idPart, urlPart || fallbackPart].filter(Boolean).join("|").toLowerCase();
    return `${uid}::${uniqueKey}`;
}

async function openPitchModal(job) {
    if (!isUserLoggedIn()) {
        if (typeof window.openSignupToUnlockLinksModal === "function") window.openSignupToUnlockLinksModal();
        return;
    }

    const modal = document.getElementById("pitchModal");

    const pitchSub = document.getElementById("pitchJobSub");

    const pitchTextarea = document.getElementById("pitchTextarea");

    if (!modal) return;

    pitchSub.textContent = `Target: ${job.title} at ${job.company}`;

    const cacheKey = _getAiCacheKey(job);
    const cachedPitch = cacheKey ? window.almondAiSessionCache.pitch[cacheKey] : "";
    if (cachedPitch) {
        pitchTextarea.value = cachedPitch;
        if (typeof window.syncAiQuotaDisplay === "function") window.syncAiQuotaDisplay();
        modal.classList.remove("hidden");
        return;
    }

    pitchTextarea.value = "Synthesizing STAR-grounded application pitch based on your verified candidate metrics...";

    modal.classList.remove("hidden");

    try {

        const resp = await fetch("/api/get-pitch", {

            method: "POST",

            headers: { "Content-Type": "application/json" },

            body: JSON.stringify({

                user_id: getCandidateUserId(),

                profile: (typeof currentProfile !== "undefined" && currentProfile) || window.currentProfile || window.omniCurrentProfile || { name: localStorage.getItem("almond_user_name") || "Candidate", role: (job && (job.role || job.title)) || "Candidate", skills: window.omniDerivedSkills || [] },

                job: job

            })

        });

        const data = await resp.json().catch(() => ({}));

        if (resp.status === 401) {
            modal.classList.add("hidden");
            if (typeof window.openSignupToUnlockLinksModal === "function") window.openSignupToUnlockLinksModal();
            return;
        }
        if (resp.status === 403) {
            modal.classList.add("hidden");
            window.almondAiQuota.pitch_remaining = 0;
            window.syncAiQuotaDisplay();
            window.openProFeatureGateModal(
                "Free AI STAR Pitch limit reached (10/10)",
                data.detail || "You have used all 10 free AI STAR Pitches on this account. Upgrade to Pro for unlimited AI career tools and fresh job links."
            );
            return;
        }
        if (!resp.ok) throw new Error(data.detail || "Could not generate pitch.");

        if (data.quota) {
            if (data.quota.unlimited) {
                window.almondAiQuota.unlimited = true;
            } else if (typeof data.quota.remaining === "number") {
                window.almondAiQuota.pitch_remaining = data.quota.remaining;
                window.almondAiQuota.limit = data.quota.limit || 10;
            }
            window.syncAiQuotaDisplay();
        }

        if (cacheKey && data.pitch) {
            window.almondAiSessionCache.pitch[cacheKey] = data.pitch;
        }
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
    if (!isUserLoggedIn()) {
        if (typeof window.openSignupToUnlockLinksModal === "function") window.openSignupToUnlockLinksModal();
        return;
    }

    const modal = document.getElementById("coverLetterModal");

    const sub = document.getElementById("coverLetterSub");

    const textarea = document.getElementById("coverLetterTextarea");

    if (!modal) return;

    sub.textContent = `Tailored for ${job.title} at ${job.company}`;

    const cacheKey = _getAiCacheKey(job);
    const cachedLetter = cacheKey ? window.almondAiSessionCache.coverLetter[cacheKey] : "";
    if (cachedLetter) {
        textarea.value = cachedLetter;
        if (typeof window.syncAiQuotaDisplay === "function") window.syncAiQuotaDisplay();
        modal.classList.remove("hidden");
        return;
    }

    textarea.value = "Synthesizing executive cover letter grounded in your verified achievements...";

    modal.classList.remove("hidden");

    try {

        const resp = await fetch("/api/get-cover-letter", {

            method: "POST",

            headers: { "Content-Type": "application/json" },

            body: JSON.stringify({

                user_id: getCandidateUserId(),

                profile: (typeof currentProfile !== "undefined" && currentProfile) || window.currentProfile || window.omniCurrentProfile || { name: localStorage.getItem("almond_user_name") || "Candidate", role: (job && (job.role || job.title)) || "Candidate", skills: window.omniDerivedSkills || [] },

                job: job

            })

        });

        const data = await resp.json().catch(() => ({}));

        if (resp.status === 401) {
            modal.classList.add("hidden");
            if (typeof window.openSignupToUnlockLinksModal === "function") window.openSignupToUnlockLinksModal();
            return;
        }
        if (resp.status === 403) {
            modal.classList.add("hidden");
            window.almondAiQuota.cover_letter_remaining = 0;
            window.syncAiQuotaDisplay();
            window.openProFeatureGateModal(
                "Free AI Cover Letter limit reached (10/10)",
                data.detail || "You have used all 10 free AI Tailored Cover Letters on this account. Upgrade to Pro for unlimited cover letters and fresh job links."
            );
            return;
        }
        if (!resp.ok) throw new Error(data.detail || "Could not generate cover letter.");

        if (data.quota) {
            if (data.quota.unlimited) {
                window.almondAiQuota.unlimited = true;
            } else if (typeof data.quota.remaining === "number") {
                window.almondAiQuota.cover_letter_remaining = data.quota.remaining;
                window.almondAiQuota.limit = data.quota.limit || 10;
            }
            window.syncAiQuotaDisplay();
        }

        if (cacheKey && data.cover_letter) {
            window.almondAiSessionCache.coverLetter[cacheKey] = data.cover_letter;
        }
        textarea.value = data.cover_letter;

    } catch (err) {

        textarea.value = "Error generating cover letter: " + err.message;

    }

}

// 5c. View Switcher Tabs (Direct Corporate / Founder Direct / Kanban Tracker)

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

    wrapper.replaceChildren();

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

        const isFounderLocked = isJobLatestFeedLocked(job);
        const founderBlurCls = isFounderLocked ? "blur-[5px] select-none pointer-events-none opacity-75" : "";

        // Date Badge

        const dateInfo = formatJobDate(job.posted_at || job.created_at, job.days_ago);

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

                        <!-- Job Title (Designation blurred if locked) -->
                        <h3 class="text-xl sm:text-2xl font-black text-slate-950 group-hover:text-orange-600 transition-colors tracking-tight leading-tight ${founderBlurCls}">
                            ${job.title}
                        </h3>

                        <!-- Unblurred Company Name and Location (Tempts Candidates with Company Identity) -->
                        <div class="flex items-center flex-wrap gap-2 text-sm font-bold text-slate-700 pt-2">
                            <span class="flex items-center space-x-1.5 text-slate-950 font-black bg-amber-50 px-2.5 py-0.5 rounded-lg border border-amber-300">
                                <i data-lucide="building-2" class="w-4 h-4 text-orange-600"></i>
                                <span>${job.company}</span>
                            </span>
                            <span class="text-slate-400">•</span>
                            <span class="flex items-center space-x-1.5 text-slate-800 font-extrabold">
                                <i data-lucide="map-pin" class="w-4 h-4 text-slate-600"></i>
                                <span>${job.location || 'Remote'}</span>
                            </span>
                        </div>

                        <!-- Secondary Info (Summary and Direct Contact blurred if locked) -->
                        <div class="${founderBlurCls}">
                            ${emailPill ? `<div class="pt-2">${emailPill}</div>` : ''}
                            <p class="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium pt-2 line-clamp-3">
                                ${job.summary || job.full_text || ''}
                            </p>
                        </div>

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

                            <span class="text-xs text-emerald-800 font-black">0% Recruiter Spread</span>

                        </div>

                        <div class="p-4 rounded-2xl border border-orange-200/90 bg-orange-50/60 shadow-xs">

                            <span class="text-xs font-black uppercase tracking-wider text-orange-950 block mb-1">Target Package / Compensation</span>

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

                        ${isFounderLocked
                            ? `<button type="button" onclick="openVipPassModal()" class="w-full py-3.5 px-5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-black text-xs sm:text-sm rounded-xl flex items-center justify-center space-x-2 shadow-lg transition cursor-pointer">
                                <span>👑 Unlock VIP for Latest Feed</span>
                               </button>`
                            : `<a href="${job.url}" target="_blank" rel="noopener noreferrer" class="direct-apply-link w-full py-3.5 px-5 bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white font-black text-xs sm:text-sm rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-orange-500/25 transition transform active:scale-98" data-container="founderCardsWrapper" data-idx="${idx}">
                                <span>Direct Apply to Founder →</span>
                                <i data-lucide="external-link" class="w-4 h-4"></i>
                               </a>`
                        }

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

        container.replaceChildren();

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
        if (!isUserLoggedIn()) {
            if (typeof window.openSignupToUnlockLinksModal === "function") window.openSignupToUnlockLinksModal();
            return;
        }
        if (!isUserPaid()) {
            const labelMap = { pdf: "Export PDF", csv: "Export Sheet (CSV)", docx: "Export Word (.docx)" };
            window.openProFeatureGateModal(
                labelMap[format] || "Job Export",
                `You need Almond Jobs Pro to download ${labelMap[format] || "job reports"}. Upgrade to unlock CSV Sheet, Word, and PDF exports along with today's latest job links.`
            );
            return;
        }
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
    const hasToken = Boolean(localStorage.getItem("almond_session_token") || localStorage.getItem("almond_auth_token"));
    const hasUser = Boolean(localStorage.getItem("almond_user_id"));
    return hasToken && hasUser;
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

// 8. Dynamic Live Postings Telemetry (Direct Corporate Synchronization Engine)

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


// =========================================================================
// CONTRIBUTE & BUY ALMOND JOBS A COFFEE CONTROLLER
// =========================================================================

window.selectedCoffeeCount = 1;
window.selectedCoffeeAmount = 485;

window.selectCoffeeCount = function(count, amount) {
    window.selectedCoffeeCount = count;
    window.selectedCoffeeAmount = amount;

    const pills = document.querySelectorAll(".coffee-pill");
    pills.forEach(p => {
        const c = parseInt(p.getAttribute("data-count"), 10);
        if (c === count) {
            p.className = "coffee-pill w-9 h-9 sm:w-10 sm:h-10 rounded-full font-black text-xs sm:text-sm flex items-center justify-center transition cursor-pointer shadow-xs bg-teal-500 text-white shadow-teal-500/25 ring-2 ring-teal-400";
        } else {
            p.className = "coffee-pill w-9 h-9 sm:w-10 sm:h-10 rounded-full font-black text-xs sm:text-sm flex items-center justify-center transition cursor-pointer shadow-xs bg-white text-slate-700 border border-slate-200 hover:border-teal-400 hover:text-teal-700";
        }
    });

    const displayEl = document.getElementById("coffeeAmountDisplay");
    if (displayEl) displayEl.textContent = amount;
};

// Live candidate emotional reviews & shoutouts rotating every 60-90 seconds
const LIVE_CANDIDATE_SHOUTOUTS = [
    {
        emotion: "Relieved & Hired",
        quote: "Finally escaped third-party broker loops! Applied directly on Greenhouse and landed an SDE-2 interview in 48 hours.",
        author: "Vikram M., Bengaluru",
        time: "Just now"
    },
    {
        emotion: "Grateful & Amazed",
        quote: "Found a stealth AI startup posting on Ashby that wasn't indexed anywhere else. Got hired as founding engineer!",
        author: "Elena R., Berlin",
        time: "1m ago"
    },
    {
        emotion: "Victorious & Empowered",
        quote: "Zero recruiter spread means I negotiated for my true worth. Signed for 32 LPA directly with company HR.",
        author: "Siddharth K., Hyderabad",
        time: "2m ago"
    },
    {
        emotion: "Thrilled & Inspired",
        quote: "The direct company application portals bypass ghost job listings completely. Bought 5 coffees gladly!",
        author: "Marcus Chen, Singapore",
        time: "3m ago"
    },
    {
        emotion: "Excited & Confident",
        quote: "Direct Lever application got me a reply within 24 hours. No consultants, no fake promises, just straight results.",
        author: "Ananya D., Pune",
        time: "4m ago"
    },
    {
        emotion: "Thankful & Relieved",
        quote: "Cleanest job hunt experience ever. The transparent package brackets gave me total clarity during negotiations.",
        author: "David O., London",
        time: "5m ago"
    },
    {
        emotion: "Joyful & Appreciative",
        quote: "Referred three of my colleagues already. This is exactly what the tech hiring market needed.",
        author: "Kavitha S., Chennai",
        time: "6m ago"
    }
];

let _liveReviewIndex = 0;
let _liveReviewTimer = null;

window.rotateLiveReview = function() {
    const card = document.getElementById("miniLiveReviewCard");
    const emotionEl = document.getElementById("liveReviewEmotion");
    const quoteEl = document.getElementById("liveReviewQuote");
    const authorEl = document.getElementById("liveReviewAuthor");
    const timeEl = document.getElementById("liveReviewTime");
    if (!card || !quoteEl) return;

    _liveReviewIndex = (_liveReviewIndex + 1) % LIVE_CANDIDATE_SHOUTOUTS.length;
    const item = LIVE_CANDIDATE_SHOUTOUTS[_liveReviewIndex];

    card.classList.add("opacity-40", "scale-[0.99]");
    setTimeout(() => {
        if (emotionEl) emotionEl.textContent = item.emotion;
        if (quoteEl) quoteEl.textContent = `"${item.quote}"`;
        if (authorEl) authorEl.textContent = `— ${item.author}`;
        if (timeEl) timeEl.textContent = item.time;
        card.classList.remove("opacity-40", "scale-[0.99]");
    }, 250);
};

window.startLiveReviewTicker = function() {
    if (_liveReviewTimer) return;
    _liveReviewTimer = setInterval(window.rotateLiveReview, 60000);
};

window.fetchRecentContributions = async function() {
    try {
        const resp = await fetch("/api/contributions/recent");
        if (!resp.ok) return;
        const data = await resp.json();
        const contributions = data.contributions || [];
        const container = document.getElementById("recentSupportersList");
        if (!container || !contributions.length) return;

        const existingDynamic = container.querySelectorAll(".dynamic-supporter-card");
        existingDynamic.forEach(el => el.remove());

        contributions.forEach(item => {
            if (!item.supporter_name && !item.supporter_message) return;
            const card = document.createElement("div");
            card.className = "dynamic-supporter-card p-3.5 rounded-2xl bg-teal-50/70 border border-teal-200/90 space-y-2 animate-in fade-in duration-300";
            
            const initials = (item.supporter_name || "Supporter").split(" ").map(w => w[0]).join("").toUpperCase().substring(0, 2) || "☕";
            const safeName = (item.supporter_name || "Generous Supporter").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const safeMsg = (item.supporter_message || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const safeReply = (item.admin_reply || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const amt = item.amount_inr || 485;

            card.innerHTML = `
                <div class="flex items-center justify-between text-xs">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-7 h-7 rounded-full bg-teal-200 text-teal-900 flex items-center justify-center font-black text-xs">
                            ${initials}
                        </div>
                        <div>
                            <div class="flex items-center gap-1.5">
                                <strong class="text-slate-900 font-extrabold text-xs">${safeName}</strong>
                                <span class="text-teal-800 text-[11px] font-semibold">contributed ₹${amt}</span>
                            </div>
                        </div>
                    </div>
                    <span class="text-[10px] text-teal-700 font-medium">Verified Supporter</span>
                </div>
                ${safeMsg ? `<div class="p-2.5 bg-white rounded-xl border border-teal-100 text-xs text-slate-800 font-medium leading-relaxed">"${safeMsg}"</div>` : ''}
                ${safeReply ? `
                <div class="mt-2 p-2.5 bg-amber-50 rounded-xl border border-amber-200 text-xs space-y-1">
                    <div class="flex items-center gap-1.5 font-bold text-amber-900 text-[11px]">
                        <span>🌰 Almond Jobs Founder</span>
                        <span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-200 text-amber-900 font-extrabold uppercase">Official Response</span>
                    </div>
                    <p class="text-slate-800 font-medium text-[11.5px] leading-relaxed">"${safeReply}"</p>
                </div>` : ''}
            `;
            const pinned = container.firstElementChild;
            if (pinned && pinned.nextSibling) {
                container.insertBefore(card, pinned.nextSibling);
            } else {
                container.appendChild(card);
            }
        });
    } catch (e) {
        console.warn("[Contributions] Unable to load dynamic supporter reviews:", e);
    }
};

window.addSupporterToFeed = function(supporterData) {
    const container = document.getElementById("recentSupportersList");
    if (!container) return;

    const data = typeof supporterData === "object" ? supporterData : {};
    const name = data.name || "Supporter";
    const message = data.message || "";
    const amount = data.amount || 485;
    const currSym = data.currency_symbol || (data.currency === "USD" ? "$" : (data.currency === "EUR" ? "€" : (data.currency === "GBP" ? "£" : "₹")));
    const formattedAmt = data.foreign_amount ? `${currSym}${data.foreign_amount}` : `${currSym}${amount}`;
    const liveStreamed = data.liveStreamed || false;

    const card = document.createElement("div");
    card.className = "dynamic-supporter-card p-3.5 rounded-2xl " + (liveStreamed ? "bg-teal-50/90 border border-teal-300" : "bg-emerald-50 border-2 border-emerald-400") + " space-y-2 shadow-sm animate-in slide-in-from-top-2 duration-300";
    
    const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().substring(0, 2) || "☕";
    const escapeClean = (str) => String(str || "").replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c] || c));
    const safeName = escapeClean(name);
    const safeMsg = escapeClean(message || "Thank you Almond Jobs for keeping job hunting honest and broker-free!");

    card.innerHTML = `
        <div class="flex items-center justify-between text-xs">
            <div class="flex items-center space-x-2.5">
                <div class="w-7 h-7 rounded-full ${liveStreamed ? 'bg-teal-200 text-teal-950' : 'bg-emerald-200 text-emerald-950'} flex items-center justify-center font-black text-xs">
                    ${initials}
                </div>
                <div>
                    <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="text-[10px] font-black ${liveStreamed ? 'text-teal-800 bg-teal-200/80' : 'text-emerald-800 bg-emerald-200'} px-1.5 py-0.5 rounded flex items-center gap-1">
                            ${liveStreamed ? '🟢 Live' : '🎉 Just supported'}
                        </span>
                        <strong class="text-slate-900 font-extrabold text-xs">${safeName}</strong>
                        <span class="text-teal-800 text-[11px] font-semibold">contributed ${formattedAmt}</span>
                    </div>
                </div>
            </div>
            <span class="text-[10px] text-teal-700 font-bold">Just now</span>
        </div>
        <div class="p-2.5 bg-white rounded-xl border border-teal-200 text-xs text-slate-800 font-medium leading-relaxed">
            "${safeMsg}"
        </div>
    `;

    const pinned = container.firstElementChild;
    if (pinned && pinned.nextSibling) {
        container.insertBefore(card, pinned.nextSibling);
    } else {
        container.insertBefore(card, container.firstChild);
    }
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });
};

window.openContributeModal = function() {
    const modal = document.getElementById("vipPricingModal");
    if (!modal) return;
    modal.classList.remove("hidden");
    if (typeof loadRazorpaySdk === "function") loadRazorpaySdk().catch(() => {});
    const nameInput = document.getElementById("coffeeSupporterName");
    if (nameInput && window.currentCandidateUser && window.currentCandidateUser.full_name) {
        if (!nameInput.value) nameInput.value = window.currentCandidateUser.full_name;
    }
    if (typeof window.startLiveReviewTicker === "function") window.startLiveReviewTicker();
    if (typeof window.fetchRecentContributions === "function") window.fetchRecentContributions();
    if (window.lucide) lucide.createIcons();
};

window.VIP_DYNAMIC_TIERS = {
    "1m": {
        id: "1m",
        name: "1-Month VIP Pass",
        title: "1-Month VIP Pass",
        duration_days: 30,
        inr_price: 699, inr_original: 699,
        usd_price: 19.99, usd_original: 19.99,
        eur_price: 18.99, eur_original: 18.99,
        gbp_price: 15.99, gbp_original: 15.99,
        discount_pct: 0,
        discount_label: "",
        badge_text: "Standard VIP"
    },
    "3m": {
        id: "3m",
        name: "3-Month Career Sprint Pass",
        title: "3-Month Career Sprint",
        duration_days: 90,
        inr_price: 1799, inr_original: 2599,
        usd_price: 49.99, usd_original: 71.99,
        eur_price: 46.99, eur_original: 67.99,
        gbp_price: 39.99, gbp_original: 57.99,
        discount_pct: 30,
        discount_label: "30% OFF Limited Offer",
        badge_text: "Career Sprint"
    },
    "6m": {
        id: "6m",
        name: "6-Month Career Dominance Pass",
        title: "6-Month Career Dominance",
        duration_days: 180,
        inr_price: 2799, inr_original: 4399,
        usd_price: 79.99, usd_original: 124.99,
        eur_price: 74.99, eur_original: 116.99,
        gbp_price: 64.99, gbp_original: 99.99,
        discount_pct: 35,
        discount_label: "35% OFF Limited Offer",
        badge_text: "Best Value"
    }
};

window.VIP_UPGRADE_TIERS = window.VIP_DYNAMIC_TIERS;

window.selectedVipPurchaseTierKey = "3m";
window.selectedVipCurrency = "INR";
window.selectedVipUpgradeTierKey = "3m";
window.selectedVipUpgradeCurrency = "INR";
window.selectedCoffeeCurrency = "INR";

window.getUserLocationCurrency = function() {
    try {
        // 1. Check server-side injected Cloudflare CF-IPCountry meta tag (real network IP)
        const serverMeta = document.querySelector('meta[name="server-geo-currency"]');
        if (serverMeta && serverMeta.content && ["INR", "USD", "EUR", "GBP"].includes(serverMeta.content.toUpperCase())) {
            return serverMeta.content.toUpperCase();
        }

        // 2. Explicit manual user override in current session
        const manualOverride = sessionStorage.getItem("almond_user_manual_currency");
        if (manualOverride && ["INR", "USD", "EUR", "GBP"].includes(manualOverride.toUpperCase())) {
            return manualOverride.toUpperCase();
        }

        // 3. Fallback to client environment heuristics
        let tz = "";
        try {
            tz = (Intl.DateTimeFormat().resolvedOptions().timeZone || "").toLowerCase();
        } catch (e) {}

        const languages = navigator.languages || [navigator.language || ""];
        const primaryLang = (languages[0] || "").toLowerCase();

        // United Kingdom detection
        if (tz.includes("london") || tz.includes("belfast") || primaryLang === "en-gb") {
            return "GBP";
        }

        // European Union / Netherlands detection
        if (
            tz.startsWith("europe/") ||
            tz.includes("amsterdam") ||
            tz.includes("berlin") ||
            tz.includes("paris") ||
            ["de-", "fr-", "es-", "it-", "nl-", "pt-", "pl-", "el-", "sv-", "da-", "fi-", "nb-", "nn-"].some(code => primaryLang.startsWith(code))
        ) {
            return "EUR";
        }

        // India detection
        if (
            tz.includes("kolkata") ||
            tz.includes("calcutta") ||
            primaryLang.endsWith("-in") ||
            primaryLang === "en-in" ||
            primaryLang.startsWith("hi") ||
            primaryLang.startsWith("ta") ||
            primaryLang.startsWith("te") ||
            primaryLang.startsWith("kn")
        ) {
            return "INR";
        }

        return "USD";
    } catch (err) {
        return "INR";
    }
};

window.fetchNetworkGeoCurrency = async function() {
    try {
        // Step 1: Call internal API (powered by Cloudflare CF-IPCountry header)
        const res = await fetch("/api/geo-currency").catch(() => null);
        if (res && res.ok) {
            const data = await res.json().catch(() => null);
            if (data && data.currency && ["INR", "USD", "EUR", "GBP"].includes(data.currency.toUpperCase())) {
                const detected = data.currency.toUpperCase();
                // If user hasn't explicitly selected another currency in session, apply network IP currency
                if (!sessionStorage.getItem("almond_user_manual_currency")) {
                    window.detectAndApplyUserCurrency(detected);
                    return detected;
                }
            }
        }

        // Step 2: Zero-permission client-side IP-to-Country fallback (country.is)
        const ipRes = await fetch("https://api.country.is").catch(() => null);
        if (ipRes && ipRes.ok) {
            const ipData = await ipRes.json().catch(() => null);
            const cc = (ipData && ipData.country ? ipData.country : "").toUpperCase();
            const eurozone = ["NL", "DE", "FR", "IT", "ES", "PT", "BE", "AT", "IE", "FI", "GR", "SK", "EE", "LV", "LT", "SI", "LU", "MT", "CY"];
            let detected = "USD";
            if (cc === "IN") detected = "INR";
            else if (cc === "GB") detected = "GBP";
            else if (eurozone.includes(cc)) detected = "EUR";
            else if (cc) detected = "USD";

            if (!sessionStorage.getItem("almond_user_manual_currency")) {
                window.detectAndApplyUserCurrency(detected);
                return detected;
            }
        }
    } catch (e) {
        // Fail silently to existing heuristics
    }
    return null;
};

window.detectAndApplyUserCurrency = function(forceCurr = null) {
    const curr = (forceCurr || window.getUserLocationCurrency() || "INR").toUpperCase();
    window.selectedVipCurrency = curr;
    window.selectedVipUpgradeCurrency = curr;
    window.selectedCoffeeCurrency = curr;

    const locNames = {
        INR: { flag: "🇮🇳", label: "INR (India)", sym: "₹" },
        USD: { flag: "🇺🇸", label: "USD (United States / Global)", sym: "$" },
        EUR: { flag: "🇪🇺", label: "EUR (Europe)", sym: "€" },
        GBP: { flag: "🇬🇧", label: "GBP (United Kingdom)", sym: "£" }
    };
    const info = locNames[curr] || locNames.USD;

    const vipBadge = document.getElementById("vipLocationCurrencyBadge");
    if (vipBadge) vipBadge.textContent = `${info.flag} Billing in ${info.label}`;

    const coffeeBadge = document.getElementById("coffeeLocationCurrencyBadge");
    if (coffeeBadge) coffeeBadge.textContent = `${info.flag} ${info.label}`;

    const vipUpBadge = document.getElementById("vipUpgradeLocationBadge");
    if (vipUpBadge) vipUpBadge.textContent = `${info.flag} Billing in ${info.label}`;
    if (typeof window.updateVipUpgradeLabels === "function") window.updateVipUpgradeLabels();

    ["INR", "USD", "EUR", "GBP"].forEach(c => {
        const vipBtn = document.getElementById("vipCurrBtn_" + c);
        if (vipBtn) {
            vipBtn.className = (c === curr)
                ? "vip-curr-tab px-2.5 py-1 rounded-lg bg-white text-slate-950 font-bold cursor-pointer"
                : "vip-curr-tab px-2.5 py-1 rounded-lg text-zinc-300 hover:text-white cursor-pointer";
        }
        const upBtn = document.getElementById("vipUpCurrBtn_" + c);
        if (upBtn) {
            upBtn.className = (c === curr)
                ? "vip-up-curr-tab px-2 py-0.5 rounded-lg bg-amber-400 text-slate-950 font-black cursor-pointer"
                : "vip-up-curr-tab px-2 py-0.5 rounded-lg text-slate-300 hover:text-white cursor-pointer";
        }
        const coffeeBtn = document.getElementById("coffeeCurrBtn_" + c);
        if (coffeeBtn) {
            coffeeBtn.className = (c === curr)
                ? "coffee-curr-tab py-2 rounded-xl bg-teal-500 text-white shadow-xs cursor-pointer transition font-black"
                : "coffee-curr-tab py-2 rounded-xl text-slate-700 hover:text-slate-950 cursor-pointer transition font-bold";
        }
    });

    if (typeof window.updateVipPurchaseCardsUI === "function") window.updateVipPurchaseCardsUI();
    if (typeof window.updateVipUpgradeLabels === "function") window.updateVipUpgradeLabels();
    if (typeof window.updateCoffeeCheckoutPrice === "function") window.updateCoffeeCheckoutPrice();
};

window.toggleVipCurrencyRow = function() {
    const row = document.getElementById("vipCurrencySelectorRow");
    if (!row) return;
    row.classList.toggle("hidden");
};

window.toggleCoffeeCurrencyRow = function() {
    const row = document.getElementById("coffeeCurrencySelectorRow");
    if (!row) return;
    row.classList.toggle("hidden");
};

window.getCurrencySymbol = function(curr) {
    if (curr === "USD") return "$";
    if (curr === "EUR") return "€";
    if (curr === "GBP") return "£";
    return "₹";
};

window.fetchLivePricing = async function() {
    try {
        const resp = await fetch("/api/pricing");
        const data = await resp.json();
        if (data && data.success && data.tiers) {
            window.VIP_DYNAMIC_TIERS = data.tiers;
            window.VIP_UPGRADE_TIERS = data.tiers;
            if (typeof window.updateVipPurchaseCardsUI === "function") window.updateVipPurchaseCardsUI();
            if (typeof window.updateVipUpgradeLabels === "function") window.updateVipUpgradeLabels();
        }
    } catch (e) {
        console.warn("[Pricing] Using fallback pricing config:", e);
    }
};

window.selectVipPurchaseTier = function(tierKey) {
    window.selectedVipPurchaseTierKey = tierKey || "3m";
    const cards = {
        "1m": document.getElementById("vipPurchaseCard_1m"),
        "3m": document.getElementById("vipPurchaseCard_3m"),
        "6m": document.getElementById("vipPurchaseCard_6m")
    };
    
    Object.keys(cards).forEach(function(key) {
        const card = cards[key];
        if (!card) return;
        if (key === window.selectedVipPurchaseTierKey) {
            card.className = "vip-tier-card p-4 rounded-2xl bg-slate-950 border-2 border-amber-400 cursor-pointer transition relative space-y-2 flex flex-col justify-between shadow-md";
            const titleEl = card.querySelector(".text-sm");
            if (titleEl) titleEl.className = "text-sm font-extrabold text-white";
            const priceEl = card.querySelector("[id^='vipCardPrice_']");
            if (priceEl) priceEl.className = "text-2xl font-black text-amber-400";
            const descEl = card.querySelector("p");
            if (descEl) descEl.className = "text-[11px] text-slate-300 leading-tight pt-1 border-t border-slate-800";
        } else {
            card.className = "vip-tier-card p-4 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 cursor-pointer transition relative space-y-2 flex flex-col justify-between shadow-xs";
            const titleEl = card.querySelector(".text-sm");
            if (titleEl) titleEl.className = "text-sm font-extrabold text-slate-900";
            const priceEl = card.querySelector("[id^='vipCardPrice_']");
            if (priceEl) priceEl.className = "text-2xl font-black text-slate-900";
            const descEl = card.querySelector("p");
            if (descEl) descEl.className = "text-[11px] text-slate-500 leading-tight pt-1 border-t border-slate-100";
        }
    });

    if (typeof window.updateVipPurchaseCardsUI === "function") window.updateVipPurchaseCardsUI();
};

window.selectVipCurrency = function(curr) {
    curr = (curr || "INR").toUpperCase();
    localStorage.setItem("almond_user_preferred_currency", curr);
    window.detectAndApplyUserCurrency(curr);
};

window.computePerMonthPrice = function(totalPrice, monthsCount, curr) {
    const num = Number(totalPrice) || 0;
    const m = Math.max(1, Number(monthsCount) || 1);
    const val = num / m;
    if ((curr || "INR").toUpperCase() === "INR") {
        return String(Math.floor(val));
    }
    return val.toFixed(2);
};

window.updateVipPurchaseCardsUI = function() {
    const curr = window.selectedVipCurrency || "INR";
    const sym = window.getCurrencySymbol(curr);
    const tiers = window.VIP_DYNAMIC_TIERS || {};

    const t1 = tiers["1m"] || {};
    const t3 = tiers["3m"] || {};
    const t6 = tiers["6m"] || {};

    // 1m
    const p1 = curr === "INR" ? (t1.inr_price || 699) : (t1[`${curr.toLowerCase()}_price`] || t1.usd_price || 19.99);
    const pm1 = window.computePerMonthPrice(p1, 1, curr);
    const price1El = document.getElementById("vipCardPrice_1m");
    if (price1El) price1El.textContent = `${sym}${pm1}/mo`;

    // 3m
    const p3 = curr === "INR" ? (t3.inr_price || 1799) : (t3[`${curr.toLowerCase()}_price`] || t3.usd_price || 49.99);
    const pm3 = window.computePerMonthPrice(p3, 3, curr);
    const o3 = curr === "INR" ? (t3.inr_original || 2599) : (t3[`${curr.toLowerCase()}_original`] || t3.usd_original || 69.99);
    const price3El = document.getElementById("vipCardPrice_3m");
    const orig3El = document.getElementById("vipCardOriginal_3m");
    const badge3El = document.getElementById("vipBadge_3m");
    if (price3El) price3El.textContent = `${sym}${pm3}/mo`;
    if (orig3El) orig3El.textContent = `${sym}${pm1}/mo`;
    if (badge3El && t3.discount_pct) badge3El.textContent = `${t3.discount_pct}% OFF`;

    // 6m
    const p6 = curr === "INR" ? (t6.inr_price || 2799) : (t6[`${curr.toLowerCase()}_price`] || t6.usd_price || 79.99);
    const pm6 = window.computePerMonthPrice(p6, 6, curr);
    const o6 = curr === "INR" ? (t6.inr_original || 4299) : (t6[`${curr.toLowerCase()}_original`] || t6.usd_original || 119.99);
    const price6El = document.getElementById("vipCardPrice_6m");
    const orig6El = document.getElementById("vipCardOriginal_6m");
    const badge6El = document.getElementById("vipBadge_6m");
    if (price6El) price6El.textContent = `${sym}${pm6}/mo`;
    if (orig6El) orig6El.textContent = `${sym}${pm1}/mo`;
    if (badge6El && t6.discount_pct) badge6El.textContent = `${t6.discount_pct}% OFF`;

    // Primary CTA Button & 2-Column Pro Header (per-month like ChatGPT/Gemini; full total appears at Razorpay checkout)
    const selTierKey = window.selectedVipPurchaseTierKey || "3m";
    const selData = tiers[selTierKey] || t3;
    const selMonths = selTierKey === "1m" ? 1 : (selTierKey === "6m" ? 6 : 3);
    const selPrice = curr === "INR" ? (selData.inr_price || (selMonths === 1 ? 699 : (selMonths === 6 ? 2799 : 1799))) : (selData[`${curr.toLowerCase()}_price`] || selData.usd_price || (selMonths === 1 ? 19.99 : (selMonths === 6 ? 79.99 : 49.99)));
    const selPerMonth = window.computePerMonthPrice(selPrice, selMonths, curr);

    const btnLabel = document.getElementById("vipPassCheckoutBtnLabel");
    if (btnLabel) {
        btnLabel.textContent = `⚡ Continue with ${selData.name || "Pro"} — ${sym}${selPerMonth}/mo`;
    }

    // Sync 2-Column Editorial SaaS Matrix elements
    const pills = {
        "1m": document.getElementById("proTierPill_1m"),
        "3m": document.getElementById("proTierPill_3m"),
        "6m": document.getElementById("proTierPill_6m")
    };
    Object.keys(pills).forEach(k => {
        const pill = pills[k];
        if (!pill) return;
        const base = k === "1m"
            ? "pro-tier-pill px-3.5 py-2 rounded-lg text-xs font-semibold cursor-pointer transition"
            : "pro-tier-pill px-3.5 py-2 rounded-lg text-xs font-semibold cursor-pointer transition flex items-center gap-1.5";
        if (k === selTierKey) {
            pill.className = `${base} bg-white text-slate-950 shadow-xs`;
        } else {
            pill.className = `${base} text-zinc-400 hover:text-white`;
        }
    });

    const proPriceDisplay = document.getElementById("proCheckoutPriceDisplay");
    if (proPriceDisplay) proPriceDisplay.textContent = `${sym}${selPerMonth}`;

    const proPriceLabel = document.getElementById("proCheckoutPriceLabel");
    if (proPriceLabel) proPriceLabel.textContent = `${sym}${selPerMonth}/mo`;

    const proOrigPrice = document.getElementById("vipCardOriginalPrice");
    if (proOrigPrice) {
        if (selMonths > 1 && Number(pm1) > Number(selPerMonth)) {
            proOrigPrice.textContent = `${sym}${pm1}/mo`;
            proOrigPrice.classList.remove("hidden");
        } else {
            proOrigPrice.classList.add("hidden");
        }
    }

    const proDurationLabel = document.getElementById("proCheckoutDurationLabel");
    if (proDurationLabel) {
        proDurationLabel.textContent = "/ mo";
    }

    const proBillingNote = document.getElementById("proCheckoutBillingNote");
    if (proBillingNote) {
        if (selMonths === 1) proBillingNote.textContent = "Billed monthly • 30 days full direct access";
        else if (selMonths === 6) proBillingNote.textContent = "Billed every 6 months • 180 days access";
        else proBillingNote.textContent = "Billed every 3 months • 90 days access";
    }

    const proSavingsNote = document.getElementById("proCheckoutSavingsNote");
    if (proSavingsNote) {
        if (selMonths === 1) {
            proSavingsNote.textContent = "Flexible 30-day direct portal pass";
            proSavingsNote.className = "text-[11px] text-zinc-400 font-medium mt-0.5";
        } else {
            const fullMonthlySum = Number(p1) * selMonths;
            const savingsRaw = Math.max(0, fullMonthlySum - Number(selPrice));
            const savingsDisp = curr === "INR" ? Math.round(savingsRaw).toLocaleString("en-IN") : savingsRaw.toFixed(2);
            const pctLabel = selMonths === 6 ? "35%" : "30%";
            proSavingsNote.textContent = savingsRaw > 0
                ? `Save ${sym}${savingsDisp} (${pctLabel} off vs monthly)`
                : `Save ${pctLabel} vs monthly plan`;
            proSavingsNote.className = "text-[11px] text-emerald-400 font-medium mt-0.5";
        }
    }

    const pillPrice1m = document.getElementById("vipPillPrice_1m");
    if (pillPrice1m) pillPrice1m.textContent = `${sym}${pm1}/mo`;
};

window.almondAiQuota = { limit: 10, pitch_remaining: 10, cover_letter_remaining: 10, unlimited: false };

window.syncAiQuotaDisplay = function() {
    const q = window.almondAiQuota || {};
    const loggedIn = isUserLoggedIn();
    const paid = isUserPaid() || Boolean(q.unlimited);
    const bar = document.getElementById("omniAiQuotaBar");
    const pitchLeft = typeof q.pitch_remaining === "number" ? q.pitch_remaining : 10;
    const clLeft = typeof q.cover_letter_remaining === "number" ? q.cover_letter_remaining : 10;
    const lim = q.limit || 10;

    if (bar) {
        if (loggedIn && !paid) {
            bar.classList.remove("hidden");
            const pEl = document.getElementById("omniPitchLeftVal");
            const cEl = document.getElementById("omniClLeftVal");
            if (pEl) pEl.textContent = String(pitchLeft);
            if (cEl) cEl.textContent = String(clLeft);
        } else {
            bar.classList.add("hidden");
        }
    }

    const updateModalBadge = (elId, rem) => {
        const el = document.getElementById(elId);
        if (!el) return;
        if (!loggedIn) {
            el.classList.add("hidden");
            return;
        }
        el.classList.remove("hidden");
        if (paid) {
            el.textContent = "Pro • Unlimited";
            el.className = "px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200";
        } else {
            el.textContent = `${rem} of ${lim} free left`;
            el.className = rem <= 2
                ? "px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200"
                : "px-2 py-0.5 rounded-full text-[10px] font-bold bg-violet-100 text-violet-800 border border-violet-200";
        }
    };
    updateModalBadge("pitchModalQuotaBadge", pitchLeft);
    updateModalBadge("coverLetterQuotaBadge", clLeft);

    document.querySelectorAll(".omni-pitch-count-pill").forEach(el => {
        if (loggedIn && !paid) {
            el.textContent = `(${pitchLeft}/${lim})`;
            el.classList.remove("hidden");
        } else {
            el.classList.add("hidden");
        }
    });
    document.querySelectorAll(".omni-cl-count-pill").forEach(el => {
        if (loggedIn && !paid) {
            el.textContent = `(${clLeft}/${lim})`;
            el.classList.remove("hidden");
        } else {
            el.classList.add("hidden");
        }
    });
};

window.fetchAiQuotaStatus = async function() {
    if (!isUserLoggedIn()) {
        window.syncAiQuotaDisplay();
        return;
    }
    try {
        const uid = getCandidateUserId();
        const resp = await fetch(`/api/ai-quota?user_id=${encodeURIComponent(uid || "")}`);
        if (!resp.ok) return;
        const data = await resp.json().catch(() => ({}));
        if (data.status === "success") {
            window.almondAiQuota = {
                limit: data.limit || 10,
                pitch_remaining: typeof data.pitch_remaining === "number" ? data.pitch_remaining : 10,
                cover_letter_remaining: typeof data.cover_letter_remaining === "number" ? data.cover_letter_remaining : 10,
                unlimited: Boolean(data.unlimited || data.is_paid)
            };
            window.syncAiQuotaDisplay();
        }
    } catch (_) {}
};

window.openProFeatureGateModal = function(featureLabel = "This feature", description = "") {
    const modal = document.getElementById("proFeatureGateModal");
    if (!modal) {
        window.openVipPassModal();
        return;
    }
    const titleEl = document.getElementById("proGateModalTitle");
    const descEl = document.getElementById("proGateModalDesc");
    if (titleEl) titleEl.textContent = `${featureLabel} is locked on the Free plan`;
    if (descEl) {
        descEl.textContent = description || "Downloading matched jobs as PDF, CSV Sheet, or Word reports is locked on the Free plan. Upgrade to Almond Jobs Pro to unlock exports, unlimited AI career tools, and today's fresh openings.";
    }
    modal.classList.remove("hidden");
    modal.style.display = "flex";
};

window.closeProFeatureGateModal = function() {
    const modal = document.getElementById("proFeatureGateModal");
    if (!modal) return;
    modal.classList.add("hidden");
    modal.style.display = "none";
};

window.proceedFromGateToPricing = function() {
    window.closeProFeatureGateModal();
    if (typeof window.openVipPassModal === "function") window.openVipPassModal();
};

window.openUpgradeModal = function() {
    window.openVipPassModal();
};

window.closeUpgradeModal = function() {
    window.closeVipPassModal();
};

window.executeVipPassCheckout = function() {
    const selTierKey = window.selectedVipPurchaseTierKey || "3m";
    const curr = window.selectedVipCurrency || "INR";
    const tiers = window.VIP_DYNAMIC_TIERS || {};
    const tierData = tiers[selTierKey] || {};
    const sym = window.getCurrencySymbol(curr);

    const price = curr === "INR" ? (tierData.inr_price || 1799) : (tierData[`${curr.toLowerCase()}_price`] || tierData.usd_price || 49.99);
    const inrAmount = tierData.inr_price || (selTierKey === "1m" ? 699 : (selTierKey === "6m" ? 2799 : 1799));
    const planTitle = `Almond Jobs ${tierData.name || "VIP Pass"} (${sym}${price})`;

    if (typeof triggerRazorpayCheckout === "function") {
        triggerRazorpayCheckout(inrAmount, planTitle, {
            purchaseType: "vip_pass",
            plan_tier: selTierKey,
            currency: curr,
            currency_symbol: sym,
            foreign_amount: price,
            display_price: `${sym}${price}`
        });
    } else {
        alert("Payment gateway is initializing. Please try again in 2 seconds.");
    }
};

window.selectVipUpgradeTier = function(tierKey) {
    window.selectedVipUpgradeTierKey = tierKey || "3m";
    const card1m = document.getElementById("vipUpgradeCard_1m");
    const card3m = document.getElementById("vipUpgradeCard_3m");
    const card6m = document.getElementById("vipUpgradeCard_6m");

    if (card1m) {
        card1m.className = (tierKey === "1m")
            ? "vip-up-card p-3 rounded-2xl bg-slate-800 hover:bg-slate-750 border-2 border-emerald-400 cursor-pointer transition relative space-y-1.5 shadow-md shadow-emerald-900/30"
            : "vip-up-card p-3 rounded-2xl bg-slate-800/40 hover:bg-slate-800 border-2 border-slate-700 cursor-pointer transition relative space-y-1.5 opacity-80 hover:opacity-100";
    }
    if (card3m) {
        card3m.className = (tierKey === "3m")
            ? "vip-up-card p-3 rounded-2xl bg-slate-800 hover:bg-slate-750 border-2 border-amber-400 cursor-pointer transition relative space-y-1.5 shadow-md shadow-amber-900/30"
            : "vip-up-card p-3 rounded-2xl bg-slate-800/40 hover:bg-slate-800 border-2 border-slate-700 cursor-pointer transition relative space-y-1.5 opacity-80 hover:opacity-100";
    }
    if (card6m) {
        card6m.className = (tierKey === "6m")
            ? "vip-up-card p-3 rounded-2xl bg-slate-800 hover:bg-slate-750 border-2 border-violet-400 cursor-pointer transition relative space-y-1.5 shadow-md shadow-violet-900/30"
            : "vip-up-card p-3 rounded-2xl bg-slate-800/40 hover:bg-slate-800 border-2 border-slate-700 cursor-pointer transition relative space-y-1.5 opacity-80 hover:opacity-100";
    }
    if (typeof window.updateVipUpgradeLabels === "function") window.updateVipUpgradeLabels();
};

window.selectVipUpgradeCurrency = function(curr) {
    window.selectedVipUpgradeCurrency = curr || "INR";
    const tabs = document.querySelectorAll(".vip-up-curr-tab");
    tabs.forEach(function(btn) {
        const isSel = btn.id === ("vipUpCurrBtn_" + curr);
        btn.className = isSel
            ? "vip-up-curr-tab px-2 py-0.5 rounded-lg bg-amber-400 text-slate-950 font-black cursor-pointer"
            : "vip-up-curr-tab px-2 py-0.5 rounded-lg text-slate-300 hover:text-white cursor-pointer";
    });
    if (typeof window.updateVipUpgradeLabels === "function") window.updateVipUpgradeLabels();
};

window.toggleVipUpgradeCurrencySelector = function() {
    const dropdown = document.getElementById("vipUpgradeCurrencyDropdown");
    if (dropdown) {
        dropdown.classList.toggle("hidden");
    }
};

window.updateVipUpgradeLabels = function() {
    const curr = (window.selectedVipUpgradeCurrency || window.selectedVipCurrency || window.getUserLocationCurrency() || "INR").toUpperCase();
    window.selectedVipUpgradeCurrency = curr;
    const sym = window.getCurrencySymbol(curr);
    const tiers = window.VIP_DYNAMIC_TIERS || {};
    const t1 = tiers["1m"] || {};
    const t3 = tiers["3m"] || {};
    const t6 = tiers["6m"] || {};

    // 1. Update location badge
    const locNames = {
        INR: { flag: "🇮🇳", label: "INR (India)" },
        USD: { flag: "🇺🇸", label: "USD (United States / Global)" },
        EUR: { flag: "🇪🇺", label: "EUR (Europe)" },
        GBP: { flag: "🇬🇧", label: "GBP (United Kingdom)" }
    };
    const info = locNames[curr] || locNames.USD;
    const vipUpBadge = document.getElementById("vipUpgradeLocationBadge");
    if (vipUpBadge) vipUpBadge.textContent = `${info.flag} Billing in ${info.label}`;

    // 2. Active Tab styling
    ["INR", "USD", "EUR", "GBP"].forEach(function(c) {
        const btn = document.getElementById("vipUpCurrBtn_" + c);
        if (btn) {
            btn.className = (c === curr)
                ? "vip-up-curr-tab px-2.5 py-1 rounded-lg bg-amber-400 text-slate-950 font-black cursor-pointer shadow-xs"
                : "vip-up-curr-tab px-2.5 py-1 rounded-lg text-slate-300 hover:text-white cursor-pointer";
        }
    });

    // 3. Prices and Original MRPs (display per-month rate in modal cards; full total shown at Razorpay checkout)
    const p1 = curr === "INR" ? (t1.inr_price || 699) : (t1[`${curr.toLowerCase()}_price`] || t1.usd_price || 19.99);
    const pm1 = window.computePerMonthPrice(p1, 1, curr);

    const p3 = curr === "INR" ? (t3.inr_price || 1799) : (t3[`${curr.toLowerCase()}_price`] || t3.usd_price || 49.99);
    const pm3 = window.computePerMonthPrice(p3, 3, curr);

    const p6 = curr === "INR" ? (t6.inr_price || 2799) : (t6[`${curr.toLowerCase()}_price`] || t6.usd_price || 79.99);
    const pm6 = window.computePerMonthPrice(p6, 6, curr);

    const price1mEl = document.getElementById("vipUpgradePrice_1m");
    if (price1mEl) price1mEl.textContent = `${sym}${pm1}/mo`;

    const price3mEl = document.getElementById("vipUpgradePrice_3m");
    const orig3mEl = document.getElementById("vipUpgradeOriginalPrice_3m");
    const badge3mEl = document.getElementById("vipUpgradeDiscountBadge_3m");
    if (price3mEl) price3mEl.textContent = `${sym}${pm3}/mo`;
    if (orig3mEl) orig3mEl.textContent = `${sym}${pm1}/mo`;
    if (badge3mEl) badge3mEl.textContent = "30% OFF";

    const price6mEl = document.getElementById("vipUpgradePrice_6m");
    const orig6mEl = document.getElementById("vipUpgradeOriginalPrice_6m");
    const badge6mEl = document.getElementById("vipUpgradeDiscountBadge_6m");
    if (price6mEl) price6mEl.textContent = `${sym}${pm6}/mo`;
    if (orig6mEl) orig6mEl.textContent = `${sym}${pm1}/mo`;
    if (badge6mEl) badge6mEl.textContent = "35% OFF";

    // 4. CTA button dynamic label
    const selTier = window.selectedVipUpgradeTierKey || "3m";
    const selMonths = selTier === "1m" ? 1 : (selTier === "6m" ? 6 : 3);
    const tierData = tiers[selTier] || (selTier === "1m" ? t1 : (selTier === "6m" ? t6 : t3));
    const selPrice = curr === "INR" ? (tierData.inr_price || (selTier === "1m" ? 699 : (selTier === "6m" ? 2799 : 1799))) : (tierData[`${curr.toLowerCase()}_price`] || tierData.usd_price || (selTier === "1m" ? 19.99 : (selTier === "6m" ? 79.99 : 49.99)));
    const selPerMonth = window.computePerMonthPrice(selPrice, selMonths, curr);

    const btnLabel = document.getElementById("vipUpgradeCheckoutBtnLabel");
    if (btnLabel) {
        let actionLabel = "3-Month Sprint";
        if (selTier === "1m") actionLabel = "1-Month Pass";
        if (selTier === "6m") actionLabel = "6-Month Dominance";
        btnLabel.textContent = `🚀 Continue: ${actionLabel} — ${sym}${selPerMonth}/mo`;
    }
};

window.executeVipUpgradeCheckout = function() {
    const tierKey = window.selectedVipUpgradeTierKey || "3m";
    const curr = window.selectedVipUpgradeCurrency || "INR";
    const tiers = window.VIP_DYNAMIC_TIERS || {};
    const tierData = tiers[tierKey] || {};
    const sym = window.getCurrencySymbol(curr);

    const price = curr === "INR" ? (tierData.inr_price || (tierKey === "1m" ? 699 : (tierKey === "6m" ? 2799 : 1799))) : (tierData[`${curr.toLowerCase()}_price`] || tierData.usd_price || (tierKey === "1m" ? 19.99 : (tierKey === "6m" ? 79.99 : 49.99)));
    const inrAmount = tierData.inr_price || (tierKey === "1m" ? 699 : (tierKey === "6m" ? 2799 : 1799));
    const planName = tierData.name || (tierKey === "1m" ? "1-Month VIP Pass" : (tierKey === "6m" ? "6-Month Dominance" : "3-Month Career Sprint"));
    const planTitle = `Almond Jobs ${planName} (${sym}${price})`;

    if (typeof triggerRazorpayCheckout === "function") {
        triggerRazorpayCheckout(inrAmount, planTitle, {
            purchaseType: "vip_upgrade",
            plan_tier: tierKey,
            currency: curr,
            currency_symbol: sym,
            foreign_amount: price,
            display_price: `${sym}${price}`
        });
    } else {
        alert("Payment gateway is initializing. Please try again in 2 seconds.");
    }
};

window.openVipPassModal = function() {
    const modal = document.getElementById("vipPassModal");
    if (!modal) return;
    if (typeof loadRazorpaySdk === "function") loadRazorpaySdk().catch(() => {});

    if (typeof window.detectAndApplyUserCurrency === "function") {
        window.detectAndApplyUserCurrency();
        if (typeof window.fetchNetworkGeoCurrency === "function") {
            window.fetchNetworkGeoCurrency();
        }
    }
    if (typeof window.fetchLivePricing === "function") window.fetchLivePricing();

    const purchaseView = document.getElementById("vipModalPurchaseView");
    const activeView = document.getElementById("vipModalActiveMemberView");
    const headerTitle = document.getElementById("vipModalHeaderTitle");
    const headerBadge = document.getElementById("vipModalHeaderBadge");
    const headerSub = document.getElementById("vipModalHeaderSubtitle");

    const paid = isUserPaid();

    if (paid) {
        if (purchaseView) purchaseView.classList.add("hidden");
        if (activeView) activeView.classList.remove("hidden");

        if (headerTitle) headerTitle.textContent = "Almond Jobs VIP Member Dashboard";
        if (headerBadge) {
            headerBadge.textContent = "Active VIP Member ✨";
            headerBadge.className = "text-[10px] font-black uppercase tracking-wider text-emerald-900 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-300";
        }
        if (headerSub) headerSub.textContent = "100% Unlocked Direct Portals • 0% Recruiter Spread";

        const planTier = (localStorage.getItem("almond_plan_tier") || localStorage.getItem("almond_plan") || "").toLowerCase();
        const remainingStr = localStorage.getItem("almond_remaining_str") || "";
        const paidUntilFormatted = localStorage.getItem("almond_paid_until_formatted") || "";

        let tierName = "1-Month VIP Pass Active";
        let tierBadge = "Active VIP Member";
        let defaultUpgradeTier = "3m";

        const card1m = document.getElementById("vipUpgradeCard_1m");
        const card3m = document.getElementById("vipUpgradeCard_3m");
        const card6m = document.getElementById("vipUpgradeCard_6m");
        if (card1m) card1m.classList.remove("hidden");
        if (card3m) card3m.classList.remove("hidden");
        if (card6m) card6m.classList.remove("hidden");

        if (planTier.includes("180") || planTier.includes("6m") || planTier.includes("6-month") || planTier.includes("dominance")) {
            tierName = "6-Month Career Dominance Pass Active";
            tierBadge = "Dominance Tier Unlocked";
            defaultUpgradeTier = "6m";
            const upTitle = document.getElementById("vipUpgradeSectionTitle");
            if (upTitle) upTitle.textContent = "Extend Career Dominance Coverage";
        } else if (planTier.includes("90") || planTier.includes("3m") || planTier.includes("3-month") || planTier.includes("sprint")) {
            tierName = "3-Month Career Sprint Pass Active";
            tierBadge = "Career Sprint Unlocked";
            defaultUpgradeTier = "6m";
            const upTitle = document.getElementById("vipUpgradeSectionTitle");
            if (upTitle) upTitle.textContent = "Upgrade to 6-Month Dominance or Extend Sprint";
        } else {
            tierName = "1-Month VIP Pass Active";
            tierBadge = "Standard VIP Active";
            defaultUpgradeTier = "3m";
            const upTitle = document.getElementById("vipUpgradeSectionTitle");
            if (upTitle) upTitle.textContent = "Continuous Career Coverage (1m, 3m, or 6m)";
        }

        const planBadgeEl = document.getElementById("vipActiveMemberPlanBadge");
        if (planBadgeEl) planBadgeEl.textContent = tierBadge;

        const planTitleEl = document.getElementById("vipActiveMemberPlanTitle");
        if (planTitleEl) planTitleEl.textContent = tierName;

        const expiryEl = document.getElementById("vipActiveMemberExpiryDetail");
        if (expiryEl) {
            let detail = "Direct Corporate Ingestion Active";
            if (paidUntilFormatted && remainingStr) {
                detail = `Valid until ${paidUntilFormatted} • ${remainingStr}`;
            } else if (remainingStr) {
                detail = `Valid • ${remainingStr}`;
            } else if (paidUntilFormatted) {
                detail = `Valid until ${paidUntilFormatted}`;
            }
            expiryEl.textContent = detail;
        }

        window.selectVipUpgradeTier(defaultUpgradeTier);
    } else {
        if (purchaseView) purchaseView.classList.remove("hidden");
        if (activeView) activeView.classList.add("hidden");

        if (headerTitle) headerTitle.textContent = "Almond Jobs Pro";
        if (headerBadge) {
            headerBadge.textContent = "Direct Company Feeds";
            headerBadge.className = "text-[10px] font-semibold text-zinc-300 bg-white/8 px-2 py-0.5 rounded-full border border-white/10";
        }
        if (headerSub) headerSub.textContent = "Direct Company Ingestion • Apply before public platforms saturate the applicant pool";

        window.selectVipPurchaseTier("6m");
        if (typeof window.updateVipPurchaseCardsUI === "function") window.updateVipPurchaseCardsUI();
    }

    modal.classList.remove("hidden");
    modal.style.display = "flex";
    if (window.lucide) lucide.createIcons();
};

window.closeVipPassModal = function() {
    const modal = document.getElementById("vipPassModal");
    if (!modal) return;
    modal.classList.add("hidden");
    modal.style.display = "none";
};

window.openVipPricingModal = function() {
    window.openVipPassModal();
};

window.executeCoffeeContribution = function() {
    const amount = window.selectedCoffeeAmount || 485;
    const count = window.selectedCoffeeCount || 1;
    const name = (document.getElementById("coffeeSupporterName")?.value || "").trim() || "Generous Candidate";
    const message = (document.getElementById("coffeeSupporterMessage")?.value || "").trim();

    const planTitle = `Buy Almond Jobs ${count} Coffee${count > 1 ? 's' : ''}`;

    if (typeof triggerRazorpayCheckout === "function") {
        triggerRazorpayCheckout(amount, planTitle, {
            purchaseType: "contribution",
            supporterName: name,
            supporterMessage: message
        });
    }
};



// Candidate Profile Placeholder Modal

// --- CANDIDATE AUTHENTICATION & PROFILE CONTROLLER ---
window.activeAuthTab = 'signup';
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

    const confirmPassField = document.getElementById("signupConfirmPasswordField");
    const passInput = document.getElementById("authPasswordInput");
    if (tab === 'signup') {
        if (passInput) passInput.setAttribute("autocomplete", "new-password");
        if (tabLogin) tabLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg transition-all text-slate-600 hover:text-slate-950 cursor-pointer";
        if (tabSignup) tabSignup.className = "flex-1 py-2 text-xs font-bold rounded-lg transition-all bg-white text-slate-950 shadow-xs cursor-pointer";
        if (nameField) nameField.classList.add("hidden");
        if (confirmPassField) confirmPassField.classList.add("hidden");
        if (submitBtnText) submitBtnText.textContent = "Create Free Account ?";
        if (toggleHint) toggleHint.innerHTML = `Already have an account? <button type="button" onclick="switchAuthTab('login')" class="text-violet-700 font-bold hover:underline cursor-pointer">Log in with Email</button>`;
    } else {
        if (passInput) passInput.setAttribute("autocomplete", "current-password");
        if (tabLogin) tabLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg transition-all bg-white text-slate-950 shadow-xs cursor-pointer";
        if (tabSignup) tabSignup.className = "flex-1 py-2 text-xs font-bold rounded-lg transition-all text-slate-600 hover:text-slate-950 cursor-pointer";
        if (nameField) nameField.classList.add("hidden");
        if (confirmPassField) confirmPassField.classList.add("hidden");
        if (submitBtnText) submitBtnText.textContent = "Log In to Almond Jobs";
        if (toggleHint) toggleHint.innerHTML = `Don't have an account? <button type="button" onclick="switchAuthTab('signup')" class="text-violet-700 font-bold hover:underline cursor-pointer">Sign up free</button>`;
    }
};

window.toggleAuthPasswordVisibility = function() {
    const passInput = document.getElementById("authPasswordInput");
    const toggleBtn = document.getElementById("toggleAuthPasswordBtn");
    if (!passInput || !toggleBtn) return;
    const isHidden = passInput.type === "password";
    passInput.type = isHidden ? "text" : "password";
    toggleBtn.textContent = isHidden ? "Hide" : "Show";
    toggleBtn.setAttribute("aria-pressed", isHidden ? "true" : "false");
    toggleBtn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
};

window.openSignupToUnlockLinksModal = function() {
    window.activeAuthTab = "signup";
    window.openProfileModal("signup_links");
    if (typeof window.switchAuthTab === "function") {
        window.switchAuthTab("signup");
    }
};

window.omniFeedSessionNonce = String(Date.now());

window.getUserGeoCountry = function() {
    try {
        const metaCountry = document.querySelector('meta[name="server-geo-country"]');
        const raw = (metaCountry && metaCountry.content ? metaCountry.content : "").trim();
        if (raw && raw.toUpperCase() !== "XX" && raw.toUpperCase() !== "UNKNOWN") {
            const codeMap = {
                IN: "India", US: "United States", GB: "United Kingdom", UK: "United Kingdom",
                CA: "Canada", DE: "Germany", FR: "France", NL: "Netherlands",
                SG: "Singapore", AE: "UAE", AU: "Australia", IE: "Ireland"
            };
            return codeMap[raw.toUpperCase()] || raw;
        }
        const curr = typeof window.getUserLocationCurrency === "function" ? window.getUserLocationCurrency() : "";
        if (curr === "INR") return "India";
        if (curr === "GBP") return "United Kingdom";
        if (curr === "EUR") return "Germany";
        if (curr === "USD") return "United States";
    } catch (_) {}
    return "";
};

window.refreshUnlockedFeedsAfterAuth = function() {
    try {
        if (typeof window.fetchAiQuotaStatus === "function") {
            window.fetchAiQuotaStatus();
        }
        window.omniCurrentOffset = 0;
        window.omniFeedSessionNonce = String(Date.now());
        if (typeof window.executeOmniSearch === "function" && document.getElementById("omniSearchResultsContainer")) {
            window.executeOmniSearch(window.omniCurrentQuery || "", false);
        }
        const curatedModal = document.getElementById("curatedFeedsModal");
        if (curatedModal && !curatedModal.classList.contains("hidden") && typeof loadCuratedFeeds === "function") {
            loadCuratedFeeds(false);
        }
    } catch (_) {}
};

window.renderDirectApplyActionHtml = function({ isAuthLocked, isVipLocked, safeUrl, externalLabel = "Apply Direct ↗", compact = false }) {
    if (isAuthLocked) {
        const pad = compact ? "px-3.5 py-2" : "w-full sm:w-auto px-4 py-2.5";
        return `
            <div class="flex flex-col items-end gap-1">
                <div class="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-[10px] font-mono text-slate-400 select-none" aria-hidden="true">
                    <span class="blur-[4px]">https://careers.direct-portal.com/apply</span>
                </div>
                <button type="button" onclick="openSignupToUnlockLinksModal()" class="${pad} rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-black text-xs shadow-xs flex items-center justify-center gap-1.5 cursor-pointer transition whitespace-nowrap">
                    <span>🔒</span>
                    <span>Sign Up Free to View Link</span>
                </button>
            </div>
        `;
    }
    if (isVipLocked) {
        const pad = compact ? "px-4 py-2" : "w-full sm:w-auto px-5 py-2.5";
        return `<div class="flex flex-col items-stretch sm:items-end gap-1">
            <span class="text-[10px] font-bold text-amber-800 tracking-tight whitespace-nowrap text-center sm:text-right">⚡ Apply fast &bull; Less competition</span>
            <button type="button" onclick="openUpgradeModal()" class="${pad} rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 text-slate-950 font-black text-xs shadow-xs flex items-center justify-center gap-1.5 cursor-pointer transition whitespace-nowrap">
                <span>👑</span>
                <span>Unlock with Pro</span>
            </button>
        </div>`;
    }
    const pad = compact ? "px-4 py-2" : "w-full sm:w-auto px-5 py-2.5";
    const sampleNote = (!isUserLoggedIn())
        ? `<span class="text-[10px] font-bold text-emerald-700 tracking-tight whitespace-nowrap text-center sm:text-right">? Free sample direct link</span>`
        : "";
    return `<div class="flex flex-col items-stretch sm:items-end gap-1">${sampleNote}<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="omni-apply-btn ${pad} rounded-xl bg-slate-950 hover:bg-violet-700 text-white font-extrabold text-xs shadow-xs flex items-center justify-center gap-1.5 transition whitespace-nowrap">
        <span>${externalLabel}</span>
        <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
    </a></div>`;
};

window.openProfileModal = function(contextReason = "") {
    const modal = document.getElementById("profileModal");
    if (!modal) return;

    const contextNotice = document.getElementById("authContextNotice");
    const contextText = document.getElementById("authContextNoticeText");
    if (contextNotice) {
        if (contextReason === "search_intercept" || contextReason === "signup_links") {
            if (contextText) {
                contextText.textContent = contextReason === "signup_links"
                    ? "Sign up free in seconds to unblur direct company apply links & save jobs."
                    : "Sign in or create a free candidate account to search and apply directly.";
            }
            contextNotice.classList.remove("hidden");
        } else {
            contextNotice.classList.add("hidden");
        }
    }

    const welcomeView = document.getElementById("authWelcomeView");
    if (welcomeView) welcomeView.classList.add("hidden");
    const authFormView = document.getElementById("authFormView");
    const authProfileView = document.getElementById("authProfileView");
    const modalTitle = document.getElementById("modalTitleText");
    const modalSub = document.getElementById("modalSubtitleText");
    const avatarInitials = document.getElementById("modalUserAvatarInitials");
    const avatarIcon = document.getElementById("modalUserAvatarIcon");

    const contribFooter = document.getElementById("profileBottomContributeSection");
    const humanCheck = document.getElementById("authHumanCheckbox");
    if (humanCheck) humanCheck.checked = false;

    const inAppHint = document.getElementById("inAppBrowserAuthHint");
    if (inAppHint) {
        const ua = (typeof navigator !== "undefined" && navigator.userAgent) ? navigator.userAgent : "";
        const isInAppWebView = /Instagram|FBAN|FBAV|FB_IAB|LinkedInApp|Line\/|Twitter/i.test(ua);
        if (isInAppWebView) inAppHint.classList.remove("hidden");
        else inAppHint.classList.add("hidden");
    }

    if (isUserLoggedIn()) {
        if (authFormView) authFormView.classList.add("hidden");
        if (authProfileView) authProfileView.classList.remove("hidden");
        if (contribFooter) contribFooter.classList.remove("hidden");

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
                statusBadge.textContent = "Standard (7+ Days Open)";
                statusBadge.className = "px-2.5 py-1 rounded-full text-[11px] font-black bg-slate-200 text-slate-700";
            }
        }

        const accessLevel = document.getElementById("profileAccessLevel");
        if (accessLevel) {
            accessLevel.textContent = paid ? "100% Unlocked (All Portals + Priority VIP)" : "Standard Access • Priority VIP Locked";
            accessLevel.className = paid ? "font-bold text-emerald-700" : "font-bold text-violet-700";
        }

        const upgradeSec = document.getElementById("profileUpgradeSection");
        const activeSec = document.getElementById("profileActiveVipSection");
        if (upgradeSec) {
            if (paid) upgradeSec.classList.add("hidden");
            else upgradeSec.classList.remove("hidden");
        }
        if (activeSec) {
            if (paid) {
                activeSec.classList.remove("hidden");
                const badgeLbl = document.getElementById("profileActiveVipBadgeLabel");
                const detailEl = document.getElementById("profileActiveVipDetail");
                const planTier = (localStorage.getItem("almond_plan_tier") || localStorage.getItem("almond_plan") || "").toLowerCase();
                let tierText = "1-Month VIP Pass Active";
                if (planTier.includes("6m") || planTier.includes("180") || planTier.includes("dominance")) tierText = "6-Month Career Dominance Pass";
                else if (planTier.includes("3m") || planTier.includes("90") || planTier.includes("sprint")) tierText = "3-Month Career Sprint Pass";

                if (badgeLbl) badgeLbl.textContent = `${tierText} ✓`;
                const formatted = localStorage.getItem("almond_paid_until_formatted") || "";
                const rem = localStorage.getItem("almond_remaining_str") || "";
                if (detailEl) {
                    if (formatted && rem) detailEl.textContent = `Valid until ${formatted} • ${rem} • 100% Direct Ingestion Unlocked`;
                    else if (rem) detailEl.textContent = `Valid • ${rem} • 100% Direct Ingestion Unlocked`;
                    else detailEl.textContent = `Active • 100% Unlocked Direct Portals`;
                }
            } else {
                activeSec.classList.add("hidden");
            }
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
        if (contribFooter) contribFooter.classList.add("hidden");
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
    const welcomeView = document.getElementById("authWelcomeView");
    if (welcomeView) welcomeView.classList.add("hidden");
};

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
            window.goToSlide(3);
        }
    }
};

// Telemetry & Hardware Device Identification (Samsung, Poco, Pixel, iPhone, PC)
if (typeof navigator !== "undefined" && navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
    try {
        navigator.userAgentData.getHighEntropyValues(["model", "platform", "platformVersion"]).then(function(vals) {
            if (vals.model) sessionStorage.setItem("almond_client_model", vals.model);
            if (vals.platform) sessionStorage.setItem("almond_client_platform", vals.platform);
        }).catch(function() {});
    } catch(e) {}
}

window.getClientDeviceModel = function() {
    return (typeof sessionStorage !== "undefined" && sessionStorage.getItem("almond_client_model")) || "";
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

    // Human / Anti-Bot Checkbox Check (Required for both Login & Sign Up)
    const humanCheckbox = document.getElementById("authHumanCheckbox");
    if (humanCheckbox && !humanCheckbox.checked) {
        if (errBox && errText) {
            errText.textContent = "Please check the 'I am human (Verify not a robot)' box to continue.";
            errBox.classList.remove("hidden");
        }
        return;
    }

    // Strict personal email validation
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!email || !emailRegex.test(email)) {
        if (errBox && errText) {
            errText.textContent = "Please enter a valid personal email address.";
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

    if (window.activeAuthTab === "signup") {
        const confirmPassField = document.getElementById("signupConfirmPasswordField");
        const isConfirmVisible = confirmPassField && !confirmPassField.classList.contains("hidden");
        const confirmPassInput = document.getElementById("authConfirmPasswordInput");
        const confirmPass = confirmPassInput?.value || "";
        if (isConfirmVisible && password !== confirmPass) {
            if (errBox && errText) {
                errText.textContent = "Passwords do not match. Please re-enter.";
                errBox.classList.remove("hidden");
            }
            return;
        }

        // Instant direct candidate activation (no disruptive email OTP round-trip on mobile WebView)
        const derivedName = fullName || email.split("@")[0].replace(/[._-]+/g, " ").trim() || "Candidate";
        try {
            await window.executeDirectSignupFallback(email, password, derivedName);
        } catch (_) {}
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
            body: JSON.stringify({ email, password, device_model: window.getClientDeviceModel() })
        });
        const data = await resp.json();

        if (!resp.ok || data.status === "error") {
            throw new Error(data.detail || data.message || "Authentication failed. Please verify credentials.");
        }

        // Store session tokens in localStorage
        if (data.token) {
            localStorage.setItem("almond_session_token", data.token);
            document.cookie = `almond_session_token=${data.token}; path=/; max-age=2592000; SameSite=Lax`;
            localStorage.setItem("almond_auth_token", data.token);
        }
        if (data.user_id) localStorage.setItem("almond_user_id", data.user_id);
        if (data.email) localStorage.setItem("almond_user_email", data.email);
        if (data.full_name) localStorage.setItem("almond_user_name", data.full_name);
        localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");

        window.updateTopProfileBar();
        if (typeof window.refreshUnlockedFeedsAfterAuth === "function") window.refreshUnlockedFeedsAfterAuth();
        window.closeProfileModal();

        // If user was intercepted when clicking search, immediately resume and execute!
        if (window._pendingJobSearch) {
            window._pendingJobSearch = false;
            const searchBtn = document.getElementById("searchJobsBtn");
            if (searchBtn && typeof executeSearch === "function") {
                executeSearch();
                window.goToSlide(3);
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
                full_name: fullName,
                device_model: window.getClientDeviceModel()
            })
        });
        const data = await resp.json();

        if (!resp.ok || data.status === "error") {
            throw new Error(data.detail || data.message || "Verification failed. Incorrect or expired code.");
        }

        // Account verified & created! Store session
        if (data.token) {
            localStorage.setItem("almond_session_token", data.token);
            document.cookie = `almond_session_token=${data.token}; path=/; max-age=2592000; SameSite=Lax`;
            localStorage.setItem("almond_auth_token", data.token);
        }
        if (data.user_id) localStorage.setItem("almond_user_id", data.user_id);
        if (data.email) localStorage.setItem("almond_user_email", data.email);
        if (data.full_name) localStorage.setItem("almond_user_name", data.full_name);
        localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");
        if (typeof window.almondTrackFunnel === "function") {
            window.almondTrackFunnel("signup", { user_email: data.email || email, user_name: data.full_name || fullName });
        }

        if (window._resendOtpInterval) {
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
        const contribFtr = document.getElementById("profileBottomContributeSection");
        if (contribFtr) contribFtr.classList.add("hidden");
        if (window.lucide) lucide.createIcons();

        // Update brand bar indicators immediately
        window.updateTopProfileBar();
        if (typeof window.refreshUnlockedFeedsAfterAuth === "function") window.refreshUnlockedFeedsAfterAuth();
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
    const spamText = document.getElementById("authSpamNoticeText");
    const email = (emailInput?.value || "").trim().toLowerCase();

    if (!email) return;

    try {
        const resp = await fetch("/api/auth/send-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await resp.json().catch(() => ({}));

        if (data.fallback_available || (!resp.ok && (data.detail || "").includes("SMTP credentials"))) {
            await window.handleInstantSignupBypass();
            return;
        }

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
        const errMsg = String(err && (err.message || err.detail || ""));
        if (errMsg.includes("SMTP credentials") || errMsg.includes("verification email")) {
            await window.handleInstantSignupBypass();
            return;
        }
        if (errBox && errText) {
            errText.textContent = err.message || "Failed to resend code.";
            errBox.classList.remove("hidden");
        }
    }
};

window.handleInstantSignupBypass = async function() {
    const emailInput = document.getElementById("authEmailInput");
    const passInput = document.getElementById("authPasswordInput");
    const nameInput = document.getElementById("authFullNameInput");

    const email = (emailInput?.value || "").trim().toLowerCase();
    const password = passInput?.value || "";
    const fullName = (nameInput?.value || "").trim();

    if (!email || !password) {
        window.cancelOtpVerification();
        return;
    }
    await window.executeDirectSignupFallback(email, password, fullName);
};

window.executeDirectSignupFallback = async function(email, password, fullName) {
    const errBox = document.getElementById("authErrorMessage");
    const errText = document.getElementById("authErrorText");
    const submitBtn = document.getElementById("authSubmitBtn");
    const verifyBtn = document.getElementById("authVerifyOtpBtn");

    if (errBox) errBox.classList.add("hidden");

    const activeBtn = (verifyBtn && verifyBtn.closest("#authOtpStep") && !verifyBtn.closest("#authOtpStep").classList.contains("hidden")) ? verifyBtn : submitBtn;
    if (activeBtn) {
        activeBtn.disabled = true;
        activeBtn.classList.add("opacity-70");
        activeBtn.innerHTML = `<span class="animate-spin mr-1">⌛</span> Activating Candidate Account...`;
    }

    try {
        const signupResp = await fetch("/api/auth/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: email,
                password: password,
                full_name: fullName,
                device_model: window.getClientDeviceModel()
            })
        });
        const data = await signupResp.json().catch(() => ({}));

        if (!signupResp.ok || data.status === "error") {
            throw new Error(data.detail || data.message || "Failed to activate candidate account.");
        }

        // Store session tokens in localStorage
        if (data.token) {
            localStorage.setItem("almond_session_token", data.token);
            document.cookie = `almond_session_token=${data.token}; path=/; max-age=2592000; SameSite=Lax`;
            localStorage.setItem("almond_auth_token", data.token);
        }
        if (data.user_id) localStorage.setItem("almond_user_id", data.user_id);
        if (data.email) localStorage.setItem("almond_user_email", data.email);
        if (data.full_name) localStorage.setItem("almond_user_name", data.full_name);
        localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");
        if (typeof window.almondTrackFunnel === "function") {
            window.almondTrackFunnel("signup", { user_email: data.email || email, user_name: data.full_name || fullName });
        }

        if (window._resendOtpInterval) {
            clearInterval(window._resendOtpInterval);
            window._resendOtpInterval = null;
        }

        // Update brand bar indicators immediately
        window.updateTopProfileBar();
        if (typeof window.refreshUnlockedFeedsAfterAuth === "function") window.refreshUnlockedFeedsAfterAuth();

        // Show celebratory in-app Welcome View
        const authFormView = document.getElementById("authFormView");
        const authOtpStep = document.getElementById("authOtpStep");
        const authWelcomeView = document.getElementById("authWelcomeView");
        const welcomeUserName = document.getElementById("welcomeUserName");
        const modalTitleText = document.getElementById("modalTitleText");
        const modalSubtitleText = document.getElementById("modalSubtitleText");

        if (authFormView) authFormView.classList.add("hidden");
        if (authOtpStep) authOtpStep.classList.add("hidden");
        if (modalTitleText) modalTitleText.textContent = "Welcome to Almond Jobs";
        if (modalSubtitleText) modalSubtitleText.textContent = "Account Active & Ready";
        if (welcomeUserName) welcomeUserName.textContent = data.full_name || "Candidate";
        if (authWelcomeView) authWelcomeView.classList.remove("hidden");
        const contribFtr = document.getElementById("profileBottomContributeSection");
        if (contribFtr) contribFtr.classList.add("hidden");
        if (window.lucide) lucide.createIcons();

        // If candidate was intercepted while clicking search, immediately resume search!
        if (window._pendingJobSearch) {
            window._pendingJobSearch = false;
            setTimeout(() => {
                window.closeProfileModal();
                if (typeof executeSearch === "function") {
                    executeSearch();
                    window.goToSlide(3);
                }
            }, 1200);
        }
        return data;
    } catch (err) {
        if (errBox && errText) {
            errText.textContent = err.message || "Direct account activation failed.";
            errBox.classList.remove("hidden");
        }
        throw err;
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove("opacity-70");
            submitBtn.innerHTML = `<span id="authSubmitBtnText">Create Free Account &rarr;</span><i data-lucide="arrow-right" class="w-4 h-4 text-white"></i>`;
        }
        if (verifyBtn) {
            verifyBtn.disabled = false;
            verifyBtn.classList.remove("opacity-70");
            verifyBtn.innerHTML = `<span>Verify OTP & Create Account</span><i data-lucide="check-circle-2" class="w-4 h-4 text-white"></i>`;
        }
        if (window.lucide) lucide.createIcons();
    }
};

window.cancelOtpVerification = function() {
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
};

// ==========================================
// GOOGLE SIGN-IN & 0-OTP AUTH CONTROLLER
// ==========================================
window.handleGoogleSignInClick = function(e) {
    const ua = (typeof navigator !== "undefined" && navigator.userAgent) ? navigator.userAgent : "";
    const isInAppWebView = /Instagram|FBAN|FBAV|FB_IAB|LinkedInApp|Line\//i.test(ua);
    if (isInAppWebView) {
        if (e && e.preventDefault) e.preventDefault();
        const errBox = document.getElementById("authErrorMessage");
        const errText = document.getElementById("authErrorText");
        if (errBox && errText) {
            errText.textContent = "Instagram blocks Google Sign-In popups. Enter your email & password below for instant 10-second free signup (no OTP code needed)!";
            errBox.classList.remove("hidden");
        }
        const emailInput = document.getElementById("authEmailInput");
        if (emailInput) {
            emailInput.focus();
            emailInput.scrollIntoView({ behavior: "smooth", block: "center" });
        }
        return false;
    }

    const googleLabel = document.getElementById("googleAuthBtnLabel");
    if (googleLabel) googleLabel.textContent = "Connecting to Google...";

    // Standard browser: redirect to official Google OAuth 2.0 Account Chooser
    window.location.href = "/api/auth/google/login";
    return true;
};

window.handleGoogleCredentialResponse = function(response) {
    if (response && response.credential) {
        completeGoogleAuth({ credential: response.credential });
    }
};

async function completeGoogleAuth(payload) {
    const errBox = document.getElementById("authErrorMessage");
    const errText = document.getElementById("authErrorText");
    const googleBtn = document.getElementById("googleAuthBtn");
    const googleLabel = document.getElementById("googleAuthBtnLabel");

    if (googleBtn) {
        googleBtn.disabled = true;
        googleBtn.classList.add("opacity-70");
    }
    if (googleLabel) googleLabel.textContent = "Connecting with Google...";

    try {
        const googlePayload = Object.assign({}, payload, { device_model: window.getClientDeviceModel() });
        const resp = await fetch("/api/auth/google", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(googlePayload)
        });
        const data = await resp.json();
        if (!resp.ok || data.status === "error") {
            throw new Error(data.detail || data.message || "Google sign-in failed.");
        }

        // Store session in localStorage (set both session and backup auth token keys)
        if (data.token) {
            localStorage.setItem("almond_session_token", data.token);
            document.cookie = `almond_session_token=${data.token}; path=/; max-age=2592000; SameSite=Lax`;
            localStorage.setItem("almond_auth_token", data.token);
        }
        localStorage.setItem("almond_user_id", data.user_id);
        localStorage.setItem("almond_user_email", data.email);
        localStorage.setItem("almond_user_name", data.full_name);
        localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");

        window.currentAuthUser = data;

        // Transition to Welcome View
        const authFormView = document.getElementById("authFormView");
        const authContextNotice = document.getElementById("authContextNotice");
        const authWelcomeView = document.getElementById("authWelcomeView");
        const welcomeUserName = document.getElementById("welcomeUserName");
        const modalTitleText = document.getElementById("modalTitleText");
        const modalSubtitleText = document.getElementById("modalSubtitleText");

        if (authFormView) authFormView.classList.add("hidden");
        if (authContextNotice) authContextNotice.classList.add("hidden");
        if (modalTitleText) modalTitleText.textContent = "Welcome to Almond Jobs";
        if (modalSubtitleText) modalSubtitleText.textContent = "Signed in with Google";
        if (welcomeUserName) welcomeUserName.textContent = data.full_name || "Candidate";
        if (authWelcomeView) authWelcomeView.classList.remove("hidden");
        const contribFtr = document.getElementById("profileBottomContributeSection");
        if (contribFtr) contribFtr.classList.add("hidden");
        if (window.lucide) lucide.createIcons();

        window.updateTopProfileBar();
        if (typeof window.refreshUnlockedFeedsAfterAuth === "function") window.refreshUnlockedFeedsAfterAuth();
    } catch (err) {
        if (errBox && errText) {
            errText.textContent = err.message || "Google authentication failed.";
            errBox.classList.remove("hidden");
        }
    } finally {
        if (googleBtn) {
            googleBtn.disabled = false;
            googleBtn.classList.remove("opacity-70");
        }
        if (googleLabel) googleLabel.textContent = "Continue with Google (0 OTP)";
    }
}

window.handleLogout = function() {
    document.cookie = "almond_session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
    localStorage.removeItem("almond_session_token");
    localStorage.removeItem("almond_auth_token");
    localStorage.removeItem("almond_remaining_str");
    localStorage.removeItem("almond_plan_tier");
    localStorage.removeItem("almond_paid_until_formatted");
    localStorage.removeItem("almond_paid_until");
    localStorage.removeItem("almond_user_id");
    localStorage.removeItem("almond_user_email");
    localStorage.removeItem("almond_user_name");
    localStorage.removeItem("almond_is_paid");
    localStorage.removeItem("almond_user_paid");
    window.currentAuthUser = null;
    window.candidateUser = null;
    window.almondAiSessionCache = { pitch: {}, coverLetter: {} };

    window.updateTopProfileBar();
    if (typeof window.refreshUnlockedFeedsAfterAuth === "function") window.refreshUnlockedFeedsAfterAuth();
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
    const topSignUpPill = document.getElementById("topSignUpPillBtn");
    const vipLbl = document.getElementById("topVipPassLabel");
    const vipCrown = document.getElementById("topProfileVipCrown");
    const vipBadge = document.getElementById("topProfileVipBadge");
    const modalAvatarBox = document.getElementById("modalUserAvatarBox");
    const paid = isUserPaid();
    const loggedIn = isUserLoggedIn();

    if (topSignUpPill) {
        if (loggedIn) topSignUpPill.classList.add("hidden");
        else topSignUpPill.classList.remove("hidden");
    }

    // Hide all VIP / Pro / payment options from anonymous (logged-out) visitors;
    // reveal them only after they sign up or log in.
    const sideVipBtn = document.getElementById("sidePanelVipBtn");
    const sideContribBtn = document.getElementById("sidePanelContributeBtn");
    if (sideVipBtn) sideVipBtn.classList.toggle("hidden", !loggedIn);
    if (sideContribBtn) sideContribBtn.classList.toggle("hidden", !loggedIn);

    const omniFreeOpt = document.getElementById("omniSortFreeJobsOption");
    const omniSortSel = document.getElementById("omniSortSelect");
    if (omniFreeOpt) {
        omniFreeOpt.hidden = !loggedIn;
        omniFreeOpt.disabled = !loggedIn;
        omniFreeOpt.classList.toggle("hidden", !loggedIn);
        if (!loggedIn && omniSortSel && omniSortSel.value === "free_jobs") {
            omniSortSel.value = "best_match";
        }
    }
    const omniFreeStrip = document.getElementById("omniFreeAccessStrip");
    if (omniFreeStrip) {
        const hasLoadedItems = Array.isArray(window.omniCurrentItems) && window.omniCurrentItems.length > 0;
        if (loggedIn && !paid && hasLoadedItems) omniFreeStrip.classList.remove("hidden");
        else omniFreeStrip.classList.add("hidden");
    }
    const curatedFreeOpt = document.getElementById("curatedSortFreeJobsOption");
    const curatedSortSel = document.getElementById("curatedSortSelect");
    if (curatedFreeOpt) {
        curatedFreeOpt.hidden = !loggedIn;
        curatedFreeOpt.disabled = !loggedIn;
        curatedFreeOpt.classList.toggle("hidden", !loggedIn);
        if (!loggedIn && curatedSortSel && curatedSortSel.value === "free_jobs") {
            curatedSortSel.value = "latest";
        }
    }

    if (vipLbl) vipLbl.textContent = paid ? "VIP Active ✓" : "VIP Pass";
    const upgradeLbl = document.getElementById("topUpgradeLabel");
    if (upgradeLbl) upgradeLbl.textContent = paid ? "Pro Active ✓" : "Upgrade";

    if (topBtn) {
        if (paid) {
            // Distinctive VIP / PRO luxury golden ring and gradient dial
            topBtn.className = "relative w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-gradient-to-tr from-amber-400 via-yellow-300 to-amber-500 ring-2 ring-amber-400 ring-offset-2 ring-offset-white text-slate-950 font-black flex items-center justify-center transition shadow-md shadow-amber-500/30 cursor-pointer group shrink-0";
            if (vipCrown) vipCrown.classList.remove("hidden");
            if (vipBadge) vipBadge.classList.remove("hidden");
            if (indicator) indicator.classList.add("hidden");
        } else {
            topBtn.className = "relative w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-slate-100 hover:bg-violet-50 border border-slate-300 hover:border-violet-300 text-slate-700 hover:text-violet-700 flex items-center justify-center transition shadow-2xs cursor-pointer group shrink-0";
            if (vipCrown) vipCrown.classList.add("hidden");
            if (vipBadge) vipBadge.classList.add("hidden");
            if (indicator) {
                if (loggedIn) indicator.classList.remove("hidden");
                else indicator.classList.add("hidden");
            }
        }
    }

    if (modalAvatarBox) {
        if (paid) {
            modalAvatarBox.className = "w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-400 to-yellow-500 text-slate-950 flex items-center justify-center border-2 border-amber-300 shadow-md ring-2 ring-amber-400/40";
        } else {
            modalAvatarBox.className = "w-10 h-10 rounded-2xl bg-violet-100 text-violet-700 flex items-center justify-center border border-violet-200 shadow-2xs";
        }
    }

    if (loggedIn) {
        const name = getCandidateUserName();
        const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().substring(0, 2) || "CA";
        if (initialsSpan) {
            initialsSpan.textContent = initials;
            initialsSpan.className = paid ? "text-[10px] font-black text-slate-950 uppercase" : "text-[10px] font-black text-violet-800 uppercase";
            initialsSpan.classList.remove("hidden");
        }
        if (topIcon) topIcon.classList.add("hidden");
        if (topBtn) topBtn.title = `${name} (${getCandidateUserEmail()}) ${paid ? '👑 [VIP PRO ACTIVE]' : ''} - Profile`;
    } else {
        if (initialsSpan) initialsSpan.classList.add("hidden");
        if (topIcon) topIcon.classList.remove("hidden");
        if (topBtn) topBtn.title = "Candidate Profile & Sign In";
    }
    if (window.lucide) lucide.createIcons();
};

window.initAuthSession = async function() {
    window.updateTopProfileBar();
    const token = localStorage.getItem("almond_session_token") || localStorage.getItem("almond_auth_token") || "";
    const userId = localStorage.getItem("almond_user_id") || "";
    const email = localStorage.getItem("almond_user_email") || "";
    const fullName = localStorage.getItem("almond_user_name") || "";

    // Seamless Google OAuth callback handler
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const isLoginSuccess = urlParams.get("login") === "success" || sessionStorage.getItem("almond_login_event") === "google_success";
        if (isLoginSuccess && isUserLoggedIn()) {
            sessionStorage.removeItem("almond_login_event");
            const isNewGoogleSignup = sessionStorage.getItem("almond_google_new_signup") === "1";
            if (isNewGoogleSignup) {
                sessionStorage.removeItem("almond_google_new_signup");
                if (typeof window.almondTrackFunnel === "function") {
                    window.almondTrackFunnel("signup", { user_email: email, user_name: fullName });
                }
            }
            if (urlParams.get("login") === "success") {
                window.history.replaceState({}, document.title, window.location.pathname);
            }
            window.updateTopProfileBar();
            setTimeout(() => {
                if (typeof window.openProfileModal === "function") {
                    window.openProfileModal();
                }
            }, 300);
        }
    } catch(e) {
        console.warn("[Auth] OAuth landing handling note:", e);
    }

    if (!token && !userId) return;

    try {
        const resp = await fetch("/api/auth/me", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, user_id: userId, email, full_name: fullName })
        });
        if (resp.ok) {
            const data = await resp.json();
            if (data.is_authenticated) {
                const resolvedToken = data.token || token;
                if (resolvedToken) {
                    localStorage.setItem("almond_session_token", resolvedToken);
                    localStorage.setItem("almond_auth_token", resolvedToken);
                    document.cookie = `almond_session_token=${resolvedToken}; path=/; max-age=2592000; SameSite=Lax`;
                }
                if (data.user_id) localStorage.setItem("almond_user_id", data.user_id);
                if (data.email) localStorage.setItem("almond_user_email", data.email);
                if (data.full_name) localStorage.setItem("almond_user_name", data.full_name);
                if (data.remaining_str) localStorage.setItem("almond_remaining_str", data.remaining_str);
                if (data.plan_tier) localStorage.setItem("almond_plan_tier", data.plan_tier);
                if (data.paid_until_formatted) localStorage.setItem("almond_paid_until_formatted", data.paid_until_formatted);
                if (data.paid_until) localStorage.setItem("almond_paid_until", String(data.paid_until));
                localStorage.setItem("almond_is_paid", data.is_paid ? "true" : "false");
                window.updateTopProfileBar();
                if (typeof window.fetchAiQuotaStatus === "function") {
                    window.fetchAiQuotaStatus();
                }
                if (typeof window.fetchKanbanFromCloud === "function") {
                    window.fetchKanbanFromCloud();
                }
                if (!data.is_paid && data.recovery_offer && data.recovery_offer.active && typeof window.showAlmondRecoveryOfferPopup === "function") {
                    window.showAlmondRecoveryOfferPopup(data.recovery_offer);
                }
            } else if (data.invalid_token === true) {
                localStorage.removeItem("almond_session_token");
                localStorage.removeItem("almond_auth_token");
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

window.triggerRazorpayCheckout = async function(amountInr = 699, planName = 'Almond Jobs 1-Month VIP Pass', optionsConfig = {}) {
    const parsedInr = parseInt(amountInr, 10);
    const finalAmount = Number.isFinite(parsedInr) ? parsedInr : 1;
    const amountPaise = finalAmount * 100;
    if (amountPaise < 100) {
        alert("Minimum payment amount is INR 1 (100 paise).");
        return;
    }

    const purchaseType = optionsConfig.purchaseType || "vip_pass";
    const selectedCurr = (optionsConfig.currency || "INR").toUpperCase();
    const currSymbol = optionsConfig.currency_symbol || (selectedCurr === "USD" ? "$" : (selectedCurr === "EUR" ? "€" : (selectedCurr === "GBP" ? "£" : "₹")));

    let computedAmountPaise;
    if (selectedCurr === "INR") {
        computedAmountPaise = Math.round(finalAmount * 100);
    } else {
        const parsedForeign = parseFloat(optionsConfig.foreign_amount);
        const foreignAmt = Number.isFinite(parsedForeign) && parsedForeign > 0
            ? parsedForeign
            : (optionsConfig.display_price ? parseFloat(optionsConfig.display_price.replace(/[^0-9.]/g, '')) : 19.99);
        computedAmountPaise = Math.round(foreignAmt * 100);
    }

    const userId = getCandidateUserId();
    const sessionToken = localStorage.getItem("almond_session_token") || "";
    const candidateUser = window.currentCandidateUser || {};

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
                token: sessionToken,
                amount_inr: finalAmount,
                amount: computedAmountPaise,
                currency: selectedCurr,
                plan_name: planName,
                purchase_type: purchaseType
            })
        });

        const orderData = await orderResp.json().catch(() => ({}));
        if (!orderResp.ok) {
            throw new Error(orderData.detail || orderData.message || "Unable to initialize Razorpay checkout session.");
        }

        if (orderData.status !== "success" || !orderData.order_id) {
            throw new Error(orderData.message || orderData.detail || "Failed to generate checkout order.");
        }

        if (typeof window.almondTrackFunnel === "function") {
            window.almondTrackFunnel("checkout_start", {
                amount_inr: finalAmount,
                currency: selectedCurr,
                meta: { plan_name: planName, purchase_type: purchaseType }
            });
        }

        // 2. Launch Razorpay Checkout Modal
        const options = {
            key: orderData.key_id,
            amount: orderData.amount,
            currency: orderData.currency || selectedCurr,
            name: "Almond Jobs",
            description: planName,
            order_id: orderData.order_id,
            image: window.location.origin + "/static/logo-512.png",
            modal: {
                ondismiss: function() {
                    console.log("[Razorpay] Checkout modal dismissed without completion.");
                    // Only display exit-intent for VIP passes, never for voluntary coffee donations
                    if (purchaseType === "vip_pass" && typeof window.openPaymentExitIntent === "function") {
                        const exitSym = currSymbol;
                        const displayPrice = (selectedCurr === "INR")
                            ? finalAmount
                            : (optionsConfig.foreign_amount || (computedAmountPaise / 100));
                        window.openPaymentExitIntent(planName, displayPrice, exitSym, optionsConfig, finalAmount);
                    }
                }
            },
            handler: async function (response) {
                // 3. Verify signature securely on backend
                try {
                    const verifyResp = await fetch("/api/payment/verify", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            user_id: userId,
                            token: sessionToken,
                            email: currentProfile?.email || candidateUser.email || optionsConfig.supporterEmail || "",
                            order_id: response.razorpay_order_id,
                            payment_id: response.razorpay_payment_id,
                            signature: response.razorpay_signature,
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                            amount_inr: finalAmount,
                            currency: selectedCurr,
                            plan_name: planName,
                            purchase_type: purchaseType,
                            supporter_name: optionsConfig.supporterName || "",
                            supporter_message: optionsConfig.supporterMessage || ""
                        })
                    });

                    const verifyData = await verifyResp.json().catch(() => ({}));
                    if (verifyResp.ok && verifyData.status === "success") {
                        if (typeof window.almondTrackFunnel === "function") {
                            window.almondTrackFunnel("purchase", {
                                amount_inr: finalAmount,
                                currency: selectedCurr,
                                meta: { plan_name: planName, purchase_type: purchaseType }
                            });
                        }
                        if (verifyData.purchase_type === "contribution" || purchaseType === "contribution") {
                            if (typeof window.closeCoffeeCheckoutModal === "function") window.closeCoffeeCheckoutModal();
                            if (typeof window.closeVipPricingModal === "function") window.closeVipPricingModal();
                            if (typeof window.addSupporterToFeed === "function") {
                                window.addSupporterToFeed({
                                    name: optionsConfig.supporterName || "Generous Supporter",
                                    message: optionsConfig.supporterMessage || "",
                                    amount: finalAmount,
                                    currency: selectedCurr,
                                    currency_symbol: currSymbol,
                                    foreign_amount: optionsConfig.foreign_amount
                                });
                            }
                            const msgInput = document.getElementById("coffeeSupporterMessage");
                            if (msgInput) msgInput.value = "";
                            alert("Thank you for your generous coffee contribution! Your feedback is now live in the recent supporters feed.");
                        } else {
                            localStorage.setItem("almond_is_paid", "true");
                            if (typeof window.closeVipPassModal === "function") window.closeVipPassModal();
                            const vipLbl = document.getElementById("topVipPassLabel");
                            if (vipLbl) vipLbl.textContent = "VIP Active ✓";
                            const topUpgLbl = document.getElementById("topUpgradeLabel");
                            if (topUpgLbl) topUpgLbl.textContent = "Pro Active ✓";
                            alert("1-Month VIP Pass Activated! All priority corporate postings and direct application portals are now fully unlocked for 30 days.");
                            const searchBtn = document.getElementById("searchJobsBtn");
                            if (searchBtn && currentProfile) {
                                searchBtn.click();
                            }
                            const curatedModal = document.getElementById("curatedFeedsModal");
                            if (curatedModal && !curatedModal.classList.contains("hidden") && typeof window.fetchCuratedFeeds === "function") {
                                window.fetchCuratedFeeds();
                            }
                        }
                    } else {
                        const reason = verifyData.detail || verifyData.message || "Signature verification failed.";
                        alert("Payment verification could not be confirmed: " + reason);
                    }
                } catch (vErr) {
                    alert("Error verifying payment signature: " + vErr.message);
                }
            },
            prefill: {
                name: currentProfile?.name || candidateUser.full_name || "",
                email: currentProfile?.email || candidateUser.email || (optionsConfig?.supporterEmail || ""),
                contact: currentProfile?.phone || ""
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
            const errDesc = response?.error?.description || response?.error?.reason || "Transaction failed";
            alert("Payment failed: " + errDesc);
        });
        rzpInstance.open();
    } catch (e) {
        alert("Payment initialization error: " + e.message);
    }
};

// 10. Proof-of-Human Presence Barrier ("Hold to Verify" Guard)

let pendingHumanAction = null;

function isHumanVerified() {
    try {
        return sessionStorage.getItem("almond_human_verified") === "true";
    } catch (e) {
        return false;
    }
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
    if (modal) {
        modal.classList.remove("hidden");
        const closeBtn = document.getElementById("closeVerifyModal");
        if (closeBtn) closeBtn.classList.remove("hidden");
    }
    if (window.lucide) lucide.createIcons();
}

function resetVerifierUI() {
    const tickBox = document.getElementById("humanTickCheckbox");
    const btnText = document.getElementById("holdVerifyBtnText");
    const hintText = document.getElementById("holdVerifyHint");
    const successIcon = document.getElementById("holdVerifySuccessIcon");
    const boxLabel = document.getElementById("holdVerifyBtn");

    if (tickBox) {
        tickBox.checked = false;
        tickBox.disabled = false;
    }
    if (btnText) {
        btnText.textContent = "I am not a robot";
        btnText.className = "text-sm font-extrabold text-slate-900 tracking-tight transition-colors";
    }
    if (hintText) {
        hintText.textContent = "Just one tap to verify and continue.";
        hintText.className = "text-xs text-slate-500 text-center mt-3 font-medium leading-relaxed transition-colors";
    }
    if (successIcon) successIcon.classList.add("hidden");
    if (boxLabel) {
        boxLabel.className = "w-full min-h-[60px] py-3.5 px-4 bg-slate-50 hover:bg-violet-50/70 border-2 border-slate-300 hover:border-violet-500 rounded-2xl flex items-center justify-between gap-3 transition-all shadow-xs cursor-pointer select-none";
    }
}

function initHumanVerifier() {
    const modal = document.getElementById("humanVerifyModal");
    const closeBtn = document.getElementById("closeVerifyModal");
    const tickBox = document.getElementById("humanTickCheckbox");
    const boxLabel = document.getElementById("holdVerifyBtn");
    const btnText = document.getElementById("holdVerifyBtnText");
    const hintText = document.getElementById("holdVerifyHint");
    const successIcon = document.getElementById("holdVerifySuccessIcon");

    if (!modal) return;

    // Never block new visitors on homepage entry with a fullscreen gate.
    modal.classList.add("hidden");
    if (!isHumanVerified()) {
        const markVerifiedPassively = () => {
            try {
                sessionStorage.setItem("almond_human_verified", "true");
                document.cookie = "almond_human_verified=1; path=/; samesite=lax";
            } catch (err) {}
        };
        ["pointerdown", "touchstart", "keydown", "scroll"].forEach((evt) => {
            window.addEventListener(evt, markVerifiedPassively, { once: true, passive: true });
        });
    }

    const closeModal = () => {
        modal.classList.add("hidden");
        pendingHumanAction = null;
    };

    if (closeBtn) {
        closeBtn.addEventListener("click", closeModal);
    }

    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !modal.classList.contains("hidden")) {
            closeModal();
        }
    });

    if (!tickBox) return;

    tickBox.addEventListener("change", () => {
        if (!tickBox.checked) return;

        try {
            sessionStorage.setItem("almond_human_verified", "true");
            document.cookie = "almond_human_verified=1; path=/; samesite=lax";
        } catch (err) {}

        try {
            fetch("/api/security/verify-human", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ check_method: "checkbox" })
            }).catch(() => {});
        } catch (err) {}

        if (btnText) {
            btnText.textContent = "Human Verified ?";
            btnText.className = "text-sm font-black text-emerald-800 tracking-tight";
        }
        if (hintText) {
            hintText.textContent = "Verification confirmed! Continuing...";
            hintText.className = "text-xs text-emerald-700 font-bold text-center mt-3";
        }
        if (successIcon) successIcon.classList.remove("hidden");
        if (boxLabel) {
            boxLabel.className = "w-full min-h-[60px] py-3.5 px-4 bg-emerald-50 border-2 border-emerald-500 rounded-2xl flex items-center justify-between gap-3 transition-all shadow-sm select-none";
        }

        setTimeout(() => {
            modal.classList.add("hidden");
            const cb = pendingHumanAction;
            pendingHumanAction = null;
            if (cb) cb();
        }, 250);
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

window.openPaymentExitIntent = function(planName = "Career Sprint", displayPrice = 1799, currencySymbol = "₹", optionsConfig = null, inrAmount = 1799) {
    const modal = document.getElementById("paymentExitIntentModal");
    if (!modal) return;

    window._lastExitIntentData = { planName, displayPrice, currencySymbol, optionsConfig, inrAmount };

    const emojiEl = document.getElementById("exitIntentEmoji");
    const badgeEl = document.getElementById("exitIntentBadge");
    const titleEl = document.getElementById("exitIntentTitle");
    const msgEl = document.getElementById("exitIntentMessage");
    const planNameEl = document.getElementById("exitIntentPlanName");
    const planSubEl = document.getElementById("exitIntentPlanSub");
    const priceEl = document.getElementById("exitIntentPrice");
    const discountEl = document.getElementById("exitIntentDiscountNote");

    const nameLower = (planName || "").toLowerCase();
    const is6m = nameLower.includes("6-month") || nameLower.includes("180") || nameLower.includes("dominance");
    const is3m = !is6m && (nameLower.includes("3-month") || nameLower.includes("90") || nameLower.includes("sprint"));
    const is1m = !is6m && !is3m;

    if (is1m) {
        // 1-Month Plan: Movie ticket comparison
        if (emojiEl) emojiEl.textContent = "🎬";
        if (badgeEl) badgeEl.textContent = "1-Month VIP Career Pass";
        if (titleEl) titleEl.textContent = "A Career Upgrade Costs Less Than a Movie Ticket.";
        if (msgEl) msgEl.textContent = `Your career leap deserves at least the price of a movie ticket. For just ${currencySymbol}${displayPrice}, unlock 30 full days of direct corporate career postings, live founder feeds, and tailored application pitches.`;
        if (planNameEl) planNameEl.textContent = "1-Month VIP Pass (30 Days)";
        if (planSubEl) planSubEl.textContent = "30 Days of Unlimited Direct Applications & Zero Recruiter Ghosting";
        if (discountEl) discountEl.textContent = "Standard Pricing";
    } else if (is3m) {
        // 3-Month Plan: Casual dinner comparison
        if (emojiEl) emojiEl.textContent = "🍽️";
        if (badgeEl) badgeEl.textContent = "3-Month Career Sprint • 30% OFF";
        if (titleEl) titleEl.textContent = "Transform Your Career for the Price of Dinner.";
        if (msgEl) msgEl.textContent = `Your career transformation deserves at least the price of a nice weekend dinner. For just ${currencySymbol}${displayPrice}, unlock 90 continuous days of priority corporate openings, verified salary benchmarks, and direct hiring manager channels.`;
        if (planNameEl) planNameEl.textContent = "Career Sprint (90 Days)";
        if (planSubEl) planSubEl.textContent = "90 Days of Uninterrupted Search Dominance (Most Popular)";
        if (discountEl) discountEl.textContent = "30% Off Limited Time Offer";
    } else {
        // 6-Month Plan: Smart shirt / sneakers investment comparison
        if (emojiEl) emojiEl.textContent = "👔";
        if (badgeEl) badgeEl.textContent = "6-Month Career Dominance • 35% OFF";
        if (titleEl) titleEl.textContent = "Half a Year of High-Growth Roles for the Cost of a Shirt.";
        if (msgEl) msgEl.textContent = `Invest what you'd spend on a single shirt to unlock 6 continuous months of early-bird corporate listings, the executive career vault, and unredacted hiring signals.`;
        if (planNameEl) planNameEl.textContent = "Career Dominance (180 Days)";
        if (planSubEl) planSubEl.textContent = "Full 180 Days of Continuous High-Compensation Role Monitoring";
        if (discountEl) discountEl.textContent = "35% Off Limited Time Offer";
    }

    if (priceEl) priceEl.textContent = `${currencySymbol}${displayPrice}`;

    modal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
};

window.closeExitIntentModal = function() {
    const modal = document.getElementById("paymentExitIntentModal");
    if (!modal) return;
    modal.classList.add("hidden");
};

window.resumePaymentFromExitIntent = function() {
    window.closeExitIntentModal();
    if (window._lastExitIntentData) {
        const { planName, inrAmount, optionsConfig } = window._lastExitIntentData;
        triggerRazorpayCheckout(inrAmount, planName, optionsConfig || {});
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
        title: "Direct Internships",
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

let curatedCurationTimers = [];

function showCuratedLoadingScreen(headline = "Curating latest special jobs for you...") {
    const loadingScreen = document.getElementById('curatedLoadingScreen');
    const container = document.getElementById('curatedCardsContainer');
    const headlineEl = document.getElementById('curatedLoadingHeadline');
    const subtitleEl = document.getElementById('curatedLoadingSubtitle');
    const progressEl = document.getElementById('curatedProgressBar');
    
    // Clear any active timers
    curatedCurationTimers.forEach(id => clearTimeout(id));
    curatedCurationTimers = [];

    if (loadingScreen && container) {
        loadingScreen.classList.remove('hidden');
        container.classList.add('hidden');
        if (headlineEl) headlineEl.textContent = headline;
        if (progressEl) progressEl.style.width = '18%';
        if (subtitleEl) subtitleEl.textContent = 'Scanning 3.3M+ direct enterprise feeds & filtering 0% recruiter spreads...';

        const t1 = setTimeout(() => {
            if (progressEl) progressEl.style.width = '55%';
            if (subtitleEl) subtitleEl.textContent = 'Bypassing agency markups & verifying active corporate portals...';
        }, 700);

        const t2 = setTimeout(() => {
            if (progressEl) progressEl.style.width = '88%';
            if (subtitleEl) subtitleEl.textContent = 'Personalizing verified direct opportunities for you...';
        }, 1500);

        const t3 = setTimeout(() => {
            if (progressEl) progressEl.style.width = '100%';
            if (subtitleEl) subtitleEl.textContent = 'Ready! Unveiling verified corporate postings...';
        }, 2200);

        curatedCurationTimers = [t1, t2, t3];
    }
}

function hideCuratedLoadingScreen() {
    curatedCurationTimers.forEach(id => clearTimeout(id));
    curatedCurationTimers = [];
    const loadingScreen = document.getElementById('curatedLoadingScreen');
    const container = document.getElementById('curatedCardsContainer');
    if (loadingScreen && container) {
        loadingScreen.classList.add('hidden');
        container.classList.remove('hidden');
    }
}

window.openCuratedFeedsModal = function(feedType, initialSearch = "") {
    const modal = document.getElementById('curatedFeedsModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    const searchInp = document.getElementById('curatedSearchInput');
    if (searchInp) {
        searchInp.value = initialSearch || "";
    }
    switchCuratedFeedTab(feedType || 'internships', true);
};

window.closeCuratedFeedsModal = function() {
    hideCuratedLoadingScreen();
    const modal = document.getElementById('curatedFeedsModal');
    if (modal) modal.classList.add('hidden');
};

window.switchCuratedFeedTab = function(feedType, withBespokeCuration = true) {
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

    loadCuratedFeeds(withBespokeCuration);
};

window.handleCuratedSearchDebounced = function(val) {
    if (typeof window.renderCuratedAutocomplete === "function") {
        window.renderCuratedAutocomplete(val);
    }
    if (curatedDebounceTimer) clearTimeout(curatedDebounceTimer);
    curatedDebounceTimer = setTimeout(() => {
        loadCuratedFeeds(false);
    }, 250);
};

window.handleCuratedFilterChange = function() {
    loadCuratedFeeds(false);
};

window.curatedCurrentOffset = 0;
window.curatedCurrentItems = [];
window.curatedTotalCount = 0;

window.loadMoreCuratedFeeds = function() {
    loadCuratedFeeds(false, true);
};

async function loadCuratedFeeds(withBespokeCuration = false, append = false) {
    const container = document.getElementById('curatedCardsContainer');
    if (!container) return;

    const query = document.getElementById('curatedSearchInput')?.value || '';
    const category = document.getElementById('curatedCategorySelect')?.value || 'All';
    const location = document.getElementById('curatedLocationSelect')?.value || 'all';
    const timeFilter = document.getElementById('curatedTimeSelect')?.value || 'all';
    const sortBy = document.getElementById('curatedSortSelect')?.value || 'latest';
    const userId = getCandidateUserId();

    if (!append) {
        window.curatedCurrentOffset = 0;
        window.curatedCurrentItems = [];
        if (withBespokeCuration) {
            showCuratedLoadingScreen(`Curating ${currentCuratedFeedType === 'internships' ? 'internships' : (currentCuratedFeedType === 'aiml' ? 'AI/ML roles' : 'entry-level roles')}...`);
        } else {
            container.innerHTML = `
                <div class="py-12 flex flex-col items-center justify-center space-y-3">
                    <span class="w-7 h-7 rounded-full border-2 border-emerald-600 border-t-transparent animate-spin"></span>
                    <p class="text-xs font-bold text-slate-500">Searching matching direct corporate openings...</p>
                </div>
            `;
        }
    } else {
        const moreBtn = document.getElementById('curatedShowMoreBtn');
        if (moreBtn) {
            moreBtn.disabled = true;
            moreBtn.innerHTML = '<span class="animate-spin mr-1">⌛</span> Loading more jobs...';
        }
    }

    try {
        const params = new URLSearchParams({
            feed_type: currentCuratedFeedType,
            query: query,
            category: category,
            location: location,
            time_filter: timeFilter,
            sort_by: sortBy,
            limit: 30,
            offset: window.curatedCurrentOffset
        });
        if (userId) params.append('user_id', userId);

        const fetchPromise = fetch(`/api/curated-feeds?${params.toString()}`).then(r => {
            if (!r.ok) throw new Error("Failed to load curated feeds.");
            return r.json();
        });

        let data;
        if (withBespokeCuration && !append) {
            const delayPromise = new Promise(resolve => setTimeout(resolve, 1200));
            const [respData] = await Promise.all([fetchPromise, delayPromise]);
            data = respData;
            hideCuratedLoadingScreen();
        } else {
            data = await fetchPromise;
        }

        const result = data.result || {};
        const batch = result.items || [];
        window.curatedTotalCount = result.total || 0;
        if (!append) {
            window.curatedCurrentItems = batch;
        } else {
            window.curatedCurrentItems = window.curatedCurrentItems.concat(batch);
        }
        window.curatedCurrentOffset = window.curatedCurrentItems.length;
        renderCuratedCards(window.curatedCurrentItems, window.curatedTotalCount, sortBy);
    } catch (err) {
        hideCuratedLoadingScreen();
        if (!append) {
            container.innerHTML = `
                <div class="p-8 text-center bg-slate-50 rounded-2xl border border-slate-200">
                    <p class="text-xs font-bold text-rose-600">Failed to load direct feeds: ${err.message}</p>
                    <button type="button" onclick="loadCuratedFeeds(true)" class="mt-3 px-4 py-1.5 rounded-xl bg-slate-900 text-white text-xs font-bold cursor-pointer">Retry</button>
                </div>
            `;
        }
    }
}

function renderCuratedCards(items, total, sortBy = 'latest') {
    const container = document.getElementById('curatedCardsContainer');
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="p-10 text-center bg-slate-50 rounded-2xl border border-slate-200">
                <p class="text-sm font-black text-slate-800">No matching direct openings found with current filters.</p>
                <p class="text-xs text-slate-500 mt-1">Try clearing the search box or choosing another filter.</p>
            </div>
        `;
        return;
    }

    const loggedIn = isUserLoggedIn();
    const freeNoticeHtml = !loggedIn ? `
        <div class="p-3 rounded-xl bg-violet-50/95 border border-violet-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <span class="text-slate-800 font-medium">
                🔒 <strong>Sign up free</strong> to view direct corporate apply links &amp; save jobs.
            </span>
            <button type="button" onclick="openSignupToUnlockLinksModal()" class="shrink-0 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-700 text-white font-bold text-[11px] transition cursor-pointer">
                Sign Up Free &rarr;
            </button>
        </div>
    ` : (!isUserPaid() ? `
        <div class="p-3 rounded-xl bg-amber-50/90 border border-amber-200 text-xs">
            <span class="text-slate-800 font-medium">
                ℹ️ <strong>Free Plan:</strong> Latest jobs (less competition &amp; viewed early by HRs) are Pro-only. Use <strong>Sort</strong> to view 5+ day free jobs.
            </span>
        </div>
    ` : '');

    let html = `
        ${freeNoticeHtml}
        <div class="flex items-center justify-between pb-1 text-xs font-bold text-slate-500">
            <span>Showing ${items.length} of ${total.toLocaleString()} Verified Roles</span>
            <span class="text-emerald-700">✓ Direct Corporate Links</span>
        </div>
    `;

    items.forEach((item) => {
        const isAuthLocked = !loggedIn || Boolean(item.is_auth_locked);
        const isLocked = isJobLatestFeedLocked(item);
        const sponsorshipBadge = item.sponsorship === 'Visa Sponsored'
            ? `<span class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300 text-[10px] font-black">🛂 Visa Sponsored</span>`
            : '';
        const pkgBadge = item.package_display
            ? `<span class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300 text-[10px] font-black shadow-2xs">💰 ${String(item.package_display).replace(/[₹\u20b9]/g, '')}</span>`
            : '';
        const compactLoc = typeof window.formatCompactLocationClient === 'function'
            ? window.formatCompactLocationClient(item.location || 'Worldwide')
            : (item.location || 'Worldwide');

        const actionBtn = window.renderDirectApplyActionHtml({
            isAuthLocked,
            isVipLocked: isLocked,
            safeUrl: item.url,
            externalLabel: "Apply Direct &rarr;",
            compact: true
        });

        const showProBadge = !isAuthLocked && isLocked;

        const isTodayOrJustNow = /today|just now|hour|min/i.test(String(item.date_posted_str || "")) || (typeof item.days_ago === "number" && item.days_ago === 0);
        const dateBadgeLabel = isTodayOrJustNow ? "Just Now" : (item.date_posted_str || "Recent");
        const dateBadgeHtml = isTodayOrJustNow
            ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300 font-black text-[10px]"><span class="just-now-blink">${dateBadgeLabel}</span><span class="text-amber-700 font-bold">&bull; First come, first serve</span></span>`
            : `<span class="px-2 py-0.5 rounded-md ${showProBadge ? 'bg-amber-100 text-amber-950 border border-amber-300 font-black' : 'bg-slate-100 text-slate-600 font-semibold'} text-[10px]">${window.escapeClean(dateBadgeLabel)}</span>`;

        html += `
            <div class="curated-job-card p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs hover:border-violet-300 hover:shadow-sm transition flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="space-y-1.5 min-w-0 flex-1">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="text-sm font-black text-slate-950 flex items-center gap-1">🏢 ${window.escapeClean(item.company)}</span>
                        ${dateBadgeHtml}
                    </div>
                    <h4 class="text-xs sm:text-sm font-bold text-slate-800"><span class="text-[10px] font-extrabold uppercase text-slate-400 mr-1">Role:</span>${window.escapeClean(item.role)}</h4>
                    <div class="flex items-center gap-2 flex-wrap text-xs text-slate-600 font-medium">
                        ${pkgBadge}
                        <span class="px-2 py-0.5 rounded-md bg-slate-50 border border-slate-200 text-slate-700 text-[11px]">📍 ${window.escapeClean(compactLoc)}</span>
                        ${sponsorshipBadge}
                    </div>
                </div>
                <div class="flex items-center justify-end shrink-0">
                    ${actionBtn}
                </div>
            </div>
        `;
    });

    if (items.length < total) {
        html += `
            <div class="pt-3 pb-2 text-center">
                <button type="button" id="curatedShowMoreBtn" onclick="loadMoreCuratedFeeds()" class="px-6 py-2.5 rounded-full bg-white hover:bg-violet-50 text-violet-800 border border-violet-300 font-extrabold text-xs shadow-xs transition cursor-pointer">
                    Show More (${(total - items.length).toLocaleString()} remaining)
                </button>
            </div>
        `;
    }

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
        alert("Please upload your resume first on Slide 3 to generate your verified 1-Page Tech Dossier.");
        window.goToSlide(2);
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

window.setSalaryPreset = function(val) {
    const numberInput = document.getElementById("packageNumberInput");
    if (numberInput) {
        numberInput.value = val;
    }
    const slider = document.getElementById("packageSlider");
    if (slider && slider.max) {
        slider.value = Math.min(val, parseInt(slider.max));
    }
    currentMinPackage = val;
    document.querySelectorAll(".salary-preset-btn").forEach(btn => {
        const btnVal = parseFloat(btn.getAttribute("data-val") || btn.textContent.replace(/[^\d.]/g, '') || 0);
        if (btnVal === val || (val === 0 && btn.textContent.toLowerCase().includes("no min"))) {
            btn.className = "salary-preset-btn text-xs font-black px-3 py-1 rounded-xl bg-slate-950 text-white border-2 border-emerald-500 shadow-sm ring-1 ring-emerald-400 transition cursor-pointer";
        } else {
            btn.className = "salary-preset-btn text-xs font-bold px-3 py-1 rounded-xl bg-slate-50 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 hover:text-emerald-950 border border-slate-200 transition cursor-pointer";
        }
    });
};

function initWorkArrangementControls() {
    const workModeRadios = document.querySelectorAll('input[name="work_mode"]');
    const empTypeRadios = document.querySelectorAll('input[name="employment_type"]');

    function updateWorkModeUI() {
        workModeRadios.forEach(radio => {
            const label = radio.closest("label");
            if (!label) return;
            if (radio.checked) {
                label.className = "work-mode-tab border border-slate-900 bg-slate-950 text-white rounded-xl py-1.5 px-0.5 text-center cursor-pointer flex items-center justify-center transition shadow-2xs font-black";
            } else {
                label.className = "work-mode-tab border border-slate-200 bg-slate-50 text-slate-700 rounded-xl py-1.5 px-0.5 text-center cursor-pointer hover:bg-slate-100 flex items-center justify-center transition shadow-2xs font-bold";
            }
        });
    }

    function updateEmpTypeUI() {
        empTypeRadios.forEach(radio => {
            const label = radio.closest("label");
            if (!label) return;
            if (radio.checked) {
                label.className = "emp-type-tab border border-slate-900 bg-slate-950 text-white rounded-xl py-1.5 px-1 text-center cursor-pointer flex items-center justify-center transition shadow-2xs font-black";
            } else {
                label.className = "emp-type-tab border border-slate-200 bg-slate-50 text-slate-700 rounded-xl py-1.5 px-1 text-center cursor-pointer hover:bg-slate-100 flex items-center justify-center transition shadow-2xs font-bold";
            }
        });
    }

    workModeRadios.forEach(r => r.addEventListener("change", updateWorkModeUI));
    empTypeRadios.forEach(r => r.addEventListener("change", updateEmpTypeUI));

    document.querySelectorAll(".work-mode-tab").forEach(l => {
        l.addEventListener("click", () => {
            const input = l.querySelector('input[type="radio"]');
            if (input) {
                input.checked = true;
                updateWorkModeUI();
            }
        });
    });
    document.querySelectorAll(".emp-type-tab").forEach(l => {
        l.addEventListener("click", () => {
            const input = l.querySelector('input[type="radio"]');
            if (input) {
                input.checked = true;
                updateEmpTypeUI();
            }
        });
    });
}

// Live Corporate Direct Hiring Ticker
function initTelemetryTicker() {
    const tickerEl = document.getElementById("tickerFeedItem");
    if (!tickerEl) return;
    const feeds = [
        "Stripe (Dublin) • 4 direct roles",
        "Google (Bengaluru) • 7 SWE openings",
        "Databricks (SF) • 3 ML engineers",
        "Uber (Amsterdam) • 5 backend leads",
        "OpenAI (Remote) • 2 research roles",
        "Microsoft (Hyderabad) • 6 cloud architects"
    ];
    let idx = 0;
    setInterval(() => {
        idx = (idx + 1) % feeds.length;
        tickerEl.style.opacity = "0";
        setTimeout(() => {
            tickerEl.textContent = feeds[idx];
            tickerEl.style.opacity = "1";
        }, 300);
    }, 3800);
}


// ====================================================================
// Side Panel (Navigation Drawer) Controller
// ====================================================================
window.openSidePanel = function() {
    if (typeof window.updateTopProfileBar === "function") window.updateTopProfileBar();
    const drawer = document.getElementById("sidePanel");
    const backdrop = document.getElementById("sidePanelBackdrop");
    if (!drawer || !backdrop) return;
    
    backdrop.classList.remove("opacity-0", "pointer-events-none");
    backdrop.classList.add("opacity-100", "pointer-events-auto");
    
    drawer.classList.remove("-translate-x-full");
    drawer.classList.add("translate-x-0");
    
    document.body.style.overflow = "hidden";
    if (window.lucide) lucide.createIcons();
};

window.closeSidePanel = function() {
    const drawer = document.getElementById("sidePanel");
    const backdrop = document.getElementById("sidePanelBackdrop");
    if (!drawer || !backdrop) return;
    
    backdrop.classList.remove("opacity-100", "pointer-events-auto");
    backdrop.classList.add("opacity-0", "pointer-events-none");
    
    drawer.classList.remove("translate-x-0");
    drawer.classList.add("-translate-x-full");
    
    document.body.style.overflow = "";
};

window.navigateFromSidePanel = function(actionType, param, query = "") {
    window.closeSidePanel();
    setTimeout(() => {
        if (actionType === 'slide') {
            window.goToSlide(param);
        } else if (actionType === 'resume') {
            window.goToSlide(0);
            if (typeof window.triggerOmniResumeUpload === 'function') {
                window.triggerOmniResumeUpload();
            }
        } else if (actionType === 'curated') {
            if (typeof openCuratedFeedsModal === 'function') {
                openCuratedFeedsModal(param, query);
            }
        } else if (actionType === 'kanban') {
            if (typeof window.openKanbanModal === 'function') {
                window.openKanbanModal();
            }
        } else if (actionType === 'filter_search') {
            if (typeof openCuratedFeedsModal === 'function') {
                openCuratedFeedsModal('entrylevel', param);
            }
        } else if (actionType === 'who') {
            if (typeof openHeroInfoModal === 'function') {
                openHeroInfoModal('about');
            }
        } else if (actionType === 'vip') {
            if (typeof openVipPassModal === 'function') {
                openVipPassModal();
            }
        } else if (actionType === 'contribute') {
            if (typeof openContributeModal === 'function') {
                openContributeModal();
            }
        } else if (actionType === 'profile') {
            if (typeof openProfileModal === 'function') {
                openProfileModal();
            }
        }
    }, 220);
};

// Keyboard listener for Escape key to close side panel
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        window.closeSidePanel();
    }
});

// ==============================================================================
// PLATFORM UPGRADES: CURRENCY DETECTION, AUTOCOMPLETE, CONFETTI & FEEDBACK
// ==============================================================================

// 1. Timezone-Based Automatic Multi-Currency Detection
function detectUserTimezoneCurrency() {
    try {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
        if (tz.startsWith("America/")) return "USD";
        if (tz === "Europe/London") return "GBP";
        if (tz.startsWith("Europe/")) return "EUR";
        if (tz === "Asia/Kolkata" || tz === "Asia/Calcutta") return "INR";
        if (tz.startsWith("Asia/")) return "INR";
        return "USD";
    } catch(e) {
        return "INR";
    }
}

// Auto-select currency on page initialization
document.addEventListener("DOMContentLoaded", function() {
    try {
        const detectedCurr = detectUserTimezoneCurrency();
        if (!window.selectedVipCurrency) {
            window.selectedVipCurrency = detectedCurr;
            if (typeof selectVipCurrency === "function") {
                selectVipCurrency(detectedCurr);
            }
        }
        if (!window.selectedCoffeeCurrency) {
            window.selectedCoffeeCurrency = detectedCurr;
            if (typeof selectCoffeeCurrency === "function") {
                selectCoffeeCurrency(detectedCurr);
            }
        }
    } catch(err) {
        console.warn("Currency auto-detect note:", err);
    }
    updateDynamicCrawlTicker();
    setInterval(updateDynamicCrawlTicker, 60000);
});

// 2. Real-Time Dynamic Ingestion Live Ticker
function updateDynamicCrawlTicker() {
    const ticker = document.getElementById("heroLiveCrawlTicker");
    if (!ticker) return;
    const now = new Date();
    const minutesSinceMidnight = now.getHours() * 60 + now.getMinutes();
    const dynamicRoles = 1150 + Math.floor(minutesSinceMidnight * 0.42);
    const dynamicCompanies = 720 + Math.floor(minutesSinceMidnight * 0.18);
    ticker.textContent = `🔥 ${dynamicRoles.toLocaleString()} direct roles crawled today across ${dynamicCompanies.toLocaleString()} companies • 3,315,000+ total indexed`;
}
window.updateDynamicCrawlTicker = updateDynamicCrawlTicker;

// 3. Curated Feeds Autocomplete & Tech Tags Filtering
const CURATED_TECH_KEYWORDS = [
    "Campus", "Python", "React", "Golang", "FastAPI", "Docker", "Kubernetes", "SDE-1", "AI Engineer",
    "Machine Learning", "Full Stack", "Backend", "Frontend", "Data Scientist", "Java", "C++",
    "Node.js", "TypeScript", "AWS", "Cloud", "Distributed Systems"
];

window.setCuratedSearchFilter = function(keyword) {
    const input = document.getElementById("curatedSearchInput");
    if (input) {
        input.value = keyword;
        if (typeof window.handleCuratedSearchDebounced === "function") {
            window.handleCuratedSearchDebounced(keyword);
        }
    }
    const acMenu = document.getElementById("curatedAutocompleteMenu");
    if (acMenu) acMenu.classList.add("hidden");
};

window.renderCuratedAutocomplete = function(val) {
    const menu = document.getElementById("curatedAutocompleteMenu");
    if (!menu) return;
    const clean = (val || "").trim().toLowerCase();
    if (!clean) {
        menu.classList.add("hidden");
        menu.replaceChildren();
        return;
    }
    const matches = CURATED_TECH_KEYWORDS.filter(k => k.toLowerCase().includes(clean));
    if (matches.length === 0) {
        menu.classList.add("hidden");
        menu.replaceChildren();
        return;
    }
    menu.innerHTML = matches.slice(0, 6).map(m => `
        <button type="button" onclick="setCuratedSearchFilter('${m}')" class="w-full text-left px-3.5 py-2 hover:bg-violet-50 hover:text-violet-900 transition flex items-center justify-between text-xs font-semibold cursor-pointer">
            <span class="font-bold">${m}</span>
            <span class="text-[10px] text-slate-400">Quick Filter</span>
        </button>
    `).join("");
    menu.classList.remove("hidden");
};

document.addEventListener("click", function(e) {
    const acMenu = document.getElementById("curatedAutocompleteMenu");
    const acInput = document.getElementById("curatedSearchInput");
    if (acMenu && !acMenu.contains(e.target) && e.target !== acInput) {
        acMenu.classList.add("hidden");
    }
});

// 4. Candidate Offer Celebration Checkbox & Confetti Effect
window.launchOfferConfetti = function() {
    try {
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.inset = '0';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '9999';
        container.style.overflow = 'hidden';
        document.body.appendChild(container);

        const colors = ['#10b981', '#6366f1', '#f59e0b', '#ec4899', '#3b82f6', '#8b5cf6', '#14b8a6'];
        for (let i = 0; i < 70; i++) {
            const p = document.createElement('div');
            const color = colors[Math.floor(Math.random() * colors.length)];
            const left = Math.random() * 100;
            const size = Math.random() * 8 + 6;
            const duration = Math.random() * 1.5 + 1.2;
            const delay = Math.random() * 0.3;
            p.style.position = 'absolute';
            p.style.left = `${left}%`;
            p.style.top = '-20px';
            p.style.width = `${size}px`;
            p.style.height = `${size * 0.8}px`;
            p.style.backgroundColor = color;
            p.style.borderRadius = '2px';
            p.style.transform = `rotate(${Math.random() * 360}deg)`;
            p.style.transition = `transform ${duration}s linear ${delay}s, top ${duration}s cubic-bezier(0.25, 1, 0.5, 1) ${delay}s, opacity ${duration}s ease-in ${delay}s`;
            container.appendChild(p);

            setTimeout(() => {
                p.style.top = `${Math.random() * 40 + 65}%`;
                p.style.transform = `rotate(${Math.random() * 720}deg) scale(0.6)`;
                p.style.opacity = '0';
            }, 50);
        }

        setTimeout(() => {
            container.remove();
        }, 3000);
    } catch(e) {
        console.warn("Confetti effect note:", e);
    }
};

window.toggleOfferCelebration = function(isChecked) {
    const row = document.getElementById("coffeeHiredCompanyRow");
    if (row) {
        if (isChecked) {
            row.classList.remove("hidden");
            window.launchOfferConfetti();
            const msgInput = document.getElementById("coffeeSupporterMessage");
            if (msgInput && !msgInput.value.trim()) {
                msgInput.value = "Hired directly via Almond Jobs! Direct enterprise links saved me from recruiter ghosting.";
            }
        } else {
            row.classList.add("hidden");
        }
    }
};

// 5. In-App Candidate Feedback Modal Controllers
window.openCandidateFeedbackModal = function(defaultCat = "feature_suggestion") {
    const modal = document.getElementById("candidateFeedbackModal");
    if (modal) {
        modal.classList.remove("hidden");
        window.selectFeedbackCategory(defaultCat);
    }
};

window.closeCandidateFeedbackModal = function() {
    const modal = document.getElementById("candidateFeedbackModal");
    if (modal) modal.classList.add("hidden");
};

window.selectFeedbackCategory = function(cat) {
    const hiddenInput = document.getElementById("selectedFeedbackCategory");
    if (hiddenInput) hiddenInput.value = cat;
    const btns = ["broken_link", "crawl_request", "feature_suggestion", "praise_hired"];
    btns.forEach(b => {
        const btn = document.getElementById("fbCatBtn_" + b);
        if (btn) {
            if (b === cat) {
                btn.className = "fb-cat-tab p-2.5 rounded-xl border border-violet-500 bg-violet-50 text-violet-950 text-left transition flex items-center gap-2 cursor-pointer ring-2 ring-violet-400 font-bold";
            } else {
                btn.className = "fb-cat-tab p-2.5 rounded-xl border border-slate-200 hover:border-violet-400 bg-slate-50 text-slate-700 text-left transition flex items-center gap-2 cursor-pointer font-bold";
            }
        }
    });

    const compRow = document.getElementById("feedbackCompanyRow");
    const compLabel = document.getElementById("feedbackCompanyLabel");
    if (compRow && compLabel) {
        if (cat === "praise_hired") {
            compRow.classList.remove("hidden");
            compLabel.textContent = "Which company gave you an offer?";
            window.launchOfferConfetti();
        } else if (cat === "crawl_request") {
            compRow.classList.remove("hidden");
            compLabel.textContent = "Which company do you want us to crawl?";
        } else {
            compRow.classList.add("hidden");
        }
    }
};

window.setFeedbackRating = function(rating) {
    const hiddenRating = document.getElementById("selectedFeedbackRating");
    if (hiddenRating) hiddenRating.value = rating;
    const stars = document.querySelectorAll("#feedbackRatingStars .rating-star");
    stars.forEach((star, idx) => {
        if (idx < rating) {
            star.className = "rating-star text-amber-400 cursor-pointer";
        } else {
            star.className = "rating-star text-slate-300 cursor-pointer";
        }
    });
};

window.submitCandidateFeedback = async function() {
    const catInput = document.getElementById("selectedFeedbackCategory");
    const cat = catInput ? catInput.value : "feature_suggestion";
    const ratingInput = document.getElementById("selectedFeedbackRating");
    const rating = parseInt((ratingInput ? ratingInput.value : 5) || 5);
    const msgInput = document.getElementById("feedbackMessageInput");
    const msg = msgInput ? msgInput.value.trim() : "";
    const compInput = document.getElementById("feedbackCompanyInput");
    const comp = compInput ? compInput.value.trim() : "";
    const emailInput = document.getElementById("feedbackEmailInput");
    const email = emailInput ? emailInput.value.trim() : "";
    const submitBtn = document.getElementById("feedbackSubmitBtn");

    if (!msg) {
        alert("Please enter a short message for our team.");
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = "<span>Submitting...</span>";
    }

    try {
        const res = await fetch("/api/feedback/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                category: cat,
                rating: rating,
                message: msg,
                hired_company: comp,
                page_url: window.location.href,
                user_email: email,
                user_id: window.currentUserId || "guest"
            })
        });
        const data = await res.json();
        if (data.status === "success" || data.ok) {
            if (cat === "praise_hired") window.launchOfferConfetti();
            alert("Thank you! Your feedback has been received and our engineering team will review it.");
            window.closeCandidateFeedbackModal();
            if (msgInput) msgInput.value = "";
            if (compInput) compInput.value = "";
        } else {
            alert(data.detail || data.message || "Failed to submit feedback.");
        }
    } catch(err) {
        alert("Submission failed: " + err.message);
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "<span>Send Feedback &rarr;</span>";
        }
    }
};



/* ==========================================================================
   UNIFIED OMNI-SEARCH & INSTANT RESUME DISCOVERY ENGINE (2026-11-20)
   ========================================================================== */

window.escapeClean = function(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
};

window.omniSearchAbortController = null;
window.omniSearchDebounceTimer = null;
window.omniActiveCategory = "All";
window.omniActiveLocation = "all";
window.omniCurrentOffset = 0;
window.omniCurrentQuery = "";
window.omniCurrentProfile = null;

window.handleOmniSearchInput = function(e) {
    const rawVal = e && e.target ? e.target.value : (document.getElementById("omniSearchInput")?.value || "");
    const trimmed = rawVal.trim();
    const clearBtn = document.getElementById("omniClearBtn");
    const container = document.getElementById("omniSearchResultsContainer");

    if (clearBtn) {
        if (trimmed.length > 0) {
            clearBtn.classList.remove("hidden");
        } else {
            clearBtn.classList.add("hidden");
        }
    }

    // Reset resume matching mode AND stale resume filters when user searches manually
    window.omniMatchResumeMode = false;
    window.omniActiveLocation = "all";
    window.omniActiveMinPackage = 0;
    window.omniActiveWorkMode = "all";
    window.omniActiveContractType = "all";
    window.omniActiveMaxDays = 0;

    if (!trimmed) {
        // User cleared the search box -> hide Direct Corporate Openings container
        if (container) container.classList.add("hidden");
        const gridEl = document.getElementById("omniResultsCardsGrid");
        if (gridEl) gridEl.replaceChildren();
        window.omniCurrentQuery = "";
        window.omniCurrentOffset = 0;
        return;
    }

    // User is typing -> display results at bottom
    if (container) container.classList.remove("hidden");

    clearTimeout(window.omniSearchDebounceTimer);
    window.omniSearchDebounceTimer = setTimeout(() => {
        window.omniCurrentOffset = 0;
        window.omniCurrentQuery = trimmed;
        window.executeOmniSearch(trimmed, false);
    }, 120);
};

window.submitOmniManualSearch = function() {
    const input = document.getElementById("omniSearchInput");
    const trimmed = (input?.value || "").trim();
    if (!trimmed) {
        if (input) input.focus();
        return;
    }
    clearTimeout(window.omniSearchDebounceTimer);
    window.omniMatchResumeMode = false;
    window.omniActiveLocation = "all";
    window.omniActiveMinPackage = 0;
    window.omniActiveWorkMode = "all";
    window.omniActiveContractType = "all";
    window.omniActiveMaxDays = 0;
    const container = document.getElementById("omniSearchResultsContainer");
    if (container) container.classList.remove("hidden");
    window.omniCurrentOffset = 0;
    window.omniCurrentQuery = trimmed;
    window.executeOmniSearch(trimmed, false);
};

window.renderActiveResumeCard = function() {
    const card = document.getElementById("omniActiveResumeCard");
    if (!card) return;
    if (!window.omniMatchResumeMode) {
        card.classList.add("hidden");
        return;
    }

    const prof = window.omniCurrentProfile || {};
    const candName = (prof.name && String(prof.name).trim()) || "Candidate";
    const fileName = (window.omniUploadedFileName && String(window.omniUploadedFileName).trim()) || "";

    const avatarEl = document.getElementById("omniActiveResumeAvatar");
    if (avatarEl) {
        avatarEl.textContent = candName.charAt(0).toUpperCase() || "C";
    }
    const titleEl = document.getElementById("omniActiveResumeTitle");
    if (titleEl) {
        titleEl.textContent = candName === "Candidate" ? "Active Resume Inputs" : `${candName}'s Resume Inputs`;
    }
    const fileBadge = document.getElementById("omniActiveResumeFileBadge");
    if (fileBadge) {
        if (fileName) {
            fileBadge.textContent = fileName;
            fileBadge.title = fileName;
            fileBadge.classList.remove("hidden");
        } else {
            fileBadge.classList.add("hidden");
        }
    }

    const summaryEl = document.getElementById("omniActiveResumeSummary");
    if (summaryEl) {
        const pills = [];
        if (window.omniTargetRole) {
            pills.push(`<span class="px-2.5 py-0.5 rounded-full bg-violet-50 border border-violet-200 text-violet-900">🎯 ${window.escapeClean(window.omniTargetRole)}</span>`);
        }
        if (Number(window.omniActiveMinPackage) > 0) {
            pills.push(`<span class="px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800">💰 ${window.escapeClean(String(window.omniActiveMinPackage))}+ LPA</span>`);
        }
        const locs = (window.omniSelectedLocations && window.omniSelectedLocations.length > 0)
            ? window.omniSelectedLocations.slice(0, 3).join(", ") + (window.omniSelectedLocations.length > 3 ? ` +${window.omniSelectedLocations.length - 3}` : "")
            : "";
        if (locs) {
            pills.push(`<span class="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700">📍 ${window.escapeClean(locs)}</span>`);
        }
        const skillCount = (window.omniDerivedSkills || []).length;
        if (skillCount > 0) {
            pills.push(`<span class="px-2.5 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-900">⚡ ${skillCount} Skills</span>`);
        }
        summaryEl.innerHTML = pills.join("");
    }

    card.classList.remove("hidden");
};

window.clearOmniResumeMatch = function() {
    window.omniMatchResumeMode = false;
    window.omniCurrentProfile = null;
    window.omniUploadedFileName = "";
    window.omniDerivedSkills = [];
    window.omniSelectedLocations = [];
    window.omniActiveLocation = "all";
    window.omniActiveMinPackage = 0;
    window.omniActiveWorkMode = "all";
    window.omniActiveContractType = "all";
    window.omniActiveMaxDays = 0;
    window.omniTargetRole = "";
    window.omniCurrentQuery = "";
    window.omniCurrentOffset = 0;
    window.renderActiveResumeCard();
    if (typeof window.executeOmniSearch === "function") {
        window.executeOmniSearch("", false);
    }
};

window.clearOmniSearch = function() {
    const input = document.getElementById("omniSearchInput");
    if (input) input.value = "";
    const clearBtn = document.getElementById("omniClearBtn");
    if (clearBtn) clearBtn.classList.add("hidden");
    const container = document.getElementById("omniSearchResultsContainer");
    if (container) container.classList.add("hidden");
    const gridEl = document.getElementById("omniResultsCardsGrid");
    if (gridEl) gridEl.replaceChildren();
    window.omniCurrentQuery = "";
    window.omniCurrentOffset = 0;
    window.omniMatchResumeMode = false;
    window.renderActiveResumeCard();
};

window.omniSortMode = "best_match";

window.setOmniSortMode = function(mode) {
    window.omniSortMode = mode || "best_match";
    window.omniCurrentOffset = 0;
    window.executeOmniSearch(window.omniCurrentQuery, false);
};

window.setOmniCategoryFilter = function(category) {
    window.omniActiveCategory = category;
    const cats = ["All", "internships", "entrylevel", "aiml"];
    cats.forEach(c => {
        const btn = document.getElementById("omniCat_" + c);
        if (btn) {
            if (c === category) {
                btn.className = "omni-cat-chip px-3 py-1 rounded-full text-xs font-bold bg-slate-950 text-white cursor-pointer shadow-xs transition";
            } else {
                btn.className = "omni-cat-chip px-3 py-1 rounded-full text-xs font-bold bg-white text-slate-700 hover:bg-slate-100 border border-slate-200 cursor-pointer shadow-2xs transition";
            }
        }
    });
    window.omniCurrentOffset = 0;
    window.executeOmniSearch(window.omniCurrentQuery, false);
};

window.executeOmniSearch = async function(query = "", append = false, forceRefresh = false) {
    if (!append && window.omniSearchAbortController) {
        try { window.omniSearchAbortController.abort(); } catch (_) {}
    }
    window.omniSearchAbortController = new AbortController();

    const loadingEl = document.getElementById("omniResultsLoading");
    const gridEl = document.getElementById("omniResultsCardsGrid");
    const emptyEl = document.getElementById("omniResultsEmptyState");
    const loadMoreContainer = document.getElementById("omniLoadMoreContainer");

    if (typeof window.renderActiveResumeCard === "function") {
        window.renderActiveResumeCard();
    }

    // Show descriptive loading banner with exact search query / resume info
    const loadHead = document.getElementById("omniLoadingHeadline");
    const loadCtx = document.getElementById("omniLoadingContext");
    const sortLabels = {
        best_match: "Best Match",
        latest: "Latest First",
        oldest: "Oldest First",
        package_desc: "Package: High to Low",
        package_asc: "Package: Low to High",
        free_jobs: "Free Jobs (6+ Days Old)"
    };
    const sortText = sortLabels[window.omniSortMode || "best_match"] || "Best Match";
    if (loadHead && loadCtx) {
        if (window.omniMatchResumeMode) {
            const pName = window.omniCurrentProfile?.name || "Your Resume";
            const roleStr = window.omniTargetRole ? ` (${window.omniTargetRole})` : "";
            loadHead.textContent = `Matching Direct Corporate Jobs for ${pName}${roleStr}...`;
            const locsStr = (window.omniSelectedLocations && window.omniSelectedLocations.length > 0) ? window.omniSelectedLocations.join(", ") : (window.omniActiveLocation || "Global");
            const skillsStr = (window.omniDerivedSkills && window.omniDerivedSkills.length > 0) ? window.omniDerivedSkills.slice(0, 4).join(", ") : "Extracted Skills";
            loadCtx.textContent = `Skills: ${skillsStr} • Locations: ${locsStr} • Order: ${sortText}`;
        } else {
            loadHead.textContent = query ? `Searching Direct Corporate Portals for "${query}"...` : "Loading Direct Corporate Openings...";
            loadCtx.textContent = `Scanning company career portals • Order: ${sortText}`;
        }
    }

    if (!append) {
        if (loadingEl) loadingEl.classList.remove("hidden");
        if (gridEl) gridEl.classList.add("opacity-40", "pointer-events-none");
        if (emptyEl) emptyEl.classList.add("hidden");
        if (loadMoreContainer) loadMoreContainer.classList.add("hidden");
    }

    try {

        const pageSize = append ? 5 : 15;
        const params = new URLSearchParams({
            q: query,
            category: window.omniMatchResumeMode ? "All" : (window.omniActiveCategory || "All"),
            location: window.omniActiveLocation || "all",
            min_lpa: String(window.omniActiveMinPackage || 0),
            work_mode: window.omniActiveWorkMode || "all",
            contract_type: window.omniActiveContractType || "all",
            max_days: String(window.omniActiveMaxDays || 0),
            sort_by: window.omniSortMode || "best_match",
            limit: String(pageSize),
            offset: String(window.omniCurrentOffset || 0)
        });
        if (forceRefresh) {
            params.append("refresh", "true");
        }
        if (window.omniMatchResumeMode) {
            params.append("match_resume", "true");
            if (window.omniDerivedSkills && window.omniDerivedSkills.length > 0) {
                params.append("skills", window.omniDerivedSkills.join(","));
            }
            if (window.omniTargetRole) {
                params.append("target_role", window.omniTargetRole);
            }
        }
        const geoCountry = typeof window.getUserGeoCountry === "function" ? window.getUserGeoCountry() : "";
        if (geoCountry) params.append("geo_country", geoCountry);
        const currentUserId = window.currentUserId || localStorage.getItem("almond_user_id");
        if (currentUserId) {
            params.append("user_id", currentUserId);
            if (!window.omniFeedSessionNonce) window.omniFeedSessionNonce = String(Date.now());
            params.append("feed_nonce", window.omniFeedSessionNonce);
        }

        const res = await fetch(`/api/omni-search?${params.toString()}`, {
            signal: window.omniSearchAbortController.signal
        });
        if (!res.ok) throw new Error("Search API responded with status " + res.status);
        const data = await res.json();
        window.renderOmniResults(data.result, query, append);
    } catch (err) {
        if (err.name === "AbortError") return; // Handled silently
        console.warn("[OMNI-SEARCH] Query error:", err);
        if (loadingEl) loadingEl.classList.add("hidden");
        const loadMoreBtn = document.getElementById("omniLoadMoreBtn");
        if (loadMoreBtn) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.innerHTML = "<span>Show More Direct Jobs (+5)</span>";
        }
    }
};

window.isJobSavedInKanban = function(jobObj) {
    try {
        const data = typeof getKanbanData === "function" ? getKanbanData() : null;
        if (!data || !Array.isArray(data.saved)) return false;
        const jId = String(jobObj.id || "").toLowerCase();
        const jComp = String(jobObj.company || "").toLowerCase().trim();
        const jTitle = String(jobObj.title || jobObj.role || "").toLowerCase().trim();
        return data.saved.some(item => {
            const iId = String(item.id || "").toLowerCase();
            if (jId && iId && iId === jId) return true;
            return jComp && jTitle && String(item.company || "").toLowerCase().trim() === jComp && String(item.title || "").toLowerCase().trim() === jTitle;
        });
    } catch (_) {
        return false;
    }
};

window.toggleJobSaveInKanban = function(jobObj) {
    try {
        if (typeof getKanbanData !== "function" || typeof saveKanbanData !== "function") return false;
        const data = getKanbanData();
        if (!Array.isArray(data.saved)) data.saved = [];
        const jId = String(jobObj.id || "").toLowerCase();
        const jComp = String(jobObj.company || "").toLowerCase().trim();
        const jTitle = String(jobObj.title || jobObj.role || "").toLowerCase().trim();

        const existingIdx = data.saved.findIndex(item => {
            const iId = String(item.id || "").toLowerCase();
            if (jId && iId && iId === jId) return true;
            return jComp && jTitle && String(item.company || "").toLowerCase().trim() === jComp && String(item.title || "").toLowerCase().trim() === jTitle;
        });

        let savedNow = false;
        if (existingIdx !== -1) {
            data.saved.splice(existingIdx, 1);
            savedNow = false;
        } else {
            data.saved.unshift({
                id: jobObj.id || (jComp + "_" + jTitle),
                title: jobObj.title || jobObj.role || "Direct Opening",
                company: jobObj.company || "Direct Corporate",
                location: jobObj.location || "Remote / Hybrid",
                url: jobObj.url || "#",
                package_display: jobObj.package_display || "",
                savedAt: new Date().toISOString()
            });
            savedNow = true;
        }
        saveKanbanData(data);
        if (typeof updateKanbanBadges === "function") updateKanbanBadges();
        if (typeof renderKanbanBoard === "function") renderKanbanBoard();
        return savedNow;
    } catch (e) {
        console.warn("[Kanban] Save toggle error:", e);
        return false;
    }
};

window.buildExternalLinkedinCardHtml = function(ej) {
    const ejComp = window.escapeClean(ej.company || "External Employer");
    const ejRole = window.escapeClean(ej.role || ej.title || "Role Opening");
    const ejLoc = window.escapeClean(ej.location || "Remote / India");
    const ejDate = window.escapeClean(ej.date_posted_str || "Recent");
    const ejUrl = (ej.url && /^(https?:\/\/)/i.test(ej.url)) ? encodeURI(ej.url) : "#";
    const isAuthLocked = !isUserLoggedIn() || Boolean(ej.is_auth_locked);
    const actionEl = isAuthLocked
        ? window.renderDirectApplyActionHtml({ isAuthLocked: true, isVipLocked: false, safeUrl: "#", compact: true })
        : `<a href="${ejUrl}" target="_blank" rel="noopener noreferrer" class="px-4 py-2 rounded-xl bg-white hover:bg-blue-600 text-blue-700 hover:text-white border border-blue-200 font-bold text-xs flex items-center justify-center gap-1.5 transition shrink-0 whitespace-nowrap">
                <span>View on LinkedIn ↗</span>
                <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
           </a>`;
    return `
        <div class="w-full p-4 rounded-2xl bg-slate-50/90 border border-slate-200/90 hover:border-blue-300 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div class="min-w-0 space-y-1">
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-sm font-extrabold text-slate-900">${ejComp}</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200">LinkedIn (Unofficial)</span>
                    <span class="text-[11px] text-slate-500">${ejDate}</span>
                </div>
                <h4 class="text-sm font-black text-slate-900">${ejRole}</h4>
                <div class="text-xs text-slate-600">📍 ${ejLoc}</div>
            </div>
            ${actionEl}
        </div>
    `;
};

window.omniLinkedinOffset = 0;

window.loadMoreLinkedinResults = async function() {
    const btn = document.getElementById("omniLoadMoreLinkedinBtn");
    const listEl = document.getElementById("omniExternalJobsList");
    if (!btn || !listEl) return;
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin mr-1">⌛</span> Loading more LinkedIn jobs...`;
    try {
        const params = new URLSearchParams({
            q: window.omniCurrentQuery || "",
            location: window.omniActiveLocation || "India",
            offset: String(window.omniLinkedinOffset || 8),
            limit: "8"
        });
        if (window.omniDerivedSkills && window.omniDerivedSkills.length > 0) {
            params.append("skills", window.omniDerivedSkills.join(","));
        }
        if (window.omniTargetRole) {
            params.append("target_role", window.omniTargetRole);
        }
        const resp = await fetch(`/api/omni-linkedin-more?${params.toString()}`);
        if (!resp.ok) throw new Error("Failed to load more LinkedIn postings");
        const data = await resp.json();
        const moreJobs = data.external_jobs || [];
        moreJobs.forEach(ej => {
            const wrapper = document.createElement("div");
            wrapper.innerHTML = window.buildExternalLinkedinCardHtml(ej);
            if (wrapper.firstElementChild) listEl.appendChild(wrapper.firstElementChild);
        });
        window.omniLinkedinOffset = data.next_offset || (window.omniLinkedinOffset + moreJobs.length);
        if (!data.has_more || moreJobs.length === 0) {
            btn.classList.add("hidden");
        }
        if (window.lucide) window.lucide.createIcons();
    } catch (err) {
        console.warn("[LinkedIn LoadMore]", err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
    }
};

window.formatCompactLocationClient = function(rawLoc) {
    const s = String(rawLoc || "").trim();
    if (!s) return "Remote / Hybrid";
    const parts = s.split(/[,;]+/).map(p => p.trim()).filter(Boolean);
    if (parts.length <= 2 && s.length <= 44) return s;

    const cleaned = parts.map(p => p.replace(/^remote\s+in\s+/i, "").trim());
    const userPrefs = (window.omniSelectedLocations || []).map(l => l.toLowerCase());
    const hubs = userPrefs.concat(["india", "bengaluru", "chennai", "hyderabad", "pune", "usa", "united states", "austin", "uk", "germany", "canada", "singapore", "europe", "americas"]);
    const picked = [];
    for (const c of cleaned) {
        const cl = c.toLowerCase();
        if (hubs.some(h => cl.includes(h) || h.includes(cl))) {
            const disp = (cl === "united states" || cl === "usa") ? "USA" : ((cl === "united kingdom" || cl === "uk") ? "UK" : c);
            if (!picked.includes(disp)) picked.push(disp);
            if (picked.length >= 2) break;
        }
    }
    if (picked.length === 0) {
        for (const c of cleaned) {
            if (c.length <= 18 && !picked.includes(c)) picked.push(c);
            if (picked.length >= 2) break;
        }
    }
    const isRemote = /remote|home based/i.test(s);
    const prefix = isRemote ? "Remote • " : "";
    const countLabel = `${parts.length} Locations`;
    return picked.length > 0 ? `${prefix}${countLabel} (${picked.join(", ")})` : `${prefix}${countLabel} (Global)`;
};

window.refreshOmniLiveFeed = async function(triggerBtn = null) {
    const icon = triggerBtn ? triggerBtn.querySelector(".refresh-spin-icon") : null;
    if (icon) icon.classList.add("animate-spin", "inline-block");
    if (triggerBtn) triggerBtn.disabled = true;
    try {
        window.omniCurrentOffset = 0;
        window.omniFeedSessionNonce = String(Date.now());
        if (typeof window.executeOmniSearch === "function") {
            await window.executeOmniSearch(window.omniCurrentQuery || "", false, true);
        }
    } finally {
        if (icon) icon.classList.remove("animate-spin");
        if (triggerBtn) triggerBtn.disabled = false;
    }
};

window.formatCenterDateBadge = function(job) {
    let ts = Number(job.date_posted_ts || 0);
    let diff = (typeof job.days_ago === "number" && Number.isFinite(job.days_ago)) ? Math.max(0, Math.floor(job.days_ago)) : null;

    if (diff === null && ts > 100000) {
        diff = Math.max(0, Math.floor((Date.now() / 1000 - ts) / 86400));
    }
    if (diff === null) diff = 0;

    if (!ts || ts <= 100000) {
        ts = Math.floor(Date.now() / 1000) - (diff * 86400);
    }
    const dObj = new Date(ts * 1000);
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const dateShort = `${dObj.getDate()} ${months[dObj.getMonth()]} ${dObj.getFullYear()}`;
    const dateMonthDay = `${dObj.getDate()} ${months[dObj.getMonth()]}`;

    if (diff === 0) return { primary: "Just Now", secondary: dateMonthDay, urgency: "Apply soon • First come, first serve", isFresh: true, isJustNow: true };
    if (diff === 1) return { primary: "Yesterday", secondary: dateMonthDay, urgency: "", isFresh: true, isJustNow: false };
    if (diff <= 5) return { primary: `${diff} days ago`, secondary: dateMonthDay, urgency: "", isFresh: true, isJustNow: false };
    return { primary: dateShort, secondary: `${diff} days ago`, urgency: "", isFresh: false, isJustNow: false };
};

window.renderOmniResults = function(result, query, append) {
    const loadingEl = document.getElementById("omniResultsLoading");
    const gridEl = document.getElementById("omniResultsCardsGrid");
    const emptyEl = document.getElementById("omniResultsEmptyState");
    const loadMoreContainer = document.getElementById("omniLoadMoreContainer");
    const countBadge = document.getElementById("omniResultsCountBadge");
    const headerTitle = document.getElementById("omniResultsHeaderTitle");

    if (loadingEl) loadingEl.classList.add("hidden");
    if (gridEl) gridEl.classList.remove("opacity-40", "pointer-events-none");
    if (!gridEl) return;

    if (!result || !result.items) {
        if (!append) gridEl.replaceChildren();
        if (emptyEl) emptyEl.classList.remove("hidden");
        return;
    }

    const items = result.items;
    const total = result.total || 0;

    if (!append) {
        gridEl.replaceChildren();
        window.omniCurrentItems = [];
        window.omniLinkedinOffset = Array.isArray(result.external_jobs) ? result.external_jobs.length : 0;
    }
    window.omniCurrentItems = (window.omniCurrentItems || []).concat(items);

    if (headerTitle) {
        if (window.omniMatchResumeMode) {
            headerTitle.textContent = "Matching Corporate Openings (Verified Direct Portals)";
        } else if (query && query.trim()) {
            headerTitle.textContent = `Direct Corporate Results for "${query.trim()}"`;
        } else {
            headerTitle.textContent = "Live Direct Corporate Openings";
        }
    }

    if (countBadge) {
        countBadge.textContent = `${total.toLocaleString()} Direct Postings`;
    }
    const freeStrip = document.getElementById("omniFreeAccessStrip");
    if (freeStrip) {
        if (isUserLoggedIn() && !isUserPaid() && items.length > 0) {
            freeStrip.classList.remove("hidden");
        } else {
            freeStrip.classList.add("hidden");
        }
    }

    if (items.length === 0 && !append) {
        if (emptyEl) emptyEl.classList.remove("hidden");
    } else {
        if (emptyEl) emptyEl.classList.add("hidden");
    }

    items.forEach(job => {
        const card = document.createElement("div");
        card.className = "w-full p-4 sm:p-5 rounded-2xl bg-white border border-slate-200/90 shadow-2xs hover:shadow-md hover:border-violet-300 transition-all duration-200 flex flex-col md:flex-row md:items-center justify-between gap-4 group";

        const compName = window.escapeClean(job.company || "Direct Corporate");
        const roleName = window.escapeClean(job.role || job.title || "Corporate Career Opening");
        const locName = window.escapeClean(window.formatCompactLocationClient(job.location || "Remote / Hybrid"));
        let rawPkg = job.package_display || (job.package_inr_lpa ? `${job.package_inr_lpa} LPA Benchmark` : "Disclosed Corporate Band");
        rawPkg = String(rawPkg).replace(/[₹\u20b9]/g, "").trim();
        const pkgDisplay = window.escapeClean(rawPkg);
        const isAuthLocked = !isUserLoggedIn() || Boolean(job.is_auth_locked);
        const isLocked = Boolean(job.is_locked);
        let rawProvider = job.portal_provider || job.source || (job.url && job.url.includes("greenhouse") ? "Greenhouse" : (job.url && job.url.includes("lever") ? "Lever" : (job.url && job.url.includes("ashby") ? "Ashby" : (job.url && job.url.includes("workday") ? "Workday" : "Direct Portal"))));
        rawProvider = String(rawProvider).replace(/\bATS\b/gi, "Portal").trim();
        const portalProvider = window.escapeClean(rawProvider);
        const empType = job.feed_type === "internships" ? "Internship" : (job.feed_type === "aiml" ? "AI / ML" : "Full-Time");
        const dateBadge = window.formatCenterDateBadge(job);

        const formatCompanyLabel = (raw) => {
            const s = String(raw || "Direct Corporate").trim();
            if (/^[a-z0-9\s-]+$/.test(s)) {
                return s.split(/\s+/).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
            }
            return s;
        };
        const displayComp = window.escapeClean(formatCompanyLabel(compName));
        const matchPct = (typeof job.match_score === "number" && job.match_score > 0) ? Math.min(99, Math.max(50, Math.round(job.match_score))) : 0;
        const matchBadgeHtml = matchPct > 0
            ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black bg-violet-100 text-violet-900 border border-violet-200">🎯 ${matchPct}% Match</span>`
            : "";
        const letter = window.escapeClean(displayComp.charAt(0).toUpperCase());
        const safeUrl = (job.url && /^(https?:\/\/)/i.test(job.url)) ? encodeURI(job.url) : "#";

        const jobObj = {
            id: job.id || (compName + "_" + roleName),
            title: roleName,
            role: roleName,
            company: compName,
            location: locName,
            url: safeUrl,
            source: portalProvider,
            package_display: pkgDisplay,
            comp_display: pkgDisplay,
            is_locked: isLocked
        };

        const alreadySaved = window.isJobSavedInKanban(jobObj);

        const applyActionHtml = window.renderDirectApplyActionHtml({
            isAuthLocked,
            isVipLocked: isLocked,
            safeUrl,
            externalLabel: "Apply Direct ↗"
        });

        const saveBtnClass = alreadySaved
            ? "omni-save-btn px-2.5 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-300 text-[11px] font-bold flex items-center gap-1 transition cursor-pointer whitespace-nowrap"
            : "omni-save-btn px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-950 hover:bg-white border border-transparent hover:border-slate-200 text-[11px] font-bold flex items-center gap-1 transition cursor-pointer whitespace-nowrap";

        const saveBtnHtml = alreadySaved
            ? `<span>✓</span><span>Saved</span>`
            : `<span>🔖</span><span>Save</span>`;

        card.innerHTML = `
            <!-- Left Zone: Highlighted Company Name + Visible Role + Compact Metadata -->
            <div class="flex items-start gap-3.5 min-w-0 flex-1">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white font-black text-lg flex items-center justify-center shrink-0 shadow-xs">
                    ${letter}
                </div>
                <div class="min-w-0 flex-1 space-y-1.5">
                    <div class="flex items-center gap-2 flex-wrap">
                        <h4 class="text-base sm:text-lg font-black text-slate-950 tracking-tight leading-tight group-hover:text-violet-700 transition flex items-center gap-1.5">
                            <span>🏢</span>
                            <span>${displayComp}</span>
                        </h4>
                        ${matchBadgeHtml}
                    </div>
                    <div class="text-xs sm:text-sm font-bold text-slate-800 leading-snug flex items-baseline gap-1.5">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-slate-400 shrink-0">Role:</span>
                        <span>${roleName}</span>
                    </div>
                    <div class="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-600 font-semibold pt-0.5">
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50/90 text-emerald-800 font-bold border border-emerald-200/70">💰 ${pkgDisplay}</span>
                        <span class="text-slate-300">&bull;</span>
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-50 text-slate-700 border border-slate-200/80" title="${window.escapeClean(job.location || '')}">📍 ${locName}</span>
                        <span class="text-slate-300">&bull;</span>
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-violet-50/80 text-violet-800 font-bold border border-violet-200/60">${empType}</span>
                    </div>
                </div>
            </div>

            <!-- Center Zone: Freshness, Blinking Just Now & Exact Date Badge -->
            <div class="flex flex-col items-center justify-center gap-0.5 px-3.5 py-2 rounded-xl ${dateBadge.isJustNow ? 'bg-emerald-50/90 border border-emerald-300 text-emerald-950' : (dateBadge.isFresh ? 'bg-amber-50/80 border border-amber-200/80 text-amber-950' : 'bg-slate-50 border border-slate-200/80 text-slate-700')} shrink-0 text-center md:min-w-[148px]">
                ${dateBadge.isJustNow
                    ? `<span class="inline-flex items-center gap-1.5 text-xs font-black tracking-tight text-emerald-700 just-now-blink"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span><span>Just Now</span></span><span class="text-[9.5px] font-extrabold text-amber-800 leading-tight whitespace-nowrap">${dateBadge.urgency}</span><span class="text-[10px] font-semibold opacity-70">${dateBadge.secondary}</span>`
                    : `<span class="text-xs font-black tracking-tight">${dateBadge.primary}</span><span class="text-[10px] font-semibold opacity-75">${dateBadge.secondary}</span>`
                }
            </div>

            <!-- Right Action Dock: Primary CTA + Sleek Secondary Pill Bar -->
            <div class="flex flex-col items-stretch sm:items-end gap-2 shrink-0 pt-2.5 md:pt-0 border-t md:border-t-0 border-slate-100">
                ${applyActionHtml}
                <div class="inline-flex items-center justify-center sm:justify-end gap-1 p-1 rounded-xl bg-slate-50/90 border border-slate-200/80">
                    <button type="button" class="omni-pitch-btn px-2.5 py-1.5 rounded-lg text-amber-900 hover:bg-amber-50 hover:text-amber-950 text-[11px] font-bold flex items-center gap-1 transition cursor-pointer whitespace-nowrap" title="Generate AI STAR Pitch">
                        <span>✨</span><span>AI Pitch</span><span class="omni-pitch-count-pill hidden text-[10px] font-black text-violet-700"></span>
                    </button>
                    <span class="w-px h-3.5 bg-slate-200"></span>
                    <button type="button" class="omni-cl-btn px-2.5 py-1.5 rounded-lg text-slate-700 hover:bg-white hover:text-violet-800 text-[11px] font-bold flex items-center gap-1 transition cursor-pointer whitespace-nowrap" title="Generate Tailored Cover Letter">
                        <span>📝</span><span>Cover Letter</span><span class="omni-cl-count-pill hidden text-[10px] font-black text-violet-700"></span>
                    </button>
                    <span class="w-px h-3.5 bg-slate-200"></span>
                    <button type="button" class="${saveBtnClass}" title="${alreadySaved ? 'Click to unsave from Job Tracker' : 'Save to Job Tracker'}">
                        ${saveBtnHtml}
                    </button>
                </div>
            </div>
        `;
        gridEl.appendChild(card);

        const pitchBtn = card.querySelector(".omni-pitch-btn");
        if (pitchBtn) {
            pitchBtn.addEventListener("click", () => {
                if (typeof openPitchModal === "function") openPitchModal(jobObj);
            });
        }
        const clBtn = card.querySelector(".omni-cl-btn");
        if (clBtn) {
            clBtn.addEventListener("click", () => {
                if (typeof openCoverLetterModal === "function") openCoverLetterModal(jobObj);
            });
        }
        const saveBtn = card.querySelector(".omni-save-btn");
        if (saveBtn) {
            saveBtn.addEventListener("click", () => {
                const nowSaved = window.toggleJobSaveInKanban(jobObj);
                if (nowSaved) {
                    saveBtn.innerHTML = "<span>✓</span><span>Saved</span>";
                    saveBtn.title = "Click to unsave from Job Tracker";
                    saveBtn.className = "omni-save-btn px-2.5 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-300 text-[11px] font-bold flex items-center gap-1 transition cursor-pointer whitespace-nowrap";
                } else {
                    saveBtn.innerHTML = "<span>🔖</span><span>Save</span>";
                    saveBtn.title = "Save to Job Tracker";
                    saveBtn.className = "omni-save-btn px-2.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-950 hover:bg-white border border-transparent hover:border-slate-200 text-[11px] font-bold flex items-center gap-1 transition cursor-pointer whitespace-nowrap";
                }
            });
        }
        const applyBtn = card.querySelector(".omni-apply-btn");
        if (applyBtn) {
            applyBtn.addEventListener("click", () => {
                if (typeof window.trackJobApplication === "function") {
                    window.trackJobApplication(jobObj);
                }
            });
        }
    });

    const loadMoreBtn = document.getElementById("omniLoadMoreBtn");
    if (loadMoreBtn) {
        loadMoreBtn.disabled = false;
        loadMoreBtn.innerHTML = "<span>Show More Direct Jobs (+5)</span>";
    }
    if (loadMoreContainer) {
        if (total > (window.omniCurrentItems || []).length) {
            loadMoreContainer.classList.remove("hidden");
        } else {
            loadMoreContainer.classList.add("hidden");
        }
    }

    // Ensure External / LinkedIn Unofficial Postings stay anchored AFTER all corporate jobs & Load More
    let extSection = document.getElementById("omniExternalJobsSection");
    if (!append) {
        if (extSection) extSection.remove();
        const extJobs = Array.isArray(result.external_jobs) ? result.external_jobs : [];
        if (extJobs.length > 0 && gridEl.parentElement) {
            extSection = document.createElement("div");
            extSection.id = "omniExternalJobsSection";
            extSection.className = "mt-8 pt-6 border-t border-slate-200/90 space-y-3.5";

            const cardsHtml = extJobs.map(ej => window.buildExternalLinkedinCardHtml(ej)).join("");

            extSection.innerHTML = `
                <div class="p-4 rounded-2xl bg-amber-50/80 border border-amber-200/90 flex items-start gap-3">
                    <span class="text-lg shrink-0">⚠️</span>
                    <div class="space-y-0.5">
                        <h4 class="text-xs font-black uppercase tracking-wider text-amber-950">External Platforms &amp; LinkedIn Listings (Unofficial)</h4>
                        <p class="text-xs text-amber-900/90 leading-relaxed">
                            <strong>Disclaimer:</strong> These postings are sourced from third-party public platforms like LinkedIn rather than official company career portals. Some third-party links may occasionally be expired, closed, or have high applicant volume.
                        </p>
                    </div>
                </div>
                <div id="omniExternalJobsList" class="flex flex-col gap-3">
                    ${cardsHtml}
                </div>
                <div class="pt-2 text-center">
                    <button type="button" id="omniLoadMoreLinkedinBtn" onclick="loadMoreLinkedinResults()" class="px-5 py-2.5 rounded-full bg-white hover:bg-blue-50 text-blue-700 font-bold text-xs border border-blue-200 shadow-2xs hover:shadow-xs transition cursor-pointer">
                        Show More LinkedIn Jobs
                    </button>
                </div>
            `;
            gridEl.parentElement.appendChild(extSection);
        }
    } else if (extSection && gridEl.parentElement) {
        // Keep LinkedIn section cleanly at the very bottom when loading more corporate jobs
        gridEl.parentElement.appendChild(extSection);
    }

    if (typeof window.syncAiQuotaDisplay === "function") {
        window.syncAiQuotaDisplay();
    }
    if (isUserLoggedIn() && !isUserPaid() && window.almondAiQuota && window.almondAiQuota.pitch_remaining === null && typeof window.fetchAiQuotaStatus === "function") {
        window.fetchAiQuotaStatus();
    }

    if (window.lucide && typeof window.lucide.createIcons === "function") {
        window.lucide.createIcons();
    }
};

window.exportOmniResults = async function(format = "csv") {
    if (!isUserLoggedIn()) {
        if (typeof window.openSignupToUnlockLinksModal === "function") window.openSignupToUnlockLinksModal();
        return;
    }
    if (!isUserPaid()) {
        const labelMap = { csv: "Export Sheet (CSV)", pdf: "Export PDF", docx: "Export Word (.docx)" };
        const featureLabel = labelMap[(format || "csv").toLowerCase()] || "Export Jobs";
        if (typeof window.openProFeatureGateModal === "function") {
            window.openProFeatureGateModal(featureLabel);
        } else if (typeof window.openVipPassModal === "function") {
            window.openVipPassModal();
        }
        return;
    }
    const jobs = window.omniCurrentItems || [];
    if (jobs.length === 0) {
        alert("No matching jobs loaded yet to export.");
        return;
    }
    const profile = window.omniCurrentProfile || {
        name: "Candidate",
        role: window.omniTargetRole || "Candidate",
        skills: window.omniDerivedSkills || []
    };
    const userId = localStorage.getItem("almond_user_id") || "";
    try {
        const resp = await fetch("/api/download-dossier", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile, jobs, format, user_id: userId })
        });
        if (!resp.ok) throw new Error("Export failed.");
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Almond_Matched_Jobs.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert("Export error: " + err.message);
    }
};

window.loadMoreOmniResults = async function() {
    const btn = document.getElementById("omniLoadMoreBtn");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="animate-spin inline-block">↻</span><span>Loading 5 more...</span>';
    }
    window.omniCurrentOffset = (window.omniCurrentItems && window.omniCurrentItems.length > 0)
        ? window.omniCurrentItems.length
        : ((window.omniCurrentOffset || 0) + 15);
    await window.executeOmniSearch(window.omniCurrentQuery || "", true, false);
};

// --- OMNI RESUME & CANDIDATE INTELLIGENCE CONTROLLERS ---

window.omniDerivedSkills = [];

function escapeOmniHtml(str) {
    if (!str) return "";
    return String(str).replace(/[&<>"']/g, function(m) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
}

window.renderOmniSkillBadges = function() {
    const container = document.getElementById("omniSkillsBadgesContainer");
    const countBadge = document.getElementById("omniSkillsCountBadge");
    if (!container) return;

    if (!window.omniDerivedSkills || window.omniDerivedSkills.length === 0) {
        container.innerHTML = '<span class="text-xs text-slate-400 font-medium">No skills detected. Type a skill and click "+ Add" below.</span>';
        if (countBadge) countBadge.textContent = "0 Extracted";
        return;
    }

    if (countBadge) {
        countBadge.textContent = `${window.omniDerivedSkills.length} Extracted`;
    }

    container.replaceChildren();
    window.omniDerivedSkills.forEach((skill) => {
        const badge = document.createElement("span");
        badge.className = "inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-lg bg-violet-50 text-violet-900 border border-violet-200 animate-in fade-in duration-150";
        
        const label = document.createElement("span");
        label.textContent = skill;
        badge.appendChild(label);

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "text-violet-400 hover:text-rose-600 hover:bg-rose-50 rounded-full w-4 h-4 flex items-center justify-center transition cursor-pointer text-xs leading-none font-bold";
        removeBtn.title = "Remove skill";
        removeBtn.textContent = "×";
        removeBtn.onclick = () => window.removeOmniSkill(skill);
        badge.appendChild(removeBtn);

        container.appendChild(badge);
    });
};

window.addOmniSkill = function(skill) {
    if (!skill) return;
    const clean = String(skill).trim();
    if (!clean) return;
    if (!window.omniDerivedSkills) window.omniDerivedSkills = [];
    const lower = clean.toLowerCase();
    if (!window.omniDerivedSkills.some(s => s.toLowerCase() === lower)) {
        window.omniDerivedSkills.push(clean);
        window.renderOmniSkillBadges();
    }
};

window.removeOmniSkill = function(skillToRemove) {
    if (!window.omniDerivedSkills) return;
    const lower = (skillToRemove || "").toLowerCase();
    window.omniDerivedSkills = window.omniDerivedSkills.filter(s => s.toLowerCase() !== lower);
    window.renderOmniSkillBadges();
};

window.addOmniSkillFromInput = function() {
    const input = document.getElementById("omniAddSkillInput");
    if (!input) return;
    const val = input.value.trim();
    if (val) {
        window.addOmniSkill(val);
        input.value = "";
    }
};


window.toggleOmniYoeEdit = function() {
    const span = document.getElementById("omniProfileYoe");
    const input = document.getElementById("omniProfileYoeInput");
    if (!span || !input) return;

    if (input.classList.contains("hidden")) {
        let currentYoe = window.omniCurrentProfile?.years_experience;
        if (currentYoe === undefined || currentYoe === null) {
            const m = span.textContent.match(/\d+/);
            currentYoe = m ? parseInt(m[0], 10) : 0;
        }
        input.value = currentYoe;
        span.classList.add("hidden");
        input.classList.remove("hidden");
        input.focus();
        input.select();
    } else {
        window.saveOmniYoeEdit();
    }
};

window.saveOmniYoeEdit = function() {
    const span = document.getElementById("omniProfileYoe");
    const input = document.getElementById("omniProfileYoeInput");
    if (!span || !input) return;

    const val = parseInt(input.value, 10);
    const validVal = (!isNaN(val) && val >= 0) ? Math.min(val, 50) : 0;

    if (!window.omniCurrentProfile) window.omniCurrentProfile = {};
    window.omniCurrentProfile.years_experience = validVal;

    if (validVal === 0) {
        span.textContent = "Fresher / Direct Entry";
    } else if (validVal === 1) {
        span.textContent = "1 Year Experience";
    } else {
        span.textContent = `${validVal} Years Experience`;
    }

    input.classList.add("hidden");
    span.classList.remove("hidden");
};

const OMNI_ALL_LOCATIONS = [
    // Global & Remote Presets
    { name: "Remote / Worldwide", flag: "🌐", code: "Remote", country: "Global", aliases: ["remote", "worldwide", "anywhere", "global", "wfh"] },
    { name: "India (All Cities)", flag: "🇮🇳", code: "India", country: "India", aliases: ["india", "bharat", "pan-india"] },
    { name: "United States (America)", flag: "🇺🇸", code: "United States", country: "USA", aliases: ["america", "usa", "us", "united states"] },
    { name: "United Kingdom (UK)", flag: "🇬🇧", code: "United Kingdom", country: "UK", aliases: ["uk", "england", "great britain", "britain"] },
    { name: "Ireland", flag: "🇮🇪", code: "Ireland", country: "Ireland", aliases: ["ireland", "ie", "irish", "dublin"] },
    { name: "Europe (EU)", flag: "🇪🇺", code: "Europe", country: "Europe", aliases: ["europe", "eu", "european union"] },
    { name: "Canada", flag: "🇨🇦", code: "Canada", country: "Canada", aliases: ["canada", "can"] },
    { name: "Germany", flag: "🇩🇪", code: "Germany", country: "Germany", aliases: ["germany", "deutschland", "de"] },
    { name: "Australia", flag: "🇦🇺", code: "Australia", country: "Australia", aliases: ["australia", "au", "aussie"] },
    { name: "Singapore", flag: "🇸🇬", code: "Singapore", country: "Singapore", aliases: ["singapore", "sg"] },
    { name: "United Arab Emirates (UAE)", flag: "🇦🇪", code: "United Arab Emirates", country: "UAE", aliases: ["uae", "dubai", "abu dhabi"] },

    // Top Indian Tech Hubs & Tier-1 Cities
    { name: "Bengaluru / Bangalore", flag: "📍", code: "Bengaluru", country: "India", aliases: ["bengaluru", "bangalore", "blr", "karnataka"] },
    { name: "Chennai", flag: "📍", code: "Chennai", country: "India", aliases: ["chennai", "madras", "tamil nadu"] },
    { name: "Hyderabad / Secunderabad", flag: "📍", code: "Hyderabad", country: "India", aliases: ["hyderabad", "secunderabad", "telangana"] },
    { name: "Pune", flag: "📍", code: "Pune", country: "India", aliases: ["pune", "maharashtra"] },
    { name: "Mumbai / Navi Mumbai / Thane", flag: "📍", code: "Mumbai", country: "India", aliases: ["mumbai", "bombay", "navi mumbai", "thane"] },
    { name: "Delhi NCR / Noida / Gurgaon / Gurugram", flag: "📍", code: "Delhi", country: "India", aliases: ["delhi", "new delhi", "noida", "gurgaon", "gurugram", "delhi ncr"] },
    { name: "Kolkata", flag: "📍", code: "Kolkata", country: "India", aliases: ["kolkata", "calcutta", "west bengal"] },
    { name: "Ahmedabad / Gandhinagar", flag: "📍", code: "Ahmedabad", country: "India", aliases: ["ahmedabad", "gandhinagar", "gujarat"] },
    { name: "Coimbatore", flag: "📍", code: "Coimbatore", country: "India", aliases: ["coimbatore", "tamil nadu"] },
    { name: "Kochi / Cochin / Ernakulam", flag: "📍", code: "Kochi", country: "India", aliases: ["kochi", "cochin", "ernakulam", "kerala"] },
    { name: "Trivandrum / Thiruvananthapuram", flag: "📍", code: "Trivandrum", country: "India", aliases: ["trivandrum", "thiruvananthapuram", "kerala"] },
    { name: "Chandigarh / Mohali / Panchkula", flag: "📍", code: "Chandigarh", country: "India", aliases: ["chandigarh", "mohali", "panchkula", "punjab"] },
    { name: "Jaipur", flag: "📍", code: "Jaipur", country: "India", aliases: ["jaipur", "rajasthan"] },
    { name: "Indore", flag: "📍", code: "Indore", country: "India", aliases: ["indore", "madhya pradesh"] },
    { name: "Lucknow", flag: "📍", code: "Lucknow", country: "India", aliases: ["lucknow", "uttar pradesh"] },
    { name: "Bhubaneswar", flag: "📍", code: "Bhubaneswar", country: "India", aliases: ["bhubaneswar", "odisha"] },
    { name: "Visakhapatnam / Vizag", flag: "📍", code: "Visakhapatnam", country: "India", aliases: ["visakhapatnam", "vizag", "andhra pradesh"] },

    // Indian Tier-2 & Emerging Cities
    { name: "Surat", flag: "📍", code: "Surat", country: "India", aliases: ["surat", "gujarat"] },
    { name: "Nagpur", flag: "📍", code: "Nagpur", country: "India", aliases: ["nagpur", "maharashtra"] },
    { name: "Kanpur", flag: "📍", code: "Kanpur", country: "India", aliases: ["kanpur", "uttar pradesh"] },
    { name: "Bhopal", flag: "📍", code: "Bhopal", country: "India", aliases: ["bhopal", "madhya pradesh"] },
    { name: "Patna", flag: "📍", code: "Patna", country: "India", aliases: ["patna", "bihar"] },
    { name: "Vadodara / Baroda", flag: "📍", code: "Vadodara", country: "India", aliases: ["vadodara", "baroda", "gujarat"] },
    { name: "Ghaziabad", flag: "📍", code: "Ghaziabad", country: "India", aliases: ["ghaziabad", "uttar pradesh"] },
    { name: "Ludhiana", flag: "📍", code: "Ludhiana", country: "India", aliases: ["ludhiana", "punjab"] },
    { name: "Agra", flag: "📍", code: "Agra", country: "India", aliases: ["agra", "uttar pradesh"] },
    { name: "Nashik", flag: "📍", code: "Nashik", country: "India", aliases: ["nashik", "maharashtra"] },
    { name: "Faridabad", flag: "📍", code: "Faridabad", country: "India", aliases: ["faridabad", "haryana"] },
    { name: "Meerut", flag: "📍", code: "Meerut", country: "India", aliases: ["meerut", "uttar pradesh"] },
    { name: "Rajkot", flag: "📍", code: "Rajkot", country: "India", aliases: ["rajkot", "gujarat"] },
    { name: "Varanasi", flag: "📍", code: "Varanasi", country: "India", aliases: ["varanasi", "kashi", "banaras", "uttar pradesh"] },
    { name: "Srinagar", flag: "📍", code: "Srinagar", country: "India", aliases: ["srinagar", "kashmir"] },
    { name: "Aurangabad / Chhatrapati Sambhajinagar", flag: "📍", code: "Aurangabad", country: "India", aliases: ["aurangabad", "sambhajinagar", "maharashtra"] },
    { name: "Dhanbad", flag: "📍", code: "Dhanbad", country: "India", aliases: ["dhanbad", "jharkhand"] },
    { name: "Amritsar", flag: "📍", code: "Amritsar", country: "India", aliases: ["amritsar", "punjab"] },
    { name: "Prayagraj / Allahabad", flag: "📍", code: "Prayagraj", country: "India", aliases: ["prayagraj", "allahabad", "uttar pradesh"] },
    { name: "Ranchi", flag: "📍", code: "Ranchi", country: "India", aliases: ["ranchi", "jharkhand"] },
    { name: "Gwalior", flag: "📍", code: "Gwalior", country: "India", aliases: ["gwalior", "madhya pradesh"] },
    { name: "Jabalpur", flag: "📍", code: "Jabalpur", country: "India", aliases: ["jabalpur", "madhya pradesh"] },
    { name: "Vijayawada", flag: "📍", code: "Vijayawada", country: "India", aliases: ["vijayawada", "andhra pradesh"] },
    { name: "Jodhpur", flag: "📍", code: "Jodhpur", country: "India", aliases: ["jodhpur", "rajasthan"] },
    { name: "Madurai", flag: "📍", code: "Madurai", country: "India", aliases: ["madurai", "tamil nadu"] },
    { name: "Raipur", flag: "📍", code: "Raipur", country: "India", aliases: ["raipur", "chhattisgarh"] },
    { name: "Kota", flag: "📍", code: "Kota", country: "India", aliases: ["kota", "rajasthan"] },
    { name: "Guwahati", flag: "📍", code: "Guwahati", country: "India", aliases: ["guwahati", "assam"] },
    { name: "Mysore / Mysuru", flag: "📍", code: "Mysore", country: "India", aliases: ["mysore", "mysuru", "karnataka"] },
    { name: "Trichy / Tiruchirappalli", flag: "📍", code: "Trichy", country: "India", aliases: ["trichy", "tiruchirappalli", "tamil nadu"] },
    { name: "Tiruppur", flag: "📍", code: "Tiruppur", country: "India", aliases: ["tiruppur", "tamil nadu"] },
    { name: "Salem", flag: "📍", code: "Salem", country: "India", aliases: ["salem", "tamil nadu"] },
    { name: "Jalandhar", flag: "📍", code: "Jalandhar", country: "India", aliases: ["jalandhar", "punjab"] },
    { name: "Warangal", flag: "📍", code: "Warangal", country: "India", aliases: ["warangal", "telangana"] },
    { name: "Guntur", flag: "📍", code: "Guntur", country: "India", aliases: ["guntur", "andhra pradesh"] },
    { name: "Jamshedpur", flag: "📍", code: "Jamshedpur", country: "India", aliases: ["jamshedpur", "jharkhand"] },
    { name: "Kozhikode / Calicut", flag: "📍", code: "Calicut", country: "India", aliases: ["calicut", "kozhikode", "kerala"] },
    { name: "Thrissur", flag: "📍", code: "Thrissur", country: "India", aliases: ["thrissur", "kerala"] },
    { name: "Mangalore / Mangaluru", flag: "📍", code: "Mangalore", country: "India", aliases: ["mangalore", "mangaluru", "karnataka"] },
    { name: "Belgaum / Belagavi", flag: "📍", code: "Belgaum", country: "India", aliases: ["belgaum", "belagavi", "karnataka"] },
    { name: "Udupi / Manipal", flag: "📍", code: "Udupi", country: "India", aliases: ["udupi", "manipal", "karnataka"] },
    { name: "Dehradun", flag: "📍", code: "Dehradun", country: "India", aliases: ["dehradun", "uttarakhand"] },
    { name: "Shimla", flag: "📍", code: "Shimla", country: "India", aliases: ["shimla", "himachal pradesh"] },
    { name: "Goa / Panaji", flag: "📍", code: "Goa", country: "India", aliases: ["goa", "panaji"] },
    { name: "Pondicherry / Puducherry", flag: "📍", code: "Pondicherry", country: "India", aliases: ["pondicherry", "puducherry"] },

    // Major US Tech Hubs & Cities
    { name: "Austin, TX (USA)", flag: "📍", code: "Austin", country: "USA", aliases: ["austin", "texas", "austin tx", "austin america"] },
    { name: "San Francisco / Bay Area, CA (USA)", flag: "📍", code: "San Francisco", country: "USA", aliases: ["san francisco", "sf", "bay area", "california"] },
    { name: "San Jose / Silicon Valley, CA (USA)", flag: "📍", code: "San Jose", country: "USA", aliases: ["san jose", "silicon valley", "sunnyvale", "santa clara", "palo alto", "mountain view"] },
    { name: "Seattle, WA (USA)", flag: "📍", code: "Seattle", country: "USA", aliases: ["seattle", "washington", "redmond", "bellevue"] },
    { name: "New York, NY (USA)", flag: "📍", code: "New York", country: "USA", aliases: ["new york", "nyc", "manhattan", "brooklyn"] },
    { name: "Boston / Cambridge, MA (USA)", flag: "📍", code: "Boston", country: "USA", aliases: ["boston", "cambridge", "massachusetts"] },
    { name: "Chicago, IL (USA)", flag: "📍", code: "Chicago", country: "USA", aliases: ["chicago", "illinois"] },
    { name: "Los Angeles, CA (USA)", flag: "📍", code: "Los Angeles", country: "USA", aliases: ["los angeles", "la", "california"] },
    { name: "Denver / Boulder, CO (USA)", flag: "📍", code: "Denver", country: "USA", aliases: ["denver", "boulder", "colorado"] },
    { name: "Atlanta, GA (USA)", flag: "📍", code: "Atlanta", country: "USA", aliases: ["atlanta", "georgia"] },
    { name: "Dallas / Fort Worth, TX (USA)", flag: "📍", code: "Dallas", country: "USA", aliases: ["dallas", "fort worth", "texas"] },
    { name: "Houston, TX (USA)", flag: "📍", code: "Houston", country: "USA", aliases: ["houston", "texas"] },
    { name: "San Diego, CA (USA)", flag: "📍", code: "San Diego", country: "USA", aliases: ["san diego", "california"] },
    { name: "Portland, OR (USA)", flag: "📍", code: "Portland", country: "USA", aliases: ["portland", "oregon"] },
    { name: "Washington, DC (USA)", flag: "📍", code: "Washington", country: "USA", aliases: ["washington", "dc", "virginia", "maryland"] },
    { name: "Raleigh / Durham, NC (USA)", flag: "📍", code: "Raleigh", country: "USA", aliases: ["raleigh", "durham", "research triangle"] },
    { name: "Salt Lake City, UT (USA)", flag: "📍", code: "Salt Lake City", country: "USA", aliases: ["salt lake city", "utah"] },
    { name: "Sunnyvale, CA (USA)", flag: "📍", code: "Sunnyvale", country: "USA", aliases: ["sunnyvale", "silicon valley"] },
    { name: "Mountain View, CA (USA)", flag: "📍", code: "Mountain View", country: "USA", aliases: ["mountain view", "silicon valley"] },
    { name: "Palo Alto, CA (USA)", flag: "📍", code: "Palo Alto", country: "USA", aliases: ["palo alto", "silicon valley"] },
    { name: "Pittsburgh, PA (USA)", flag: "📍", code: "Pittsburgh", country: "USA", aliases: ["pittsburgh", "pennsylvania"] },

    // European Tech Hubs & Cities
    { name: "London (United Kingdom)", flag: "📍", code: "London", country: "UK", aliases: ["london", "england", "uk"] },
    { name: "Dublin (Ireland)", flag: "📍", code: "Dublin", country: "Ireland", aliases: ["dublin", "ireland"] },
    { name: "Cork (Ireland)", flag: "📍", code: "Cork", country: "Ireland", aliases: ["cork", "ireland"] },
    { name: "Berlin (Germany)", flag: "📍", code: "Berlin", country: "Germany", aliases: ["berlin", "germany"] },
    { name: "Munich (Germany)", flag: "📍", code: "Munich", country: "Germany", aliases: ["munich", "germany"] },
    { name: "Frankfurt (Germany)", flag: "📍", code: "Frankfurt", country: "Germany", aliases: ["frankfurt", "germany"] },
    { name: "Amsterdam (Netherlands)", flag: "📍", code: "Amsterdam", country: "Netherlands", aliases: ["amsterdam", "holland", "netherlands"] },
    { name: "Paris (France)", flag: "📍", code: "Paris", country: "France", aliases: ["paris", "france"] },
    { name: "Zurich (Switzerland)", flag: "📍", code: "Zurich", country: "Switzerland", aliases: ["zurich", "switzerland"] },
    { name: "Geneva (Switzerland)", flag: "📍", code: "Geneva", country: "Switzerland", aliases: ["geneva", "switzerland"] },
    { name: "Stockholm (Sweden)", flag: "📍", code: "Stockholm", country: "Sweden", aliases: ["stockholm", "sweden"] },
    { name: "Copenhagen (Denmark)", flag: "📍", code: "Copenhagen", country: "Denmark", aliases: ["copenhagen", "denmark"] },
    { name: "Warsaw (Poland)", flag: "📍", code: "Warsaw", country: "Poland", aliases: ["warsaw", "poland"] },
    { name: "Madrid (Spain)", flag: "📍", code: "Madrid", country: "Spain", aliases: ["madrid", "spain"] },
    { name: "Barcelona (Spain)", flag: "📍", code: "Barcelona", country: "Spain", aliases: ["barcelona", "spain"] },
    { name: "Milan (Italy)", flag: "📍", code: "Milan", country: "Italy", aliases: ["milan", "italy"] },
    { name: "Vienna (Austria)", flag: "📍", code: "Vienna", country: "Austria", aliases: ["vienna", "austria"] },
    { name: "Brussels (Belgium)", flag: "📍", code: "Brussels", country: "Belgium", aliases: ["brussels", "belgium"] },
    { name: "Lisbon (Portugal)", flag: "📍", code: "Lisbon", country: "Portugal", aliases: ["lisbon", "portugal"] },
    { name: "Prague (Czech Republic)", flag: "📍", code: "Prague", country: "Czech Republic", aliases: ["prague", "czech"] },

    // Canada
    { name: "Toronto (Canada)", flag: "📍", code: "Toronto", country: "Canada", aliases: ["toronto", "ontario", "canada"] },
    { name: "Vancouver (Canada)", flag: "📍", code: "Vancouver", country: "Canada", aliases: ["vancouver", "british columbia", "canada"] },
    { name: "Montreal (Canada)", flag: "📍", code: "Montreal", country: "Canada", aliases: ["montreal", "quebec", "canada"] },
    { name: "Waterloo / Kitchener (Canada)", flag: "📍", code: "Waterloo", country: "Canada", aliases: ["waterloo", "kitchener", "canada"] },

    // Asia-Pacific, Middle East, Global
    { name: "Singapore", flag: "📍", code: "Singapore", country: "Singapore", aliases: ["singapore", "sg"] },
    { name: "Dubai (UAE)", flag: "📍", code: "Dubai", country: "UAE", aliases: ["dubai", "uae"] },
    { name: "Abu Dhabi (UAE)", flag: "📍", code: "Abu Dhabi", country: "UAE", aliases: ["abu dhabi", "uae"] },
    { name: "Tokyo (Japan)", flag: "📍", code: "Tokyo", country: "Japan", aliases: ["tokyo", "japan"] },
    { name: "Seoul (South Korea)", flag: "📍", code: "Seoul", country: "South Korea", aliases: ["seoul", "korea"] },
    { name: "Sydney (Australia)", flag: "📍", code: "Sydney", country: "Australia", aliases: ["sydney", "australia"] },
    { name: "Melbourne (Australia)", flag: "📍", code: "Melbourne", country: "Australia", aliases: ["melbourne", "australia"] },
    { name: "Auckland (New Zealand)", flag: "📍", code: "Auckland", country: "New Zealand", aliases: ["auckland", "new zealand"] },
    { name: "Hong Kong", flag: "📍", code: "Hong Kong", country: "Hong Kong", aliases: ["hong kong", "hk"] },
    { name: "Sao Paulo (Brazil)", flag: "📍", code: "Sao Paulo", country: "Brazil", aliases: ["sao paulo", "brazil"] },
    { name: "Mexico City (Mexico)", flag: "📍", code: "Mexico City", country: "Mexico", aliases: ["mexico city", "mexico"] }
];

window.filterOmniLocationList = function(q) {
    const dropdown = document.getElementById("omniCriteriaLocationDropdown");
    if (!dropdown) return;
    const query = (q || "").trim().toLowerCase();

    const filtered = OMNI_ALL_LOCATIONS.filter(loc => {
        if (!query) return true;
        const nameMatch = loc.name.toLowerCase().includes(query);
        const codeMatch = loc.code.toLowerCase().includes(query);
        const countryMatch = loc.country ? loc.country.toLowerCase().includes(query) : false;
        const aliasesMatch = loc.aliases ? loc.aliases.some(a => a.toLowerCase().includes(query)) : false;
        return nameMatch || codeMatch || countryMatch || aliasesMatch;
    }).slice(0, 35);

    dropdown.replaceChildren();

    if (query && !filtered.some(loc => loc.code.toLowerCase() === query || loc.name.toLowerCase() === query)) {
        const customItem = document.createElement("div");
        customItem.className = "px-3.5 py-2.5 text-xs font-bold text-violet-800 bg-violet-50/70 hover:bg-violet-100 cursor-pointer flex items-center justify-between transition border-b border-violet-100";
        customItem.innerHTML = `<span class="flex items-center gap-2"><span>🎯</span><span>Use custom: <strong>${escapeOmniHtml(q)}</strong></span></span><span class="text-[10px] text-violet-600 font-semibold uppercase">Custom</span>`;
        customItem.onclick = () => window.selectOmniLocation(q, q);
        dropdown.appendChild(customItem);
    }

    if (filtered.length === 0 && !query) {
        dropdown.innerHTML = '<div class="p-3 text-xs text-slate-400">Type any city or country name...</div>';
        dropdown.classList.remove("hidden");
        return;
    }

    filtered.forEach(loc => {
        const item = document.createElement("div");
        item.className = "px-3.5 py-2 text-xs font-bold text-slate-800 hover:bg-violet-50 hover:text-violet-900 cursor-pointer flex items-center justify-between transition";
        item.innerHTML = `<span class="flex items-center gap-2"><span>${loc.flag || '📍'}</span><span>${escapeOmniHtml(loc.name)}</span></span><span class="text-[10px] text-slate-400 font-semibold uppercase">${escapeOmniHtml(loc.country || loc.code)}</span>`;
        item.onclick = () => window.selectOmniLocation(loc.code, loc.name);
        dropdown.appendChild(item);
    });

    dropdown.classList.remove("hidden");
};

window.omniSelectedLocations = window.omniSelectedLocations || [];

window.renderOmniLocationBadges = function() {
    const container = document.getElementById("omniLocationsBadgesContainer");
    const countBadge = document.getElementById("omniLocationsCountBadge");
    const errEl = document.getElementById("omniLocationError");
    if (!container) return;

    const locs = window.omniSelectedLocations || [];
    if (errEl && locs.length > 0) errEl.classList.add("hidden");

    if (countBadge) {
        if (locs.length > 0) {
            countBadge.textContent = `${locs.length} Selected`;
            countBadge.className = "text-[10px] font-black text-emerald-800 bg-emerald-100 border border-emerald-200 px-2 py-0.5 rounded-full";
        } else {
            countBadge.textContent = "Required • Add 1+";
            countBadge.className = "text-[10px] font-black text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full";
        }
    }

    container.replaceChildren();
    if (locs.length === 0) {
        const empty = document.createElement("span");
        empty.className = "text-xs text-slate-400 font-medium";
        empty.textContent = "Type a city or country below and press Enter to add...";
        container.appendChild(empty);
        return;
    }

    locs.forEach(loc => {
        const badge = document.createElement("span");
        badge.className = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-violet-200 text-violet-950 font-bold text-[11px] shadow-2xs";
        const label = document.createElement("span");
        label.textContent = "📍 " + loc;
        badge.appendChild(label);

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "text-violet-400 hover:text-rose-600 hover:bg-rose-50 rounded-full w-4 h-4 flex items-center justify-center transition cursor-pointer text-xs leading-none font-bold";
        removeBtn.title = "Remove location";
        removeBtn.textContent = "×";
        removeBtn.onclick = () => window.removeOmniLocation(loc);
        badge.appendChild(removeBtn);
        container.appendChild(badge);
    });
};

window.addOmniLocation = function(locStr) {
    const clean = String(locStr || "").trim();
    if (!clean) return;
    if (!window.omniSelectedLocations) window.omniSelectedLocations = [];
    if (!window.omniSelectedLocations.some(l => l.toLowerCase() === clean.toLowerCase())) {
        window.omniSelectedLocations.push(clean);
        window.renderOmniLocationBadges();
    }
};

window.removeOmniLocation = function(locToRemove) {
    if (!window.omniSelectedLocations) return;
    const lower = String(locToRemove || "").toLowerCase();
    window.omniSelectedLocations = window.omniSelectedLocations.filter(l => l.toLowerCase() !== lower);
    window.renderOmniLocationBadges();
};

window.addOmniLocationFromInput = function() {
    const input = document.getElementById("omniCriteriaLocationInput");
    const dropdown = document.getElementById("omniCriteriaLocationDropdown");
    if (!input) return;
    const val = input.value.trim();
    if (val) {
        window.addOmniLocation(val);
        input.value = "";
    }
    if (dropdown) dropdown.classList.add("hidden");
};

window.selectOmniLocation = function(code, name) {
    const input = document.getElementById("omniCriteriaLocationInput");
    const dropdown = document.getElementById("omniCriteriaLocationDropdown");
    window.addOmniLocation(code || name);
    if (input) input.value = "";
    if (dropdown) dropdown.classList.add("hidden");
};

window.setOmniLocationPreset = function(loc) {
    const input = document.getElementById("omniCriteriaLocationInput");
    const dropdown = document.getElementById("omniCriteriaLocationDropdown");
    window.addOmniLocation(loc);
    if (input) input.value = "";
    if (dropdown) dropdown.classList.add("hidden");
};

window.updateOmniPillStyles = function() {
    document.querySelectorAll('.omni-work-pill').forEach(pill => {
        const radio = pill.querySelector('input[type="radio"]');
        if (radio && radio.checked) {
            pill.className = "omni-work-pill border border-slate-900 bg-slate-950 text-white rounded-xl py-1.5 text-center cursor-pointer flex items-center justify-center transition";
        } else {
            pill.className = "omni-work-pill border border-slate-200 bg-slate-50 text-slate-700 rounded-xl py-1.5 text-center cursor-pointer hover:bg-slate-100 flex items-center justify-center transition";
        }
    });

    document.querySelectorAll('.omni-emp-pill').forEach(pill => {
        const radio = pill.querySelector('input[type="radio"]');
        if (radio && radio.checked) {
            pill.className = "omni-emp-pill border border-slate-900 bg-slate-950 text-white rounded-xl py-1.5 text-center cursor-pointer flex items-center justify-center transition";
        } else {
            pill.className = "omni-emp-pill border border-slate-200 bg-slate-50 text-slate-700 rounded-xl py-1.5 text-center cursor-pointer hover:bg-slate-100 flex items-center justify-center transition";
        }
    });
};

window.handleOmniResumeSelected = async function(event) {
    const file = event && event.target && event.target.files && event.target.files[0];
    if (!file) return;
    window.omniUploadedFileName = file.name || "";

    const uploadLabel = document.getElementById("omniResumeUploadLabel");
    const originalLabel = uploadLabel ? uploadLabel.textContent : "Drop Resume (PDF/DOCX)";
    if (uploadLabel) uploadLabel.textContent = "Analyzing Profile Vector...";

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
        const profile = data.profile || {};
        window.omniCurrentProfile = profile;
        if (typeof window.almondTrackFunnel === "function") {
            window.almondTrackFunnel("resume_upload", {
                user_name: profile.name || "",
                meta: { target_role: profile.current_role || "" }
            });
        }

        // 1. Identified Candidate Name & Avatar
        const nameEl = document.getElementById("omniProfileName");
        if (nameEl) {
            nameEl.textContent = profile.name || "Identified Candidate";
        }
        const avatarEl = document.getElementById("omniProfileAvatar");
        if (avatarEl) {
            avatarEl.textContent = profile.name ? profile.name.trim().charAt(0).toUpperCase() : "👤";
        }

        // 2. Verified Experience
        const yoeEl = document.getElementById("omniProfileYoe");
        const yoeInput = document.getElementById("omniProfileYoeInput");
        const yoe = profile.years_experience;
        if (yoeEl) {
            if (yoe !== undefined && yoe !== null && yoe > 0) {
                yoeEl.textContent = `${yoe} Years Experience`;
            } else {
                yoeEl.textContent = "Fresher / Direct Entry";
            }
            yoeEl.classList.remove("hidden");
        }
        if (yoeInput) {
            yoeInput.value = (yoe !== undefined && yoe !== null) ? yoe : 0;
            yoeInput.classList.add("hidden");
        }

        // 3. Derived Skills
        window.omniDerivedSkills = Array.isArray(profile.skills) ? [...profile.skills] : [];
        window.renderOmniSkillBadges();

        // 4. Target Role
        const roleField = document.getElementById("omniCriteriaTargetRole");
        if (roleField) {
            roleField.value = profile.current_role || (profile.skills && profile.skills[0]) || "";
        }

        // 5. Minimum Expected Package Dropdown
        const pkgSelect = document.getElementById("omniCriteriaPackageSelect");
        if (pkgSelect) {
            pkgSelect.value = "7";
        }
        const pkgField = document.getElementById("omniCriteriaExpectedPackage");
        if (pkgField) {
            pkgField.value = "7 LPA";
        }

        // 6. Preferred Locations: Pre-seed detected country (e.g. India) for 1-tap matching while still editable
        const locInput = document.getElementById("omniCriteriaLocationInput");
        const locHidden = document.getElementById("omniCriteriaLocation");
        if (locInput) locInput.value = "";
        if (locHidden) locHidden.value = "";
        const detectedCountry = typeof window.getUserGeoCountry === "function" ? window.getUserGeoCountry() : "";
        window.omniSelectedLocations = detectedCountry ? [detectedCountry] : [];
        window.renderOmniLocationBadges();

        window.openOmniCriteriaModal(profile);
    } catch (err) {
        alert("Resume intake failed: " + err.message);
    } finally {
        if (uploadLabel) uploadLabel.textContent = originalLabel;
        if (event && event.target) event.target.value = "";
    }
};

window.openOmniCriteriaModal = function(profile) {
    const modal = document.getElementById("omniCriteriaModal");
    if (modal) {
        modal.classList.remove("hidden");
        window.updateOmniPillStyles();
    }
};

window.closeOmniCriteriaModal = function() {
    const modal = document.getElementById("omniCriteriaModal");
    if (modal) modal.classList.add("hidden");
    const dropdown = document.getElementById("omniCriteriaLocationDropdown");
    if (dropdown) dropdown.classList.add("hidden");
};

window.submitOmniCriteria = async function() {
    const role = (document.getElementById("omniCriteriaTargetRole")?.value || "").trim();
    const pkgSelect = document.getElementById("omniCriteriaPackageSelect");
    const pkgVal = pkgSelect ? parseFloat(pkgSelect.value) || 0 : 7;
    const freshnessSelect = document.getElementById("omniCriteriaFreshnessSelect");
    const maxDaysVal = freshnessSelect ? parseInt(freshnessSelect.value, 10) || 0 : 0;

    // Auto-add any typed text still sitting in location input
    const locInputEl = document.getElementById("omniCriteriaLocationInput");
    const typedLoc = (locInputEl?.value || "").trim();
    if (typedLoc) {
        window.addOmniLocation(typedLoc);
        if (locInputEl) locInputEl.value = "";
    }

    const selectedLocs = window.omniSelectedLocations || [];
    const locErrEl = document.getElementById("omniLocationError");
    if (selectedLocs.length === 0) {
        if (locErrEl) locErrEl.classList.remove("hidden");
        if (locInputEl) locInputEl.focus();
        return;
    }
    if (locErrEl) locErrEl.classList.add("hidden");

    const loc = selectedLocs.join(",");
    const workMode = document.querySelector('input[name="omni_work_mode"]:checked')?.value || "all";
    const contractType = document.querySelector('input[name="omni_contract_type"]:checked')?.value || "all";

    window.omniActiveLocation = loc;
    window.omniActiveMinPackage = pkgVal;
    window.omniActiveWorkMode = workMode;
    window.omniActiveContractType = contractType;
    window.omniActiveMaxDays = maxDaysVal;
    window.omniSortMode = "best_match";
    const sortSel = document.getElementById("omniSortSelect");
    if (sortSel) sortSel.value = "best_match";
    window.currentProfile = window.omniCurrentProfile || { name: "Candidate", role: role, skills: window.omniDerivedSkills || [] };

    // Do NOT restrict search query strictly to designation: role is optional criteria
    window.omniTargetRole = role;
    window.omniMatchResumeMode = true;

    // Clean up omni search input box
    const input = document.getElementById("omniSearchInput");
    if (input) input.value = "";

    const clearBtn = document.getElementById("omniClearBtn");
    if (clearBtn) clearBtn.classList.add("hidden");

    window.closeOmniCriteriaModal();

    if (typeof window.renderActiveResumeCard === "function") {
        window.renderActiveResumeCard();
    }

    // Reveal search results container
    const streamContainer = document.getElementById("omniSearchResultsContainer");
    if (streamContainer) {
        streamContainer.classList.remove("hidden");
    }

    window.omniCurrentQuery = "";
    window.omniCurrentOffset = 0;
    await window.executeOmniSearch("", false);

    const scrollTarget = document.getElementById("omniActiveResumeCard") || streamContainer;
    if (scrollTarget) {
        scrollTarget.scrollIntoView({ behavior: "smooth", block: "start" });
    }
};


// Global Resume Upload Trigger & Kanban Modal Controllers
window.triggerOmniResumeUpload = function() {
    const fileInput = document.getElementById("omniResumeFileInput");
    if (fileInput) {
        fileInput.value = "";
        fileInput.click();
    }
};

window.openKanbanModal = function() {
    const modal = document.getElementById("kanbanModal");
    if (modal) {
        modal.classList.remove("hidden");
        const board = document.getElementById("kanbanBoardContainer");
        if (board) board.classList.remove("hidden");
        if (typeof renderKanbanBoard === "function") {
            renderKanbanBoard();
        }
    }
};

window.closeKanbanModal = function() {
    const modal = document.getElementById("kanbanModal");
    if (modal) modal.classList.add("hidden");
};

window.initOmniSearch = function() {
    const uploadBtn = document.getElementById("omniResumeUploadBtn");
    if (uploadBtn && !uploadBtn.dataset.bound) {
        uploadBtn.dataset.bound = "true";
        uploadBtn.addEventListener("click", () => {
            window.triggerOmniResumeUpload();
        });
    }

    const searchContainer = document.getElementById("omniSearchBarContainer");
    if (searchContainer) {
        ["dragenter", "dragover"].forEach(evtName => {
            searchContainer.addEventListener(evtName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                searchContainer.classList.add("ring-2", "ring-violet-500", "bg-violet-50/50");
            });
        });
        ["dragleave", "drop"].forEach(evtName => {
            searchContainer.addEventListener(evtName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                searchContainer.classList.remove("ring-2", "ring-violet-500", "bg-violet-50/50");
            });
        });
        searchContainer.addEventListener("drop", (e) => {
            e.preventDefault();
            const files = e.dataTransfer && e.dataTransfer.files;
            if (files && files.length > 0) {
                window.handleOmniResumeSelected({ target: { files: files } });
            }
        });
    }

    // Auto-close location dropdown on outside click
    document.addEventListener("click", (e) => {
        const dropdown = document.getElementById("omniCriteriaLocationDropdown");
        const input = document.getElementById("omniCriteriaLocationInput");
        if (dropdown && !dropdown.contains(e.target) && e.target !== input) {
            dropdown.classList.add("hidden");
        }
    });
};

window.applyQuickJobFilter = function(preset, clickedBtn) {
    document.querySelectorAll(".omni-quick-chip").forEach(btn => {
        const isFreeBtn = btn.getAttribute("data-quick-filter") === "free";
        if (btn === clickedBtn) {
            btn.className = "omni-quick-chip shrink-0 px-3.5 py-2 rounded-full text-xs font-extrabold bg-slate-950 text-white border border-slate-950 shadow-xs transition cursor-pointer";
        } else if (isFreeBtn) {
            btn.className = "omni-quick-chip shrink-0 px-3.5 py-2 rounded-full text-xs font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-200 shadow-2xs transition cursor-pointer";
        } else {
            btn.className = "omni-quick-chip shrink-0 px-3.5 py-2 rounded-full text-xs font-bold bg-white/95 hover:bg-violet-50 text-slate-800 hover:text-violet-900 border border-slate-200 shadow-2xs transition cursor-pointer";
        }
    });

    const inputEl = document.getElementById("omniSearchInput");
    const clearBtn = document.getElementById("omniClearBtn");
    window.omniMatchResumeMode = false;
    window.omniCurrentOffset = 0;
    window.omniActiveLocation = "all";
    window.omniActiveCategory = "All";
    window.omniActiveWorkMode = "all";
    window.omniActiveContractType = "all";
    window.omniSortMode = "best_match";

    let q = "";
    if (preset === "india") {
        window.omniActiveLocation = "India";
    } else if (preset === "software") {
        q = "Software Engineer";
    } else if (preset === "ai") {
        window.omniActiveCategory = "AI";
    } else if (preset === "intern") {
        window.omniActiveContractType = "internship";
    } else if (preset === "remote") {
        window.omniActiveWorkMode = "remote";
    } else if (preset === "free") {
        window.omniSortMode = "free_jobs";
        const sortSel = document.getElementById("omniSortSelect");
        if (sortSel) sortSel.value = "free_jobs";
    }

    if (inputEl) inputEl.value = q;
    if (clearBtn) {
        if (q) clearBtn.classList.remove("hidden");
        else clearBtn.classList.add("hidden");
    }
    window.omniCurrentQuery = q;

    const streamContainer = document.getElementById("omniSearchResultsContainer");
    if (streamContainer) streamContainer.classList.remove("hidden");
    if (typeof window.executeOmniSearch === "function") {
        window.executeOmniSearch(q, false);
    }
};

// Initial load: render server-inlined geo-matched feed synchronously at 0ms, or fetch via /api/omni-search
window.initInitialLiveFeed = function() {
    const streamContainer = document.getElementById("omniSearchResultsContainer");
    if (!streamContainer) return;
    streamContainer.classList.remove("hidden");
    window.omniCurrentQuery = "";
    window.omniCurrentOffset = 0;

    try {
        const boot = window.__ALMOND_INITIAL_FEED__;
        const clientLoggedIn = typeof isUserLoggedIn === "function" ? isUserLoggedIn() : false;
        const clientCountry = typeof window.getUserGeoCountry === "function" ? window.getUserGeoCountry() : "";
        const bootCountry = (boot && boot.country) || "";
        const countryCompatible = !clientCountry || !bootCountry || bootCountry.toLowerCase() === clientCountry.toLowerCase();
        if (boot && boot.result && Array.isArray(boot.result.items) && boot.result.items.length > 0 && Boolean(boot.logged_in) === clientLoggedIn && countryCompatible) {
            window.__ALMOND_INITIAL_FEED__ = null;
            if (typeof window.renderOmniResults === "function") {
                window.renderOmniResults(boot.result, "", false);
                return;
            }
        }
    } catch (_) {}

    if (typeof window.executeOmniSearch === "function") {
        window.executeOmniSearch("", false);
    }
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        window.initOmniSearch();
        window.initSocialProofToasts();
        window.initInitialLiveFeed();
    });
} else {
    setTimeout(() => {
        window.initOmniSearch();
        window.initSocialProofToasts();
        window.initInitialLiveFeed();
    }, 100);
}


// ==============================================================================
// SOCIAL PROOF MICRO-MOMENTS TOAST MANAGER
// ==============================================================================

const ALMOND_SOCIAL_PROOF_FEED = [
    { candidate: "Full Stack Dev in Bengaluru", company: "Uber Careers (Direct)", time: "1m ago", avatar: "UB" },
    { candidate: "SWE Fresher in Hyderabad", company: "Microsoft Careers", time: "2m ago", avatar: "MS" },
    { candidate: "AI / ML Engineer in Remote", company: "OpenAI Ashby Gateway", time: "3m ago", avatar: "AI" },
    { candidate: "Frontend Architect in Pune", company: "Cisco Systems Direct", time: "4m ago", avatar: "CS" },
    { candidate: "Backend Developer in Bengaluru", company: "Swiggy Greenhouse", time: "1m ago", avatar: "SW" },
    { candidate: "Cloud Solutions Lead in Gurgaon", company: "Zomato Workday Portal", time: "5m ago", avatar: "ZM" },
    { candidate: "Data Scientist in Dublin", company: "Stripe Careers", time: "3m ago", avatar: "ST" },
    { candidate: "DevOps Engineer in Austin, TX", company: "Tesla Internal Careers", time: "6m ago", avatar: "TS" },
    { candidate: "AI Research Intern in Bengaluru", company: "Adobe Research Feed", time: "2m ago", avatar: "AD" },
    { candidate: "Junior SWE in Chennai", company: "Zoho Careers Direct", time: "4m ago", avatar: "ZH" }
];

let _socialToastIndex = 0;
let _socialToastTimer = null;
let _socialToastHideTimer = null;

function dismissSocialToast() {
    const toast = document.getElementById("socialProofToast");
    if (toast) {
        toast.classList.remove("translate-y-0", "opacity-100", "pointer-events-auto");
        toast.classList.add("translate-y-10", "opacity-0", "pointer-events-none");
    }
    try {
        sessionStorage.setItem("almond_social_toast_dismissed", "true");
    } catch (e) {}
    if (_socialToastTimer) clearInterval(_socialToastTimer);
    if (_socialToastHideTimer) clearTimeout(_socialToastHideTimer);
}
window.dismissSocialToast = dismissSocialToast;

function showNextSocialToast() {
    try {
        if (sessionStorage.getItem("almond_social_toast_dismissed") === "true") return;
    } catch (e) {}

    const toast = document.getElementById("socialProofToast");
    if (!toast) return;

    // Do not show toast if any full-screen modal or criteria intake modal is open
    const openModal = document.querySelector(".fixed.inset-0:not(.hidden)");
    if (openModal) return;

    const data = ALMOND_SOCIAL_PROOF_FEED[_socialToastIndex % ALMOND_SOCIAL_PROOF_FEED.length];
    _socialToastIndex++;

    const candEl = document.getElementById("socialToastCandidate");
    const compEl = document.getElementById("socialToastCompany");
    const timeEl = document.getElementById("socialToastTime");
    const avEl = document.getElementById("socialToastAvatar");

    if (candEl) candEl.textContent = data.candidate;
    if (compEl) compEl.textContent = data.company;
    if (timeEl) timeEl.textContent = data.time;
    if (avEl) avEl.textContent = data.avatar;

    toast.classList.remove("translate-y-10", "opacity-0", "pointer-events-none");
    toast.classList.add("translate-y-0", "opacity-100", "pointer-events-auto");

    // Hide after 5 seconds
    if (_socialToastHideTimer) clearTimeout(_socialToastHideTimer);
    _socialToastHideTimer = setTimeout(() => {
        toast.classList.remove("translate-y-0", "opacity-100", "pointer-events-auto");
        toast.classList.add("translate-y-10", "opacity-0", "pointer-events-none");
    }, 5000);
}

function initSocialProofToasts() {
    try {
        if (sessionStorage.getItem("almond_social_toast_dismissed") === "true") return;
    } catch (e) {}

    // First display delayed by 7 seconds to let the user absorb the hero fold
    setTimeout(() => {
        showNextSocialToast();
        // Subsequent rotations every 24 seconds
        _socialToastTimer = setInterval(showNextSocialToast, 24000);
    }, 7000);
}
window.initSocialProofToasts = initSocialProofToasts;


// ==============================================================================
// UNIVERSAL KEYBOARD ACCESSIBILITY: ESCAPE MODAL MANAGER
// ==============================================================================

function closeAnyActiveModal() {
    let closedAny = false;
    const isVisible = (el) => el && !el.classList.contains("hidden") && el.style.display !== "none";

    // 1. Check modals
    const omniModal = document.getElementById("omniCriteriaModal");
    if (isVisible(omniModal)) {
        if (typeof window.closeOmniCriteriaModal === "function") window.closeOmniCriteriaModal();
        else omniModal.classList.add("hidden");
        closedAny = true;
    }

    const profModal = document.getElementById("profileModal");
    if (isVisible(profModal)) {
        if (typeof closeProfileModal === "function") closeProfileModal();
        else profModal.classList.add("hidden");
        closedAny = true;
    }

    const vipPass = document.getElementById("vipPassModal");
    if (isVisible(vipPass)) {
        if (typeof window.closeVipPassModal === "function") window.closeVipPassModal();
        else vipPass.classList.add("hidden");
        closedAny = true;
    }

    const vipPricing = document.getElementById("vipPricingModal");
    if (isVisible(vipPricing)) {
        if (typeof closeVipPricingModal === "function") closeVipPricingModal();
        else vipPricing.classList.add("hidden");
        closedAny = true;
    }

    const kanban = document.getElementById("kanbanModal");
    if (isVisible(kanban)) {
        if (typeof closeKanbanModal === "function") closeKanbanModal();
        else kanban.classList.add("hidden");
        closedAny = true;
    }

    const feedback = document.getElementById("candidateFeedbackModal");
    if (isVisible(feedback)) {
        if (typeof closeCandidateFeedbackModal === "function") closeCandidateFeedbackModal();
        else feedback.classList.add("hidden");
        closedAny = true;
    }

    const curated = document.getElementById("curatedFeedsModal");
    if (isVisible(curated)) {
        if (typeof closeCuratedFeedsModal === "function") closeCuratedFeedsModal();
        else curated.classList.add("hidden");
        closedAny = true;
    }

    const pitch = document.getElementById("pitchModal");
    if (isVisible(pitch)) {
        pitch.classList.add("hidden");
        closedAny = true;
    }

    const coverLetter = document.getElementById("coverLetterModal");
    if (isVisible(coverLetter)) {
        coverLetter.classList.add("hidden");
        closedAny = true;
    }

    const dossier = document.getElementById("techDossierModal");
    if (isVisible(dossier)) {
        if (typeof closeTechDossierModal === "function") closeTechDossierModal();
        else dossier.classList.add("hidden");
        closedAny = true;
    }

    const coffee = document.getElementById("coffeeCheckoutModal");
    if (isVisible(coffee)) {
        if (typeof closeCoffeeCheckoutModal === "function") closeCoffeeCheckoutModal();
        else coffee.classList.add("hidden");
        closedAny = true;
    }

    const exitIntent = document.getElementById("paymentExitIntentModal");
    if (isVisible(exitIntent)) {
        if (typeof closeExitIntentModal === "function") closeExitIntentModal();
        else exitIntent.classList.add("hidden");
        closedAny = true;
    }

    const heroInfo = document.getElementById("heroInfoModal");
    if (isVisible(heroInfo)) {
        if (typeof closeHeroInfoModal === "function") closeHeroInfoModal();
        else heroInfo.classList.add("hidden");
        closedAny = true;
    }

    // 2. Side Panel / Navigation Drawer
    const sidePanel = document.getElementById("sidePanel");
    if (sidePanel && !sidePanel.classList.contains("translate-x-full")) {
        if (typeof window.closeSidePanel === "function") window.closeSidePanel();
        closedAny = true;
    }

    // 3. Dropdowns
    const omniDrop = document.getElementById("omniCriteriaLocationDropdown");
    if (isVisible(omniDrop)) {
        omniDrop.classList.add("hidden");
        closedAny = true;
    }

    const prefDrop = document.getElementById("preferredLocationDropdown");
    if (isVisible(prefDrop)) {
        prefDrop.classList.add("hidden");
        closedAny = true;
    }

    return closedAny;
}
window.closeAnyActiveModal = closeAnyActiveModal;

// Unified global Escape key listener
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" || e.keyCode === 27) {
        closeAnyActiveModal();
    }
});


// ==============================================================================
// PROGRESSIVE WEB APP (PWA) & SERVICE WORKER CONTROLLER
// ==============================================================================

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then((registration) => {
                console.log('[PWA] Service worker registered with scope:', registration.scope);
            })
            .catch((err) => {
                console.warn('[PWA] Service worker registration failed:', err);
            });
    });
}

let _deferredPwaPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    _deferredPwaPrompt = e;

    try {
        if (localStorage.getItem('almond_pwa_dismissed') === 'true') return;
    } catch (err) {}

    const promptCard = document.getElementById('pwaInstallPrompt');
    if (promptCard) {
        setTimeout(() => {
            promptCard.classList.remove('hidden');
        }, 8000);
    }
});

function installPwaApp() {
    const promptCard = document.getElementById('pwaInstallPrompt');
    if (promptCard) promptCard.classList.add('hidden');

    if (_deferredPwaPrompt) {
        _deferredPwaPrompt.prompt();
        _deferredPwaPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('[PWA] Candidate accepted A2HS install');
            }
            _deferredPwaPrompt = null;
        });
    }
}
window.installPwaApp = installPwaApp;

function dismissPwaPrompt() {
    const promptCard = document.getElementById('pwaInstallPrompt');
    if (promptCard) promptCard.classList.add('hidden');
    try {
        localStorage.setItem('almond_pwa_dismissed', 'true');
    } catch (err) {}
}
window.dismissPwaPrompt = dismissPwaPrompt;

window.showAlmondRecoveryOfferPopup = function(offer) {
    if (!offer || !offer.active || document.getElementById('almond-recovery-offer-dialog')) return;
    const dlg = document.createElement('dialog');
    dlg.id = 'almond-recovery-offer-dialog';
    dlg.setAttribute('aria-labelledby', 'almond-recovery-offer-title');
    dlg.style.cssText = 'max-width:440px;width:calc(100% - 2rem);border-radius:20px;border:1px solid #e5e5ea;padding:24px;background:#ffffff;color:#1d1d1f;box-shadow:0 24px 60px rgba(0,0,0,0.18);font-family:-apple-system,BlinkMacSystemFont,Inter,sans-serif;';

    const badge = document.createElement('div');
    badge.style.cssText = 'display:inline-block;font-size:11px;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;color:#0071e3;background:#f0f7ff;border:1px solid #d0e5ff;padding:4px 10px;border-radius:999px;margin-bottom:10px;';
    badge.textContent = offer.discount_badge || 'Limited Last Offer';

    const title = document.createElement('h2');
    title.id = 'almond-recovery-offer-title';
    title.style.cssText = 'margin:0 0 8px;font-size:20px;font-weight:700;line-height:1.25;color:#1d1d1f;';
    title.textContent = offer.headline || 'Final Offer: Unlock Almond Jobs Pro';

    const body = document.createElement('p');
    body.style.cssText = 'margin:0 0 20px;font-size:14px;line-height:1.55;color:#424245;';
    body.textContent = offer.message || 'Finish your Pro upgrade today to unlock direct global & remote corporate links before this offer expires.';

    const actions = document.createElement('div');
    actions.style.cssText = 'display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;';

    const dismissBtn = document.createElement('button');
    dismissBtn.type = 'button';
    dismissBtn.textContent = 'Maybe Later';
    dismissBtn.style.cssText = 'min-height:40px;padding:8px 16px;border-radius:980px;border:1px solid #d2d2d7;background:#ffffff;color:#1d1d1f;font-size:13px;font-weight:600;cursor:pointer;';
    dismissBtn.addEventListener('click', () => {
        dlg.close();
        dlg.remove();
        const tk = localStorage.getItem('almond_session_token') || '';
        const em = localStorage.getItem('almond_user_email') || '';
        fetch('/api/recovery-offer/dismiss', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: tk, email: em })
        }).catch(() => {});
    });

    const upgradeBtn = document.createElement('button');
    upgradeBtn.type = 'button';
    upgradeBtn.textContent = 'Claim Pro Offer';
    upgradeBtn.style.cssText = 'min-height:40px;padding:8px 18px;border-radius:980px;border:none;background:#0071e3;color:#ffffff;font-size:13px;font-weight:600;cursor:pointer;';
    upgradeBtn.addEventListener('click', () => {
        dlg.close();
        dlg.remove();
        if (typeof window.openVipPricingModal === 'function') {
            window.openVipPricingModal();
        } else {
            document.querySelector('[onclick*="openVipPricingModal"]')?.click();
        }
    });

    actions.appendChild(dismissBtn);
    actions.appendChild(upgradeBtn);
    dlg.appendChild(badge);
    dlg.appendChild(title);
    dlg.appendChild(body);
    dlg.appendChild(actions);
    document.body.appendChild(dlg);
    dlg.showModal();
};
