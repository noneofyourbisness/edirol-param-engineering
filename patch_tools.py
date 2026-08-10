#!/usr/bin/env python3
"""
Python port of Patch Decode (bit-field codec for HyperCanvas patch/rhythm structs).

Direct translation of Encoder.h / Main.cpp's sub_404400 / sub_4045C0 / sub_4044E0
(decode) and sub_10040DA0 / sub_10041540 / sub_10041410 (encode), plus the
higher-level DecodePatchData / RhythmDecode / sub_404E50Encode / RhythmEncode
orchestration functions.

Validated byte-for-byte against the original C++ build's decoded output.
"""
import struct


# dword_451948[k] = the (k+1)-bit mask: 1,3,7,15,31,63,127,255,511,...
DWORD_451948 = [(1 << (k + 1)) - 1 for k in range(33)]


def _signed_byte(b: int) -> int:
    return b - 256 if b >= 128 else b


def _negate_u8(b: int) -> int:
    """Mirror C's `Byte = -Byte;` on an unsigned char (wraps mod 256)."""
    return (256 - b) & 0xFF if b != 0 else 0


# ------------------------- DECODE SIDE -------------------------

def _sub_404400(data: bytes, data_off: int, mp: bytes, mp_off: int) -> int:
    base = mp[mp_off + 0]
    ptr_pos = data_off + base
    byte = mp[mp_off + 2]
    if byte & 0x80:
        byte = _negate_u8(byte)
    byte_1 = byte
    loopindex = byte + mp[mp_off + 3]
    v6 = -loopindex
    v7 = 0
    while True:
        loopindex -= 8
        v6 += 8
        v7 = (data[ptr_pos] | (v7 << 8)) & 0xFFFFFFFF
        ptr_pos += 1
        if loopindex <= 0:
            break
    return (v7 >> v6) & DWORD_451948[byte_1 - 1]


def _sub_4045C0(data: bytes, data_off: int, mp: bytes, mp_off: int) -> int:
    result = _sub_404400(data, data_off, mp, mp_off)
    v3 = mp[mp_off + 4]
    if mp[mp_off + 8] < v3 and v3 < 64:
        result += 64 - v3
    return result


def _sub_4044E0(data: bytes, data_off: int, mp: bytes, mp_off: int, size: int) -> bytes:
    out = bytearray()
    loopindex = size
    v5 = 0
    i = 0
    while loopindex > 0:
        byte = _signed_byte(mp[mp_off + 2])
        loopindex -= 1
        if byte >= 0:
            out.append(_sub_4045C0(data, data_off, mp, mp_off) & 0xFF)
            mp_off += 12
            i += 1
            v5 = 0
            continue

        sizea = 0
        while -byte < 8:
            v5 -= byte
            out.append(_sub_404400(data, data_off, mp, mp_off) & 0xFF)
            mp_off += 12
            sizea += 1
            if loopindex == 0:
                return bytes(out)
            loopindex -= 1
            byte = _signed_byte(mp[mp_off + 2])

        v10 = -(byte + v5)
        if v10 >= 8:
            raise ValueError("decode error: v10 >= 8")
        mask = DWORD_451948[v10 - 1] & 0xFF
        out.append(mask & _sub_404400(data, data_off, mp, mp_off))
        mp_off += 12
        i += sizea
        v5 = 0
    return bytes(out)


PATCH_INIT_SEGMENTS = [(0, 79), (79, 145), (0xE4, 52), (0x118, 83), (0x16C, 41)]
# (map_off, length, pointer-advance applied BEFORE this segment is read/written)
PATCH_MAP_SEGMENTS = [
    (0x242, 79, 0),
    (0x294, 145, 56),
    (0x328, 52, 78),
    (0x35D, 83, 26),
    (0x3B1, 41, 42),
]
PATCH_SRC_OFFSETS = [0, 79, 224, 276, 359]


