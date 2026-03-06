from flask import Flask, render_template, request
import cv2
import numpy as np

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    
    file = request.files['image']
    
    if file:
        img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x,y,w,h) in faces:
            cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

        cv2.imwrite('static/result.jpg', img)

        return render_template('index.html', result=True)

    return render_template('index.html', result=False)

if __name__ == '__main__':
    app.run(debug=True)