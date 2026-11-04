# 收件箱监视器：E:\RentAGirl 里出现新视频且下载完成 -> 改名归档到 raw\SxxEyy.mp4
# 用法: powershell -ExecutionPolicy Bypass -File E:\RentAGirl\tools\watch.ps1
param(
    [string]$Inbox = 'E:\RentAGirl',
    [string]$RawDir = 'E:\RentAGirl\raw',
    [string]$Season = '01',
    [int]$StableSeconds = 30
)

$ErrorActionPreference = 'Continue'
$log = Join-Path $RawDir 'watch.log'
$meta = Join-Path $RawDir '.meta'
New-Item -ItemType Directory -Force -Path $RawDir, $meta | Out-Null
$exts = @('.mp4', '.mkv', '.flv', '.ts', '.webm')
$seen = @{}

function Write-Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Output $line
}

function Get-NextEpisode {
    $used = @()
    Get-ChildItem $RawDir -File -Filter 'S*E*.mp4' -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Name -match 'S\d{2}E(\d{2})') { $used += [int]$Matches[1] }
    }
    $n = 1
    while ($used -contains $n) { $n++ }
    return $n
}

Write-Log "watcher started: inbox=$Inbox raw=$RawDir season=S$Season"

while ($true) {
    $files = Get-ChildItem $Inbox -File -ErrorAction SilentlyContinue |
             Where-Object { $exts -contains $_.Extension.ToLower() }

    foreach ($f in $files) {
        $partial = Get-ChildItem $Inbox -File -ErrorAction SilentlyContinue |
                   Where-Object { $_.Name -like "$($f.BaseName)*" -and $_.Extension -match 'crdownload|part|tmp' }
        if ($partial) { continue }

        $key = $f.FullName
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = @{ size = $f.Length; since = Get-Date }
            Write-Log "detected: $($f.Name) ($([math]::Round($f.Length/1MB,1)) MB)"
            continue
        }
        $st = $seen[$key]
        if ($st.size -ne $f.Length) {
            $st.size = $f.Length
            $st.since = Get-Date
            continue
        }
        if (((Get-Date) - $st.since).TotalSeconds -lt $StableSeconds) { continue }

        # 文件已稳定 -> 分配集数
        $ep = $null
        if ($f.Name -match '第\s*(\d{1,3})\s*[话話集]') { $ep = [int]$Matches[1] }
        elseif ($f.Name -match '[Ee]p?\s*(\d{1,3})') { $ep = [int]$Matches[1] }
        if (-not $ep) { $ep = Get-NextEpisode }
        $target = Join-Path $RawDir ("S{0}E{1:00}.mp4" -f $Season, $ep)

        $i = 1
        while (Test-Path $target) {
            $target = Join-Path $RawDir ("S{0}E{1:00}_dup{2}.mp4" -f $Season, $ep, $i)
            $i++
        }

        try {
            Move-Item -LiteralPath $f.FullName -Destination $target -ErrorAction Stop
            $json = @{
                original   = $f.Name
                size_bytes = $f.Length
                moved_at   = (Get-Date -Format 'o')
                cut_s      = 1470
                note       = 'B站过审片段在片尾，默认 24:30 处裁掉；如实际内容更长请改 meta'
            } | ConvertTo-Json
            [System.IO.File]::WriteAllText((Join-Path $meta ("S{0}E{1:00}.json" -f $Season, $ep)), $json, (New-Object System.Text.UTF8Encoding($false)))
            Write-Log "moved -> $target"
            $seen.Remove($key)
        } catch {
            Write-Log "move FAILED: $($_.Exception.Message)"
        }
    }
    Start-Sleep -Seconds 5
}
