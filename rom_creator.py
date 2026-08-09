#!/usr/bin/env python3
"""
EDIROL ROM Creator
Converts C++ ROMCreator to Python.
Extracts and rebuilds encrypted param.dat files from EDIROL synthesizer plugins.

Usage:
    python rom_creator.py extract     # Extract param.dat → .bin files
    python rom_creator.py rebuild     # Reassemble .bin files → ParamResult.dat
"""

import struct
import os
import sys
from typing import List, Tuple


# Byte manipulation macros
def LOWBYTE(v: int) -> int:
    return v & 0xFF


def HIGHBYTE(v: int) -> int:
    return (v >> 8) & 0xFF


def BYTELOW(v: int) -> int:
    """Get second byte (little-endian)."""
    return (v >> 8) & 0xFF


def BYTEHIGH(v: int) -> int:
    """Get first byte (little-endian)."""
    return v & 0xFF


def BYTEn(v: int, n: int) -> int:
    """Get nth byte."""
    return (v >> (n * 8)) & 0xFF


def BYTE1(v: int) -> int:
    """Get second byte."""
    return BYTEn(v, 1)


def HIBYTE(v: int) -> int:
    """Get high byte."""
    return (v >> 8) & 0xFF


def hex_array_to_int(array: bytes) -> int:
    """Convert 4-byte array to little-endian int."""
    if len(array) < 4:
        array = array + b'\x00' * (4 - len(array))
    return struct.unpack('<I', array[:4])[0]


def get_low_sub_byte(byte_val: int) -> int:
    """Get low 4 bits."""
    return byte_val & 0x0F


def get_high_sub_byte(byte_val: int) -> int:
    """Get high 4 bits."""
    return (byte_val >> 4) & 0x0F


def int_little_endian(value: int) -> int:
    """Convert int to little-endian representation."""
    return byte_array_to_int_little_endian(struct.pack('<I', value))


def int_big_endian(value: int) -> int:
    """Convert int to big-endian representation."""
    return byte_array_to_int_big_endian(struct.pack('>I', value))


def byte_array_to_int_big_endian(array: bytes) -> int:
    """Convert big-endian byte array to int."""
    if len(array) < 4:
        array = array + b'\x00' * (4 - len(array))
    return struct.unpack('>I', array[:4])[0]


def byte_array_to_int_little_endian(array: bytes) -> int:
    """Convert little-endian byte array to int."""
    if len(array) < 4:
        array = array + b'\x00' * (4 - len(array))
    return struct.unpack('<I', array[:4])[0]


def byte_array_to_int_special1(array: bytes) -> int:
    """Convert special byte order to int."""
    if len(array) < 4:
        array = array + b'\x00' * (4 - len(array))
    return struct.unpack('<I', array[:4])[0]


def byte_array_to_int_mid_big_endian(array: bytes) -> int:
    """Convert mid-big-endian (BADC order) to int."""
    if len(array) < 4:
        array = array + b'\x00' * (4 - len(array))
    # BADC order: swap middle bytes
    b = bytearray(4)
    b[1] = array[0]
    b[0] = array[1]
    b[3] = array[2]
    b[2] = array[3]
    return struct.unpack('<I', bytes(b))[0]


def set_low_byte(value: int, byte_val: int) -> int:
    """Replace the low byte of a 32-bit int."""
    return (value & 0xFFFFFF00) | (byte_val & 0xFF)


def set_high_byte(value: int, byte_val: int) -> int:
    """Replace the high byte of a 32-bit int."""
    return (value & 0x00FFFFFF) | ((byte_val & 0xFF) << 24)


def decode_array1(decode_map: bytes, buffer: bytes, position: int, size: int) -> bytes:
    """Decode array using map.
    
    Args:
        decode_map: 256-byte decode map
        buffer: Input buffer
        position: Starting position in buffer
        size: Number of bytes to decode
    
    Returns:
        Decoded data
    """
    ex_buffer = bytearray(size)
    
    for i in range(size):
        var1 = i & 0xFF
        extra = set_low_byte(i, 0)
        
        move_byte = decode_map[var1]
        byte_val = buffer[position + move_byte + extra]
        ex_buffer[i] = byte_val
    
    return bytes(ex_buffer)


