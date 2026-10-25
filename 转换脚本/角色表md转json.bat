@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON_EXE="H:\ComfyUI-aki-v3\ComfyUI-aki-v3\python\python.exe"
set SCRIPT="cast2json.py"

if "%~1"=="" (
    echo 正在搜索当前文件夹的 *-cast.md 文件...
    set found=0
    setlocal enabledelayedexpansion
    for %%f in (*-cast.md) do (
        set found=1
        echo 正在转换: [%%f]
        %PYTHON_EXE% %SCRIPT% "%%f" -o "%%~nf.json"
        echo -------------------------------------
    )
    if "!found!"=="0" (
        echo 没找到 *-cast.md 文件！请把文件拖到 bat 上运行。
    )
    endlocal
) else (
    echo 正在转换拖拽进来的文件: [%~nx1]
    echo.
    %PYTHON_EXE% %SCRIPT% "%~1" -o "%~dpn1.json"
)

echo.
echo 任务执行完毕！
pause