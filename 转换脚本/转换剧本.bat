@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON_EXE="H:\ComfyUI-aki-v3\ComfyUI-aki-v3\python\python.exe"
set SCRIPT="script2json.py"

if "%~1"=="" (
    echo 正在搜索当前文件夹的 *-script.md 文件...
    set found=0
    for %%f in (*-script.md) do (
        set found=1
        echo.
        echo 正在转换: [%%f]
        %PYTHON_EXE% -X utf8 %SCRIPT% "%%f" -o "%%~nf.json"
    )
    if "!found!"=="0" (
        echo.
        echo [提示] 没找到 *-script.md 文件！
        echo 请把 md 文件重命名为 xxx-script.md，或者直接把文件拖到 bat 图标上。
    )
) else (
    echo 正在转换拖拽进来的文件: [%~nx1]
    echo.
    %PYTHON_EXE% -X utf8 %SCRIPT% "%~1" -o "%~dpn1.json"
)

echo.
echo =========================================
echo 任务执行完毕！如果上方显示 Error，请截图反馈。
echo =========================================
pause