@echo off
REM HF Spaces Deployment Script for Windows
REM This script automates the process of pushing code to Hugging Face Spaces

setlocal enabledelayedexpansion

echo.
echo ====================================================
echo   HF Spaces Deployment Script
echo ====================================================
echo.

REM Get GitHub info
set "GITHUB_REPO=https://github.com/JoseBCN91/electric-demand-forecasting.git"
set "GITHUB_BRANCH=feature/nube-microservicios"

REM Get HF username
echo Please enter your Hugging Face username:
set /p HF_USERNAME=

if "!HF_USERNAME!"=="" (
    echo Error: HF username is required
    exit /b 1
)

set "HF_SPACE_NAME=electric-demand-forecasting"
set "HF_SPACE_URL=https://huggingface.co/spaces/!HF_USERNAME!/!HF_SPACE_NAME!"
set "HF_REPO_URL=https://huggingface.co/spaces/!HF_USERNAME!/!HF_SPACE_NAME!"

echo.
echo ====================================================
echo   STEP 1: Create HF Space (Manual in Browser)
echo ====================================================
echo.
echo Before proceeding, please:
echo.
echo 1. Go to: https://huggingface.co/new-space
echo 2. Fill in:
echo    - Owner: !HF_USERNAME!
echo    - Space name: !HF_SPACE_NAME!
echo    - License: MIT
echo    - SDK: Docker
echo 3. Click "Create Space"
echo.
echo Press Enter when you have created the Space and are ready to continue...
pause

echo.
echo ====================================================
echo   STEP 2: Add ENTSOE_API_KEY Secret
echo ====================================================
echo.
echo Please enter your ENTSOE API Key:
set /p ENTSOE_API_KEY=

if "!ENTSOE_API_KEY!"=="" (
    echo Warning: ENTSOE_API_KEY not set
    echo The API will still work, but data pipeline will fail
    echo You can add this later in HF Space Settings ^> Repository secrets
) else (
    echo.
    echo Go to: !HF_SPACE_URL!/settings
    echo 1. Scroll to "Repository secrets"
    echo 2. Click "Add new secret"
    echo 3. Key: ENTSOE_API_KEY
    echo 4. Value: [Your API key]
    echo 5. Click "Add secret"
    echo.
    echo Press Enter when you have added the secret...
    pause
)

echo.
echo ====================================================
echo   STEP 3: Clone and Sync Code
echo ====================================================
echo.
echo Creating temporary deployment directory...

set "TEMP_DIR=%TEMP%\hf-spaces-deploy-%RANDOM%"
mkdir "!TEMP_DIR!"
cd /d "!TEMP_DIR!"

echo.
echo Step 3a: Cloning HF Space repository...
git clone !HF_REPO_URL! .

if errorlevel 1 (
    echo Error: Failed to clone HF Space
    pause
    exit /b 1
)

echo.
echo Step 3b: Adding GitHub as remote...
git remote add github !GITHUB_REPO!

echo.
echo Step 3c: Pulling code from GitHub...
git pull github !GITHUB_BRANCH!

if errorlevel 1 (
    echo Error: Failed to pull from GitHub
    pause
    exit /b 1
)

echo.
echo Step 3d: Pushing to HF Spaces (this starts the build)...
git push origin main

if errorlevel 1 (
    echo Error: Failed to push to HF Spaces
    pause
    exit /b 1
)

echo.
echo ====================================================
echo   SUCCESS! Deployment Started
echo ====================================================
echo.
echo Your HF Space is now building! This may take 2-5 minutes.
echo.
echo View deployment progress:
echo   !HF_SPACE_URL!/logs
echo.
echo Once complete, test these endpoints:
echo.
echo Health check:
echo   curl !HF_SPACE_URL!/health
echo.
echo Make a prediction:
echo   curl -X POST !HF_SPACE_URL!/predict ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"horizon\": 24, \"country\": \"ES\"}"
echo.
echo View metrics:
echo   curl !HF_SPACE_URL!/metrics
echo.
echo Open in browser:
echo   !HF_SPACE_URL!/
echo.
echo Cleaning up temporary directory...
cd /
rmdir /s /q "!TEMP_DIR!"

echo.
echo Deployment complete!
pause