class EncryptionController:
    """Handle encryption/decryption and encoding/decoding of EDIROL data."""
    
    def __init__(self, data: bytes):
        """Initialize with header/core data.
        
        Args:
            data: Core file data (at least 428 bytes)
        """
        self.header_buffer = data[:428]
        self.data = data
    
    def get_data1(self, a2: int, a3: int) -> int:
        """Get size field (little-endian)."""
        data1 = self.data[20:]  # Offset by 20
        
        offsets = {
            0: 304,
            1: 312,
            2: 320,
            3: (8 * a3) + 332,
            4: (8 * a3) + 372,
            5: (8 * a3) + 412,
        }
        
        offset = offsets.get(a2, 0)
        return hex_array_to_int(data1[offset:offset+4])
    
    def get_data2(self, a2: int, a3: int) -> int:
        """Get address field (big-endian) + 0x1ac."""
        data1 = self.data[20:]  # Offset by 20
        add = 0x1ac
        
        offsets = {
            0: 300,
            1: 308,
            2: 316,
            3: (8 * a3) + 328,
            4: (8 * a3) + 368,
            5: (8 * a3) + 408,
        }
        
        offset = offsets.get(a2, 0)
        return hex_array_to_int(data1[offset:offset+4]) + add
    
    def decode_array(self, buffer: bytes, position: int, size: int) -> bytes:
        """Decode array using stored header map.
        
        Args:
            buffer: Input buffer
            position: Starting position
            size: Number of bytes
        
        Returns:
            Decoded data
        """
        # Use stored header buffer's decode map
        return decode_array1(self.header_buffer[24:280], buffer, position, size)
    
    def encode_array(self, buffer: bytes, size: int) -> bytes:
        """Encode array using stored header map.
        
        Args:
            buffer: Input data
            size: Size to encode
        
        Returns:
            Encoded data
        """
        ex_buffer = bytearray(size)
        
        for i in range(size):
            var1 = i & 0xFF
            extra = set_low_byte(i, 0)
            
            move_byte = self.header_buffer[var1 + 24]
            byte_val = buffer[i]
            ex_buffer[move_byte + extra] = byte_val
        
        return bytes(ex_buffer)


def read_file(path: str) -> Tuple[bytes, int]:
    """Read binary file.
    
    Args:
        path: File path
    
    Returns:
        (file_data, file_size)
    """
    try:
        with open(path, 'rb') as f:
            data = f.read()
        return data, len(data)
    except FileNotFoundError:
        print(f"Error: cannot open {path}: File not found")
        return None, 0


def write_file(path: str, data: bytes) -> bool:
    """Write binary file.
    
    Args:
        path: File path
        data: Data to write
    
    Returns:
        True if successful
    """
    try:
        with open(path, 'wb') as f:
            f.write(data)
        return True
    except IOError as e:
        print(f"Error: cannot open {path}: {e}")
        return False


def run_extract(param_dat_path: str, output_dir: str) -> int:
    """Extract param.dat into component .bin files.
    
    Args:
        param_dat_path: Path to param.dat file
        output_dir: Output directory for .bin files
    
    Returns:
        0 on success, 1 on error
    """
    # Load param.dat
    buf, fsize = read_file(param_dat_path)
    if buf is None:
        return 1
    
    # Create encryption controller
    encryption = EncryptionController(buf)
    
    header_position = buf
    
    # Extract sizes and addresses
    patch_size = encryption.get_data1(1, 0)
    patch_address = encryption.get_data2(1, 0)
    
    rhythm_size = encryption.get_data1(2, 0)
    rhythm_address = encryption.get_data2(2, 0)
    
    rom_count = hex_array_to_int(header_position[0x130:0x134])
    
    print(f"Extraction: Found {rom_count} ROM bank(s)")
    
    # Extract each ROM bank
    for i in range(rom_count):
        rom_size = encryption.get_data1(5, i)
        rom_address = encryption.get_data2(5, i)
        
        wave_init_size = encryption.get_data1(4, i)
        wave_init_address = encryption.get_data2(4, i)
        
        tone_init_size = encryption.get_data1(3, i)
        tone_init_address = encryption.get_data2(3, i)
        
        # Decode data
        rom_data = encryption.decode_array(buf, rom_address, rom_size)
        wave_init_data = encryption.decode_array(buf, wave_init_address, wave_init_size)
        tone_init_data = encryption.decode_array(buf, tone_init_address, tone_init_size)
        
        # Write ROM data
        rom_path = os.path.join(output_dir, f"ROMData {i}.bin")
        if not write_file(rom_path, rom_data):
            return 1
        
        # Write wave init data
        wave_path = os.path.join(output_dir, f"WaveInitData {i}.bin")
        if not write_file(wave_path, wave_init_data):
            return 1
        
        # Write tone init data
        tone_path = os.path.join(output_dir, f"ToneInitData {i}.bin")
        if not write_file(tone_path, tone_init_data):
            return 1
    
    # Extract patch data
    patch_data = encryption.decode_array(buf, patch_address, patch_size)
    patch_path = os.path.join(output_dir, "PatchData.bin")
    if not write_file(patch_path, patch_data):
        return 1
    
    # Extract rhythm data
    rhythm_data = encryption.decode_array(buf, rhythm_address, rhythm_size)
    rhythm_path = os.path.join(output_dir, "RhythmData.bin")
    if not write_file(rhythm_path, rhythm_data):
        return 1
    
    print(f"Extraction complete: {rom_count} ROM bank(s), Patch={patch_size} bytes, Rhythm={rhythm_size} bytes")
    return 0


