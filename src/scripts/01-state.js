/* Cisco UI catalog — chunk 1: setup, SI, state, helpers, filter core */
if (typeof EQUIPMENT === 'undefined') window.EQUIPMENT = [];
if (typeof CAT_META === 'undefined') window.CAT_META = {};
if (typeof CAT_GROUPS === 'undefined') window.CAT_GROUPS = {};
if (typeof FILTER_FACETS === 'undefined') window.FILTER_FACETS = {};
if (typeof DATA === 'undefined') window.DATA = [];

var SITE = Object.assign({
  heroBadge: "> Splunk Solutions Engineering", heroTitle: "Use Case Repository", heroTitleSpan: "for Splunk",
  heroIntro: "A curated path through {useCases} use cases across {categories} infrastructure domains.",
  statUseCases: "Use Cases", statCategories: "Categories", statSubcategories: "Subcategories", statQuickWins: "Quick Wins",
  roadmapTitle: "Implementation Roadmap", roadmapSub: "A phased approach to building comprehensive infrastructure monitoring",
  phase1Title: "Phase 1", phase1Heading: "Foundation", phase1Desc: "Deploy forwarders and start collecting data for immediate visibility.",
  phase2Title: "Phase 2", phase2Heading: "Core Monitoring", phase2Desc: "Expand data collection and build dashboards for critical infrastructure.",
  phase3Title: "Phase 3", phase3Heading: "Expand Coverage", phase3Desc: "Bring in cloud, application, and database monitoring for full-stack visibility.",
  phase4Title: "Phase 4", phase4Heading: "Optimize & Automate", phase4Desc: "Add ML-driven anomaly detection, automated remediation, and executive reporting.",
  filterAll: "All Categories", siteAuthor: "", siteRepoUrl: "https://github.com/fenre/splunk-monitoring-use-cases"
}, window.SITE_CUSTOM || {});

var EQUIPMENT_GROUPS = window.EQUIPMENT_GROUPS || [];

