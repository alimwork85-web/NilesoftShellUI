"""إعداد أول مرة: يربط ملفات الواجهة بـ shell.nss ويعطي المستخدم صلاحية الكتابة عليها.

مجلد Shell في Program Files لا يُكتب إلا بصلاحية المسؤول، لذلك نجهّز كل شيء
في مجلد مؤقت ثم نشغّل سكربت PowerShell واحدًا بصلاحية المسؤول (نافذة UAC):
ينسخ shell.nss إلى shell.nss.bak مرة واحدة، وينشئ ملفات ui-*.nss الناقصة،
ويمنح المستخدم الحالي صلاحية التعديل عليها وحدها، ثم يضع shell.nss الجديد.

© 2026 Ali Alhumedi - MIT License
"""

import os
import re
import subprocess
import tempfile

import hide_file
import items_file
import menus_file
import theme_file
from theme_file import AppError

MODULES = (theme_file, hide_file, menus_file, items_file)
FILES = {theme_file: "ui-theme.nss", hide_file: "ui-hide.nss", menus_file: "ui-menus.nss", items_file: "ui-items.nss"}

# أسطر shell.nss الأصلية التي تحل محلها ملفات الواجهة
THEME_RE = re.compile(r"^[ \t]*import 'imports/theme\.nss'[ \t]*$", re.M)
MODIFY_RE = re.compile(r"^[ \t]*import 'imports/modify\.nss'[ \t]*$", re.M)
BLOCKS = {
    "pin": re.compile(r'^[ \t]*menu\(mode="multiple" title="Pin/Unpin" image=icon\.pin\)\s*\{\s*\}[ \t]*$', re.M),
    "more": re.compile(r"^[ \t]*menu\(mode=\"multiple\" title=title\.more_options image=icon\.more_options\)\s*\{\s*\}[ \t]*$", re.M),
}
for _k in ("terminal", "file-manage", "develop", "goto", "taskbar"):
    BLOCKS[_k] = re.compile(r"^[ \t]*import 'imports/%s\.nss'[ \t]*$" % _k, re.M)


def _writable(path):
    try:
        with open(path, "r+b"):
            return True
    except OSError:
        return False


def needed():
    """هل ينقص شيء: ملف غير مربوط أو غير قابل للكتابة؟"""
    if not os.path.exists(os.path.join(theme_file.shell_dir(), "shell.nss")):
        return True
    return not all(m.is_linked() for m in MODULES) or not all(
        _writable(os.path.join(theme_file.shell_dir(), "imports", f)) for f in FILES.values())


def link(text):
    """يرجع (نص shell.nss بعد الربط، حالة قوائم Shell). لا يغيّر ما هو مربوط أصلًا."""
    menus = None
    if menus_file.IMPORT_LINE not in text:
        menus, first = {}, None
        for k, rx in BLOCKS.items():
            m = rx.search(text)
            menus[k] = bool(m)
            if m:
                first = m.start() if first is None else min(first, m.start())
        marker = "\0MENUS\0"
        if first is None:
            text = text.rstrip("\n") + "\n\n" + marker + "\n"
        else:
            text = text[:first] + marker + "\n" + text[first:]
            for rx in BLOCKS.values():
                text = rx.sub("", text, count=1)
        text = text.replace(marker, menus_file.IMPORT_LINE)
    if items_file.IMPORT_LINE not in text:
        text = text.replace(menus_file.IMPORT_LINE, menus_file.IMPORT_LINE + "\n" + items_file.IMPORT_LINE, 1)
    if theme_file.IMPORT_LINE not in text:
        if THEME_RE.search(text):
            text = THEME_RE.sub(theme_file.IMPORT_LINE, text, count=1)
        else:
            i = text.find("import ")
            text = text[:i] + theme_file.IMPORT_LINE + "\n" + text[i:] if i >= 0 else text + theme_file.IMPORT_LINE + "\n"
    if hide_file.IMPORT_LINE not in text:
        m = MODIFY_RE.search(text)
        at = m.end() if m else text.find(theme_file.IMPORT_LINE) + len(theme_file.IMPORT_LINE)
        text = text[:at] + "\n" + hide_file.IMPORT_LINE + text[at:]
    text = re.sub(r"\n{3,}", "\n\n", text).rstrip("\n") + "\n"
    return text, menus


