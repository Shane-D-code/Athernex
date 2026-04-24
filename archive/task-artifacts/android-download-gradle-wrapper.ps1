# Download Gradle Wrapper JAR
$url = "https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradle-wrapper.jar"
$output = "gradle/wrapper/gradle-wrapper.jar"

Write-Host "Downloading Gradle Wrapper JAR..."
try {
    Invoke-WebRequest -Uri $url -OutFile $output
    Write-Host "✅ Gradle Wrapper JAR downloaded successfully!"
} catch {
    Write-Host "❌ Failed to download. Error: $_"
    Write-Host ""
    Write-Host "Alternative: Let Android Studio download it automatically"
    Write-Host "Just sync the project and Android Studio will download the wrapper."
}