var SI = {
  magnifier: '<path fill-rule="evenodd" clip-rule="evenodd" d="M15.05 16.46c-1.26.97-2.84 1.54-4.55 1.54C6.36 18 3 14.64 3 10.5S6.36 3 10.5 3 18 6.36 18 10.5c0 1.71-.57 3.29-1.54 4.55l4.24 4.24a1 1 0 0 1-1.41 1.41l-4.24-4.24ZM16 10.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0Z"/>',
  chevronRight: '<path fill-rule="evenodd" clip-rule="evenodd" d="M14.79 12 8.49 5.7a1 1 0 0 1 1.41-1.41l6.65 6.65a1.5 1.5 0 0 1 0 2.12l-6.65 6.65a1 1 0 0 1-1.41-1.41L14.79 12Z"/>',
  chevronDown: '<path fill-rule="evenodd" clip-rule="evenodd" d="M12 14.79l6.3-6.3a1 1 0 0 1 1.41 1.42l-6.65 6.65a1.5 1.5 0 0 1-2.12 0L4.29 9.9a1 1 0 0 1 1.41-1.41L12 14.79Z"/>',
  cross: '<path d="M6.7 5.3a1 1 0 0 0-1.41 1.41L10.59 12l-5.3 5.3a1 1 0 1 0 1.42 1.41L12 13.41l5.3 5.3a1 1 0 0 0 1.41-1.42L13.41 12l5.3-5.3a1 1 0 0 0-1.42-1.41L12 10.59 6.7 5.3Z"/>',
  list: '<path d="M3.5 7.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"/><path d="M8 6a1 1 0 0 1 1-1h12a1 1 0 1 1 0 2H9a1 1 0 0 1-1-1Z"/><path d="M9 11a1 1 0 1 0 0 2h12a1 1 0 1 0 0-2H9Z"/><path d="M9 17a1 1 0 1 0 0 2h12a1 1 0 1 0 0-2H9Z"/><path d="M3.5 13.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"/><path d="M5 18a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z"/>',
  external: '<path fill-rule="evenodd" clip-rule="evenodd" d="M14 5a1 1 0 0 1 1-1h4a2 2 0 0 1 2 2v4a1 1 0 1 1-2 0V7.41l-7.29 7.3a1 1 0 0 1-1.42-1.42L17.59 6H15a1 1 0 0 1-1-1ZM5 7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4a1 1 0 1 0-2 0v4H5V9h4a1 1 0 0 0 0-2H5Z"/>',
  monitor: '<path fill-rule="evenodd" clip-rule="evenodd" d="M5.5 2.97H18.5A2.5 2.5 0 0 1 21 5.47v9a2.5 2.5 0 0 1-2.5 2.5H15V19h2a1 1 0 1 1 0 2H7a1 1 0 1 1 0-2h2v-2.03H5.5a2.5 2.5 0 0 1-2.5-2.5v-9a2.5 2.5 0 0 1 2.5-2.5ZM11 19h2v-2h-2v2ZM5.5 4.97a.5.5 0 0 0-.5.5v9a.5.5 0 0 0 .5.5h13a.5.5 0 0 0 .5-.5v-9a.5.5 0 0 0-.5-.5h-13Z"/>',
  cloudNodes: '<path d="M19.21 8.31C18.59 5.98 16.15 3 12 3 9.68 3 7.88 4.03 6.66 5.26 5.97 5.95 5.43 6.75 5.08 7.5h6.69a2.5 2.5 0 1 1 0 3H2.75C1.74 10.45 1 11.83 1 13.5c0 1.33.45 2.7 1.38 3.75C3.32 18.32 4.72 19 6.5 19h11c1.74 0 3.14-.59 4.1-1.64.61-.67 1.01-1.49 1.22-2.36H9.73a2.5 2.5 0 1 1 0-3h13.25c-.11-1.32-.73-2.42-1.51-3.23a6.84 6.84 0 0 0-2.26-1.46Z"/>',
  container: '<path fill-rule="evenodd" clip-rule="evenodd" d="M4.5 4A1.5 1.5 0 0 0 3 5.5v13A1.5 1.5 0 0 0 4.5 20h15a1.5 1.5 0 0 0 1.5-1.5v-13A1.5 1.5 0 0 0 19.5 4h-15ZM9 9a1 1 0 1 0-2 0v6a1 1 0 1 0 2 0V9Zm3-1a1 1 0 0 1 1 1v6a1 1 0 1 1-2 0V9a1 1 0 0 1 1-1Zm4 0a1 1 0 0 1 1 1v6a1 1 0 1 1-2 0V9a1 1 0 0 1 1-1Z"/>',
  globe: '<path fill-rule="evenodd" clip-rule="evenodd" d="M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Zm-2.06 1a8.01 8.01 0 0 1-5.38 6.58c.97-2.06 1.53-4.3 1.63-6.58h3.75Zm-5.76 7A15.9 15.9 0 0 0 14.18 13H9.82c.12 2.47.84 4.87 2.11 7h.14Zm-4.63-.42A8.01 8.01 0 0 1 4.06 13h3.76a15.9 15.9 0 0 0 1.63 6.58ZM9.82 11h4.36A15.87 15.87 0 0 0 12.07 4H12c-.03 0-.05 0-.07 0a15.87 15.87 0 0 0-2.11 7Zm-.38-6.58A15.87 15.87 0 0 0 7.82 11H4.06a8.01 8.01 0 0 1 5.38-6.58ZM19.94 11h-3.76a15.87 15.87 0 0 0-1.62-6.58A8.01 8.01 0 0 1 19.94 11Z"/>',
  networkDevices: '<path fill-rule="evenodd" clip-rule="evenodd" d="M20 4.5A1.5 1.5 0 0 0 18.5 3h-13A1.5 1.5 0 0 0 4 4.5v10A1.5 1.5 0 0 0 5.5 16H11v1.17A3 3 0 0 0 9.17 19H4a1 1 0 1 0 0 2h5.17a3 3 0 0 0 5.66 0H20a1 1 0 1 0 0-2h-5.17A3 3 0 0 0 13 17.17V16h5.5a1.5 1.5 0 0 0 1.5-1.5v-10ZM7.9 7.7a1.2 1.2 0 1 1 0-2.4 1.2 1.2 0 0 1 0 2.4Zm0 6a1.2 1.2 0 1 1 0-2.4 1.2 1.2 0 0 1 0 2.4ZM10.8 20a1.2 1.2 0 0 1 1.2-1.2 1.2 1.2 0 1 1-1.2 1.2Z"/>',
  layersTriple: '<path fill-rule="evenodd" clip-rule="evenodd" d="M13.27 2.92a2.5 2.5 0 0 0-2.54 0L3.84 5.6c-1.28.5-1.28 2.3 0 2.8l6.9 2.68a2.5 2.5 0 0 0 2.54 0l6.9-2.68c1.27-.5 1.27-2.3 0-2.8l-6.9-2.68Zm-.73 1.86a1 1 0 0 1 1.09 0L18.24 7l-5.7 2.22a1 1 0 0 1-1.09 0L5.76 7l5.78-2.22Z"/><path d="M17.33 11.65l2.76-1.08.07.03c1.28.5 1.28 2.3 0 2.8l-6.9 2.68a2.5 2.5 0 0 1-2.54 0l-6.9-2.68c-1.27-.5-1.27-2.3 0-2.8l.08-.03 2.76 1.07-.91.35 5.7 2.22a1 1 0 0 0 1.09 0l5.7-2.22-.91-.36Z"/><path d="M17.33 16.65l2.76-1.08.07.03c1.28.5 1.28 2.3 0 2.8l-6.9 2.68a2.5 2.5 0 0 1-2.54 0l-6.9-2.68c-1.27-.5-1.27-2.3 0-2.8l.08-.03 2.76 1.07-.91.35 5.7 2.22a1 1 0 0 0 1.09 0l5.7-2.22-.91-.36Z"/>',
  table: '<path fill-rule="evenodd" clip-rule="evenodd" d="M1 6.5A1.5 1.5 0 0 1 2.5 5h19A1.5 1.5 0 0 1 23 6.5v11a1.5 1.5 0 0 1-1.5 1.5h-19A1.5 1.5 0 0 1 1 17.5v-11ZM13 13v4h8v-4H13Zm8-2H13V7h8v4ZM3 11h8V7H3v4Zm8 6H3v-4h8v4Z"/>',
  cog: '<path fill-rule="evenodd" clip-rule="evenodd" d="M8.93 3.09A1.5 1.5 0 0 1 10.38 2h3.25a1.5 1.5 0 0 1 1.44 1.09l.69 2.41 2.43-.61a1.5 1.5 0 0 1 1.7.7l1.62 2.81a1.5 1.5 0 0 1-.22 1.79L19.51 12l1.74 1.8a1.5 1.5 0 0 1 .22 1.79l-1.62 2.81a1.5 1.5 0 0 1-1.7.7l-2.43-.6-.69 2.41a1.5 1.5 0 0 1-1.44 1.09h-3.25a1.5 1.5 0 0 1-1.44-1.09l-.69-2.41-2.43.61a1.5 1.5 0 0 1-1.7-.7l-1.62-2.82a1.5 1.5 0 0 1 .22-1.79L4.49 12 2.75 10.2a1.5 1.5 0 0 1-.22-1.8l1.62-2.8a1.5 1.5 0 0 1 1.7-.71l2.43.61.69-2.41ZM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/>',
  key: '<path fill-rule="evenodd" clip-rule="evenodd" d="M10 9a6 6 0 1 1 3.71 5.55l-.5 1.82a1.5 1.5 0 0 1-1.05 1.05l-1.95.53-.62 1.98a1.5 1.5 0 0 1-1.67 1.05l-4.7-.75a1.37 1.37 0 0 1-.83-2.54L10.08 9.99A6 6 0 0 1 10 9Zm6.2 1.27a1.4 1.4 0 1 0 0-2.8 1.4 1.4 0 0 0 0 2.8Z"/>',
  shield: '<path fill-rule="evenodd" clip-rule="evenodd" d="M11.19 2.33a1.5 1.5 0 0 1 1.62 0c.94.58 4.03 2.39 6.95 2.92a1.5 1.5 0 0 1 1.24 1.5c-.05 5.17-.92 8.45-2.48 10.72-1.56 2.27-3.72 3.37-5.9 4.35a1.5 1.5 0 0 1-1.22 0c-2.19-.98-4.35-2.08-5.91-4.35-1.56-2.27-2.44-5.55-2.48-10.72a1.5 1.5 0 0 1 1.24-1.5c2.92-.54 6.01-2.34 6.95-2.92ZM12 4.18c-1.15.7-4.05 2.33-6.99 2.96.09 4.74.93 7.45 2.12 9.2C8.32 18.06 9.94 18.97 12 19.9c2.06-.93 3.68-1.84 4.87-3.56 1.2-1.74 2.04-4.46 2.12-9.2-2.94-.63-5.85-2.26-7-2.96Z"/>',
  envelope: '<path fill-rule="evenodd" clip-rule="evenodd" d="M19.73 4H4.27C3.02 4 2 5.12 2 6.5v10.99C2 18.88 3.02 20 4.27 20h15.46C20.98 20 22 18.88 22 17.5V6.5C22 5.12 20.98 4 19.73 4ZM3.82 7.32V17.5c0 .28.2.5.45.5h15.45c.25 0 .45-.22.45-.5V7.33l-7.23 6.33a1.5 1.5 0 0 1-1.9 0L3.82 7.32ZM18.67 6H5.34L12 11.86 18.67 6Z"/>',
  nodeBranch: '<path fill-rule="evenodd" clip-rule="evenodd" d="M5 4a3 3 0 0 0-3 3 3 3 0 0 0 2.77 1.15c1.39.36 2.42 1.62 2.42 3.12v2.09c0 2.14 1.37 3.96 3.28 4.63.18 1.49 1.44 2.65 2.98 2.65a3 3 0 1 0-2.53-4.62c-1.02-.45-1.73-1.47-1.73-2.66v-2.09c0-1.22-.42-2.33-1.11-3.22h5.08a3 3 0 0 0 5.86-.98 3 3 0 0 0-5.86-.99H7.84A3 3 0 0 0 5 4Z"/>',
  monitorChart: '<path fill-rule="evenodd" clip-rule="evenodd" d="M5.5 2.97H18.5A2.5 2.5 0 0 1 21 5.47v9A2.5 2.5 0 0 1 18.5 16.97H15V19h2a1 1 0 1 1 0 2H7a1 1 0 1 1 0-2h2v-2.03H5.5A2.5 2.5 0 0 1 3 14.47v-9a2.5 2.5 0 0 1 2.5-2.5ZM13 17v2h-2v-2h2ZM14 7a1 1 0 0 1 1 1v5h-2V8a1 1 0 0 1 1-1Zm-4 2a1 1 0 0 1 1 1v3H9v-3a1 1 0 0 1 1-1Z"/>',
  factory: '<path fill-rule="evenodd" clip-rule="evenodd" d="M4 9.46V4.75A1.75 1.75 0 0 1 5.75 3h2.5C9.22 3 10 3.78 10 4.75v2.04l.54-.24a1.5 1.5 0 0 1 2.46 1.6V9.46L14.04 9H14V4.75A1.75 1.75 0 0 1 15.75 3h2.5c.97 0 1.75.78 1.75 1.75v1.67C21.02 6.27 22 7.05 22 8.15v11.1c0 .97-.78 1.75-1.75 1.75H3.75A1.75 1.75 0 0 1 2 19.25v-7.76c0-.69.41-1.32 1.04-1.6L4 9.46Z"/>',
  buildings: '<path fill-rule="evenodd" clip-rule="evenodd" d="M4 4.5A1.5 1.5 0 0 1 5.5 3h9A1.5 1.5 0 0 1 16 4.5V7h-4.5A1.5 1.5 0 0 0 10 8.5V19h2V9h8v10h1a1 1 0 1 1 0 2H3a1 1 0 1 1 0-2h1V4.5ZM6 9h2V7H6v2Zm8 4v-2h4v2h-4Zm0 4v-2h4v2h-4ZM6 17h2v-2H6v2Zm2-4H6v-2h2v2Z"/>',
  clipboard: '<path fill-rule="evenodd" clip-rule="evenodd" d="M8.36 3.15A2 2 0 0 1 9.82 2.02h3.94a2 2 0 0 1 1.45 1.13l.22.85h2.85A1.5 1.5 0 0 1 19.78 5.5v15c0 .83-.67 1.5-1.5 1.5H5.28a1.5 1.5 0 0 1-1.5-1.5v-15c0-.83.67-1.5 1.5-1.5h2.87l.21-.85Zm1.85.87l-.37 1.47h3.91l-.37-1.47h-3.17ZM8.78 10a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-6Zm0 4a1 1 0 1 0 0 2h3a1 1 0 1 0 0-2h-3Z"/>',
  lock: '<path fill-rule="evenodd" clip-rule="evenodd" d="M6.94 7.06V9.91H5.89A2 2 0 0 0 3.89 11.91v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-1.02V7.06a4.96 4.96 0 1 0-9.93 0Zm4.96-2.96a2.96 2.96 0 0 0-2.96 2.96v2.85h5.93V7.06a2.96 2.96 0 0 0-2.97-2.96ZM11.89 18a1 1 0 0 1-1-1v-2a1 1 0 1 1 2 0v2a1 1 0 0 1-1 1Z"/>',
  nodeNetwork: '<path fill-rule="evenodd" clip-rule="evenodd" d="M19 8a3 3 0 1 0-2.71-4.71L14.29 5.29A3 3 0 0 0 13 5c-.79 0-1.5.3-2.04.8L7.94 3.91a3 3 0 1 0-3.81 3.47l.31 3.07A3 3 0 0 0 3 13a3 3 0 0 0 6 0 3 3 0 0 0-.13-.88l2.45-1.63A3 3 0 0 0 13 11c.16 0 .32-.01.47-.04l2.28 3.05A3 3 0 1 0 21 16a3 3 0 0 0-3.47-2.96l-2.29-3.05A3 3 0 0 0 16 8c0-.46-.1-.9-.29-1.29l2-2A3 3 0 0 0 19 5a3 3 0 0 0 0-3Z"/>',
  servers: '<path fill-rule="evenodd" clip-rule="evenodd" d="M20 4.5A1.5 1.5 0 0 0 18.5 3h-13A1.5 1.5 0 0 0 4 4.5v5A1.5 1.5 0 0 0 5.5 11h13A1.5 1.5 0 0 0 20 9.5v-5ZM7.2 7a1.2 1.2 0 1 0 2.4 0 1.2 1.2 0 0 0-2.4 0Z"/><path fill-rule="evenodd" clip-rule="evenodd" d="M20 14.5a1.5 1.5 0 0 0-1.5-1.5h-13A1.5 1.5 0 0 0 4 14.5v5A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5v-5ZM7.2 17a1.2 1.2 0 1 0 2.4 0 1.2 1.2 0 0 0-2.4 0Z"/>',
  data: '<path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C7.58 2 4 3.79 4 6v12c0 2.21 3.58 4 8 4s8-1.79 8-4V6c0-2.21-3.58-4-8-4Zm6 4c0 .62-1.14 1.4-2.87 1.87A16.4 16.4 0 0 1 12 8.2c-1.11 0-2.17-.11-3.13-.33C7.14 7.4 6 6.62 6 6s1.14-1.4 2.87-1.87C9.83 3.8 10.89 3.68 12 3.68c1.11 0 2.17.11 3.13.33C16.86 4.6 18 5.38 18 6ZM6 8.65V12c0 .62 1.14 1.4 2.87 1.87.96.24 2.02.36 3.13.36s2.17-.12 3.13-.36C16.86 13.4 18 12.62 18 12V8.65c-.55.36-1.24.67-2.02.91A17.8 17.8 0 0 1 12 10.07c-1.44 0-2.81-.17-4-.51-.77-.24-1.46-.55-2-.91ZM6 18V14.65c.55.36 1.24.67 2.02.91 1.18.34 2.55.51 3.98.51s2.8-.17 3.98-.51c.78-.24 1.47-.55 2.02-.91V18c0 .62-1.14 1.4-2.87 1.87-.96.24-2.02.36-3.13.36s-2.17-.12-3.13-.36C7.14 19.4 6 18.62 6 18Z"/>',
  dollarMark: '<path d="M13 3a1 1 0 1 0-2 0v2.07a6.7 6.7 0 0 0-.7.11l-.12.03a4.5 4.5 0 0 0-1.44.62l-.13.09c-.32.21-.61.47-.85.78a3.5 3.5 0 0 0-.67 1.41l-.01.03c-.11.51-.1 1.03.03 1.53.17.66.54 1.26 1.06 1.7l.04.03c.22.19.47.36.73.49l.24.12c.36.18.74.31 1.13.41l.73.18 1.25.23.77.15V21a1 1 0 1 0 2 0v-2.03c.27-.03.54-.08.8-.15l.19-.05c.41-.11.8-.28 1.16-.5l.09-.06c.41-.25.77-.58 1.05-.97.37-.5.6-1.1.68-1.73V3Z"/>',
  chart: '<path d="M4 5a1 1 0 0 1 1 1v11h15a1 1 0 1 1 0 2H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z"/><path d="M7 13a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v3H7v-3Zm5-3a1 1 0 0 0-1 1v5h3v-5a1 1 0 0 0-1-1h-1Zm3 1a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v5h-3v-5Zm4-4a1 1 0 0 0-1-1h-1a1 1 0 0 0-1 1v2h3V7Z"/>',
  download: '<path d="M12 3a1 1 0 0 1 1 1v9.59l3.3-3.3a1 1 0 1 1 1.4 1.42l-5 5a1 1 0 0 1-1.4 0l-5-5a1 1 0 1 1 1.4-1.42L11 13.59V4a1 1 0 0 1 1-1Z"/><path d="M4 17a1 1 0 0 1 1 1v1h14v-1a1 1 0 1 1 2 0v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1Z"/>'
};
function si(name, cls) {
  return '<svg class="si' + (cls ? ' ' + cls : '') + '" viewBox="0 0 24 24" aria-hidden="true">' + (SI[name] || '') + '</svg>';
}

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function stripMd(s) {
  if (!s) return '';
  return String(s).replace(/`([^`]+)`/g, '$1').replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
}
function linkify(s) {
  var t = esc(s);
  t = t.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  t = t.replace(/(^|[\s(])(https?:\/\/[^\s)<]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
  return t;
}
function linkifyRefs(s) {
  if (!s) return '';
  var t = String(s);
  t = t.replace(/`([^`]+)`/g, '$1').replace(/\*\*([^*]+)\*\*/g, '$1');
  var parts = t.split(/,\s*/);
  var out = [];
  parts.forEach(function (p) {
    var m = p.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (m) {
      var label = esc(m[1]), url = m[2];
      if (/^docs\/guides\/[\w-]+\.md/i.test(url)) {
        out.push('<a href="guide-reader.html?src=' + encodeURIComponent(url) + '">' + label + '</a>');
      } else if (/^https?:\/\//i.test(url)) {
        out.push('<a href="' + esc(url) + '" target="_blank" rel="noopener">' + label + '</a>');
      } else {
        out.push('<a href="' + esc(url) + '">' + label + '</a>');
      }
    } else {
      out.push(esc(p));
    }
  });
  return out.join(', ');
}

