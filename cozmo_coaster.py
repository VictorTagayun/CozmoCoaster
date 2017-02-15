import numpy as np
import cozmo
import asyncio
import time
from Common.woc import WOC
from Common.colors import Colors
from PIL import Image
from random import randrange
from cozmo.util import distance_mm, speed_mmps
import cv2

'''
@class CozmoCoaster
Take Cozmo on ride and make him dizzy.
@author - Wizards of Coz
'''

class CozmoCoaster(WOC):    
    def __init__(self):
        WOC.__init__(self)
        self.acceleration = [0, 0, 0]
        self.orientation = [0, 0, 0]
        self.dizzy = 0      #0 = normal, 1 = tipsy, 2 = drunk, 3 = throwing up, 4 = out of order
        self.robot = None
        self.pitch = 0
        self.interval = 0
        self.counter = 0
        cozmo.connect(self.run)               

    async def start_program(self):
        await self.robot.set_lift_height(0).wait_for_completed()
        await self.robot.set_head_angle(cozmo.util.Angle(degrees=0)).wait_for_completed()
        await self.robot.play_anim_trigger(cozmo.anim.Triggers.MeetCozmoLookFaceGetOut).wait_for_completed()
        await self.robot.say_text("Ready for lift off", use_cozmo_voice=False, voice_pitch=0, duration_scalar=1).wait_for_completed()
        img = Image.open("Media/belt.jpg")
        resized_img = img.resize(cozmo.oled_face.dimensions(), Image.BICUBIC)
        screen_data_1 = cozmo.oled_face.convert_image_to_screen_data(resized_img)
        screen_data_2 = cozmo.oled_face.convert_image_to_screen_data(resized_img, invert_image=True)
        while self.robot.is_picked_up is False:
            await self.robot.display_oled_face_image(screen_data_1, in_parallel=True, duration_ms=500).wait_for_completed()
            await self.robot.display_oled_face_image(screen_data_2, in_parallel=True, duration_ms=500).wait_for_completed()
            await asyncio.sleep(0)
        await self.robot.play_anim_trigger(cozmo.anim.Triggers.DroneModeTurboDrivingStart).wait_for_completed()

    async def fly(self):     
        while True:
            if self.robot.is_picked_up is True:
                self.counter = 0
                self.interval += 1
                if self.interval > 25:
                    self.interval = 0
                    x = randrange(3)
                    if x == 0:
                        self.robot.say_text("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", duration_scalar=0.15, voice_pitch=self.pitch, in_parallel=True)
                    elif x == 1:
                        self.robot.say_text("woooohoooo yayyyy", duration_scalar=5, voice_pitch=self.pitch, in_parallel=True)
                    elif x == 2:
                        self.robot.say_text("I can fly", duration_scalar=5, voice_pitch=self.pitch, in_parallel=True)
                    else:
                        self.robot.say_text("Faster", duration_scalar=5, voice_pitch=self.pitch, in_parallel=True)
                self.orientation = np.floor_divide([self.robot.gyro.x, self.robot.gyro.y, self.robot.gyro.z], 1)
                if np.linalg.norm(self.orientation) > 5:
                    self.dizzy += 1
                prev_accel = self.acceleration
                self.acceleration = np.floor_divide([self.robot.accelerometer.x, self.robot.accelerometer.y, self.robot.accelerometer.z], 1000)
                d_accel = np.subtract(prev_accel, self.acceleration)
                d_accel_mag = np.linalg.norm(d_accel)
                if d_accel_mag > 15:
                    self.pitch = 1
                else:
                    self.pitch = (d_accel_mag/5) - 2
            else:
                self.counter += 1
                if self.counter > 30:
                    await self.end_program()
            await asyncio.sleep(0.1)    

    async def end_program(self):
        self.robot.abort_all_actions()
        print(self.dizzy)
        dizzy_meter = np.floor_divide(self.dizzy, 500)
        if dizzy_meter > 4:
            dizzy_meter = 4
        dizzy_meter += 1
        print (dizzy_meter)
        x = 1
        for i in range(3):
            x = -x
            await self.robot.drive_straight(distance_mm(5*(10-dizzy_meter)), speed_mmps(50), False).wait_for_completed()
            await self.robot.turn_in_place(cozmo.util.Angle(degrees=(dizzy_meter)*10*x)).wait_for_completed()
            await asyncio.sleep(0)
        await self.robot.set_head_angle(cozmo.util.Angle(degrees=45)).wait_for_completed()
        await self.robot.say_text("I'm so dizzy", duration_scalar=2*(dizzy_meter), voice_pitch=-1, in_parallel=True).wait_for_completed()

        while True:
            vidcap = cv2.VideoCapture("Media/" + str(dizzy_meter) + ".gif")
            success, image = vidcap.read()
            success = True
            while success:
                img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                resized_img = img.resize(cozmo.oled_face.dimensions(), Image.BICUBIC)
                screen_data = cozmo.oled_face.convert_image_to_screen_data(resized_img) 
                await self.robot.display_oled_face_image(screen_data, in_parallel=True, duration_ms=1).wait_for_completed()
                success,image = vidcap.read()                
            await asyncio.sleep(0)
        
    async def run(self, conn):
        asyncio.set_event_loop(conn._loop)
        self.robot = await conn.wait_for_robot()
        await self.start_program()
        await self.fly()

if __name__ == '__main__':
    CozmoCoaster()