def decode_patch_data(buf: bytes, patch_init: bytes, main_map: bytes):
    """
    Returns (patch_buffer_bytes, inst_count). 948 bytes per instrument.
    NOTE: instrument 0 starts at byte offset 0 of the returned buffer, not 4 -
    the "+4" in the allocated size (948*InstCount+4) is just slack, not a header.
    Same convention applies to rhythm_decode's kit buffer below.
    """
    bank_count = buf[0]
    inst_count = bank_count * 256
    patch_buffer = bytearray(948 * inst_count + 4)

    for i in range(inst_count):
        pos = 948 * i
        offset = 0
        for init_off, length in PATCH_INIT_SEGMENTS:
            patch_buffer[pos + offset: pos + offset + length] = patch_init[init_off: init_off + length]
            offset += length

    main_data_off = 14  # into buf
    position = 0
    for i in range(inst_count):
        cur = main_data_off
        off_in_inst = 0
        for map_off, length, advance in PATCH_MAP_SEGMENTS:
            cur += advance
            seg = _sub_4044E0(buf, cur, main_map, 12 * map_off, length)
            patch_buffer[position + off_in_inst: position + off_in_inst + length] = seg
            off_in_inst += length
        main_data_off = cur + 32

        pos1 = position
        for _ in range(4):
            seg = _sub_4044E0(buf, main_data_off, main_map, 12 * 0x3D8 + 36, 137)
            patch_buffer[pos1 + 400: pos1 + 400 + 137] = seg
            main_data_off += 85
            pos1 += 137
        position += 948

    return bytes(patch_buffer), inst_count


# (map_off, length, pointer-advance applied BEFORE this segment is read/written)
RHYTHM_MAP_SEGMENTS = [(0x46c, 18, 0), (0x480, 145, 14), (0x514, 52, 78), (0x549, 83, 26)]
RHYTHM_SRC_OFFSETS = [0, 18, 163, 215]
RHYTHM_FINAL_ADVANCE = 42


def rhythm_decode(rhythm_map: bytes, data_buffer: bytes, add_inst_size: int = 0):
    """
    Returns decoded rhythm buffer, 17282 bytes per kit.
    add_inst_size only enlarges the allocated/returned buffer (for later use with
    a larger inst_count in rhythm_encode) - it does NOT decode more kits than
    actually exist in data_buffer[1]; the extra tail is left zero-filled, matching
    the original C++ (which leaves it as unitialized malloc'd memory).
    """
    count = data_buffer[1]  # kits actually present in the source
    final_size = 17282 * (count + add_inst_size) + 4
    final_data = bytearray(final_size)  # zero-filled, unlike C's malloc

    v26_off = 20  # into data_buffer
    v12_off = 20
    position = 0

    for _kit in range(count):
        cur = v12_off
        out_pos = position
        for map_off, length, advance in RHYTHM_MAP_SEGMENTS:
            cur += advance
            seg = _sub_4044E0(data_buffer, cur, rhythm_map, 12 * map_off, length)
            final_data[out_pos: out_pos + length] = seg
            out_pos += length
        cur += RHYTHM_FINAL_ADVANCE
        v12_off = cur

        for i in range(0, 16984, 193):
            aaa = struct.unpack_from('<I', data_buffer, v12_off)[0]
            note_id = ((((aaa & 0xFF00 | (aaa << 16)) & 0xFFFFFFFF) << 8) |
                       (((aaa >> 16) | (aaa & 0xFF0000)) >> 8)) & 0xFFFFFFFF
            note_id = (note_id - 20) & 0xFFFFFFFF
            seg = _sub_4044E0(data_buffer, v26_off + note_id, rhythm_map, 12 * 0x59d, 193)
            final_data[position + i + 298: position + i + 298 + 193] = seg
            v12_off += 4

        position += 17282

    return bytes(final_data)


# ------------------------- ENCODE SIDE -------------------------

