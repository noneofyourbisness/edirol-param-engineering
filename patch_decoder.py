#!/usr/bin/env python3
"""
EDIROL Patch Decoder
Converts C++ PatchDecoder to Python.
Decodes patch and rhythm data from EDIROL synthesizer parameter files.
"""

import struct
import os
from typing import Tuple


# Precomputed lookup table (from C++ dword_4519481)
DWORD_4519481 = bytes([
    0x01, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00, 0x0f, 0x00, 0x00, 0x00,
    0x1f, 0x00, 0x00, 0x00, 0x3f, 0x00, 0x00, 0x00, 0x7f, 0x00, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00,
    0xff, 0x01, 0x00, 0x00, 0xff, 0x03, 0x00, 0x00, 0xff, 0x07, 0x00, 0x00, 0xff, 0x0f, 0x00, 0x00,
    0xff, 0x1f, 0x00, 0x00, 0xff, 0x3f, 0x00, 0x00, 0xff, 0x7f, 0x00, 0x00, 0xff, 0xff, 0x00, 0x00,
    0xff, 0xff, 0x01, 0x00, 0xff, 0xff, 0x03, 0x00, 0xff, 0xff, 0x07, 0x00, 0xff, 0xff, 0x0f, 0x00,
    0xff, 0xff, 0x1f, 0x00, 0xff, 0xff, 0x3f, 0x00, 0xff, 0xff, 0x7f, 0x00, 0xff, 0xff, 0xff, 0x00,
    0xff, 0xff, 0xff, 0x01, 0xff, 0xff, 0xff, 0x03, 0xff, 0xff, 0xff, 0x07, 0xff, 0xff, 0xff, 0x0f,
    0xff, 0xff, 0xff, 0x1f, 0xff, 0xff, 0xff, 0x3f, 0xff, 0xff, 0xff, 0x7f, 0xff, 0xff, 0xff, 0xff
])

# Lookup table: convert byte array indices to integers
DWORD_451948 = [0] * 33


def init_lookup_table():
    """Initialize DWORD_451948 from DWORD_4519481."""
    global DWORD_451948
    for i in range(33):
        DWORD_451948[i] = struct.unpack(
            '<I', DWORD_4519481[4*i:4*i+4]
        )[0]


def hex_array_to_int(array: bytes) -> int:
    """Convert 4-byte array to little-endian int."""
    if len(array) < 4:
        array = array + b'\x00' * (4 - len(array))
    return struct.unpack('<I', array[:4])[0]


def hex_array_to_short(array: bytes) -> int:
    """Convert 2-byte array to little-endian short."""
    if len(array) < 2:
        array = array + b'\x00' * (2 - len(array))
    return struct.unpack('<H', array[:2])[0]


def set_low_byte(value: int, byte_val: int) -> int:
    """Replace the low byte of a 32-bit int."""
    return (value & 0xFFFFFF00) | (byte_val & 0xFF)


def get_bit(byte_val: int, bit_id: int) -> bool:
    """Extract a single bit at position bit_id."""
    return bool((byte_val >> bit_id) & 1)


def set_bit(byte_val: int, bit_id: int, bit: bool) -> int:
    """Set a single bit at position bit_id."""
    if bit:
        return byte_val | (1 << bit_id)
    else:
        return byte_val & ~(1 << bit_id)


def get_byte_by_bit(data: bytes, bit_position: int) -> int:
    """Extract byte using bit positioning."""
    real_position = bit_position // 8
    shift = bit_position - (real_position * 8)
    shift_byte1 = shift
    shift_byte2 = 8 - shift
    
    result = (data[real_position] >> shift_byte1) | (data[real_position] << shift_byte1)
    return result & 0xFF


def sub_404400(pointer: bytes, decode_map: bytes) -> int:
    """Decode variable-length data using map.
    
    Args:
        pointer: Data buffer starting position
        decode_map: 12-byte decode map structure
    
    Returns:
        Decoded integer value
    """
    main_data_address = pointer[decode_map[0]:]
    byte_val = decode_map[2]
    
    # Handle sign
    if byte_val & 128:
        byte_val = (-byte_val) & 0xFF
    
    byte_1 = byte_val
    loop_index = byte_val + decode_map[3]
    v6 = -loop_index
    v7 = 0
    
    pos = 0
    while loop_index > 0:
        loop_index -= 8
        v6 += 8
        v7 = (main_data_address[pos] | (v7 << 8)) & 0xFFFFFFFF
        pos += 1
    
    result = (v7 >> v6) & DWORD_451948[byte_1 - 1]
    return result


