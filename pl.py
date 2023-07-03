import cv2
import mysql.connector
from mysql.connector import Error
import torch
from yolov7.models.experimental import attempt_load
from yolov7.utils.datasets import LoadStreams
from yolov7.utils.general import check_img_size, non_max_suppression, scale_coords
from yolov7.utils.torch_utils import select_device

# Set device
device = select_device('')

# Load modelll
model = attempt_load('best.pt', map_location=device)
imgsz = check_img_size(640, s=model.stride.max())

# Set half precision
model.half()

# Load data
dataset = LoadStreams('0', img_size=imgsz)

# Connect to the MySQL database
try:
    connection = mysql.connector.connect(host='localhost',
                                         database='database_name',
                                         user='user_name',
                                         password='password')
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)

except Error as e:
    print("Error while connecting to MySQL", e)

# Run inference
for path, img, im0s, vid_cap in dataset:
    img = torch.from_numpy(img).to(device)
    img = img.half()
    img /= 255.0
    if img.ndimension() == 3:
        img = img.unsqueeze(0)

    # Inference
    pred = model(img)[0]

    # Apply NMS
    pred = non_max_suppression(pred)

    # Process detections
    for i, det in enumerate(pred):
        p, s, im0 = path[i], f'{i}: ', im0s[i].copy()

        # Rescale boxes from img_size to im0 size
        det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

        # Print results
        for c in det[:, -1].unique():
            n = (det[:, -1] == c).sum()
            s += f"{n} {model.names[int(c)]}{'s' * (n > 1)}, "

        # Write results and insert into the MySQL database
        for *xyxy, conf, cls in reversed(det):
            label = f'{model.names[int(cls)]} {conf:.2f}'
            print(label)
            query = "INSERT INTO predictions (label, confidence) VALUES (%s, %s)"
            values = (model.names[int(cls)], conf.item())
            cursor.execute(query, values)

connection.commit()
print(cursor.rowcount, "Record inserted successfully into predictions table")

# Close the MySQL connection
if connection.is_connected():
    cursor.close()
    connection.close()
    print("MySQL connection is closed")
