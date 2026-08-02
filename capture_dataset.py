import cv2
import os
import time

# ==========================
# NHẬP TÊN ĐIỆN THOẠI
# ==========================

PHONE_NAME = input("Tên điện thoại: ").strip()

SAVE_PATH = os.path.join(
    "dataset",
    "images",
    PHONE_NAME
)

os.makedirs(SAVE_PATH, exist_ok=True)

# ==========================

camera = cv2.VideoCapture(0)

camera.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT,720)

print("="*50)
print("SPACE : Chụp ảnh")
print("A     : Chụp tự động")
print("ESC   : Thoát")
print("="*50)

count = len(os.listdir(SAVE_PATH))

auto_capture = False

last_capture = time.time()

while True:

    ret, frame = camera.read()

    if not ret:
        break

    show = frame.copy()

    cv2.putText(
        show,
        f"Phone : {PHONE_NAME}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )

    cv2.putText(
        show,
        f"Images : {count}",
        (20,80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,255),
        2
    )

    cv2.imshow("Capture Dataset",show)

    key = cv2.waitKey(1)

    # SPACE

    if key == 32:

        filename = os.path.join(
            SAVE_PATH,
            f"{count:04d}.jpg"
        )

        cv2.imwrite(filename,frame)

        print("Saved",filename)

        count += 1

    # AUTO

    if key == ord("a"):

        auto_capture = not auto_capture

        print("Auto :",auto_capture)

    if auto_capture:

        if time.time()-last_capture>0.5:

            filename = os.path.join(
                SAVE_PATH,
                f"{count:04d}.jpg"
            )

            cv2.imwrite(filename,frame)

            print("Saved",filename)

            count += 1

            last_capture=time.time()

    if key==27:
        break

camera.release()

cv2.destroyAllWindows()
