import joblib
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Load the model once at the top using the full path
pipeline = joblib.load("/home/ibm-user/shared/safecircle/models/message_model.joblib")

# Get vocabulary and weights for the reasons logic
feature_names = pipeline.named_steps["tfidf"].get_feature_names_out()
coefs = pipeline.named_steps["clf"].coef_[0]

# Your updated translation dictionary
reason_dict = {
    "gift": "asks for gift cards",
    "cards": "asks for gift cards",
    "locked": "says your account is locked",
    "verify": "asks you to verify your identity",
    "link": "asks you to click a link",
    "tell": "asks you to keep it secret",
    "text": "asks you to text a code",
    "it me": "claims to be a family member",
    "account": "mentions your account",
    "your": "uses urgent language"
}

def score_message(text):
    # 1. Get the scam probability score
    prob = pipeline.predict_proba([text])[0][1]
    
    # NEW: If score is under 0.5, return empty reasons (Walter's case)
    if prob < 0.5:
        return {"score": float(prob), "reasons": []}
    
    # 2. Extract reasons
    tfidf_matrix = pipeline.named_steps["tfidf"].transform([text])
    word_scores = tfidf_matrix.toarray()[0] * coefs
    top_indices = np.argsort(word_scores)[::-1]
    
    reasons = []
    for i in top_indices:
        if word_scores[i] <= 0 or len(reasons) >= 2:
            break
            
        word = feature_names[i]
        
        # NEW: Skip filler words
        if word in ENGLISH_STOP_WORDS:
            continue
            
        if word in reason_dict:
            if reason_dict[word] not in reasons:
                reasons.append(reason_dict[word])
        else:
            reasons.append(f"uses the word '{word}'")
            
    # 3. Return the exact dictionary shape the contract requires
    return {"score": float(prob), "reasons": reasons}