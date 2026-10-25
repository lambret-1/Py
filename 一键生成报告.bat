@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "BASE_DIR=%~dp0"
if "%BASE_DIR:~-1%"=="\" set "BASE_DIR=%BASE_DIR:~0,-1%"

:: ==========================================
:: 模式1：如果是拖拽文件到 BAT 上运行
:: ==========================================
if not "%~1"=="" (
    set "TARGET_FILE=%~1"
    set "TARGET_DIR=%~dp1"
    if "!TARGET_DIR:~-1!"=="\" set "TARGET_DIR=!TARGET_DIR:~0,-1!"
    set "FNAME=%~n1"
    
    :: 剔除后缀提取书名
    set "BOOK_NAME=!FNAME:-outline=!"
    set "BOOK_NAME=!BOOK_NAME:outline=!"
    set "BOOK_NAME=!BOOK_NAME:-cast=!"
    set "BOOK_NAME=!BOOK_NAME:cast=!"
    set "BOOK_NAME=!BOOK_NAME:-art=!"
    set "BOOK_NAME=!BOOK_NAME:art=!"
    set "BOOK_NAME=!BOOK_NAME:-script=!"
    set "BOOK_NAME=!BOOK_NAME:script=!"
    set "BOOK_NAME=!BOOK_NAME:-storyboard=!"
    set "BOOK_NAME=!BOOK_NAME:storyboard=!"
    if "!BOOK_NAME:~-1!"=="-" set "BOOK_NAME=!BOOK_NAME:~0,-1!"
    if "!BOOK_NAME:~-1!"=="_" set "BOOK_NAME=!BOOK_NAME:~0,-1!"
    
    call :PROCESS_ONE "!BOOK_NAME!" "!TARGET_DIR!"
    pause
    exit /b
)

:: ==========================================
:: 模式2：双击运行，自动扫描所有项目
:: ==========================================
set "SEARCH_DIR=%BASE_DIR%"
if exist "%BASE_DIR%\01_剧本数据" set "SEARCH_DIR=%BASE_DIR%\01_剧本数据"

echo =======================================
echo 正在扫描目录: %SEARCH_DIR%
echo =======================================

:: 采用临时文件去重法，彻底解决书名粘连问题
set "TEMP_LIST=%TEMP%\book_list.txt"
if exist "%TEMP_LIST%" del "%TEMP_LIST%"
set "FOUND=0"

for %%f in ("%SEARCH_DIR%\*.json") do (
    set "FNAME=%%~nf"
    set "FNAME=!FNAME:-outline=!"
    set "FNAME=!FNAME:outline=!"
    set "FNAME=!FNAME:-cast=!"
    set "FNAME=!FNAME:cast=!"
    set "FNAME=!FNAME:-art=!"
    set "FNAME=!FNAME:art=!"
    set "FNAME=!FNAME:-script=!"
    set "FNAME=!FNAME:script=!"
    set "FNAME=!FNAME:-storyboard=!"
    set "FNAME=!FNAME:storyboard=!"
    if "!FNAME:~-1!"=="-" set "FNAME=!FNAME:~0,-1!"
    if "!FNAME:~-1!"=="_" set "FNAME=!FNAME:~0,-1!"
    
    if not "!FNAME!"=="" (
        :: 去重判断：如果在列表里找不到这个名字，就写进去
        findstr /X /C:"!FNAME!" "%TEMP_LIST%" >nul 2>&1
        if errorlevel 1 (
            echo !FNAME!>> "%TEMP_LIST%"
            set "FOUND=1"
        )
    )
)

if "!FOUND!"=="0" (
    echo 没找到任何项目文件！
    if exist "%TEMP_LIST%" del "%TEMP_LIST%"
    pause
    exit /b
)

:: 逐行读取书名列表，依次处理
for /f "usebackq delims=" %%p in ("%TEMP_LIST%") do (
    call :PROCESS_ONE "%%p" "%SEARCH_DIR%"
)

if exist "%TEMP_LIST%" del "%TEMP_LIST%"

echo.
echo =======================================
echo 所有任务执行完毕！
echo =======================================
pause
exit /b


:: ==========================================
:: 核心生成逻辑
:: ==========================================
:PROCESS_ONE
set "BOOK_NAME=%~1"
set "TARGET_DIR=%~2"

:: 寻找真实存在的文件（兼容带横杠和不带横杠）
set "OUTLINE_FILE=!TARGET_DIR!\!BOOK_NAME!-outline.json"
if not exist "!OUTLINE_FILE!" set "OUTLINE_FILE=!TARGET_DIR!\!BOOK_NAME!outline.json"
if not exist "!OUTLINE_FILE!" set "OUTLINE_FILE="

set "CAST_FILE=!TARGET_DIR!\!BOOK_NAME!-cast.json"
if not exist "!CAST_FILE!" set "CAST_FILE=!TARGET_DIR!\!BOOK_NAME!cast.json"
if not exist "!CAST_FILE!" set "CAST_FILE="

set "ART_FILE=!TARGET_DIR!\!BOOK_NAME!-art.json"
if not exist "!ART_FILE!" set "ART_FILE=!TARGET_DIR!\!BOOK_NAME!art.json"
if not exist "!ART_FILE!" set "ART_FILE="

set "SCRIPT_FILE=!TARGET_DIR!\!BOOK_NAME!-script.json"
if not exist "!SCRIPT_FILE!" set "SCRIPT_FILE=!TARGET_DIR!\!BOOK_NAME!script.json"
if not exist "!SCRIPT_FILE!" set "SCRIPT_FILE="

set "STORYBOARD_FILE=!TARGET_DIR!\!BOOK_NAME!-storyboard.json"
if not exist "!STORYBOARD_FILE!" set "STORYBOARD_FILE=!TARGET_DIR!\!BOOK_NAME!storyboard.json"
if not exist "!STORYBOARD_FILE!" set "STORYBOARD_FILE="

