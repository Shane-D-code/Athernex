package com.vyapaarsetu.aitester.data.model

import com.google.gson.annotations.SerializedName

data class IntentResult(
    val primaryIntent: PrimaryIntent,
    val paymentIntent: PaymentIntent,
    val modificationType: ModificationType?,
    val sentiment: Sentiment,
    val confidence: Float,
    val ambiguityFlag: Boolean,
    val clarificationNeeded: String?,
    val extractedEntities: Map<String, String>,
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
}

enum class PaymentIntent {
    @SerializedName("pay_now")
    PAY_NOW,
    
    @SerializedName("udhaar")
    UDHAAR,
    
    @SerializedName("partial")
    PARTIAL,
    
    @SerializedName("none")
    NONE;
    
    fun getDisplayName(): String = when (this) {
        PAY_NOW -> "Pay Now"
        UDHAAR -> "Udhaar"
        PARTIAL -> "Partial"
        NONE -> "None"
    }
}

enum class ModificationType {
    @SerializedName("add_item")
    ADD_ITEM,
    
    @SerializedName("remove_item")
    REMOVE_ITEM,
    
    @SerializedName("change_quantity")
    CHANGE_QUANTITY,
    
    @SerializedName("change_time")
    CHANGE_TIME;
    
    fun getDisplayName(): String = when (this) {
        ADD_ITEM -> "Add Item"
        REMOVE_ITEM -> "Remove Item"
        CHANGE_QUANTITY -> "Change Quantity"
        CHANGE_TIME -> "Change Time"
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
    
    fun getDisplayName(): String = when (this) {
        POSITIVE -> "Positive"
        NEUTRAL -> "Neutral"
        NEGATIVE -> "Negative"
        ANGRY -> "Angry"
    }
}

enum class ConfidenceGate {
    PROCEED,
    ASK_CLARIFICATION,
    ESCALATE_TO_HUMAN
}
