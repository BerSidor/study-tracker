$raw  = [Console]::In.ReadToEnd()
$data = $raw | ConvertFrom-Json
$path = $data.tool_input.file_path
$dataDir = "C:\Users\berna\Claude_Code_Learning\study-tracker\data"

function Format-Hrs($hrs) {
    $totalMin = [math]::Round($hrs * 60)
    $h = [math]::Floor($totalMin / 60)
    $m = $totalMin % 60
    if ($h -gt 0 -and $m -gt 0) { return "${h}h ${m}m" }
    elseif ($h -gt 0)            { return "${h}h" }
    else                         { return "${m}m" }
}

function Get-SegmentMins($seg) {
    if ($null -eq $seg.endTime) { return 0.0 }
    $s    = [datetime]::ParseExact($seg.startTime, "HH:mm", $null)
    $e    = [datetime]::ParseExact($seg.endTime,   "HH:mm", $null)
    $diff = ($e - $s).TotalMinutes
    if ($diff -lt 0) { $diff += 1440 }
    return $diff
}

function Get-SessionHrs($session) {
    $total = 0.0
    foreach ($seg in $session.segments) { $total += Get-SegmentMins $seg }
    return $total / 60
}

function Get-TodayCompletedHrs($sessions) {
    $today = Get-Date -Format "yyyy-MM-dd"
    $total = 0.0
    foreach ($s in ($sessions | Where-Object { $_.date -eq $today })) {
        $total += Get-SessionHrs $s
    }
    return $total
}

function Build-ProgressXml($todayHrs, $targetHrs) {
    $pct    = [math]::Min(1.0, $todayHrs / $targetHrs)
    $pctStr = $pct.ToString("F2", [System.Globalization.CultureInfo]::InvariantCulture)
    $label  = "$(Format-Hrs $todayHrs) of $(Format-Hrs $targetHrs)"
    $disp   = "$([math]::Round($pct * 100))%"
    return "<progress value=""$pctStr"" title=""Today"" status=""$label"" valueStringOverride=""$disp""/>"
}

$config = Get-Content "$dataDir\config.json" | ConvertFrom-Json
$target = [double]$config.dailyTargetHours

if ($path -match 'sessions\.json') {
    $sessions = $data.tool_input.content | ConvertFrom-Json
    $last     = $sessions | Select-Object -Last 1
    $todayHrs = Get-TodayCompletedHrs $sessions
    $message  = "Session saved - $(Format-Hrs (Get-SessionHrs $last))"
    $progress = Build-ProgressXml $todayHrs $target

} elseif ($path -match 'current-session\.json') {
    $session  = $data.tool_input.content | ConvertFrom-Json
    $lastSeg  = $session.segments | Select-Object -Last 1
    $prevSeg  = if ($session.segments.Count -gt 1) { $session.segments[-2] } else { $null }

    $trackerDir = Split-Path $dataDir -Parent
    $todayHrs = [double]::Parse(
        (python "$trackerDir\cli.py" today),
        [System.Globalization.CultureInfo]::InvariantCulture
    )
    $progress = Build-ProgressXml $todayHrs $target

    if ($null -ne $lastSeg.endTime) {
        $message = "Session paused"
    } elseif ($session.segments.Count -eq 1) {
        $message = "Session started - $($lastSeg.topic)"
    } elseif ($null -ne $prevSeg -and $prevSeg.topic -eq $lastSeg.topic) {
        $breakStart = [datetime]::ParseExact($prevSeg.endTime,    "HH:mm", $null)
        $breakEnd   = [datetime]::ParseExact($lastSeg.startTime,  "HH:mm", $null)
        $breakMin   = [math]::Round(($breakEnd - $breakStart).TotalMinutes)
        $message    = "Session resumed - ${breakMin}m break"
    } else {
        $message = "Now studying: $($lastSeg.topic)"
    }
} else {
    exit 0
}

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
$xml = [Windows.Data.Xml.Dom.XmlDocument]::new()
$xml.LoadXml("<toast><visual><binding template=""ToastGeneric""><text>$message</text>$progress</binding></visual></toast>")
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(
    "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
).Show($toast)
