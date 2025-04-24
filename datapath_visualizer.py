# datapath_visualizer.py
import tkinter as tk
import math
import time # Dùng để tính toán thời gian animation (có thể không cần nếu dùng after chuẩn)

# --- Constants ---
COLOR_INACTIVE = "grey"
COLOR_ACTIVE = "blue"
COLOR_CONTROL_ACTIVE = "red"
COLOR_MEM_ACCESS = "orange"
COLOR_REG_WRITE = "darkgreen"
COLOR_COMPONENT_BG = "lightblue"
COLOR_IMEM_DMEM_BG = "lightgoldenrodyellow"
COLOR_MUX_BG = "lightyellow"
COLOR_ALU_BG = "lightpink"
COLOR_CTRL_BG = "palegreen"
COLOR_ANIM_DOT = "red" # Màu chấm animation

LINE_WIDTH_INACTIVE = 1.5
LINE_WIDTH_ACTIVE = 3
LINE_WIDTH_CONTROL = 1
LINE_WIDTH_CONTROL_ACTIVE = 2.5 # Width khi highlight tĩnh
ANIM_DOT_SIZE = 3 # Bán kính chấm animation
ANIM_DURATION_MS = 400 # Thời gian animation cho một tín hiệu (ms)
ANIM_STEP_MS = 25 # Tần suất cập nhật vị trí chấm (ms) -> ~40 FPS