def sub_4045C0(data_ptr: bytes, decode_map: bytes) -> int:
    """Decode with conditional offset.
    
    Args:
        data_ptr: Data buffer
        decode_map: 12-byte decode map
    
    Returns:
        Decoded value, possibly offset by (64 - v3)
    """
    result = sub_404400(data_ptr, decode_map)
    v3 = decode_map[4]
    
    if decode_map[8] - v3 < 0 and v3 < 64:
        result += 64 - v3
    
    return result & 0xFFFFFFFF


def sub_4044E0(data_buffer: bytes, decode_map: bytes, size: int) -> Tuple[bytes, int]:
    """Main decoding function for patch/rhythm data.
    
    Args:
        data_buffer: Input buffer
        decode_map: Map table buffer
        size: Number of bytes to decode
    
    Returns:
        (decoded_data, items_processed)
    """
    result_buffer = bytearray(size)
    loop_index = size
    v5 = 0
    i = 0
    
    while loop_index > 0:
        byte_val = struct.unpack('b', bytes([decode_map[2]]))[0]  # signed byte
        loop_index -= 1
        
        if byte_val >= 0:
            result_buffer[i] = sub_4045C0(data_buffer, decode_map)
            i += 1
        else:
            sizea = 0
            while -byte_val < 8:
                v5 -= byte_val
                result_buffer[i] = sub_404400(data_buffer, decode_map)
                i += 1
                decode_map = decode_map[12:]
                sizea += 1
                if loop_index == 0:
                    return bytes(result_buffer), i
                byte_val = struct.unpack('b', bytes([decode_map[2]]))[0]
            
            v10 = -(byte_val + v5)
            if v10 >= 8:
                return bytes(result_buffer), -1
            
            result_buffer[i] = DWORD_451948[v10 - 1] & sub_404400(data_buffer, decode_map)
            i += 1
            i += sizea
        
        decode_map = decode_map[12:]
        v5 = 0
    
    return bytes(result_buffer), i


def convert_ex(data: bytes, size: int) -> bytes:
    """Convert array using bit shifting.
    
    Args:
        data: Input data
        size: Number of bytes
    
    Returns:
        Converted data
    """
    converted = bytearray(size)
    
    for i in range(size - 1):
        byte_val = data[i] << 1
        byte_val |= (data[i + 1] >> 6) & 0x01
        converted[i] = byte_val & 0xFF
    
    return bytes(converted)


def decode_patch_data(buf: bytes, buf_patch_init: bytes, buf_map: bytes) -> Tuple[bytes, int]:
    """Decode patch data from buffer.
    
    Args:
        buf: Input patch buffer
        buf_patch_init: Initial patch template
        buf_map: Decode map table
    
    Returns:
        (decoded_data, total_size)
    """
    bank_count = buf[0]
    inst_count = bank_count * 256
    patch_buffer_size = 948 * inst_count + 4
    patch_buffer = bytearray(patch_buffer_size)
    
    # Initialize patches
    for i in range(inst_count):
        current_pos = 948 * i
        patch_buffer[current_pos:current_pos+79] = buf_patch_init[0:79]
        patch_buffer[current_pos+79:current_pos+224] = buf_patch_init[79:224]
        patch_buffer[current_pos+224:current_pos+276] = buf_patch_init[0xe4:0xe4+52]
        patch_buffer[current_pos+276:current_pos+359] = buf_patch_init[0x118:0x118+83]
        patch_buffer[current_pos+359:current_pos+400] = buf_patch_init[0x16c:0x16c+41]
    
    # Decode data
    main_data_address = buf[14:]
    position = 0
    
    for i in range(inst_count):
        # Decode main sections
        decoded, _ = sub_4044E0(main_data_address, buf_map[12 * 0x242:], 79)
        patch_buffer[position:position+79] = decoded
        main_data_address = main_data_address[56:]
        
        decoded, _ = sub_4044E0(main_data_address, buf_map[12 * 0x294:], 145)
        patch_buffer[position+79:position+224] = decoded
        main_data_address = main_data_address[78:]
        
        decoded, _ = sub_4044E0(main_data_address, buf_map[12 * 0x328:], 52)
        patch_buffer[position+224:position+276] = decoded
        main_data_address = main_data_address[26:]
        
        decoded, _ = sub_4044E0(main_data_address, buf_map[12 * 0x35D:], 83)
        patch_buffer[position+276:position+359] = decoded
        main_data_address = main_data_address[42:]
        
        decoded, _ = sub_4044E0(main_data_address, buf_map[12 * 0x3B1:], 41)
        patch_buffer[position+359:position+400] = decoded
        main_data_address = main_data_address[32:]
        
        # Decode rhythm sections
        position_1 = position
        for _ in range(4):
            decoded, _ = sub_4044E0(main_data_address, buf_map[12 * 0x3D8 + 36:], 137)
            patch_buffer[position_1+400:position_1+537] = decoded
            main_data_address = main_data_address[85:]
            position_1 += 137
        
        position += 948
    
    return bytes(patch_buffer), patch_buffer_size


