---
title: "File Storage Anatomy"
date: 2026-11-11 10:00:00 +0800
categories:
  - system
tags: system linux kernel storage filesystems low-latency performance
excerpt: >
  A first-principles deep dive into Linux file storage anatomy through the lens of the inode: how dentries, inodes, and extent trees decouple names from physical blocks, why disks report ENOSPC with 500GB free, the mechanics of unlinked ghost files, and filesystem lock contention.
---

Consider two perplexing production mysteries that every systems engineer eventually encounters:

1. **The Empty-Yet-Full Disk:** Your server's monitoring alerts scream that a database drive is completely full. You run `df -h` and see **$500\,\text{GB}$ of free disk space**. Yet the very next write operation crashes with `ENOSPC: No space left on device`.
2. **The Ghost File:** A background logging process inflates a $200\,\text{GB}$ log file. You run `rm app.log`. The filename vanishes instantly from `ls`. But when you check `df -h`, **zero bytes were reclaimed**. The disk remains at $100\%$ capacity.

How can a disk with $500\,\text{GB}$ of free blocks reject new writes? And how can deleting a file reclaim zero bytes of storage?

To understand these anomalies, we must discard the human intuition that a "file" is a single entity containing a name, metadata, and bytes.

In the Linux kernel, **files do not have names**, and names do not contain data. 

Linux file storage is an elegant, multi-tier decoupling of three distinct concepts:
* **The Name:** The directory entry (`dentry`).
* **The Identity & Metadata:** The Index Node (**`inode`**).
* **The Raw Data:** Physical filesystem blocks managed by **Extent Trees**.

This post explores the anatomy of Linux storage from the VFS layer down to NVMe blocks, using the `inode` as our lens.

---

## 1. The Core Architecture: The Three-Tier Separation

When an application calls `open("/var/log/market.dat", O_RDWR)`, the Linux kernel navigates three completely separate layers:

```text
USER SPACE                                VFS & FILESYSTEM LAYERS
┌─────────────────────────────────┐
│ Path: "/var/log/market.dat"     │
└────────────────┬────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. DENTRY (Directory Entry)                                            │
│    • Name: "market.dat"                                                │
│    • Inode Number: 144210                                              │
│    • Purely a string-to-number mapping; holds NO file data!            │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. INODE (Index Node - struct inode)                                   │
│    • Inode Number: 144210                                              │
│    • File Size: 104,857,600 Bytes (100 MB)                             │
│    • Permissions: 0644, Owner: UID 1000                                │
│    • Timestamps: atime, mtime, ctime                                   │
│    • Link Count (i_nlink): 1                                           │
│    • Block Pointers: Points to Extent Tree                             │
│    • Holds NO filename!                                                │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. DATA BLOCKS (Physical 4KB Sectors / Flash LBAs)                     │
│    • Extent Tree: [Blocks 204,800 to 230,399] (Contiguous 100 MB data)  │
│    • Actual market ticks and raw payload bytes                          │
└────────────────────────────────────────────────────────────────────────┘
```

Notice the central realization: **the filename is not part of the file.** 

A filename is merely a label in a phonebook (the directory). The real file is the `inode`.

---

## 2. Layer 1: Dentries and Path Resolution

Resolving a path like `/var/log/market.dat` requires traversing each directory component from root `/` down to the target leaf.

### The Dentry Cache (dcache)
Performing multiple disk I/O operations for every single directory lookup along a path would cripple system performance. To eliminate this overhead, the kernel maintains the **`dentry cache` (`dcache`)** in RAM.

* Each component is represented as an in-memory `struct dentry` linking the parent directory to the child inode.
* Path walks are resolved in RAM via lockless **RCU-walk** (`rcu_read_lock`), completing in **nanoseconds with zero disk reads**.
* If a path component is not cached in RAM, the kernel falls back to the slow path: reading the parent directory's underlying **Directory Data Blocks** from storage.

---

## 3. Layer 2: The Inode (The True Identity)

Once the VFS identifies the inode number (e.g., `144210`), it reads the **`inode`** into memory.

On disk (e.g., ext4), every inode occupies a fixed, compact structure (typically **128 or 256 bytes**):

