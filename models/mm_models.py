import tensorflow as tf
from keras.layers import GlobalAveragePooling2D, Dropout, Dense, Flatten, Layer
from keras import Model
from config import *


def build_ConcatClf(bert, conv_base, top_dropout_rate_mm):
    MODEL = "MM-GRID-CONCAT"
    # text inputs
    in_id = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="input_ids")
    in_mask = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="attention_mask")
    in_segment = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="token_type_ids")
    # img inputs
    in_img = tf.keras.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3,), dtype="float32", name="input_imgs")
    inputs = {"input_ids": in_id,
              "attention_mask": in_mask,
              "token_type_ids": in_segment,
              "img_input": in_img
              }
    inputs_bert = inputs.copy()
    img_input = inputs_bert.pop("img_input")
    # out of img is 2048 and text is 768
    bert_out = bert(inputs_bert, return_dict=True)
    txt = bert_out.pooler_output
    img = conv_base(img_input)
    # project the img to a 768 space (same dimension as bert)
    img_dense = Dense(HFixed, name="ImgDense")(img)
    # concatenate layers
    H_fused = tf.keras.layers.Concatenate()([txt, img_dense])
    x = Dropout(top_dropout_rate_mm, name="top_dropout")(H_fused)
    output = Dense(NUM_LABELS, activation="softmax", name="pred")(x)
    # Build and compile model
    model = Model(inputs=inputs, outputs=output, name=MODEL)
    return model

def build_AttentionClf(bert, conv_base, top_dropout_rate_mm):
    MODEL = "MM-GRID-Attention"
    # text inputs
    in_id = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="input_ids")
    in_mask = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="attention_mask")
    in_segment = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="token_type_ids")
    # img inputs
    in_img = tf.keras.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3,), dtype="float32", name="input_imgs")
    inputs = {"input_ids": in_id,
              "attention_mask": in_mask,
              "token_type_ids": in_segment,
              "img_input": in_img
              }
    inputs_bert = inputs.copy()
    img_input = inputs_bert.pop("img_input")
    # out of img is 2048 and text is 768
    bert_out = bert(inputs_bert, return_dict=True)
    txt = bert_out.pooler_output
    img = conv_base(img_input)
    # project the img and text to a 200 space
    fixed = 200
    img_dense = Dense(fixed, name="ImgDense", activation=tf.nn.tanh)(img)
    txt_dense = Dense(fixed, name="TxtDense", activation=tf.nn.tanh)(txt)
    s = tf.stack([txt_dense, img_dense], axis=1)
    # Attention scores
    s_a = tf.keras.layers.Concatenate(axis=-1)([txt, img])
    s_a = Dense(fixed, activation="relu", name="Fa")(s_a)
    alpha = Dense(2, activation="softmax", name="alpha")(s_a)
    H_fused = tf.keras.layers.Dot(axes=1, name="fused")([alpha, s])
    x = Dropout(top_dropout_rate_mm, name="top_dropout")(H_fused)
    output = Dense(NUM_LABELS, activation="softmax", name="pred")(x)
    # Build and compile model
    model = Model(inputs=inputs, outputs=output, name=MODEL)
    return model

def build_GLUClf(bert, conv_base, top_dropout_rate_mm):
    MODEL = "MM-GRID-GLU"
    fixed = 200
    # text inputs
    in_id = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="input_ids")
    in_mask = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="attention_mask")
    in_segment = tf.keras.Input(shape=(MAX_SEQ,), dtype="int32", name="token_type_ids")
    # img inputs
    in_img = tf.keras.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3,), dtype="float32", name="input_imgs")
    inputs = {"input_ids": in_id,
              "attention_mask": in_mask,
              "token_type_ids": in_segment,
              "img_input": in_img
              }
    inputs_bert = inputs.copy()
    img_input = inputs_bert.pop("img_input")
    # out of img is 2048 and text is 768
    bert_out = bert(inputs_bert, return_dict=True)
    txt = bert_out.pooler_output
    img = conv_base(img_input)
    # project the img and text to a 200 space
    img_dense = Dense(fixed, name="ImgDense", activation=tf.nn.tanh)(img)
    txt_dense = Dense(fixed, name="TxtDense", activation=tf.nn.tanh)(txt)

    # concat txt and img
    txt_img = tf.keras.layers.Concatenate(axis=-1)([txt, img])
    gate_z = Dense(fixed, activation=tf.nn.sigmoid, name="Gate")(txt_img)
    H_fused = gate_z * txt_dense + (1 - gate_z) * img_dense

    # MLP
    x = Dropout(top_dropout_rate_mm, name="top_dropout")(H_fused)
    output = Dense(NUM_LABELS, activation="softmax", name="pred")(x)
    # Build and compile model
    model = Model(inputs=inputs, outputs=output, name=MODEL)
    return model







