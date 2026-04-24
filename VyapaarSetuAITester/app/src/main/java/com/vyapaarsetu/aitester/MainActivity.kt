package com.vyapaarsetu.aitester

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    
    private lateinit var titleText: TextView
    private lateinit var recordButton: Button
    private lateinit var statusText: TextView
    private lateinit var resultText: TextView
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Initialize views
        titleText = findViewById(R.id.titleText)
        recordButton = findViewById(R.id.recordButton)
        statusText = findViewById(R.id.statusText)
        resultText = findViewById(R.id.resultText)
        
        // Set up button click listener
        recordButton.setOnClickListener {
            onRecordButtonClicked()
        }
        
        // Display welcome message
        statusText.text = "Ready to test voice assistant"
        resultText.text = "Foundation complete ✓\n\n" +
                "• Data models created\n" +
                "• API service configured\n" +
                "• Project structure ready\n\n" +
                "Next: Implement voice recording and API integration"
    }
    
    private fun onRecordButtonClicked() {
        statusText.text = "Recording feature coming soon..."
        resultText.text = "This will integrate with:\n" +
                "• Speech recognition\n" +
                "• Language detection API\n" +
                "• Intent classification\n" +
                "• TTS playback"
    }
}
