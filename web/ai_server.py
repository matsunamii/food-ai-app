from flask import Flask, request, jsonify
import onnxruntime as ort
import numpy as np
import cv2
from PIL import Image

app = Flask(__name__)

session = None
input_name = None

def get_session():
    global session, input_name

    if session is None:
        session = ort.InferenceSession("best.onnx")
        input_name = session.get_inputs()[0].name

    return session, input_name

# 前処理
def preprocess(img):

    img = cv2.resize(img,(640,640))
    img = img.astype(np.float32)/255.0
    img = np.transpose(img,(2,0,1))
    img = np.expand_dims(img,0)

    return img

# API
@app.route("/analyze", methods=["POST"])
def analyze():

    if "image" not in request.files:
        return jsonify({"error":"image not found"}),400

    file = request.files["image"]

    image = Image.open(file).convert("RGB")
    img = np.array(image)

    input_img = preprocess(img)

    session, input_name = get_session()

    outputs = session.run(None,{input_name:input_img})

    preds = outputs[0][0]
    preds = preds.transpose(1,0)

    boxes = []
    confidences = []
    class_ids = []

    for p in preds:

        cx,cy,w,h = p[:4]

        scores = p[4:]
        cls = int(np.argmax(scores))
        score = float(scores[cls])

        if score < 0.01:
            continue

        x1 = int(cx - w/2)
        y1 = int(cy - h/2)
        x2 = int(cx + w/2)
        y2 = int(cy + h/2)

        boxes.append([x1,y1,x2-x1,y2-y1])
        confidences.append(score)
        class_ids.append(cls)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.01, 0.45)

    results = []

    if len(indices) > 0:

        for i in indices:

            i = i[0] if isinstance(i,(list,tuple,np.ndarray)) else i

            x,y,w,h = boxes[i]

            results.append({
                "class_id":int(class_ids[i]),
                "score":float(confidences[i]),
                "bbox":[int(x),int(y),int(x+w),int(y+h)]
            })

    return jsonify(results)
