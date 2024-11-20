import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Libraries.MQTT_config import MQTT_config

from Libraries.SQL import SQL

class App:
    def __init__(self, master):
        self.master = master
        self.master.title("PI Controller Configuration and Temperature Display")
        
        # Create the main frame using grid layout
        self.main_frame = tk.Frame(master)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10)
        
        # Configure main window for resizing
        master.grid_rowconfigure(1, weight=1)  # Allow bottom frame to expand vertically
        master.grid_columnconfigure(0, weight=1)  # Allow bottom frame to expand horizontally

        # --- SQL Connection Frame (Column 0) ---
        self.sql_frame = tk.Frame(self.main_frame)
        self.sql_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Username Label and Entry (same row)
        tk.Label(self.sql_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.username_entry = tk.Entry(self.sql_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Password Label and Entry (same row)
        tk.Label(self.sql_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.password_entry = tk.Entry(self.sql_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Connect Button
        self.connect_button = tk.Button(self.sql_frame, text="Connect", command=self.test_connection)
        self.connect_button.grid(row=2, column=0, padx=5, pady=10, sticky="w")

        # Disconnect Button
        self.disconnect_button = tk.Button(self.sql_frame, text="Disconnect", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_button.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        # Status Label
        self.status_label = tk.Label(self.sql_frame, text="", fg="green")
        self.status_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # --- PI Controller Configuration Frame (Column 1) ---
        self.pi_frame = tk.Frame(self.main_frame)
        self.pi_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # PI Controller Configurations
        tk.Label(self.pi_frame, text="Reference:").grid(row=0, column=0, padx=5, sticky="w")
        self.reference_entry = tk.Entry(self.pi_frame)
        self.reference_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(self.pi_frame, text="Kp:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.kp_entry = tk.Entry(self.pi_frame)
        self.kp_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(self.pi_frame, text="Ti:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.ti_entry = tk.Entry(self.pi_frame)
        self.ti_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Confirm Button
        self.confirm_button = tk.Button(self.pi_frame, text="Confirm", command=self.confirm_pi_values)
        self.confirm_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # --- Chart Display Frame (Column 2) ---
        self.chart_frame = tk.Frame(self.main_frame)
        self.chart_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Clear Plot Button
        self.clear_plot_button = tk.Button(self.chart_frame, text="Clear Plot", command=self.clear_chart, state=tk.DISABLED)
        self.clear_plot_button.grid(row=0, column=0, padx=5, pady=5)

        # Waiting Message Label
        self.message_wait_label = tk.Label(self.chart_frame, text="Waiting for data from MQTT broker.", fg="black")
        self.message_wait_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # --- Bottom Frame for Plot Display ---
        self.bottom_frame = tk.Frame(master)
        self.bottom_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        # Configure bottom frame for expanding plot
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # Matplotlib Figure and Canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.bottom_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")  # Expand to fill entire bottom frame

        # Configure main frame grid weights for resizing
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Configure bottom frame for expanding plot
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize data storage for the chart
        self.temperature = [] # °C
        self.output = [] # V
        self.timestamps = [] 
        self.target = [] # °C
        
        # MQTT configuration
        self.mqtt_client = MQTT_config(type='laptop', on_message_callback=self.update_chart)
        
    def test_connection(self):
        # Retrieve user inputs
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        sql_client = SQL()
        
        # Check the login details in the database
        if sql_client.login(username, password):
            self.status_label.config(text="Connected", fg="green")
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.mqtt_client.sql_connection = True
        else:
            self.status_label.config(text="Invalid credentials", fg="red")
            self.mqtt_client.sql_connection = False
    
    def disconnect(self):
        # Reset the connection state
        self.status_label.config(text="Disconnected from the SQL database", fg="blue")
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.mqtt_client.sql_connection = False
        
    def update_chart(self, temperature, output, timestamps, target):
        # When this method is called, it is that some data are received !
        self.message_wait_label.config(text="")
        self.clear_plot_button.config(state=tk.NORMAL)
        myFontSize = 7
        
        self.temperature.append(temperature)
        self.output.append(output)
        self.timestamps.append(timestamps)
        self.target.append(target)

        # Limit the display to the last N points
        N = 100
        if len(self.timestamps) > N:
            self.timestamps = self.timestamps[-N:]
            self.temperature = self.temperature[-N:]
            self.output = self.output[-N:]
            self.target = self.target[-N:]
            
        # Verify that the list aren't empty before plotting them.
        if len(self.timestamps) == 0 or len(self.temperature) == 0 or len(self.output) == 0 or len(self.target) == 0:
            print("Aucune donnée disponible pour mettre à jour le graphique.")
            print(self.target)
            return

        # Clear and redraw the plot
        self.ax.clear()
        self.ax.plot(self.timestamps, self.temperature, label="Temperature (°C)")
        self.ax.plot(self.timestamps, self.output, label="Output (V)")
        self.ax.plot(self.timestamps, self.target, linestyle='--', label="Targetted Temperature (°C)")

        # Set labels and titles
        self.ax.set_xlabel("Time (s)", fontsize=myFontSize)
        self.ax.set_ylabel("Value", fontsize=myFontSize)
        self.ax.set_title("Temperature and Output Response", fontsize=myFontSize)
        
        if len(self.timestamps) > 0:
            self.ax.set_xlim(self.timestamps[0], self.timestamps[-1])
        self.ax.set_ylim(0, 50)  # Adjust Y-axis scale

        # Set tick parameters for smaller font sizes on axes numbers
        self.ax.tick_params(axis='both', labelsize=myFontSize)  # Adjust the labelsize for both axes

         # Add legend
        self.ax.legend(fontsize=myFontSize)

        self.figure.tight_layout()  # Automatically adjust layout to fit labels

        # Update the canvas
        self.canvas.draw()
        
    def clear_chart(self):
        self.ax.clear()
        
        self.timestamps.clear()
        self.temperature.clear()
        self.output.clear()
        self.target.clear()
        
    def confirm_pi_values(self):
        try:
            reference = float(self.reference_entry.get())
            Kp = float(self.kp_entry.get())
            Ti = float(self.ti_entry.get())
            
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter valid float values for reference, Kp and Ti.")
            
        self.mqtt_client.send_PI_configuration(reference, Kp, Ti)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()