```text
ext4 On-Disk Inode Structure (256 Bytes):
┌───────────────────────────┬────────────────────────────────────────────┐
│ Field                     │ Purpose                                    │
├───────────────────────────┼────────────────────────────────────────────┤
│ i_mode (16 bits)          │ File type (regular, directory) & rwxr-xr-x │
│ i_uid / i_gid (32 bits)   │ User and Group ownership                   │
│ i_size_lo / i_size_high   │ 64-bit file size in bytes                  │
│ i_atime (32 bits)         │ Access time (last read)                    │
│ i_mtime (32 bits)         │ Modification time (last data write)        │
│ i_ctime (32 bits)         │ Change time (last inode metadata write)    │
│ i_crtime (32 bits)        │ Creation time (birth time in ext4)         │
│ i_links_count (16 bits)   │ Hard link count (how many dentries point)  │
│ i_blocks_lo (32 bits)     │ Number of 512-byte blocks allocated        │
│ i_flags (32 bits)         │ Attributes (e.g., append-only, immutable)  │
│ i_block[15] (60 bytes)    │ Extent Tree Root (Pointer to data blocks)  │
└───────────────────────────┴────────────────────────────────────────────┘
```

### Mystery Solved: Why Disks Run Out of Space with 500GB Free!
In classical Linux filesystems like `ext4`, the number of inodes is **fixed at format time (`mkfs.ext4`)**:
* When creating an ext4 filesystem on a 1 TB drive, `mkfs` pre-allocates an **Inode Table** at the beginning of each block group (e.g., allocating 1 inode for every 16 KB of disk space $\approx 65\text{ million inodes}$).
* Every single file, directory, or symlink consumes **exactly one inode**.

If an application generates 65 million tiny 4-byte sensor files, **all 65 million inodes are exhausted**, while physical data blocks remain $90\%$ empty:

```bash
# Check physical disk space:
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p1  1.0T  500G  500G  50% /data    # 500 GB Free!

# Check inode utilization:
$ df -i
Filesystem       Inodes    IUsed   IFree IUse% Mounted on
/dev/nvme0n1p1  65536000 65536000       0  100% /data  # 0 INODES FREE!
```

When an application calls `open("new_tick.dat", O_CREAT)`, the kernel attempts to allocate a new inode from the inode allocation bitmap. Since no free inodes exist, the kernel returns **`ENOSPC`**, even though hundreds of gigabytes of disk storage sit idle!

*(Modern filesystems like XFS allocate inodes dynamically, largely mitigating this historical ext4 constraint.)*

---

## 4. Layer 3: Physical Data Blocks and Storage

How does a 256-byte inode connect to actual bytes stored on physical flash or magnetic platters?

### 1. From Inode to Blocks: Extent Trees
In legacy filesystems (ext2/3), the inode stored an array of block addresses: 12 direct pointers, 1 indirect pointer, 1 double-indirect pointer, and 1 triple-indirect pointer. To read a large file, the disk head had to jump back and forth reading indirect metadata pointer tables—creating massive I/O fragmentation.

Modern filesystems (ext4 / XFS) discarded indirect block pointers in favor of **Extents**.

An **extent** is a single descriptor that maps a contiguous range of logical file blocks to a contiguous range of physical storage blocks:

$$\text{Extent} = (\text{Logical Block Number}, \text{Length}, \text{Physical Block Number})$$

Inside the 60-byte `i_block` field of the ext4 inode, the kernel stores an **Extent Tree**:

```text
                 [ Inode: i_block[60B] ]
                  (Extent Tree Header)
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
 [ Leaf Node: Extent 1 ]             [ Leaf Node: Extent 2 ]
 Logical Blocks: 0 - 25,599          Logical Blocks: 25,600 - 51,199
 Length: 25,600 Blocks (100 MB)      Length: 25,600 Blocks (100 MB)
 Physical LBA: 4,000,000             Physical LBA: 8,500,000
```

* **Efficiency:** A single 12-byte `struct ext4_extent` can map up to **$128\,\text{MB}$ of contiguous storage** in one entry.
* A $10\,\text{GB}$ contiguous file requires only 80 extents instead of 2.6 million individual block pointers.
* **Low-Latency Impact:** When your application issues a sequential read, the kernel does not search pointer chains; it calculates the physical LBA with simple arithmetic:
  $$\text{Physical LBA} = \text{Extent.physical_start} + (\text{File Offset} - \text{Extent.logical_start})$$

### 2. The Two Faces of Data Blocks: Regular Files vs. Directory Data Blocks

