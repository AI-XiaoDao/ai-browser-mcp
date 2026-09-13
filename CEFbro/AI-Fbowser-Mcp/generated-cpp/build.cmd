@echo off
rem ============================================================
rem  AI-Fbowser-Mcp standalone build (no Volcano dev env needed)
rem  Prerequisites (Microsoft standard components via VS Installer):
rem    1) Visual Studio 2019/2022 Build Tools with "Desktop development with C++"
rem    2) "C++ MFC" component (REQUIRED - vol_mfc.h depends on MFC headers)
rem    3) Windows 10/11 SDK
rem  Usage (run in this folder):
rem    build.cmd x64      -> ..\linker\AI-Fbowser-Mcp.exe (64-bit)
rem    build.cmd win32    -> ..\linker\AI-Fbowser-Mcp.exe (32-bit)
rem  All SDK deps live in ..\standalone\ (relative paths, no Volcano paths).
rem ============================================================
setlocal
set ARCH=%~1
if "%ARCH%"=="" set ARCH=x64
rem vcvarsall: 32-bit uses x86 (win32 is not a valid vcvarsall arg)
set VCVARARG=%ARCH%
if "%ARCH%"=="win32" set VCVARARG=x86

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSDIR="
if exist "%VSWHERE%" (
  for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSDIR=%%i"
)

set USE_FALLBACK=0
if "%VSDIR%"=="" set USE_FALLBACK=1
if not "%USE_FALLBACK%"=="1" (
  dir /b "%VSDIR%\VC\Tools\MSVC\*\atlmfc" >nul 2>&1
  if errorlevel 1 set USE_FALLBACK=1
)

set "FALLBACK_VS=E:\HSPC\plugins\vprj_win\sdk\compiler\normal"
if "%USE_FALLBACK%"=="1" (
  if exist "%FALLBACK_VS%\VC\Auxiliary\Build\vcvarsall.bat" (
    echo [INFO] VS without MFC found; falling back to bundled MSVC+MFC toolchain (toolchain only)
    call "%FALLBACK_VS%\VC\Auxiliary\Build\vcvarsall.bat" %VCVARARG% >nul 2>&1
    goto :build
  )
  echo [ERROR] No MFC-capable C++ toolchain found. Install VS2019/2022 with the MFC component.
  exit /b 1
)
call "%VSDIR%\VC\Auxiliary\Build\vcvarsall.bat" %VCVARARG% >nul 2>&1
if errorlevel 1 (
  echo [ERROR] vcvarsall %ARCH% failed
  exit /b 1
)

:build
cd /d "%~dp0%ARCH%"
if not exist ..\linker mkdir ..\linker
if not exist ..\linker\out mkdir ..\linker\out
if not exist ..\linker\out\extern mkdir ..\linker\out\extern
rem clean stale artifacts from the other arch (shared out dir; x64/win32 objects are incompatible)
del /q ..\linker\out\*.obj ..\linker\out\*.pch ..\linker\out\*.pdb ..\linker\out\*.res 2>nul
nmake /f makefile
if errorlevel 1 (
  echo [FAILED] build failed, see output above
  exit /b 1
)
echo [OK] Output: %~dp0%ARCH%\..\linker\AI-Fbowser-Mcp.exe
endlocal
