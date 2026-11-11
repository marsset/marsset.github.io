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

## 2. Layer 1: Dentries and Directory Lookup

In Linux, a directory is not a special physical partition. A directory is simply a **regular file whose data payload is a lookup table** of entries:

```text
Directory File Payload (/var/log/):
┌──────────────┬──────────────┬──────────────┬────────────────────────┐
│ Inode Number │ Record Length│ Name Length  │ Filename               │
├──────────────┼──────────────┼──────────────┼────────────────────────┤
│ 144208       │ 16           │ 1            │ "."                    │
│ 144101       │ 16           │ 2            │ ".."                   │
│ 144210       │ 24           │ 10           │ "market.dat"           │
│ 144211       │ 24           │ 9            │ "syslog.log"           │
└──────────────┴──────────────┴──────────────┴────────────────────────┘
```

### The Dentry Cache (dcache)
Resolving a path like `/var/log/market.dat` requires reading the root directory `/`, finding `var`'s inode, opening `var`, finding `log`'s inode, opening `log`, and finally locating `market.dat`'s inode number.

Performing multiple disk I/O operations for every single file path lookup would cripple system performance.

To eliminate this overhead, the kernel maintains the **`dentry cache` (`dcache`)** in RAM. Once resolved, directory lookups are cached as `struct dentry` objects in memory. Subsequent path walks resolve in **nanoseconds with zero disk reads**.

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

## 4. Layer 3: From Inode to Data (Extent Trees)

How does a 256-byte inode point to a $100\,\text{GB}$ market data file?

### Legacy ext2/3: Indirect Block Pointers
In legacy filesystems, the inode stored an array of block addresses: 12 direct pointers, 1 indirect pointer, 1 double-indirect pointer, and 1 triple-indirect pointer.

To read a large file, the disk head had to jump back and forth reading indirect metadata pointer tables—creating massive I/O fragmentation.

### Modern ext4 / XFS: Extent Trees
Modern filesystems discarded indirect block pointers in favor of **Extents**.

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
| **Identity** | `struct inode` | Inode Table (Disk & RAM) | Size, permissions, timestamps, link count, and block map |
| **Data Map** | `ext4_extent` | Inode `i_block` Tree | Contiguous physical LBA block spans |
| **Storage** | 4KB Data Blocks | NVMe / SSD NAND Flash | Actual binary payload bytes |
| **Deletion Rule** | Data blocks freed | When `i_nlink == 0` **and** `f_count == 0` | Prevents data corruption while active processes read |
