# legv8_simulator.py
import random # Để ví dụ thay đổi giá trị thanh ghi/bộ nhớ

class LEGv8_Simplified_Simulator:
    """
    Lớp mô phỏng lõi (rất đơn giản hóa) cho LEGv8.
    CHÚ Ý: Phần xử lý lệnh ('step') hiện tại chỉ là placeholder,
           cần được triển khai chi tiết cho từng lệnh LEGv8 thực tế.
    """
    def __init__(self, num_registers=32, mem_size=1024):
        self.num_registers = num_registers
        self.mem_size = mem_size # Kích thước bộ nhớ dữ liệu (theo byte)
        self.initial_pc = 0x00000000 # Địa chỉ bắt đầu mặc định

        # Trạng thái nội bộ
        self.registers = [0] * self.num_registers
        self.data_memory = {} # Dùng dictionary cho bộ nhớ dữ liệu thưa
        self.instruction_memory = {} # Lưu lệnh đã biên dịch {addr: instruction_data}
        self.pc = self.initial_pc
        self.flags = {'N': 0, 'Z': 0, 'V': 0, 'C': 0}
        self.halted = False
        self.pc_to_line_map = {} # Lưu map từ GUI để dễ debug (không dùng trực tiếp trong step)
        self.label_to_pc_map = {} # Lưu map nhãn từ assembler

        # Trạng thái chu kỳ trước (để trả về cho GUI)
        self.last_state = {}

        print("LEGv8 Simulator Initialized")

    def reset(self):
        """Reset trạng thái runtime của simulator (PC, registers, flags), giữ nguyên chương trình."""
        print("Simulator Resetting...")
        self.pc = self.initial_pc
        self.registers = [0] * self.num_registers
        # self.data_memory = {} # Quyết định xem có xóa bộ nhớ dữ liệu khi reset hay không
        self.flags = {'N': 0, 'Z': 0, 'V': 0, 'C': 0}
        self.halted = False
        self.last_state = {} # Xóa trạng thái cũ
        print(f"Simulator Reset. PC = {self.pc:#0x}")

    def load_program(self, instruction_memory, label_to_pc_map):
        """Nạp chương trình đã biên dịch vào bộ nhớ lệnh."""
        print(f"Loading program. {len(instruction_memory)} instructions.")
        self.instruction_memory = instruction_memory
        self.label_to_pc_map = label_to_pc_map
        # Tìm địa chỉ bắt đầu thực tế nếu có (ví dụ: lệnh đầu tiên)
        if self.instruction_memory:
             # Mặc định bắt đầu từ địa chỉ nhỏ nhất được nạp
            self.initial_pc = min(self.instruction_memory.keys())
        else:
            self.initial_pc = 0x00000000
        self.reset() # Reset trạng thái sau khi nạp chương trình mới
        self.halted = False # Đảm bảo không bị dừng sau khi load

    def step(self):
        """
        Thực thi một lệnh tại địa chỉ PC hiện tại.
        *** PHẦN NÀY CẦN TRIỂN KHAI CHI TIẾT LOGIC CỦA TỪNG LỆNH LEGv8 ***
        Hiện tại chỉ là mô phỏng đơn giản việc chạy và tạo state giả.
        """
        current_pc = self.pc

        if self.halted:
            print("Simulator HALTED.")
            self.last_state = {'halted': True, 'pc': current_pc}
            return self.last_state

        if current_pc not in self.instruction_memory:
            print(f"Error: PC {current_pc:#0x} points outside loaded program memory.")
            self.halted = True
            self.last_state = {'halted': True, 'pc': current_pc, 'error': 'Invalid PC'}
            return self.last_state

        # --- Bắt đầu phần logic giả lập ---
        # Lấy "lệnh" giả định (trong thực tế cần giải mã từ instruction_memory[current_pc])
        mock_instruction_info = self._get_mock_instruction_info(current_pc)
        instruction_name = mock_instruction_info.get('name', 'UNKNOWN')
        print(f"Executing at PC={current_pc:#0x}: Instruction '{instruction_name}' (Mock)")

        # Tạo trạng thái giả lập cho GUI
        state = {
            'pc': current_pc,
            'next_pc': current_pc + 4, # Giả định lệnh dài 4 byte
            'control_signals': self._get_mock_control_signals(instruction_name),
            'active_component': self._get_mock_active_component(instruction_name),
            'mem_addr': None,
            'mem_write': False,
            'mem_read': False,
            'reg_written': None, # Thanh ghi nào được ghi
            'flags': self.flags.copy(), # Trạng thái cờ TRƯỚC khi lệnh chạy (hoặc sau tùy thiết kế)
            'halted': False,
            'instruction_raw': self.instruction_memory.get(current_pc, None) # Gửi lệnh thô nếu cần
        }

        # --- Giả lập thay đổi trạng thái ---
        # Ví dụ: Nếu là lệnh ADD/ADDI, giả lập ghi vào thanh ghi
        if instruction_name in ["ADD", "ADDI", "SUB"]:
            reg_idx = random.randint(1, self.num_registers - 1) # Ghi vào X1-X31
            old_val = self.registers[reg_idx]
            self.registers[reg_idx] = random.randint(0, 1000) # Giá trị ngẫu nhiên
            state['reg_written'] = f'X{reg_idx}'
            print(f"  Mock: Write {self.registers[reg_idx]} to X{reg_idx} (was {old_val})")
            # Giả lập cập nhật cờ Z
            if self.registers[reg_idx] == 0:
                 state['flags']['Z'] = 1
            else:
                 state['flags']['Z'] = 0

        # Ví dụ: Nếu là lệnh LDUR/STUR, giả lập truy cập bộ nhớ
        elif instruction_name in ["LDUR", "STUR"]:
            mem_addr = random.randint(0, self.mem_size - 8) & ~0x7 # Địa chỉ căn 8 byte
            state['mem_addr'] = mem_addr
            state['active_component'] = 'MEM' # Ưu tiên MEM nếu có truy cập
            if instruction_name == "STUR":
                state['mem_write'] = True
                write_val = random.randint(0, 255)
                self.data_memory[mem_addr] = write_val # Lưu giá trị vào bộ nhớ giả
                print(f"  Mock: Write {write_val} to Memory Address {mem_addr:#0x}")
            else: # LDUR
                state['mem_read'] = True
                read_val = self.data_memory.get(mem_addr, 0) # Đọc từ bộ nhớ giả
                reg_idx = random.randint(1, self.num_registers - 1)
                self.registers[reg_idx] = read_val
                state['reg_written'] = f'X{reg_idx}'
                print(f"  Mock: Read {read_val} from Memory Address {mem_addr:#0x} into X{reg_idx}")

        # Ví dụ: Lệnh HALT
        elif instruction_name == "HALT":
            state['halted'] = True
            self.halted = True
            state['next_pc'] = current_pc # PC không tăng nữa
            print("  Mock: HALT instruction encountered.")

        # --- Kết thúc phần logic giả lập ---

        # Cập nhật PC cho bước tiếp theo (trừ khi HALT)
        if not self.halted:
            self.pc = state['next_pc']
        self.flags = state['flags'].copy() # Cập nhật cờ trạng thái của simulator

        self.last_state = state # Lưu lại trạng thái để GUI có thể truy vấn nếu cần
        return state

    # --- Các hàm helper giả lập ---
    def _get_mock_instruction_info(self, pc):
        # Hàm này cần phân tích instruction_memory[pc] thực tế
        # Hiện tại chỉ trả về tên lệnh giả dựa trên PC
        seed = pc // 4
        mock_ops = ["ADDI", "LDUR", "ADD", "STUR", "SUB", "B", "CBZ", "HALT"]
        if pc > 0x40 : # Giả sử chương trình kết thúc bằng HALT
             return {'name': 'HALT'}
        return {'name': mock_ops[seed % (len(mock_ops)-1)]} # Tránh HALT quá sớm

    def _get_mock_control_signals(self, instruction_name):
        # Tạo tín hiệu điều khiển giả dựa trên tên lệnh
        signals = {'RegWrite': 0, 'ALUSrc': 0, 'MemRead': 0, 'MemWrite': 0, 'Branch': 0, 'ALUOp': '??'}
        if instruction_name in ["ADD", "SUB", "AND", "ORR"]:
            signals['RegWrite'] = 1
            signals['ALUOp'] = instruction_name[:3]
        elif instruction_name in ["ADDI", "SUBI"]:
            signals['RegWrite'] = 1
            signals['ALUSrc'] = 1
            signals['ALUOp'] = instruction_name[:3]
        elif instruction_name == "LDUR":
            signals['RegWrite'] = 1
            signals['ALUSrc'] = 1
            signals['MemRead'] = 1
            signals['ALUOp'] = 'ADD' # Tính địa chỉ
        elif instruction_name == "STUR":
            signals['ALUSrc'] = 1
            signals['MemWrite'] = 1
            signals['ALUOp'] = 'ADD' # Tính địa chỉ
        elif instruction_name in ["B", "CBZ", "B.cond"]:
            signals['Branch'] = 1
            signals['ALUOp'] = '??' # Có thể không cần ALU chính
        return signals

    def _get_mock_active_component(self, instruction_name):
        # Xác định thành phần chính hoạt động (giả lập)
        if instruction_name in ["ADD", "SUB", "AND", "ORR", "ADDI", "SUBI"]:
            return 'ALU'
        elif instruction_name in ["LDUR", "STUR"]:
            return 'MEM' # ALU cũng hoạt động để tính địa chỉ, nhưng MEM là đích chính
        elif instruction_name in ["B", "CBZ", "B.cond"]:
            return 'BRANCH'
        elif instruction_name == "HALT":
            return 'NONE'
        return 'DECODE' # Mặc định

    def get_register_value(self, reg_index):
        if 0 <= reg_index < self.num_registers:
            return self.registers[reg_index]
        return None

    def get_memory_value(self, address):
         # Nên xử lý alignment và kích thước đọc/ghi thực tế
        return self.data_memory.get(address, 0) # Trả về 0 nếu chưa có gì

    def get_state_summary(self):
        """Trả về tóm tắt trạng thái hiện tại (hữu ích cho update_display)."""
        return {
            'pc': self.pc,
            'flags': self.flags.copy(),
            'halted': self.halted,
            # Thêm các thông tin khác nếu cần hiển thị tức thì
        }