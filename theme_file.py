"""قراءة وكتابة ملف ثيم Nilesoft Shell (ui-theme.nss) بأمان.

الواجهة لا تكتب إلا ملفها الخاص imports\\ui-theme.nss داخل مجلد Shell
(لحسابك صلاحية كتابة على هذا الملف وحده)، وملفات Shell الأصلية لا تُلمس.
Shell لا يستطيع فتح ملفات الاستيراد من AppData، لذلك يبقى الملف في مجلده.

© 2026 Ali Alhumedi - MIT License
"""

import glob
import os
import re
import shutil
import subprocess
import time
import winreg

APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
DATA_DIR = os.path.join(APPDATA, "NilesoftShellUI")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
IMPORT_LINE = "import 'imports/ui-theme.nss'"
KEEP_BACKUPS = 50

COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
# مفاتيح قيمتها نص بين علامتي تنصيص، والباقي يُكتب كما هو
QUOTED = {("name",), ("font", "name")}


class AppError(Exception):
    def __init__(self, ar, en):
        super().__init__(en)
        self.ar, self.en = ar, en

    def text(self, lang):
        return self.en if lang == "en" else self.ar


def shell_dir():
    """مجلد تثبيت Shell من الريجستري، أو المسار الافتراضي."""
    try:
        key = r"CLSID\{BAE3934B-8A6A-4BFB-81BD-3FC599A1BAF1}\InprocServer32"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key) as k:
            return os.path.dirname(winreg.QueryValueEx(k, "")[0])
    except OSError:
        return os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Nilesoft Shell")


THEME_FILE = os.path.join(shell_dir(), "imports", "ui-theme.nss")


def is_linked():
    """هل يستورد shell.nss ملف الثيم الخاص بالواجهة؟"""
    try:
        with open(os.path.join(shell_dir(), "shell.nss"), encoding="utf-8-sig") as f:
            return IMPORT_LINE in f.read()
    except OSError:
        return False


# ---------- القراءة ----------

def _strip_comments(text):
    out = []
    for line in text.splitlines():
        in_str, i = None, 0
        while i < len(line):
            c = line[i]
            if in_str:
                if c == in_str:
                    in_str = None
            elif c in "'\"":
                in_str = c
            elif line.startswith("//", i):
                line = line[:i]
                break
            i += 1
        out.append(line)
    return "\n".join(out)


TOKEN_RE = re.compile(r'\s*("[^"]*"|\'[^\']*\'|\[|[{}=]|[^\s{}=\[\]]+)')


def _split_list(body):
    """يقسم محتوى [ ... ] على الفواصل العليا فقط، لدعم القوائم المتداخلة."""
    parts, depth, cur = [], 0, ""
    for ch in body:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def _value(tok):
    if tok[0] in "'\"":
        return tok[1:-1]
    if tok.startswith("["):
        return [_value(t) for t in _split_list(tok[1:-1])]
    if tok in ("true", "false"):
        return tok == "true"
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    return tok


def parse(text):
    """يحوّل كتلة theme { ... } إلى قاموس متداخل."""
    src = _strip_comments(text)
    toks, pos = [], 0
    for m in TOKEN_RE.finditer(src):
        if m.start() < pos:
            continue
        tok = m.group(1)
        if tok == "[":  # القائمة كاملة حتى قوسها المقابل، ولو كانت متداخلة
            depth, i = 0, m.start(1)
            while i < len(src):
                depth += {"[": 1, "]": -1}.get(src[i], 0)
                i += 1
                if depth == 0:
                    break
            tok, pos = src[m.start(1):i], i
        toks.append(tok)
    pos = 0

    def block():
        nonlocal pos
        d = {}
        while pos < len(toks) and toks[pos] != "}":
            name = toks[pos]
            if pos + 1 < len(toks) and toks[pos + 1] == "{":
                pos += 2
                d[name] = block()
                pos += 1  # }
            elif pos + 2 < len(toks) and toks[pos + 1] == "=":
                d[name] = _value(toks[pos + 2])
                pos += 3
            else:
                raise AppError("ملف الثيم غير مفهوم.", "The theme file could not be understood.")
        return d

    root = block()
    if "theme" not in root:
        raise AppError("لم أجد كتلة theme في الملف.", "No theme block found in the file.")
    return root["theme"]


