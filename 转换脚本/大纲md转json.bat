@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 设置 Python 和 脚本路径
set PYTHON_EXE="H:\ComfyUI-aki-v3\ComfyUI-aki-v3\python\python.exe"
set SCRIPT="md2json.py"

:: 判断是否把文件拖拽到了 bat 上
if "%~1"=="" (
    echo 未检测到拖拽操作，正在自动搜索当前文件夹下的所有 .md 文件...
    echo.
    set found=0
    setlocal enabledelayedexpansion
    for %%f in (*.md) do (
        set found=1
        echo 正在转换: [%%f]
        %PYTHON_EXE% %SCRIPT% "%%f" -o "%%~nf.json"
        echo -------------------------------------
    )
    if "!found!"=="0" (
        echo 当前文件夹下没有找到 .md 文件！
    )
    endlocal
) else (
    echo 正在转换拖拽进来的文件: [%~nx1]
    echo.
    :: %~dpn1 会自动获取拖入文件的完整路径，并把后缀改为 .json
    %PYTHON_EXE% %SCRIPT% "%~1" -o "%~dpn1.json"
)

echo.
echo 任务执行完毕！
pause