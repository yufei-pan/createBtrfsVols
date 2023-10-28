#!/usr/bin/env python3
import subprocess
import json

def run_command(command):
    output = []
    print('> '+' '.join(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in iter(process.stdout.readline, b''):
        decoded_line = line.decode().strip()
        print(decoded_line)
        output.append(decoded_line)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Command failed with error: {stderr.decode().strip()}")
    return "\n".join(output)

# Initialize an empty list to store fstab entries
fstab_entries = []
mount_name_prefix = 'impulse'

# Use lsblk to list all block devices in JSON format
lsblk_output = run_command(["lsblk", "-Jb"])
lsblk_json = json.loads(lsblk_output)

# Loop through all devices
for device in lsblk_json['blockdevices']:
    device_name = device['name']
    device_path = f"/dev/{device_name}"
    # Get disk size in bytes and convert to TB
    disk_size_tb = int(device['size']) / (10 ** 12)

    if 1.7 <= disk_size_tb <= 2.0:  # Adjusted the size range to 1.5-2.5TB
        print('*'*80)
        print(f"Identified {device_path} of size {disk_size_tb}TB")

        # User confirmation
        user_input = input(f"Hit 'Enter' to format {device_path} or any other key to skip: ")

        if user_input == '':
            # Remove all existing partitions (This will wipe the drive!)
            run_command(["sudo", "parted", device_path, "--script", "mklabel", "gpt"])

            # Format the drive with Btrfs (Compression will be set via mount options)
            run_command(["sudo", "mkfs.btrfs", "-f", device_path])
        else:
            print(f"Skipped formatting {device_path}")

        # Fetch the UUID of the formatted partition
        uuid_output = run_command(["sudo", "blkid", "-o", "value", "-s", "UUID", device_path])

        if uuid_output:
            # Add to fstab entries with compression and trim options
            mount_point = f'/mnt/{mount_name_prefix}_data/{mount_name_prefix}_{uuid_output[0:3]}'
            run_command(['mkdir','-p',mount_point])
            fstab_entry = f"UUID={uuid_output}\t{mount_point}\tbtrfs\tcompress=zstd:2,discard=async\t0\t0"
            fstab_entries.append(fstab_entry)
            print(f"{device_path} -> {mount_point}")
        else:
            print(f"Could not fetch UUID for {device_path}")
        print('-'*80)

# Write the fstab entries to a file
if fstab_entries:
    with open(f"{mount_name_prefix}_fstab_entries.txt", "w") as f:
        for entry in fstab_entries:
            f.write(entry + "\n")
    print(f"Generated {mount_name_prefix}_fstab_entries.txt")
    run_command(['mkdir','-p','/mnt/'+mount_name_prefix])
else:
    print("No fstab entries generated.")

