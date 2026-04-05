import numpy as np
import tensorflow as tf
from tensorflow import keras
import keras
from tensorflow.keras import layers
from tensorflow.keras.layers import Layer
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers.schedules import ExponentialDecay
# from tensorflow.keras.layers import Lambda
# import tensorflow_addons as tfa
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import pandas as pd
import pickle
from describeDefect import describe_defect_types

label_keys = ["Center", "Donut", "Edge_Local", "Edge_Ring",
                          "Local", "Near_Full", "Scratch", "Random"]
def read_label(label, defect_types =[]):

      """this funtion is to translate the label into defect_types

      Args:
          label(list): the label that indicate type of  defect, for instance [0 1 0 1 0 0 0 1]

      Return:
          defect_types(string): the string that indicate defect type
      """

      if np.sum(label) == 0:
          defect_types = []

      else:
          for digit in range(np.shape(label)[0]):

              if label[digit] == 1:

                  defect_types.append(label_keys[digit])

      return list(set(defect_types))
class PatchExtractorLayer(Layer):
    def __init__(self, patch_size):
        super(PatchExtractorLayer, self).__init__()
        self.patch_size = patch_size

    def call(self, images):
        batch_size = tf.shape(images)[0]
        patches = tf.image.extract_patches(
            images=images,
            sizes=[1, self.patch_size, self.patch_size, 1],
            strides=[1, self.patch_size, self.patch_size, 1],
            rates=[1, 1, 1, 1],
            padding="VALID",
        )
        patch_dims = patches.shape[-1]
        patches = tf.reshape(patches, [batch_size, -1, patch_dims])
        return patches
def extract_patches(images, patch_size):
    return tf.image.extract_patches(
        images=images,
        sizes=[1, patch_size, patch_size, 1],
        strides=[1, patch_size, patch_size, 1],
        rates=[1, 1, 1, 1],
        padding="VALID"
    )

# def reshape_patches(patches, batch_size, patch_dims):
    return tf.reshape(patches, [batch_size, -1, patch_dims])
# def reshape_patches(x):
    batch_size = tf.shape(x)[0]
    return tf.reshape(x, [batch_size, -1, patch_dims])

