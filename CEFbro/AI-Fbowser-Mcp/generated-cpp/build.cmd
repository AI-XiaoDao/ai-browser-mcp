@echo off
rem ============================================================
rem  AI-Fbowser-Mcp 独立编译脚本(不依赖火山开发环境)
rem  前置要求(微软标准组件, 可从 VS Installer 安装):
rem    1) Visual Studio 2019/2022 Build Tools, 勾选 "C++ 桌面开发"
rem    2) "适用于最新 v143/v142 生成工具的 C++ MFC"(MFC 组件, 必须)
rem    3) Windows 10/11 SDK
rem  用法(在本文件所在目录执行):
rem    build.cmd x64     编译 64 位 -> ..\linker\AI-Fbowser-Mcp.exe
rem    build.cmd win32   编译 32 位 -> ..\linker\AI-Fbowser-Mcp.exe
rem  SDK 依赖全部在本仓库 standalone\ 目录内(头文件/源/库/manifest 相对路径),
rem  不引用任何 E:\HSPC 或火山环境路径。
rem ============================================================
setlocal
set ARCH=%~1
if "%ARCH%"=="" set ARCH=x64

rem 定位 Visual Studio 安装目录(vswhere 标准位置)
set VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe
if not exist "%VSWHERE%" (
  echo [错误] 未找到 vswhere, 请先安装 Visual Studio Build Tools(含 MFC 组件)
  exit /b 1
)
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set VSDIR=%%i
if "%VSDIR%"=="" (
  echo [错误] 未找到含 C++ 工具链的 Visual Studio
  exit /b 1
)
call "%VSDIR%\VC\Auxiliary\Build\vcvarsall.bat" %ARCH% >nul 2>&1
if errorlevel 1 (
  echo [错误] vcvarsall %ARCH% 失败
  exit /b 1
)

cd /d "%~dp0%ARCH%"
if not exist ..\linker mkdir ..\linker
if not exist ..\linker\out mkdir ..\linker\out
if not exist ..\linker\out\extern mkdir ..\linker\out\extern
nmake /f makefile
if errorlevel 1 (
  echo [失败] 编译未通过, 请查看上方输出
  exit /b 1
)
echo [成功] 产出: %~dp0%ARCH%\..\linker\AI-Fbowser-Mcp.exe
endlocal
