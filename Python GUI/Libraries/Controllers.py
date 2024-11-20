class controllers:
    def __init__(self, r, ts=0.1):
        self.r = r
        self.ui_prev = 0
        self.u_prev = 0
        self.ts = ts
        self.uf_prev = 0

    def PI_controller(self, input, Kc, Ti, ui_max=5, ui_min=-5, u_max=5, u_min=1):
        error = self.r - input
        up = Kc * error #P term
        ui = self.ui_prev + Kc/Ti * self.ts * error

        # Anti windup integral
        if(ui > ui_max):
            ui = ui_max
        elif(ui < ui_min):
            ui = ui_min
        
        self.ui_prev = ui
        u = up + ui

        if(u > u_max):
            u = u_max
        elif(u < u_min):
            u = u_min
        
        return u
    
    def on_off_controller(self, input, u_min=1, u_max=5, D=0.5):
        u = self.u_prev
        if (input > self.r + D/2):
            u = u_min
        elif (input < self.r - D/2):
            u = u_max

        self.u_prev = u
        return u
    
    def lowPass_filter(self, value):
        filter_time_constant = 5*self.ts
        a = self.ts / (filter_time_constant + self.ts)
        uf = (1-a)*self.uf_prev + a*value
        self.uf_prev = uf
        return uf