var CRIT_ORDER = {critical:0, high:1, medium:2, low:3};
var DIFF_ORDER = {beginner:0, intermediate:1, advanced:2, expert:3};
var SIDEBAR_GROUP_LABELS = { infra:'Infrastructure', security:'Security', cloud:'Cloud & Containers', app:'Applications', industry:'Industry Verticals', compliance:'Regulatory & Compliance', business:'Business & Executive' };

var allUCs = [];
var ucIndex = {};
var _cachedRegKeys = [];
var _cachedMtypes = [];
// Phase 3a — clause-level regulation facet.
// ``_cachedClausesByReg[regName]`` → sorted array of unique clause strings
// (``"{version}#{clause}"`` canonical form). The UI renders a second-level
// dropdown from this map when the user has picked a regulation that
// actually has per-clause compliance rows. Populated from the compact
// ``uc.cmp[]`` array materialised by build.py's sidecar merge.
var _cachedClausesByReg = {};

function __bootstrapCatalogState() {
  allUCs.length = 0;
  Object.keys(ucIndex).forEach(function(k) { delete ucIndex[k]; });
  (window.DATA || []).forEach(function(cat) {
    (cat.s || []).forEach(function(sc) {
      (sc.u || []).forEach(function(uc) {
        var entry = { cat: cat, sc: sc, uc: uc, flatIdx: allUCs.length };
        var blob = [uc.n, uc.i, uc.v, uc.q, uc.t, uc.d, cat.n, sc.n].join(' ');
        if (Array.isArray(uc.a)) blob += ' ' + uc.a.join(' ');
        if (Array.isArray(uc.mtype)) blob += ' ' + uc.mtype.join(' ');
        if (Array.isArray(uc.regs)) blob += ' ' + uc.regs.join(' ');
        if (Array.isArray(uc.cmp)) {
          // Fold clause ids ("Art.5", "§164.312(b)") into the search blob
          // so an auditor typing "Art.5" or "164.312" lands on the right UC.
          uc.cmp.forEach(function(row) { if (row && row.cl) blob += ' ' + row.cl; });
        }
        if (uc.hw) blob += ' ' + uc.hw;
        if (uc.escu) blob += ' escu enterprise security content detection';
        if (uc.escu_rba) blob += ' rba risk based alerting';
        entry._searchBlob = blob.toLowerCase();
        allUCs.push(entry);
        ucIndex[uc.i] = entry;
      });
    });
  });
  __recomputeCachedFacets();
  __rebuildEqById();
}

