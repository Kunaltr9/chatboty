# PowerShell script to run the Watermark Security Chatbot
# This sets the GROQ_API_KEY environment variable and runs the app

Write-Host "🛡️ Watermark Security Intelligence Chatbot" -ForegroundColor Cyan
Write-Host ""

# Check if API key is already set
if ($env:GROQ_API_KEY) {
    Write-Host "✅ Found GROQ_API_KEY in environment" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⚠️  GROQ_API_KEY not set in environment" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please enter your Groq API key:" -ForegroundColor White
    Write-Host "Get a free key at: https://console.groq.com/keys" -ForegroundColor Gray
    Write-Host ""
    $apiKey = Read-Host "Enter your Groq API key" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
    $plainApiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    $env:GROQ_API_KEY = $plainApiKey
    Write-Host ""
    Write-Host "✅ API key set for this session" -ForegroundColor Green
    Write-Host ""
}

# Run the application
Write-Host "🚀 Starting the application..." -ForegroundColor Cyan
Write-Host "📍 The app will be available at: http://127.0.0.1:7860" -ForegroundColor Green
Write-Host ""
python appp.py
