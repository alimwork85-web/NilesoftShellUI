# يرسم أيقونة التطبيق من الصفر (WPF المدمج في Windows، دون حزم خارجية)
# الفكرة: قائمة زر أيمن صغيرة سطرها الأوسط مظلل بالبنفسجي، مع قطرة لون.
# الناتج: app.ico (16-256) و app-256.png و app-1024.png و preview.png
# © 2026 Ali Alhumedi - MIT License

Add-Type -AssemblyName PresentationCore, WindowsBase
$out = $PSScriptRoot
$N = 1024.0

function C($hex) { [Windows.Media.ColorConverter]::ConvertFromString($hex) }
function B($hex) { $b = New-Object Windows.Media.SolidColorBrush (C $hex); $b.Freeze(); $b }
function RR($x, $y, $w, $h, $r) { New-Object Windows.Media.RectangleGeometry (New-Object Windows.Rect $x, $y, $w, $h), $r, $r }

$dv = New-Object Windows.Media.DrawingVisual
$dc = $dv.RenderOpen()

# الخلفية: مربع مستدير بتدرج عمودي هادئ (ألوان Catppuccin Mocha)
$m = $N * 0.06
$bg = New-Object Windows.Media.LinearGradientBrush (C '#313244'), (C '#1E1E2E'), 90.0
$dc.DrawGeometry($bg, (New-Object Windows.Media.Pen (B '#CBA6F7'), ($N * 0.022)), (RR $m $m ($N - 2 * $m) ($N - 2 * $m) ($N * 0.22)))

# لوحة القائمة
$px = $N * 0.20; $py = $N * 0.22; $pw = $N * 0.50; $ph = $N * 0.56
$dc.DrawGeometry((B '#CDD6F4'), $null, (RR $px $py $pw $ph ($N * 0.07)))

# ثلاثة أسطر: الأوسط مظلل بالبنفسجي
$rowH = $N * 0.085; $gap = ($ph - 3 * $rowH) / 4
for ($i = 0; $i -lt 3; $i++) {
    $ry = $py + $gap + $i * ($rowH + $gap)
    if ($i -eq 1) {
        $dc.DrawGeometry((B '#CBA6F7'), $null, (RR ($px + $N * 0.035) ($ry - $N * 0.02) ($pw - $N * 0.07) ($rowH + $N * 0.04) ($N * 0.035)))
        $dc.DrawGeometry((B '#1E1E2E'), $null, (RR ($px + $N * 0.08) $ry ($pw * 0.58) $rowH ($rowH / 2)))
    } else {
        $dc.DrawGeometry((B '#45475A'), $null, (RR ($px + $N * 0.08) $ry ($pw * 0.58) $rowH ($rowH / 2)))
    }
}

# قطرة لون في الزاوية: دائرة وردية بحد داكن تتداخل مع اللوحة
$cx = $N * 0.72; $cy = $N * 0.70; $r = $N * 0.135
$dc.DrawEllipse((B '#F5C2E7'), (New-Object Windows.Media.Pen (B '#1E1E2E'), ($N * 0.035)), (New-Object Windows.Point $cx, $cy), $r, $r)
$dc.DrawEllipse((B '#FAB387'), $null, (New-Object Windows.Point ($cx - $r * 0.25), ($cy - $r * 0.25)), ($r * 0.38), ($r * 0.38))
$dc.Close()

$master = New-Object Windows.Media.Imaging.RenderTargetBitmap 1024, 1024, 96, 96, ([Windows.Media.PixelFormats]::Pbgra32)
$master.Render($dv)

function Scaled($size) {
    # تصغير بجودة عالية من النسخة الكبيرة
    $dv2 = New-Object Windows.Media.DrawingVisual
    $c2 = $dv2.RenderOpen()
    [Windows.Media.RenderOptions]::SetBitmapScalingMode($dv2, [Windows.Media.BitmapScalingMode]::Fant)
    $c2.DrawImage($master, (New-Object Windows.Rect 0, 0, $size, $size))
    $c2.Close()
    $rt = New-Object Windows.Media.Imaging.RenderTargetBitmap $size, $size, 96, 96, ([Windows.Media.PixelFormats]::Pbgra32)
    $rt.Render($dv2)
    $rt
}
function PngBytes($bmp) {
    $enc = New-Object Windows.Media.Imaging.PngBitmapEncoder
    $enc.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($bmp))
    $ms = New-Object IO.MemoryStream; $enc.Save($ms); ,[byte[]]$ms.ToArray()  # الفاصلة تمنع PowerShell من تفكيك المصفوفة
}

[IO.File]::WriteAllBytes("$out\app-1024.png", (PngBytes $master))
$sizes = 16, 24, 32, 48, 64, 128, 256
$pngs = @{}
foreach ($s in $sizes) { $pngs[$s] = PngBytes (Scaled $s) }
[IO.File]::WriteAllBytes("$out\app-256.png", $pngs[256])

# ملف ICO فيه كل الأحجام (صور PNG داخلية، يدعمها Windows Vista وما بعده)
$ms = New-Object IO.MemoryStream; $bw = New-Object IO.BinaryWriter $ms
$bw.Write([uint16]0); $bw.Write([uint16]1); $bw.Write([uint16]$sizes.Count)
$offset = 6 + 16 * $sizes.Count
foreach ($s in $sizes) {
    $d = $pngs[$s]; $dim = if ($s -ge 256) { 0 } else { $s }
    $bw.Write([byte]$dim); $bw.Write([byte]$dim); $bw.Write([byte]0); $bw.Write([byte]0)
    $bw.Write([uint16]1); $bw.Write([uint16]32); $bw.Write([uint32]$d.Length); $bw.Write([uint32]$offset)
    $offset += $d.Length
}
foreach ($s in $sizes) { $bw.Write([byte[]]$pngs[$s]) }
[IO.File]::WriteAllBytes("$out\app.ico", $ms.ToArray())

# صفحة معاينة بالأحجام الحقيقية على خلفية فاتحة وداكنة
$pv = New-Object Windows.Media.DrawingVisual
$p = $pv.RenderOpen()
$p.DrawRectangle((B '#F3F3F3'), $null, (New-Object Windows.Rect 0, 0, 520, 150))
$p.DrawRectangle((B '#202020'), $null, (New-Object Windows.Rect 0, 150, 520, 150))
foreach ($row in 0, 1) {
    $x = 16
    foreach ($s in 16, 24, 32, 48, 128) {
        $p.DrawImage((Scaled $s), (New-Object Windows.Rect $x, (10 + $row * 150), $s, $s)); $x += $s + 24
    }
}
$p.Close()
$prt = New-Object Windows.Media.Imaging.RenderTargetBitmap 520, 300, 96, 96, ([Windows.Media.PixelFormats]::Pbgra32)
$prt.Render($pv)
[IO.File]::WriteAllBytes("$out\preview.png", (PngBytes $prt))
"done: " + (Get-ChildItem $out -Filter 'app*' | % { "$($_.Name)=$($_.Length)" }) -join ' '
