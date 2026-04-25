package com.vyapaarsetu.aitester.data.model

/**
 * Voice session data model.
 * Stores complete audit trail of each voice interaction.
 */
data class VoiceSession(
    val id: Long = 0,
    val sessionId: String,
    val timestamp: Long = System.currentTimeMillis(),
    val customerName: String,
    val transcript: String,
    val detectedLanguage: String,
    val languageConfidence: Float,
    val intent: String,
    val intentConfidence: Float,
    val gateDecision: String,
    val paymentDecision: String,
    val finalStatus: String,
    val durationSeconds: Int,
    val languageSwitches: Int,
    val botResponse: String,
    val extractedEntities: Map<String, String> = emptyMap()
)

/**
 * Order data model
 */
data class Order(
    val id: Long = 0,
    val orderId: String,
    val customerName: String,
    val amount: Int,
    val items: String,
    val status: OrderStatus,
    val language: String,
    val paymentMode: PaymentMode,
    val timestamp: Long = System.currentTimeMillis(),
    val sessionId: String? = null
)

enum class OrderStatus {
    PENDING,
    CONFIRMED,
    CANCELLED,
    MODIFIED,
    PAYMENT_PENDING,
    PAYMENT_COMPLETED;

    fun getDisplayName(): String = when (this) {
        PENDING -> "Pending"
        CONFIRMED -> "Confirmed"
        CANCELLED -> "Cancelled"
        MODIFIED -> "Modified"
        PAYMENT_PENDING -> "Payment Pending"
        PAYMENT_COMPLETED -> "Payment Completed"
    }

    fun getEmoji(): String = when (this) {
        PENDING -> "⏳"
        CONFIRMED -> "✅"
        CANCELLED -> "❌"
        MODIFIED -> "✏️"
        PAYMENT_PENDING -> "💳"
        PAYMENT_COMPLETED -> "💰"
    }
}

enum class PaymentMode {
    PAY_NOW,
    UDHAAR,
    PARTIAL,
    NONE;

    fun getDisplayName(): String = when (this) {
        PAY_NOW -> "Pay Now"
        UDHAAR -> "Udhaar"
        PARTIAL -> "Partial"
        NONE -> "None"
    }
}

/**
 * Payment event for soundbox alerts
 */
data class PaymentEvent(
    val customerName: String,
    val amount: Int,
    val language: String,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * Audit log entry
 */
data class AuditLog(
    val sessionId: String,
    val timestamp: Long,
    val customerName: String,
    val transcript: String,
    val detectedLanguage: String,
    val languageConfidence: Float,
    val intent: String,
    val intentConfidence: Float,
    val gateDecision: String,
    val paymentDecision: String,
    val finalStatus: String,
    val durationSeconds: Int,
    val languageSwitches: Int
)

/**
 * Dashboard statistics
 */
data class DashboardStats(
    val totalOrders: Int,
    val confirmedOrders: Int,
    val udhaarAmount: Int,
    val paymentsReceived: Int,
    val languageDistribution: Map<String, Int>,
    val averageConfidence: Float,
    val recentOrders: List<Order>
)