def _sub_10040DA0(buf: bytearray, buf_off: int, mp: bytes, mp_off: int, byte_val: int) -> int:
    base = mp[mp_off + 0]
    buffer_ptr_1 = buf_off + base
    map_byte = mp[mp_off + 2]
    if map_byte & 0x80:
        map_byte = _negate_u8(map_byte)
    loopindex = map_byte + mp[mp_off + 3]
    loopindex_1 = (-loopindex) & 0xFF
    number = 0
    ptr = buffer_ptr_1
    while loopindex > 0:
        loopindex -= 8
        loopindex_1 = (loopindex_1 + 8) & 0xFF
        number = (buf[ptr] | (number << 8)) & 0xFFFFFFFF
        ptr += 1
    mask = DWORD_451948[map_byte - 1]
    result = (number & ~(mask << loopindex_1) | ((mask << loopindex_1) & (byte_val << loopindex_1))) & 0xFFFFFFFF
    # write back big-to-little, same as: do{*--BufferPointer=(u8)result; result>>=8;} while(BufferPointer>BufferPointer_1);
    write_ptr = ptr
    val = result
    while write_ptr > buffer_ptr_1:
        write_ptr -= 1
        buf[write_ptr] = val & 0xFF
        val >>= 8
    return result


def _sub_10041540(buf: bytearray, buf_off: int, mp: bytes, mp_off: int, byte_val: int) -> int:
    v4 = mp[mp_off + 4]
    if mp[mp_off + 8] - v4 >= 0 or v4 >= 0x40:
        v5 = 0
    else:
        v5 = 64 - v4
    v6 = mp[mp_off + 2]
    v6 = _signed_byte(v6)
    if v6 < 0:
        v6 = -v6
    mapa = v6
    byte_1 = byte_val
    if byte_val - v5 > DWORD_451948[mapa - 1]:
        byte_1 = v5 + mp[mp_off + 6]
    return _sub_10040DA0(buf, buf_off, mp, mp_off, byte_1 - v5)


def _sub_10041410(buf: bytearray, buf_off: int, mp: bytes, mp_off: int, src: bytes, size: int) -> int:
    """
    Faithful state-machine translation of the original goto-heavy C function
    (labels TOP / LABEL_8 / LABEL_14 / LABEL_15 / WHILE2 preserved as states),
    validated by round-tripping through the already-verified decode function.
    """
    v4 = size
    v5 = 0
    v15 = 0
    src_i = 0
    if size <= 0:
        return v15

    v8 = v9 = v16 = v18 = v19 = 0
    state = 'TOP'
    while True:
        if state == 'TOP':
            v8 = _signed_byte(mp[mp_off + 2])
            v4 -= 1
            v19 = v4
            if v8 >= 0:
                v13 = src[src_i]
                src_i += 1
                _sub_10041540(buf, buf_off, mp, mp_off, v13)
                state = 'LABEL_14'
                continue
            v18 = 0
            v9 = -v8
            v16 = 0
            state = 'WHILE2' if -v8 < 8 else 'LABEL_8'
            continue

        elif state == 'LABEL_14':
            mp_off += 12
            v15 += 1
            state = 'LABEL_15'
            continue

        elif state == 'LABEL_15':
            v5 = 0
            if v4 <= 0:
                return v15
            state = 'TOP'
            continue

        elif state == 'LABEL_8':
            v11 = -(v8 + v18)
            if v11 < 8:
                v12 = src[src_i]
                src_i += 1
                if v12 > DWORD_451948[v11 - 1]:
                    v5 = -1
                write_val = v5 | v12
                _sub_10041540(buf, buf_off, mp, mp_off, write_val)
                v15 += v16
                state = 'LABEL_14'
                continue
            else:
                src_i += 1
                mp_off += 12
                state = 'LABEL_15'
                continue

        elif state == 'WHILE2':
            v17 = src[src_i]
            v18 -= v8
            src_i += 1
            if v17 > DWORD_451948[(-v8) - 1]:
                v5 = -1
            mp_off += 12
            v16 += 1
            v5 = ((v5 | v17) << v9)
            v4 = v19 - 1
            cond = (v19 == 0)
            v19 -= 1
            if cond:
                return v15
            v8 = _signed_byte(mp[mp_off + 2])
            v9 = -v8
            state = 'LABEL_8' if -v8 >= 8 else 'WHILE2'
            continue
    return v15


AAAAAAA = bytes([0xAD, 0xBA, 0x0D, 0xF0])