def create_param_file(core_file: bytes, core_file_size: int,
                      patch_data: bytes, patch_data_size: int,
                      rhythm_data: bytes, rhythm_data_size: int,
                      rom_count: int,
                      rom_arr: List[bytes], rom_size_arr: List[int],
                      wave_init_arr: List[bytes], wave_init_size_arr: List[int],
                      tone_init_arr: List[bytes], tone_init_size_arr: List[int]) -> Tuple[bytes, int]:
    """Reassemble param.dat from components.
    
    Args:
        core_file: Original core file data (428 bytes header)
        core_file_size: Size of core file
        patch_data: Patch data
        patch_data_size: Patch data size
        rhythm_data: Rhythm data
        rhythm_data_size: Rhythm data size
        rom_count: Number of ROM banks
        rom_arr: List of ROM data
        rom_size_arr: List of ROM sizes
        wave_init_arr: List of wave init data
        wave_init_size_arr: List of wave init sizes
        tone_init_arr: List of tone init data
        tone_init_size_arr: List of tone init sizes
    
    Returns:
        (final_data, total_size)
    """
    encryption = EncryptionController(core_file)
    
    # Calculate total size
    size = 428 + patch_data_size + rhythm_data_size
    for i in range(rom_count):
        size += rom_size_arr[i] + wave_init_size_arr[i] + tone_init_size_arr[i]
    
    # Create final buffer
    final_data = bytearray(size)
    final_data[:428] = core_file[:428]
    
    # Update ROM bank count in header
    final_data[0x130:0x134] = struct.pack('<I', rom_count)
    
    # Update sizes in header
    final_data[0x124:0x128] = struct.pack('<I', patch_data_size)
    final_data[0x12c:0x130] = struct.pack('<I', rhythm_data_size)
    
    # Encode and write data
    address = 0
    
    # Write patch data
    encoded_patch = encryption.encode_array(patch_data, patch_data_size)
    final_data[0x1ac + address:0x1ac + address + patch_data_size] = encoded_patch
    final_data[0x120:0x124] = struct.pack('<I', address)
    address += patch_data_size
    
    # Write rhythm data
    encoded_rhythm = encryption.encode_array(rhythm_data, rhythm_data_size)
    final_data[0x1ac + address:0x1ac + address + rhythm_data_size] = encoded_rhythm
    final_data[0x128:0x12c] = struct.pack('<I', address)
    address += rhythm_data_size
    
    # Write ROM banks
    for i in range(rom_count):
        tone_init_size_off = (8 * i) + 312
        tone_init_addr_off = (8 * i) + 308
        wave_init_size_off = (8 * i) + 352
        wave_init_addr_off = (8 * i) + 348
        rom_size_off = (8 * i) + 392
        rom_addr_off = (8 * i) + 388
        
        # Update sizes
        final_data[tone_init_size_off:tone_init_size_off+4] = struct.pack('<I', tone_init_size_arr[i])
        final_data[wave_init_size_off:wave_init_size_off+4] = struct.pack('<I', wave_init_size_arr[i])
        final_data[rom_size_off:rom_size_off+4] = struct.pack('<I', rom_size_arr[i])
        
        # Encode and write tone init
        encoded_tone = encryption.encode_array(tone_init_arr[i], tone_init_size_arr[i])
        final_data[0x1ac + address:0x1ac + address + tone_init_size_arr[i]] = encoded_tone
        final_data[tone_init_addr_off:tone_init_addr_off+4] = struct.pack('<I', address)
        address += tone_init_size_arr[i]
        
        # Encode and write wave init
        encoded_wave = encryption.encode_array(wave_init_arr[i], wave_init_size_arr[i])
        final_data[0x1ac + address:0x1ac + address + wave_init_size_arr[i]] = encoded_wave
        final_data[wave_init_addr_off:wave_init_addr_off+4] = struct.pack('<I', address)
        address += wave_init_size_arr[i]
        
        # Encode and write ROM
        encoded_rom = encryption.encode_array(rom_arr[i], rom_size_arr[i])
        final_data[0x1ac + address:0x1ac + address + rom_size_arr[i]] = encoded_rom
        final_data[rom_addr_off:rom_addr_off+4] = struct.pack('<I', address)
        address += rom_size_arr[i]
    
    return bytes(final_data), len(final_data)