# Infer the output shape
# def output_shape(input_shape):
    batch_size = input_shape[0]
    num_patches = (input_shape[1] // patch_size) * (input_shape[2] // patch_size)
    return (batch_size, num_patches, patch_dims)

def get_patches(images):
    """this funtion is to split image into patches of "self.patch_size" x "self.patch_size"

    Args:
        images(array): the images to applied patches

    Return:
        patches(array): the image patches

    """
    patch_size = 13
    batch_size = tf.shape(images)[0]
    patches = tf.image.extract_patches(
        images=images,
        sizes=[1, patch_size, patch_size, 1],
        strides=[1, patch_size, patch_size, 1],
        rates=[1, 1, 1, 1],
        padding="VALID",
    )
    patch_dims = patches.shape[-1]

    patches = tf.reshape(patches, [batch_size, -1, patch_dims])
    return patches



def get_patchencoder(patch, images):
    """this funtion is encode the patch as projection on dense layer with position embedding

    Args:
        patch(array): the images to applied patches

    Return:
        encoded(oject): the encoded patches

    """
    patch_size = 13
    projection_dim = 96
    (_, image_size, b, c) = np.shape(images)
    num_patches = 16
    projection = layers.Dense(units=projection_dim)
    position_embedding = layers.Embedding(input_dim=num_patches, output_dim=projection_dim)
    positions = tf.range(start=0, limit=num_patches, delta=1)
    encoded = projection(patch) + position_embedding(positions)

    return encoded


def mlp(x, hidden_units, dropout_rate):
    """this funtion is multilayer perceptron(mpl) head

    Args:
        hidden_units(list): the hidden dimenstion of the mpl
        dropout_rate(float): dropout rate of mpl

    """

    for units in hidden_units:
        x = layers.Dense(units, activation=tf.nn.gelu)(x)
        x = layers.Dropout(dropout_rate)(x)

    return x

def create_model():

    """this funtion is to create visual transformer

    Return:
        model(object): visual transformer model

    """
    transformer_layers = 16
    num_heads = 4
    projection_dim = 96
    transformer_units = [projection_dim * 2, projection_dim, ]
    mlp_head_units = [2048, 1024]
    label_size = 8
    inputs = layers.Input(shape=(52, 52, 1))

    # Augment data.
    images = inputs  # data_augmentation(inputs)

    # Create patches.
    # patches = get_patches(images)
    patches = PatchExtractorLayer(13)(images)
    # Encode patches.
    encoded_patches = get_patchencoder(patches, images)

    # print(np.shape(encoded_patches))

    # Create multiple layers of the Transformer block.

    for _ in range(transformer_layers):
        # Layer normalization 1.
        x1 = layers.LayerNormalization(epsilon=1e-6)(encoded_patches)

        # Create a multi-head attention layer.
        attention_output = layers.MultiHeadAttention(num_heads=num_heads, key_dim=projection_dim, dropout=0.1)(x1,x1)

        # print(np.shape(attention_output))

        # Skip connection 1.
        x2 = layers.Add()([attention_output, encoded_patches])

        # Layer normalization 2.
        x3 = layers.LayerNormalization(epsilon=1e-6)(x2)

        # MLP.
        x3 = mlp(x3, hidden_units=transformer_units, dropout_rate=0.1)

        # Skip connection 2.
        encoded_patches = layers.Add()([x3, x2])

    # print('encoded_patches:', np.shape(encoded_patches))

    # Create a [batch_size, projection_dim] tensor.
    representation = layers.LayerNormalization(epsilon=1e-6)(encoded_patches)
    representation = layers.Flatten()(representation)
    representation = layers.Dropout(0.2)(representation)

    # print('representation:', np.shape(representation))

    # Add MLP.
    features = mlp(representation, hidden_units=mlp_head_units, dropout_rate=0.5)

    # print('features:', np.shape(features))

    # Classify outputs.
    # features = layers.Dense(label_size*2, kernel_initializer='he_uniform', activation='relu')(features)
    logits = layers.Dense(label_size, activation='sigmoid')(features)

    # Create the Keras model.
    model = keras.Model(inputs=inputs, outputs=logits)

    # print(model.summary())

    return model

def load_model(path, plot=False):
    """this funtion is to load the training weight of the visual transformer model

    Args:
        path(string): model oject address, and it will be use for history loading file too

    Return:
        self.model_vit(oject): the visual transformer model with loaded weight

    """
    model_vit = create_model()
    model_vit.load_weights(path)
    lr_schedule = ExponentialDecay(initial_learning_rate=1e-3, decay_steps=10000,decay_rate=0.9)
    opt = tf.keras.optimizers.Adam(lr_schedule)

    model_vit.compile(optimizer=opt, loss='binary_crossentropy',
                      metrics=[keras.metrics.BinaryAccuracy(name="accuracy")])

    # with open(path+'_history', "rb") as file_pi:
    #     history = pickle.load(file_pi)

    # if (plot):
    #     # Plot training and validation loss
    #     plt.figure(dpi=100)  # You can adjust the figure size if needed

    #     plt.plot(history['val_accuracy'], label='Validation accuracy')
    #     plt.plot(history['accuracy'], label='Training accuracy')

    #     plt.plot(history['val_loss'], label='Validation loss')
    #     plt.plot(history['loss'], label='Training Loss')

    #     plt.legend()
    #     plt.xlabel('Epochs')
    #     plt.ylabel('Loss')
    #     plt.show()

    return model_vit

def find_defects(test):
    path='/home/sbna/Documents/WaferDefectDetector/model_og.h5'
    VT = load_model(path)
    output = VT.predict(test, verbose=1)
    # print(output)
    # output_label = np.array(["{:.0f}".format(val) for val in output]).astype(float)
    output_label = np.array(["{:.0f}".format(val) for val in output[0]]).astype(float)
    return describe_defect_types(read_label(output_label))

if __name__ == "__main__":
    # model = '/home/sbna/Documents/work/myModel'
    path = "npy_files/image3.npy"
    array = np.load(path, allow_pickle=True)
    array = np.expand_dims(array, -1)  # Add batch dimension
    image = np.array([array])
    print(find_defects(image))