class DatapathVisualizer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.elements = {} # Dictionary to store canvas item IDs and path coords
        self.animated_dots = [] # List to keep track of animation dot IDs
        self.animation_busy = False # Flag to prevent overlapping animations (optional)

    def _create_box(self, x, y, w, h, text, bg_color, element_key):
        """Creates a rectangle with text and stores its ID."""
        box_id = self.canvas.create_rectangle(x, y, x + w, y + h, fill=bg_color, outline="black", width=LINE_WIDTH_INACTIVE, tags=("component", element_key))
        text_id = self.canvas.create_text(x + w / 2, y + h / 2, text=text, tags=("component_text", element_key + "_text"), state=tk.DISABLED) # Disable text selection
        self.elements[element_key + '_box'] = box_id
        self.elements[element_key + '_text'] = text_id
        return box_id

    def _create_line(self, coords, color, width, element_key, tags=("path",)):
        """Creates a line, stores its ID and coordinates."""
        flat_coords = []
        path_points = []
        if coords and len(coords) >= 2:
            current_point = coords[0]
            flat_coords.extend(current_point)
            path_points.append(current_point)
            for next_point in coords[1:]:
                flat_coords.extend(next_point)
                path_points.append(next_point)

            line_id = self.canvas.create_line(*flat_coords, fill=color, width=width, tags=tags + (element_key,))
            self.elements[element_key] = line_id
            # Store detailed coordinates for animation
            self.elements[element_key + '_coords'] = path_points
            return line_id
        return None

    def draw_static_datapath(self):
        """
        Vẽ datapath tĩnh dựa trên layout của image_80fd53.png.
        """
        self.canvas.delete("all")
        self.elements = {}
        self.animated_dots = []
        w = int(self.canvas.cget("width"))
        h = int(self.canvas.cget("height"))

        # --- Component Dimensions (Adjust as needed) ---
        pc_w, pc_h = 50, 35
        adder_w, adder_h = 35, 35
        mem_w, mem_h = 90, 70
        mux_w, mux_h = 25, 50
        reg_w, reg_h = 90, 100
        alu_w, alu_h = 70, 90
        ctrl_w, ctrl_h = 50, 130
        signex_w, signex_h = 50, 35
        shift_w, shift_h = 50, 35
        aluctrl_w, aluctrl_h = 35, 35

        # --- Component Positions (Based on image_80fd53.png layout) ---
        pc_x, pc_y = 50, h * 0.25
        add4_x, add4_y = pc_x + pc_w + 20, pc_y - adder_h * 0.7

        imem_x, imem_y = pc_x - 10, pc_y + pc_h + 40 # Left of PC

        ctrl_x, ctrl_y = imem_x + mem_w + 30, imem_y + mem_h/2 - ctrl_h/2
        reg_x, reg_y = ctrl_x + ctrl_w + 40, h * 0.5 - reg_h / 2 # Center vertically

        mux_wreg_x, mux_wreg_y = ctrl_x + ctrl_w/2 - mux_w/2, reg_y - mux_h - 10 # Above RegFile, near Control

        mux_alusrc_x, mux_alusrc_y = reg_x + reg_w + 20, reg_y + reg_h * 0.6 # Right of RegFile
        signex_x, signex_y = mux_alusrc_x + mux_w + 20, reg_y + reg_h + 15 # Below MuxAluSrc
        aluctrl_x, aluctrl_y = signex_x + signex_w/2 - aluctrl_w/2, signex_y + signex_h + 10 # Below SignEx

        alu_x, alu_y = mux_alusrc_x + mux_w + 20, reg_y + reg_h/2 - alu_h/2 # Right of MuxAluSrc

        dmem_x, dmem_y = alu_x + alu_w + 70, reg_y + reg_h/2 - mem_h/2 # Right of ALU

        shift_x, shift_y = alu_x + alu_w/2 - shift_w/2, alu_y - shift_h - 50 # Above ALU
        addBr_x, addBr_y = shift_x + shift_w + 20, shift_y

        mux_mem2reg_x, mux_mem2reg_y = dmem_x + mem_w + 20, dmem_y + mem_h/2 - mux_h/2 # Right of DataMem
        mux_pcs_x, mux_pcs_y = add4_x + adder_w + 50, add4_y + adder_h/2 - mux_h/2 # Right of Add4


        # --- Create Components ---
        self._create_box(pc_x, pc_y, pc_w, pc_h, "PC", COLOR_COMPONENT_BG, "pc")
        self._create_box(add4_x, add4_y, adder_w, adder_h, "+4", COLOR_COMPONENT_BG, "add4")
        self._create_box(imem_x, imem_y, mem_w, mem_h, "Instruction\nMemory", COLOR_IMEM_DMEM_BG, "imem")
        self._create_box(ctrl_x, ctrl_y, ctrl_w, ctrl_h, "Control", COLOR_CTRL_BG, "control")
        self._create_box(reg_x, reg_y, reg_w, reg_h, "Registers", COLOR_COMPONENT_BG, "regfile")
        self._create_box(mux_wreg_x, mux_wreg_y, mux_w, mux_h, "Mux", COLOR_MUX_BG, "mux_wreg")
        self._create_box(signex_x, signex_y, signex_w, signex_h, "Sign\nExtend", COLOR_COMPONENT_BG, "signext")
        self._create_box(mux_alusrc_x, mux_alusrc_y, mux_w, mux_h, "Mux", COLOR_MUX_BG, "mux_alusrc")
        self._create_box(alu_x, alu_y, alu_w, alu_h, "ALU", COLOR_ALU_BG, "alu")
        self._create_box(aluctrl_x, aluctrl_y, aluctrl_w, aluctrl_h, "ALU\nCtrl", COLOR_CTRL_BG, "alucontrol")
        self._create_box(dmem_x, dmem_y, mem_w, mem_h, "Data\nMemory", COLOR_IMEM_DMEM_BG, "datamem")
        self._create_box(mux_mem2reg_x, mux_mem2reg_y, mux_w, mux_h, "Mux", COLOR_MUX_BG, "mux_mem2reg")
        self._create_box(mux_pcs_x, mux_pcs_y, mux_w, mux_h, "Mux", COLOR_MUX_BG, "mux_pcsource")
        self._create_box(shift_x, shift_y, shift_w, shift_h, "Shift\nLeft 2", COLOR_COMPONENT_BG, "shiftleft2")
        self._create_box(addBr_x, addBr_y, adder_w, adder_h, "Add", COLOR_COMPONENT_BG, "add_branch")

        # --- Create Data Paths (Adjust coordinates carefully) ---
        # PC -> Add4, IMEM
        pc_out_y = pc_y + pc_h / 2
        pc_mid_x = pc_x + pc_w / 2
        self._create_line([(pc_mid_x, pc_y), (pc_mid_x, add4_y + adder_h / 2), (add4_x, add4_y + adder_h / 2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_pc_to_add4")
        self._create_line([(pc_x, pc_out_y), (imem_x + mem_w / 2, pc_out_y), (imem_x + mem_w / 2, imem_y)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_pc_to_imem_addr")

        # IMEM -> Control, Registers, MuxWreg, SignEx, ALUCtrl
        imem_r_x = imem_x + mem_w
        imem_mid_y = imem_y + mem_h / 2
        self._create_line([(imem_r_x, imem_mid_y), (ctrl_x, imem_mid_y)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_imem_to_control")
        self._create_line([(imem_r_x, imem_y + 0.2*mem_h), (reg_x, imem_y + 0.2*mem_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_imem_to_reg_r1") # Read Addr 1
        self._create_line([(imem_r_x, imem_y + 0.35*mem_h), (reg_x, imem_y + 0.35*mem_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_imem_to_reg_r2") # Read Addr 2
        self._create_line([(imem_r_x, imem_y + 0.5*mem_h), (mux_wreg_x, imem_y + 0.5*mem_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_imem_to_mux_wreg1") # Mux Input 1
        self._create_line([(imem_r_x, imem_y + 0.65*mem_h), (mux_wreg_x, imem_y + 0.65*mem_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_imem_to_mux_wreg2") # Mux Input 2
        imem_bot_y = imem_y + mem_h
        self._create_line([(imem_x + 0.7*mem_w, imem_bot_y), (imem_x + 0.7*mem_w, signex_y + signex_h/2), (signex_x, signex_y + signex_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_imem_to_signext") # Imm to SignEx
        self._create_line([(imem_x + 0.3*mem_w, imem_bot_y), (imem_x + 0.3*mem_w, aluctrl_y + aluctrl_h/2), (aluctrl_x, aluctrl_y + aluctrl_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_imem_to_aluctrl") # Func/Opcode to ALUCtrl

        # Control -> MuxWreg Select
        self._create_line([(ctrl_x + ctrl_w/2, mux_wreg_y + mux_h + 5), (mux_wreg_x + mux_w/2, mux_wreg_y + mux_h + 5), (mux_wreg_x + mux_w/2, mux_wreg_y + mux_h)], COLOR_INACTIVE, LINE_WIDTH_CONTROL, "ctrl_reg2loc_muxwreg", tags=("control_path",)) # Example control line

        # MuxWreg -> Reg Write Address
        self._create_line([(mux_wreg_x + mux_w, mux_wreg_y + mux_h / 2), (reg_x, mux_wreg_y + mux_h / 2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_mux_wreg_to_regaddr")

        # Registers -> ALU, DataMem Write Data
        reg_r_x = reg_x + reg_w
        self._create_line([(reg_r_x, reg_y + 0.3*reg_h), (alu_x, reg_y + 0.3*reg_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_reg_r1_to_alu_a") # Read Data 1 -> ALU A
        self._create_line([(reg_r_x, reg_y + 0.6*reg_h), (mux_alusrc_x, reg_y + 0.6*reg_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_reg_r2_to_mux_alusrc") # Read Data 2 -> MuxAluSrc 0
        # Need path from Read Data 2 to Data Memory Write Data
        self._create_line([(reg_r_x, reg_y + 0.75*reg_h), (alu_x + alu_w/2, reg_y + 0.75*reg_h), (alu_x + alu_w/2, dmem_y + 0.75*mem_h), (dmem_x, dmem_y + 0.75*mem_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_reg_r2_to_dmem_wdata")

        # SignEx -> MuxAluSrc, ShiftLeft2
        self._create_line([(signex_x + signex_w, signex_y + signex_h/2), (mux_alusrc_x, signex_y + signex_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_signext_to_mux_alusrc") # SignEx -> MuxAluSrc 1
        self._create_line([(signex_x + signex_w/2, signex_y), (signex_x + signex_w/2, shift_y + shift_h/2), (shift_x, shift_y + shift_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_signext_to_shift") # SignEx -> ShiftLeft2

        # MuxAluSrc -> ALU B
        self._create_line([(mux_alusrc_x + mux_w, mux_alusrc_y + mux_h/2), (alu_x, mux_alusrc_y + mux_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_mux_alusrc_to_alu_b")

        # ALUCtrl -> ALU
        self._create_line([(aluctrl_x + aluctrl_w/2, aluctrl_y), (alu_x + alu_w*0.7, alu_y + alu_h)], COLOR_INACTIVE, LINE_WIDTH_CONTROL, "path_aluctrl_to_alu", tags=("control_path",))

        # ALU -> DataMem Addr, MuxMemToReg
        alu_r_x = alu_x + alu_w
        alu_mid_y = alu_y + alu_h / 2
        self._create_line([(alu_r_x, alu_mid_y), (dmem_x, alu_mid_y)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_alu_res_to_dmem_addr") # ALU Res -> Mem Addr
        self._create_line([(alu_r_x, alu_mid_y + 15), (mux_mem2reg_x, alu_mid_y + 15)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_alu_res_to_mux_mem2reg") # ALU Res -> MuxMem2Reg 0

        # DataMem -> MuxMemToReg
        self._create_line([(dmem_x + mem_w, dmem_y + mem_h/2), (mux_mem2reg_x, dmem_y + mem_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_dmem_rdata_to_mux_mem2reg") # Mem Data -> MuxMem2Reg 1

        # MuxMemToReg -> Reg Write Data
        mux_m2r_r_x = mux_mem2reg_x + mux_w
        mux_m2r_mid_y = mux_mem2reg_y + mux_h / 2
        reg_wdata_y = reg_y + reg_h * 0.8
        self._create_line([(mux_m2r_r_x, mux_m2r_mid_y), (mux_m2r_r_x + 30, mux_m2r_mid_y), (mux_m2r_r_x + 30, reg_wdata_y), (reg_x, reg_wdata_y)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_mux_mem2reg_to_reg_wdata")

        # Branch Path: Shift -> AddBr, Add4 -> AddBr, AddBr -> MuxPCSrc
        self._create_line([(shift_x + shift_w, shift_y + shift_h/2), (addBr_x, shift_y + shift_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_shift_to_addbr")
        self._create_line([(add4_x + adder_w, add4_y + adder_h/2), (add4_x + adder_w + 10, add4_y + adder_h/2), (add4_x + adder_w + 10, addBr_y + adder_h*0.7), (addBr_x, addBr_y + adder_h*0.7)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_add4_to_addbr")
        self._create_line([(addBr_x + adder_w, addBr_y + adder_h/2), (mux_pcs_x, addBr_y + adder_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_addbr_to_mux_pcsource") # Branch Target -> MuxPCSrc 1

        # Add4 -> MuxPCSrc
        self._create_line([(add4_x + adder_w, add4_y + adder_h/2), (mux_pcs_x, add4_y + adder_h/2)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_add4_to_mux_pcsource") # PC+4 -> MuxPCSrc 0

        # MuxPCSrc -> PC
        self._create_line([(mux_pcs_x + mux_w, mux_pcs_y + mux_h/2), (mux_pcs_x + mux_w + 20, mux_pcs_y + mux_h/2), (mux_pcs_x + mux_w + 20, pc_y + pc_h*0.8), (pc_x + pc_w/2, pc_y + pc_h*0.8), (pc_x + pc_w/2, pc_y + pc_h)], COLOR_INACTIVE, LINE_WIDTH_INACTIVE, "path_mux_pcsource_to_pc")


        # --- Create Control Signal Paths (Store coords for animation) ---
        ctrl_out_x = ctrl_x + ctrl_w
        ctrl_sigs_targets = {
            "RegWrite": (reg_x, reg_y), # Target: RegFile top-left
            "ALUSrc": (mux_alusrc_x + mux_w / 2, mux_alusrc_y + mux_h + 5), # Target: Below MuxAluSrc
            "MemRead": (dmem_x + mem_w * 0.3, dmem_y - 10), # Target: Top of DataMem
            "MemWrite": (dmem_x + mem_w * 0.7, dmem_y - 10), # Target: Top of DataMem
            "MemToReg": (mux_mem2reg_x + mux_w / 2, mux_mem2reg_y + mux_h + 5), # Target: Below MuxMemToReg
            "ALUOp": (aluctrl_x + aluctrl_w / 2, aluctrl_y - 10), # Target: Above ALUCtrl
            "Branch": (mux_pcs_x + mux_w / 2, mux_pcs_y - 10), # Target: Above MuxPCSrc
            # Add Reg2Loc/WriteRegMuxSel target if needed -> mux_wreg_x...
        }

        # Draw control lines and store coordinates
        for i, (name, target_coords) in enumerate(ctrl_sigs_targets.items()):
            ctrl_start_y = ctrl_y + (i + 0.5) * (ctrl_h / (len(ctrl_sigs_targets)))
            start_point = (ctrl_out_x, ctrl_start_y)
            # Simple L-shape routing for now
            bend1_x = max(start_point[0], target_coords[0]) + 20 # Bend point to the right
            bend1_y = start_point[1]
            bend2_x = bend1_x
            bend2_y = target_coords[1]
            path_coords = [start_point, (bend1_x, bend1_y), (bend2_x, bend2_y), target_coords]
            self._create_line(path_coords, COLOR_INACTIVE, LINE_WIDTH_CONTROL, f"ctrl_{name.lower()}", tags=("control_path",))

        print("Static datapath drawn (Layout based on image_80fd53.png).")
        return self.elements # Return elements dictionary

    def reset_datapath_visualization(self):
        """Đặt lại màu sắc/độ dày và xóa các chấm animation."""
        if not self.elements: return
        for item_id in self.canvas.find_withtag("path"):
            self.canvas.itemconfig(item_id, fill=COLOR_INACTIVE, width=LINE_WIDTH_INACTIVE)
        for item_id in self.canvas.find_withtag("control_path"):
            self.canvas.itemconfig(item_id, fill=COLOR_INACTIVE, width=LINE_WIDTH_CONTROL)
        for item_id in self.canvas.find_withtag("component"):
            self.canvas.itemconfig(item_id, outline="black", width=LINE_WIDTH_INACTIVE)

        # Delete any existing animation dots
        for dot_id in self.animated_dots:
            self.canvas.delete(dot_id)
        self.animated_dots = []
        self.animation_busy = False
        # print("Datapath visualization reset.")


    def _animate_dot(self, dot_id, path_coords, segment_lengths, total_length, start_time):
        """Recursive function to move the dot along the path."""
        elapsed_time = (time.perf_counter() - start_time) * 1000 # ms
        progress = min(elapsed_time / ANIM_DURATION_MS, 1.0) # Normalize progress 0.0 to 1.0

        # Calculate current distance along the total path
        current_dist = progress * total_length

        # Find which segment the dot is on and its position on that segment
        cumulative_dist = 0
        current_x, current_y = path_coords[0] # Default to start
        for i in range(len(segment_lengths)):
            segment_start = path_coords[i]
            segment_end = path_coords[i+1]
            seg_len = segment_lengths[i]

            if current_dist <= cumulative_dist + seg_len + 1e-6: # Check if on or before this segment
                segment_progress = (current_dist - cumulative_dist) / seg_len if seg_len > 0 else 0
                segment_progress = max(0.0, min(1.0, segment_progress)) # Clamp progress

                current_x = segment_start[0] + (segment_end[0] - segment_start[0]) * segment_progress
                current_y = segment_start[1] + (segment_end[1] - segment_start[1]) * segment_progress
                break
            cumulative_dist += seg_len
        else:
             # If loop completes, dot is at the very end
             current_x, current_y = path_coords[-1]


        # Move the dot
        radius = ANIM_DOT_SIZE
        try:
            if self.canvas.winfo_exists() and dot_id in self.canvas.find_all():
                 self.canvas.coords(dot_id, current_x - radius, current_y - radius, current_x + radius, current_y + radius)
            else:
                 # print(f"Dot {dot_id} deleted or canvas destroyed, stopping animation.")
                 return # Stop if dot or canvas is gone
        except tk.TclError:
             # print(f"Error moving dot {dot_id}, stopping animation.")
             return # Stop if error occurs


        # Schedule next step or finish
        if progress < 1.0:
            self.canvas.after(ANIM_STEP_MS, self._animate_dot, dot_id, path_coords, segment_lengths, total_length, start_time)
        else:
            # Animation finished, remove dot from tracking but keep it visible for a moment?
            # Or just delete it now. Let's delete it for simplicity.
            if dot_id in self.animated_dots:
                self.animated_dots.remove(dot_id)
            # Slight delay before deleting? Optional.
            # self.canvas.after(100, lambda: self.canvas.delete(dot_id) if dot_id in self.canvas.find_all() else None)
            self.canvas.delete(dot_id) # Delete immediately
            # print(f"Animation finished for dot {dot_id}")
            # Check if all animations are done
            # if not self.animated_dots:
            #     self.animation_busy = False


    def start_signal_animation(self, signal_name):
        """Initiates the animation for a specific control signal."""
        path_key = f"ctrl_{signal_name.lower()}_coords"
        if path_key in self.elements:
            path_coords = self.elements[path_key]
            if len(path_coords) < 2: return # Need at least start and end point

            # Calculate segment lengths and total length
            segment_lengths = []
            total_length = 0
            for i in range(len(path_coords) - 1):
                x1, y1 = path_coords[i]
                x2, y2 = path_coords[i+1]
                length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                segment_lengths.append(length)
                total_length += length

            if total_length <= 0: return # Cannot animate zero length path

            # Create the animation dot
            start_x, start_y = path_coords[0]
            radius = ANIM_DOT_SIZE
            dot_id = self.canvas.create_oval(start_x - radius, start_y - radius, start_x + radius, start_y + radius, fill=COLOR_ANIM_DOT, outline=COLOR_ANIM_DOT, tags="anim_dot")
            self.animated_dots.append(dot_id)
            self.animation_busy = True

            # Start the recursive animation movement
            start_time = time.perf_counter()
            # print(f"Starting animation for {signal_name} (dot {dot_id})")
            self._animate_dot(dot_id, path_coords, segment_lengths, total_length, start_time)


    def update_datapath_visualization(self, state):
        """
        Cập nhật hình ảnh datapath VÀ bắt đầu animation cho tín hiệu control.
        """
        # Reset previous state BUT keep ongoing animations running
        # Reset colors/widths first
        if not self.elements: return
        for item_id in self.canvas.find_withtag("path"):
            self.canvas.itemconfig(item_id, fill=COLOR_INACTIVE, width=LINE_WIDTH_INACTIVE)
        for item_id in self.canvas.find_withtag("control_path"):
             # Don't reset color/width of control paths, let animation handle it?
             # Or reset width, keep color default, animation adds color?
             self.canvas.itemconfig(item_id, fill=COLOR_INACTIVE, width=LINE_WIDTH_CONTROL)
        for item_id in self.canvas.find_withtag("component"):
            self.canvas.itemconfig(item_id, outline="black", width=LINE_WIDTH_INACTIVE)

        # Check state
        if not state or state.get('halted'):
            # If halted, ensure any lingering animations are cleared
            for dot_id in self.animated_dots:
                self.canvas.delete(dot_id)
            self.animated_dots = []
            self.animation_busy = False
            return

        signals = state.get('control_signals', {})
        pc = state.get('pc')
        next_pc = state.get('next_pc')
        is_branch_taken = (next_pc != pc + 4) if pc is not None and next_pc is not None else False

        active_color = COLOR_ACTIVE
        active_width = LINE_WIDTH_ACTIVE
        mem_color = COLOR_MEM_ACCESS
        regw_color = COLOR_REG_WRITE
        # ctrl_color = COLOR_CONTROL_ACTIVE # Color used for static highlight
        # ctrl_width = LINE_WIDTH_CONTROL_ACTIVE

        # --- Highlight Data Paths and Components (Static) ---
        # (Giữ lại logic highlight tĩnh cho đường dữ liệu và component outlines như trước)
        # Ví dụ:
        self._highlight_element("path_pc_to_imem_addr", active_color, active_width)
        self._highlight_component("pc", active_color, active_width)
        self._highlight_component("imem", active_color, active_width)
        # ... (Thêm các highlight tĩnh khác cho đường data và component)

        # --- Trigger Control Signal Animations ---
        active_control_signals = []
        for signame, sigval in signals.items():
             # Xác định tín hiệu có đang active hay không (logic có thể cần chi tiết hơn)
            is_active_signal = (isinstance(sigval, (int, float)) and sigval != 0) or \
                               (isinstance(sigval, str) and sigval != '??' and sigval != '0')
            if is_active_signal:
                 active_control_signals.append(signame)
                 # Start animation for this signal
                 # print(f"Triggering animation for: {signame}")
                 self.start_signal_animation(signame)
                 # Optionally, also highlight the static control line immediately?
                 # ctrl_key = f"ctrl_{signame.lower()}"
                 # self._highlight_element(ctrl_key, COLOR_CONTROL_ACTIVE, LINE_WIDTH_CONTROL_ACTIVE)


    def _highlight_element(self, key, color, width):
        """Helper to highlight a specific element if it exists."""
        if key in self.elements:
            try:
                self.canvas.itemconfig(self.elements[key], fill=color, width=width)
            except tk.TclError: pass # Ignore if element deleted

    def _highlight_component(self, key, outline_color, outline_width):
         """Helper to highlight a component's outline."""
         comp_key = key + "_box"
         if comp_key in self.elements:
             try:
                 self.canvas.itemconfig(self.elements[comp_key], outline=outline_color, width=outline_width)
             except tk.TclError: pass # Ignore if element deleted
