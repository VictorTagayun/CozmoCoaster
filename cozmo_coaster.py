import numpy as np
import cozmo
import asyncio
from PIL import Image
import _thread
import os
import random

'''
@class CozmoCoaster
Take Cozmo on a ride and make him dizzy.
@author - Wizards of Coz
'''

class CozmoCoaster():    
    def __init__(self):
        self.pitch = 0
        self.dizzy = 0      #0 = normal, 1 = tipsy, 2 = drunk, 3 = throwing up, 4 = out of order
        self.robot = None
        cozmo.connect(self.run)

    async def capture_values(self):
        #caluclate dizziness and voice pitch according to accelerometer and gyroscope values
        self.acceleration = [0, 0, 0]
        while True:
            if self.robot.is_picked_up:
                orientation = np.floor_divide([self.robot.gyro.x, self.robot.gyro.y, self.robot.gyro.z], 1)
                if np.linalg.norm(orientation) > 10:
                    self.dizzy +=  1
                a = self.acceleration
                self.acceleration = np.floor_divide([self.robot.accelerometer.x, self.robot.accelerometer.y, self.robot.accelerometer.z], 1000)
                da = np.subtract(self.acceleration, a)
                self.da_norm = np.trunc(np.linalg.norm(da))
                if self.da_norm > 10:
                    self.pitch = 1
                else:
                    self.pitch = (self.da_norm/10)
            await asyncio.sleep(0.1);


    async def fly(self):     
        #Cozmo behavior when he's in the air - he speaks in a pitch dependent on how fast or how much he is moving, and his dizzy meter value adds up
        while True:
            if self.robot.is_picked_up is True:
                x = random.randint(1, 4)
                self.counter = 0
                if x == 1:
                    await self.robot.say_text("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", duration_scalar=0.1, voice_pitch=self.pitch).wait_for_completed()
                elif x == 2:
                    await self.robot.say_text("Faster", duration_scalar=1.5, voice_pitch=self.pitch).wait_for_completed()
                elif x == 3:
                    await self.robot.say_text("I, can fly", duration_scalar=1.5, voice_pitch=self.pitch).wait_for_completed()
                elif x == 4:
                    await self.robot.say_text("I'm, super man", duration_scalar=1.5, voice_pitch=self.pitch).wait_for_completed()
            else:
                self.counter += 1
                if self.counter > 0:
                    await self.end_program()
            await asyncio.sleep(0.1)    

    async def end_program(self):
        #once he is put down, calculate dizzy meter value and make him act dizzy
        self.robot.abort_all_actions()
        dizzy_meter = np.floor_divide(self.dizzy, 1)
        
        if dizzy_meter > 4:
            dizzy_meter = 4
        dizzy_meter += 1
        print(dizzy_meter)
        await self.robot.set_head_angle(cozmo.util.Angle(degrees=30)).wait_for_completed()
        self.robot.say_text("I'm so dizzy", duration_scalar=2*dizzy_meter, voice_pitch=-1, in_parallel=True)
        await self.robot.drive_wheels(l_wheel_speed=100, r_wheel_speed=10, l_wheel_acc=0, r_wheel_acc=0, duration=1.5*dizzy_meter)
        await self.robot.drive_wheels(l_wheel_speed=10, r_wheel_speed=70, l_wheel_acc=0, r_wheel_acc=0, duration=1.5*dizzy_meter)
        await self.robot.drive_wheels(l_wheel_speed=100, r_wheel_speed=10, l_wheel_acc=0, r_wheel_acc=0, duration=1.5*dizzy_meter)

        count = 0
        while True:
            #gifs displaying dizziness
            if(not os.path.exists("Media/" + str(int(dizzy_meter)) + "/" + str(count) + ".jpg")):
                count = 0
            img = Image.open("Media/" + str(int(dizzy_meter)) + "/" + str(count) + ".jpg")
            resized_img = img.resize(cozmo.oled_face.dimensions(), Image.BICUBIC)
            screen_data = cozmo.oled_face.convert_image_to_screen_data(resized_img) 
            await self.robot.display_oled_face_image(screen_data, duration_ms=10).wait_for_completed()
            count += 1               
            await asyncio.sleep(0)

    def start_capture_values(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.capture_values())

    async def run(self, conn):
        #start up code and call capture_values. Also start another thread for his in-air screams
        asyncio.set_event_loop(conn._loop)
        self.robot = await conn.wait_for_robot()
        await self.robot.set_lift_height(0).wait_for_completed()
        await self.robot.set_head_angle(cozmo.util.Angle(degrees=0)).wait_for_completed()
        await self.robot.play_anim_trigger(cozmo.anim.Triggers.MeetCozmoLookFaceGetOut).wait_for_completed()
        await self.robot.say_text("Ready for lift off", use_cozmo_voice=True, voice_pitch=-1, duration_scalar=1).wait_for_completed()
        img = Image.open("Media/belt.jpg")
        resized_img = img.resize(cozmo.oled_face.dimensions(), Image.BICUBIC)
        screen_data_1 = cozmo.oled_face.convert_image_to_screen_data(resized_img)
        screen_data_2 = cozmo.oled_face.convert_image_to_screen_data(resized_img, invert_image=True)
        while self.robot.is_picked_up is False:
            await self.robot.display_oled_face_image(screen_data_1, duration_ms=200).wait_for_completed()
            await self.robot.display_oled_face_image(screen_data_2, duration_ms=200).wait_for_completed()
            await asyncio.sleep(0)
        await self.robot.play_anim_trigger(cozmo.anim.Triggers.DroneModeTurboDrivingStart).wait_for_completed()
        _thread.start_new_thread(self.start_capture_values, ())
        await self.fly()

if __name__ == '__main__':
    CozmoCoaster()
