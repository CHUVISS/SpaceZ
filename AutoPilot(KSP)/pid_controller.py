class PID:
    def __init__(self,Kp,Ti,Td,i_max,i_min):
        self.i_error = 0.0
        command      = 0.0
        self.running = False
        self.set_gains(Kp,Ti,Td,i_max,i_min)

    def set_gains(self,Kp,Ti,Td,i_max,i_min):
        self.Kp    = Kp
        self.Ti    = Ti
        self.Td    = Td
        self.i_max = i_max
        self.i_min = i_min
        
    def reset(self):
        self.i_error    = 0.0
        self.error_last = 0.0
        self.running    = False

    def calculate_command(self,error,dt):
        if self.Ti > 0.0:
            self.i_error = self.i_error + error*dt
            self.i_error = min(max(self.i_error,self.i_min*self.Ti/self.Kp),self.i_max*self.Ti/self.Kp)

            error += self.i_error/self.Ti

        if self.Td > 0.0:
            if self.running == True:
                d_error = (error - self.error_last)*dt
            else:
                d_error = 0.0
                running = True
            self.error_last = error

            error += d_error/self.Td

        self.command = self.Kp*error
        return self.command
