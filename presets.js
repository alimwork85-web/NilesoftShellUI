// ثيمات جاهزة. كل ثيم يُبنى من مجموعة ألوان قليلة.
function makeTheme(id, c, extra) {
  const t = {
    name: id,
    view: "view.small",
    background: { color: c.bg, opacity: 100, effect: 0 },
    item: {
      opacity: 100, radius: 2, prefix: 1,
      text: { normal: c.text, select: c.textSel || c.text, "normal-disabled": c.dis, "select-disabled": c.dis },
      back: { normal: c.bg, select: c.sel, "normal-disabled": c.bg, "select-disabled": c.selDis || c.sel },
      padding: { left: 12, top: 4, right: 12, bottom: 4 },
      margin: { left: 4, top: 2, right: 4, bottom: 2 },
    },
    font: { size: 18, name: "Segoe UI Variable Text", weight: 4, italic: 0 },
    border: { enabled: true, size: 1, color: c.border, opacity: 100, radius: 3 },
    shadow: { enabled: true, size: 8, opacity: c.shadowOp || 20, color: c.shadow || "#11111B" },
    separator: { size: 1, color: c.sep },
    symbol: { normal: c.sym, select: c.accent, "normal-disabled": c.dis, "select-disabled": c.dis },
    image: { enabled: true, color: [c.icon || c.text, c.accent, c.bg] },
  };
  return Object.assign(t, extra || {});
}

// ثيم متدرج: الخلفية من gradient، وخلفية العنصر العادي تُحذف حتى لا تغطي التدرج
function tealGradient() {
  const t = makeTheme("teal-gradient", {
    bg: "#148C8C", text: "#FFFFFF", dis: "#8BABAB", sel: "#2A9C9C", selDis: "#1E7A7A",
    border: "#126666", sep: "#1A6A6A", sym: "#FAFDFD", accent: "#4CC2FF", icon: "#E0DFDF",
    shadow: "#000000", shadowOp: 40 });
  delete t.item.back.normal;
  delete t.item.back["normal-disabled"];
  t.shadow.size = 14;
  t.font.size = 17;
  // Shell يقبل gradient داخل background فقط
  t.background.gradient = { enabled: true, linear: [0, 0, 0, 100], stop: [["0.0", "#1BA0A0"], ["1.0", "#1E3A3A"]] };
  return t;
}

// زجاجي: أكريليك شفاف، نص أبيض أكبر. خلفية العنصر العادي تُترك لـ Shell
function glass() {
  const t = makeTheme("glass", {
    bg: "#2E2E50", text: "#FFFFFF", dis: "#9595A7", sel: "#3C3C60", selDis: "#34344F",
    border: "#3A3A60", sep: "#3A3A5C", sym: "#E0E0EA", accent: "#4CC2FF", icon: "#E0DFDF",
    shadow: "#000000", shadowOp: 30 });
  delete t.item.back.normal;
  // بدون هذا يرسم Shell شريطًا رماديًا خلف العناصر المعطّلة
  t.item.back["normal-disabled"] = "color.transparent";
  Object.assign(t.background, { opacity: 70, effect: 3 });
  Object.assign(t.font, { size: 20, weight: 5 });
  Object.assign(t.item.padding, { top: 5, bottom: 5 });
  t.border.radius = 2;
  t.shadow.size = 10;
  t.symbol.select = "#FFFFFF";
  return t;
}

const PRESETS = [
  { id: "glass", ar: "زجاجي", en: "Glass", theme: glass() },
  { id: "reference-dark", ar: "ثيمك المرجعي (داكن)", en: "Your reference (dark)",
    theme: makeTheme("reference-dark", {
      bg: "#24283B", text: "#D7DCF3", textSel: "#E6E9F8", dis: "#6B7089", sel: "#494C64", selDis: "#2E3248",
      border: "#BB9AF7", sep: "#34384B", sym: "#9A96BE", accent: "#BB9AF7", icon: "#D7DCF3" }) },
  { id: "reference-light", ar: "ثيمك المرجعي (فاتح)", en: "Your reference (light)",
    theme: makeTheme("reference-light", {
      bg: "#EFF1F5", text: "#43444D", textSel: "#1E1F26", dis: "#9CA0B0", sel: "#BBC0CC", selDis: "#DCE0E8",
      border: "#AC71FC", sep: "#CECFD3", sym: "#22223D", accent: "#8839EF", icon: "#454651",
      shadow: "#4C4F69", shadowOp: 10 }) },
  { id: "dracula", ar: "Dracula (السابق)", en: "Dracula (previous)",
    theme: makeTheme("dracula", {
      bg: "#282A36", text: "#F8F8F2", textSel: "#50FA7B", dis: "#6272A4", sel: "#FF79C6", selDis: "#313244",
      border: "#BD93F9", sep: "#44475A", sym: "#FF79C6", accent: "#FF79C6", icon: "#F8F8F2" }) },
  // نسخة مطابقة لملف catppuccin/nilesoft-shell (mocha/mauve) مع إصلاح شريط العنصر المعطّل
  { id: "modern", ar: "Catppuccin Mocha (Mauve)", en: "Catppuccin Mocha (Mauve)",
    theme: {
      name: "modern", view: "view.small",
      background: { color: "#1e1e2e", opacity: 100 },
      item: { opacity: 100, prefix: 1,
        text: { normal: "#cdd6f4", select: "#cdd6f4", "normal-disabled": "#a6adc8", "select-disabled": "#a6adc8" },
        back: { select: "#45475a", "select-disabled": "#313244", "normal-disabled": "color.transparent" } },
      border: { enabled: true, size: 1, color: "#cba6f7", opacity: 100, radius: 2 },
      shadow: { enabled: true, size: 5, opacity: 5, color: "#11111b" },
      separator: { size: 1, color: "#313244" },
      symbol: { normal: "#cba6f7", select: "#cba6f7", "normal-disabled": "#a6adc8", "select-disabled": "#a6adc8" },
      image: { enabled: true, color: ["#cdd6f4", "#cba6f7", "#1e1e2e"] },
    } },
  { id: "nord", ar: "Nord", en: "Nord",
    theme: makeTheme("nord", {
      bg: "#2E3440", text: "#ECEFF4", dis: "#616E88", sel: "#434C5E",
      border: "#88C0D0", sep: "#3B4252", sym: "#81A1C1", accent: "#88C0D0" }) },
  { id: "windows-light", ar: "Windows فاتح", en: "Windows light",
    theme: makeTheme("windows-light", {
      bg: "#F9F9F9", text: "#1A1A1A", dis: "#A0A0A0", sel: "#E5E5E5",
      border: "#E0E0E0", sep: "#E0E0E0", sym: "#5C5C5C", accent: "#0067C0", icon: "#3A3A3A",
      shadow: "#000000", shadowOp: 10 }) },
];
