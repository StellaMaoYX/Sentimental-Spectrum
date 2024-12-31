# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 14:39:09 2023

@author: Stella
@EID: 56641467
"""

import sys
import os
from joblib import dump, load

########## Data Processing ##########

import pandas as pd
import numpy as np
import neattext.functions as nfx
import cv2

# load the dataset
df = pd.read_csv("input/emotion-dataset.csv")

# check how the dataset is structured
df.head()
df['Emotion'].value_counts()

# list all the methods and attributes used by neattext for data cleaning
dir(nfx)

print("Read dataset...")

########## Text -- Machine Learning ##########

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn import svm

# Text data and labels
X_train = df['Text']
y_train = df['Emotion'] #totally 7 labels

# Apply a count vectorizer. The n-gram range can be changed.
vectorizer = CountVectorizer(ngram_range=(2, 2))

# Output of the vectorizer X. 
X = vectorizer.fit_transform(X_train)

# Apply the tfidf transformer that will scale to (0,1)
tfidf = TfidfTransformer( norm = 'l2')
# pass the X, which is the output of the vectorizer
X_tfidf = tfidf.fit_transform(X)

########## Color -- Machine Learning ##########

import matplotlib.pyplot as plt
from sklearn.cluster import MiniBatchKMeans

# Define the emotion labels and color numbers
emotions = ['anger', 'disgust', 'fear', 'joy', 'sadness', 'surprise']
num_colors = 64

print("Loading the images")

# Load image data
def load_images(emotions):
    data = []
    labels = []
    target_size = (50, 50)
    for idx, emotion in enumerate(emotions):
        folder_path = os.path.join("input/emotion-images", emotion)
        for filename in os.listdir(folder_path):
            image_path = os.path.join(folder_path, filename)
            img = cv2.imread(image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # Resize the image
            img = cv2.resize(img, target_size)
            data.append(img)
            labels.append(idx)
    return np.array(data, dtype=object), np.array(labels, dtype=object)

data, labels = load_images(emotions)

# Extract the color palette and combine them into the color plate
def extract_color_palette(image):
    image = image.reshape((-1, 3))  # Transform into a 1D matrix
    km = MiniBatchKMeans(n_clusters=num_colors)
    km.fit(image)
    palette_colors = km.cluster_centers_
    return palette_colors.reshape((num_colors, 1, 3))

print("Getting the color palette...")



########## Check and load existing models ##########

classifier_model_filename = "emotion_classifier_model.pkl"
color_model_filename = "color_clustering_model.pkl"

if os.path.exists(classifier_model_filename) and os.path.exists(color_model_filename):
    classifier = load(classifier_model_filename)
    emotion_palette = load(color_model_filename)
else:
    # Train new models if existing ones are not found
    classifier = svm.SVC(kernel="linear", decision_function_shape="ovr")
    classifier.fit(X_tfidf, y_train)
    
    # Train color clustering model
    # Generate each emotion's color plate
    emotion_palette = []
    
    for i, emotion in enumerate(emotions):
        km = MiniBatchKMeans(n_clusters=num_colors)
        emotion_images = data[labels == i]
        for img in emotion_images:
            img = img.reshape((-1, 3))
            km.partial_fit(img)
        palette_colors = km.cluster_centers_
        print("Shape of palette colors", palette_colors.shape)
        emotion_palette.append(palette_colors)
    
    emotion_palette = np.array(emotion_palette)
    
    # Save the models for future use
    dump(classifier, classifier_model_filename)
    dump(emotion_palette, color_model_filename)

print("Finish text training...")

########## Predict the emotion ##########

# Input -- one single sentence
X_test = input('Write a sentence to describe your current feeling\n')
# Vectorize it
X_vectorized = vectorizer.transform([X_test])
# Scale it
X_scaled = tfidf.transform(X_vectorized)
# Now predict
pred = classifier.predict(X_scaled)
print(pred)

if pred == ['neutral']:
    sys.exit()

# Reshape emotion_palette to a suitable shape
emotion_palette_reshaped = emotion_palette.reshape(8, 8, -1)
for i in range(0, 6):
    if emotions[i] == pred[0]:
        selected_palette_idx = i
        break

selected_palette = emotion_palette[i]
selected_palette = selected_palette.reshape(8, 8, 3)

plt.figure(figsize=(8, 8))
plt.imshow(selected_palette.astype(np.uint8))
plt.title(pred)
plt.axis('off')
plt.show()
