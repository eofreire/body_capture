import cv2
import mediapipe as mp
import csv
import time
import os
import sys
import tensorflow as tf

def resource_path(relative_path):
    """Obtém o caminho correto para os recursos, considerando PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Caminhos para os modelos TFLite
pose_model_path = resource_path("mediapipe/modules/pose_landmark/pose_landmark_lite.tflite")
hand_model_path = resource_path("mediapipe/modules/hand_landmark/hand_landmark.tflite")

# Carregar os modelos manualmente
pose_model = tf.lite.Interpreter(model_path=pose_model_path)
hand_model = tf.lite.Interpreter(model_path=hand_model_path)

# Inicializar os modelos
pose_model.allocate_tensors()
hand_model.allocate_tensors()

# Inicializar MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# Configurar a captura de vídeo
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

# Variável para armazenar o timestamp do início
start_time = None

# Abrir arquivo CSV para salvar os landmarks
with open('landmarks.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    # Escrever cabeçalhos
    headers = ['elapsed_time']  # Adiciona o tempo decorrido como o primeiro cabeçalho
    for i in range(33):
        headers += [f'pose_landmark_{i}_x', f'pose_landmark_{i}_y', f'pose_landmark_{i}_z', f'pose_landmark_{i}_visibility']
    for i in range(21):
        headers += [f'left_hand_landmark_{i}_x', f'left_hand_landmark_{i}_y', f'left_hand_landmark_{i}_z']
        headers += [f'right_hand_landmark_{i}_x', f'right_hand_landmark_{i}_y', f'right_hand_landmark_{i}_z']
    writer.writerow(headers)

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=0) as holistic:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Capturar o timestamp atual
            current_timestamp = time.time()

            # Definir o timestamp inicial
            if start_time is None:
                start_time = current_timestamp

            # Calcular o tempo decorrido desde o início
            elapsed_time = current_timestamp - start_time

            # Converter a imagem para RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Processar a imagem com MediaPipe Holistic
            results = holistic.process(image)

            # Desenhar os landmarks na imagem
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
            mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

            # Mostrar a imagem em uma janela
            cv2.imshow('MediaPipe Holistic', image)

            # Salvar os landmarks e o tempo decorrido no arquivo CSV
            if results.pose_landmarks or results.left_hand_landmarks or results.right_hand_landmarks:
                landmarks = [elapsed_time]  # Adiciona o tempo decorrido como o primeiro dado
                if results.pose_landmarks:
                    for landmark in results.pose_landmarks.landmark:
                        landmarks += [landmark.x, landmark.y, landmark.z, landmark.visibility]
                else:
                    landmarks += [float('nan')] * 132  # 33 landmarks * 4 valores (x, y, z, visibility)
                if results.left_hand_landmarks:
                    for landmark in results.left_hand_landmarks.landmark:
                        landmarks += [landmark.x, landmark.y, landmark.z]
                else:
                    landmarks += [float('nan')] * 63  # 21 landmarks * 3 valores (x, y, z)
                if results.right_hand_landmarks:
                    for landmark in results.right_hand_landmarks.landmark:
                        landmarks += [landmark.x, landmark.y, landmark.z]
                else:
                    landmarks += [float('nan')] * 63  # 21 landmarks * 3 valores (x, y, z)
                writer.writerow(landmarks)

            # Finalizar se pressionar ESC
            if cv2.waitKey(10) & 0xFF == 27:
                break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
