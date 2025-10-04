import os
import re
import zlib

def decompress_game_file(input_path, output_path):
    with open(input_path, "rb") as f:
        f.seek(8)  
        compressed_data = f.read()
    try:
        decompressed_data = zlib.decompress(compressed_data)
    except Exception as e:
        print(f"ZLIB decompression failed: {e}")
        return False
    with open(output_path, "wb") as f:
        f.write(decompressed_data)
    print(f"Decompression complete ({len(decompressed_data)} bytes)")
    return True

def extract_all_tags():
    bin_filename = "decompressed_world.bin"
    output_folder = "extracted"
    os.makedirs(output_folder, exist_ok=True)

    print("Scanning for all tags...")

    if not os.path.isfile(bin_filename):
        print("decompressed_world.bin not found.")
        return

    with open(bin_filename, "rb") as f:
        data = f.read()

    
    structure_sig = b'\x0A\x00\x00\x0A\x00\x04\x64\x61\x74\x61'
    player_sig = b'\x0A\x00\x00\x03\x00\x0E'
    level_sig = b'\x0A\x00\x00\x0A\x00\x04\x44\x61\x74\x61'
    zlib_sig = b'\x78\x9C'
    all_starts = []

    
    index = 0
    while True:
        index = data.find(structure_sig, index)
        if index == -1:
            break
        all_starts.append((index, "Structure"))
        index += 1

    
    index = 0
    while True:
        index = data.find(player_sig, index)
        if index == -1:
            break
        all_starts.append((index, "Player"))
        index += 1

    
    index = 0
    while True:
        index = data.find(level_sig, index)
        if index == -1:
            break
        all_starts.append((index, "Level"))
        index += 1

    
    all_starts = sorted(set(all_starts), key=lambda x: x[0])

    if not all_starts:
        print("No Tags found.")
        return

    print(f"Found {len(all_starts)} tag starts")

    for i, (start_index, tag_type) in enumerate(all_starts):
        next_index = all_starts[i + 1][0] if i + 1 < len(all_starts) else len(data)
        end_index = next_index
        stop_reason = "Next Tag"

        zlib_index = data.find(zlib_sig, start_index, next_index)
        if zlib_index != -1:
            end_index = zlib_index
            stop_reason = "ZLIB boundary"

        tag_data = data[start_index:end_index]

        compound_name = tag_type
        if tag_type == "Structure":
            try:
                features_offset = start_index + len(structure_sig) + 3
                scan_limit = min(len(tag_data), 256)
                for j in range(features_offset, scan_limit):
                    if tag_data[j] == 0x0A:
                        name_len = tag_data[j + 1] << 8 | tag_data[j + 2]
                        raw_name = tag_data[j + 3:j + 3 + name_len]
                        clean_bytes = bytes([b for b in raw_name if b > 31 and b != 127 and b != 0])
                        compound_name = clean_bytes.decode('utf-8', errors='ignore') or tag_type
                        compound_name = re.sub(r'[^\w\-]', '_', compound_name)
                        break
                else:
                    if b'unlimitedTracking' in tag_data:
                        compound_name = "map_0"
            except Exception:
                compound_name = tag_type

        filename = f"{compound_name}_{i}.dat"
        filepath = os.path.join(output_folder, filename)

        with open(filepath, "wb") as f:
            f.write(tag_data)

        print(f"Extracted {filename} ({len(tag_data)} bytes) at 0x{start_index:X} [{tag_type}] → {stop_reason}")

    
    try:
        os.remove(bin_filename)
        print("Complete. You can open these files using NBTExplorer or just look at them through text editor for UTF-8 Strings.")
    except Exception as e:
        print(f"Failed to delete temporary file.{e}")


compressed_file = "savegame.wii"
if os.path.isfile(compressed_file):
    if decompress_game_file(compressed_file, "decompressed_world.bin"):
        extract_all_tags()
else:
    print("savegame.wii not found in current directory.")



input("Press Enter to continue...")
