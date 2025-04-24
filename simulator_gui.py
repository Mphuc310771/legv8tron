# simulator_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, font, messagebox
from datapath_visualizer import DatapathVisualizer
from legv8_simulator import LEGv8_Simplified_Simulator
from assembler import placeholder_assembler



class SimulatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("LEGv8 Simulator")
        master.geometry("1300x850")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('Treeview', font=('Consolas', 9), rowheight=25)
        self.style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
        
        # Colors
        self.bg_color = '#f5f5f5'
        self.panel_color = '#e8e8e8'
        self.highlight_color = '#4a9cff'
        
        # Initialize simulator and visualizer
        self.simulator = LEGv8_Simplified_Simulator()
        self.visualizer = None
        self.pc_map = {}
        self.current_highlight_tag = "highlight"
        self.is_paused = False
        self.animation_speed = 400  # Default animation speed
        
        self.setup_gui()
        self.update_display()
        self._update_button_states()

    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Assembly and registers
        left_panel = ttk.Frame(main_frame, width=450, style='TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)
        
        # Assembly code section
        asm_frame = ttk.LabelFrame(
            left_panel, text="Assembly Code", 
            padding=10, style='TFrame'
        )
        asm_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.asm_text = scrolledtext.ScrolledText(
            asm_frame, wrap=tk.WORD, height=25,
            font=('Consolas', 11), relief=tk.SOLID, borderwidth=1,
            padx=10, pady=10
        )
        self.asm_text.pack(fill=tk.BOTH, expand=True)
        
        # Add sample code
        sample_code = """// LEGv8 Assembly Code
START:
    ADDI X1, XZR, #15     // X1 = 15
    ADDI X2, XZR, #10     // X2 = 10
    ADD X3, X1, X2        // X3 = X1 + X2
    SUB X4, X1, X2        // X4 = X1 - X2
    STUR X3, [SP, #8]     // Store X3 to memory
    LDUR X5, [SP, #8]     // Load from memory to X5
    CMP X5, X3            // Compare X5 and X3
    CBZ X5, END           // Branch if zero
    B START               // Unconditional branch
END:
    HALT                  // Stop execution
"""
        self.asm_text.insert(tk.END, sample_code)
        self.asm_text.tag_configure(
            self.current_highlight_tag, 
            background='yellow', 
            foreground='black'
        )
        
        # Control buttons frame
        control_frame = ttk.Frame(left_panel, style='TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        self.assemble_btn = ttk.Button(
            control_frame, text="Assemble & Load", 
            command=self.assemble_and_load, width=15
        )
        self.assemble_btn.pack(side=tk.LEFT, padx=(0,5), expand=True, fill=tk.X)
        
        self.step_btn = ttk.Button(
            control_frame, text="Step", 
            command=self.do_step, state=tk.DISABLED, width=8
        )
        self.step_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.reset_btn = ttk.Button(
            control_frame, text="Reset", 
            command=self.do_reset, state=tk.DISABLED, width=8
        )
        self.reset_btn.pack(side=tk.LEFT, padx=(5,0), expand=True, fill=tk.X)
        
        # Execution control section
        exec_frame = ttk.LabelFrame(
            left_panel, text="Execution Control", 
            padding=10, style='TFrame'
        )
        exec_frame.pack(fill=tk.BOTH, pady=(0, 10))
        
        # Current instruction
        ttk.Label(exec_frame, text="Current Instruction:").pack(anchor=tk.W)
        self.curr_instr_label = ttk.Label(
            exec_frame, text="0 (NOP)", 
            font=('Consolas', 11), background='white', 
            relief=tk.SOLID, padding=5, width=40
        )
        self.curr_instr_label.pack(fill=tk.X, pady=(0, 10))
        
        # Micro-step control
        ttk.Label(exec_frame, text="Micro-Step:").pack(anchor=tk.W)
        self.micro_step_label = ttk.Label(
            exec_frame, text="Fetch (1/5)", 
            font=('Consolas', 10)
        )
        self.micro_step_label.pack(anchor=tk.W)
        
        # Pause/Resume button
        self.pause_btn = ttk.Button(
            exec_frame, text="Pause", 
            command=self.toggle_pause, state=tk.DISABLED
        )
        self.pause_btn.pack(pady=(10, 0))
        
        # Animation speed control
        speed_frame = ttk.Frame(exec_frame)
        speed_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_scale = ttk.Scale(
            speed_frame, from_=100, to=1000, 
            command=self.update_animation_speed
        )
        self.speed_scale.set(400)
        self.speed_scale.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Register display section
        reg_frame = ttk.LabelFrame(
            left_panel, text="Register File", 
            padding=10, style='TFrame'
        )
        reg_frame.pack(fill=tk.BOTH, expand=True)
        
        # Register table
        self.reg_table = ttk.Treeview(
            reg_frame, columns=('hex', 'decimal'), 
            show='headings', height=12
        )
        self.reg_table.heading('#0', text='REGISTER')
        self.reg_table.heading('hex', text='HEX')
        self.reg_table.heading('decimal', text='DECIMAL')
        
        # Configure column widths
        self.reg_table.column('#0', width=80, anchor=tk.W)
        self.reg_table.column('hex', width=150, anchor=tk.W)
        self.reg_table.column('decimal', width=120, anchor=tk.W)
        
        vsb = ttk.Scrollbar(reg_frame, orient="vertical", command=self.reg_table.yview)
        hsb = ttk.Scrollbar(reg_frame, orient="horizontal", command=self.reg_table.xview)
        self.reg_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.reg_table.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        reg_frame.grid_rowconfigure(0, weight=1)
        reg_frame.grid_columnconfigure(0, weight=1)
        
        # Right panel - Datapath and tabs
        right_panel = ttk.Frame(main_frame, style='TFrame')
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Notebook for tabs
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Datapath tab
        datapath_tab = ttk.Frame(notebook)
        notebook.add(datapath_tab, text="CPU Datapath")
        
        # Create canvas for datapath visualization
        self.canvas = tk.Canvas(
            datapath_tab, bg="white", 
            width=800, height=700, 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize visualizer after canvas is created
        self.visualizer = DatapathVisualizer(self.canvas)
        self.master.after(100, self.visualizer.draw_static_datapath)
        
        # Memory tab
        memory_tab = ttk.Frame(notebook)
        notebook.add(memory_tab, text="Memory")
        
        self.mem_text = scrolledtext.ScrolledText(
            memory_tab, wrap=tk.WORD, 
            font=('Consolas', 10), state=tk.DISABLED
        )
        self.mem_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CPU State tab
        cpu_tab = ttk.Frame(notebook)
        notebook.add(cpu_tab, text="CPU State")
        
        # Control Signals tab
        ctrl_tab = ttk.Frame(notebook)
        notebook.add(ctrl_tab, text="Control Signals")
        
        # Initialize register table
        self.update_register_table()

    def toggle_pause(self):
        """Toggle pause state of the simulation"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text="Resume")
            # Pause all animations
            if self.visualizer:
                self.visualizer.pause_animations()
        else:
            self.pause_btn.config(text="Pause")
            # Resume animations
            if self.visualizer:
                self.visualizer.resume_animations()

    def update_animation_speed(self, value):
        """Update animation speed based on slider value"""
        self.animation_speed = int(float(value))
        if self.visualizer:
            self.visualizer.set_animation_speed(self.animation_speed)

    def assemble_and_load(self):
        """Assemble and load the program into simulator"""
        assembly_code = self.asm_text.get("1.0", tk.END)

        if not assembly_code.strip():
            messagebox.showwarning("Warning", "Assembly code is empty.")
            return

        try:
            instruction_mem, pc_map, label_map = placeholder_assembler(assembly_code)

            if not instruction_mem:
                messagebox.showinfo("Info", "No executable instructions.")
                self.simulator.load_program({}, {})
                self.pc_map = {}
                self.visualizer.draw_static_datapath()
                self.do_reset(reload_assembly=False)
                return

            self.simulator.load_program(instruction_mem, label_map)
            self.pc_map = pc_map
            self.visualizer.draw_static_datapath()
            self.do_reset(reload_assembly=False)

            # Enable pause button
            self.pause_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"{len(instruction_mem)} instructions loaded.")

        except Exception as e:
            messagebox.showerror("Error", f"Assembly error:\n{e}")
            self.simulator.load_program({}, {})
            self.pc_map = {}
            if self.visualizer:
                self.visualizer.reset_datapath_visualization()
            self.update_display()
            self._update_button_states()

    def do_step(self):
        """Execute one step of simulation"""
        if self.simulator.halted:
            messagebox.showinfo("Info", "Simulator is halted.")
            return

        try:
            # If paused, just update display without stepping
            if self.is_paused:
                self.update_display()
                return
                
            state = self.simulator.step()
            
            if not state:
                messagebox.showerror("Error", "No state returned.")
                self.simulator.halted = True
                self._update_button_states()
                return

            self.highlight_assembly_line(state.get('pc'))
            
            # Update datapath visualization with animation
            if self.visualizer:
                self.visualizer.update_datapath_visualization(state)
            
            self.update_display()

            if self.simulator.halted:
                messagebox.showinfo("Halted", "Execution completed.")

            self._update_button_states()

        except Exception as e:
            messagebox.showerror("Error", f"Runtime error:\n{e}")
            self.simulator.halted = True
            if self.visualizer:
                self.visualizer.reset_datapath_visualization()
            self.update_display()
            self._update_button_states()

    def do_reset(self, reload_assembly=True):
        """Reset the simulator state"""
        self.simulator.reset()
        self.is_paused = False
        self.pause_btn.config(text="Pause")
        
        self.highlight_assembly_line(None)
        if self.visualizer:
            self.visualizer.reset_datapath_visualization()
        
        self.update_display()
        self._update_button_states()

    def highlight_assembly_line(self, pc_to_highlight):
        """Highlight the current assembly line"""
        self.asm_text.tag_remove(self.current_highlight_tag, "1.0", tk.END)

        if pc_to_highlight is not None and pc_to_highlight in self.pc_map:
            try:
                line_num = self.pc_map[pc_to_highlight]
                line_start = f"{line_num}.0"
                line_end = f"{line_num}.end"
                self.asm_text.tag_add(self.current_highlight_tag, line_start, line_end)
                self.asm_text.see(line_start)
            except Exception:
                pass

    def update_register_table(self):
        """Update the register table display"""
        self.reg_table.delete(*self.reg_table.get_children())
        
        for i, val in enumerate(self.simulator.registers):
            reg_name = f"X{i}"
            hex_val = f"0x{val:016x}"
            dec_val = str(val)
            
            self.reg_table.insert('', 'end', text=reg_name, 
                                values=(hex_val, dec_val))
            
    def update_memory_display(self):
        """Update the memory display"""
        self.mem_text.config(state=tk.NORMAL)
        self.mem_text.delete(1.0, tk.END)
        
        content = "Memory Contents:\n" + "="*40 + "\n"
        for addr, val in sorted(self.simulator.data_memory.items()):
            content += f"{addr:#010x}: {val}\n"
            
        self.mem_text.insert(1.0, content)
        self.mem_text.config(state=tk.DISABLED)

    def update_display(self):
        """Update all displays"""
        state_summary = self.simulator.get_state_summary()
        pc_val = state_summary.get('pc', 0)
        
        # Update current instruction
        if pc_val in self.simulator.instruction_memory:
            instr_data = self.simulator.instruction_memory[pc_val]
            self.curr_instr_label.config(text=f"{pc_val:#x} ({instr_data[1].strip()})")
        
        # Update registers and memory
        self.update_register_table()
        self.update_memory_display()

    def _update_button_states(self):
        """Update button states based on simulator state"""
        can_step = bool(self.simulator.instruction_memory) and not self.simulator.halted
        self.step_btn.config(state=tk.NORMAL if can_step else tk.DISABLED)

        can_reset = bool(self.simulator.instruction_memory)
        self.reset_btn.config(state=tk.NORMAL if can_reset else tk.DISABLED)
    


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorGUI(root)
    root.mainloop()