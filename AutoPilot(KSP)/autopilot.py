import krpc
import time
import pid_controller
import os
import math

def clear_console():
    os.system('cls')

if __name__ == "__main__":
    connection = krpc.connect(name="autopilot")
    vessel     = connection.space_center.active_vessel
    vessel_name = vessel.name

    running = True
    #else:
    #    running = False

    surface_velocity_frame = vessel.surface_velocity_reference_frame
    surface_frame = vessel.surface_reference_frame
    orbit_frame = vessel.orbit.body.reference_frame

    velocity_surface = connection.add_stream(connection.space_center.transform_velocity,vessel.position(orbit_frame),vessel.velocity(orbit_frame),orbit_frame,surface_frame)
    altitude = connection.add_stream(getattr, vessel.flight(), 'mean_altitude')
    surface_altitude = connection.add_stream(getattr, vessel.flight(), 'surface_altitude')
    latitude = connection.add_stream(getattr,vessel.flight(),'latitude')
    longitude = connection.add_stream(getattr,vessel.flight(),'longitude')

    stage_1_resources = vessel.resources_in_decouple_stage(stage=1, cumulative=False)
    launcher_liquid_fuel = connection.add_stream(stage_1_resources.amount, 'LiquidFuel')

    altitude_pid       = pid_controller.PID(0.2,0.0,0.0,0.0,0.0)
    vertical_speed_pid = pid_controller.PID(0.2,2.0,0.0,1.0,0.0)
    speed_pid = pid_controller.PID(0.2,0.0,0.0,1.0,0.0)
    horizontal_speed_pid = pid_controller.PID(2.0,0.0,0.0,20.0,-20.0)
    pos_latitude_pid = pid_controller.PID(750,0,0.0,0,0)
    pos_longitude_pid = pid_controller.PID(750,0,0.0,0,0)
    altitude_target = 500
    vertical_speed_target = 0

    state = "INIT"
    loop_time = 0.1
    launch_site_altitude_ASL = altitude()
    launch_site_latitude = latitude()
    launch_site_longitude = longitude()
    kerbin = connection.space_center.bodies['Kerbin']
    launch_site_radius = 10/(2*math.pi*kerbin.equatorial_radius)*360.0
    landing_site_latlonalt = (latitude(),longitude(),altitude())
    
    dt = 0.0

    while running:
        # Найти время с последней итерации.
        # Не вычислять, если он находится в состоянии INIT.   
        time_now = connection.space_center.ut
        if state != "INIT":
            dt = time_now - time_last
        time_last = time_now

        altitude_above_launch_site = altitude() - launch_site_altitude_ASL
        velocity_ned   = (-velocity_surface()[1],-velocity_surface()[2],velocity_surface()[0])
        vertical_speed = -velocity_ned[2]
        speed_north    = velocity_ned[0]
        speed_east     = velocity_ned[1]

        # Направление к месту посадки, расстояние до него и высота над ним.
        landing_site_distance_north = (landing_site_latlonalt[0]-latitude())*(2*math.pi*kerbin.equatorial_radius)/360.0
        landing_site_distance_east  = (landing_site_latlonalt[1]-longitude())*(2*math.pi*kerbin.equatorial_radius)/360.0
        heading_to_landing_site = 180.0*math.atan2(landing_site_distance_east,landing_site_distance_north)/math.pi
        if heading_to_landing_site < 0.0: heading_to_landing_site += 360.0
        distance_to_landing_site = math.sqrt(landing_site_distance_north*landing_site_distance_north + landing_site_distance_east*landing_site_distance_east)
        altitude_above_landing_site = altitude() - landing_site_latlonalt[2]

        # Режимы полета
        if state == "INIT":
            altitude_control = False
            vertical_speed_control = False
            spoiler_active = False
            position_control = False
            horizontal_speed_control = False
            vessel.control.throttle = 0.0
            state = "LANDED"

        elif state == "LANDED":
            vertical_speed_control =  False
            altitude_control = False
            position_control = False
            vessel.control.rcs = False
            vessel.control.throttle = 0.0
            vessel.auto_pilot.disengage()
            if vessel.available_thrust > 0.0:
                state = "PRE_LAUNCH"
                launch_time = time_now + 2.0

        elif state == "PRE_LAUNCH":
            vessel.auto_pilot.target_pitch_and_heading(90,90)
            vessel.auto_pilot.engage()
            vessel.control.rcs = True
            vessel.control.throttle = 0.0
            if time_now > launch_time:
                state = "LAUNCH"

        elif state == "LAUNCH":
            vertical_speed_target = vessel.flight().terminal_velocity
            vertical_speed_control = True
            if altitude_above_launch_site < 2.0:
                vessel.auto_pilot.target_pitch_and_heading(90,90)
            elif altitude_above_launch_site < 50.0:
                vessel.control.gear = False
                vessel.auto_pilot.target_pitch_and_heading(90,90)
            elif altitude_above_launch_site < 100.0:
                vessel.auto_pilot.target_pitch_and_heading(85,90)
            else:
                state = "ACENDING"

        elif state == "ACENDING":
            pitch = min(max(180.0*math.atan(vertical_speed/speed_east)/math.pi + 5.0,45),85)
            vessel.auto_pilot.reference_frame = surface_frame
            vessel.auto_pilot.target_pitch_and_heading(pitch,90)
            vessel.control.throttle = 1.0
            if altitude() > 8000.0:
                wait_time = time_now + 5.0
                state = "LAUNCH_PAYLOAD"
                ap_error_OK = 0

        elif state == "LAUNCH_PAYLOAD":
            pitch = 180.0*math.atan(vertical_speed/speed_east)/math.pi
            vessel.auto_pilot.reference_frame = surface_frame
            vessel.auto_pilot.target_pitch_and_heading(pitch,90)
            vessel.control.throttle = 0.0
            vessel.control.toggle_action_group(5)
            if wait_time < time_now:
                state = "BOOST-BACK-FLIP"

        elif state == "BOOST-BACK-FLIP":
            vessel.auto_pilot.reference_frame = surface_frame
            vessel.auto_pilot.target_pitch_and_heading(0,heading_to_landing_site)
            vessel.control.throttle = 0.0
            ap_error = vessel.auto_pilot.error
            if ap_error < 30.0:
                ap_error_OK += 1
            else:
                ap_error_OK = 0
            if ap_error_OK > 20:
                state = "BOOST-BACK"


        elif state == "BOOST-BACK":
            # Вычисление скорости для возврата ступени
            t = (vertical_speed + math.sqrt(vertical_speed*vertical_speed + 2*kerbin.surface_gravity*altitude_above_landing_site))/kerbin.surface_gravity
            velocity_boostback = (1.3*distance_to_landing_site)/t + 10.0
            heading_boostback = heading_to_landing_site
            velocity_error_north = velocity_boostback*math.cos(math.pi*heading_boostback/180.0) - speed_north
            velocity_error_east = velocity_boostback*math.sin(math.pi*heading_boostback/180.0) - speed_east
            velocity_error_direction = 180.0*math.atan2(velocity_error_east, velocity_error_north)/math.pi
            if velocity_error_direction < 0: velocity_error_direction += 360
            velocity_error_magnitude = math.sqrt(velocity_error_north*velocity_error_north+velocity_error_east*velocity_error_east)

            if velocity_error_magnitude < 10.0:
                state = "DECENDING"
                vessel.control.throttle = 0.0
            else:
                # Возврат на пусковую площадку
                ap_error = vessel.auto_pilot.error
                vessel.auto_pilot.reference_frame = surface_frame
                vessel.auto_pilot.target_pitch_and_heading(0,velocity_error_direction)
                throttle_command = min(max(0.1*velocity_error_magnitude,0.0),1.0)
                vessel.control.throttle = min(max(throttle_command-ap_error/45.0, 0.0),1.0)

        
        elif state == "HOVER":
            altitude_target = 3000.0
            altitude_control = True
            position_control = True
            position_target = (launch_site_latitude,launch_site_longitude)
            if time_now > hover_time:
                state = "DECENDING"

        elif state == "DECENDING":
            vertical_speed_target = -0.1*(altitude_above_launch_site-20.0) - 1.0
            vertical_speed_control = True
            position_control = True
            position_target = (launch_site_latitude,launch_site_longitude)
            spoiler_active = True
            if altitude_above_landing_site < 20.0:
                state = "FINE_TUNE_LANDING"

        elif state == "FINE_TUNE_LANDING":
            vertical_speed_target = 0.0
            vertical_speed_control = True
            position_control = True
            position_target = (launch_site_latitude,launch_site_longitude)
            if at_position_target:
                state = "LANDING"

        elif state == "LANDING":
            vertical_speed_target = -1.0
            vertical_speed_control = True
            position_control = True
            position_target = (launch_site_latitude,launch_site_longitude)
            spoiler_active = True
            vessel.control.gear = True
            if vertical_speed > -0.1 and altitude_above_launch_site < 1:
                landing_time = time_now
                state = "POST_LANDING"

        elif state == "POST_LANDING":
            vessel.auto_pilot.target_pitch_and_heading(90,90)
            vessel.auto_pilot.engage()
            vessel.control.throttle = 0.0
            if landing_time + 10.0 < time_now:
                state = "LANDED"
                running = False

        elif state == "ABORT":
            spoiler_active = True
            if vertical_speed < -2.0:
                vessel.control.abort(True)
            if min(surface_altitude() ,altitude()) < 20.0:
                vertical_speed_target = -1.0
                vertical_speed_control = True
            if vertical_speed > -0.1 and min(surface_altitude() ,altitude()) < 10.0:
                landing_time = time_now
                state = "POST_LANDING"


        # PID вычисляет погрешность высоты для ее регулирования
        if altitude_control: 
            altitude_error = altitude_target - altitude()
            vertical_speed_target = altitude_pid.calculate_command(altitude_error,dt)
            vertical_speed_control = True
        else:
            altitude_pid.reset()

        # PID регулирует вертикальную скорость
        throttle_command = 0.0
        if vertical_speed_control: 
            vertical_speed_error = vertical_speed_target - vertical_speed
            throttle_command = min(max(vertical_speed_pid.calculate_command(vertical_speed_error,dt),0.0),1.0) 
            vessel.control.throttle = throttle_command
        else:
            vertical_speed_pid.reset()
        
        # Контроль позиции
        if position_control:
            latitude_error = position_target[0]-latitude()
            longitude_error = position_target[1]-longitude()
            horizontal_speed_target = (pos_latitude_pid.calculate_command(latitude_error,dt),pos_longitude_pid.calculate_command(longitude_error,dt))
            horizontal_speed_control = True    
            if math.sqrt(latitude_error*latitude_error+longitude_error*longitude_error) < launch_site_radius:
                at_position_target = True
            else:
                at_position_target = False
        else:
            pos_latitude_pid.reset()
            pos_longitude_pid.reset()
            at_position_target = False
            
        # Контроль горизонтальной скорости
        if horizontal_speed_control:
            horizontal_speed_north_target = horizontal_speed_target[0]
            horizontal_speed_east_target  = horizontal_speed_target[1] 
            speed_north_error = horizontal_speed_north_target - speed_north
            speed_east_error  = horizontal_speed_east_target - speed_east
            horizontal_speed_error_magnitude = math.sqrt(speed_north_error*speed_north_error+speed_east_error*speed_east_error)
            horizontal_speed_error_direction = 180.0*math.atan2(speed_east_error,speed_north_error)/math.pi
            pitch_effort = min(max(horizontal_speed_pid.calculate_command(horizontal_speed_error_magnitude,dt),-45),45)
            if throttle_command < 0.05 and vertical_speed < 0:
                pitch = 90 + pitch_effort
            else:
                pitch = 90 - pitch_effort 
            heading = horizontal_speed_error_direction
            while heading < 0.0:
                heading += 360.0
            while heading > 360.0:
                heading -= 360.0
            vessel.auto_pilot.reference_frame = surface_frame
            vessel.auto_pilot.target_pitch_and_heading(pitch,heading)
            vessel.auto_pilot.engage()
        else:
            horizontal_speed_pid.reset()


        # Активация шасси
        if spoiler_active and vertical_speed < -0.1 and throttle_command > 0.05: 
            vessel.control.toggle_action_group(1)
        else:
            vessel.control.toggle_action_group(2)

        # Состояния
        if state != "INIT":
            clear_console()
            print("State:                 " + state)
            print("Altitude ASL:          " + str(altitude()))
            print("Altitude SURF:         " + str(surface_altitude()))
            print("Altitude ALS:          " + str(altitude_above_launch_site))
            print("Altitude ASL target:   " + str(altitude_target)) 
            print("speed:                 " + str(vessel.flight(orbit_frame).speed))
            print("Vertical speed:        " + str(vertical_speed))
            print("Vertical speed target: " + str(vertical_speed_target))
            print("Launcher fuel:         " + str(launcher_liquid_fuel()))
            print("Throttle effort:       " + str(throttle_command*100))
            print("Delta time:            " + str(dt))
            print("Velocity:              " + str(velocity_ned))
            if horizontal_speed_control:
                print("Horizontal speed err:  " + str(horizontal_speed_error_magnitude) + "m/s " + str(horizontal_speed_error_direction) + "deg")
            print("Landing site: heading=" + str(heading_to_landing_site) + ", dist=" + str(distance_to_landing_site) + ", alt=" +str(altitude_above_landing_site))

        horizontal_speed_control = False
        vertical_speed_control = False
        altitude_control = False
        position_control = False
        spoiler_activate = False

        # Спящий режим на оставшееся время цикла
        sleep_time = loop_time - (connection.space_center.ut - time_now)
        if sleep_time > 0.0:
            time.sleep(sleep_time)

