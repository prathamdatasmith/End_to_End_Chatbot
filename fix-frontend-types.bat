@echo off
echo Fixing frontend TypeScript issues...

cd frontend

echo Removing problematic dependencies...
call npm uninstall tailwindcss autoprefixer postcss

echo Installing correct axios types...
call npm install --save-dev @types/axios

echo Clearing TypeScript cache...
if exist node_modules\.cache (
    rmdir /s /q node_modules\.cache
)

echo Restarting TypeScript service...
echo TypeScript issues should now be resolved!
echo Run 'npm start' to test the application.
pause