# ---------- الكتابة ----------

def _fmt(path, v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_fmt(path, x) for x in v) + "]"
    s = str(v)
    if path in QUOTED:
        return '"' + s.replace('"', "") + '"'
    if not re.fullmatch(r"[#A-Za-z0-9_.\-]+", s):
        raise AppError(f"قيمة غير صالحة: {s}", f"Invalid value: {s}")
    return s


def _validate(path, v):
    if isinstance(v, str) and v.startswith("#") and not COLOR_RE.match(v):
        raise AppError(f"لون غير صالح: {v}", f"Invalid color: {v}")
    if isinstance(v, list):
        for x in v:
            _validate(path, x)


def build(theme):
    lines = ["// Generated by Nilesoft Shell UI - edits here are overwritten on save", "theme", "{"]

    def walk(d, path, depth):
        pad = "\t" * depth
        for k, v in d.items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-]*", k):
                raise AppError(f"اسم مفتاح غير صالح: {k}", f"Invalid key: {k}")
            p = path + (k,)
            if isinstance(v, dict):
                lines.append(f"{pad}{k}")
                lines.append(pad + "{")
                walk(v, p, depth + 1)
                lines.append(pad + "}")
            else:
                _validate(p, v)
                lines.append(f"{pad}{k} = {_fmt(p, v)}")

    walk(theme, (), 1)
    lines.append("}")
    return "\n".join(lines) + "\n"


def load():
    if not os.path.exists(THEME_FILE):
        return {}
    with open(THEME_FILE, encoding="utf-8-sig") as f:
        return parse(f.read())


def _backup():
    if not os.path.exists(THEME_FILE):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(THEME_FILE, os.path.join(BACKUP_DIR, f"ui-theme-{stamp}.nss"))
    old = sorted(glob.glob(os.path.join(BACKUP_DIR, "ui-theme-*.nss")))
    for p in old[:-KEEP_BACKUPS]:
        os.remove(p)


def save(theme):
    text = build(theme)
    if parse(text) != parse(build(parse(text))):  # تحقق: الملف يُقرأ كما كُتب
        raise AppError("فشل التحقق من الملف قبل الحفظ.", "Verification failed before saving.")
    _backup()
    _write(text)
    return parse(text)


def _write(text):
    # الكتابة في نفس الملف: الصلاحية على الملف وحده لا تسمح بإنشاء ملف مؤقت بجانبه
    try:
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            f.write(text)
    except PermissionError:
        raise AppError("لا توجد صلاحية كتابة على ملف الثيم: " + THEME_FILE,
                       "No write permission on the theme file: " + THEME_FILE)


def undo():
    """يرجع آخر نسخة احتياطية."""
    old = sorted(glob.glob(os.path.join(BACKUP_DIR, "ui-theme-*.nss")))
    if not old:
        raise AppError("لا توجد نسخة سابقة.", "No previous version.")
    with open(old[-1], encoding="utf-8-sig") as f:
        text = f.read()
    parse(text)
    _write(text)
    os.remove(old[-1])
    return load()


# ---------- Shell ----------

def restart_explorer():
    exe = os.path.join(shell_dir(), "shell.exe")
    if os.path.exists(exe):
        subprocess.Popen([exe, "-restart", "-silent"], creationflags=0x08000000)
    else:
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], creationflags=0x08000000)
        subprocess.Popen(["explorer.exe"])


def apply(wait=8):
    """Shell يقرأ الإعدادات عند تشغيل Explorer فقط: نعيد تشغيله ثم نقرأ أخطاء السجل."""
    start = time.time()
    restart_explorer()
    time.sleep(wait)
    return recent_errors(start)


def recent_errors(since):
    """أخطاء shell.log المسجلة بعد وقت معين (ثوانٍ منذ epoch)."""
    path = os.path.join(shell_dir(), "shell.log")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return []
    text = raw.decode("utf-16", errors="ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in raw[:200] \
        else raw.decode("utf-8", errors="ignore")
    errs = []
    for line in text.splitlines():
        m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[(?:error|warning)\]\s*(.*)", line.strip())
        if m and time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")) >= since - 1:
            errs.append(m.group(2))
    return errs
