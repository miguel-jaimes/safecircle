import os, joblib
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
pipe = joblib.load("/home/ibm-user/shared/safecircle/models/message_model.joblib")
clf = pipe.named_steps["clf"]
W, b = clf.coef_.T.astype("float32"), clf.intercept_.astype("float32")
model = tf.keras.Sequential([tf.keras.Input(shape=(W.shape[0],)),
                             tf.keras.layers.Dense(1, activation="sigmoid")])
model.layers[0].set_weights([W, b])
X = pipe.named_steps["tfidf"].transform(["Grandma it's me, please buy gift cards"] * 2000).toarray().astype("float32")
print("scores:", model(X, training=False).numpy()[:3, 0])