def rhythm_decode(rhythm_map: bytes, data_buffer: bytes, add_inst_size: int) -> Tuple[bytes, int]:
    """Decode rhythm data.
    
    Args:
        rhythm_map: Rhythm decode map
        data_buffer: Rhythm data buffer
        add_inst_size: Additional instrument size offset
    
    Returns:
        (decoded_rhythm_data, total_size)
    """
    offset = 0
    count = data_buffer[1]
    count = count + offset
    
    final_size = 17282 * (count + add_inst_size) + 4
    final_data = bytearray(final_size)
    
    v12 = data_buffer[20:]
    position = 17282 * offset
    loop_index = count - offset
    
    while loop_index > 0:
        decoded, _ = sub_4044E0(v12, rhythm_map[12 * 0x46c:], 18)
        final_data[position:position+18] = decoded
        v14 = v12[14:]
        
        decoded, _ = sub_4044E0(v14, rhythm_map[12 * 0x480:], 145)
        final_data[position+18:position+163] = decoded
        v14 = v14[78:]
        
        decoded, _ = sub_4044E0(v14, rhythm_map[12 * 0x514:], 52)
        final_data[position+163:position+215] = decoded
        v14 = v14[26:]
        
        decoded, _ = sub_4044E0(v14, rhythm_map[12 * 0x549:], 83)
        final_data[position+215:position+298] = decoded
        v12 = v14[42:]
        
        # Decode rhythm patterns
        for i in range(0, 16984, 193):
            aaa = hex_array_to_int(v12[:4])
            id_val = (((aaa & 0xFF00) | (aaa << 16)) << 8) | (((aaa >> 16) | (aaa & 0xFF0000)) >> 8)
            id_val -= 20
            
            decoded, _ = sub_4044E0(v12[id_val:], rhythm_map[12 * 0x59d:], 193)
            final_data[position+i+298:position+i+491] = decoded
            v12 = v12[4:]
        
        position += 17282
        loop_index -= 1
    
    return bytes(final_data), final_size


def read_file(path: str) -> bytes:
    """Read binary file."""
    with open(path, 'rb') as f:
        return f.read()


def write_file(path: str, data: bytes) -> None:
    """Write binary file."""
    with open(path, 'wb') as f:
        f.write(data)


def main():
    """Main execution."""
    init_lookup_table()
    
    # File paths
    filename_in = "RhythmData.bin"
    filename_map = "MainMap"
    filename_rhythm_map = "RhythmMap"
    filename_patch_init = "PatchInit"
    filename_out = "Result"
    filename_out_clear = "ResultClear"
    
    # Load input files
    print("Loading input files...")
    buf = read_file(filename_in)
    buf_map = read_file(filename_map)
    buf_rhythm_map = read_file(filename_rhythm_map)
    buf_patch_init = read_file(filename_patch_init)
    
    # Decode rhythm data
    print("Decoding rhythm data...")
    inst_count = 0x1b
    patch_buffer, patch_buffer_size = rhythm_decode(buf_rhythm_map, buf, 128 - inst_count)
    
    # Write clear/decoded data
    print(f"Writing decoded data ({len(patch_buffer)} bytes)...")
    write_file(filename_out_clear, patch_buffer)
    
    # Reload for encoding (simulated - would need RhythmEncode implementation)
    print(f"Decode complete. Output: {filename_out_clear}")
    print(f"Total size: {len(patch_buffer)} bytes")


if __name__ == "__main__":
    main()