def run_rebuild(param_dat_path: str, input_dir: str, output_path: str) -> int:
    """Rebuild param.dat from extracted .bin files.
    
    Args:
        param_dat_path: Path to original param.dat (for header)
        input_dir: Directory containing .bin files
        output_path: Output param.dat path
    
    Returns:
        0 on success, 1 on error
    """
    # Load original param.dat for header
    core_file_data, core_file_size = read_file(param_dat_path)
    if core_file_data is None:
        print("Error: could not load original param.dat")
        return 1
    
    # Load patch and rhythm data
    patch_data, patch_data_size = read_file(os.path.join(input_dir, "PatchData.bin"))
    if patch_data is None:
        return 1
    
    rhythm_data, rhythm_data_size = read_file(os.path.join(input_dir, "RhythmData.bin"))
    if rhythm_data is None:
        return 1
    
    if patch_data is None or rhythm_data is None:
        print("Error: PatchData.bin/RhythmData.bin missing - run 'extract' first.")
        return 1
    
    # Get ROM count from header
    rom_count = hex_array_to_int(core_file_data[0x130:0x134])
    print(f"Rebuilding with {rom_count} ROM bank(s)")
    
    # Load ROM banks
    rom_arr = []
    rom_size_arr = []
    wave_init_arr = []
    wave_init_size_arr = []
    tone_init_arr = []
    tone_init_size_arr = []
    
    for i in range(rom_count):
        rom_path = os.path.join(input_dir, f"ROMData {i}.bin")
        wave_path = os.path.join(input_dir, f"WaveInitData {i}.bin")
        tone_path = os.path.join(input_dir, f"ToneInitData {i}.bin")
        
        rom_data, rom_size = read_file(rom_path)
        wave_data, wave_size = read_file(wave_path)
        tone_data, tone_size = read_file(tone_path)
        
        if rom_data is None or wave_data is None or tone_data is None:
            print(f"Error: missing bank {i} files - run 'extract' first, or check bank count.")
            return 1
        
        rom_arr.append(rom_data)
        rom_size_arr.append(rom_size)
        wave_init_arr.append(wave_data)
        wave_init_size_arr.append(wave_size)
        tone_init_arr.append(tone_data)
        tone_init_size_arr.append(tone_size)
    
    # Create param file
    final_data, final_size = create_param_file(
        core_file_data, core_file_size,
        patch_data, patch_data_size,
        rhythm_data, rhythm_data_size,
        rom_count,
        rom_arr, rom_size_arr,
        wave_init_arr, wave_init_size_arr,
        tone_init_arr, tone_init_size_arr
    )
    
    # Write output
    if not write_file(output_path, final_data):
        return 1
    
    print(f"Rebuild complete: wrote {final_size} bytes to {output_path}")
    return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [extract|rebuild]")
        return 1
    
    mode = sys.argv[1]
    
    # Define paths
    param_dat = "param.dat"
    output_dir = "./"
    
    if mode == "extract":
        return run_extract(param_dat, output_dir)
    elif mode == "rebuild":
        return run_rebuild(param_dat, output_dir, "ParamResult.dat")
    else:
        print(f"Unknown mode '{mode}'. Use 'extract' or 'rebuild'.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
