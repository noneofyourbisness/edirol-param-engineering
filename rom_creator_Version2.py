#!/usr/bin/env python3
"""
Python port of ROM Creator (container-level extract/rebuild for HyperCanvas param.dat).

Handles:
  - the 428-byte header + 256-byte permutation table
  - splitting param.dat into PatchData.bin / RhythmData.bin / per-bank
    ROMData/WaveInitData/ToneInitData
  - reassembling those pieces back into a valid param.dat

This is a direct translation of the C++ ROM Creator (Main.cpp / EncryptionController.h),
validated byte-for-byte against the original C++ build's output.
"""
import struct
import sys
import os


def decode_block(buf: bytes, decode_map: bytes, position: int, size: int) -> bytes:
    """Reverse the container's byte-permutation cipher for one block."""
    out = bytearray(size)
    for i in range(size):
        var1 = i & 0xFF
        extra = i - var1
        move = decode_map[var1]
        out[i] = buf[position + move + extra]
    return bytes(out)


def encode_block(cleartext: bytes, decode_map: bytes) -> bytes:
    """Inverse of decode_block: scramble cleartext bytes back into container form.

    The container stores encoded blocks padded to 256-byte rows, so the encoded
    buffer must be the next multiple of 256 in length.
    """
    size = len(cleartext)
    # encoded blocks are stored in 256-byte rows in the container
    enc_size = ((size + 255) // 256) * 256
    out = bytearray(enc_size)
    for i in range(size):
        var1 = i & 0xFF
        extra = i - var1
        move = decode_map[var1]
        out[move + extra] = cleartext[i]
    return bytes(out)


# --- per-bank header field offsets (validated against real multi-bank param.dat files) ---
def _size_addr_offsets(case: int, idx: int = 0):
    if case == 0:
        return 284, 280
    elif case == 1:
        return 292, 288
    elif case == 2:
        return 300, 296
    elif case == 3:  # ToneInit
        return (8 * idx) + 312, (8 * idx) + 308
    elif case == 4:  # WaveInit
        return (8 * idx) + 352, (8 * idx) + 348
    elif case == 5:  # ROM
        return (8 * idx) + 392, (8 * idx) + 388
    raise ValueError("bad case")


def read_header_field(data: bytes, case: int, idx: int = 0):
    size_off, addr_off = _size_addr_offsets(case, idx)
    size = struct.unpack_from('<i', data, size_off)[0]
    addr = struct.unpack_from('<i', data, addr_off)[0] + 428
    return size, addr


def extract(param_dat_path: str, out_dir: str):
    """Split a param.dat into its component .bin files, written to out_dir."""
    with open(param_dat_path, 'rb') as f:
        data = f.read()

    decode_map = data[24:24 + 256]
    assert sorted(decode_map) == list(range(256)), "not a valid permutation table - is this really a param.dat?"

    patch_size, patch_addr = read_header_field(data, 1)
    rhythm_size, rhythm_addr = read_header_field(data, 2)
    rom_count = struct.unpack_from('<I', data, 0x130)[0]

    os.makedirs(out_dir, exist_ok=True)

    patch_data = decode_block(data, decode_map, patch_addr, patch_size)
    with open(os.path.join(out_dir, 'PatchData.bin'), 'wb') as f:
        f.write(patch_data)

    rhythm_data = decode_block(data, decode_map, rhythm_addr, rhythm_size)
    with open(os.path.join(out_dir, 'RhythmData.bin'), 'wb') as f:
        f.write(rhythm_data)

    for i in range(rom_count):
        tone_size, tone_addr = read_header_field(data, 3, i)
        wave_size, wave_addr = read_header_field(data, 4, i)
        rom_size, rom_addr = read_header_field(data, 5, i)

        tone_data = decode_block(data, decode_map, tone_addr, tone_size)
        with open(os.path.join(out_dir, f'ToneInitData {i}.bin'), 'wb') as f:
            f.write(tone_data)

        wave_data = decode_block(data, decode_map, wave_addr, wave_size)
        with open(os.path.join(out_dir, f'WaveInitData {i}.bin'), 'wb') as f:
            f.write(wave_data)

        rom_data = decode_block(data, decode_map, rom_addr, rom_size)
        with open(os.path.join(out_dir, f'ROMData {i}.bin'), 'wb') as f:
            f.write(rom_data)

    print(f"Extraction complete: {rom_count} ROM bank(s), Patch={patch_size} bytes, Rhythm={rhythm_size} bytes")


def rebuild(param_dat_path: str, in_dir: str, out_path: str):
    """Reassemble the component .bin files in in_dir back into a valid param.dat."""
    with open(param_dat_path, 'rb') as f:
        core_file = f.read()

    decode_map = core_file[24:24 + 256]

    with open(os.path.join(in_dir, 'PatchData.bin'), 'rb') as f:
        patch_data = f.read()
    with open(os.path.join(in_dir, 'RhythmData.bin'), 'rb') as f:
        rhythm_data = f.read()

    rom_count = struct.unpack_from('<I', core_file, 0x130)[0]
    print(f"Rebuilding with {rom_count} ROM bank(s)")

    banks = []
    for i in range(rom_count):
        with open(os.path.join(in_dir, f'ToneInitData {i}.bin'), 'rb') as f:
            tone_data = f.read()
        with open(os.path.join(in_dir, f'WaveInitData {i}.bin'), 'rb') as f:
            wave_data = f.read()
        with open(os.path.join(in_dir, f'ROMData {i}.bin'), 'rb') as f:
            rom_data = f.read()
        banks.append((tone_data, wave_data, rom_data))

    def enc_len(n: int) -> int:
        return ((n + 255) // 256) * 256

    total_size = 428 + enc_len(len(patch_data)) + enc_len(len(rhythm_data))
    for tone_data, wave_data, rom_data in banks:
        total_size += enc_len(len(tone_data)) + enc_len(len(wave_data)) + enc_len(len(rom_data))

    final_data = bytearray(total_size)
    final_data[0:428] = core_file[0:428]

    # keep the header's own ROM bank count in sync
    struct.pack_into('<I', final_data, 0x130, rom_count)

    # sizes in header are the cleartext sizes (unpadded)
    struct.pack_into('<I', final_data, 0x124, len(patch_data))
    struct.pack_into('<I', final_data, 0x12c, len(rhythm_data))

    address = 0

    def place(cleartext, size_off, addr_off):
        nonlocal address
        encoded = encode_block(cleartext, decode_map)
        final_data[0x1ac + address: 0x1ac + address + len(encoded)] = encoded
        struct.pack_into('<I', final_data, addr_off, address)
        # advance by the encoded (padded) length so blocks don't overlap
        address += len(encoded)

    place(patch_data, 0x124, 0x120)
    place(rhythm_data, 0x12c, 0x128)

    for i, (tone_data, wave_data, rom_data) in enumerate(banks):
        tone_size_off, tone_addr_off = _size_addr_offsets(3, i)
        wave_size_off, wave_addr_off = _size_addr_offsets(4, i)
        rom_size_off, rom_addr_off = _size_addr_offsets(5, i)

        struct.pack_into('<I', final_data, tone_size_off, len(tone_data))
        struct.pack_into('<I', final_data, wave_size_off, len(wave_data))
        struct.pack_into('<I', final_data, rom_size_off, len(rom_data))

        place(tone_data, tone_size_off, tone_addr_off)
        place(wave_data, wave_size_off, wave_addr_off)
        place(rom_data, rom_size_off, rom_addr_off)

    with open(out_path, 'wb') as f:
        f.write(final_data)

    print(f"Rebuild complete: wrote {len(final_data)} bytes to {out_path}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  rom_creator.py extract <param.dat> <out_dir>")
        print("  rom_creator.py rebuild <original_param.dat> <in_dir> <out_param.dat>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == 'extract':
        extract(sys.argv[2], sys.argv[3])
    elif mode == 'rebuild':
        rebuild(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Unknown mode '{mode}'")
        sys.exit(1)