def encode_patch_data(decoded_patch_buffer: bytes, main_map: bytes, add: int, inst_count: int):
    final_bank_count = inst_count + add
    size = 574 * inst_count + 14
    file_buffer = bytearray(size)
    struct.pack_into('<i', file_buffer, 0, inst_count // 0xFF)
    struct.pack_into('<i', file_buffer, 4, 234881024)
    struct.pack_into('<i', file_buffer, 8, 1040318464)
    file_buffer[6] = 0

    for i in range((size - 14) // 4):
        file_buffer[14 + i * 4: 14 + i * 4 + 4] = AAAAAAA

    if add < final_bank_count:
        position = 948 * add
        file_ptr = 14
        for _ in range(final_bank_count - add):
            cur = file_ptr
            for (map_off, length, advance), src_off in zip(PATCH_MAP_SEGMENTS, PATCH_SRC_OFFSETS):
                cur += advance
                src = decoded_patch_buffer[position + src_off: position + src_off + length]
                _sub_10041410(file_buffer, cur, main_map, 12 * map_off, src, length)
            file_ptr = cur + 32

            pos1 = position
            for _ in range(4):
                src = decoded_patch_buffer[pos1 + 400: pos1 + 400 + 137]
                _sub_10041410(file_buffer, file_ptr, main_map, 12 * 0x3D8 + 36, src, 137)
                file_ptr += 85
                pos1 += 137
            position += 948

    return bytes(file_buffer)


def rhythm_encode(decoded_rhythm_buffer: bytes, rhythm_map: bytes, offset: int, inst_count: int):
    inst_count = inst_count - offset
    size = 11160 * inst_count + 20
    file_buffer = bytearray(size)
    file_buffer[1] = inst_count & 0xFF
    struct.pack_into('<i', file_buffer, 4, 335544320)
    struct.pack_into('<i', file_buffer, 8, 942276608)
    file_buffer[6] = 0

    position = 17282 * offset
    file_ptr = 20
    v20 = (inst_count << 9) + 20

    for _ in range(inst_count):
        cur = file_ptr
        for (map_off, length, advance), src_off in zip(RHYTHM_MAP_SEGMENTS, RHYTHM_SRC_OFFSETS):
            cur += advance
            src = decoded_rhythm_buffer[position + src_off: position + src_off + length]
            _sub_10041410(file_buffer, cur, rhythm_map, 12 * map_off, src, length)
        file_ptr = cur + RHYTHM_FINAL_ADVANCE

        loopindex_1 = v20
        for _ in range(88):
            v12 = (loopindex_1 >> 16) | (loopindex_1 & 0xFF0000)
            file_ptr += 4
            v13 = (loopindex_1 & 0xFF00) | ((loopindex_1 << 16) & 0xFFFFFFFF)
            loopindex_1 = (loopindex_1 + 121) & 0xFFFFFFFF
            value = ((v13 << 8) | (v12 >> 8)) & 0xFFFFFFFF
            struct.pack_into('<I', file_buffer, file_ptr - 4, value)
        v20 = loopindex_1
        position += 17282

    position_1 = 0
    for _ in range(inst_count):
        for i in range(0, 16984, 193):
            src = decoded_rhythm_buffer[i + position_1 + 298: i + position_1 + 298 + 193]
            _sub_10041410(file_buffer, file_ptr, rhythm_map, 12 * 0x59d, src, 193)
            file_ptr += 121
        position_1 += 17282

    return bytes(file_buffer)


# ------------------------- CLI -------------------------
import os
import sys


def _read(path):
    with open(path, 'rb') as f:
        return f.read()


def _write(path, data):
    with open(path, 'wb') as f:
        f.write(data)


def cmd_decode(args):
    """decode <extracted_dir> [--maps-dir DIR] [--kit-slots N]
    Reads PatchData.bin / RhythmData.bin from extracted_dir (produced by
    rom_creator.py extract), and PatchInit / MainMap / RhythmMap from maps_dir
    (defaults to extracted_dir). Writes PatchDecoded.bin / RhythmDecoded.bin
    into extracted_dir - these are the files you hex-edit.
    Rhythm data is padded up to kit_slots (default 128) total kit slots, since
    that's what a full param.dat needs - the padding is zero-filled and safe
    to leave untouched if you only want to edit the kits that already exist.
    """
    extracted_dir, maps_dir, kit_slots = args
    patch_data = _read(os.path.join(extracted_dir, 'PatchData.bin'))
    rhythm_data = _read(os.path.join(extracted_dir, 'RhythmData.bin'))
    patch_init = _read(os.path.join(maps_dir, 'PatchInit'))
    main_map = _read(os.path.join(maps_dir, 'MainMap'))
    rhythm_map = _read(os.path.join(maps_dir, 'RhythmMap'))

    patches, inst_count = decode_patch_data(patch_data, patch_init, main_map)
    _write(os.path.join(extracted_dir, 'PatchDecoded.bin'), patches)
    print(f"Decoded {inst_count} instruments -> PatchDecoded.bin ({len(patches)} bytes)")

    real_kit_count = rhythm_data[1]
    pad = max(0, kit_slots - real_kit_count)
    kits = rhythm_decode(rhythm_map, rhythm_data, add_inst_size=pad)
    _write(os.path.join(extracted_dir, 'RhythmDecoded.bin'), kits)
    print(f"Decoded {real_kit_count} real kits (padded to {kit_slots} slots) -> "
          f"RhythmDecoded.bin ({len(kits)} bytes)")


def cmd_encode(args):
    """encode <extracted_dir> [--maps-dir DIR]
    Reads your edited PatchDecoded.bin / RhythmDecoded.bin from extracted_dir
    and re-encodes them back over PatchData.bin / RhythmData.bin in that same
    directory, ready for `rom_creator.py rebuild`. The kit slot count is
    read automatically from RhythmDecoded.bin's own size - it must have been
    produced by `decode` (or otherwise sized as 17282*N+4 bytes).
    """
    extracted_dir, maps_dir = args
    main_map = _read(os.path.join(maps_dir, 'MainMap'))
    rhythm_map = _read(os.path.join(maps_dir, 'RhythmMap'))

    patches = _read(os.path.join(extracted_dir, 'PatchDecoded.bin'))
    inst_count = (len(patches) - 4) // 948
    new_patch_data = encode_patch_data(patches, main_map, 0, inst_count)
    _write(os.path.join(extracted_dir, 'PatchData.bin'), new_patch_data)
    print(f"Encoded {inst_count} instruments -> PatchData.bin ({len(new_patch_data)} bytes)")

    kits = _read(os.path.join(extracted_dir, 'RhythmDecoded.bin'))
    kit_slots = (len(kits) - 4) // 17282
    new_rhythm_data = rhythm_encode(kits, rhythm_map, 0, kit_slots)
    _write(os.path.join(extracted_dir, 'RhythmData.bin'), new_rhythm_data)
    print(f"Encoded {kit_slots} kit slots -> RhythmData.bin ({len(new_rhythm_data)} bytes)")


def cmd_list_patches(args):
    """list-patches <extracted_dir> [--maps-dir DIR]"""
    extracted_dir, maps_dir = args
    decoded_path = os.path.join(extracted_dir, 'PatchDecoded.bin')
    if os.path.exists(decoded_path):
        patches = _read(decoded_path)
    else:
        patch_data = _read(os.path.join(extracted_dir, 'PatchData.bin'))
        patch_init = _read(os.path.join(maps_dir, 'PatchInit'))
        main_map = _read(os.path.join(maps_dir, 'MainMap'))
        patches, _ = decode_patch_data(patch_data, patch_init, main_map)

    inst_count = (len(patches) - 4) // 948
    for i in range(inst_count):
        name = patches[948 * i: 948 * i + 8].decode('ascii', errors='replace').rstrip('\x00')
        if name.strip():
            print(f"{i}: {name!r}")


def cmd_list_kits(args):
    """list-kits <extracted_dir> [--maps-dir DIR]"""
    extracted_dir, maps_dir = args
    decoded_path = os.path.join(extracted_dir, 'RhythmDecoded.bin')
    if os.path.exists(decoded_path):
        kits = _read(decoded_path)
    else:
        rhythm_data = _read(os.path.join(extracted_dir, 'RhythmData.bin'))
        rhythm_map = _read(os.path.join(maps_dir, 'RhythmMap'))
        kits = rhythm_decode(rhythm_map, rhythm_data)

    kit_count = (len(kits) - 4) // 17282
    for i in range(kit_count):
        name = kits[17282 * i: 17282 * i + 8].decode('ascii', errors='replace').rstrip('\x00')
        if name.strip():
            print(f"{i}: {name!r}")


def cmd_rename_patch(args):
    """rename-patch <extracted_dir> <index> <new_name>"""
    extracted_dir, index, new_name = args
    index = int(index)
    decoded_path = os.path.join(extracted_dir, 'PatchDecoded.bin')
    patches = bytearray(_read(decoded_path))
    name_bytes = new_name.encode('ascii')[:8].ljust(8, b' ')
    patches[948 * index: 948 * index + 8] = name_bytes
    _write(decoded_path, bytes(patches))
    print(f"Renamed instrument {index} to {new_name!r} in PatchDecoded.bin")
    print("Run 'encode' to write this back into PatchData.bin")


def cmd_rename_kit(args):
    """rename-kit <extracted_dir> <index> <new_name>"""
    extracted_dir, index, new_name = args
    index = int(index)
    decoded_path = os.path.join(extracted_dir, 'RhythmDecoded.bin')
    kits = bytearray(_read(decoded_path))
    name_bytes = new_name.encode('ascii')[:8].ljust(8, b' ')
    kits[17282 * index: 17282 * index + 8] = name_bytes
    _write(decoded_path, bytes(kits))
    print(f"Renamed kit {index} to {new_name!r} in RhythmDecoded.bin")
    print("Run 'encode' to write this back into RhythmData.bin")


def _parse_common(argv):
    """Pulls --maps-dir and --kit-slots out of argv, returns (positional, maps_dir, kit_slots)."""
    positional = []
    maps_dir = None
    kit_slots = 128
    i = 0
    while i < len(argv):
        if argv[i] == '--maps-dir':
            maps_dir = argv[i + 1]
            i += 2
        elif argv[i] == '--kit-slots':
            kit_slots = int(argv[i + 1])
            i += 2
        else:
            positional.append(argv[i])
            i += 1
    return positional, maps_dir, kit_slots


if __name__ == '__main__':
    COMMANDS = {
        'decode': cmd_decode,
        'encode': cmd_encode,
        'list-patches': cmd_list_patches,
        'list-kits': cmd_list_kits,
        'rename-patch': cmd_rename_patch,
        'rename-kit': cmd_rename_kit,
    }

    if len(sys.argv) < 3 or sys.argv[1] not in COMMANDS:
        print("Usage:")
        print("  patch_tools.py decode <extracted_dir> [--maps-dir DIR]")
        print("  patch_tools.py encode <extracted_dir> [--maps-dir DIR] [--kit-slots N]")
        print("  patch_tools.py list-patches <extracted_dir> [--maps-dir DIR]")
        print("  patch_tools.py list-kits <extracted_dir> [--maps-dir DIR]")
        print("  patch_tools.py rename-patch <extracted_dir> <index> <new_name>")
        print("  patch_tools.py rename-kit <extracted_dir> <index> <new_name>")
        print()
        print("--maps-dir defaults to <extracted_dir> if not given (put PatchInit/")
        print("MainMap/RhythmMap there, or point --maps-dir at wherever they live).")
        print("--kit-slots defaults to 128 (total kit slots HyperCanvas expects).")
        sys.exit(1)

    mode = sys.argv[1]
    rest, maps_dir_arg, kit_slots_arg = _parse_common(sys.argv[2:])

    if mode == 'decode':
        extracted_dir = rest[0]
        cmd_decode((extracted_dir, maps_dir_arg or extracted_dir, kit_slots_arg))
    elif mode == 'encode':
        extracted_dir = rest[0]
        cmd_encode((extracted_dir, maps_dir_arg or extracted_dir))
    elif mode == 'list-patches':
        extracted_dir = rest[0]
        cmd_list_patches((extracted_dir, maps_dir_arg or extracted_dir))
    elif mode == 'list-kits':
        extracted_dir = rest[0]
        cmd_list_kits((extracted_dir, maps_dir_arg or extracted_dir))
    elif mode == 'rename-patch':
        cmd_rename_patch(rest)
    elif mode == 'rename-kit':
        cmd_rename_kit(rest)