def _first_theme(shell):
    """ملف الثيم الأول: نسخة من theme.nss إن فهمناه، حتى لا يتغير شكل القائمة."""
    try:
        with open(os.path.join(shell, "imports", "theme.nss"), encoding="utf-8-sig") as f:
            return theme_file.build(theme_file.parse(f.read()))
    except (OSError, AppError):
        return "theme\n{\n}\n"


def _sid():
    exe = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "whoami.exe")
    out = subprocess.run([exe, "/user", "/fo", "csv", "/nh"], capture_output=True, text=True,
                         creationflags=0x08000000).stdout
    sid = out.strip().split(",")[-1].strip('"')
    if not re.fullmatch(r"S-1-[0-9-]+", sid):
        raise AppError("تعذّر معرفة حساب المستخدم.", "Could not identify the user account.")
    return sid


def _ps(s):
    return "'" + s.replace("'", "''") + "'"


def run():
    shell = theme_file.shell_dir()
    shell_nss = os.path.join(shell, "shell.nss")
    if not os.path.exists(shell_nss):
        raise AppError("لم أجد Nilesoft Shell. ثبّته أولًا من nilesoft.org ثم أعد المحاولة.",
                       "Nilesoft Shell was not found. Install it from nilesoft.org, then try again.")
    with open(shell_nss, encoding="utf-8-sig") as f:
        text, menus = link(f.read().replace("\r\n", "\n"))

    tmp = tempfile.mkdtemp(prefix="NilesoftShellUI-")

    def write(name, body):
        with open(os.path.join(tmp, name), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(body)

    write("shell.nss", text)
    write("ui-theme.nss", _first_theme(shell))
    write("ui-hide.nss", hide_file.build([]))
    write("ui-menus.nss", menus_file.build(menus or menus_file.load()))
    write("ui-items.nss", items_file.build(items_file.load()))
    script = os.path.join(tmp, "setup.ps1")
    write("setup.ps1", f"""$ErrorActionPreference = 'Stop'
$s = {_ps(shell)}; $t = {_ps(tmp)}
if (-not (Test-Path "$s\\shell.nss.bak")) {{ Copy-Item "$s\\shell.nss" "$s\\shell.nss.bak" }}
foreach ($n in {", ".join(_ps(f) for f in FILES.values())}) {{
  $f = "$s\\imports\\$n"
  if (-not (Test-Path $f)) {{ Copy-Item "$t\\$n" $f }}
  icacls $f /grant '*{_sid()}:(M)' | Out-Null
  if ($LASTEXITCODE) {{ exit 2 }}
}}
Copy-Item "$t\\shell.nss" "$s\\shell.nss" -Force
""")
    # نافذة UAC: إن رفضها المستخدم يفشل Start-Process ويرجع رمزًا غير صفري
    cmd = (f"$p = Start-Process powershell -Verb RunAs -Wait -PassThru -WindowStyle Hidden "
           f"-ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{script}\"'; exit $p.ExitCode")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, creationflags=0x08000000)
    if r.returncode != 0 or needed():
        raise AppError("لم يكتمل الإعداد. وافق على نافذة صلاحية المسؤول ثم أعد المحاولة.",
                       "Setup did not finish. Accept the administrator prompt, then try again.")


if __name__ == "__main__":  # فحص ذاتي على shell.nss الافتراضي من Nilesoft
    DEFAULT = """settings
{
\tpriority=1
}

import 'imports/theme.nss'
import 'imports/images.nss'

import 'imports/modify.nss'

menu(mode="multiple" title="Pin/Unpin" image=icon.pin)
{
}

menu(mode="multiple" title=title.more_options image=icon.more_options)
{
}

import 'imports/terminal.nss'
import 'imports/file-manage.nss'
import 'imports/develop.nss'
import 'imports/goto.nss'
import 'imports/taskbar.nss'
"""
    out, menus = link(DEFAULT)
    print(out)
    assert all(m.IMPORT_LINE in out for m in MODULES)
    assert "imports/theme.nss" not in out and "terminal.nss" not in out and "Pin/Unpin" not in out
    assert out.index("ui-hide") > out.index("modify.nss") and out.index("ui-items") > out.index("ui-menus")
    assert menus == {k: True for k in BLOCKS}, menus
    assert link(out) == (out, None)  # مرة ثانية لا تغيّر شيئًا
    out2, menus2 = link(DEFAULT.replace("import 'imports/develop.nss'\n", ""))
    assert menus2["develop"] is False and menus2["goto"] is True
    print("ok")