Once physical 4 KB blocks are mapped via extents, what is stored inside them falls into two fundamentally distinct categories:

| Dimension | Regular File Data Blocks | Directory Data Blocks |
| :--- | :--- | :--- |
| **Payload Content** | Arbitrary user bytes (binary, text, Parquet, ticks) | Structured records (`ext4_dir_entry_2` or HTree index) |
| **Kernel Interpretation** | **Opaque:** Kernel does not inspect or validate bytes | **Strictly Parsed:** Kernel reads, hashes, and navigates entries |
| **User-Space Modification** | **Permitted:** Arbitrary writes via `write()`, `pwrite()`, `mmap` | **Forbidden:** Calling `write()` returns `-EISDIR` (*Is a directory*) |
| **How Content is Changed** | Direct application data writes | Indirectly via VFS syscalls (`mkdir`, `unlink`, `rename`, `link`) |
| **Read System Call** | `read()` / `pread()` | `getdents64()` (used by `ls`, `find`) |

#### Anatomy of a 4 KB Directory Data Block

Inside an ext4 directory data block, the payload is an array of variable-length directory entries (`struct ext4_dir_entry_2`):

```text
 0                        4096 Bytes
 ┌──────────────────────────────────────────────────────────────┐
 │ Record 1 │ Record 2 │   Record 3   │     Record 4 ...        │
 └──────────────────────────────────────────────────────────────┘
```

Each record contains 5 specific fields:
* **`inode` (4 bytes):** The 32-bit inode number pointing to the file's metadata.
* **`rec_len` (2 bytes):** Offset to the next record in bytes.
* **`name_len` (1 byte):** Length of the filename string.
* **`file_type` (1 byte):** Type code (`1` = Regular, `2` = Directory, `7` = Symlink).
* **`name` (variable):** Raw filename characters (e.g., `"market.dat"`).

```text
Offset    Sample Directory Block Payload (/var/log/):
───────   ────────────────────────────────────────────────────────────────
0x000     [ Inode: 144208 | rec_len: 12 | name_len: 1 | type: DIR | "."   ]
0x00C     [ Inode: 144101 | rec_len: 12 | name_len: 2 | type: DIR | ".."  ]
0x018     [ Inode: 144210 | rec_len: 24 | name_len: 10| type: REG | "market.dat" ]
0x030     [ Inode: 144211 | rec_len: 4048|name_len: 9 | type: REG | "syslog.log" ... ]
───────   ────────────────────────────────────────────────────────────────
Total: 4096 bytes (Last entry's rec_len stretches to pad the 4 KB boundary)
```

#### Why Directory Deletion (`rm`) Never Wipes Bytes

This directory block format explains two counter-intuitive Linux storage phenomena:

```text
Before Deletion:
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ ".." (rec_len: 12)  │ "old.log" (len: 20) │ "new.log" (len: 24) │
└─────────────────────┴─────────────────────┴─────────────────────┘

After `rm old.log` (unlink):
┌───────────────────────────────────────────┬─────────────────────┐
│ ".." (rec_len: 12 + 20 = 32)              │ "new.log" (len: 24) │
│       [ "old.log" bytes remain intact! ]  │                     │
└───────────────────────────────────────────┴─────────────────────┘
```

1. **How `rm` actually works on disk:** When you run `rm old.log`, Linux does **not** zero out the filename or wipe the directory block. It merely adds `old.log`'s `rec_len` to the preceding entry's `rec_len` (`12 + 20 = 32`). When traversing the block, the kernel skips directly over `old.log`. The original filename and inode number remain intact in the block until overwritten, which is why forensics and undelete tools can recover unlinked files.
2. **Why directory sizes never shrink:** If you create 1,000,000 files in `/tmp/scratch/`, the kernel allocates thousands of 4 KB directory data blocks (e.g., $32\,\text{MB}$ shown in `ls -ld`). If you delete all 1,000,000 files, the directory entries are skipped, but the **$32\,\text{MB}$ of directory data blocks remain allocated**. Linux ext4 does not automatically truncate directory blocks on deletion.

#### Scaling to Millions of Files: ext4 HTree Indexing
* **Small Directories (< ~50 files):** All entries fit in a single 4 KB data block. The kernel performs a linear scan.
* **Large Directories (> thousands of files):** Linear scans would degrade `open()` latency to hundreds of milliseconds. When a directory exceeds a single block, ext4 converts its directory data blocks into an **HTree** (a specialized 2-level B-tree indexed by filename hash). The root 4 KB block stores 32-bit hashes pointing to leaf 4 KB directory blocks, keeping lookup complexity at $O(1)$ regardless of directory size.