function __recomputeCachedFacets() {
  var regSet = {};
  allUCs.forEach(function(e) { if (Array.isArray(e.uc.regs)) e.uc.regs.forEach(function(r) { regSet[r] = 1; }); });
  _cachedRegKeys = Object.keys(regSet).sort();

  // Rebuild the per-regulation clause facet from the compact
  // ``uc.cmp[]`` rows. Each row carries regulation + version + clause so
  // we can offer an auditor-facing clause dropdown that is scoped to
  // whichever framework they've picked in the first dropdown. Clauses
  // are stored in their canonical ``{version}#{clause}`` form so the
  // same clause string under two different versions shows up as two
  // separate options (regulators often renumber clauses between
  // revisions and conflating them would silently mask coverage gaps).
  var clauseMap = Object.create(null);
  allUCs.forEach(function(e) {
    var cmp = e.uc.cmp;
    if (!Array.isArray(cmp)) return;
    cmp.forEach(function(row) {
      if (!row || !row.r || !row.cl || !row.v) return;
      var reg = row.r;
      var canonical = row.v + '#' + row.cl;
      if (!clauseMap[reg]) clauseMap[reg] = Object.create(null);
      clauseMap[reg][canonical] = 1;
    });
  });
  _cachedClausesByReg = {};
  Object.keys(clauseMap).forEach(function(reg) {
    _cachedClausesByReg[reg] = Object.keys(clauseMap[reg]).sort(function(a, b) {
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
    });
  });

  var mtypes = new Set();
  allUCs.forEach(function(e) { if (Array.isArray(e.uc.mtype)) e.uc.mtype.forEach(function(t) { mtypes.add(t); }); });
  var mtOrder = ['Availability','Performance','Security','Configuration','Capacity','Fault','Anomaly','Compliance'];
  _cachedMtypes = Array.from(mtypes).sort(function(a, b) {
    var ia = mtOrder.indexOf(a), ib = mtOrder.indexOf(b);
    if (ia >= 0 && ib >= 0) return ia - ib;
    if (ia >= 0) return -1;
    if (ib >= 0) return 1;
    return a.localeCompare(b);
  });
}

