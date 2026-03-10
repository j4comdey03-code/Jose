from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture

import cv2
import numpy as np
import time


class JosephApp(App):

    def build(self):

        layout = BoxLayout(orientation='vertical')

        self.img = Image()
        layout.add_widget(self.img)

        controls = BoxLayout(orientation='vertical', size_hint_y=0.35)

        controls.add_widget(Label(text="Stump Position"))
        self.stump_slider = Slider(min=0, max=640, value=320)
        controls.add_widget(self.stump_slider)

        controls.add_widget(Label(text="Pitch Line"))
        self.pitch_slider = Slider(min=0, max=480, value=300)
        controls.add_widget(self.pitch_slider)

        controls.add_widget(Label(text="Stump Height"))
        self.stump_height_slider = Slider(min=50, max=300, value=150)
        controls.add_widget(self.stump_height_slider)

        layout.add_widget(controls)

        self.cap = cv2.VideoCapture(0)

        self.prev_center = None
        self.prev_time = None
        self.ball_positions = []

        Clock.schedule_interval(self.update, 1/30)

        return layout


    def detect_ball(self, frame):

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower = np.array([0,120,70])
        upper = np.array([10,255,255])

        mask = cv2.inRange(hsv, lower, upper)

        contours,_ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:

            if cv2.contourArea(cnt) > 300:

                x,y,w,h = cv2.boundingRect(cnt)
                return (x+w//2 , y+h//2)

        return None


    def calculate_speed(self, center, frame):

        if self.prev_center is None:
            self.prev_center = center
            self.prev_time = time.time()
            return

        dist = np.linalg.norm(np.array(center)-np.array(self.prev_center))
        time_diff = time.time() - self.prev_time

        self.prev_center = center
        self.prev_time = time.time()

        if time_diff > 0:

            speed = (dist/time_diff) * 0.036

            cv2.putText(frame,
                        f"Speed: {speed:.1f} km/h",
                        (20,40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0,255,0),
                        2)


    def detect_swing(self, center, frame):

        if self.prev_center is None:
            return

        dx = center[0] - self.prev_center[0]

        if dx > 5:
            swing = "OUTSWING"

        elif dx < -5:
            swing = "INSWING"

        else:
            swing = "NO SWING"

        cv2.putText(frame,
                    swing,
                    (20,80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255,255,0),
                    2)


    def predict_trajectory(self, frame):

        if len(self.ball_positions) < 5:
            return

        pts = np.array(self.ball_positions)

        x = pts[:,0]
        y = pts[:,1]

        curve = np.polyfit(x,y,2)

        for i in range(0,640,10):

            y_pred = int(curve[0]*i*i + curve[1]*i + curve[2])

            if 0 < y_pred < 480:
                cv2.circle(frame,(i,y_pred),3,(0,0,255),-1)


    def lbw_decision(self, center, frame, stump_x, pitch_y, stump_height):

        if center[1] > pitch_y:

            if abs(center[0]-stump_x) < 35 and center[1] < pitch_y + stump_height:

                cv2.putText(frame,
                            "LBW OUT",
                            (20,120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.5,
                            (0,0,255),
                            3)

            else:

                cv2.putText(frame,
                            "NOT OUT",
                            (20,120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.5,
                            (0,255,0),
                            3)


    def update(self, dt):

        ret, frame = self.cap.read()

        if not ret:
            return

        frame = cv2.resize(frame,(640,480))

        stump_x = int(self.stump_slider.value)
        pitch_y = int(self.pitch_slider.value)
        stump_height = int(self.stump_height_slider.value)

        center = self.detect_ball(frame)

        if center:

            cv2.circle(frame,center,10,(0,255,0),-1)

            self.detect_swing(center,frame)

            self.calculate_speed(center,frame)

            self.ball_positions.append(center)

            if len(self.ball_positions) > 20:
                self.ball_positions.pop(0)

            self.predict_trajectory(frame)

            self.lbw_decision(center,frame,stump_x,pitch_y,stump_height)


        cv2.line(frame,(stump_x,0),(stump_x,480),(255,0,0),2)

        cv2.line(frame,(0,pitch_y),(640,pitch_y),(0,255,255),2)

        cv2.rectangle(frame,
                      (stump_x-35,pitch_y),
                      (stump_x+35,pitch_y+stump_height),
                      (255,0,255),
                      2)


        buf = cv2.flip(frame,0).tobytes()

        texture = Texture.create(size=(frame.shape[1],frame.shape[0]), colorfmt='bgr')

        texture.blit_buffer(buf,colorfmt='bgr',bufferfmt='ubyte')

        self.img.texture = texture


if __name__ == "__main__":
    JosephApp().run()
