Start-Process powershell -ArgumentList "cd `"$PSScriptRoot\api`"; npm install; npm run start" -WindowStyle Normal
Start-Process powershell -ArgumentList "cd `"$PSScriptRoot\admin-dashboard`"; npm install; npm run dev" -WindowStyle Normal
Start-Process powershell -ArgumentList "cd `"$PSScriptRoot\bot`"; pip install -r requirements.txt; python main.py" -WindowStyle Normal 