var currentCat = null;
var currentSubcat = null;
var catShowAllUCs = false;
var currentSearch = '';
var searchShowAll = false;
var currentPillarFilter = 'all';
var currentFilter = 'all';
var currentDiffFilter = 'all';
var currentStatusFilter = 'all';
var currentFreshFilter = 'all';
var currentRegulationFilter = 'all';
// Phase 3a — second-level filter scoped to the currently selected
// regulation. Stored in canonical ``{version}#{clause}`` form so the
// filter logic can split back into (version, clause) without extra
// lookups. Reset to ``'all'`` whenever the top-level regulation changes.
var currentClauseFilter = 'all';
var currentMtypeFilter = 'all';
var currentIndustryFilter = 'all';
var currentEscuFilter = 'all';
var currentDtypeFilter = 'all';
var currentPremiumFilter = 'all';
var currentCimFilter = 'all';
var currentSappFilter = 'all';
var currentMitreFilter = '';
var currentMitreTacticFilter = '';
var currentDsGroup = '';
var currentDatasourceFilter = '';
var currentTrendFilter = false;
var selectedEquipmentId = '';
var inventorySelections = [];
var _invTempSelections = new Set();
var INVENTORY_STORAGE_KEY = 'uc-inventory';
var selectedUCIds = new Set();
var UC_SELECTION_STORAGE_KEY = 'uc-selected-ucs';
var advFiltersOpen = false;
var nonTechnicalView = false;
var ovGroupFilter = 'all';
var ovHeroGroupFilter = null;
var expandedSidebarGroups = new Set();
var sidebarManualToggle = false;

var panelUCList = [];
var panelIdx = -1;
var panelOpen = false;
var currentDisplayedList = [];

var currentSort = 'criticality';
try { var _ss = localStorage.getItem('uc-sort-pref'); if (_ss) currentSort = _ss; } catch (e) {}

var _eqById = {};
function __rebuildEqById() {
  Object.keys(_eqById).forEach(function(k) { delete _eqById[k]; });
  (window.EQUIPMENT || []).forEach(function(eq) { if (eq && eq.id != null) _eqById[eq.id] = eq; });
}
__rebuildEqById();

var ucRenderBatch = 50;
var ucRenderedCount = 0;
var ucScrollObserver = null;
var ucAllCardsHtml = [];
var ucGridTargets = [];
