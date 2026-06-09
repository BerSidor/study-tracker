$raw     = [Console]::In.ReadToEnd()
$data    = $raw | ConvertFrom-Json
$path    = $data.tool_input.file_path
$dataDir = "C:\Users\berna\Claude_Code_Learning\study-tracker\data"

function Format-Hrs($hrs) {
    $totalMin = [math]::Round($hrs * 60)
    $h = [math]::Floor($totalMin / 60)
    $m = $totalMin % 60
    if ($h -gt 0 -and $m -gt 0) { return "${h}h ${m}m" }
    elseif ($h -gt 0)            { return "${h}h" }
    else                         { return "${m}m" }
}

function Get-TodayCompletedHrs($sessions) {
    $today = Get-Date -Format "yyyy-MM-dd"
    $sum = ($sessions | Where-Object { $_.date -eq $today } |
            Measure-Object -Property durationHrs -Sum).Sum
    return [double]$(if ($null -eq $sum) { 0 } else { $sum })
}

function Get-CurrentSessionHrs($session) {
    $start   = [datetime]::ParseExact($session.startTime, "HH:mm", $null)
    $now     = Get-Date
    $elapsed = ($now - $start).TotalHours
    foreach ($p in $session.pauses) {
        $ps = [datetime]::ParseExact($p.startTime, "HH:mm", $null)
        if ($null -ne $p.endTime) {
            $elapsed -= ([datetime]::ParseExact($p.endTime, "HH:mm", $null) - $ps).TotalHours
        } else {
            $elapsed -= ($now - $ps).TotalHours
        }
    }
    return [math]::Max(0.0, $elapsed)
}

function Build-ProgressXml($todayHrs, $targetHrs) {
    $pct    = [math]::Min(1.0, $todayHrs / $targetHrs)
    $pctStr = $pct.ToString("F2", [System.Globalization.CultureInfo]::InvariantCulture)
    $label  = "$(Format-Hrs $todayHrs) of $(Format-Hrs $targetHrs)"
    $disp   = "$([math]::Round($pct * 100))%"
    return "<progress value=""$pctStr"" title=""Today"" status=""$label"" valueStringOverride=""$disp""/>"
}

$config    = Get-Content "$dataDir\config.json" | ConvertFrom-Json
$target    = [double]$config.dailyTargetHours

if ($path -match 'sessions\.json') {
    $sessions  = $data.tool_input.content | ConvertFrom-Json
    $last      = $sessions | Select-Object -Last 1
    $todayHrs  = Get-TodayCompletedHrs $sessions
    $message   = "Session saved - $(Format-Hrs $last.durationHrs)"
    $progress  = Build-ProgressXml $todayHrs $target

} elseif ($path -match 'current-session\.json') {
    $session   = $data.tool_input.content | ConvertFrom-Json
    $pauses    = $session.pauses
    $pastHrs   = Get-TodayCompletedHrs (Get-Content "$dataDir\sessions.json" | ConvertFrom-Json)
    $curHrs    = Get-CurrentSessionHrs $session
    $todayHrs  = $pastHrs + $curHrs
    $progress  = Build-ProgressXml $todayHrs $target

    if ($pauses.Count -gt 0) {
        $last = $pauses | Select-Object -Last 1
        if ($null -eq $last.endTime) {
            $message = "Session paused"
        } else {
            $ps       = [datetime]::ParseExact($last.startTime, "HH:mm", $null)
            $pe       = [datetime]::ParseExact($last.endTime,   "HH:mm", $null)
            $breakMin = [math]::Round(($pe - $ps).TotalMinutes)
            $message  = "Session resumed - ${breakMin}m break"
        }
    } else {
        $topic = ($session.segments | Select-Object -Last 1).topic
        $message = if ($session.segments.Count -eq 1) {
            "Session started - $topic"
        } else {
            "Now studying: $topic"
        }
    }
} else {
    exit 0
}

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
$xml = [Windows.Data.Xml.Dom.XmlDocument]::new()
$xml.LoadXml("<toast><visual><binding template=""ToastGeneric""><text>$message</text>$progress</binding></visual></toast>")
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe").Show($toast)
