import numpy as np
import cozmo
import asyncio
from Common.woc import WOC
from PIL import Image
from cozmo.util import distance_mm, speed_mmps
import _thread
import os

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
        self.d_accel_mag = 0
        self.dizzy = 0      #0 = normal, 1 = tipsy, 2 = drunk, 3 = throwing up, 4 = out of order
        self.robot = None
        self.pitch = 0
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
            await self.robot.display_oled_face_image(screen_data_1, duration_ms=500).wait_for_completed()
            await self.robot.display_oled_face_image(screen_data_2, duration_ms=500).wait_for_completed()
            await asyncio.sleep(0)
        await self.robot.play_anim_trigger(cozmo.anim.Triggers.DroneModeTurboDrivingStart).wait_for_completed()

    async def capture_values(self):
        while True:
            if self.robot.is_picked_up:

                self.orientation = np.floor_divide([self.robot.gyro.x, self.robot.gyro.y, self.robot.gyro.z], 1)
                if np.linalg.norm(self.orientation) > 5:
                    self.dizzy += 0.1
                prev_accel = self.acceleration
                self.acceleration = np.floor_divide([self.robot.accelerometer.x, self.robot.accelerometer.y, self.robot.accelerometer.z], 1000)
                d_accel = np.subtract(prev_accel, self.acceleration)
                self.d_accel_mag = np.linalg.norm(d_accel)
                if self.d_accel_mag > 15:
                    self.pitch = 1
                else:
                    self.pitch = (self.d_accel_mag / 5) - 2
            await asyncio.sleep(0.1);


    async def fly(self):     
        while True:
            if self.robot.is_picked_up is True:
                self.counter = 0
                if self.d_accel_mag > 15:
                    await self.robot.say_text("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", duration_scalar=0.2, voice_pitch=self.pitch).wait_for_completed()
                elif self.d_accel_mag > 10:
                    await self.robot.say_text("woohoo", duration_scalar=3, voice_pitch=self.pitch).wait_for_completed()
                elif self.d_accel_mag > 5:
                    await self.robot.say_text("I can fly", duration_scalar=2, voice_pitch=self.pitch).wait_for_completed()
                else:
                    await self.robot.say_text("Faster", duration_scalar=1, voice_pitch=self.pitch).wait_for_completed()
            else:
                self.counter += 1
                if self.counter > 20:
                    await self.end_program()
            await asyncio.sleep(0.1)    

    async def end_program(self):
        self.robot.abort_all_actions()
        dizzy_meter = np.floor_divide(self.dizzy, 1000)
        if dizzy_meter > 4:
            dizzy_meter = 4
        dizzy_meter += 1
        x = 1
        for i in range(3):
            x = -x
            await self.robot.drive_straight(distance_mm(5*(10-dizzy_meter)), speed_mmps(50), False).wait_for_completed()
            await self.robot.turn_in_place(cozmo.util.Angle(degrees=(dizzy_meter)*10*x)).wait_for_completed()
            await asyncio.sleep(0)
        await self.robot.set_head_angle(cozmo.util.Angle(degrees=45)).wait_for_completed()
        await self.robot.say_text("I'm so dizzy", duration_scalar=2*(dizzy_meter), voice_pitch=-1, in_parallel=True).wait_for_completed()

        count = 0
        while True:
            if(not os.path.exists("Media/" + str(int(dizzy_meter)) + "/" + str(count) + ".jpg")):
                count = 0
            img = Image.open("Media/" + str(int(dizzy_meter)) + "/" + str(count) + ".jpg")
            resized_img = img.resize(cozmo.oled_face.dimensions(), Image.BICUBIC)
            screen_data = cozmo.oled_face.convert_image_to_screen_data(resized_img) 
            await self.robot.display_oled_face_image(screen_data, in_parallel=True, duration_ms=10).wait_for_completed()
            count += 1               
            await asyncio.sleep(0)

    def start_capture_values(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.capture_values())
        
    async def run(self, conn):
        asyncio.set_event_loop(conn._loop)
        self.robot = await conn.wait_for_robot()
        await self.start_program()
        _thread.start_new_thread(self.start_capture_values, ())
        await self.fly()

if __name__ == '__main__':
    CozmoCoaster()
