import cv2
from deepface import DeepFace


def emotion_detection():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    # Detección de rostros y análisis de emociones
    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

    # Identificación de la emoción dominante
    emotion_counts = {}
    for face in result:
        dominant_emotion = face['dominant_emotion']
        if dominant_emotion in emotion_counts:
            emotion_counts[dominant_emotion] += 1
        else:
            emotion_counts[dominant_emotion] = 1

    if emotion_counts:
        # Determinar la emoción predominante
        max_emotion = max(emotion_counts, key=emotion_counts.get)
        return max_emotion