---

## 5. Mystery Solved: The Ghost File (`rm` Reclaims 0 Bytes)

Why does running `rm huge.log` fail to reclaim disk space when a background process has the file open?

The answer lies in how Linux tracks file deletion:

```text
1. User executes: rm huge.log
   └─► System call: unlink("huge.log")
         ├─► Kernel removes "huge.log" entry from directory table.
         └─► Inode link count decrements: inode->i_nlink (1 ──► 0)

2. BUT: A trading daemon still has the file open!
   └─► Kernel File Descriptor reference count: file->f_count > 0

3. THE KERNEL DELETION CONTRACT:
   Physical data blocks are freed ONLY WHEN BOTH:
   (i_nlink == 0)  AND  (f_count == 0)
```

Because the logging process holds an open file descriptor (`f_count >= 1`), the kernel **refuses to deallocate the extent tree or return physical data blocks to the free bitmap**.

The file becomes a **Ghost Inode**:
* It has no name in the directory tree (`ls` cannot find it).
* No new process can open it.
* But it continues consuming 200 GB of physical flash memory until the process terminates or closes the descriptor!

### How to Diagnose and Fix Ghost Files in Production

```bash
# 1. Identify processes holding open unlinked inodes:
$ lsof +L1 /data
COMMAND    PID USER   FD   TYPE DEVICE SIZE/OFF   NLINK       NAME
trading_gw 8421 root    3u   REG  259,1 214748364800     0 /data/huge.log (deleted)

# 2. Reclaim space immediately WITHOUT stopping the application:
# Truncate the file to 0 bytes via the process's file descriptor in procfs!
$ : > /proc/8421/fd/3
```
By truncating the file descriptor via `/proc/<pid>/fd/<fd>`, the kernel immediately frees all data blocks in the extent tree, restoring disk space without requiring an application restart.

---

## 6. Systems Tuning: Inode Latency Traps

In high-frequency trading and low-latency databases, several inode mechanics introduce severe tail-latency liabilities:

### 1. The `atime` Catastrophe (Read Becoming a Write)
By default, the POSIX specification mandates that every time a file is read, its access timestamp (`inode->i_atime`) must be updated.

* **The Trap:** When your market data engine reads an order book historical snapshot, the kernel must execute an **in-memory inode update**, followed by writing the modified inode back to storage.
* A read operation silently generates disk write amplification and locks the inode metadata.
* **The Production Fix:** Always mount high-performance filesystems with **`noatime`**:
  ```bash
  # /etc/fstab
  /dev/nvme0n1p1  /data  ext4  defaults,noatime,nodiratime  0  2
  ```

### 2. Inode Lock Contention (`i_rwsem`)
In the Linux kernel, every `struct inode` is protected by a read/write semaphore: **`inode->i_rwsem`**.

* When multiple threads append data concurrently to the same shared log file or trade journal, each thread must acquire `i_rwsem` in exclusive write mode.
* This serializes multi-threaded writers, causing severe lock contention and thread stalls.
* **The Fix:** In low-latency architectures, adopt **thread-per-core file partitioning**: each core appends strictly to its own dedicated private file (e.g., `ticks_core_1.dat`, `ticks_core_2.dat`), eliminating cross-core inode lock contention.

---

## Summary Architecture Checklist

| Layer | Object | Stored In | Responsibility |
| :--- | :--- | :--- | :--- |
| **Naming** | `struct dentry` | RAM (`dcache`) | Maps human-readable path string to Inode Number |
| **Directory Blocks** | `ext4_dir_entry_2` / HTree | 4 KB Data Blocks | On-disk table mapping child filenames to inode numbers |
| **Identity** | `struct inode` | Inode Table (Disk & RAM) | Size, permissions, timestamps, link count, and block map |
| **Data Map** | `ext4_extent` | Inode `i_block` Tree | Contiguous physical LBA block spans |
| **Regular Blocks** | 4 KB Data Blocks | NVMe / SSD NAND Flash | Opaque application payload bytes (ticks, logs, binary) |
| **Deletion Rule** | Data blocks freed | When `i_nlink == 0` **and** `f_count == 0` | Prevents data corruption while active processes read |
