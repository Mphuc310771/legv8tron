# assembler.py

def placeholder_assembler(assembly_code):
    """
    Placeholder rất đơn giản cho bộ biên dịch LEGv8.
    CHỈ phân tích cơ bản để lấy instruction_memory, pc_to_line, label_to_pc.
    KHÔNG thực hiện biên dịch sang mã máy thực sự.
    """
    print("Running Placeholder Assembler...")
    instruction_memory = {} # {address: (line_number, instruction_string)}
    pc_to_line_map = {}     # {address: line_number}
    label_to_pc_map = {}    # {label_name: address}
    current_pc = 0x00000000 # Bắt đầu từ địa chỉ 0
    line_number = 0

    lines = assembly_code.splitlines()
    for i, line in enumerate(lines):
        line_number = i + 1
        original_line = line # Giữ lại dòng gốc
        # Xóa comment và khoảng trắng thừa
        line = line.split('//')[0].strip()
        if not line:
            continue

        # Kiểm tra nhãn (ví dụ: "LOOP:")
        if line.endswith(':'):
            label_name = line[:-1].strip()
            if label_name:
                if label_name in label_to_pc_map:
                    print(f"Assembler Warning: Duplicate label '{label_name}' at line {line_number}")
                else:
                    label_to_pc_map[label_name] = current_pc
                    print(f"  Found label '{label_name}' at address {current_pc:#0x}")
            # Dòng chứa nhãn không tạo ra lệnh, trừ khi có lệnh trên cùng dòng (ít phổ biến)
            parts = line[:-1].split(maxsplit=1) # Tách nhãn khỏi phần còn lại nếu có
            if len(parts) > 1 and parts[1].strip(): # Có lệnh sau nhãn trên cùng dòng
                 line = parts[1].strip()
            else:
                 continue # Chỉ có nhãn, đi tiếp dòng sau


        # Giả định mọi dòng còn lại là một lệnh và chiếm 4 byte
        # Lưu trữ dòng lệnh gốc thay vì mã máy thực sự trong ví dụ này
        instruction_data = (line_number, original_line) # Lưu cả số dòng gốc và lệnh text
        instruction_memory[current_pc] = instruction_data
        pc_to_line_map[current_pc] = line_number
        print(f"  Mapping PC {current_pc:#0x} to line {line_number}: '{line}'")

        current_pc += 4 # Tăng PC cho lệnh tiếp theo

    print("Placeholder Assembly Complete.")
    print(f"  Instructions: {len(instruction_memory)}, Labels: {len(label_to_pc_map)}")
    print("Instruction Memory:", instruction_memory)
    print("PC to Line Map:", pc_to_line_map)
    print("Label to PC Map:", label_to_pc_map)
    return instruction_memory, pc_to_line_map, label_to_pc_map