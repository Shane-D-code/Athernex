package com.vyapaarsetu.aitester.data.model

import com.google.gson.annotations.SerializedName

/**
 * Result of intent classification from Claude API.
 * Maps to the Python backend's intent classification output.
 */
data class IntentResult(
    @SerializedName("primary_intent")
    val primaryIntent: PrimaryIntent,
    
    @SerializedName("payment_intent")
    val paymentIntent: PaymentIntent,
    
    @SerializedName("modification_type")
    val modificationType: ModificationType?,
    
    val sentiment: Sentiment,
    val confidence: Float,              // 0.0 - 1.0
    
    @SerializedName("ambiguity_flag")
    val ambiguityFlag: Boolean,
    
    @SerializedName("clarification_needed")
    val clarificationNeeded: String?,
    
    @SerializedName("extracted_entities")
    val extractedEntities: Map<String, String> = emptyMap(),
    
    @SerializedName("bot_response_suggestion")
    val botResponseSuggestion: String
)

enum class PrimaryIntent {
    @SerializedName("confirm_order")
    CONFIRM_ORDER,
    
    @SerializedName("cancel_order")
    CANCEL_ORDER,
    
    @SerializedName("modify_order")
    MODIFY_ORDER,
    
    @SerializedName("confused")
    CONFUSED,
    
    @SerializedName("payment_query")
    PAYMENT_QUERY,
    
    @SerializedName("complaint")
    COMPLAINT,
    
    @SerializedName("unknown")
    UNKNOWN;

    fun getDisplayName(): String = when (this) {
        CONFIRM_ORDER -> "Confirm Order"
        CANCEL_ORDER -> "Cancel Order"
        MODIFY_ORDER -> "Modify Order"
        CONFUSED -> "Confused"
        PAYMENT_QUERY -> "Payment Query"
        COMPLAINT -> "Complaint"
        UNKNOWN -> "Unknown"
    }

    fun getEmoji(): String = when (this) {
        CONFIRM_ORDER -> "✅"
        CANCEL_ORDER -> "❌"
        MODIFY_ORDER -> "✏️"
        CONFUSED -> "❓"
        PAYMENT_QUERY -> "💳"
        COMPLAINT -> "😠"
        UNKNOWN -> "🤷"
    }

    fun getColor(): androidx.compose.ui.graphics.Color = when (this) {
        CONFIRM_ORDER -> androidx.compose.ui.graphics.Color(0xFF2E7D32)
        CANCEL_ORDER -> androidx.compose.ui.graphics.Color(0xFFC62828)
        MODIFY_ORDER -> androidx.compose.ui.graphics.Color(0xFF1976D2)
        CONFUSED -> androidx.compose.ui.graphics.Color(0xFFF57C00)
        PAYMENT_QUERY -> androidx.compose.ui.graphics.Color(0xFF7B1FA2)
        COMPLAINT -> androidx.compose.ui.graphics.Color(0xFFD32F2F)
        UNKNOWN -> androidx.compose.ui.graphics.Color(0xFF757575)
    }
}

enum class PaymentIntent {
    @SerializedName("pay_now")
    PAY_NOW,
    
    @SerializedName("pay_later")
    PAY_LATER,
    
    @SerializedName("udhaar")
    UDHAAR,
    
    @SerializedName("partial_payment")
    PARTIAL_PAYMENT,
    
    @SerializedName("none")
    NONE;

    fun getDisplayName(): String = when (this) {
        PAY_NOW -> "Pay Now"
        PAY_LATER -> "Pay Later"
        UDHAAR -> "Udhaar"
        PARTIAL_PAYMENT -> "Partial Payment"
        NONE -> "None"
    }

    fun getEmoji(): String = when (this) {
        PAY_NOW -> "💰"
        PAY_LATER -> "⏰"
        UDHAAR -> "📝"
        PARTIAL_PAYMENT -> "💵"
        NONE -> "➖"
    }
}

enum class ModificationType {
    @SerializedName("change_address")
    CHANGE_ADDRESS,
    
    @SerializedName("change_quantity")
    CHANGE_QUANTITY,
    
    @SerializedName("change_time")
    CHANGE_TIME,
    
    @SerializedName("none")
    NONE;

    fun getDisplayName(): String = when (this) {
        CHANGE_ADDRESS -> "Change Address"
        CHANGE_QUANTITY -> "Change Quantity"
        CHANGE_TIME -> "Change Time"
        NONE -> "None"
    }
}

enum class Sentiment {
    @SerializedName("positive")
    POSITIVE,
    
    @SerializedName("neutral")
    NEUTRAL,
    
    @SerializedName("negative")
    NEGATIVE,
    
    @SerializedName("angry")
    ANGRY;

    fun getEmoji(): String = when (this) {
        POSITIVE -> "😊"
        NEUTRAL -> "😐"
        NEGATIVE -> "😟"
        ANGRY -> "😠"
    }

    fun getColor(): androidx.compose.ui.graphics.Color = when (this) {
        POSITIVE -> androidx.compose.ui.graphics.Color(0xFF2E7D32)
        NEUTRAL -> androidx.compose.ui.graphics.Color(0xFF757575)
        NEGATIVE -> androidx.compose.ui.graphics.Color(0xFFF57C00)
        ANGRY -> androidx.compose.ui.graphics.Color(0xFFC62828)
    }
}

/**
 * Confidence gate decision based on intent confidence
 */
enum class ConfidenceGate {
    PROCEED,
    ASK_CLARIFICATION,
    ESCALATE_TO_HUMAN;

    fun getDisplayName(): String = when (this) {
        PROCEED -> "Proceed"
        ASK_CLARIFICATION -> "Ask Clarification"
        ESCALATE_TO_HUMAN -> "Escalate to Human"
    }

    fun getColor(): androidx.compose.ui.graphics.Color = when (this) {
        PROCEED -> androidx.compose.ui.graphics.Color(0xFF2E7D32)
        ASK_CLARIFICATION -> androidx.compose.ui.graphics.Color(0xFFF57C00)
        ESCALATE_TO_HUMAN -> androidx.compose.ui.graphics.Color(0xFFC62828)
    }

    fun getEmoji(): String = when (this) {
        PROCEED -> "✅"
        ASK_CLARIFICATION -> "❓"
        ESCALATE_TO_HUMAN -> "👤"
    }
}

/**
 * Extension functions
 */
fun IntentResult.getConfidenceGate(): ConfidenceGate {
    return when {
        confidence >= 0.80f && !ambiguityFlag -> ConfidenceGate.PROCEED
        confidence >= 0.60f -> ConfidenceGate.ASK_CLARIFICATION
        sentiment == Sentiment.ANGRY -> ConfidenceGate.ESCALATE_TO_HUMAN
        else -> ConfidenceGate.ASK_CLARIFICATION
    }
}

fun IntentResult.getConfidenceColor(): androidx.compose.ui.graphics.Color {
    return when {
        confidence >= 0.80f -> androidx.compose.ui.graphics.Color(0xFF2E7D32)
        confidence >= 0.60f -> androidx.compose.ui.graphics.Color(0xFFF57C00)
        else -> androidx.compose.ui.graphics.Color(0xFFC62828)
    }
}
