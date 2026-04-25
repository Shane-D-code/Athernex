package com.vyapaarsetu.aitester

import android.Manifest
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.widget.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.android.material.floatingactionbutton.FloatingActionButton
import kotlinx.coroutines.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.*

class MainActivity : AppCompatActivity(), TextToSpeech.OnInitListener {
    
    companion object {
        private const val TAG = "VyapaarSetuAI"
    }
    
    private lateinit var userNameText: TextView
    private lateinit var settingsButton: ImageView
    private lateinit var statusText: TextView
    private lateinit var transcriptText: TextView
    private lateinit var callButton: FloatingActionButton
    private lateinit var responseText: TextView
    private lateinit var connectionIndicator: View
    private lateinit var connectionText: TextView
    
    private lateinit var prefs: SharedPreferences
    private lateinit var tts: TextToSpeech
    private var speechRecognizer: SpeechRecognizer? = null
    private val client = OkHttpClient()
    private var mediaPlayer: android.media.MediaPlayer? = null
    
    private var isCallActive = false
    private var serverUrl = "http://192.168.137.205:5000"
    
    private val PERMISSION_REQUEST_CODE = 100
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        initViews()
        initPreferences()
        initTTS()
        initSpeechRecognizer()
        setupListeners()
        checkServerConnection()
    }
    
    private fun initViews() {
        userNameText = findViewById(R.id.userNameText)
        settingsButton = findViewById(R.id.settingsButton)
        statusText = findViewById(R.id.statusText)
        transcriptText = findViewById(R.id.transcriptText)
        callButton = findViewById(R.id.callButton)
        responseText = findViewById(R.id.responseText)
        connectionIndicator = findViewById(R.id.connectionIndicator)
        connectionText = findViewById(R.id.connectionText)
    }
    
    private fun initPreferences() {
        prefs = getSharedPreferences("VyapaarSetuPrefs", MODE_PRIVATE)
        val userName = prefs.getString("user_name", "Agent") ?: "Agent"
        serverUrl = prefs.getString("server_url", "http://192.168.137.205:5000") ?: "http://192.168.137.205:5000"
        userNameText.text = userName
    }
    
    private fun initTTS() {
        tts = TextToSpeech(this, this)
    }
    
    private fun initSpeechRecognizer() {
        if (SpeechRecognizer.isRecognitionAvailable(this)) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        }
    }
    
    private fun setupListeners() {
        callButton.setOnClickListener {
            if (isCallActive) {
                endCall()
            } else {
                startCall()
            }
        }
        
        settingsButton.setOnClickListener {
            showSettingsDialog()
        }
        
        userNameText.setOnClickListener {
            showSettingsDialog()
        }
    }
    
    private fun startCall() {
        if (!checkPermissions()) {
            requestPermissions()
            return
        }
        
        isCallActive = true
        updateUI(CallState.LISTENING)
        callButton.setImageResource(android.R.drawable.ic_delete)
        callButton.backgroundTintList = ContextCompat.getColorStateList(this, R.color.call_end)
        
        startListening()
    }
    
    private fun endCall() {
        isCallActive = false
        updateUI(CallState.READY)
        callButton.setImageResource(android.R.drawable.ic_btn_speak_now)
        callButton.backgroundTintList = ContextCompat.getColorStateList(this, R.color.green_primary)
        
        speechRecognizer?.stopListening()
        tts.stop()
    }
    
    private fun startListening() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                runOnUiThread {
                    updateUI(CallState.LISTENING)
                }
            }
            
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}
            
            override fun onError(error: Int) {
                runOnUiThread {
                    if (isCallActive) {
                        Handler(Looper.getMainLooper()).postDelayed({ startListening() }, 500)
                    }
                }
            }
            
            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    val transcript = matches[0]
                    processTranscript(transcript)
                }
            }
            
            override fun onPartialResults(partialResults: Bundle?) {
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    runOnUiThread {
                        transcriptText.text = matches[0]
                    }
                }
            }
            
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
        
        speechRecognizer?.startListening(intent)
    }
    
    private fun processTranscript(transcript: String) {
        runOnUiThread {
            transcriptText.text = transcript
            updateUI(CallState.PROCESSING)
        }
        
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val json = JSONObject().apply {
                    put("audio", transcript)
                    put("session_id", UUID.randomUUID().toString())
                }
                
                val body = json.toString().toRequestBody("application/json".toMediaType())
                val request = Request.Builder()
                    .url("$serverUrl/api/v1/process")
                    .post(body)
                    .build()
                
                client.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        val jsonResponse = JSONObject(responseBody ?: "{}")
                        
                        val aiResponse = jsonResponse.optString("response_text", "I didn't understand that.")
                        val audioBase64 = jsonResponse.optString("audio_response_b64", "")
                        
                        withContext(Dispatchers.Main) {
                            responseText.text = aiResponse
                            updateUI(CallState.SPEAKING)
                            
                            // Play audio from backend if available, otherwise use local TTS
                            if (audioBase64.isNotEmpty()) {
                                playAudioFromBase64(audioBase64)
                            } else {
                                speak(aiResponse)
                            }
                        }
                    } else {
                        withContext(Dispatchers.Main) {
                            responseText.text = "Server error: ${response.code}"
                            if (isCallActive) {
                                Handler(Looper.getMainLooper()).postDelayed({ startListening() }, 1000)
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    responseText.text = "Error: ${e.message}"
                    if (isCallActive) {
                        Handler(Looper.getMainLooper()).postDelayed({ startListening() }, 1000)
                    }
                }
            }
        }
    }
    
    private fun playAudioFromBase64(audioBase64: String) {
        try {
            val audioBytes = android.util.Base64.decode(audioBase64, android.util.Base64.DEFAULT)
            val tempFile = java.io.File.createTempFile("tts_audio", ".mp3", cacheDir)
            tempFile.writeBytes(audioBytes)
            
            mediaPlayer?.release()
            mediaPlayer = android.media.MediaPlayer().apply {
                setDataSource(tempFile.absolutePath)
                setOnCompletionListener {
                    if (isCallActive) {
                        Handler(Looper.getMainLooper()).postDelayed({ startListening() }, 500)
                    }
                    tempFile.delete()
                }
                setOnErrorListener { _, _, _ ->
                    if (isCallActive) {
                        Handler(Looper.getMainLooper()).postDelayed({ startListening() }, 500)
                    }
                    tempFile.delete()
                    true
                }
                prepare()
                start()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error playing audio: ${e.message}")
            // Fallback to local TTS
            speak(responseText.text.toString())
        }
    }
    
    private fun speak(text: String) {
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, UUID.randomUUID().toString())
    }
    
    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            tts.language = Locale("hi", "IN")
            tts.setOnUtteranceProgressListener(object : android.speech.tts.UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    runOnUiThread { updateUI(CallState.SPEAKING) }
                }
                
                override fun onDone(utteranceId: String?) {
                    runOnUiThread {
                        if (isCallActive) {
                            Handler(Looper.getMainLooper()).postDelayed({ startListening() }, 500)
                        }
                    }
                }
                
                override fun onError(utteranceId: String?) {
                    runOnUiThread {
                        if (isCallActive) {
                            Handler(Looper.getMainLooper()).postDelayed({ startListening() }, 500)
                        }
                    }
                }
            })
        }
    }
    
    private fun checkServerConnection() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val request = Request.Builder()
                    .url("$serverUrl/health")
                    .get()
                    .build()
                
                client.newCall(request).execute().use { response ->
                    withContext(Dispatchers.Main) {
                        if (response.isSuccessful) {
                            updateConnectionStatus(true)
                        } else {
                            updateConnectionStatus(false)
                        }
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    updateConnectionStatus(false)
                }
            }
        }
    }
    
    private fun updateConnectionStatus(connected: Boolean) {
        if (connected) {
            connectionIndicator.backgroundTintList = ContextCompat.getColorStateList(this, R.color.green_primary)
            connectionText.text = getString(R.string.connected)
            connectionText.setTextColor(ContextCompat.getColor(this, R.color.green_primary))
        } else {
            connectionIndicator.backgroundTintList = ContextCompat.getColorStateList(this, R.color.text_muted)
            connectionText.text = getString(R.string.disconnected)
            connectionText.setTextColor(ContextCompat.getColor(this, R.color.text_muted))
        }
    }
    
    private fun updateUI(state: CallState) {
        when (state) {
            CallState.READY -> {
                statusText.text = getString(R.string.ready)
                statusText.setTextColor(ContextCompat.getColor(this, R.color.green_primary))
            }
            CallState.LISTENING -> {
                statusText.text = getString(R.string.listening)
                statusText.setTextColor(ContextCompat.getColor(this, R.color.call_ring))
            }
            CallState.PROCESSING -> {
                statusText.text = getString(R.string.processing)
                statusText.setTextColor(ContextCompat.getColor(this, R.color.blue_info))
            }
            CallState.SPEAKING -> {
                statusText.text = getString(R.string.speaking)
                statusText.setTextColor(ContextCompat.getColor(this, R.color.green_primary))
            }
        }
    }
    
    private fun showSettingsDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_settings, null)
        val nameInput = dialogView.findViewById<EditText>(R.id.nameInput)
        val serverUrlInput = dialogView.findViewById<EditText>(R.id.serverUrlInput)
        
        nameInput.setText(prefs.getString("user_name", "Agent"))
        serverUrlInput.setText(serverUrl)
        
        val dialog = AlertDialog.Builder(this)
            .setView(dialogView)
            .create()
        
        dialogView.findViewById<Button>(R.id.saveButton).setOnClickListener {
            val newName = nameInput.text.toString()
            val newUrl = serverUrlInput.text.toString()
            
            prefs.edit().apply {
                putString("user_name", newName)
                putString("server_url", newUrl)
                apply()
            }
            
            userNameText.text = newName
            serverUrl = newUrl
            checkServerConnection()
            dialog.dismiss()
        }
        
        dialogView.findViewById<Button>(R.id.cancelButton).setOnClickListener {
            dialog.dismiss()
        }
        
        dialog.show()
    }
    
    private fun checkPermissions(): Boolean {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestPermissions() {
        ActivityCompat.requestPermissions(
            this,
            arrayOf(Manifest.permission.RECORD_AUDIO),
            PERMISSION_REQUEST_CODE
        )
    }
    
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startCall()
            } else {
                Toast.makeText(this, getString(R.string.permission_required), Toast.LENGTH_LONG).show()
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        tts.shutdown()
        speechRecognizer?.destroy()
        mediaPlayer?.release()
    }
    
    enum class CallState {
        READY, LISTENING, PROCESSING, SPEAKING
    }
}