:: 检查是否一个文件都没找到
if "!OUTLINE_FILE!!CAST_FILE!!ART_FILE!!SCRIPT_FILE!!STORYBOARD_FILE!"=="" exit /b

echo.
echo =======================================
echo 正在处理项目: !BOOK_NAME!
echo =======================================

:: 给每个项目单独创建独立文件夹
set "REPORT_DIR=%BASE_DIR%\03_!BOOK_NAME!"

if exist "!REPORT_DIR!\01_小说大纲" rmdir "!REPORT_DIR!\01_小说大纲" /s /q 2>nul
if exist "!REPORT_DIR!\02_角色设定" rmdir "!REPORT_DIR!\02_角色设定" /s /q 2>nul
if exist "!REPORT_DIR!\03_美术设定" rmdir "!REPORT_DIR!\03_美术设定" /s /q 2>nul
if exist "!REPORT_DIR!\04_分集剧本" rmdir "!REPORT_DIR!\04_分集剧本" /s /q 2>nul
if exist "!REPORT_DIR!\05_分镜列表" rmdir "!REPORT_DIR!\05_分镜列表" /s /q 2>nul

mkdir "!REPORT_DIR!\01_小说大纲" 2>nul
mkdir "!REPORT_DIR!\02_角色设定" 2>nul
mkdir "!REPORT_DIR!\03_美术设定" 2>nul
mkdir "!REPORT_DIR!\04_分集剧本" 2>nul
mkdir "!REPORT_DIR!\05_分镜列表" 2>nul

:: [1/5] 生成大纲
if not "!OUTLINE_FILE!"=="" (
    echo [1/5] 正在生成【大纲】...
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-outline.mjs" render "!OUTLINE_FILE!" --md > "!REPORT_DIR!\01_小说大纲\!BOOK_NAME!_大纲.md" 2>&1
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-outline.mjs" render "!OUTLINE_FILE!" --html > "!REPORT_DIR!\01_小说大纲\!BOOK_NAME!_大纲报告.html" 2>&1
    echo [OK] 完成
) else (
    echo [1/5] 缺少 outline.json，跳过【大纲】
)

:: [2/5] 生成角色
if not "!CAST_FILE!"=="" (
    echo [2/5] 正在生成【角色设定】...
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-characters.mjs" render "!CAST_FILE!" --md > "!REPORT_DIR!\02_角色设定\!BOOK_NAME!_角色设定.md" 2>&1
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-characters.mjs" render "!CAST_FILE!" --html > "!REPORT_DIR!\02_角色设定\!BOOK_NAME!_角色报告.html" 2>&1
    echo [OK] 完成
) else (
    echo [2/5] 缺少 cast.json，跳过【角色设定】
)

:: [3/5] 生成美术
if not "!ART_FILE!"=="" (
    echo [3/5] 正在生成【美术设定】...
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-art.mjs" render "!ART_FILE!" --md > "!REPORT_DIR!\03_美术设定\!BOOK_NAME!_美术设定.md" 2>&1
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-art.mjs" render "!ART_FILE!" --html > "!REPORT_DIR!\03_美术设定\!BOOK_NAME!_美术报告.html" 2>&1
    echo [OK] 完成
) else (
    echo [3/5] 缺少 art.json，跳过【美术设定】
)

:: [4/5] 生成剧本 (动态判定需要的参数)
if not "!SCRIPT_FILE!"=="" (
    echo [4/5] 正在生成【剧本】...
    set "ARG_OUTLINE="
    if not "!OUTLINE_FILE!"=="" set "ARG_OUTLINE=--outline "!OUTLINE_FILE!""
    set "ARG_ART="
    if not "!ART_FILE!"=="" set "ARG_ART=--art "!ART_FILE!""
    
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-script.mjs" render "!SCRIPT_FILE!" --md !ARG_OUTLINE! !ARG_ART! > "!REPORT_DIR!\04_分集剧本\!BOOK_NAME!_剧本.md" 2>&1
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-script.mjs" render "!SCRIPT_FILE!" --html !ARG_OUTLINE! !ARG_ART! > "!REPORT_DIR!\04_分集剧本\!BOOK_NAME!_剧本报告.html" 2>&1
    echo [OK] 完成
) else (
    echo [4/5] 缺少 script.json，跳过【剧本】
)

:: [5/5] 生成分镜
if not "!STORYBOARD_FILE!"=="" (
    echo [5/5] 正在生成【分镜表】...
    set "ARG_SCRIPT="
    if not "!SCRIPT_FILE!"=="" set "ARG_SCRIPT=--script "!SCRIPT_FILE!""
    set "ARG_OUTLINE="
    if not "!OUTLINE_FILE!"=="" set "ARG_OUTLINE=--outline "!OUTLINE_FILE!""
    set "ARG_ART="
    if not "!ART_FILE!"=="" set "ARG_ART=--art "!ART_FILE!""
    
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-storyboard.mjs" render "!STORYBOARD_FILE!" --md !ARG_SCRIPT! !ARG_OUTLINE! !ARG_ART! > "!REPORT_DIR!\05_分镜列表\!BOOK_NAME!_分镜表.md" 2>&1
    "%BASE_DIR%\node.exe" "%BASE_DIR%\02_核心代码\novel-storyboard.mjs" render "!STORYBOARD_FILE!" --html !ARG_SCRIPT! !ARG_OUTLINE! !ARG_ART! > "!REPORT_DIR!\05_分镜列表\!BOOK_NAME!_分镜报告.html" 2>&1
    echo [OK] 完成
) else (
    echo [5/5] 缺少 storyboard.json，跳过【分镜表】
)

exit /b