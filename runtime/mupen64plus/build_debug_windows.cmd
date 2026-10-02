@echo off
setlocal
if "%MUPEN64PLUS_CORE_SRC%"=="" (
  echo MUPEN64PLUS_CORE_SRC must point to the mupen64plus-core source tree.
  exit /b 2
)
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
msbuild "%MUPEN64PLUS_CORE_SRC%\projects\msvc\mupen64plus-core.vcxproj" /m /p:Configuration=Debug /p:Platform=x64 /p:PlatformToolset=v143 /v:minimal
exit /b %errorlevel%
