@echo off
chcp 65001 >nul
echo =======================================
echo 正在提取章节数字并进行精准排序合并...
echo =======================================

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$outFile = '全书合并汇总.txt';" ^
    "if (Test-Path $outFile) { Remove-Item $outFile };" ^
    "$files = Get-ChildItem -Filter '*.md' | Where-Object { $_.Name -ne $outFile };" ^
    "$files | ForEach-Object { if ($_.BaseName -match '第(\d+)章') { $_ | Add-Member -MemberType NoteProperty -Name 'SortOrder' -Value ([int]$matches[1]) } else { $_ | Add-Member -MemberType NoteProperty -Name 'SortOrder' -Value 99999 } };" ^
    "$sortedFiles = $files | Sort-Object SortOrder;" ^
    "foreach ($f in $sortedFiles) {" ^
        "Write-Host '正在合并:' $f.Name;" ^
        "$sep = [Environment]::NewLine + '==================================================' + [Environment]::NewLine + '【' + $f.BaseName + '】' + [Environment]::NewLine + '==================================================' + [Environment]::NewLine;" ^
        "Add-Content -Path $outFile -Value $sep -Encoding UTF8;" ^
        "Get-Content -Path $f.FullName -Encoding UTF8 | Add-Content -Path $outFile -Encoding UTF8;" ^
    "}" ^
    "Write-Host '✅ 合并完成！请查看【全书合并汇总.txt】' -ForegroundColor Green"

pause