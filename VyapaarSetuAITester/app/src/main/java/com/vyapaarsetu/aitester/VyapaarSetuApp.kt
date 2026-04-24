package com.vyapaarsetu.aitester

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * Application class for VyapaarSetu AI Tester.
 * Initializes Hilt dependency injection.
 */
@HiltAndroidApp
class VyapaarSetuApp : Application() {
    
    override fun onCreate() {
        super.onCreate()
        // Initialize any global components here
    }
}
