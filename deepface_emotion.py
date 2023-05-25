import cv2
from deepface import DeepFace

# Umbral de confianza para las emociones
emotion_confidence_threshold = 30

cap = cv2.VideoCapture(0)

# Saltar n-1 fotogramas para reducir la carga de procesamiento
frame_skip_rate = 5
frame_count = 0

while True:
    ret, frame = cap.read()
    frame_count += 1

    if frame_count % frame_skip_rate == 0:
        # Detección de rostros y análisis de emociones
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

        # Dibujar rectángulo y mostrar las emociones en la ventana
        for face in result:
            x, y, w, h = face['region']['x'], face['region']['y'], face['region']['w'], face['region']['h']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            dominant_emotion = face['dominant_emotion']
            emotion_score = face['emotion'][dominant_emotion]

            if emotion_score > emotion_confidence_threshold:
                emotion_text = f"{dominant_emotion}: {emotion_score:.1f}%"
                cv2.putText(frame, emotion_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2, cv2.LINE_AA)
            print(emotion_text)
    cv2.imshow('Emotion Recognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
