
!function() {
    "use strict";
    self.importScripts("scripts/supabase-js@2.js", "scripts/google-analytics.js");
    const serverUrl = "https://app.vindy.tech"
      , client = supabase.createClient("https://uqsnyfywnjvfqamoausw.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxc255Znl3bmp2ZnFhbW9hdXN3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDkxMDYxODcsImV4cCI6MjAyNDY4MjE4N30.XgGrZ5rNO2sRYdRuadEVZMj77K1LzCYwVuaiT-jp9kA", {
        auth: {
            persistSession: !0
        }
    })
      , saveSession = async session => {
        await chrome.storage.local.set({
            supabaseSession: session
        })
    }
      , getSession = async () => (await chrome.storage.local.get(["supabaseSession"])).supabaseSession;
    client.auth.onAuthStateChange(( (event, session) => {
        session ? (saveSession(session),
        invalidateAuthGateCache(),
        setTimeout(( () => async function() {
            await getFromStorage("pendingCommunityLikesCleanup") && await verifyAndCleanCommunityLikes()
        }()), 5e3),
        setTimeout(( () => {
            (async function() {
                try {
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const response = await fetch(`${serverUrl}/api/v1/user_settings`, {
                        method: "GET",
                        headers: {
                            Authorization: `Bearer ${session.access_token}`,
                            "Content-Type": "application/json"
                        }
                    })
                      , result = await response.json();
                    return response.ok ? result.settings ? (await applySettingsFromServer(result.settings),
                    _settingsSyncVersion = result.version || 0,
                    {
                        success: !0,
                        version: _settingsSyncVersion,
                        source: "server"
                    }) : await syncSettingsToServer() : (console.error("[SETTINGS_SYNC] Load failed:", result),
                    {
                        success: !1,
                        error: result.error || "API error"
                    })
                } catch (error) {
                    return console.error("[SETTINGS_SYNC] Load error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            }
            )().then((result => {
                result.success
            }
            )).catch((err => console.error("[SETTINGS_SYNC] Auth sync error:", err)))
        }
        ), 3e3)) : ((async () => {
            await chrome.storage.local.remove(["supabaseSession"])
        }
        )(),
        invalidateAuthGateCache(),
        _settingsSyncVersion = 0)
    }
    ));
    async function getBrowserEnvironment() {
        return (await chrome.storage.local.get(["browserEnvironment"])).browserEnvironment || null
    }
    (async () => {
        const storedSession = await getSession();
        storedSession && client.auth.setSession(storedSession)
    }
    )(),
    async function() {
        const browserInfo = function() {
            const userAgent = navigator.userAgent || ""
              , mobilePatterns = {
                "Orion iOS": /Orion.*iPhone|Orion.*iPad|iPhone.*Orion|iPad.*Orion|ORI\/|Orion/i,
                Kiwi: /Kiwi/i,
                "Yandex Mobile": /YaBrowser.*Mobile/i,
                "Samsung Browser": /SamsungBrowser/i,
                "Firefox Mobile": /Firefox.*Mobile|Mobile.*Firefox/i,
                "Mobile Safari": /Mobile.*Safari|Safari.*Mobile/i,
                "Android Chrome": /Android.*Chrome|Chrome.*Android/i
            }
              , isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|CriOS|FxiOS/i.test(userAgent)
              , isIOSDevice = /iPhone|iPad|iPod/i.test(userAgent) || userAgent.includes("Mac") && "ontouchend"in self;
            let detectedBrowser = "Unknown";
            for (const [name,pattern] of Object.entries(mobilePatterns))
                if (pattern.test(userAgent)) {
                    detectedBrowser = name;
                    break
                }
            return isIOSDevice && "Unknown" === detectedBrowser && (detectedBrowser = "iOS Browser"),
            {
                isMobile: isMobileDevice || isIOSDevice || "Unknown" !== detectedBrowser,
                browser: detectedBrowser,
                userAgent: userAgent,
                isIOS: isIOSDevice
            }
        }();
        await chrome.storage.local.set({
            browserEnvironment: browserInfo
        })
    }();
    const VINTED_DOMAINS = ["www.vinted.fr", "www.vinted.es", "www.vinted.be", "www.vinted.lu", "www.vinted.nl", "www.vinted.lt", "www.vinted.de", "www.vinted.at", "www.vinted.it", "www.vinted.co.uk", "www.vinted.pt", "www.vinted.com", "www.vinted.cz", "www.vinted.sk", "www.vinted.pl", "www.vinted.se", "www.vinted.hu", "www.vinted.ro", "www.vinted.dk", "www.vinted.fi", "www.vinted.hr", "www.vinted.gr"]
      , INVALID_SUBDOMAIN_PREFIXES = ["images", "images1", "images2", "images3", "static", "cdn", "api", "assets", "media", "img", "content", "files", "upload", "cache", "web"];
    function isValidVintedDomain(domain) {
        if (!domain)
            return !1;
        const normalizedDomain = domain.toLowerCase();
        if (VINTED_DOMAINS.includes(normalizedDomain))
            return !0;
        for (const prefix of INVALID_SUBDOMAIN_PREFIXES)
            if (normalizedDomain.startsWith(prefix + ".vinted.") || normalizedDomain.startsWith("www." + prefix + ".vinted.") || normalizedDomain.includes("." + prefix + ".vinted."))
                return console.warn(`[DOMAIN_VALIDATION] âš ï¸ Invalid domain detected (CDN/image subdomain): ${domain}`),
                !1;
        return /^www\.vinted\.[a-z]{2,3}(\.uk)?$/.test(normalizedDomain)
    }
    async function detectVintedDomainFromCookies() {
        try {
            const foundDomains = [];
            for (const domain of VINTED_DOMAINS)
                try {
                    const cookies = await chrome.cookies.getAll({
                        domain: domain.replace("www.", ""),
                        name: "access_token_web"
                    });
                    if (cookies && cookies.length > 0) {
                        const validCookie = cookies.reduce(( (best, current) => best ? (current.expirationDate || 0) > (best.expirationDate || 0) ? current : best : current), null);
                        validCookie && foundDomains.push({
                            domain: domain,
                            expirationDate: validCookie.expirationDate || 0,
                            cookie: validCookie
                        })
                    }
                } catch (err) {}
            if (0 === foundDomains.length)
                return null;
            const bestDomain = foundDomains.reduce(( (best, current) => best ? current.expirationDate > best.expirationDate ? current : best : current), null);
            return isValidVintedDomain(bestDomain.domain) ? (await chrome.storage.local.set({
                domain: bestDomain.domain
            }),
            console.log(`[DETECT_DOMAIN] âœ… Domain saved to chrome storage: ${bestDomain.domain}`),
            bestDomain.domain) : (console.error(`[DETECT_DOMAIN] âŒ Invalid domain detected, not saving: ${bestDomain.domain}`),
            null)
        } catch (error) {
            return console.error("[DETECT_DOMAIN] âŒ Error detecting Vinted domain:", error),
            null
        }
    }
    !async function() {
        let existingDomain = await getFromStorage("domain");
        if (existingDomain && !isValidVintedDomain(existingDomain) && (console.warn(`[INIT_DOMAIN] âš ï¸ Invalid domain in storage: ${existingDomain}, clearing...`),
        await chrome.storage.local.remove(["domain"]),
        existingDomain = null),
        existingDomain)
            try {
                const cookies = await chrome.cookies.getAll({
                    domain: existingDomain.replace("www.", ""),
                    name: "access_token_web"
                });
                if (cookies && cookies.length > 0)
                    return existingDomain
            } catch (err) {}
        await detectVintedDomainFromCookies()
    }();
    let repostUploadLock = !1
      , repostUploadLockTimeout = null;
    let lastLoginCheckTime = 0;
    chrome.cookies.onChanged.addListener((async changeInfo => {
        const {cookie: cookie, removed: removed} = changeInfo;
        if ("access_token_web" !== cookie.name)
            return;
        if (removed)
            return void invalidateAuthGateCache();
        const cookieDomain = cookie.domain.startsWith(".") ? `www${cookie.domain}` : cookie.domain
          , isVintedDomain = VINTED_DOMAINS.some((domain => cookieDomain === domain || cookieDomain.endsWith(domain.replace("www.", ""))));
        if (!isVintedDomain)
            return;
        const domainToSave = VINTED_DOMAINS.find((d => cookieDomain === d || cookieDomain.includes(d.replace("www.", ""))));
        if (!domainToSave || !isValidVintedDomain(domainToSave))
            return;
        const existingDomain = await getFromStorage("domain");
        existingDomain || await chrome.storage.local.set({
            domain: domainToSave
        });
        const now = Date.now();
        if (now - lastLoginCheckTime < 2e3)
            return;
        if (lastLoginCheckTime = now,
        repostUploadLock)
            return;
        invalidateAuthGateCache();
        let domain = existingDomain;
        domain && isValidVintedDomain(domain) || (domain = domainToSave,
        existingDomain && !isValidVintedDomain(existingDomain) && await chrome.storage.local.set({
            domain: domainToSave
        }));
        try {
            const loginResult = await checkLogin(domain);
            if (loginResult.success) {
                const currentUserStats = await getVintedUserStats();
                if (currentUserStats.success) {
                    const savedUser = await getFromStorage("user")
                      , currentUserId = currentUserStats.data.userId;
                    savedUser && savedUser.id && savedUser.id !== currentUserId && await clearUserRelatedData()
                }
                await async function(eventType, data) {
                    try {
                        const tabs = await chrome.tabs.query({
                            url: `chrome-extension://${chrome.runtime.id}/*`
                        });
                        for (const tab of tabs)
                            chrome.tabs.sendMessage(tab.id, {
                                type: eventType,
                                data: data
                            }).catch(( () => {}
                            ))
                    } catch (error) {
                        console.log("[COOKIE_LISTENER] Could not notify tabs:", error.message)
                    }
                }("vintedLoginDetected", {
                    domain: domain,
                    success: !0,
                    vintedData: loginResult.vintedData
                })
            }
        } catch (error) {
            console.error("[COOKIE_LISTENER] Error checking login:", error)
        }
    }
    ));
    var follow_automation_status = !1
      , unfollow_automation_status = !1
      , fetch_notifications_status = !1
      , notifications_interval = null;
    const storage = {
        setup: {
            vinted_id: !1
        },
        subscription: {
            login: !1,
            bearer: null,
            active: !1,
            lastCheck: null,
            user: null
        },
        followunfollowAutomation: {
            feedbackCount: 3,
            itemsBought: 20,
            lastLogin: 7,
            followLimit: 1e4,
            followPerFlow: 1,
            unfollowPerFlow: 1,
            messages: [],
            followed: {
                day: null,
                number: 0
            },
            unfollowed: {
                day: null,
                number: 0
            },
            idsToFollow: []
        },
        newNotifications: {},
        notifications: {
            lastNotification: null
        },
        domain: null,
        following: [],
        orders: []
    };
    var x_csrf = "";
    const FeatureHandler = {
        API_BASE_URL: serverUrl + "/api/v1",
        CACHE_KEY: "featureStatusCache",
        CACHE_DURATION: 3e5,
        CACHE_MAX_AGE: 6e5,
        async getFeatureStatus() {
            try {
                const cachedData = (await chrome.storage.local.get(this.CACHE_KEY))[this.CACHE_KEY]
                  , now = Date.now()
                  , cacheAge = cachedData?.timestamp ? now - cachedData.timestamp : 1 / 0
                  , isCacheValid = cacheAge < this.CACHE_DURATION
                  , isCacheUsable = cacheAge < this.CACHE_MAX_AGE;
                if (cachedData && isCacheValid)
                    return this.refreshFeatureStatusBackground(),
                    cachedData.data;
                const session = await this.getCurrentSession();
                if (!session) {
                    if (console.error("[ERROR] No active session found"),
                    cachedData && isCacheUsable)
                        return cachedData.data;
                    throw new Error("No active session found")
                }
                const url = `${this.API_BASE_URL}/feature_status`
                  , response = await fetch(url, {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${session.token}`,
                        "Content-Type": "application/json"
                    }
                });
                if (!response.ok) {
                    if (console.error("[ERROR] Failed to fetch feature status:", response.statusText),
                    cachedData && isCacheUsable)
                        return cachedData.data;
                    throw new Error(`Failed to fetch feature status: ${response.statusText}`)
                }
                const data = await response.json();
                return await chrome.storage.local.set({
                    [this.CACHE_KEY]: {
                        timestamp: Date.now(),
                        data: data,
                        lastSuccessfulFetch: Date.now()
                    }
                }),
                data
            } catch (error) {
                console.error("[ERROR] Exception in getFeatureStatus:", error);
                const cachedData = (await chrome.storage.local.get(this.CACHE_KEY))[this.CACHE_KEY];
                if (cachedData?.data && cachedData?.timestamp) {
                    if (Date.now() - cachedData.timestamp < this.CACHE_MAX_AGE)
                        return cachedData.data
                }
                throw error
            }
        },
        async refreshFeatureStatusBackground() {
            try {
                const session = await this.getCurrentSession();
                if (!session)
                    return;
                const url = `${this.API_BASE_URL}/feature_status`
                  , response = await fetch(url, {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${session.token}`,
                        "Content-Type": "application/json"
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    await chrome.storage.local.set({
                        [this.CACHE_KEY]: {
                            timestamp: Date.now(),
                            data: data,
                            lastSuccessfulFetch: Date.now()
                        }
                    })
                }
            } catch (error) {}
        },
        async canUseFeature(featureName) {
            try {
                const cacheData = (await chrome.storage.local.get(this.CACHE_KEY))[this.CACHE_KEY]
                  , currentTime = Date.now();
                if (!cacheData?.timestamp || currentTime - cacheData.timestamp > 6e5) {
                    await this.getFeatureStatus();
                    const freshCache = await chrome.storage.local.get(this.CACHE_KEY)
                      , featureData = freshCache[this.CACHE_KEY]?.data?.features?.[featureName];
                    if (!featureData)
                        return !1;
                    const dailyOk = featureData.used_today < featureData.daily_limit
                      , monthlyOk = !featureData.monthly_limit || featureData.used_this_month < featureData.monthly_limit
                      , canUse = dailyOk && monthlyOk;
                    return canUse || "aidescription" !== featureName ? canUse : await this.checkOnboardingAICredit()
                }
                const featureData = cacheData?.data?.features?.[featureName];
                if (!featureData)
                    return !1;
                const dailyOk = featureData.used_today < featureData.daily_limit
                  , monthlyOk = !featureData.monthly_limit || featureData.used_this_month < featureData.monthly_limit
                  , canUse = dailyOk && monthlyOk;
                return canUse || "aidescription" !== featureName ? canUse : await this.checkOnboardingAICredit()
            } catch (error) {
                return console.error("Error checking feature usage:", error),
                !1
            }
        },
        async checkOnboardingAICredit() {
            try {
                const session = await this.getCurrentSession();
                if (!session)
                    return !1;
                const response = await fetch(`${this.API_BASE_URL.replace("/api/v1", "")}/api/v1/ai_credits`, {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${session.token}`,
                        "Content-Type": "application/json"
                    }
                });
                if (!response.ok)
                    return !1;
                const result = await response.json();
                return result.success && !0 === result.onboarding_credit_available
            } catch (error) {
                return console.error("[FEATURE_HANDLER] Error checking onboarding AI credit:", error),
                !1
            }
        },
        async incrementFeature(featureName, incrementN=1) {
            try {
                const currentCache = (await chrome.storage.local.get(this.CACHE_KEY))[this.CACHE_KEY]
                  , featureData = currentCache?.data?.features?.[featureName];
                if (!featureData)
                    throw console.error(`[ERROR] Feature ${featureName} not found`),
                    new Error(`Feature ${featureName} not found`);
                const oldUsage = featureData.used_today;
                featureData.used_today += incrementN,
                await chrome.storage.local.set({
                    [this.CACHE_KEY]: currentCache
                });
                if (!await this.notifyServerIncrement(featureName, incrementN))
                    throw console.error("[ERROR] Server increment failed, rolling back local increment"),
                    featureData.used_today = oldUsage,
                    await chrome.storage.local.set({
                        [this.CACHE_KEY]: currentCache
                    }),
                    new Error("Failed to update server");
                return this.broadcastUpdate(),
                {
                    success: !0,
                    feature: featureData
                }
            } catch (error) {
                throw console.error("[ERROR] Exception in incrementFeature:", error),
                error
            }
        },
        async notifyServerIncrement(featureName, incrementN=1) {
            try {
                const session = await this.getCurrentSession();
                if (!session)
                    return console.error("[ERROR] No session found for notifyServerIncrement"),
                    !1;
                const url = `${this.API_BASE_URL}/increment_feature`
                  , response = await fetch(url, {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${session.token}`,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        feature: featureName,
                        increment: incrementN
                    })
                });
                if (!response.ok) {
                    console.error(`[ERROR] Server returned status ${response.status}`);
                    const errorText = await response.text();
                    return console.error(`[ERROR] Server response: ${errorText}`),
                    !1
                }
                const result = await response.json();
                return !!result.success || (console.error(`[ERROR] Server increment failed: ${result.message}`),
                !1)
            } catch (error) {
                return console.error("[ERROR] Exception in notifyServerIncrement:", error),
                !1
            }
        },
        async broadcastUpdate() {
            (await chrome.tabs.query({})).forEach((tab => {
                chrome.tabs.sendMessage(tab.id, {
                    type: "featureUpdate"
                }).catch(( () => {}
                ))
            }
            ))
        },
        async getFeatureLimits(featureName) {
            const cache = await chrome.storage.local.get(this.CACHE_KEY)
              , featureData = cache[this.CACHE_KEY]?.data?.features?.[featureName];
            return featureData ? {
                used: featureData.used_today,
                limit: featureData.daily_limit,
                usedMonthly: featureData.used_this_month || 0,
                monthlyLimit: featureData.monthly_limit || null
            } : null
        },
        async clearCache() {
            await chrome.storage.local.remove(this.CACHE_KEY)
        },
        async getCurrentSession() {
            try {
                const session = await checkLoginSupabase();
                return session ? {
                    token: session.access_token,
                    userId: session.user.id
                } : null
            } catch (error) {
                return console.error("Error getting current session:", error),
                null
            }
        }
    }
      , DISMISSED_ANNOUNCEMENTS_KEY = "dismissed_announcements";
    async function getActiveAnnouncements() {
        try {
            const data = await async function() {
                try {
                    const response = await fetch("https://gist.githubusercontent.com/alessandroirace/6d0af357f4477bac616698a5ad5c63ba/raw/announcements.json", {
                        method: "GET",
                        headers: {
                            Accept: "application/json"
                        },
                        cache: "no-store"
                    });
                    if (!response.ok)
                        return console.error("[ANNOUNCEMENTS] Failed to fetch:", response.status, response.statusText),
                        null;
                    const text = await response.text();
                    try {
                        return JSON.parse(text)
                    } catch (parseError) {
                        return console.error("[ANNOUNCEMENTS] JSON parse error:", parseError),
                        null
                    }
                } catch (error) {
                    return console.error("[ANNOUNCEMENTS] Fetch error:", error.message, error),
                    null
                }
            }();
            if (!data || !data.configurazione_generale?.sistema_attivo)
                return [];
            const announcements = data.annunci || []
              , extensionVersion = chrome.runtime.getManifest().version
              , dismissedIds = (await chrome.storage.local.get("dismissed_announcements")).dismissed_announcements || [];
            return announcements.filter((announcement => {
                if (!announcement.attivo)
                    return !1;
                if (dismissedIds.includes(announcement.id))
                    return !1;
                const targetMode = announcement.target_mode
                  , targetVersions = announcement.versioni_target || [];
                return !("all" !== targetMode && !targetVersions.includes("all")) || ("include" === targetMode ? targetVersions.includes(extensionVersion) : "exclude" === targetMode && !targetVersions.includes(extensionVersion))
            }
            ))
        } catch (error) {
            return console.error("[ANNOUNCEMENTS] Error getting active announcements:", error),
            []
        }
    }
    function sleep(ms) {
        return new Promise((resolve => setTimeout(resolve, ms)))
    }
    async function getFromStorage(key) {
        return new Promise(( (resolve, reject) => {
            chrome.storage.local.get([key], (result => {
                chrome.runtime.lastError ? reject(chrome.runtime.lastError) : resolve(result[key])
            }
            ))
        }
        ))
    }
    async function updateStatus() {
        try {
            chrome.tabs.query({
                url: `chrome-extension://${chrome.runtime.id}/*`
            }, (tabs => {
                tabs.forEach((tab => chrome.tabs.sendMessage(tab.id, "updateUI").catch(( () => {}
                ))))
            }
            ))
        } catch (error) {}
    }
    const SYNCABLE_DIRECT_KEYS = ["autoMsg_templates", "autoMsg_discount", "autoMsg_delay", "autoMsg_dailyLimit", "autoMsg_ruleReviews", "autoMsg_minReviews", "auto_messages_enabled", "autoMessagesConsent", "vindy_product_costs", "vindy_achievements", "vindyButtonPosition", "boostLikesConsent", "boost_likes_enabled"];
    let _settingsSyncTimer = null
      , _settingsSyncVersion = 0;
    async function applySettingsFromServer(serverSettings) {
        if (!serverSettings || "object" != typeof serverSettings)
            return;
        const toSet = {};
        for (const key of SYNCABLE_DIRECT_KEYS)
            void 0 !== serverSettings[key] && (toSet[key] = serverSettings[key]);
        if (serverSettings.quickReplies && "object" == typeof serverSettings.quickReplies)
            for (const [lang,replies] of Object.entries(serverSettings.quickReplies))
                Array.isArray(replies) && (toSet[`vindyQuickReplies_${lang}`] = replies);
        if (serverSettings.followunfollowConfig && "object" == typeof serverSettings.followunfollowConfig) {
            const existing = await getFromStorage("followunfollowAutomation") || {
                feedbackCount: 3,
                itemsBought: 20,
                lastLogin: 7,
                followLimit: 1e4,
                followPerFlow: 1,
                unfollowPerFlow: 1,
                messages: [],
                followed: {
                    day: null,
                    number: 0
                },
                unfollowed: {
                    day: null,
                    number: 0
                },
                idsToFollow: []
            }
              , config = serverSettings.followunfollowConfig;
            existing.feedbackCount = config.feedbackCount ?? existing.feedbackCount,
            existing.itemsBought = config.itemsBought ?? existing.itemsBought,
            existing.lastLogin = config.lastLogin ?? existing.lastLogin,
            existing.followLimit = config.followLimit ?? existing.followLimit,
            existing.followPerFlow = config.followPerFlow ?? existing.followPerFlow,
            existing.unfollowPerFlow = config.unfollowPerFlow ?? existing.unfollowPerFlow,
            toSet.followunfollowAutomation = existing
        }
        Object.keys(toSet).length > 0 && await chrome.storage.local.set(toSet)
    }
    async function syncSettingsToServer() {
        try {
            const session = await getSession();
            if (!session || !session.access_token)
                return {
                    success: !1,
                    error: "Not logged in"
                };
            const settings = await async function() {
                const settings = {}
                  , directData = await chrome.storage.local.get(SYNCABLE_DIRECT_KEYS);
                for (const key of SYNCABLE_DIRECT_KEYS)
                    void 0 !== directData[key] && (settings[key] = directData[key]);
                const allStorage = await chrome.storage.local.get(null)
                  , quickReplies = {};
                for (const [key,value] of Object.entries(allStorage))
                    key.startsWith("vindyQuickReplies_") && Array.isArray(value) && (quickReplies[key.replace("vindyQuickReplies_", "")] = value);
                Object.keys(quickReplies).length > 0 && (settings.quickReplies = quickReplies);
                const followData = allStorage.followunfollowAutomation;
                return followData && "object" == typeof followData && (settings.followunfollowConfig = {
                    feedbackCount: followData.feedbackCount,
                    itemsBought: followData.itemsBought,
                    lastLogin: followData.lastLogin,
                    followLimit: followData.followLimit,
                    followPerFlow: followData.followPerFlow,
                    unfollowPerFlow: followData.unfollowPerFlow
                }),
                settings
            }()
              , response = await fetch(`${serverUrl}/api/v1/user_settings`, {
                method: "PUT",
                headers: {
                    Authorization: `Bearer ${session.access_token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    settings: settings,
                    version: _settingsSyncVersion
                })
            })
              , result = await response.json();
            return response.ok ? (_settingsSyncVersion = result.version || _settingsSyncVersion + 1,
            {
                success: !0,
                version: _settingsSyncVersion
            }) : 409 === response.status ? (result.server_settings && (await applySettingsFromServer(result.server_settings),
            _settingsSyncVersion = result.server_version || 0),
            {
                success: !0,
                version: _settingsSyncVersion,
                conflict: !0,
                source: "server"
            }) : (console.error("[SETTINGS_SYNC] Save failed:", result),
            {
                success: !1,
                error: result.error || "API error"
            })
        } catch (error) {
            return console.error("[SETTINGS_SYNC] Save error:", error),
            {
                success: !1,
                error: error.message
            }
        }
    }
    async function verifyAndCleanCommunityLikes() {
        console.log("[COMMUNITY_CLEANUP] Starting verification of stored notifications...");
        try {
            const session = await getFromStorage("supabaseSession");
            if (!session || !session.access_token)
                return await chrome.storage.local.set({
                    pendingCommunityLikesCleanup: !0
                }),
                setTimeout(( () => verifyAndCleanCommunityLikes()), 6e4),
                {
                    success: !1,
                    reason: "not_logged_in"
                };
            const notifications = await getFromStorage("notifications");
            if (!notifications || "object" != typeof notifications || 0 === Object.keys(notifications).length)
                return await chrome.storage.local.remove("pendingCommunityLikesCleanup"),
                {
                    success: !0,
                    cleaned: 0
                };
            const likesToCheck = []
              , likeLocationMap = {};
            for (const productId in notifications) {
                const notificationArray = notifications[productId];
                Array.isArray(notificationArray) && notificationArray.forEach(( (notif, index) => {
                    if (20 == notif.entry_type && notif.liker_id) {
                        const key = `${productId}_${notif.liker_id}`;
                        likesToCheck.push({
                            product_id: String(productId),
                            vinted_user_id: String(notif.liker_id)
                        }),
                        likeLocationMap[key] = {
                            productId: productId,
                            index: index,
                            notifId: notif.id
                        }
                    }
                }
                ))
            }
            if (0 === likesToCheck.length)
                return await chrome.storage.local.remove("pendingCommunityLikesCleanup"),
                {
                    success: !0,
                    cleaned: 0
                };
            const BATCH_SIZE = 100;
            let totalCommunityLikes = 0;
            const communityLikeKeys = new Set;
            for (let i = 0; i < likesToCheck.length; i += BATCH_SIZE) {
                const batch = likesToCheck.slice(i, i + BATCH_SIZE);
                try {
                    const checkResponse = await fetch(`${serverUrl}/api/v1/boost/check_community_likes`, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${session.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            likes: batch
                        })
                    });
                    if (checkResponse.ok) {
                        const checkResult = await checkResponse.json();
                        checkResult.success && checkResult.results && Object.entries(checkResult.results).forEach(( ([key,isCommunity]) => {
                            isCommunity && (communityLikeKeys.add(key),
                            totalCommunityLikes++)
                        }
                        ))
                    }
                } catch (batchError) {
                    console.error(`[COMMUNITY_CLEANUP] Error checking batch ${i / BATCH_SIZE + 1}:`, batchError)
                }
                i + BATCH_SIZE < likesToCheck.length && await new Promise((resolve => setTimeout(resolve, 200)))
            }
            if (0 === communityLikeKeys.size)
                return await chrome.storage.local.remove("pendingCommunityLikesCleanup"),
                {
                    success: !0,
                    cleaned: 0
                };
            let removedCount = 0;
            for (const productId in notifications) {
                const notificationArray = notifications[productId];
                if (!Array.isArray(notificationArray))
                    continue;
                const originalLength = notificationArray.length;
                notifications[productId] = notificationArray.filter((notif => {
                    if (20 != notif.entry_type || !notif.liker_id)
                        return !0;
                    const key = `${productId}_${notif.liker_id}`
                      , shouldRemove = communityLikeKeys.has(key);
                    return !shouldRemove
                }
                )),
                removedCount += originalLength - notifications[productId].length,
                0 === notifications[productId].length && delete notifications[productId]
            }
            return await chrome.storage.local.set({
                notifications: notifications
            }),
            await chrome.storage.local.remove("pendingCommunityLikesCleanup"),
            console.log(`[COMMUNITY_CLEANUP] âœ… Removed ${removedCount} community likes from storage`),
            {
                success: !0,
                cleaned: removedCount
            }
        } catch (error) {
            return console.error("[COMMUNITY_CLEANUP] âŒ Error during cleanup:", error),
            {
                success: !1,
                error: error.message
            }
        }
    }
    async function fetch_notifications() {
        try {
            var domain = await getFromStorage("domain");
            let lastProcessedNotificationId = await getFromStorage("lastProcessedNotificationId")
              , existingNotifications = await getFromStorage("notifications");
            existingNotifications && "object" == typeof existingNotifications || (existingNotifications = {});
            let existingLikeIds = new Set;
            Object.values(existingNotifications).forEach((notificationArray => {
                Array.isArray(notificationArray) && notificationArray.forEach((notif => {
                    20 == notif.entry_type && existingLikeIds.add(notif.id)
                }
                ))
            }
            ));
            for (var page = 0, foundLastProcessed = !1, firstNotificationId = null; ; ) {
                page++;
                var resp = await fetch("https://" + domain + "/web/api/notifications/notifications?page=" + page + "&per_page=99", {
                    method: "GET",
                    headers: {
                        accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                    }
                });
                if (!resp.ok) {
                    console.error(`[FETCH_NOTIFICATIONS] âŒ Error fetching page ${page}:`, resp.status);
                    break
                }
                {
                    var data = await resp.json()
                      , page_notifications = []
                      , pageLikes = [];
                    data.notifications.forEach(( (notification, index) => {
                        if (1 === page && 0 === index && (firstNotificationId = notification.id),
                        lastProcessedNotificationId && notification.id === lastProcessedNotificationId)
                            foundLastProcessed = !0;
                        else if (20 == notification.entry_type && !existingLikeIds.has(notification.id)) {
                            const offeringMatch = notification.link?.match(/offering_id=(\d+)/);
                            if (!offeringMatch)
                                return;
                            notification.liker_id = offeringMatch[1],
                            notification.viewed = !1,
                            page_notifications.push(notification),
                            existingLikeIds.add(notification.id),
                            pageLikes.push({
                                notification_id: notification.id,
                                item_id: notification.subject_id,
                                liker_vinted_id: notification.liker_id,
                                liked_at: notification.updated_at,
                                notification_body: notification.body,
                                item_photo_url: notification.small_photo_url,
                                domain: domain
                            })
                        }
                    }
                    ));
                    let filteredNotifications = page_notifications;
                    if (pageLikes.length > 0)
                        try {
                            const likesToCheck = pageLikes.map((like => ({
                                product_id: String(like.item_id),
                                vinted_user_id: String(like.liker_vinted_id)
                            })))
                              , checkResponse = await fetch(`${serverUrl}/api/v1/boost/check_community_likes`, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    likes: likesToCheck
                                })
                            });
                            if (checkResponse.ok) {
                                const checkResult = await checkResponse.json();
                                if (checkResult.success && checkResult.results) {
                                    const communityLikeKeys = new Set(Object.entries(checkResult.results).filter(( ([key,isCommunity]) => isCommunity)).map(( ([key]) => key)));
                                    communityLikeKeys.size > 0 && (filteredNotifications = page_notifications.filter((notification => {
                                        const key = `${notification.subject_id}_${notification.liker_id}`
                                          , isCommunityLike = communityLikeKeys.has(key);
                                        return !isCommunityLike
                                    }
                                    )))
                                }
                            }
                        } catch (checkError) {
                            console.error("[FETCH_NOTIFICATIONS] âš ï¸ Error checking community likes, saving all:", checkError.message)
                        }
                    filteredNotifications.length > 0 && filteredNotifications.length;
                    let res = await getFromStorage("notifications") || {}
                      , res_new = await getFromStorage("newNotifications") || {};
                    for (let i = 0; i < filteredNotifications.length; i++)
                        null == res[filteredNotifications[i].subject_id] ? (res[filteredNotifications[i].subject_id] = [filteredNotifications[i]],
                        res_new[filteredNotifications[i].subject_id] = [filteredNotifications[i]]) : (res[filteredNotifications[i].subject_id].push(filteredNotifications[i]),
                        null == res_new[filteredNotifications[i].subject_id] ? res_new[filteredNotifications[i].subject_id] = [filteredNotifications[i]] : res_new[filteredNotifications[i].subject_id].push(filteredNotifications[i]));
                    if (await chrome.storage.local.set({
                        notifications: res
                    }),
                    foundLastProcessed || data.pagination.total_pages <= page)
                        break
                }
            }
            firstNotificationId && await chrome.storage.local.set({
                lastProcessedNotificationId: firstNotificationId
            })
        } catch (error) {
            console.error("[FETCH_NOTIFICATIONS] âŒ Error during fetch:", error)
        } finally {
            fetch_notifications_status = !1
        }
    }
    var fetch_offers_status = !1;
    async function deleteVintedItem(itemId, retryCount=0) {
        try {
            if (!itemId)
                throw new Error("Missing required parameter: itemId");
            const domain = await getFromStorage("domain");
            if (!domain)
                throw new Error("Domain not found in storage");
            if (x_csrf || await updateCSRF(),
            !x_csrf)
                throw new Error("Failed to get CSRF token");
            const url = `https://${domain}/api/v2/items/${itemId}/delete`
              , response = await fetch(url, {
                method: "POST",
                headers: {
                    "x-csrf-token": x_csrf,
                    accept: "application/json, text/plain, */*",
                    "content-length": "0"
                },
                credentials: "include"
            });
            if ((403 === response.status || 422 === response.status) && retryCount < 2)
                return x_csrf = "",
                await updateCSRF(),
                await deleteVintedItem(itemId, retryCount + 1);
            if (!response.ok) {
                const errorText = await response.text();
                throw console.error("[DELETE_ITEM] API error:", errorText),
                new Error(`Failed to delete item: ${response.status} ${response.statusText}`)
            }
            let result = null;
            try {
                result = await response.json()
            } catch (e) {
                result = {
                    success: !0
                }
            }
            return console.log("[DELETE_ITEM] âœ… Item deleted successfully"),
            {
                success: !0,
                message: "Item deleted successfully",
                data: result
            }
        } catch (error) {
            return console.error("[DELETE_ITEM] âŒ Error:", error),
            {
                success: !1,
                message: error.message || "Failed to delete item"
            }
        }
    }
    async function clearUserRelatedData() {
        console.log("[CLEAR_DATA] ðŸ—‘ï¸ Clearing user-related data due to profile change..."),
        notifications_interval && (clearInterval(notifications_interval),
        notifications_interval = null),
        follow_automation_status = !1,
        unfollow_automation_status = !1,
        fetch_notifications_status = !1;
        await chrome.storage.local.remove(["user", "items", "orders", "pending_offers", "user_balance", "notifications", "likes_data", "performance_data", "setup"])
    }
    async function fetch_userinfo(domain) {
        try {
            const currentUserResponse = await fetch(`https://${domain}/api/v2/users/current`, {
                method: "GET",
                headers: {
                    Accept: "application/json"
                }
            });
            if (!currentUserResponse.ok)
                return console.error("[FETCH_USERINFO] âŒ Failed to fetch current user:", currentUserResponse.status),
                {
                    success: !1,
                    status: currentUserResponse.status,
                    message: "Not logged in, unable to get current user"
                };
            const currentUserData = await currentUserResponse.json();
            if (!currentUserData.user || !currentUserData.user.id)
                return console.error("[FETCH_USERINFO] âŒ No user data in response"),
                {
                    success: !1,
                    status: 1,
                    message: "Not logged in"
                };
            const currentUserId = currentUserData.user.id
              , savedUser = await getFromStorage("user");
            savedUser && savedUser.id && savedUser.id !== currentUserId && await clearUserRelatedData();
            const userResponse = await fetch(`https://${domain}/api/v2/users/${currentUserId}.json?localize=false`, {
                headers: {
                    accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                }
            });
            if (userResponse.ok) {
                const userData = await userResponse.json();
                return await chrome.storage.local.set({
                    user: userData.user
                }),
                async function(vintedDomain, vintedUser) {
                    try {
                        const session = await checkLoginSupabase();
                        if (!session || 200 !== session.status || !session.access_token)
                            return;
                        const response = await fetch(`${serverUrl}/api/v1/link_vinted_account`, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer ${session.access_token}`
                            },
                            body: JSON.stringify({
                                vinted_domain: vintedDomain,
                                vinted_user_id: vintedUser.id,
                                vinted_username: vintedUser.login || null,
                                profile_photo_url: vintedUser.photo?.url || vintedUser.photo?.full_size_url || null,
                                country_code: vintedUser.country_code || vintedUser.country_iso_code || null,
                                locale: vintedUser.locale || null,
                                iso_locale_code: vintedUser.iso_locale_code || null,
                                currency: vintedUser.currency || null
                            })
                        })
                          , result = await response.json();
                        if (response.ok && result.success) {
                            if (result.already_existed,
                            result.onboarding_step_completed)
                                try {
                                    chrome.runtime.sendMessage({
                                        action: "onboardingStepCompleted",
                                        step: "link_vinted"
                                    })
                                } catch (e) {}
                        } else
                            console.warn("[LINK_VINTED] âš ï¸ Failed to link account:", result.error || result.message)
                    } catch (error) {
                        console.warn("[LINK_VINTED] âš ï¸ Error linking account (non-critical):", error.message)
                    }
                }(domain, userData.user),
                fetch_notifications_status || (fetch_notifications_status = !0,
                fetch_notifications().then(( () => {
                    fetch_notifications_status = !1
                }
                )).catch((error => {
                    console.error("Error in background notification fetch:", error),
                    fetch_notifications_status = !1
                }
                ))),
                await async function() {
                    notifications_interval && clearInterval(notifications_interval),
                    notifications_interval = setInterval((async () => {
                        if (!fetch_notifications_status) {
                            fetch_notifications_status = !0;
                            try {
                                await fetch_notifications()
                            } catch (error) {
                                console.error("Error in automatic notification fetch:", error)
                            } finally {
                                fetch_notifications_status = !1
                            }
                        }
                    }
                    ), 3e5)
                }(),
                {
                    success: !0
                }
            }
            return console.error("Error fetching data:", userResponse.status, userResponse.statusText),
            {
                success: !1,
                status: 1,
                message: "Not logged in"
            }
        } catch (error) {
            return console.error("Error during fetch:", error),
            {
                success: !1,
                status: 0,
                message: "Error fetching data"
            }
        }
    }
    async function completeOnboardingStep(step) {
        try {
            const session = await getSession();
            if (!session || !session.access_token)
                return;
            const cacheKey = `onboarding_step_${step}_completed`;
            if ((await chrome.storage.local.get(cacheKey))[cacheKey])
                return void console.log(`[ONBOARDING] â© Step '${step}' already completed, skipping API call`);
            const response = await fetch(`${serverUrl}/api/v1/onboarding/complete_step`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${session.access_token}`
                },
                body: JSON.stringify({
                    step: step
                })
            })
              , result = await response.json();
            if (response.ok && result.success) {
                console.log(`[ONBOARDING] âœ… Step ${step} completed! All done: ${result.all_completed}`),
                await chrome.storage.local.set({
                    [cacheKey]: !0
                });
                const messagePayload = {
                    action: "onboardingStepCompleted",
                    step: step,
                    allCompleted: result.all_completed
                };
                try {
                    chrome.runtime.sendMessage(messagePayload).catch(( () => {}
                    ))
                } catch (e) {}
                try {
                    const extensionUrl = chrome.runtime.getURL("")
                      , tabs = await chrome.tabs.query({
                        url: extensionUrl + "*"
                    });
                    for (const tab of tabs)
                        chrome.tabs.sendMessage(tab.id, messagePayload).catch(( () => {}
                        ))
                } catch (e) {}
                return result
            }
            return console.warn(`[ONBOARDING] âš ï¸ Failed to complete step ${step}:`, result.error),
            null
        } catch (error) {
            return console.warn(`[ONBOARDING] âš ï¸ Error completing step ${step}:`, error.message),
            null
        }
    }
    async function get_following(id, per_page=100, page=1) {
        const domain = await getFromStorage("domain");
        try {
            const response = await fetch(`https://${domain}/api/v2/users/${id}/followed_users?per_page=${per_page}&page=${page}`, {
                headers: {
                    accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                }
            });
            if (response.ok)
                return await response.json();
            console.error("Error fetching data:", response.status, response.statusText)
        } catch (error) {
            console.error("Error during fetch:", error)
        }
    }
    async function updateCSRF() {
        try {
            const user = await getFromStorage("user")
              , domain = await getFromStorage("domain");
            if (!user || !user.id || !domain)
                return void console.warn("[updateCSRF] Missing user or domain, cannot fetch CSRF token");
            const response = await fetch(`https://${domain}/member/${user.id}`, {
                method: "GET"
            });
            if (response.ok) {
                const match = (await response.text()).match(/CSRF_TOKEN[^0-9A-Za-z]*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
                match && (x_csrf = match[1].replace(/\\/g, ""))
            }
        } catch (error) {
            console.error("Error updating CSRF token:", error)
        }
    }
    async function updateActivity(message, type="info") {
        try {
            let res = await getFromStorage("followunfollowAutomation");
            res || (res = {
                feedbackCount: 3,
                itemsBought: 20,
                lastLogin: 7,
                followLimit: 1e4,
                followPerFlow: 1,
                unfollowPerFlow: 1,
                messages: [],
                followed: {
                    day: null,
                    number: 0
                },
                unfollowed: {
                    day: null,
                    number: 0
                },
                idsToFollow: []
            }),
            res.messages || (res.messages = []);
            const messageObject = {
                message: message,
                type: type,
                timestamp: (new Date).toISOString()
            };
            res.messages.unshift(messageObject),
            res.messages.length > 20 && res.messages.pop(),
            await chrome.storage.local.set({
                followunfollowAutomation: res
            }),
            updateStatus()
        } catch (error) {
            console.error("Error updating activity:", error)
        }
    }
    async function getSimilarItemsUsers() {
        try {
            const domain = await getFromStorage("domain");
            if (!domain)
                return {
                    success: !1,
                    users: [],
                    error: "Domain not found"
                };
            let items = await getFromStorage("items");
            if (!items || 0 === items.length) {
                const user = await getFromStorage("user");
                if (!user || !user.id)
                    return {
                        success: !1,
                        users: [],
                        error: "NO_PRODUCTS",
                        message: "You need to upload products on Vinted before starting the follow automation."
                    };
                const response = await fetch(`https://${domain}/api/v2/wardrobe/${user.id}/items?page=1&per_page=200`, {
                    headers: {
                        accept: "application/json"
                    }
                });
                if (!response.ok)
                    return {
                        success: !1,
                        users: [],
                        error: "FETCH_FAILED",
                        message: "Failed to fetch your products from Vinted."
                    };
                items = (await response.json()).items || [],
                await chrome.storage.local.set({
                    items: items
                })
            }
            if (!items || 0 === items.length)
                return {
                    success: !1,
                    users: [],
                    error: "NO_PRODUCTS",
                    message: "You need to upload products on Vinted before starting the follow automation."
                };
            const itemsOnSale = items.filter((item => !item.is_draft && !item.is_processing && "sold" !== item.item_closing_action && 1 != item.is_hidden));
            let itemsToSearch = itemsOnSale
              , searchType = "on_sale";
            if (0 === itemsOnSale.length) {
                const soldItems = items.filter((item => "sold" === item.item_closing_action));
                soldItems.length > 0 ? (itemsToSearch = soldItems,
                searchType = "sold") : (itemsToSearch = items.filter((item => !item.is_draft)),
                searchType = "all")
            }
            if (0 === itemsToSearch.length)
                return {
                    success: !1,
                    users: [],
                    error: "NO_VALID_PRODUCTS",
                    message: "No valid products found to search for similar items."
                };
            const maxProductsToSearch = Math.min(itemsToSearch.length, 10)
              , selectedItems = itemsToSearch.slice(0, maxProductsToSearch)
              , allUserIds = new Set
              , currentUserId = (await getFromStorage("user"))?.id;
            for (const item of selectedItems)
                try {
                    const similarResponse = await fetch(`https://${domain}/api/v2/items/${item.id}/more?content_source=similar_items&screen=item`, {
                        headers: {
                            accept: "application/json"
                        }
                    });
                    if (similarResponse.ok) {
                        const similarItems = (await similarResponse.json()).items || [];
                        for (const similarItem of similarItems)
                            similarItem.user_id && similarItem.user_id !== currentUserId && allUserIds.add(similarItem.user_id)
                    }
                    await sleep(300)
                } catch (error) {
                    console.error(`[SIMILAR_USERS] Error fetching similar items for ${item.id}:`, error)
                }
            const userIdsArray = Array.from(allUserIds);
            return 0 === userIdsArray.length ? {
                success: !1,
                users: [],
                error: "NO_SIMILAR_USERS",
                message: "Could not find similar items or users. Try uploading more products or different categories."
            } : {
                success: !0,
                users: userIdsArray,
                searchType: searchType,
                productsSearched: selectedItems.length
            }
        } catch (error) {
            return console.error("[SIMILAR_USERS] âŒ Error:", error),
            {
                success: !1,
                users: [],
                error: "UNEXPECTED_ERROR",
                message: error.message || "An unexpected error occurred."
            }
        }
    }
    async function getFeedback(id) {
        try {
            if (!id)
                throw new Error("User ID is required");
            const domain = await getFromStorage("domain");
            if (!domain)
                throw new Error("Domain not found");
            const response = await fetch(`https://${domain}/api/v2/user_feedbacks?user_id=${id}&page=1&per_page=100&by=all`, {
                headers: {
                    accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                }
            });
            if (!response.ok)
                throw new Error(`Request failed with status: ${response.status}`);
            const data = await response.json();
            if (!data)
                throw new Error("No data received");
            return data
        } catch (error) {
            return console.error("getFeedback error:", error),
            null
        }
    }
    async function checkFilters(feedback) {
        let filters = await getFromStorage("followunfollowAutomation");
        if (feedback.user.feedback_count < filters.feedbackCount)
            return !1;
        if (feedback.user.taken_item_count < filters.itemsBought)
            return !1;
        let last_login = new Date(feedback.user.last_loged_on_ts)
          , now = new Date
          , diffTime = Math.abs(now - last_login);
        return !(Math.ceil(diffTime / 864e5) > filters.lastLogin)
    }
    async function getUser(id) {
        const domain = await getFromStorage("domain")
          , response = await fetch("https://" + domain + "/api/v2/users/" + id + ".json", {
            headers: {
                accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
            }
        });
        var status = response.status;
        if (200 == status || 304 == status) {
            return await response.json()
        }
        return null
    }
    async function follow_unfollow(id, retry=!0, _retryCount429=0) {
        try {
            const domain = await getFromStorage("domain");
            if (!domain)
                throw new Error("Domain not found");
            if (x_csrf || await updateCSRF(),
            Array.isArray(id) && id.length > 1)
                return {
                    code: 403,
                    message: "You are trying to unfollow more than one user at a time. This is not allowed. Please try again."
                };
            Array.isArray(id) && (id = id[0]);
            const data_ts = {
                user_id: id
            }
              , response = await fetch("https://" + domain + "/api/v2/followed_users/toggle", {
                body: JSON.stringify(data_ts),
                headers: {
                    "Content-Type": "application/json",
                    "x-csrf-token": x_csrf
                },
                method: "POST"
            });
            if (response.ok)
                return await response.json();
            if (429 === response.status && retry && _retryCount429 < 3)
                return await sleep(Math.floor(10001 * Math.random() + 2e4)),
                await follow_unfollow(id, !0, _retryCount429 + 1);
            if (429 === response.status)
                return {
                    code: 429,
                    message: "Rate limited after multiple retries, please try again later"
                };
            if (403 === response.status && retry)
                return await updateCSRF(),
                await follow_unfollow(id, !1);
            if (401 === response.status && retry)
                return await updateCSRF(),
                await follow_unfollow(id, !1);
            if (401 === response.status)
                return {
                    code: 401,
                    message: "Open Vinted in another tab, and restart the automation"
                };
            if (403 === response.status)
                return {
                    code: 403,
                    message: "Rate Limited, retry later"
                };
            if (524 === response.status && retry)
                return await follow_unfollow(id, !1);
            if (524 === response.status)
                return {
                    code: 524,
                    message: "Vinted server timeout, retry later"
                };
            try {
                return await response.json()
            } catch {
                return {
                    code: response.status,
                    message: response.statusText || "Unknown error"
                }
            }
        } catch (error) {
            return {
                code: 400,
                message: error.message || "Unknown error"
            }
        }
    }
    async function processFeedbacks(feedbacks) {
        let usersAlreadyFollowed = await getFromStorage("following");
        usersAlreadyFollowed && Array.isArray(usersAlreadyFollowed) || (usersAlreadyFollowed = [],
        await chrome.storage.local.set({
            following: []
        }));
        let usersToFollow = [];
        for (let feedback of feedbacks.user_feedbacks) {
            if (null == feedback.user || null == feedback.user)
                continue;
            if (usersAlreadyFollowed.includes(feedback.user.id))
                continue;
            const user = await getUser(feedback.user.id);
            if (user) {
                if (user.user.is_account_ban_permanent)
                    continue;
                if (user.user.is_favourite)
                    continue;
                feedback.user = user.user,
                await checkFilters(feedback) && (user.user.is_account_ban_permanent || 1 != user.user.can_view_profile || user.user.is_catalog_moderator || user.user.moderator || user.user.hates_you || user.business || usersToFollow.push(user.user.id))
            }
        }
        return usersToFollow
    }
    function getRandomSleepTime(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min
    }
    function aggiungiNuoveChiavi(dizionario1, dizionario2) {
        const nuovoDizionario = {
            ...dizionario2
        }
          , chiaviDizionario1 = Object.keys(dizionario1);
        for (const chiave of chiaviDizionario1)
            chiave in nuovoDizionario ? "object" != typeof dizionario1[chiave] || "object" != typeof nuovoDizionario[chiave] || null === dizionario1[chiave] || null === nuovoDizionario[chiave] || Array.isArray(dizionario1[chiave]) || Array.isArray(nuovoDizionario[chiave]) || (nuovoDizionario[chiave] = aggiungiNuoveChiavi(dizionario1[chiave], nuovoDizionario[chiave])) : nuovoDizionario[chiave] = dizionario1[chiave];
        return nuovoDizionario
    }
    chrome.runtime.onInstalled.addListener((details => {
        "install" === details.reason ? (console.log("Extension installed for the first time"),
        Analytics.fireEvent("install"),
        chrome.runtime.openOptionsPage(),
        chrome.storage.local.get(null, (function(data) {
            var nuovaData = aggiungiNuoveChiavi(storage, data);
            chrome.storage.local.set(nuovaData, (function() {}
            ))
        }
        ))) : "update" === details.reason && (console.log("Extension updated to version", chrome.runtime.getManifest().version),
        Analytics.fireEvent("updated"),
        chrome.storage.local.get(null, (function(data) {
            var nuovaData = aggiungiNuoveChiavi(storage, data);
            chrome.storage.local.set(nuovaData, (function() {}
            ))
        }
        ))),
        setTimeout(( () => verifyAndCleanCommunityLikes()), 1e4),
        console.log("[BOOST_AUTO_LIKE] Starting auto-like loop on startup..."),
        setTimeout(( () => startBoostAutoLikeLoop()), 5e3),
        setTimeout(( () => startAutoMessagesJob()), 7e3)
    }
    )),
    setTimeout(( () => {
        boost_auto_like_status || startBoostAutoLikeLoop(),
        autoMsg_interval || startAutoMessagesJob(),
        verifyAndCleanCommunityLikes()
    }
    ), 1e4),
    chrome.action.onClicked.addListener((async () => {
        try {
            const browserEnv = await getBrowserEnvironment();
            if (browserEnv && browserEnv.isMobile) {
                const mobileDashboardUrl = chrome.runtime.getURL("html/mobile-dashboard/index.html");
                chrome.tabs.create({
                    url: mobileDashboardUrl
                })
            } else
                chrome.runtime.openOptionsPage()
        } catch (error) {
            console.error("[action.onClicked] Error:", error),
            chrome.runtime.openOptionsPage()
        }
    }
    ));
    let checkLoginCache = {
        promise: null,
        timestamp: 0,
        domain: null
    };
    const CHECK_LOGIN_CACHE_TTL = 3e3;
    async function checkLogin(domain, retry=!0) {
        const now = Date.now();
        return checkLoginCache.promise && checkLoginCache.domain === domain && now - checkLoginCache.timestamp < CHECK_LOGIN_CACHE_TTL || (checkLoginCache.domain = domain,
        checkLoginCache.timestamp = now,
        checkLoginCache.promise = async function(domain) {
            try {
                if (repostUploadLock)
                    return {
                        success: !0,
                        vintedData: null,
                        skippedForLock: !0
                    };
                const response = await fetch(`https://${domain}/web/api/auth/refresh`, {
                    method: "POST",
                    headers: {
                        accept: "application/json",
                        "content-type": "application/json"
                    },
                    credentials: "include"
                });
                if (401 === response.status || 403 === response.status)
                    return {
                        success: !1,
                        message: "Not authenticated on Vinted"
                    };
                if (!response.ok)
                    return {
                        success: !1,
                        message: "Error verifying Vinted authentication"
                    };
                if ("user" !== (await response.json()).scope)
                    return {
                        success: !1,
                        message: "Not authenticated on Vinted"
                    };
                const userData = await fetch(`https://${domain}/api/v2/users/current`, {
                    method: "GET",
                    headers: {
                        accept: "application/json"
                    },
                    credentials: "include"
                });
                if (userData.ok) {
                    return {
                        success: !0,
                        vintedData: await userData.json()
                    }
                }
                return {
                    success: !0,
                    vintedData: null
                }
            } catch (error) {
                return console.error("[CHECK_LOGIN] Error during fetch:", error),
                {
                    success: !1,
                    message: "Error during fetch"
                }
            }
        }(domain, retry)),
        checkLoginCache.promise
    }
    async function getVintedUserStats() {
        try {
            const domain = await getFromStorage("domain");
            if (!domain)
                return console.warn("[VINTED STATS] No domain found in storage"),
                {
                    success: !1,
                    error: "Domain not configured"
                };
            const response = await fetch(`https://${domain}/api/v2/users/current`, {
                method: "GET",
                headers: {
                    Accept: "application/json"
                }
            });
            if (!response.ok)
                return console.error("[VINTED STATS] API request failed:", response.status),
                {
                    success: !1,
                    error: "Failed to fetch user data"
                };
            const data = await response.json();
            if (!data.user)
                return console.error("[VINTED STATS] No user data in response"),
                {
                    success: !1,
                    error: "Invalid response format"
                };
            const followers = data.user.followers_count || 0;
            return {
                success: !0,
                data: {
                    followers: followers,
                    following: data.user.following_count || 0,
                    userId: data.user.id,
                    username: data.user.login
                }
            }
        } catch (error) {
            return console.error("[VINTED STATS] Error:", error),
            {
                success: !1,
                error: error.message
            }
        }
    }
    async function checkMembershipStripe(force=!1) {
        const authResponse = await checkLoginSupabase();
        if (!authResponse || "email_not_confirmed" === authResponse.code || "NO_SESSION" === authResponse.code)
            return {
                status: authResponse ? authResponse.status : 403,
                error: authResponse ? authResponse.error : "User not authenticated",
                code: authResponse ? authResponse.code : "NO_SESSION"
            };
        try {
            let subscription = await chrome.storage.local.get("subscription");
            subscription = subscription.subscription;
            const now = (new Date).getTime()
              , CACHE_DURATION = 3e5
              , CACHE_MAX_AGE = 6e5
              , cacheAge = now - (subscription?.lastCheck ? new Date(subscription.lastCheck).getTime() : 0)
              , isCacheUsable = cacheAge < CACHE_MAX_AGE;
            if (subscription && cacheAge < CACHE_DURATION && !force)
                return async function(accessToken) {
                    try {
                        const response = await fetch(serverUrl + "/api/v1/check_membership", {
                            method: "GET",
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer ${accessToken}`
                            }
                        });
                        if (response.ok) {
                            const data = await response.json();
                            await chrome.storage.local.set({
                                subscription: {
                                    hasAccess: data.hasAccess,
                                    plan: data.plan,
                                    isPremium: data.isPremium,
                                    status: data.status,
                                    stripe_product_id: data.stripe_product_id,
                                    has_billing_account: data.has_billing_account || !1,
                                    trial: data.trial || null,
                                    lastCheck: new Date,
                                    lastSuccessfulCheck: new Date
                                }
                            })
                        }
                    } catch (error) {}
                }(authResponse.access_token).catch(( () => {}
                )),
                {
                    status: 200,
                    hasAccess: subscription.hasAccess || !0,
                    plan: subscription.plan || "free",
                    isPremium: subscription.isPremium || !1,
                    stripe_product_id: subscription.stripe_product_id || null
                };
            const response = await fetch(serverUrl + "/api/v1/check_membership", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${authResponse.access_token}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                return await chrome.storage.local.set({
                    subscription: {
                        hasAccess: data.hasAccess,
                        plan: data.plan,
                        isPremium: data.isPremium,
                        status: data.status,
                        stripe_product_id: data.stripe_product_id,
                        has_billing_account: data.has_billing_account || !1,
                        trial: data.trial || null,
                        lastCheck: new Date,
                        lastSuccessfulCheck: new Date
                    }
                }),
                {
                    status: 200,
                    hasAccess: data.hasAccess,
                    plan: data.plan,
                    isPremium: data.isPremium,
                    stripe_product_id: data.stripe_product_id,
                    trial: data.trial || null
                }
            }
            return subscription && isCacheUsable ? {
                status: 200,
                hasAccess: subscription.hasAccess || !0,
                plan: subscription.plan || "free",
                isPremium: subscription.isPremium || !1,
                stripe_product_id: subscription.stripe_product_id || null,
                trial: subscription.trial || null
            } : {
                status: response.status,
                error: `Server responded with status: ${response.status}`
            }
        } catch (error) {
            console.error("[ERROR] Exception in checkMembership:", error);
            if (error.message && (error.message.includes("checksum mismatch") || error.message.includes("Corruption") || error.message.includes("InvalidStateError") || error.message.includes("QuotaExceededError"))) {
                console.error("[checkMembershipStripe] Storage corruption detected, cleaning...");
                try {
                    await chrome.storage.local.remove(["subscription"])
                } catch (cleanupError) {
                    console.error("[checkMembershipStripe] Cleanup failed:", cleanupError)
                }
                return {
                    status: 500,
                    error: "Storage corrotto. Riprova o rieffettua il login.",
                    code: "STORAGE_CORRUPTION"
                }
            }
            try {
                let subscription = await chrome.storage.local.get("subscription");
                if (subscription = subscription.subscription,
                subscription?.lastCheck) {
                    const cacheAge = (new Date).getTime() - new Date(subscription.lastCheck).getTime();
                    if (cacheAge < 6e5)
                        return {
                            status: 200,
                            hasAccess: subscription.hasAccess || !0,
                            plan: subscription.plan || "free",
                            isPremium: subscription.isPremium || !1,
                            stripe_product_id: subscription.stripe_product_id || null,
                            trial: subscription.trial || null
                        }
                }
            } catch (cacheError) {
                console.error("[checkMembershipStripe] Failed to read cache:", cacheError)
            }
            return {
                status: 500,
                error: `Error checking membership: ${error.message}`
            }
        }
    }
    async function fetchRecentLikes(onlyUnviewed=!1) {
        try {
            const notifications = await getFromStorage("notifications");
            if (!notifications || "object" != typeof notifications)
                return console.log("[FETCH_RECENT_LIKES] No notifications found in storage"),
                [];
            let allLikes = [];
            return Object.values(notifications).forEach((notificationArray => {
                Array.isArray(notificationArray) && notificationArray.forEach((notif => {
                    if (20 == notif.entry_type) {
                        if (onlyUnviewed && !0 === notif.viewed)
                            return;
                        allLikes.push(notif)
                    }
                }
                ))
            }
            )),
            allLikes.sort(( (a, b) => {
                if (a.id && b.id)
                    return Number(b.id) - Number(a.id);
                const aTime = a.updated_at ? new Date(a.updated_at).getTime() : 0;
                return (b.updated_at ? new Date(b.updated_at).getTime() : 0) - aTime
            }
            )),
            allLikes
        } catch (error) {
            return console.error("Error fetching recent likes from storage:", error),
            []
        }
    }
    async function checkLoginSupabase() {
        try {
            let {data: data, error: error} = await client.auth.getSession();
            if (!data?.session && !error) {
                const browserEnv = await getBrowserEnvironment();
                if (browserEnv?.isMobile) {
                    const storedSession = await getSession();
                    if (storedSession?.access_token && storedSession?.refresh_token)
                        try {
                            const restored = await client.auth.setSession({
                                access_token: storedSession.access_token,
                                refresh_token: storedSession.refresh_token
                            });
                            restored.data?.session && (data = restored.data,
                            error = restored.error)
                        } catch (restoreError) {
                            console.error("[checkLoginSupabase] Failed to restore session:", restoreError)
                        }
                }
            }
            return error ? (console.error("Error checking session:", error.message),
            {
                status: error.status || 500,
                error: error.message,
                code: error.code || "AUTH_ERROR"
            }) : data && data.session ? data.session.user.email_confirmed_at ? {
                status: 200,
                data: data.session,
                code: "SIGNED_IN",
                access_token: data.session.access_token,
                user: data.session.user
            } : {
                status: 400,
                error: "Email non confermata. Verifica la tua email.",
                code: "email_not_confirmed"
            } : {
                status: 403,
                error: "Utente non autenticato",
                code: "NO_SESSION"
            }
        } catch (e) {
            console.error("Errore imprevisto durante il controllo del login:", e);
            if (e.message && (e.message.includes("checksum mismatch") || e.message.includes("Corruption") || e.message.includes("InvalidStateError") || e.message.includes("QuotaExceededError"))) {
                console.error("[checkLoginSupabase] Storage corruption detected, attempting recovery...");
                try {
                    await chrome.storage.local.remove(["supabase.auth.token", "subscription"]),
                    await client.auth.signOut().catch(( () => {}
                    ))
                } catch (cleanupError) {
                    console.error("[checkLoginSupabase] Cleanup failed:", cleanupError)
                }
                return {
                    status: 500,
                    error: "Storage corrotto. Effettua nuovamente il login.",
                    code: "STORAGE_CORRUPTION"
                }
            }
            return {
                status: 500,
                error: "Errore imprevisto",
                code: "UNEXPECTED_ERROR"
            }
        }
    }
    chrome.runtime.onMessage.addListener(( (request, sender, sendResponse) => ((async () => {
        try {
            const messageType = request.message || request.action;
            if (self.MessageRouter && self.MessageRouter.hasHandler(messageType))
                try {
                    return await self.MessageRouter.handle(request, sender)
                } catch (routerError) {
                    console.error("[MESSAGE_HANDLER] MessageRouter error:", routerError)
                }
            switch (messageType) {
            case "getFeatureStatus":
                return {
                    status: 200,
                    data: await FeatureHandler.getFeatureStatus()
                };
            case "checkVindyStatus":
                try {
                    const authResult = await checkLoginSupabase()
                      , isAuthenticated = authResult && 200 === authResult.status && "SIGNED_IN" === authResult.code
                      , vintedUser = await getFromStorage("user");
                    return {
                        success: !0,
                        isAuthenticated: isAuthenticated,
                        isVintedLinked: !(!vintedUser || !vintedUser.id),
                        vintedUsername: vintedUser?.login || null
                    }
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] checkVindyStatus error:", error),
                    {
                        success: !1,
                        isAuthenticated: !1,
                        isVintedLinked: !1
                    }
                }
            case "getAICredits":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const response = await fetch(`${serverUrl}/api/v1/ai_credits`, {
                        method: "GET",
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`,
                            "Content-Type": "application/json"
                        }
                    })
                      , result = await response.json();
                    return response.ok && result.success ? {
                        success: !0,
                        ...result
                    } : (console.warn("[MESSAGE_HANDLER] getAICredits: API failed:", result.error),
                    {
                        success: !1,
                        error: result.error || "Failed to get AI credits info"
                    })
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error getting AI credits:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "reserveAICredits":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const reserveResp = await fetch(`${serverUrl}/api/v1/ai_credits/reserve`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            items: request.items
                        })
                    })
                      , reserveResult = await reserveResp.json();
                    return reserveResp.ok && reserveResult.success ? {
                        success: !0,
                        ...reserveResult
                    } : {
                        success: !1,
                        error: reserveResult.error || "Reserve failed",
                        remaining: reserveResult.remaining
                    }
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] reserveAICredits error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "refundAICredits":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const refundResp = await fetch(`${serverUrl}/api/v1/ai_credits/refund`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            items: request.items
                        })
                    })
                      , refundResult = await refundResp.json();
                    return refundResp.ok && refundResult.success ? {
                        success: !0,
                        ...refundResult
                    } : {
                        success: !1,
                        error: refundResult.error || "Refund failed"
                    }
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] refundAICredits error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getAnnouncements":
                try {
                    return {
                        success: !0,
                        announcements: await getActiveAnnouncements()
                    }
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error getting announcements:", error),
                    {
                        success: !1,
                        announcements: []
                    }
                }
            case "dismissAnnouncement":
                try {
                    return await async function(announcementId) {
                        try {
                            const dismissedIds = (await chrome.storage.local.get("dismissed_announcements")).dismissed_announcements || [];
                            return dismissedIds.includes(announcementId) || (dismissedIds.push(announcementId),
                            await chrome.storage.local.set({
                                [DISMISSED_ANNOUNCEMENTS_KEY]: dismissedIds
                            })),
                            {
                                success: !0
                            }
                        } catch (error) {
                            return console.error("[ANNOUNCEMENTS] Error dismissing:", error),
                            {
                                success: !1,
                                error: error.message
                            }
                        }
                    }(request.announcementId)
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error dismissing announcement:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getFeatureLimits":
                const limits = await FeatureHandler.getFeatureLimits(request.featureName);
                return {
                    success: null !== limits,
                    limits: limits
                };
            case "increaseFeatureUsage":
                const result = await FeatureHandler.incrementFeature(request.name);
                return "repost" === request.name && completeOnboardingStep("bump_item").catch((e => console.log("[ONBOARDING] Error:", e.message))),
                {
                    status: 200,
                    data: result
                };
            case "canUseTheFeature":
                if (await FeatureHandler.canUseFeature(request.name))
                    return {
                        status: 200
                    };
                {
                    const cache = await chrome.storage.local.get(FeatureHandler.CACHE_KEY)
                      , featureData = cache[FeatureHandler.CACHE_KEY]?.data?.features?.[request.name];
                    let limitType = "daily";
                    if (featureData) {
                        const dailyReached = featureData.used_today >= featureData.daily_limit;
                        featureData.monthly_limit && featureData.monthly_limit > 0 && featureData.used_this_month >= featureData.monthly_limit ? limitType = "monthly" : dailyReached && (limitType = "daily")
                    }
                    return {
                        status: 400,
                        limitType: limitType
                    }
                }
            case "sendMetrics":
                return await async function(action, details={}) {
                    const sessione = await checkLoginSupabase();
                    if (!sessione)
                        return;
                    const data = {
                        user_id: sessione.user.id,
                        action: action,
                        timestamp: (new Date).toISOString(),
                        details: details
                    }
                      , response = await fetch(serverUrl + "/api/v1/analisi", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify(data)
                    });
                    response.ok || console.error("Error sending data:", response.status, response.statusText)
                }(request.event, request.details),
                {
                    status: 200
                };
            case "getServerUrl":
                return {
                    status: 200,
                    serverUrl: serverUrl
                };
            case "classifyGarment":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const classifyResp = await fetch(`${serverUrl}/api/v1/classify_garment`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            image_base64: request.imageBase64,
                            mime_type: request.mimeType
                        })
                    })
                      , classifyResult = await classifyResp.json();
                    return classifyResp.ok && classifyResult.success ? {
                        success: !0,
                        category: classifyResult.category,
                        side: classifyResult.side,
                        view_type: classifyResult.view_type || "product",
                        has_bg: !1 !== classifyResult.has_bg,
                        raw: classifyResult.raw
                    } : {
                        success: !1,
                        error: classifyResult.error || "Classification failed"
                    }
                } catch (error) {
                    return console.error("[BACKGROUND] classifyGarment error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "classifyGarmentsBatch":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const batchResp = await fetch(`${serverUrl}/api/v1/classify_garments_batch`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            images: request.images
                        })
                    })
                      , batchResult = await batchResp.json();
                    return batchResp.ok && batchResult.success ? {
                        success: !0,
                        results: batchResult.results
                    } : {
                        success: !1,
                        error: batchResult.error || "Batch classification failed"
                    }
                } catch (error) {
                    return console.error("[BACKGROUND] classifyGarmentsBatch error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "stageGarment":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const stageResp = await fetch(`${serverUrl}/api/v1/stage_garment`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            image_base64: request.imageBase64,
                            mime_type: request.mimeType,
                            mode: request.mode,
                            category: request.category,
                            side: request.side,
                            background: request.background,
                            model_options: request.modelOptions || null,
                            credits_pre_reserved: request.creditsPreReserved || !1
                        })
                    })
                      , stageResult = await stageResp.json();
                    return stageResp.ok && stageResult.success ? {
                        success: !0,
                        imageUrl: stageResult.image_url,
                        imageBase64: stageResult.image_base64,
                        creditsRemaining: stageResult.credits_remaining
                    } : {
                        success: !1,
                        error: stageResult.error || "Staging failed"
                    }
                } catch (error) {
                    return console.error("[BACKGROUND] stageGarment error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "processAIImage":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const imageUrls = request.imageUrls || (request.imageUrl ? [request.imageUrl] : [])
                      , options = request.options || {};
                    if (0 === imageUrls.length)
                        return {
                            success: !1,
                            error: "No image URL provided"
                        };
                    if (options.addModel && options.modelOptions) {
                        const startResponse = await fetch(`${serverUrl}/api/v1/generate_virtual_model`, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer ${sessione.access_token}`
                            },
                            body: JSON.stringify({
                                image_urls: imageUrls,
                                model_options: options.modelOptions
                            })
                        })
                          , startResult = await startResponse.json();
                        if (!startResponse.ok || !startResult.success)
                            return {
                                success: !1,
                                error: startResult.message || startResult.error || "Failed to start virtual model generation"
                            };
                        const jobId = startResult.job_id;
                        console.log("[BACKGROUND] Virtual model job started:", jobId);
                        const maxWaitTime = 12e4
                          , pollInterval = 3e3
                          , startTime = Date.now();
                        for (; Date.now() - startTime < maxWaitTime; ) {
                            await new Promise((resolve => setTimeout(resolve, pollInterval)));
                            const statusResponse = await fetch(`${serverUrl}/api/v1/job_status/${jobId}`, {
                                method: "GET",
                                headers: {
                                    Authorization: `Bearer ${sessione.access_token}`
                                }
                            })
                              , statusResult = await statusResponse.json();
                            if ("completed" === statusResult.status) {
                                const processedUrls = statusResult.results.filter((r => r.success)).map((r => r.processed));
                                if (0 === processedUrls.length) {
                                    const errors = statusResult.results.filter((r => !r.success && r.error)).map((r => r.error));
                                    return {
                                        success: !1,
                                        error: errors.length > 0 ? errors[0] : "All images failed to process"
                                    }
                                }
                                return {
                                    success: !0,
                                    imageUrl: processedUrls[0] || null,
                                    imageUrls: processedUrls
                                }
                            }
                            if ("failed" === statusResult.status)
                                return {
                                    success: !1,
                                    error: statusResult.error || "Virtual model generation failed"
                                };
                            if (void 0 !== statusResult.progress)
                                try {
                                    const tabs = await chrome.tabs.query({
                                        active: !0,
                                        currentWindow: !0
                                    });
                                    tabs[0] && chrome.tabs.sendMessage(tabs[0].id, {
                                        type: "AI_IMAGE_PROGRESS",
                                        progress: statusResult.progress,
                                        status: statusResult.status,
                                        jobType: "virtual_model"
                                    }).catch(( () => {}
                                    ))
                                } catch (e) {}
                        }
                        return {
                            success: !1,
                            error: "Virtual model generation timed out"
                        }
                    }
                    const pollJobStatus = async (jobId, maxWaitTime=18e4, pollInterval=2e3) => {
                        const startTime = Date.now();
                        for (; Date.now() - startTime < maxWaitTime; ) {
                            await new Promise((resolve => setTimeout(resolve, pollInterval)));
                            const statusResponse = await fetch(`${serverUrl}/api/v1/job_status/${jobId}`, {
                                method: "GET",
                                headers: {
                                    Authorization: `Bearer ${sessione.access_token}`
                                }
                            })
                              , statusResult = await statusResponse.json();
                            if ("completed" === statusResult.status)
                                return {
                                    success: !0,
                                    results: statusResult.results
                                };
                            if ("failed" === statusResult.status)
                                return {
                                    success: !1,
                                    error: statusResult.error || "Processing failed"
                                };
                            if (void 0 !== statusResult.progress)
                                try {
                                    const tabs = await chrome.tabs.query({
                                        active: !0,
                                        currentWindow: !0
                                    });
                                    tabs[0] && chrome.tabs.sendMessage(tabs[0].id, {
                                        type: "AI_IMAGE_PROGRESS",
                                        progress: statusResult.progress,
                                        status: statusResult.status,
                                        jobType: "image_processing"
                                    }).catch(( () => {}
                                    ))
                                } catch (e) {}
                        }
                        return {
                            success: !1,
                            error: "Processing timed out"
                        }
                    }
                      , response = await fetch(`${serverUrl}/api/v1/process_image`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            image_urls: imageUrls,
                            image_url: imageUrls[0],
                            remove_background: options.removeBackground,
                            add_background: options.addBackground,
                            background_style: options.backgroundStyle,
                            custom_prompt: options.customPrompt,
                            center_product: options.centerProduct
                        })
                    })
                      , result = await response.json();
                    if (202 === response.status && result.job_id) {
                        console.log("[BACKGROUND] Async job started:", result.job_id);
                        const jobResult = await pollJobStatus(result.job_id);
                        if (jobResult.success && jobResult.results) {
                            const processedUrls = jobResult.results.image_urls || [];
                            return completeOnboardingStep("use_ai_feature").catch((e => console.log("[ONBOARDING] Error:", e.message))),
                            {
                                success: !0,
                                imageUrl: processedUrls[0] || jobResult.results.image_url,
                                imageUrls: processedUrls,
                                creditsUsed: jobResult.results.credits_used || imageUrls.length,
                                creditsRemaining: jobResult.results.credits_remaining || 0
                            }
                        }
                        return {
                            success: !1,
                            error: jobResult.error || "Processing failed",
                            errorType: "processing_error"
                        }
                    }
                    if (response.ok && result.success)
                        return completeOnboardingStep("use_ai_feature").catch((e => console.log("[ONBOARDING] Error:", e.message))),
                        {
                            success: !0,
                            imageUrl: result.image_url,
                            imageUrls: result.image_urls || [result.image_url],
                            creditsUsed: result.credits_used || 0,
                            creditsRemaining: result.credits_remaining || 0
                        };
                    {
                        const errorType = result.error || "unknown"
                          , errorMessage = result.message || "Failed to process image";
                        return console.error("[BACKGROUND] AI image processing failed:", {
                            status: response.status,
                            errorType: errorType,
                            errorMessage: errorMessage,
                            result: result
                        }),
                        {
                            success: !1,
                            error: errorMessage,
                            errorType: errorType,
                            statusCode: response.status,
                            requiredCredits: result.required_credits,
                            remainingCredits: result.remaining_credits
                        }
                    }
                } catch (error) {
                    return console.error("[BACKGROUND] Process AI image error:", error),
                    {
                        success: !1,
                        error: error.message || "Network error",
                        errorType: "network_error",
                        statusCode: 0
                    }
                }
            case "analyzeProductImages":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const photoUrls = request.photoUrls || []
                      , domain = request.domain || "";
                    if (0 === photoUrls.length)
                        return {
                            success: !1,
                            error: "No photos provided"
                        };
                    const storedUserForImages = await getFromStorage("user")
                      , userLocaleForImages = storedUserForImages?.locale || storedUserForImages?.iso_locale_code || null
                      , response = await fetch(`${serverUrl}/api/v1/analyze_product_images`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            photo_urls: photoUrls,
                            domain: domain,
                            user_locale: userLocaleForImages
                        })
                    })
                      , result = await response.json();
                    return response.ok && result.success ? (completeOnboardingStep("use_ai_feature").catch((e => console.log("[ONBOARDING] Error:", e.message))),
                    {
                        success: !0,
                        data: result.data
                    }) : {
                        success: !1,
                        error: result.message || result.error || "Failed to analyze images"
                    }
                } catch (error) {
                    return console.error("[BACKGROUND] Analyze images error:", error),
                    {
                        success: !1,
                        error: error.message || "Network error"
                    }
                }
            case "generateDescription":
                try {
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const storedUser = await getFromStorage("user")
                      , userLocale = storedUser?.locale || storedUser?.iso_locale_code || null
                      , response = await fetch(`${serverUrl}/api/v1/generate_description`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            product: request.productData,
                            additional_notes: request.additional_notes || "",
                            user_locale: request.user_locale || userLocale
                        })
                    })
                      , result = await response.json();
                    return response.ok && result.success ? (completeOnboardingStep("use_ai_feature").catch((e => console.log("[ONBOARDING] Error:", e.message))),
                    {
                        success: !0,
                        description: result.description
                    }) : {
                        success: !1,
                        error: result.message || result.error || "Failed to generate description"
                    }
                } catch (error) {
                    return console.error("[BACKGROUND] Generate description error:", error),
                    {
                        success: !1,
                        error: error.message || "Network error"
                    }
                }
            case "isLoggedIn":
                return await checkLoginSupabase();
            case "createPaymentLink":
                return await async function(priceId, planName) {
                    try {
                        const session = await checkLoginSupabase();
                        if (!session || !session.access_token)
                            return {
                                status: 401,
                                reason: "Not authenticated"
                            };
                        const response = await fetch(`${serverUrl}/api/v1/create_payment_link`, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer ${session.access_token}`
                            },
                            body: JSON.stringify({
                                price_id: priceId,
                                plan_name: planName,
                                success_url: "https://vindy.tech/payment-success",
                                cancel_url: "https://vindy.tech/pricing"
                            })
                        });
                        if (!response.ok) {
                            const errorData = await response.json().catch(( () => ({})));
                            return {
                                status: response.status,
                                reason: errorData.error || `Server error: ${response.status}`
                            }
                        }
                        return {
                            status: 200,
                            data: await response.json()
                        }
                    } catch (error) {
                        return console.error("âŒ Error creating payment link:", error),
                        {
                            status: 500,
                            reason: error.message
                        }
                    }
                }(request.priceId, request.planName);
            case "logout":
            case "logoutSupabase":
                return await async function() {
                    try {
                        return await client.auth.signOut(),
                        !0
                    } catch (error) {
                        return console.error("Error during logout:", error),
                        !1
                    }
                }(),
                await FeatureHandler.clearCache(),
                {
                    status: 200,
                    success: !0
                };
            case "handleEmailConfirmation":
                try {
                    const {data: data, error: error} = await client.auth.setSession({
                        access_token: request.session.access_token,
                        refresh_token: request.session.refresh_token
                    });
                    return error ? (console.error("Supabase setSession error:", error),
                    {
                        status: 400,
                        error: error.message
                    }) : data.session ? (await saveSession(data.session),
                    {
                        status: 200
                    }) : (console.error("No session returned from setSession"),
                    {
                        status: 400,
                        error: "No session returned"
                    })
                } catch (error) {
                    return console.error("Error handling email confirmation:", error),
                    {
                        status: 400,
                        error: error.message
                    }
                }
            case "loginSupabase":
                return await async function(email, password) {
                    try {
                        const {data: loginData, error: loginError} = await client.auth.signInWithPassword({
                            email: email,
                            password: password
                        });
                        return loginError ? {
                            status: loginError.status,
                            error: loginError.message,
                            code: loginError.code
                        } : loginData?.user?.email_confirmed_at ? {
                            status: 200,
                            data: loginData,
                            code: "SUCCESS"
                        } : (await client.auth.signOut(),
                        {
                            status: 400,
                            error: "Email non confermata. Per favore, verifica la tua email prima di accedere.",
                            code: "email_not_confirmed"
                        })
                    } catch (error) {
                        return {
                            status: 500,
                            error: "Error during login: " + error.message,
                            code: "UNEXPECTED_ERROR"
                        }
                    }
                }(request.email, request.password);
            case "checkLoginStatus":
                try {
                    const session = await getSession();
                    return session && session.access_token ? {
                        isLoggedIn: !0,
                        userId: session.user?.id
                    } : {
                        isLoggedIn: !1
                    }
                } catch (e) {
                    return {
                        isLoggedIn: !1
                    }
                }
            case "resendVerificationEmail":
                return await async function(email) {
                    try {
                        const {data: data, error: error} = await client.auth.resend({
                            type: "signup",
                            email: email
                        });
                        return error ? {
                            status: 400,
                            code: "RESEND_EMAIL_ERROR",
                            error: error.message
                        } : {
                            status: 200,
                            code: "RESEND_EMAIL_SUCCESS"
                        }
                    } catch (error) {
                        return {
                            status: 500,
                            code: "UNEXPECTED_ERROR",
                            error: error.message
                        }
                    }
                }(request.email);
            case "signupSupabase":
                return await async function(first_name, email, password) {
                    try {
                        const {data: data, error: error} = await client.auth.signUp({
                            email: email,
                            password: password,
                            options: {
                                data: {
                                    first_name: first_name
                                }
                            }
                        });
                        return error ? {
                            success: !1,
                            code: error.code,
                            message: error.message
                        } : data.user && data.user.identities && 0 !== data.user.identities.length ? {
                            success: !0,
                            data: data,
                            code: "SUCCESS",
                            message: "Account created! Please check your email to verify."
                        } : (console.warn("[SIGNUP] Email already exists:", email),
                        {
                            success: !1,
                            code: "user_already_exists",
                            message: "This email is already registered. Please login instead."
                        })
                    } catch (error) {
                        return console.error("[SIGNUP] Exception:", error),
                        {
                            success: !1,
                            code: "signup_exception",
                            message: error.message
                        }
                    }
                }(request.first_name, request.email, request.password);
            case "resetPasswordSupabase":
                return await async function(email) {
                    try {
                        const {data: data, error: error} = await client.auth.resetPasswordForEmail(email, {
                            redirectTo: "https://vindy.tech/password-reset-confirm"
                        });
                        return error ? (console.error("[RESET_PASSWORD] Error:", error),
                        {
                            success: !1,
                            code: error.code,
                            message: error.message
                        }) : {
                            success: !0,
                            code: "SUCCESS",
                            message: "Password reset email sent."
                        }
                    } catch (error) {
                        return console.error("[RESET_PASSWORD] Exception:", error),
                        {
                            success: !1,
                            code: "reset_exception",
                            message: error.message
                        }
                    }
                }(request.email);
            case "checkMembershipStripe":
                return await checkMembershipStripe();
            case "checkTrialStatus":
                return await async function(vintedUserId) {
                    const authResponse = await checkLoginSupabase();
                    if (!authResponse || "NO_SESSION" === authResponse.code)
                        return {
                            status: 403,
                            error: "User not authenticated",
                            code: "NO_SESSION"
                        };
                    if (!vintedUserId)
                        return {
                            status: 400,
                            error: "vinted_user_id is required",
                            code: "MISSING_VINTED_ID"
                        };
                    try {
                        const response = await fetch(serverUrl + "/api/v1/trial/check", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer ${authResponse.access_token}`
                            },
                            body: JSON.stringify({
                                vinted_user_id: vintedUserId
                            })
                        })
                          , data = await response.json();
                        return response.ok ? {
                            status: 200,
                            ...data
                        } : (console.error("[TRIAL] Error checking trial:", data),
                        {
                            status: response.status,
                            error: data.error || "Failed to check trial status",
                            code: data.code || "UNKNOWN_ERROR"
                        })
                    } catch (error) {
                        return console.error("[TRIAL] Exception:", error),
                        {
                            status: 500,
                            error: error.message,
                            code: "NETWORK_ERROR"
                        }
                    }
                }(request.vinted_user_id);
            case "startProTrial":
                return await async function(vintedUserId=null) {
                    const authResponse = await checkLoginSupabase();
                    if (!authResponse || "NO_SESSION" === authResponse.code)
                        return {
                            status: 403,
                            error: "User not authenticated",
                            code: "NO_SESSION"
                        };
                    try {
                        const body = {};
                        vintedUserId && (body.vinted_user_id = vintedUserId);
                        const response = await fetch(serverUrl + "/api/v1/trial/start", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer ${authResponse.access_token}`
                            },
                            body: JSON.stringify(body)
                        })
                          , data = await response.json();
                        return response.ok ? (await chrome.storage.local.remove("subscription"),
                        await FeatureHandler.clearCache(),
                        await checkMembershipStripe(!0),
                        {
                            status: 200,
                            success: !0,
                            ...data
                        }) : (console.error("[TRIAL] âŒ Failed to start trial:", data),
                        {
                            status: response.status,
                            success: !1,
                            error: data.error || "Failed to start trial",
                            code: data.code || "UNKNOWN_ERROR",
                            missing_steps: data.missing_steps || null
                        })
                    } catch (error) {
                        return console.error("[TRIAL] Exception:", error),
                        {
                            status: 500,
                            success: !1,
                            error: error.message,
                            code: "NETWORK_ERROR"
                        }
                    }
                }(request.vinted_user_id);
            case "completeOnboardingStep":
                return await completeOnboardingStep(request.step);
            case "getVintedUserStats":
                return await getVintedUserStats();
            case "getCurrentDomain":
                return {
                    status: 200,
                    domain: await getFromStorage("domain") || null
                };
            case "openVindyDashboard":
                try {
                    const browserEnvDash = await getBrowserEnvironment();
                    if (browserEnvDash && browserEnvDash.isMobile) {
                        let mobileProductsUrl = chrome.runtime.getURL("html/mobile-dashboard/index.html")
                          , params = [];
                        params.push("tab=products"),
                        request.productId && params.push(`focusProduct=${request.productId}`),
                        request.action && params.push(`action=${request.action}`),
                        mobileProductsUrl += "?" + params.join("&"),
                        await chrome.tabs.create({
                            url: mobileProductsUrl,
                            active: !0
                        })
                    } else {
                        const productsUrl = chrome.runtime.getURL("html/modern-light-menu/products.html");
                        let params = [];
                        request.productId && params.push(`focusProduct=${request.productId}`),
                        request.action && params.push(`action=${request.action}`);
                        const urlWithParam = params.length > 0 ? `${productsUrl}?${params.join("&")}` : productsUrl;
                        await chrome.tabs.create({
                            url: urlWithParam,
                            active: !0
                        })
                    }
                } catch (error) {
                    console.error("[openVindyDashboard] Error:", error);
                    const productsUrl = chrome.runtime.getURL("html/modern-light-menu/products.html");
                    await chrome.tabs.create({
                        url: productsUrl,
                        active: !0
                    })
                }
                return {
                    status: 200,
                    success: !0
                };
            case "openVindyLikes":
                try {
                    const browserEnvLikes = await getBrowserEnvironment();
                    if (browserEnvLikes && browserEnvLikes.isMobile) {
                        let mobileLikesUrl = chrome.runtime.getURL("html/mobile-dashboard/index.html");
                        mobileLikesUrl += request.itemId ? `?tab=likes&focusLike=${request.itemId}` : "?tab=likes",
                        await chrome.tabs.create({
                            url: mobileLikesUrl,
                            active: !0
                        })
                    } else {
                        const dashboardUrl = chrome.runtime.getURL("html/modern-light-menu/dashboard.html")
                          , dashUrlWithParam = request.itemId ? `${dashboardUrl}?focusLike=${request.itemId}` : `${dashboardUrl}?scrollTo=recentLikes`;
                        await chrome.tabs.create({
                            url: dashUrlWithParam,
                            active: !0
                        })
                    }
                } catch (error) {
                    console.error("[openVindyLikes] Error:", error);
                    const dashboardUrl = chrome.runtime.getURL("html/modern-light-menu/dashboard.html");
                    await chrome.tabs.create({
                        url: dashboardUrl,
                        active: !0
                    })
                }
                return {
                    status: 200,
                    success: !0
                };
            case "openVintedChat":
                try {
                    const chatDomain = request.domain || await getFromStorage("domain")
                      , chatUserId = request.userId
                      , chatItemId = request.itemId;
                    if (chatDomain && chatUserId && chatItemId) {
                        const chatUrl = `https://${chatDomain}/inbox/want_it?receiver_id=${chatUserId}&item_id=${chatItemId}`;
                        await chrome.tabs.create({
                            url: chatUrl,
                            active: !0
                        })
                    } else if (chatDomain && chatUserId) {
                        const chatUrl = `https://${chatDomain}/inbox?offering_id=${chatUserId}`;
                        await chrome.tabs.create({
                            url: chatUrl,
                            active: !0
                        })
                    } else {
                        const dashboardUrl = chrome.runtime.getURL("html/modern-light-menu/dashboard.html");
                        await chrome.tabs.create({
                            url: dashboardUrl,
                            active: !0
                        })
                    }
                } catch (error) {
                    console.error("[openVintedChat] Error:", error);
                    const dashboardUrl = chrome.runtime.getURL("html/modern-light-menu/dashboard.html");
                    await chrome.tabs.create({
                        url: dashboardUrl,
                        active: !0
                    })
                }
                return {
                    status: 200,
                    success: !0
                };
            case "openVindyOffers":
                try {
                    const browserEnvOffers = await getBrowserEnvironment();
                    if (browserEnvOffers && browserEnvOffers.isMobile) {
                        const mobileOffersUrl = chrome.runtime.getURL("html/mobile-dashboard/index.html") + "?tab=offers";
                        await chrome.tabs.create({
                            url: mobileOffersUrl,
                            active: !0
                        })
                    } else {
                        const offersUrlWithParam = `${chrome.runtime.getURL("html/modern-light-menu/dashboard.html")}?scrollTo=offers`;
                        await chrome.tabs.create({
                            url: offersUrlWithParam,
                            active: !0
                        })
                    }
                } catch (error) {
                    console.error("[openVindyOffers] Error:", error);
                    const offersUrl = chrome.runtime.getURL("html/modern-light-menu/dashboard.html");
                    await chrome.tabs.create({
                        url: offersUrl,
                        active: !0
                    })
                }
                return {
                    status: 200,
                    success: !0
                };
            case "load_notifications":
                return fetch_notifications_status || (fetch_notifications_status = !0,
                await fetch_notifications(),
                fetch_notifications_status = !1),
                {
                    status: 200
                };
            case "load_offers":
                fetch_offers_status || (fetch_offers_status = !0,
                await async function() {
                    try {
                        const domain = await getFromStorage("domain")
                          , user = await getFromStorage("user");
                        if (!domain || !user)
                            return void console.error("[FETCH_OFFERS] Domain or user not found");
                        const MAX_PAGES = 5
                          , conversation_ids = [];
                        for (let page = 1; page <= MAX_PAGES; page++) {
                            const inbox_url = `https://${domain}/api/v2/inbox?page=${page}&per_page=50`
                              , resp = await fetch(inbox_url, {
                                method: "GET",
                                headers: {
                                    accept: "application/json"
                                }
                            });
                            if (!resp.ok) {
                                console.error(`[FETCH_OFFERS] Failed to fetch inbox page ${page}:`, resp.status);
                                break
                            }
                            {
                                const data = await resp.json()
                                  , conversations = data.conversations || [];
                                if (0 === conversations.length)
                                    break;
                                let filteredCount = 0;
                                if (conversations.forEach((conv => {
                                    conv.item_count && 0 !== conv.item_count && (conversation_ids.push(conv.id),
                                    filteredCount++)
                                }
                                )),
                                data.pagination && page >= data.pagination.total_pages)
                                    break
                            }
                        }
                        const fetchPromises = conversation_ids.map((async conv_id => {
                            try {
                                const conv_url = `https://${domain}/api/v2/conversations/${conv_id}`
                                  , resp = await fetch(conv_url, {
                                    method: "GET",
                                    headers: {
                                        accept: "application/json"
                                    }
                                });
                                if (resp.ok)
                                    return function(data, domain, current_user_id) {
                                        const offers = []
                                          , conversation = data.conversation || {}
                                          , messages = conversation.messages || []
                                          , transaction = conversation.transaction || {}
                                          , opposite_user = conversation.opposite_user || {};
                                        return "buyer" === transaction.current_user_side ? [] : (messages.forEach(( (message, index) => {
                                            if ("offer_request_message" === message.entity_type) {
                                                const offer_entity = message.entity || {};
                                                if (offer_entity.user_id === current_user_id)
                                                    return;
                                                const PENDING_STATUS = 10
                                                  , statusCode = offer_entity.status;
                                                if (statusCode === PENDING_STATUS) {
                                                    const offerPrice = offer_entity.price
                                                      , originalPrice = offer_entity.original_price
                                                      , resolvedOfferAmount = "object" == typeof offerPrice && offerPrice ? offerPrice.amount : offerPrice
                                                      , resolvedOfferCurrency = "object" == typeof offerPrice && offerPrice ? offerPrice.currency_code : offer_entity.currency || "EUR"
                                                      , resolvedOriginalPrice = "object" == typeof originalPrice && originalPrice ? originalPrice.amount : originalPrice
                                                      , resolvedOriginalCurrency = "object" == typeof originalPrice && originalPrice ? originalPrice.currency_code : resolvedOfferCurrency
                                                      , offer_data = {
                                                        offer_amount: resolvedOfferAmount,
                                                        offer_currency: resolvedOfferCurrency,
                                                        offer_status: offer_entity.status_title || "Pending",
                                                        offer_status_code: statusCode,
                                                        offer_id: offer_entity.offer_request_id,
                                                        transaction_id: offer_entity.transaction_id,
                                                        conversation_id: conversation.id,
                                                        buyer_name: opposite_user.login || "Unknown",
                                                        buyer_id: offer_entity.user_id || opposite_user.id,
                                                        buyer_photo: opposite_user.photo?.url,
                                                        product_title: transaction.item_title || "Product",
                                                        product_id: transaction.item_id,
                                                        product_url: transaction.item_url,
                                                        product_photo: transaction.item_photo?.url,
                                                        original_price: resolvedOriginalPrice,
                                                        original_currency: resolvedOriginalCurrency,
                                                        created_at: message.created_at_ts || message.created_at,
                                                        updated_at: message.updated_at_ts || message.created_at_ts || message.created_at
                                                    };
                                                    offers.push(offer_data)
                                                }
                                            }
                                        }
                                        )),
                                        offers)
                                    }(await resp.json(), 0, user.id)
                            } catch (error) {}
                            return []
                        }
                        ))
                          , all_offers = (await Promise.all(fetchPromises)).flat().filter((offer => null !== offer));
                        all_offers.forEach(( (offer, index) => {}
                        )),
                        await chrome.storage.local.set({
                            pending_offers: all_offers,
                            offers_last_fetch: (new Date).toISOString()
                        })
                    } catch (error) {
                        console.error("[FETCH_OFFERS] âŒ Error during fetch:", error)
                    } finally {
                        fetch_offers_status = !1
                    }
                }(),
                fetch_offers_status = !1);
                try {
                    const pendingOffers = await getFromStorage("pending_offers");
                    return {
                        success: !0,
                        status: 200,
                        offers: pendingOffers || [],
                        lastFetch: await getFromStorage("offers_last_fetch")
                    }
                } catch (error) {
                    return console.error("[load_offers] Error getting offers:", error),
                    {
                        success: !1,
                        status: 500,
                        offers: [],
                        error: error.message
                    }
                }
            case "openOptionsPage":
                return chrome.runtime.openOptionsPage(( () => {
                    chrome.runtime.lastError ? console.error("Error opening options page:", chrome.runtime.lastError) : chrome.tabs.reload(sender.tab.id, ( () => {
                        chrome.runtime.lastError && console.error("Error reloading tab:", chrome.runtime.lastError)
                    }
                    ))
                }
                )),
                await chrome.tabs.remove(sender.tab.id),
                {
                    status: 200
                };
            case "isLoggedInVinted":
                let {domain: domain} = await chrome.storage.local.get(["domain"]);
                if (domain && !isValidVintedDomain(domain) && (console.warn(`[isLoggedInVinted] âš ï¸ Invalid domain in storage: ${domain}, clearing and re-detecting...`),
                await chrome.storage.local.remove(["domain"]),
                domain = null),
                !domain && (domain = await detectVintedDomainFromCookies(),
                !domain))
                    return {
                        success: !1,
                        message: "domain_not_set"
                    };
                const vintedResponse = await checkLogin(domain);
                return vintedResponse.success ? {
                    success: !0,
                    domain: domain
                } : {
                    success: !1,
                    message: vintedResponse.message
                };
            case "detectVintedDomain":
                try {
                    const detectedDomain = await detectVintedDomainFromCookies();
                    return detectedDomain ? {
                        success: !0,
                        domain: detectedDomain
                    } : {
                        success: !1,
                        message: "no_vinted_cookie_found"
                    }
                } catch (error) {
                    return console.error("[detectVintedDomain] Error:", error),
                    {
                        success: !1,
                        message: error.message || "detection_error"
                    }
                }
            case "can":
                return !!(await chrome.storage.local.get(["domain"])).domain;
            case "startStopFollowAutomation":
                return (follow_automation_status = !follow_automation_status) && await async function() {
                    let canUse = await FeatureHandler.canUseFeature("follow");
                    if (!canUse)
                        return await updateActivity("Plan limit reached, can't use follow feature now", "warning"),
                        follow_automation_status = !1,
                        void updateStatus();
                    await updateActivity("Follow automation started", "success");
                    let usersToFollow = []
                      , idListToFetch = [];
                    for (; ; ) {
                        if (!follow_automation_status)
                            return void updateActivity("Follow automation stopped", "warning");
                        if (canUse = await FeatureHandler.canUseFeature("follow"),
                        !canUse)
                            return await updateActivity("Feature limit reached during execution", "warning"),
                            follow_automation_status = !1,
                            void updateStatus();
                        if (0 != usersToFollow.length) {
                            let info = await getFromStorage("followunfollowAutomation");
                            info || (info = {
                                feedbackCount: 3,
                                itemsBought: 20,
                                lastLogin: 7,
                                followLimit: 1e4,
                                followPerFlow: 1,
                                unfollowPerFlow: 1,
                                messages: [],
                                followed: {
                                    day: null,
                                    number: 0
                                },
                                unfollowed: {
                                    day: null,
                                    number: 0
                                },
                                idsToFollow: []
                            },
                            await chrome.storage.local.set({
                                followunfollowAutomation: info
                            }));
                            const batchSize = getRandomSleepTime(1, 1)
                              , usersBatch = usersToFollow.slice(0, batchSize)
                              , followResponse = await follow_unfollow(usersBatch);
                            if (0 == followResponse.code) {
                                if (!(await FeatureHandler.incrementFeature("follow")).success)
                                    return await updateActivity("Feature limit reached", "warning"),
                                    follow_automation_status = !1,
                                    void updateStatus();
                                let result = await getFromStorage("following");
                                result && Array.isArray(result) || (result = []),
                                await chrome.storage.local.set({
                                    following: Array.from(new Set(result.concat(usersBatch)))
                                }),
                                usersToFollow = usersToFollow.filter((user => !usersBatch.includes(user))),
                                updateActivity(`Followed ${usersBatch.length} users.`),
                                await sleep(getRandomSleepTime(2e3, 4e3))
                            } else {
                                if (117 == followResponse.code)
                                    return await updateActivity("Vinted Follow Limit Reached! Start unfollowing flow to continue following new users."),
                                    follow_automation_status = !1,
                                    void updateStatus();
                                if (150 == followResponse.code)
                                    usersToFollow = usersToFollow.filter((user => !usersBatch.includes(user))),
                                    await updateActivity("Follow forbidden by geo location. Skipping user."),
                                    await sleep(getRandomSleepTime(1e3, 3e3));
                                else {
                                    if (100 != followResponse.code)
                                        return updateActivity(followResponse.message),
                                        follow_automation_status = !1,
                                        void updateStatus();
                                    await updateActivity("Invalid authentication token. Waiting 10 seconds."),
                                    await sleep(1e4)
                                }
                            }
                        } else {
                            if (0 === idListToFetch.length) {
                                await updateActivity("Searching for users from similar items...", "info");
                                const similarResult = await getSimilarItemsUsers();
                                if (!similarResult.success)
                                    return await updateActivity(similarResult.message || "Could not find users to follow", "error"),
                                    follow_automation_status = !1,
                                    void updateStatus();
                                if (0 === similarResult.users.length)
                                    return await updateActivity("No users found from similar items. Try uploading more products.", "warning"),
                                    follow_automation_status = !1,
                                    void updateStatus();
                                await updateActivity(`Found ${similarResult.users.length} users from similar items (${similarResult.searchType})`, "success"),
                                idListToFetch.push(...similarResult.users)
                            }
                            const feedbacks = await getFeedback(idListToFetch.shift());
                            if (feedbacks) {
                                for (let i = 0; i < feedbacks.user_feedbacks.length; i++)
                                    null != feedbacks.user_feedbacks[i].user || null != feedbacks.user_feedbacks[i].user ? idListToFetch.push(feedbacks.user_feedbacks[i].user.id) : feedbacks.user_feedbacks.splice(i, 1);
                                updateActivity("Filtering users to follow...");
                                const usersFiltered = await processFeedbacks(feedbacks);
                                usersToFollow.push(...usersFiltered),
                                await updateActivity("Found " + usersFiltered.length + " users to follow...")
                            }
                        }
                    }
                }(),
                {
                    status: follow_automation_status
                };
            case "startStopUnfollowAutomation":
                return (unfollow_automation_status = !unfollow_automation_status) && await async function() {
                    let canUse = await FeatureHandler.canUseFeature("unfollow");
                    if (!canUse)
                        return await updateActivity("Plan limit reached, can't use unfollow feature now", "warning"),
                        unfollow_automation_status = !1,
                        void updateStatus();
                    await updateActivity("Unfollow automation started", "success");
                    let usersToUnfollow = [];
                    for (; ; ) {
                        if (!unfollow_automation_status)
                            return await updateActivity("Unfollow automation stopped", "warning"),
                            unfollow_automation_status = !1,
                            void updateStatus();
                        if (canUse = await FeatureHandler.canUseFeature("unfollow"),
                        !canUse)
                            return await updateActivity("Feature limit reached during execution", "warning"),
                            unfollow_automation_status = !1,
                            void updateStatus();
                        if (0 === usersToUnfollow.length) {
                            await updateActivity("Fetching page 1 of following users...");
                            const user = await getFromStorage("user")
                              , followingPage = await get_following(user.id);
                            if (!followingPage || 0 === followingPage.users.length)
                                return await updateActivity("No more users to unfollow"),
                                unfollow_automation_status = !1,
                                void updateStatus();
                            for (let i = 0; i < followingPage.users.length; i++) {
                                const user = followingPage.users[i];
                                usersToUnfollow.push(user.id)
                            }
                        }
                        let info = await getFromStorage("followunfollowAutomation");
                        info || (info = {
                            feedbackCount: 3,
                            itemsBought: 20,
                            lastLogin: 7,
                            followLimit: 1e4,
                            followPerFlow: 1,
                            unfollowPerFlow: 1,
                            messages: [],
                            followed: {
                                day: null,
                                number: 0
                            },
                            unfollowed: {
                                day: null,
                                number: 0
                            },
                            idsToFollow: []
                        },
                        await chrome.storage.local.set({
                            followunfollowAutomation: info
                        }));
                        const batchSize = getRandomSleepTime(1, 1)
                          , usersBatch = usersToUnfollow.slice(0, batchSize)
                          , unfollowResponse = await follow_unfollow(usersBatch);
                        if (0 == unfollowResponse.code) {
                            if (!(await FeatureHandler.incrementFeature("unfollow", usersBatch.length)).success)
                                return await updateActivity("Feature limit reached", "warning"),
                                unfollow_automation_status = !1,
                                void updateStatus();
                            await updateActivity(`Unfollowed ${usersBatch.length} users.`),
                            usersToUnfollow = usersToUnfollow.filter((user => !usersBatch.includes(user))),
                            updateStatus(),
                            await sleep(getRandomSleepTime(1e3, 4e3))
                        } else
                            await updateActivity(unfollowResponse.message),
                            updateStatus(),
                            await sleep(getRandomSleepTime(1e3, 3e3))
                    }
                }(),
                {
                    status: unfollow_automation_status
                };
            case "fetch_orders":
                const {domain: ordersDomain} = await chrome.storage.local.get(["domain"]);
                if (!ordersDomain)
                    return {
                        success: !1,
                        status: 0,
                        message: "Error fetching data: domain not found"
                    };
                const ordersResponse = await async function(domain) {
                    try {
                        let allOrders = []
                          , page = 1
                          , hasMore = !0;
                        for (; hasMore; ) {
                            const response = await fetch(`https://${domain}/api/v2/my_orders?type=sold&status=all&per_page=100&page=${page}`, {
                                headers: {
                                    accept: "application/json, text/plain, */*"
                                }
                            });
                            if (!response.ok) {
                                console.error("[FETCH_ORDERS] Error fetching page", page, response.status);
                                break
                            }
                            const orders = (await response.json()).my_orders || [];
                            allOrders = allOrders.concat(orders),
                            orders.length < 100 ? hasMore = !1 : page++
                        }
                        const convIds = [...new Set(allOrders.map((o => o.conversation_id)).filter(Boolean))]
                          , buyerMap = {}
                          , BATCH_SIZE = 10;
                        for (let i = 0; i < convIds.length; i += BATCH_SIZE) {
                            const promises = convIds.slice(i, i + BATCH_SIZE).map((async convId => {
                                try {
                                    const resp = await fetch(`https://${domain}/api/v2/conversations/${convId}`, {
                                        method: "GET",
                                        headers: {
                                            accept: "application/json"
                                        }
                                    });
                                    if (resp.ok) {
                                        const oppositeUser = ((await resp.json()).conversation || {}).opposite_user || {};
                                        oppositeUser.id && (buyerMap[convId] = {
                                            buyer_id: oppositeUser.id,
                                            buyer_login: oppositeUser.login || "Unknown",
                                            buyer_photo: oppositeUser.photo?.url || null
                                        })
                                    }
                                } catch (e) {
                                    console.warn(`[FETCH_ORDERS] Failed to fetch conversation ${convId}:`, e.message)
                                }
                            }
                            ));
                            await Promise.all(promises)
                        }
                        const enrichedOrders = allOrders.map((order => {
                            const buyerInfo = buyerMap[order.conversation_id];
                            return buyerInfo ? {
                                ...order,
                                ...buyerInfo
                            } : order
                        }
                        ));
                        await chrome.storage.local.set({
                            orders: enrichedOrders
                        });
                        try {
                            const {user: vintedUser} = await chrome.storage.local.get(["user"])
                              , vintedId = vintedUser?.id;
                            if (vintedId && enrichedOrders.length > 0) {
                                const sessione = await checkLoginSupabase();
                                if (sessione) {
                                    const ordersPayload = enrichedOrders.filter((o => o.transaction_id)).map((o => ({
                                        transaction_id: o.transaction_id,
                                        price: o.price,
                                        date: o.date || null
                                    })))
                                      , syncResp = await fetch(serverUrl + "/api/v1/orders/sync", {
                                        method: "POST",
                                        headers: {
                                            "Content-Type": "application/json",
                                            Authorization: `Bearer ${sessione.access_token}`
                                        },
                                        body: JSON.stringify({
                                            vinted_user_id: String(vintedId),
                                            orders: ordersPayload
                                        })
                                    });
                                    if (syncResp.ok) {
                                        const syncData = await syncResp.json();
                                        console.log(`[AUTO-SUCCESS] Synced: ${syncData.new_orders} new, ${syncData.notified} notified`)
                                    } else
                                        console.warn(`[AUTO-SUCCESS] Sync failed: ${syncResp.status}`)
                                }
                            }
                        } catch (syncErr) {
                            console.warn("[AUTO-SUCCESS] Error syncing orders:", syncErr.message)
                        }
                        return {
                            success: !0
                        }
                    } catch (error) {
                        return console.error("[FETCH_ORDERS] Error:", error),
                        {
                            success: !1,
                            status: 0,
                            message: "Error fetching data"
                        }
                    }
                }(ordersDomain);
                return {
                    ...ordersResponse,
                    message: "fetch_orders"
                };
            case "fetch_userinfo":
                const {domain: userDomain} = await chrome.storage.local.get(["domain"]);
                if (!userDomain)
                    return {
                        success: !1,
                        status: 0,
                        message: "Error fetching data: domain not found"
                    };
                return {
                    ...await fetch_userinfo(userDomain),
                    message: "fetch_userinfo"
                };
            case "fetch_user_stats":
                const {domain: statsDomain} = await chrome.storage.local.get(["domain"]);
                if (!statsDomain)
                    return {
                        success: !1,
                        status: 0,
                        message: "Error fetching data: domain not found"
                    };
                const statsResponse = await async function(domain) {
                    try {
                        const response = await fetch(`https://${domain}/api/v2/wallet/invoices/current`, {
                            headers: {
                                accept: "application/json, text/plain, */*"
                            }
                        });
                        if (response.ok) {
                            const data = await response.json();
                            return await chrome.storage.local.set({
                                user_balance: data
                            }),
                            {
                                success: !0
                            }
                        }
                        return console.error("[ERROR] Failed to fetch wallet data:", response.status, response.statusText),
                        {
                            success: !1,
                            status: response.status,
                            message: "Error fetching data"
                        }
                    } catch (error) {
                        return console.error("[ERROR] Exception in fetch_user_stats:", error),
                        {
                            success: !1,
                            status: 0,
                            message: "Error fetching data"
                        }
                    }
                }(statsDomain);
                return {
                    ...statsResponse,
                    message: "fetch_user_stats"
                };
            case "fetch_personal_items":
                const {domain: itemsDomain} = await chrome.storage.local.get(["domain"]);
                if (!itemsDomain)
                    return {
                        success: !1,
                        status: 0,
                        message: "Error fetching data: domain not found"
                    };
                const itemsResponse = await async function(domain, tabId) {
                    try {
                        const user = await getFromStorage("user");
                        if (!user?.id)
                            throw new Error("User not found in storage. Please reload the page or log in again.");
                        await chrome.storage.local.set({
                            items: []
                        });
                        let allItems = []
                          , page = 1
                          , totalPages = 1;
                        for (; page <= totalPages; ) {
                            const response = await fetch(`https://${domain}/api/v2/wardrobe/${user.id}/items?page=${page}&per_page=100`, {
                                headers: {
                                    accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                                }
                            });
                            if (!response.ok)
                                return console.error("[FETCH_ITEMS] Failed to fetch page:", response.status, response.statusText),
                                {
                                    success: !1,
                                    status: response.status,
                                    message: "Error fetching data"
                                };
                            {
                                const data = await response.json()
                                  , pageItems = data.items || [];
                                allItems = allItems.concat(pageItems),
                                await chrome.storage.local.set({
                                    items: allItems
                                }),
                                chrome.tabs.sendMessage(tabId, {
                                    type: "itemsPageLoaded",
                                    data: {
                                        currentPage: page,
                                        totalPages: data.pagination.total_pages,
                                        newItems: pageItems,
                                        totalItems: allItems.length
                                    }
                                }).catch(( () => {}
                                )),
                                totalPages = data.pagination.total_pages,
                                page++,
                                page <= totalPages && await sleep(200)
                            }
                        }
                        chrome.tabs.sendMessage(tabId, {
                            type: "itemsFetchCompleted",
                            data: {
                                totalItems: allItems.length,
                                totalPages: totalPages
                            }
                        }).catch(( () => {}
                        ));
                        try {
                            const cachedTrial = await chrome.storage.local.get(["activeTrialExpiresAt"]);
                            if (cachedTrial.activeTrialExpiresAt && new Date(cachedTrial.activeTrialExpiresAt) > new Date) {
                                const viewsItems = allItems.filter((item => item.id && "number" == typeof item.view_count)).map((item => ({
                                    item_id: String(item.id),
                                    view_count: item.view_count
                                })));
                                if (viewsItems.length > 0) {
                                    const session = await getSession();
                                    session?.access_token && fetch(`${serverUrl}/api/v1/trial/views-snapshot`, {
                                        method: "POST",
                                        headers: {
                                            Authorization: `Bearer ${session.access_token}`,
                                            "Content-Type": "application/json"
                                        },
                                        body: JSON.stringify({
                                            items: viewsItems
                                        })
                                    }).catch((err => console.log("[TRIAL_VIEWS] Snapshot error:", err.message)))
                                }
                            }
                        } catch (e) {
                            console.log("[TRIAL_VIEWS] Error:", e.message)
                        }
                        return {
                            success: !0,
                            status: 200,
                            message: "Items fetched successfully"
                        }
                    } catch (error) {
                        return console.error("[FETCH_ITEMS] âŒ Error:", error),
                        {
                            success: !1,
                            status: 0,
                            message: "Error fetching data"
                        }
                    }
                }(itemsDomain, sender.tab.id);
                return {
                    ...itemsResponse,
                    message: "fetch_personal_items"
                };
            case "followAutomationStatus":
                return {
                    active: follow_automation_status
                };
            case "unfollowAutomationStatus":
                return {
                    active: unfollow_automation_status
                };
            case "fetchRecentLikes":
                return {
                    status: 200,
                    likes: await fetchRecentLikes()
                };
            case "getLikesForItem":
                return {
                    status: 200,
                    likes: await async function(itemId) {
                        try {
                            const notifications = await getFromStorage("notifications");
                            if (!notifications || "object" != typeof notifications)
                                return [];
                            const itemNotifications = notifications[itemId];
                            return itemNotifications && Array.isArray(itemNotifications) ? itemNotifications.filter((n => "favorite" === n.entity_type)) : []
                        } catch (error) {
                            return console.error(`Error fetching likes for item ${itemId}:`, error),
                            []
                        }
                    }(request.itemId)
                };
            case "forceFetchNotifications":
                return fetch_notifications_status || (fetch_notifications_status = !0,
                await fetch_notifications(),
                fetch_notifications_status = !1),
                {
                    status: 200
                };
            case "accept_offer":
                try {
                    const acceptResult = await async function(data) {
                        try {
                            const {offer_id: offer_id, transaction_id: transaction_id, conversation_id: conversation_id, domain: domain} = data;
                            if (!offer_id || !transaction_id || !domain)
                                throw new Error("Missing required parameters: offer_id, transaction_id, or domain");
                            if (x_csrf || await updateCSRF(),
                            !x_csrf)
                                throw new Error("Failed to get CSRF token");
                            const url = `https://${domain}/api/v2/transactions/${transaction_id}/offer_requests/${offer_id}/accept`
                              , response = await fetch(url, {
                                method: "PUT",
                                headers: {
                                    "x-csrf-token": x_csrf,
                                    accept: "application/json",
                                    "content-type": "application/json",
                                    "X-Requested-With": "XMLHttpRequest"
                                },
                                credentials: "include"
                            });
                            if (!response.ok) {
                                const errorText = await response.text();
                                throw console.error("[ACCEPT_OFFER] API error:", errorText),
                                new Error(`Failed to accept offer: ${response.status} ${response.statusText}`)
                            }
                            const result = await response.json()
                              , storage = await chrome.storage.local.get(["pending_offers"]);
                            if (storage.pending_offers) {
                                const updatedOffers = storage.pending_offers.filter((o => o.offer_id !== offer_id));
                                await chrome.storage.local.set({
                                    pending_offers: updatedOffers
                                })
                            }
                            return console.log("[ACCEPT_OFFER] âœ… Offer accepted successfully"),
                            {
                                success: !0,
                                message: "Offer accepted successfully",
                                data: result
                            }
                        } catch (error) {
                            return console.error("[ACCEPT_OFFER] âŒ Error:", error),
                            {
                                success: !1,
                                message: error.message || "Failed to accept offer"
                            }
                        }
                    }(request.data);
                    return acceptResult
                } catch (error) {
                    return console.error("[ERROR] Error accepting offer:", error),
                    {
                        success: !1,
                        message: error.message || "Failed to accept offer"
                    }
                }
            case "decline_offer":
                try {
                    const declineResult = await async function(data) {
                        try {
                            const {offer_id: offer_id, transaction_id: transaction_id, conversation_id: conversation_id, domain: domain} = data;
                            if (!offer_id || !transaction_id || !domain)
                                throw new Error("Missing required parameters: offer_id, transaction_id, or domain");
                            if (x_csrf || await updateCSRF(),
                            !x_csrf)
                                throw new Error("Failed to get CSRF token");
                            const url = `https://${domain}/api/v2/transactions/${transaction_id}/offer_requests/${offer_id}/reject`
                              , response = await fetch(url, {
                                method: "PUT",
                                headers: {
                                    "x-csrf-token": x_csrf,
                                    accept: "application/json",
                                    "content-type": "application/json",
                                    "X-Requested-With": "XMLHttpRequest"
                                },
                                body: "{}",
                                credentials: "include"
                            });
                            if (!response.ok) {
                                const errorText = await response.text();
                                throw console.error("[DECLINE_OFFER] API error:", errorText),
                                new Error(`Failed to decline offer: ${response.status} ${response.statusText}`)
                            }
                            const result = await response.json()
                              , storage = await chrome.storage.local.get(["pending_offers"]);
                            if (storage.pending_offers) {
                                const updatedOffers = storage.pending_offers.filter((o => o.offer_id !== offer_id));
                                await chrome.storage.local.set({
                                    pending_offers: updatedOffers
                                })
                            }
                            return console.log("[DECLINE_OFFER] âœ… Offer declined successfully"),
                            {
                                success: !0,
                                message: "Offer declined successfully",
                                data: result
                            }
                        } catch (error) {
                            return console.error("[DECLINE_OFFER] âŒ Error:", error),
                            {
                                success: !1,
                                message: error.message || "Failed to decline offer"
                            }
                        }
                    }(request.data);
                    return declineResult
                } catch (error) {
                    return console.error("[ERROR] Error declining offer:", error),
                    {
                        success: !1,
                        message: error.message || "Failed to decline offer"
                    }
                }
            case "counter_offer":
                try {
                    const counterResult = await async function(data) {
                        try {
                            const {offer_id: offer_id, transaction_id: transaction_id, conversation_id: conversation_id, new_price: new_price, currency: currency, domain: domain} = data;
                            if (!transaction_id || !domain)
                                throw new Error("Missing required parameters: transaction_id or domain");
                            if (!new_price || isNaN(new_price) || new_price <= 0)
                                throw new Error("Invalid price");
                            if (x_csrf || await updateCSRF(),
                            !x_csrf)
                                throw new Error("Failed to get CSRF token");
                            const url = `https://${domain}/api/v2/transactions/${transaction_id}/offers`
                              , payload = {
                                offer: {
                                    price: parseFloat(new_price).toFixed(2),
                                    currency: currency || "EUR"
                                }
                            }
                              , response = await fetch(url, {
                                method: "POST",
                                headers: {
                                    "x-csrf-token": x_csrf,
                                    accept: "application/json",
                                    "content-type": "application/json",
                                    "X-Requested-With": "XMLHttpRequest"
                                },
                                body: JSON.stringify(payload),
                                credentials: "include"
                            });
                            if (!response.ok) {
                                const errorText = await response.text();
                                throw console.error("[COUNTER_OFFER] API error:", errorText),
                                new Error(`Failed to send counter offer: ${response.status} ${response.statusText}`)
                            }
                            const result = await response.json()
                              , storage = await chrome.storage.local.get(["pending_offers"]);
                            if (storage.pending_offers) {
                                const updatedOffers = storage.pending_offers.filter((o => o.offer_id !== offer_id));
                                await chrome.storage.local.set({
                                    pending_offers: updatedOffers
                                })
                            }
                            return console.log("[COUNTER_OFFER] âœ… Counter offer sent successfully"),
                            {
                                success: !0,
                                message: "Counter offer sent successfully",
                                data: result
                            }
                        } catch (error) {
                            return console.error("[COUNTER_OFFER] âŒ Error:", error),
                            {
                                success: !1,
                                message: error.message || "Failed to send counter offer"
                            }
                        }
                    }(request.data);
                    return counterResult
                } catch (error) {
                    return console.error("[ERROR] Error sending counter offer:", error),
                    {
                        success: !1,
                        message: error.message || "Failed to send counter offer"
                    }
                }
            case "deleteItem":
                try {
                    return await deleteVintedItem(request.itemId)
                } catch (error) {
                    return console.error("[ERROR] Error deleting item:", error),
                    {
                        success: !1,
                        message: error.message || "Failed to delete item"
                    }
                }
            case "fetchImageBlob":
                try {
                    const imageUrl = request.url;
                    if (!imageUrl)
                        return {
                            success: !1,
                            error: "No URL provided"
                        };
                    const imageResponse = await fetch(imageUrl, {
                        method: "GET",
                        mode: "cors",
                        credentials: "omit"
                    });
                    if (!imageResponse.ok)
                        return console.error("[FETCH_IMAGE] Failed to fetch image:", imageResponse.status),
                        {
                            success: !1,
                            error: `HTTP ${imageResponse.status}`
                        };
                    const imageBlob = await imageResponse.blob()
                      , reader = new FileReader;
                    return {
                        success: !0,
                        data: await new Promise(( (resolve, reject) => {
                            reader.onloadend = () => resolve(reader.result),
                            reader.onerror = reject,
                            reader.readAsDataURL(imageBlob)
                        }
                        )),
                        size: imageBlob.size,
                        type: imageBlob.type
                    }
                } catch (error) {
                    return console.error("[FETCH_IMAGE] Error downloading image:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "setRepostUploadLock":
                return active = !!request.active,
                repostUploadLock = active,
                repostUploadLockTimeout && clearTimeout(repostUploadLockTimeout),
                repostUploadLockTimeout = active ? setTimeout(( () => {
                    repostUploadLock = !1
                }
                ), 12e4) : null,
                {
                    success: !0
                };
            case "processImageForRepostServer":
                try {
                    const {imageUrl: imageUrl, imageBase64: imageBase64} = request;
                    if (!imageUrl && !imageBase64)
                        return {
                            success: !1,
                            error: "No image data provided"
                        };
                    const sessione = await getSession();
                    if (!sessione || !sessione.access_token)
                        return {
                            success: !1,
                            error: "not_logged_in",
                            fallback: !0
                        };
                    const response = await fetch(`${serverUrl}/api/v1/process_image_repost`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${sessione.access_token}`
                        },
                        body: JSON.stringify({
                            image_url: imageUrl,
                            image_base64: imageBase64
                        })
                    })
                      , result = await response.json();
                    return response.ok && result.success ? {
                        success: !0,
                        data: result.image_base64,
                        originalHash: result.original_hash,
                        newHash: result.new_hash,
                        size: result.size
                    } : (console.error("[PROCESS_IMAGE_SERVER] Server processing failed:", result),
                    {
                        success: !1,
                        error: result.message || result.error || "Server processing failed",
                        fallback: !0
                    })
                } catch (error) {
                    return console.error("[PROCESS_IMAGE_SERVER] Error:", error),
                    {
                        success: !1,
                        error: error.message,
                        fallback: !0
                    }
                }
            case "uploadPhotoToVinted":
                try {
                    const {imageBase64: imageBase64, domain: domain, csrf: csrf, tempUuid: tempUuid} = request;
                    if (!(imageBase64 && domain && csrf && tempUuid))
                        return console.error("[UPLOAD_PHOTO] Missing params!"),
                        {
                            success: !1,
                            error: "Missing required parameters"
                        };
                    let base64Content = imageBase64;
                    base64Content.includes(",") && (base64Content = base64Content.split(",")[1]);
                    const byteString = atob(base64Content)
                      , ab = new ArrayBuffer(byteString.length)
                      , ia = new Uint8Array(ab);
                    for (let i = 0; i < byteString.length; i++)
                        ia[i] = byteString.charCodeAt(i);
                    255 === ia[0] && 216 === ia[1] && ia[2],
                    ia[0].toString(16),
                    ia[1].toString(16),
                    ia[2].toString(16);
                    const blob = new Blob([ab],{
                        type: "image/jpeg"
                    })
                      , filename = `IMG_${Math.floor(1e3 + 9e3 * Math.random())}.jpeg`
                      , formData = new FormData;
                    formData.append("photo[type]", "item"),
                    formData.append("photo[file]", blob, filename),
                    formData.append("photo[temp_uuid]", tempUuid);
                    let cookieHeader = "";
                    try {
                        cookieHeader = (await chrome.cookies.getAll({
                            domain: domain
                        })).map((c => `${c.name}=${c.value}`)).join("; ")
                    } catch (cookieErr) {}
                    const headers = {
                        Accept: "application/json, text/plain, */*",
                        "X-CSRF-Token": csrf,
                        "X-Requested-With": "XMLHttpRequest"
                    };
                    cookieHeader && (headers.Cookie = cookieHeader);
                    const uploadResponse = await fetch(`https://${domain}/api/v2/photos`, {
                        method: "POST",
                        headers: headers,
                        credentials: "include",
                        body: formData
                    });
                    if (uploadResponse.ok) {
                        const data = await uploadResponse.json();
                        return console.log("[UPLOAD_PHOTO] SUCCESS! Photo ID:", data.id),
                        {
                            success: !0,
                            data: data
                        }
                    }
                    {
                        const errorText = await uploadResponse.text();
                        return console.error("[UPLOAD_PHOTO] FAILED:", uploadResponse.status),
                        console.error("[UPLOAD_PHOTO] Response body:", errorText.substring(0, 300)),
                        {
                            success: !1,
                            error: `Upload failed: ${uploadResponse.status}`,
                            status: uploadResponse.status,
                            body: errorText.substring(0, 500)
                        }
                    }
                } catch (error) {
                    return console.error("[UPLOAD_PHOTO] EXCEPTION:", error.message, error.stack),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "openDashboard":
                try {
                    const browserEnv = await getBrowserEnvironment();
                    if (browserEnv && browserEnv.isMobile) {
                        let mobileDashboardUrl = chrome.runtime.getURL("html/mobile-dashboard/index.html");
                        request.tab && (mobileDashboardUrl += `?tab=${request.tab}`),
                        chrome.tabs.create({
                            url: mobileDashboardUrl
                        })
                    } else
                        chrome.runtime.openOptionsPage()
                } catch (error) {
                    console.error("[openDashboard] Error:", error),
                    chrome.runtime.openOptionsPage()
                }
                return {
                    success: !0
                };
            case "openPricingPage":
                try {
                    const browserEnv = await getBrowserEnvironment();
                    if (browserEnv && browserEnv.isMobile)
                        chrome.tabs.create({
                            url: "https://vindy.tech/pricing"
                        });
                    else {
                        const pricingUrl = chrome.runtime.getURL("html/modern-light-menu/products.html");
                        chrome.tabs.create({
                            url: pricingUrl
                        })
                    }
                } catch (error) {
                    console.error("[openPricingPage] Error:", error),
                    chrome.tabs.create({
                        url: "https://vindy.tech/pricing"
                    })
                }
                return {
                    success: !0
                };
            case "getOldProducts":
                try {
                    const items = await getFromStorage("items");
                    if (!items || !Array.isArray(items))
                        return {
                            products: []
                        };
                    const getLastPushUpTimestamp = item => item.push_up && item.push_up.next_push_up_time ? new Date(item.push_up.next_push_up_time).getTime() / 1e3 : item.photos && item.photos.length > 0 && item.photos[0].high_resolution?.timestamp ? item.photos[0].high_resolution.timestamp : item.created_at_ts ? item.created_at_ts : item.updated_at_ts ? item.updated_at_ts : item.created_at ? new Date(item.created_at).getTime() / 1e3 : item.updated_at ? new Date(item.updated_at).getTime() / 1e3 : 0
                      , fiveDaysAgo = Date.now() / 1e3 - 432e3
                      , activeItems = items.filter((item => !item.is_draft && !item.is_processing && "sold" !== item.item_closing_action && 1 != item.is_hidden));
                    return {
                        products: activeItems.filter((item => {
                            const pushUpTime = getLastPushUpTimestamp(item);
                            return pushUpTime > 0 && pushUpTime < fiveDaysAgo
                        }
                        )).map((item => ({
                            ...item,
                            _timestamp: getLastPushUpTimestamp(item)
                        }))).sort(( (a, b) => a._timestamp - b._timestamp)).slice(0, 10)
                    }
                } catch (error) {
                    return console.error("[ERROR] Error getting old products:", error),
                    {
                        products: []
                    }
                }
            case "getAutoMsgStatus":
                try {
                    const {autoMsg_sentToday: autoMsg_sentToday, autoMsg_dailyLimit: autoMsg_dailyLimit, auto_messages_enabled: auto_messages_enabled, autoMsg_rateLimited: autoMsg_rateLimited, autoMsg_rateLimitedAt: autoMsg_rateLimitedAt} = await chrome.storage.local.get(["autoMsg_sentToday", "autoMsg_dailyLimit", "auto_messages_enabled", "autoMsg_rateLimited", "autoMsg_rateLimitedAt"]);
                    return {
                        success: !0,
                        isRunning: null !== autoMsg_interval,
                        enabled: auto_messages_enabled || !1,
                        sentToday: autoMsg_sentToday || 0,
                        dailyLimit: autoMsg_dailyLimit || 10,
                        rateLimited: autoMsg_rateLimited || !1,
                        rateLimitedAt: autoMsg_rateLimitedAt || null
                    }
                } catch (error) {
                    return console.error("[ERROR] Error getting auto msg status:", error),
                    {
                        success: !1
                    }
                }
            case "clearAutoMsgRateLimit":
                try {
                    return await chrome.storage.local.set({
                        autoMsg_rateLimited: !1,
                        autoMsg_rateLimitedAt: null
                    }),
                    {
                        success: !0
                    }
                } catch (error) {
                    return {
                        success: !1
                    }
                }
            case "getRecentLikes":
                try {
                    const likes = await fetchRecentLikes(!0)
                      , {domain: likesDomain} = await chrome.storage.local.get(["domain"]);
                    return {
                        likes: likes.slice(0, 20).map((like => {
                            const username = like.initiator?.login || like.user?.login || like.body?.match(/^([^\s]+)/)?.[1] || "User"
                              , userPhoto = like.initiator?.photo?.url || like.user?.photo?.url || like.initiator_photo_url || ""
                              , itemTitle = like.subject_title || like.item_title || like.body?.split(" liked ")[1]?.replace(/\.$/, "") || "your item"
                              , offeringIdMatch = like.link?.match(/offering_id=(\d+)/)
                              , offeringId = offeringIdMatch ? offeringIdMatch[1] : ""
                              , productPhoto = like.small_photo_url || like.photo?.url || like.photo?.thumbnails?.[0]?.url || like.item_photo_url || userPhoto || ""
                              , createdAt = like.created_at_ts || like.updated_at_ts
                              , itemId = like.subject_id || like.item_id || "";
                            return {
                                id: like.id || `${itemId}_${offeringId}_${createdAt}`,
                                username: username,
                                user_photo: userPhoto,
                                item_title: itemTitle,
                                item_id: itemId,
                                offering_id: offeringId,
                                product_photo: productPhoto,
                                created_at: createdAt,
                                domain: likesDomain
                            }
                        }
                        ))
                    }
                } catch (error) {
                    return console.error("[ERROR] Error getting recent likes:", error),
                    {
                        likes: []
                    }
                }
            case "load_items":
                try {
                    const {domain: loadItemsDomain} = await chrome.storage.local.get(["domain"]);
                    if (!loadItemsDomain)
                        return {
                            success: !1,
                            items: []
                        };
                    const user = await getFromStorage("user");
                    if (!user)
                        return {
                            success: !1,
                            items: []
                        };
                    let allLoadedItems = []
                      , loadPage = 1
                      , loadTotalPages = 1;
                    const PER_PAGE = 200;
                    for (; loadPage <= loadTotalPages; ) {
                        const response = await fetch(`https://${loadItemsDomain}/api/v2/wardrobe/${user.id}/items?page=${loadPage}&per_page=${PER_PAGE}`, {
                            headers: {
                                accept: "application/json"
                            }
                        });
                        if (!response.ok) {
                            if (console.error(`[LOAD_ITEMS] Failed to fetch page ${loadPage}:`, response.status),
                            1 === loadPage) {
                                return {
                                    success: !0,
                                    items: await getFromStorage("items") || [],
                                    fromCache: !0
                                }
                            }
                            break
                        }
                        const data = await response.json()
                          , pageItems = data.items || [];
                        if (allLoadedItems = allLoadedItems.concat(pageItems),
                        !data.pagination || !data.pagination.total_pages)
                            break;
                        if (loadTotalPages = data.pagination.total_pages,
                        pageItems.length < PER_PAGE)
                            break;
                        loadPage++,
                        loadPage <= loadTotalPages && await new Promise((r => setTimeout(r, 150)))
                    }
                    return await chrome.storage.local.set({
                        items: allLoadedItems
                    }),
                    {
                        success: !0,
                        items: allLoadedItems,
                        loadedAt: Date.now()
                    }
                } catch (error) {
                    return console.error("[LOAD_ITEMS] Error loading items:", error),
                    {
                        success: !1,
                        items: [],
                        error: error.message
                    }
                }
            case "getProductBackups":
                try {
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    let pbUrl = `${serverUrl}/api/v1/product_backups`;
                    request.source_vinted_user_id && (pbUrl += `?source_vinted_user_id=${request.source_vinted_user_id}`);
                    const pbResp = await fetch(pbUrl, {
                        headers: {
                            Authorization: `Bearer ${session.access_token}`
                        }
                    })
                      , pbResult = await pbResp.json();
                    return pbResp.ok ? {
                        success: !0,
                        ...pbResult
                    } : {
                        success: !1,
                        error: pbResult.error || "Failed to fetch backups"
                    }
                } catch (error) {
                    return console.error("[PRODUCT_BACKUP] Error listing backups:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getProductBackupUsage":
                try {
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const usageResp = await fetch(`${serverUrl}/api/v1/product_backups/usage`, {
                        headers: {
                            Authorization: `Bearer ${session.access_token}`
                        }
                    })
                      , usageResult = await usageResp.json();
                    return usageResp.ok ? {
                        success: !0,
                        ...usageResult
                    } : {
                        success: !1,
                        error: usageResult.error || "Failed"
                    }
                } catch (error) {
                    return console.error("[PRODUCT_BACKUP] Error getting usage:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "createProductBackups":
                try {
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const backupItems = request.items || [];
                    if (0 === backupItems.length)
                        return {
                            success: !1,
                            error: "No items provided"
                        };
                    const createResp = await fetch(`${serverUrl}/api/v1/product_backups`, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${session.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            items: backupItems
                        })
                    })
                      , createResult = await createResp.json();
                    return createResp.ok ? {
                        success: !0,
                        ...createResult
                    } : {
                        success: !1,
                        error: createResult.error || createResult.message || "Backup failed",
                        current: createResult.current,
                        limit: createResult.limit
                    }
                } catch (error) {
                    return console.error("[PRODUCT_BACKUP] Error creating backups:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getProductBackupData":
                try {
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const backupId = request.backup_id;
                    if (!backupId)
                        return {
                            success: !1,
                            error: "backup_id required"
                        };
                    const detailResp = await fetch(`${serverUrl}/api/v1/product_backups/${backupId}`, {
                        headers: {
                            Authorization: `Bearer ${session.access_token}`
                        }
                    })
                      , detailResult = await detailResp.json();
                    return detailResp.ok ? {
                        success: !0,
                        ...detailResult
                    } : {
                        success: !1,
                        error: detailResult.error || "Not found"
                    }
                } catch (error) {
                    return console.error("[PRODUCT_BACKUP] Error getting backup data:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "deleteProductBackup":
                try {
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const delBackupId = request.backup_id;
                    if (!delBackupId)
                        return {
                            success: !1,
                            error: "backup_id required"
                        };
                    const delResp = await fetch(`${serverUrl}/api/v1/product_backups/${delBackupId}`, {
                        method: "DELETE",
                        headers: {
                            Authorization: `Bearer ${session.access_token}`
                        }
                    })
                      , delResult = await delResp.json();
                    return delResp.ok ? {
                        success: !0
                    } : {
                        success: !1,
                        error: delResult.error || "Delete failed"
                    }
                } catch (error) {
                    return console.error("[PRODUCT_BACKUP] Error deleting backup:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "fetchItemDetailsForBackup":
                try {
                    const {domain: bkDomain} = await chrome.storage.local.get(["domain"]);
                    if (!bkDomain)
                        return {
                            success: !1,
                            error: "Domain not found"
                        };
                    const itemIds = request.item_ids || [];
                    if (0 === itemIds.length)
                        return {
                            success: !1,
                            error: "No item IDs provided"
                        };
                    let bkCsrf = null;
                    try {
                        const csrfResp = await fetch(`https://${bkDomain}/items/new`);
                        if (csrfResp.ok) {
                            const csrfMatch = (await csrfResp.text()).match(/CSRF_TOKEN[^0-9A-Za-z]*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
                            csrfMatch && (bkCsrf = csrfMatch[1])
                        }
                    } catch (e) {
                        console.warn("[PRODUCT_BACKUP] Could not get CSRF, falling back to details endpoint")
                    }
                    const itemDetails = [];
                    for (const itemId of itemIds)
                        try {
                            let itemData = null;
                            if (bkCsrf) {
                                const resp = await fetch(`https://${bkDomain}/api/v2/item_upload/items/${itemId}`, {
                                    method: "GET",
                                    headers: {
                                        accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                                        "x-csrf-token": bkCsrf
                                    }
                                });
                                if (resp.ok) {
                                    const data = await resp.json();
                                    data.item && (itemData = data.item)
                                }
                            }
                            if (!itemData) {
                                const resp = await fetch(`https://${bkDomain}/api/v2/items/${itemId}/details/`, {
                                    headers: {
                                        Accept: "application/json"
                                    }
                                });
                                if (resp.ok) {
                                    const data = await resp.json();
                                    data.item && (itemData = data.item)
                                }
                            }
                            itemData ? itemDetails.push(itemData) : console.warn(`[PRODUCT_BACKUP] Failed to fetch item ${itemId}`),
                            itemIds.length > 1 && await new Promise((r => setTimeout(r, 300)))
                        } catch (fetchErr) {
                            console.error(`[PRODUCT_BACKUP] Error fetching item ${itemId}:`, fetchErr)
                        }
                    return {
                        success: !0,
                        items: itemDetails
                    }
                } catch (error) {
                    return console.error("[PRODUCT_BACKUP] Error fetching item details:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "restoreProductFromBackup":
                try {
                    const {domain: restoreDomain} = await chrome.storage.local.get(["domain"]);
                    if (!restoreDomain)
                        return {
                            success: !1,
                            error: "Domain not found. Make sure you are logged into Vinted."
                        };
                    const restoreMode = request.mode || "normal"
                      , backupId = request.backup_id;
                    if (!backupId)
                        return {
                            success: !1,
                            error: "backup_id required"
                        };
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in"
                        };
                    const bkDataResp = await fetch(`${serverUrl}/api/v1/product_backups/${backupId}`, {
                        headers: {
                            Authorization: `Bearer ${session.access_token}`
                        }
                    });
                    if (!bkDataResp.ok)
                        return {
                            success: !1,
                            error: "Failed to load backup data"
                        };
                    const backup = (await bkDataResp.json()).backup;
                    if (!backup || !backup.product_data)
                        return {
                            success: !1,
                            error: "Invalid backup data"
                        };
                    const item = backup.product_data
                      , sendProgress = (phase, desc, pct) => {
                        try {
                            chrome.runtime.sendMessage({
                                type: "restoreProgress",
                                backup_id: backupId,
                                phase: phase,
                                desc: desc,
                                pct: pct
                            }).catch(( () => {}
                            ))
                        } catch (_) {}
                    }
                    ;
                    sendProgress("Loading backup data", "Backup loaded successfully", 10);
                    const csrfPageResp = await fetch(`https://${restoreDomain}/items/new`);
                    if (!csrfPageResp.ok)
                        throw new Error("Failed to get CSRF token");
                    const csrfPageMatch = (await csrfPageResp.text()).match(/CSRF_TOKEN[^0-9A-Za-z]*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
                    if (!csrfPageMatch)
                        throw new Error("Unable to get CSRF token");
                    let restoreCsrf = csrfPageMatch[1];
                    sendProgress("CSRF Token", "Connected to Vinted", 20);
                    const restoreUuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c => {
                        const r = 16 * Math.random() | 0;
                        return ("x" === c ? r : 3 & r | 8).toString(16)
                    }
                    ))
                      , photos = item.photos || []
                      , uploadedPhotos = []
                      , storedPhotos = backup.stored_photo_urls || []
                      , editedPhotos = request.edited_photos || []
                      , isNewEditorFormat = editedPhotos.length > 0 && "object" == typeof editedPhotos[0] && null !== editedPhotos[0]
                      , photoQueue = [];
                    if (isNewEditorFormat)
                        for (let i = 0; i < editedPhotos.length; i++) {
                            const entry = editedPhotos[i]
                              , origIdx = entry.originalIndex
                              , origPhoto = origIdx >= 0 && origIdx < photos.length ? photos[origIdx] : null
                              , origUrl = origIdx >= 0 ? storedPhotos[origIdx] || origPhoto && (origPhoto.full_size_url || origPhoto.url) : null
                              , label = entry.isAiGenerated ? "AI" : entry.dataUrl ? "edited" : "original";
                            photoQueue.push({
                                dataUrl: entry.dataUrl,
                                photoUrl: origUrl,
                                label: label
                            })
                        }
                    else
                        for (let i = 0; i < photos.length; i++) {
                            const photo = photos[i]
                              , photoUrl = storedPhotos[i] || photo.full_size_url || photo.url
                              , dataUrl = editedPhotos[i] || null;
                            (photoUrl || dataUrl) && photoQueue.push({
                                dataUrl: dataUrl,
                                photoUrl: photoUrl,
                                label: dataUrl ? "edited" : "original"
                            })
                        }
                    const totalToUpload = photoQueue.length;
                    for (let i = 0; i < totalToUpload; i++) {
                        const qEntry = photoQueue[i];
                        if (!qEntry.dataUrl && !qEntry.photoUrl)
                            continue;
                        const photoPct = Math.round(25 + i / totalToUpload * 55);
                        try {
                            let photoBlob;
                            if (qEntry.dataUrl) {
                                sendProgress(`Using ${qEntry.label} photo ${i + 1}/${totalToUpload}`, "Applying your edits...", photoPct);
                                const b64 = qEntry.dataUrl.includes(",") ? qEntry.dataUrl.split(",")[1] : qEntry.dataUrl
                                  , byteStr = atob(b64)
                                  , ab = new ArrayBuffer(byteStr.length)
                                  , ia = new Uint8Array(ab);
                                for (let j = 0; j < byteStr.length; j++)
                                    ia[j] = byteStr.charCodeAt(j);
                                photoBlob = new Blob([ab],{
                                    type: "image/jpeg"
                                })
                            } else {
                                sendProgress(`Downloading photo ${i + 1}/${totalToUpload}`, "safe" === restoreMode ? "Downloading & processing..." : "Downloading...", photoPct);
                                const photoResp = await fetch(qEntry.photoUrl, {
                                    mode: "cors",
                                    credentials: "same-origin"
                                });
                                if (!photoResp.ok)
                                    throw new Error(`HTTP ${photoResp.status}`);
                                photoBlob = await photoResp.blob()
                            }
                            if ("safe" === restoreMode) {
                                sendProgress(`Processing photo ${i + 1}/${totalToUpload}`, "Making image unique (Safe Mode)...", photoPct + 2);
                                try {
                                    const base64 = await new Promise(( (resolve, reject) => {
                                        const reader = new FileReader;
                                        reader.onloadend = () => resolve(reader.result),
                                        reader.onerror = reject,
                                        reader.readAsDataURL(photoBlob)
                                    }
                                    ))
                                      , processResult = await fetch(`${serverUrl}/api/v1/process_image_repost`, {
                                        method: "POST",
                                        headers: {
                                            Authorization: `Bearer ${session.access_token}`,
                                            "Content-Type": "application/json"
                                        },
                                        body: JSON.stringify({
                                            image_base64: base64
                                        })
                                    });
                                    if (processResult.ok) {
                                        const processData = await processResult.json();
                                        if (processData.success && processData.image_base64) {
                                            const base64Data = processData.image_base64.split(",")[1]
                                              , byteString = atob(base64Data)
                                              , ab = new ArrayBuffer(byteString.length)
                                              , ia = new Uint8Array(ab);
                                            for (let j = 0; j < byteString.length; j++)
                                                ia[j] = byteString.charCodeAt(j);
                                            photoBlob = new Blob([ab],{
                                                type: "image/jpeg"
                                            })
                                        }
                                    }
                                } catch (procErr) {}
                            }
                            sendProgress(`Uploading photo ${i + 1}/${totalToUpload}`, "Uploading to Vinted...", photoPct + 4);
                            const formData = new FormData;
                            formData.append("photo[type]", "item"),
                            formData.append("photo[file]", photoBlob),
                            formData.append("photo[temp_uuid]", restoreUuid);
                            const uploadResp = await fetch(`https://${restoreDomain}/api/v2/photos`, {
                                method: "POST",
                                headers: {
                                    accept: "application/json, text/plain, */*,image/webp",
                                    "x-csrf-token": restoreCsrf
                                },
                                referrer: `https://${restoreDomain}/items/new`,
                                credentials: "include",
                                body: formData
                            });
                            if (!uploadResp.ok)
                                throw new Error(`Upload failed: ${uploadResp.status}`);
                            const photoData = await uploadResp.json();
                            uploadedPhotos.push(photoData)
                        } catch (photoErr) {
                            console.error(`[RESTORE] âŒ Failed to upload image ${i + 1}:`, photoErr)
                        }
                        i < totalToUpload - 1 && await new Promise((r => setTimeout(r, 300)))
                    }
                    if (0 === uploadedPhotos.length)
                        return {
                            success: !1,
                            error: "Failed to upload any images. The original photos may no longer be available."
                        };
                    const assignedPhotos = uploadedPhotos.map((p => ({
                        id: p.id,
                        orientation: 0
                    })))
                      , draftData = {
                        item: {
                            id: null,
                            currency: item.currency || "EUR",
                            temp_uuid: restoreUuid,
                            title: item.title,
                            description: item.description,
                            brand_id: item.brand_dto?.id || item.brand_id,
                            brand: item.brand_dto?.title || item.brand,
                            size_id: item.size_id,
                            catalog_id: item.catalog_id,
                            isbn: item.isbn,
                            is_unisex: null != item.is_unisex && (1 !== item.is_unisex && item.is_unisex),
                            status_id: item.status_id,
                            video_game_rating_id: item.video_game_rating_id,
                            price: "object" == typeof item.price ? item.price.amount : item.price,
                            package_size_id: item.package_size_id,
                            shipment_prices: {
                                domestic: null,
                                international: null
                            },
                            color_ids: [item.color1_id, item.color2_id].filter(Boolean),
                            assigned_photos: assignedPhotos,
                            measurement_length: item.measurement_length,
                            measurement_width: item.measurement_width,
                            item_attributes: item.item_attributes?.length ? item.item_attributes : [{
                                code: "material",
                                ids: []
                            }],
                            manufacturer: item.manufacturer,
                            manufacturer_labelling: item.manufacturer_labelling
                        },
                        feedback_id: null,
                        parcel: null,
                        push_up: !1
                    };
                    sendProgress("Creating listing", "Publishing on Vinted...", 85);
                    const draftResp = await fetch(`https://${restoreDomain}/api/v2/item_upload/items`, {
                        method: "POST",
                        headers: {
                            accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                            "content-type": "application/json",
                            "x-csrf-token": restoreCsrf
                        },
                        referrer: `https://${restoreDomain}/items/new`,
                        credentials: "include",
                        body: JSON.stringify(draftData)
                    })
                      , draftResult = await draftResp.json();
                    if (draftResult.url && draftResult.url.includes("captcha"))
                        return {
                            success: !1,
                            error: "captcha_required",
                            captcha_url: draftResult.url
                        };
                    if (146 === draftResult.code && "entity_2fa_required" === draftResult.message_code)
                        return {
                            success: !1,
                            error: "2fa_required",
                            entity_id: draftResult.payload?.entity_id
                        };
                    if (!draftResult || !draftResult.item || !draftResult.item.id)
                        return console.error("[RESTORE] Draft creation failed:", draftResult),
                        {
                            success: !1,
                            error: "Failed to create listing: " + (draftResult.message || JSON.stringify(draftResult))
                        };
                    const newItemId = draftResult.item.id;
                    sendProgress("Finalizing", "Marking backup as restored...", 95);
                    const {user: vintedUser} = await chrome.storage.local.get(["user"]);
                    return await fetch(`${serverUrl}/api/v1/product_backups/${backupId}/restore`, {
                        method: "PUT",
                        headers: {
                            Authorization: `Bearer ${session.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            restored_to_vinted_user_id: vintedUser?.id || ""
                        })
                    }),
                    await chrome.storage.local.set({
                        items: []
                    }),
                    sendProgress("Complete", "Product restored successfully!", 100),
                    {
                        success: !0,
                        newItemId: newItemId,
                        photosUploaded: uploadedPhotos.length,
                        totalPhotos: photos.length
                    }
                } catch (error) {
                    return console.error("[RESTORE] âŒ Error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "apiRequest":
                try {
                    const endpoint = request.endpoint
                      , method = request.method || "GET"
                      , data = request.data;
                    if (!endpoint)
                        return {
                            success: !1,
                            error: "Endpoint required"
                        };
                    const session = await getSession();
                    if (!session || !session.access_token)
                        return {
                            success: !1,
                            error: "Not logged in",
                            code: "NOT_LOGGED_IN"
                        };
                    const fetchOptions = {
                        method: method,
                        headers: {
                            Authorization: `Bearer ${session.access_token}`,
                            "Content-Type": "application/json"
                        }
                    };
                    data && "GET" !== method && (fetchOptions.body = JSON.stringify(data));
                    const apiUrl = `${serverUrl}/api/v1/${endpoint}`
                      , response = await fetch(apiUrl, fetchOptions)
                      , result = await response.json();
                    return response.ok ? {
                        success: !0,
                        ...result
                    } : {
                        success: !1,
                        error: result.error || "API request failed",
                        code: result.code,
                        status: response.status
                    }
                } catch (error) {
                    return console.error("[API_REQUEST] Error:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "debouncedSyncSettings":
                return _settingsSyncTimer && clearTimeout(_settingsSyncTimer),
                _settingsSyncTimer = setTimeout(( () => {
                    syncSettingsToServer().catch((err => console.error("[SETTINGS_SYNC] Debounced sync error:", err)))
                }
                ), 2e3),
                {
                    success: !0,
                    queued: !0
                };
            case "startBoostAutoLike":
                try {
                    return startBoostAutoLikeLoop(),
                    {
                        success: !0,
                        status: boost_auto_like_status
                    }
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error starting boost auto-like:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getBoostStats":
                try {
                    const sessione = await getSession();
                    if (!sessione?.access_token)
                        return {
                            success: !1,
                            error: "Not authenticated"
                        };
                    const statsResponse = await fetch(`${serverUrl}/api/v1/boost/stats`, {
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`
                        }
                    });
                    return await statsResponse.json()
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error getting boost stats:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "createBoostRequest":
                try {
                    const sessione = await getSession();
                    if (!sessione?.access_token)
                        return {
                            success: !1,
                            error: "Not authenticated"
                        };
                    const storageData = await chrome.storage.local.get(["user", "domain"])
                      , vintedUserId = storageData.user?.id
                      , domain = storageData.domain || "vinted.it";
                    if (!vintedUserId)
                        return {
                            success: !1,
                            error: "Vinted account not connected"
                        };
                    const boostData = {
                        product_id: request.product_id,
                        product_title: request.product_title,
                        product_image: request.product_image,
                        product_url: request.product_url || `https://${domain}/items/${request.product_id}`,
                        requested_likes: request.requested_likes,
                        vinted_user_id: vintedUserId.toString(),
                        domain: domain
                    }
                      , createResponse = await fetch(`${serverUrl}/api/v1/boost/request`, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify(boostData)
                    });
                    return await createResponse.json()
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error creating boost request:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getBoostNotifications":
                try {
                    const sessione = await getSession();
                    if (!sessione?.access_token)
                        return {
                            success: !1,
                            error: "Not authenticated"
                        };
                    const limit = request.limit || 10
                      , notifResponse = await fetch(`${serverUrl}/api/v1/boost/notifications?limit=${limit}`, {
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`
                        }
                    });
                    return await notifResponse.json()
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error getting boost notifications:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "markBoostNotificationsRead":
                try {
                    const sessione = await getSession();
                    if (!sessione?.access_token)
                        return {
                            success: !1,
                            error: "Not authenticated"
                        };
                    const markResponse = await fetch(`${serverUrl}/api/v1/boost/notifications/read`, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            all: request.all || !1
                        })
                    });
                    return await markResponse.json()
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error marking notifications read:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getBoostRequests":
                try {
                    const sessione = await getSession();
                    if (!sessione?.access_token)
                        return {
                            success: !1,
                            error: "Not authenticated"
                        };
                    const status = request.status || ""
                      , limit = request.limit || 50
                      , excludeCancelled = request.exclude_cancelled || !1;
                    let url = `${serverUrl}/api/v1/boost/requests?limit=${limit}`;
                    status && (url += `&status=${status}`),
                    excludeCancelled && (url += "&exclude_cancelled=true");
                    const reqResponse = await fetch(url, {
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`
                        }
                    });
                    return await reqResponse.json()
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error getting boost requests:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "cancelBoostRequest":
                try {
                    const sessione = await getSession();
                    if (!sessione?.access_token)
                        return {
                            success: !1,
                            error: "Not authenticated"
                        };
                    const cancelResponse = await fetch(`${serverUrl}/api/v1/boost/cancel`, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            boost_request_id: request.boost_request_id
                        })
                    });
                    return await cancelResponse.json()
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error cancelling boost request:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "requestBoostLikes":
                try {
                    const sessione = await getSession();
                    if (!sessione?.access_token)
                        return {
                            success: !1,
                            error: "Not authenticated"
                        };
                    let vintedDomain = "www.vinted.it"
                      , vintedUserId = null;
                    try {
                        const storageData = await chrome.storage.local.get(["vinted_domain", "user"]);
                        vintedDomain = storageData.vinted_domain || "www.vinted.it",
                        vintedUserId = storageData.user?.id || null
                    } catch (e) {
                        console.error("[MESSAGE_HANDLER] Error getting storage data:", e)
                    }
                    if (!vintedUserId)
                        return {
                            success: !1,
                            error: "Vinted user not found. Please connect to Vinted first."
                        };
                    const domainClean = vintedDomain.replace(/^www\./, "")
                      , boostResponse = await fetch(`${serverUrl}/api/v1/boost/request`, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${sessione.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            product_id: String(request.product_id),
                            product_title: request.product_title || "Product",
                            product_image: request.product_image || "",
                            product_url: `https://${vintedDomain}/items/${request.product_id}`,
                            vinted_user_id: String(vintedUserId),
                            domain: domainClean,
                            requested_likes: request.requested_likes || 5
                        })
                    });
                    return await boostResponse.json()
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] Error requesting boost likes:", error),
                    {
                        success: !1,
                        error: error.message
                    }
                }
            case "getSupabaseSession":
                try {
                    return {
                        success: !0,
                        session: await getSession()
                    }
                } catch (error) {
                    return {
                        success: !1,
                        error: error.message
                    }
                }
            case "getPlansPricing":
                try {
                    const plansData = await async function() {
                        const session = await checkLoginSupabase();
                        if (!session || !session.access_token)
                            return {
                                status: 403,
                                error: "Not authenticated"
                            };
                        try {
                            const cached = await chrome.storage.local.get(PLANS_PRICING_CACHE_KEY);
                            if (cached[PLANS_PRICING_CACHE_KEY]?.timestamp && Date.now() - cached[PLANS_PRICING_CACHE_KEY].timestamp < 3e5)
                                return {
                                    status: 200,
                                    ...cached[PLANS_PRICING_CACHE_KEY].data
                                }
                        } catch (e) {}
                        try {
                            const response = await fetch(`${serverUrl}/api/v1/plans/pricing`, {
                                method: "GET",
                                headers: {
                                    Authorization: `Bearer ${session.access_token}`,
                                    "Content-Type": "application/json"
                                }
                            });
                            if (response.ok) {
                                const data = await response.json();
                                try {
                                    await chrome.storage.local.set({
                                        [PLANS_PRICING_CACHE_KEY]: {
                                            timestamp: Date.now(),
                                            data: data
                                        }
                                    })
                                } catch (e) {}
                                return {
                                    status: 200,
                                    ...data
                                }
                            }
                            return {
                                status: response.status,
                                error: "Failed to get plans pricing"
                            }
                        } catch (error) {
                            return console.error("[PLANS_PRICING] Error:", error),
                            {
                                status: 500,
                                error: error.message
                            }
                        }
                    }();
                    return plansData
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] getPlansPricing error:", error),
                    {
                        status: 500,
                        error: error.message
                    }
                }
            case "getPayment":
                try {
                    return await async function(price_id, referer, plan_name) {
                        const sessione = await checkLoginSupabase();
                        if (sessione) {
                            const response = await fetch(serverUrl + "/api/v1/get_payment_link", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    Back: referer,
                                    Authorization: `Bearer ${sessione.access_token}`,
                                    Referer: referer
                                },
                                body: JSON.stringify({
                                    price_id: price_id,
                                    plan_name: plan_name || "Premium Plan"
                                })
                            });
                            return response.ok ? {
                                status: 200,
                                data: await response.json()
                            } : {
                                status: response.status,
                                reason: `Server responded with status: ${response.status}`
                            }
                        }
                        return {
                            status: 403,
                            reason: "Not logged in"
                        }
                    }(request.price_id, request.referer, request.plan_name)
                } catch (error) {
                    return console.error("[MESSAGE_HANDLER] getPayment error:", error),
                    {
                        status: 500,
                        error: error.message
                    }
                }
            default:
                return {
                    success: !1,
                    message: "Invalid message"
                }
            }
        } catch (error) {
            return console.error("Error in message handler:", error),
            {
                status: 500,
                error: error.message
            }
        }
        var active
    }
    )().then((response => {
        try {
            sendResponse(response)
        } catch (e) {}
    }
    )).catch((error => {
        try {
            sendResponse({
                status: 500,
                error: error.message
            })
        } catch (e) {}
    }
    )),
    !0)));
    let boost_auto_like_status = !1
      , boost_auto_like_interval = null
      , boost_iteration_running = !1
      , boost_next_like_allowed = 0
      , boost_empty_count = 0
      , boost_excluded_product_ids = new Set
      , boost_excluded_last_cleared = Date.now();
    const BOOST_LIKE_INTERVAL = 1e4
      , BOOST_LIKE_MIN_TIME = 3e4
      , BOOST_LIKE_MAX_TIME = 24e4
      , BOOST_EMPTY_BACKOFF_TIME = 6e4
      , BOOST_EMPTY_THRESHOLD = 5
      , BOOST_HOURLY_LIMIT = 15
      , BOOST_EXCLUSION_CLEAR_TIME = 36e5;
    async function likeVintedItem(itemId, domain, retryCount=0) {
        try {
            if (x_csrf || await updateCSRF(),
            !x_csrf)
                return {
                    success: !1,
                    message: "Failed to get CSRF token"
                };
            const url = `https://${domain}/api/v2/user_favourites/toggle`
              , response = await fetch(url, {
                method: "POST",
                headers: {
                    Accept: "application/json, text/plain, */*,image/webp",
                    "Content-Type": "application/json",
                    "X-CSRF-Token": x_csrf
                },
                credentials: "include",
                body: JSON.stringify({
                    type: "item",
                    user_favourites: [parseInt(itemId)]
                })
            });
            if (response.ok)
                try {
                    const responseData = await response.json();
                    return 0 === responseData.code || "ok" === responseData.message_code ? (console.log(`[BOOST_LIKE] âœ… Successfully liked item ${itemId}`),
                    await chrome.storage.local.set({
                        boostLastLikeTimestamp: Date.now()
                    }),
                    {
                        success: !0
                    }) : {
                        success: !1,
                        message: responseData.message || "Unexpected response"
                    }
                } catch (parseError) {
                    return console.log(`[BOOST_LIKE] âœ… Successfully liked item ${itemId} (no JSON body)`),
                    await chrome.storage.local.set({
                        boostLastLikeTimestamp: Date.now()
                    }),
                    {
                        success: !0
                    }
                }
            if ((403 === response.status || 422 === response.status) && retryCount < 2)
                return x_csrf = "",
                await updateCSRF(),
                likeVintedItem(itemId, domain, retryCount + 1);
            if (429 === response.status)
                return {
                    success: !1,
                    message: "Rate limited",
                    retry: !0
                };
            const errorText = await response.text().catch(( () => ""));
            return {
                success: !1,
                message: `HTTP ${response.status}: ${errorText.substring(0, 100)}`
            }
        } catch (error) {
            return console.error("[BOOST_LIKE] Error:", error),
            {
                success: !1,
                message: error.message
            }
        }
    }
    const AUTH_GATE_CACHE_TTL = 6e4;
    let _authGateCache = {
        result: null,
        timestamp: 0
    };
    async function ensureAuthenticated() {
        const now = Date.now();
        if (_authGateCache.result && now - _authGateCache.timestamp < AUTH_GATE_CACHE_TTL) {
            if (_authGateCache.result.ready)
                return _authGateCache.result;
            if (now - _authGateCache.timestamp < 1e4)
                return _authGateCache.result
        }
        const session = await checkLoginSupabase();
        if (!session || !session.access_token) {
            const fail = {
                ready: !1,
                reason: "Supabase session not active"
            };
            return _authGateCache = {
                result: fail,
                timestamp: now
            },
            fail
        }
        const domain = await getFromStorage("domain");
        if (!domain) {
            const fail = {
                ready: !1,
                reason: "No Vinted domain configured"
            };
            return _authGateCache = {
                result: fail,
                timestamp: now
            },
            fail
        }
        const vintedLogin = await checkLogin(domain);
        if (!vintedLogin || !vintedLogin.success) {
            const fail = {
                ready: !1,
                reason: vintedLogin?.message || "Not authenticated on Vinted"
            };
            return _authGateCache = {
                result: fail,
                timestamp: now
            },
            fail
        }
        const ok = {
            ready: !0,
            session: session,
            domain: domain
        };
        return _authGateCache = {
            result: ok,
            timestamp: now
        },
        ok
    }
    function invalidateAuthGateCache() {
        _authGateCache = {
            result: null,
            timestamp: 0
        }
    }
    async function canDoBoostLike() {
        const data = await chrome.storage.local.get(["boostLikesConsent", "boost_likes_enabled"]);
        if (!1 === data.boost_likes_enabled)
            return {
                canLike: !1,
                reason: "Feature disabled by user"
            };
        if (!0 !== data.boostLikesConsent)
            return {
                canLike: !1,
                reason: "No consent"
            };
        const limitStatus = await async function() {
            try {
                const timestamps = (await chrome.storage.local.get("boost_likes_given_timestamps")).boost_likes_given_timestamps || []
                  , oneHourAgo = Date.now() - 36e5
                  , recentLikes = timestamps.filter((ts => ts > oneHourAgo));
                let resetAt = 0;
                return recentLikes.length >= BOOST_HOURLY_LIMIT && recentLikes.length > 0 && (resetAt = Math.min(...recentLikes) + 36e5),
                {
                    canLike: recentLikes.length < BOOST_HOURLY_LIMIT,
                    likesGiven: recentLikes.length,
                    remaining: Math.max(0, BOOST_HOURLY_LIMIT - recentLikes.length),
                    resetAt: resetAt
                }
            } catch (error) {
                return console.error("[BOOST_LIMIT] Error checking limit:", error),
                {
                    canLike: !0,
                    likesGiven: 0,
                    remaining: BOOST_HOURLY_LIMIT,
                    resetAt: 0
                }
            }
        }();
        if (!limitStatus.canLike) {
            return {
                canLike: !1,
                reason: "Hourly limit reached",
                waitTime: limitStatus.resetAt - Date.now(),
                limitStatus: limitStatus
            }
        }
        const now = Date.now();
        if (now < boost_next_like_allowed) {
            return {
                canLike: !1,
                reason: "Too soon",
                waitTime: boost_next_like_allowed - now
            }
        }
        return {
            canLike: !0,
            limitStatus: limitStatus
        }
    }
    async function doBoostLikeIteration() {
        if (!boost_iteration_running)
            try {
                boost_iteration_running = !0,
                Date.now() - boost_excluded_last_cleared > BOOST_EXCLUSION_CLEAR_TIME && (boost_excluded_product_ids.size,
                boost_excluded_product_ids.clear(),
                boost_excluded_last_cleared = Date.now());
                if (!(await canDoBoostLike()).canLike)
                    return;
                const auth = await ensureAuthenticated();
                if (!auth.ready)
                    return;
                const session = auth.session
                  , userDomain = auth.domain
                  , userData = await getFromStorage("user")
                  , vintedUserId = userData?.id || "";
                let pendingUrl = `${serverUrl}/api/v1/boost/pending?limit=1`;
                if (vintedUserId && (pendingUrl += `&vinted_user_id=${vintedUserId}`),
                boost_excluded_product_ids.size > 0) {
                    const excludeParam = Array.from(boost_excluded_product_ids).join(",");
                    pendingUrl += `&exclude=${encodeURIComponent(excludeParam)}`
                }
                const pendingResponse = await fetch(pendingUrl, {
                    headers: {
                        Authorization: `Bearer ${session.access_token}`
                    }
                });
                if (!pendingResponse.ok)
                    return;
                const pendingResult = await pendingResponse.json();
                if (!pendingResult.success || !pendingResult.data || 0 === pendingResult.data.length)
                    return boost_empty_count++,
                    void (boost_empty_count >= BOOST_EMPTY_THRESHOLD && (boost_next_like_allowed = Date.now() + BOOST_EMPTY_BACKOFF_TIME,
                    boost_empty_count = 0));
                boost_empty_count = 0;
                const boostRequest = pendingResult.data[0];
                let itemId = boostRequest.product_id;
                if (boostRequest.product_url) {
                    const itemIdMatch = boostRequest.product_url.match(/items\/(\d+)/);
                    itemIdMatch && (itemId = itemIdMatch[1])
                }
                const itemCheck = await async function(itemId, domain) {
                    try {
                        const response = await fetch(`https://${domain}/api/v2/items/${itemId}/details/`, {
                            method: "GET",
                            headers: {
                                Accept: "application/json, text/plain, */*"
                            },
                            credentials: "include"
                        });
                        if (404 === response.status)
                            return {
                                exists: !1,
                                status: 404,
                                reason: "not_found"
                            };
                        if (410 === response.status)
                            return {
                                exists: !1,
                                status: 410,
                                reason: "deleted"
                            };
                        if (response.ok)
                            try {
                                const item = (await response.json()).item;
                                return item ? item.is_draft ? {
                                    exists: !1,
                                    status: response.status,
                                    reason: "draft"
                                } : item.is_processing ? {
                                    exists: !1,
                                    status: response.status,
                                    reason: "processing"
                                } : "sold" === item.item_closing_action ? {
                                    exists: !1,
                                    status: response.status,
                                    reason: "sold"
                                } : !0 === item.is_hidden || 1 === item.is_hidden ? {
                                    exists: !1,
                                    status: response.status,
                                    reason: "hidden"
                                } : item.is_closed ? {
                                    exists: !1,
                                    status: response.status,
                                    reason: "closed"
                                } : {
                                    exists: !0,
                                    status: response.status
                                } : {
                                    exists: !1,
                                    status: response.status,
                                    reason: "no_data"
                                }
                            } catch (parseError) {
                                return {
                                    exists: !0,
                                    status: response.status,
                                    uncertain: !0
                                }
                            }
                        return {
                            exists: !0,
                            status: response.status,
                            uncertain: !0
                        }
                    } catch (error) {
                        return console.error(`[BOOST_CHECK] Error checking item ${itemId}:`, error),
                        {
                            exists: !0,
                            error: error.message,
                            uncertain: !0
                        }
                    }
                }(itemId, userDomain);
                if (!itemCheck.exists && !itemCheck.uncertain)
                    return void boost_excluded_product_ids.add(String(boostRequest.product_id));
                let lockId = null;
                try {
                    const lockResponse = await fetch(`${serverUrl}/api/v1/boost/acquire_lock`, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${session.access_token}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            boost_request_id: boostRequest.id
                        })
                    });
                    if (!lockResponse.ok)
                        return;
                    const lockResult = await lockResponse.json();
                    if (!lockResult.success) {
                        lockResult.error;
                        return
                    }
                    lockId = lockResult.lock_id
                } catch (lockError) {
                    return void console.error("[BOOST_AUTO_LIKE] Error acquiring lock:", lockError)
                }
                const productUrl = `https://${userDomain}/items/${itemId}`;
                await async function(productUrl) {
                    try {
                        const response = await fetch(productUrl, {
                            method: "GET",
                            credentials: "include",
                            headers: {
                                Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Accept-Language": "en-US,en;q=0.5",
                                "Upgrade-Insecure-Requests": "1"
                            }
                        });
                        return !!response.ok || (console.warn(`[BOOST_VIEW] âš ï¸ View request returned status: ${response.status}`),
                        !1)
                    } catch (error) {
                        return console.error(`[BOOST_VIEW] Error simulating view: ${error.message}`),
                        !1
                    }
                }(productUrl);
                const likeResult = await likeVintedItem(itemId, userDomain);
                if (likeResult.success) {
                    console.log("[BOOST_AUTO_LIKE] âœ… Like successful!"),
                    await async function() {
                        try {
                            const timestamps = (await chrome.storage.local.get("boost_likes_given_timestamps")).boost_likes_given_timestamps || []
                              , now = Date.now()
                              , oneHourAgo = now - 36e5
                              , recentLikes = timestamps.filter((ts => ts > oneHourAgo));
                            recentLikes.push(now),
                            await chrome.storage.local.set({
                                boost_likes_given_timestamps: recentLikes
                            })
                        } catch (error) {
                            console.error("[BOOST_LIMIT] Error recording like:", error)
                        }
                    }(),
                    function() {
                        const randomWait = BOOST_LIKE_MIN_TIME + Math.random() * (BOOST_LIKE_MAX_TIME - BOOST_LIKE_MIN_TIME);
                        boost_next_like_allowed = Date.now() + randomWait
                    }();
                    const userData = await getFromStorage("user")
                      , vintedUserId = userData?.id || "";
                    try {
                        const confirmResponse = await fetch(`${serverUrl}/api/v1/boost/confirm_like`, {
                            method: "POST",
                            headers: {
                                Authorization: `Bearer ${session.access_token}`,
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                boost_request_id: boostRequest.id,
                                liker_vinted_user_id: vintedUserId,
                                lock_id: lockId
                            })
                        });
                        if (!confirmResponse.ok)
                            return;
                        const confirmResult = await confirmResponse.json();
                        if (confirmResult.success)
                            console.log("[BOOST_AUTO_LIKE] âœ… Confirm successful!");
                        else {
                            confirmResult.error
                        }
                    } catch (confirmError) {
                        console.error("[BOOST_AUTO_LIKE] Error confirming like:", confirmError)
                    }
                } else if (likeResult.retry) {
                    if (boost_next_like_allowed = Date.now() + 6e4,
                    lockId)
                        try {
                            await fetch(`${serverUrl}/api/v1/boost/release_lock`, {
                                method: "POST",
                                headers: {
                                    Authorization: `Bearer ${session.access_token}`,
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    lock_id: lockId
                                })
                            }),
                            console.log("[BOOST_AUTO_LIKE] ðŸ”“ Lock released after rate limit")
                        } catch (releaseError) {
                            console.error("[BOOST_AUTO_LIKE] Error releasing lock:", releaseError)
                        }
                } else {
                    const shortDelay = 1e4 + 2e4 * Math.random();
                    if (boost_next_like_allowed = Date.now() + shortDelay,
                    lockId)
                        try {
                            await fetch(`${serverUrl}/api/v1/boost/release_lock`, {
                                method: "POST",
                                headers: {
                                    Authorization: `Bearer ${session.access_token}`,
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    lock_id: lockId
                                })
                            })
                        } catch (releaseError) {
                            console.error("[BOOST_AUTO_LIKE] Error releasing lock:", releaseError)
                        }
                }
            } catch (error) {
                console.error("[BOOST_AUTO_LIKE] Error in iteration:", error)
            } finally {
                boost_iteration_running = !1
            }
    }
    function startBoostAutoLikeLoop() {
        boost_auto_like_interval || (console.log("[BOOST_AUTO_LIKE] ðŸš€ Starting PERSISTENT auto-like loop (every 10s)..."),
        boost_auto_like_status = !0,
        doBoostLikeIteration(),
        boost_auto_like_interval = setInterval(( () => {
            doBoostLikeIteration()
        }
        ), BOOST_LIKE_INTERVAL))
    }
    let autoMsg_interval = null
      , autoMsg_lastTemplateIndex = 0
      , autoMsg_busy = !1
      , autoMsg_nextAllowedTime = 0;
    const AUTO_MSG_CHECK_INTERVAL = 1e4
      , AUTO_MSG_RATE_LIMIT_WAIT = 18e4
      , AUTO_MSG_CONVERSATION_FAIL_WAIT = 6e4;
    function startAutoMessagesJob() {
        autoMsg_interval ? console.log("[AUTO_MSG] Job already running") : (console.log("[AUTO_MSG] ðŸš€ Starting Auto Messages job (every 10s)..."),
        autoMessagesCycle(),
        autoMsg_interval = setInterval(( () => {
            autoMessagesCycle()
        }
        ), AUTO_MSG_CHECK_INTERVAL))
    }
    async function autoMessagesCycle() {
        if (autoMsg_busy)
            return;
        const now = Date.now();
        if (now < autoMsg_nextAllowedTime)
            return;
        const {autoMsg_retryAfter: autoMsg_retryAfter} = await chrome.storage.local.get("autoMsg_retryAfter");
        if (autoMsg_retryAfter && now < autoMsg_retryAfter) {
            const waitSeconds = Math.ceil((autoMsg_retryAfter - now) / 1e3);
            console.log(`[AUTO_MSG] â±ï¸ Rate-limit cooldown: retrying in ${waitSeconds}s...`)
        } else {
            autoMsg_busy = !0;
            try {
                if (!(await ensureAuthenticated()).ready)
                    return;
                const {auto_messages_enabled: auto_messages_enabled} = await chrome.storage.local.get("auto_messages_enabled");
                if (!auto_messages_enabled)
                    return;
                const {autoMessagesConsent: autoMessagesConsent} = await chrome.storage.local.get("autoMessagesConsent");
                if (!autoMessagesConsent)
                    return;
                const {autoMsg_templates: autoMsg_templates} = await chrome.storage.local.get("autoMsg_templates");
                if (!autoMsg_templates || !Array.isArray(autoMsg_templates))
                    return;
                const activeTemplates = autoMsg_templates.filter((t => !0 === t.isActive));
                if (0 === activeTemplates.length)
                    return;
                const {autoMsg_dailyLimit: autoMsg_dailyLimit} = await chrome.storage.local.get("autoMsg_dailyLimit")
                  , dailyLimit = parseInt(autoMsg_dailyLimit) || 10
                  , {autoMsg_sentToday: autoMsg_sentToday, autoMsg_lastResetDate: autoMsg_lastResetDate} = await chrome.storage.local.get(["autoMsg_sentToday", "autoMsg_lastResetDate"])
                  , today = (new Date).toDateString();
                let sentToday = autoMsg_sentToday || 0;
                if (autoMsg_lastResetDate !== today && (console.log("[AUTO_MSG] ðŸ”„ New day - resetting counter"),
                sentToday = 0,
                await chrome.storage.local.set({
                    autoMsg_sentToday: 0,
                    autoMsg_lastResetDate: today,
                    autoMsg_logDate: today,
                    autoMsg_messageLog: []
                })),
                sentToday >= dailyLimit)
                    return void console.log(`[AUTO_MSG] âŒ Daily limit reached (${sentToday}/${dailyLimit})`);
                const allLikes = await fetchRecentLikes();
                if (!allLikes || 0 === allLikes.length)
                    return;
                const {autoMsg_processedLikes: autoMsg_processedLikes} = await chrome.storage.local.get("autoMsg_processedLikes")
                  , processedLikes = autoMsg_processedLikes || []
                  , validLikes = allLikes.filter((like => {
                    const hasLikerId = like.liker_id
                      , hasOfferingId = like.link && like.link.includes("offering_id=");
                    return hasLikerId || hasOfferingId
                }
                ))
                  , unprocessedLikes = validLikes.filter((like => {
                    const likeId = like.id || `${like.subject_id}_${like.initiator?.id}_${like.created_at_ts}`;
                    return !processedLikes.includes(likeId)
                }
                ));
                if (0 === unprocessedLikes.length)
                    return;
                unprocessedLikes.sort(( (a, b) => {
                    if (a.id && b.id)
                        return Number(b.id) - Number(a.id);
                    const aTime = a.updated_at ? new Date(a.updated_at).getTime() : 0;
                    return (b.updated_at ? new Date(b.updated_at).getTime() : 0) - aTime
                }
                ));
                const AUTO_MSG_MAX_LIKE_AGE_MS = 864e6;
                let like = null
                  , likeId = null;
                for (const candidate of unprocessedLikes) {
                    const candidateId = candidate.id || `${candidate.subject_id}_${candidate.initiator?.id}_${candidate.updated_at}`
                      , likeTime = candidate.updated_at ? new Date(candidate.updated_at).getTime() : 0
                      , ageMs = Date.now() - likeTime;
                    if (!(likeTime > 0 && ageMs > AUTO_MSG_MAX_LIKE_AGE_MS)) {
                        like = candidate,
                        likeId = candidateId;
                        break
                    }
                    Math.round(ageMs / 864e5);
                    await markLikeProcessed(candidateId),
                    await logAutoMessage(null, candidate, "failed_too_old", candidate.initiator?.login || candidate.user?.login || null, candidate.title || candidate.subject_title || null, candidate.small_photo_url || candidate.photo?.url || null)
                }
                if (!like)
                    return;
                const itemId = like.subject_id || like.item_id;
                let likerId = like.liker_id;
                if (!likerId && like.link) {
                    const match = like.link.match(/offering_id=(\d+)/);
                    match && (likerId = match[1])
                }
                let likerUsername = like.initiator?.login || like.user?.login || null
                  , likeItemTitle = like.title || like.subject_title || null
                  , likeItemPhoto = like.small_photo_url || like.photo?.url || like.photo?.thumbnails?.[0]?.url || null;
                if (like.body) {
                    if (!likerUsername) {
                        const usernameMatch = like.body.match(/^([^\s]+)/);
                        usernameMatch && (likerUsername = usernameMatch[1])
                    }
                    if (!likeItemTitle) {
                        const titleMatch = like.body.match(/(?:liked |ha messo like a )(.+)$/i);
                        titleMatch && (likeItemTitle = titleMatch[1])
                    }
                }
                if (!itemId || !likerId)
                    return void await markLikeProcessed(likeId);
                const domain = await getFromStorage("domain");
                if (!domain)
                    return;
                const hasConversation = await async function(domain, itemId, userId) {
                    try {
                        const response = await fetch(`https://${domain}/api/v2/inbox?page=1&per_page=100&item_id=${itemId}`, {
                            method: "GET",
                            headers: {
                                Accept: "application/json"
                            },
                            credentials: "include"
                        });
                        if (!response.ok)
                            return !1;
                        const conversations = (await response.json()).conversations || []
                          , userIdStr = userId.toString();
                        return conversations.some((conv => {
                            const oppositeUserId = conv.opposite_user?.id?.toString()
                              , match = oppositeUserId === userIdStr;
                            return match
                        }
                        ))
                    } catch (error) {
                        return console.error("[AUTO_MSG] âš ï¸ Error checking conversations:", error.message),
                        !1
                    }
                }(domain, itemId, likerId);
                if (hasConversation)
                    return await markLikeProcessed(likeId),
                    void await logAutoMessage(null, like, "skipped_conversation", likerUsername, likeItemTitle, likeItemPhoto);
                const templatesForItem = activeTemplates.filter((template => !template.excludedProducts || 0 === template.excludedProducts.length || !template.excludedProducts.some((p => p.id == itemId))));
                if (0 === templatesForItem.length)
                    return await markLikeProcessed(likeId),
                    void await logAutoMessage(null, like, "skipped_excluded", likerUsername, likeItemTitle, likeItemPhoto);
                const itemStatus = await async function(domain, itemId) {
                    try {
                        const response = await fetch(`https://${domain}/api/v2/items/${itemId}/details/`, {
                            headers: {
                                Accept: "application/json"
                            }
                        });
                        if (!response.ok)
                            return 404 === response.status ? {
                                forSale: !1,
                                reason: "not_found"
                            } : {
                                forSale: !0,
                                reason: "unknown"
                            };
                        const item = (await response.json()).item;
                        return item ? item.is_draft ? {
                            forSale: !1,
                            reason: "draft"
                        } : item.is_processing ? {
                            forSale: !1,
                            reason: "processing"
                        } : "sold" === item.item_closing_action ? {
                            forSale: !1,
                            reason: "sold"
                        } : 1 == item.is_hidden || !0 === item.is_hidden ? {
                            forSale: !1,
                            reason: "hidden"
                        } : item.is_closed ? {
                            forSale: !1,
                            reason: "closed"
                        } : !1 === item.can_be_sold ? {
                            forSale: !1,
                            reason: "cannot_be_sold"
                        } : item.is_reserved ? {
                            forSale: !1,
                            reason: "reserved"
                        } : {
                            forSale: !0,
                            item: item
                        } : {
                            forSale: !1,
                            reason: "no_data"
                        }
                    } catch (error) {
                        return console.error(`[AUTO_MSG_JOB] Error checking item ${itemId}:`, error),
                        {
                            forSale: !0,
                            reason: "error"
                        }
                    }
                }(domain, itemId);
                if (!itemStatus.forSale)
                    return await markLikeProcessed(likeId),
                    void await logAutoMessage(null, like, "failed_item_" + itemStatus.reason, likerUsername, likeItemTitle, likeItemPhoto);
                itemStatus.item && (likeItemTitle = itemStatus.item.title || likeItemTitle,
                likeItemPhoto = itemStatus.item.photos?.[0]?.url || itemStatus.item.photos?.[0]?.thumbnails?.[0]?.url || likeItemPhoto);
                const settings = await chrome.storage.local.get(["autoMsg_ruleReviews", "autoMsg_minReviews", "autoMsg_delay"]);
                if (settings.autoMsg_ruleReviews) {
                    const userInfo = await getUser(likerId);
                    if (!userInfo || !userInfo.user)
                        return await markLikeProcessed(likeId),
                        void await logAutoMessage(null, like, "failed_user_fetch", likerUsername, likeItemTitle, likeItemPhoto);
                    const minReviews = parseInt(settings.autoMsg_minReviews) || 3;
                    if ((userInfo.user.feedback_count || 0) < minReviews)
                        return await markLikeProcessed(likeId),
                        void await logAutoMessage(null, like, "skipped_reviews", userInfo.user.login || likerUsername, likeItemTitle, likeItemPhoto)
                }
                const selectedTemplate = templatesForItem[autoMsg_lastTemplateIndex % templatesForItem.length];
                autoMsg_lastTemplateIndex++;
                const conversationData = await async function(domain, userId, itemId) {
                    const REFERER_RULE_ID = 9999;
                    try {
                        if (!itemId)
                            return console.error("[AUTO_MSG_JOB] âŒ itemId is required for starting conversation"),
                            null;
                        const url = `https://${domain}/api/v2/conversations`
                          , inboxPageUrl = `https://${domain}/inbox/want_it?receiver_id=${userId}&item_id=${itemId}`;
                        try {
                            await chrome.declarativeNetRequest.updateDynamicRules({
                                removeRuleIds: [REFERER_RULE_ID],
                                addRules: [{
                                    id: REFERER_RULE_ID,
                                    priority: 100,
                                    action: {
                                        type: "modifyHeaders",
                                        requestHeaders: [{
                                            header: "Referer",
                                            operation: "set",
                                            value: inboxPageUrl
                                        }]
                                    },
                                    condition: {
                                        urlFilter: `||${domain}/api/v2/conversations`,
                                        resourceTypes: ["xmlhttprequest"]
                                    }
                                }]
                            })
                        } catch (err) {}
                        let csrfToken = null;
                        try {
                            const pageResponse = await fetch(inboxPageUrl, {
                                method: "GET",
                                credentials: "include"
                            });
                            if (pageResponse.ok) {
                                const html = await pageResponse.text()
                                  , csrfMatch = html.match(/CSRF_TOKEN["':,\s]*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
                                if (csrfMatch)
                                    csrfToken = csrfMatch[1];
                                else {
                                    html.indexOf("CSRF")
                                }
                            }
                        } catch (err) {
                            console.error("[AUTO_MSG_JOB] âš ï¸ Error fetching inbox page:", err)
                        }
                        if (csrfToken || (await updateCSRF(),
                        csrfToken = x_csrf),
                        !csrfToken)
                            return console.error("[AUTO_MSG_JOB] âŒ Failed to obtain CSRF token"),
                            await chrome.declarativeNetRequest.updateDynamicRules({
                                removeRuleIds: [REFERER_RULE_ID]
                            }).catch(( () => {}
                            )),
                            null;
                        x_csrf = csrfToken;
                        let anonId = null;
                        try {
                            const cookies = await chrome.cookies.getAll({
                                domain: domain.replace("www.", ""),
                                name: "anon_id"
                            });
                            cookies.length > 0 && (anonId = cookies[0].value)
                        } catch (e) {}
                        const payload = {
                            initiator: "seller_enters_notification",
                            item_id: String(itemId),
                            opposite_user_id: String(userId)
                        }
                          , headers = {
                            accept: "application/json, text/plain, */*,image/webp",
                            "content-type": "application/json",
                            "x-csrf-token": x_csrf
                        };
                        anonId && (headers["x-anon-id"] = anonId);
                        const response = await fetch(url, {
                            method: "POST",
                            headers: headers,
                            credentials: "include",
                            body: JSON.stringify(payload)
                        })
                          , responseHeaders = {};
                        if (response.headers.forEach(( (v, k) => {
                            responseHeaders[k] = v
                        }
                        )),
                        response.ok) {
                            const successData = await response.json();
                            return await chrome.storage.local.set({
                                autoMsg_rateLimited: !1
                            }),
                            await chrome.declarativeNetRequest.updateDynamicRules({
                                removeRuleIds: [REFERER_RULE_ID]
                            }).catch(( () => {}
                            )),
                            successData
                        }
                        const errorBody = await response.text().catch(( () => ""));
                        let errorData = {};
                        try {
                            errorData = JSON.parse(errorBody)
                        } catch (e) {}
                        return console.error("[AUTO_MSG_JOB] âŒ CONVERSATION FAILED"),
                        console.error(`[AUTO_MSG_JOB] Status: ${response.status} ${response.statusText}`),
                        console.error(`[AUTO_MSG_JOB] Response body: ${errorBody}`),
                        console.error("[AUTO_MSG_JOB] Response headers:", JSON.stringify(responseHeaders, null, 2)),
                        console.error(`[AUTO_MSG_JOB] Request was: POST ${url}`),
                        console.error(`[AUTO_MSG_JOB] Payload: ${JSON.stringify(payload)}`),
                        console.error(`[AUTO_MSG_JOB] CSRF used: ${x_csrf}`),
                        console.error(`[AUTO_MSG_JOB] Inbox page URL (referer): ${inboxPageUrl}`),
                        401 === response.status || 403 === response.status ? (await chrome.declarativeNetRequest.updateDynamicRules({
                            removeRuleIds: [REFERER_RULE_ID]
                        }).catch(( () => {}
                        )),
                        {
                            accessDenied: !0
                        }) : 106 === errorData.code || "rate_limit_exceeded" === errorData.message_code ? (await chrome.storage.local.set({
                            autoMsg_rateLimited: !0,
                            autoMsg_rateLimitedAt: Date.now()
                        }),
                        await chrome.declarativeNetRequest.updateDynamicRules({
                            removeRuleIds: [REFERER_RULE_ID]
                        }).catch(( () => {}
                        )),
                        {
                            rateLimited: !0
                        }) : (await chrome.declarativeNetRequest.updateDynamicRules({
                            removeRuleIds: [REFERER_RULE_ID]
                        }).catch(( () => {}
                        )),
                        null)
                    } catch (error) {
                        return console.error("[AUTO_MSG_JOB] Error starting conversation:", error),
                        await chrome.declarativeNetRequest.updateDynamicRules({
                            removeRuleIds: [REFERER_RULE_ID]
                        }).catch(( () => {}
                        )),
                        null
                    }
                }(domain, likerId, itemId);
                if (conversationData && conversationData.rateLimited) {
                    const retryAfter = Date.now() + AUTO_MSG_RATE_LIMIT_WAIT;
                    return await chrome.storage.local.set({
                        autoMsg_rateLimited: !0,
                        autoMsg_rateLimitedAt: Date.now(),
                        autoMsg_retryAfter: retryAfter
                    }),
                    console.log(`[AUTO_MSG] âš ï¸ RATE LIMITED for ${likerUsername || likerId} - like stays PENDING, retrying in ${AUTO_MSG_RATE_LIMIT_WAIT / 1e3}s`),
                    void await logAutoMessage(selectedTemplate, like, "rate_limited", likerUsername, likeItemTitle, likeItemPhoto)
                }
                if (conversationData && conversationData.accessDenied) {
                    console.log(`[AUTO_MSG] â›” Access denied for ${likerUsername || likerId} on item ${itemId} - marking processed, skipping`),
                    await markLikeProcessed(likeId),
                    await logAutoMessage(selectedTemplate, like, "failed_access_denied", likerUsername, likeItemTitle, likeItemPhoto);
                    const settings = await chrome.storage.local.get(["autoMsg_delay"])
                      , userDelay = parseInt(settings.autoMsg_delay) || 120;
                    return autoMsg_nextAllowedTime = Date.now() + 1e3 * userDelay,
                    void console.log(`[AUTO_MSG] â±ï¸ Next message allowed in ${userDelay}s`)
                }
                if (!conversationData || !conversationData.conversation) {
                    const retryAfter = Date.now() + AUTO_MSG_CONVERSATION_FAIL_WAIT;
                    return await chrome.storage.local.set({
                        autoMsg_retryAfter: retryAfter
                    }),
                    console.log(`[AUTO_MSG] âŒ Failed to start conversation with ${likerUsername || likerId} - like stays PENDING, retrying in ${AUTO_MSG_CONVERSATION_FAIL_WAIT / 1e3}s`),
                    void await logAutoMessage(selectedTemplate, like, "failed_conversation", likerUsername, likeItemTitle, likeItemPhoto)
                }
                await chrome.storage.local.set({
                    autoMsg_rateLimited: !1,
                    autoMsg_retryAfter: 0
                });
                const conversation = conversationData.conversation
                  , conversationId = conversation.id
                  , transactionId = conversation.transaction?.id
                  , buyerName = conversation.opposite_user?.login || "User"
                  , productName = conversation.transaction?.item_title || conversation.subtitle || "Item"
                  , productPrice = conversation.transaction?.offer_price?.amount || "0";
                let messageSent = !1;
                if (selectedTemplate.hasMessage && selectedTemplate.message) {
                    const messageText = selectedTemplate.message.replace(/\{buyer_name\}/g, buyerName).replace(/\{product_name\}/g, productName).replace(/\{product_price\}/g, productPrice)
                      , messageSuccess = await async function(domain, conversationId, message) {
                        try {
                            const url = `https://${domain}/api/v2/conversations/${conversationId}/replies`
                              , response = await fetch(url, {
                                method: "POST",
                                headers: {
                                    Accept: "application/json, text/plain, */*",
                                    "Content-Type": "application/json",
                                    "x-csrf-token": x_csrf
                                },
                                credentials: "include",
                                body: JSON.stringify({
                                    reply: {
                                        body: message,
                                        photo_temp_uuids: null,
                                        is_personal_data_sharing_check_skipped: !1
                                    }
                                })
                            });
                            if (401 === response.status || 403 === response.status) {
                                x_csrf = "",
                                await updateCSRF();
                                return (await fetch(url, {
                                    method: "POST",
                                    headers: {
                                        Accept: "application/json, text/plain, */*",
                                        "Content-Type": "application/json",
                                        "x-csrf-token": x_csrf
                                    },
                                    credentials: "include",
                                    body: JSON.stringify({
                                        reply: {
                                            body: message,
                                            photo_temp_uuids: null,
                                            is_personal_data_sharing_check_skipped: !1
                                        }
                                    })
                                })).ok
                            }
                            return response.ok
                        } catch (error) {
                            return console.error("[AUTO_MSG_JOB] Error sending reply:", error),
                            !1
                        }
                    }(domain, conversationId, messageText);
                    if (!messageSuccess)
                        return await markLikeProcessed(likeId),
                        void await logAutoMessage(selectedTemplate, like, "failed_message", buyerName, productName, likeItemPhoto);
                    messageSent = !0
                }
                if (selectedTemplate.hasOffer && selectedTemplate.discount && transactionId) {
                    let itemPrice = parseFloat(productPrice) || 0
                      , itemCurrency = "EUR";
                    const itemDetails = await async function(domain, itemId) {
                        try {
                            const response = await fetch(`https://${domain}/api/v2/items/${itemId}/details/`, {
                                headers: {
                                    Accept: "application/json"
                                }
                            });
                            if (response.ok) {
                                const item = (await response.json()).item
                                  , price = parseFloat(item?.price?.amount || item?.price || 0);
                                return {
                                    price: price,
                                    currency: item?.price?.currency_code || item?.currency || "EUR",
                                    title: item?.title || "Unknown item",
                                    brand: item?.brand_dto?.title || item?.brand || "",
                                    sellerName: item?.user?.login || "",
                                    item: item
                                }
                            }
                            return null
                        } catch (error) {
                            return console.error("[AUTO_MSG_JOB] Error getting item details:", error),
                            null
                        }
                    }(domain, itemId);
                    if (itemDetails && (0 === itemPrice && (itemPrice = itemDetails.price || 0),
                    itemCurrency = itemDetails.currency || "EUR"),
                    itemPrice > 0) {
                        const discountPercent = parseInt(selectedTemplate.discount) || 10
                          , discountedPrice = Math.max(1, Math.round(itemPrice * (1 - discountPercent / 100)));
                        await async function(domain, transactionId, price, currency="EUR") {
                            try {
                                const url = `https://${domain}/api/v2/transactions/${transactionId}/offers`
                                  , response = await fetch(url, {
                                    method: "POST",
                                    headers: {
                                        Accept: "application/json, text/plain, */*",
                                        "Content-Type": "application/json",
                                        "x-csrf-token": x_csrf
                                    },
                                    credentials: "include",
                                    body: JSON.stringify({
                                        offer: {
                                            price: price.toString(),
                                            currency: currency
                                        }
                                    })
                                });
                                if (401 === response.status || 403 === response.status) {
                                    x_csrf = "",
                                    await updateCSRF();
                                    return (await fetch(url, {
                                        method: "POST",
                                        headers: {
                                            Accept: "application/json, text/plain, */*",
                                            "Content-Type": "application/json",
                                            "x-csrf-token": x_csrf
                                        },
                                        credentials: "include",
                                        body: JSON.stringify({
                                            offer: {
                                                price: price.toString(),
                                                currency: currency
                                            }
                                        })
                                    })).ok
                                }
                                return response.ok
                            } catch (error) {
                                return console.error("[AUTO_MSG_JOB] Error sending offer:", error),
                                !1
                            }
                        }(domain, transactionId, discountedPrice, itemCurrency)
                    }
                }
                await markLikeProcessed(likeId);
                const {autoMsg_sentToday: currentSent} = await chrome.storage.local.get("autoMsg_sentToday");
                if (await chrome.storage.local.set({
                    autoMsg_sentToday: (currentSent || 0) + 1
                }),
                await logAutoMessage(selectedTemplate, like, "sent", buyerName, productName, likeItemPhoto),
                console.log(`[AUTO_MSG] âœ… SUCCESS! Sent ${(currentSent || 0) + 1}/${dailyLimit} today`),
                messageSent) {
                    const userDelay = parseInt(settings.autoMsg_delay) || 120;
                    autoMsg_nextAllowedTime = Date.now() + 1e3 * userDelay,
                    console.log(`[AUTO_MSG] â±ï¸ Next message allowed in ${userDelay}s`)
                }
            } catch (error) {
                console.error("[AUTO_MSG] âŒ Cycle error:", error)
            } finally {
                autoMsg_busy = !1
            }
        }
    }
    async function markLikeProcessed(likeId) {
        try {
            const {autoMsg_processedLikes: autoMsg_processedLikes} = await chrome.storage.local.get("autoMsg_processedLikes")
              , processedLikes = autoMsg_processedLikes || [];
            if (!processedLikes.includes(likeId)) {
                processedLikes.push(likeId);
                const trimmed = processedLikes.slice(-1e3);
                await chrome.storage.local.set({
                    autoMsg_processedLikes: trimmed
                })
            }
        } catch (error) {
            console.error("[AUTO_MSG] Error marking processed:", error)
        }
    }
    async function logAutoMessage(template, like, status, username, itemTitle, itemPhoto) {
        try {
            const {autoMsg_messageLog: autoMsg_messageLog} = await chrome.storage.local.get("autoMsg_messageLog")
              , messageLog = autoMsg_messageLog || []
              , itemId = like?.subject_id || like?.item_id || "unknown"
              , userId = like?.liker_id || like?.initiator?.id || "unknown"
              , logEntry = {
                id: Date.now().toString(),
                templateId: template?.id || null,
                templateName: template?.name || "N/A",
                userId: userId,
                username: username || "Unknown",
                itemId: itemId,
                itemTitle: itemTitle || "Unknown item",
                itemPhoto: itemPhoto || null,
                hasMessage: template?.hasMessage || !1,
                hasOffer: template?.hasOffer || !1,
                discount: template?.discount || null,
                status: status,
                timestamp: Date.now()
            };
            messageLog.unshift(logEntry);
            const trimmedLog = messageLog.slice(0, 50);
            await chrome.storage.local.set({
                autoMsg_messageLog: trimmedLog
            })
        } catch (error) {
            console.error("[AUTO_MSG] Error logging message:", error)
        }
    }
    !async function() {
        try {
            const {auto_messages_enabled: auto_messages_enabled, autoMessagesConsent: autoMessagesConsent} = await chrome.storage.local.get(["auto_messages_enabled", "autoMessagesConsent"]);
            auto_messages_enabled && autoMessagesConsent && startAutoMessagesJob()
        } catch (error) {
            console.error("[AUTO_MSG_JOB] Error initializing:", error)
        }
    }(),
    chrome.storage.onChanged.addListener(( (changes, areaName) => {
        if ("local" === areaName && changes.auto_messages_enabled) {
            changes.auto_messages_enabled.newValue ? startAutoMessagesJob() : (console.log("[AUTO_MSG] ðŸ›‘ Stopping Auto Messages job..."),
            autoMsg_interval && (clearInterval(autoMsg_interval),
            autoMsg_interval = null))
        }
    }
    ))
}();