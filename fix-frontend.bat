@echo off
echo Fixing frontend issues...

cd frontend

echo Cleaning up node_modules...
if exist node_modules (
    rmdir /s /q node_modules
)

echo Clearing npm cache...
call npm cache clean --force

echo Installing React Scripts...
call npm install react-scripts@5.0.1 --save

echo Installing all dependencies...
call npm install --legacy-peer-deps

echo Frontend fix completed!
echo Run 'cd frontend' and then 'npm start' to start the application.
pause
