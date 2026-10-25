@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

:: 你的 Python 路径
set PYTHON_EXE="H:\ComfyUI-aki-v3\ComfyUI-aki-v3\python\python.exe"

echo =======================================
echo 开始一键转换所有 Markdown 为 JSON...
echo =======================================

:: 1. 转换角色表
echo.
echo [1/5] 正在扫描并转换角色表 (*-cast.md)...
set found=0
for %%f in (*-cast.md) do (
    set found=1
    echo 转换中: [%%f]
    %PYTHON_EXE% -X utf8 cast2json.py "%%f" -o "%%~nf.json"
)
if "!found!"=="0" echo 未找到角色表，跳过。

:: 2. 转换美术集
echo.
echo [2/5] 正在扫描并转换美术集 (*-art.md)...
set found=0
for %%f in (*-art.md) do (
    set found=1
    echo 转换中: [%%f]
    %PYTHON_EXE% -X utf8 art2json.py "%%f" -o "%%~nf.json"
)
if "!found!"=="0" echo 未找到美术集，跳过。

:: 3. 转换剧本
echo.
echo [3/5] 正在扫描并转换剧本 (*-script.md)...
set found=0
for %%f in (*-script.md) do (
    set found=1
    echo 转换中: [%%f]
    %PYTHON_EXE% -X utf8 script2json.py "%%f" -o "%%~nf.json"
)
if "!found!"=="0" echo 未找到剧本，跳过。

:: 4. 转换分镜表
echo.
echo [4/5] 正在扫描并转换分镜表 (*-storyboard.md)...
set found=0
for %%f in (*-storyboard.md) do (
    set found=1
    echo 转换中: [%%f]
    %PYTHON_EXE% -X utf8 storyboard2json.py "%%f" -o "%%~nf.json"
)
if "!found!"=="0" echo 未找到分镜表，跳过。

:: 5. 转换大纲 (智能过滤其他已转换的后缀)
echo.
echo [5/5] 正在扫描并转换大纲 (*.md)...
set found=0
for %%f in (*.md) do (
    set "fname=%%~nf"
    :: 检查文件名结尾是否包含特定的四个后缀，如果不包含，则视为大纲
    echo !fname! | findstr /i /e /C:"-cast" /C:"-art" /C:"-script" /C:"-storyboard" >nul
    if errorlevel 1 (
        set found=1
        echo 转换中: [%%f]
        %PYTHON_EXE% -X utf8 md2json.py "%%f" -o "%%~nf.json"
    )
)
if "!found!"=="0" echo 未找到大纲，跳过。

echo.
echo =======================================
echo 全部任务执行完毕！请检查生成的 JSON 文件。
echo =======================================
pause