$dataDir = "C:\Users\berna\Claude_Code_Learning\study-tracker\data"

if (-not (Test-Path "$dataDir\current-session.json")) { exit 0 }

$session  = Get-Content "$dataDir\current-session.json" | ConvertFrom-Json
$sessions = Get-Content "$dataDir\sessions.json"        | ConvertFrom-Json
$config   = Get-Content "$dataDir\config.json"          | ConvertFrom-Json
$target   = [double]$config.dailyTargetHours
$today    = Get-Date -Format "yyyy-MM-dd"
$now      = Get-Date

function Get-SegmentMins($seg) {
    $s = [datetime]::ParseExact($seg.startTime, "HH:mm", $null)
    if ($null -ne $seg.endTime) {
        $e    = [datetime]::ParseExact($seg.endTime, "HH:mm", $null)
        $diff = ($e - $s).TotalMinutes
        if ($diff -lt 0) { $diff += 1440 }   # midnight crossover
        return $diff
    } else {
        return ($now - $s).TotalMinutes
    }
}

# Past completed sessions today
$pastMins = 0.0
foreach ($s in ($sessions | Where-Object { $_.date -eq $today })) {
    foreach ($seg in $s.segments) {
        if ($null -ne $seg.endTime) { $pastMins += Get-SegmentMins $seg }
    }
}

# Current open session
$curMins = 0.0
foreach ($seg in $session.segments) { $curMins += Get-SegmentMins $seg }

$todayHrs = [math]::Max(0.0, ($pastMins + $curMins) / 60)

$totalMin = [math]::Round($todayHrs * 60)
$h = [math]::Floor($totalMin / 60); $m = $totalMin % 60
$durStr = if ($h -gt 0 -and $m -gt 0) { "${h}h ${m}m" } elseif ($h -gt 0) { "${h}h" } else { "${m}m" }

$tgtMin = [math]::Round($target * 60)
$th = [math]::Floor($tgtMin / 60); $tm = $tgtMin % 60
$tgtStr = if ($th -gt 0 -and $tm -gt 0) { "${th}h ${tm}m" } elseif ($th -gt 0) { "${th}h" } else { "${tm}m" }

$pct    = [math]::Min(1.0, $todayHrs / $target)
$pctStr = $pct.ToString("F2", [System.Globalization.CultureInfo]::InvariantCulture)
$disp   = "$([math]::Round($pct * 100))%"

$lastSeg = $session.segments | Select-Object -Last 1
$paused  = $null -ne $lastSeg.endTime
$topic   = ($lastSeg.topic -replace '&', '&amp;')
$status  = if ($paused) { "Paused — $topic" } else { "Studying: $topic" }

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
$xml = [Windows.Data.Xml.Dom.XmlDocument]::new()
$xml.LoadXml("<toast><visual><binding template=""ToastGeneric""><text>$status</text><progress value=""$pctStr"" title=""Today"" status=""$durStr of $tgtStr"" valueStringOverride=""$disp""/></binding></visual></toast>")
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(
    "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
).Show($toast)
